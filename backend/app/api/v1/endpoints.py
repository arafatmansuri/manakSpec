import io
import zipfile
import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from asyncpg import Connection, Pool
from typing import Dict, Optional, Any, List
from app.core.db import get_db_connection,get_db_pool
from app.schemas.response import RecommendationOutput
from app.services.session_service import session_service
from app.services.parser import document_parser
from app.services.ingester import bis_ingester
from app.agent.workflow import agent_executor

router = APIRouter()

@router.post("/recommend", response_model=RecommendationOutput)
async def recommend_standards(
    query_text: Optional[str] = Form(None, description="Optional text query or prompt"),
    session_id: Optional[str] = Form(None, description="Optional UUID to continue chat session"),
    file: Optional[UploadFile] = File(None, description="Optional PDF or image upload"),
    conn: Connection = Depends(get_db_connection)
):
    # Ensure the request contains at least text or a file attachment
    if not query_text and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a query text, attach a document (PDF/Image), or both."
        )

    extracted_file_text = ""
    
    # 1. Parse File if Provided
    if file:
        contents = await file.read()
        filename = file.filename.lower() if file.filename else ""

        if filename.endswith(".pdf"):
            extracted_file_text = document_parser.extract_text_from_pdf(contents)
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            extracted_file_text = document_parser.extract_text_from_image(contents)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Please upload PDF or image files."
            )

        if not extracted_file_text and not query_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract legible text from the uploaded document."
            )

    # 2. Combine Text Query and Extracted Document Text
    combined_query_parts = []
    if query_text and query_text.strip():
        combined_query_parts.append(f"User Instruction: {query_text.strip()}")
    if extracted_file_text and extracted_file_text.strip():
        combined_query_parts.append(f"Extracted Document Content:\n{extracted_file_text.strip()}")
    
    full_prompt = "\n\n".join(combined_query_parts)

    try:
        # 3. Resolve or Create Chat Session
        active_session_id = await session_service.get_or_create_session(conn, session_id)

        # 4. Retrieve Past Conversation History for Session Context
        chat_history = await session_service.get_recent_history(conn, active_session_id)

        # 5. Persist User Message to DB
        await session_service.save_message(conn, active_session_id, "user", full_prompt)

        # 6. Execute LangGraph Workflow with Memory
        initial_state = {
            "raw_query": full_prompt,
            "chat_history": chat_history,
            "expanded_query": "",
            "retrieved_data": {},
            "final_output": None,
            "execution_provider": "",
            "db_conn": conn
        }
        
        result = await agent_executor.ainvoke(initial_state)
        structured_synthesis = result["final_output"]

        # 7. Persist Assistant Synthesis Response to DB
        await session_service.save_message(
            conn, 
            active_session_id, 
            "assistant", 
            structured_synthesis.model_dump_json()
        )

        return RecommendationOutput(
            session_id=active_session_id,
            query_expansion_used=result["expanded_query"],
            primary_standards=result["retrieved_data"]["primary_standards"],
            allied_references=result["retrieved_data"]["allied_references"],
            structured_synthesis=structured_synthesis,
            execution_provider=result["execution_provider"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing procurement request: {str(e)}"
        )

# In-memory status store for bulk jobs
ingestion_jobs_db: Dict[str, Dict[str, Any]] = {}

async def process_bulk_ingestion_job(job_id: str, file_items: List[Dict[str, Any]], db_pool: Pool):
    """Worker task executing batch ingestion asynchronously using the db_pool."""
    ingestion_jobs_db[job_id]["status"] = "processing"

    async with db_pool.acquire() as conn:
        for item in file_items:
            filename = item["filename"]
            file_bytes = item["bytes"]

            try:
                json_payload = None
                if filename.lower().endswith(".json"):
                    json_payload = json.loads(file_bytes.decode("utf-8"))

                result = await bis_ingester.ingest_document(
                    conn=conn,
                    file_bytes=file_bytes,
                    filename=filename,
                    json_payload=json_payload
                )

                ingestion_jobs_db[job_id]["processed_files"] += 1
                ingestion_jobs_db[job_id]["details"].append({
                    "filename": filename,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                ingestion_jobs_db[job_id]["failed_files"] += 1
                ingestion_jobs_db[job_id]["details"].append({
                    "filename": filename,
                    "status": "failed",
                    "error": str(e)
                })

    ingestion_jobs_db[job_id]["status"] = "completed"


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_bis_standard(
    file: Optional[UploadFile] = File(None, description="BIS Standard PDF or JSON document"),
    is_number: Optional[str] = Form(None, description="Optional manual override for IS Code"),
    title: Optional[str] = Form(None, description="Optional manual override for Standard Title"),
    publication_year: Optional[int] = Form(None, description="Optional manual override for Publication Year"),
    scope: Optional[str] = Form(None, description="Optional manual override for Scope Description"),
    is_mandatory_qco: Optional[bool] = Form(None, description="Optional flag for Mandatory QCO"),
    scheme_type: Optional[str] = Form(None, description="Optional scheme type (e.g., Scheme-I)"),
    relation_type: Optional[str] = Form(None, description="Explicit relation type (e.g., 'Amendment')"),
    parent_is_number: Optional[str] = Form(None, description="Parent IS Code if file is an Amendment"),
    technical_specifications_json: Optional[str] = Form(None, description="JSON string of dynamic specs"),
    conn: Connection = Depends(get_db_connection)
):
    try:
        manual_overrides: Dict[str, Any] = {
            "is_number": is_number,
            "title": title,
            "publication_year": publication_year,
            "scope_text": scope,
            "is_mandatory_qco": is_mandatory_qco,
            "scheme_type": scheme_type,
            "relation_type": relation_type
        }

        if technical_specifications_json:
            manual_overrides["technical_specifications"] = json.loads(technical_specifications_json)

        if not file:
            raise HTTPException(status_code=400, detail="No file provided for ingestion.")

        file_bytes = await file.read()
        filename = file.filename or ""

        json_payload = None
        if filename.lower().endswith(".json"):
            json_payload = json.loads(file_bytes.decode("utf-8"))

        result = await bis_ingester.ingest_document(
            conn=conn,
            file_bytes=file_bytes,
            filename=filename,
            json_payload=json_payload,
            relation_type=relation_type,
            parent_is_number=parent_is_number,
            manual_overrides=manual_overrides
        )
        return result

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest-bulk", status_code=status.HTTP_202_ACCEPTED)
async def ingest_bulk_standards(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="List of PDFs/JSONs or a ZIP archive containing standards"),
    db_pool: Pool = Depends(get_db_pool)
):
    """
    Accepts multiple standalone PDF/JSON files or .zip archives.
    Extracts files in memory and processes them in a background task.
    """
    extracted_file_items: List[Dict[str, Any]] = []

    for upload_file in files:
        filename = upload_file.filename or ""
        file_bytes = await upload_file.read()

        # Handle ZIP Archives
        if filename.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    for zip_info in z.infolist():
                        if zip_info.is_dir() or zip_info.filename.startswith("__MACOSX"):
                            continue
                        
                        inner_filename = zip_info.filename
                        if inner_filename.lower().endswith((".pdf", ".json")):
                            extracted_file_items.append({
                                "filename": inner_filename,
                                "bytes": z.read(zip_info.filename)
                            })
            except zipfile.BadZipFile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid or corrupted ZIP archive: {filename}"
                )

        # Handle Standalone Files
        elif filename.lower().endswith((".pdf", ".json")):
            extracted_file_items.append({
                "filename": filename,
                "bytes": file_bytes
            })

    if not extracted_file_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No supported files (.pdf or .json) were found in the uploaded request."
        )

    job_id = str(uuid.uuid4())
    ingestion_jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "total_files": len(extracted_file_items),
        "processed_files": 0,
        "failed_files": 0,
        "details": []
    }

    background_tasks.add_task(process_bulk_ingestion_job, job_id, extracted_file_items, db_pool)

    return {
        "message": "Bulk ingestion job queued successfully.",
        "job_id": job_id,
        "total_files_queued": len(extracted_file_items),
        "status_check_url": f"/api/v1/standards/ingest-job/{job_id}"
    }


@router.get("/ingest-job/{job_id}")
async def get_bulk_ingestion_status(job_id: str):
    job_status = ingestion_jobs_db.get(job_id)
    if not job_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job ID not found.")
    return job_status