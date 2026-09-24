import io
import zipfile
import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Response
from asyncpg import Connection, Pool
from typing import Dict, Optional, Any, List
from app.core.db import get_db_connection,get_db_pool
from app.schemas.response import RecommendationOutput
from app.services.session_service import session_service
from app.services.parser import document_parser
from app.services.ingester import bis_ingester
from app.services.exporter import tender_exporter
from app.agent.workflow import agent_executor

router = APIRouter()

@router.post("/recommend", response_model=RecommendationOutput)
async def recommend(
    session_id: str = Form(..., description="UUID of the active chat session"),
    user_id: str = Form(..., description="User ID associated with the session"),
    query_text: Optional[str] = Form(None, description="Optional text query or procurement prompt"),
    file: Optional[UploadFile] = File(None, description="Optional PDF, DOCX, TXT, or image tender document upload"),
    language: Optional[str] = Form(None, description="Optional preferred output language (e.g. 'Hindi', 'Gujarati', 'Tamil', 'English')"),
    conn: Connection = Depends(get_db_connection)
):
    if not query_text and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a query text, attach a document (PDF/DOCX/TXT/Image), or both."
        )

    extracted_file_text = ""
    
    # 1. Document Extraction (.pdf, .docx, .txt, images)
    if file:
        contents = await file.read()
        filename = file.filename.lower() if file.filename else ""

        if filename.endswith(".pdf"):
            extracted_file_text = document_parser.extract_text_from_pdf(contents)
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            extracted_file_text = document_parser.extract_text_from_image(contents)
        elif filename.endswith(".docx"):
            extracted_file_text = document_parser.extract_text_from_docx(contents)
        elif filename.endswith((".txt", ".csv")):
            extracted_file_text = document_parser.extract_text_from_txt(contents)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Please upload PDF, Word (.docx), TXT, or image files."
            )

        if not extracted_file_text and not query_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract legible text from the uploaded document."
            )

    # 2. Combine Inputs into Prompt
    combined_query_parts = []
    if query_text and query_text.strip():
        combined_query_parts.append(query_text.strip())
    if extracted_file_text and extracted_file_text.strip():
        combined_query_parts.append(f"Extracted Document Content:\n{extracted_file_text.strip()}")
    
    full_prompt = "\n\n".join(combined_query_parts)

    try:
        # 3. Retrieve Session & Chat History
        session_info = await session_service.get_or_create_session(conn, session_id, user_id)
        active_session_id = session_info["session_id"]
        verified_user_id = session_info["user_id"]
        current_title = session_info.get("title", "New Chat")

        chat_history = await session_service.get_recent_history(conn, active_session_id)
        
        # Log User Query
        await session_service.save_message(conn, active_session_id, "user", full_prompt)

        # 4. Invoke Agent Execution Graph with Multilingual Context
        initial_state = {
            "raw_query": full_prompt,
            "chat_history": chat_history,
            "expanded_query": "",
            "detected_language": "",
            "target_language": language or "",
            "english_query": "",
            "retrieved_data": {},
            "final_output": None,
            "execution_provider": "",
            "db_conn": conn
        }
        
        result = await agent_executor.ainvoke(initial_state)
        structured_synthesis = result["final_output"]
        detected_language = result.get("detected_language", "English")

        # 5. Auto-Title Session (First Turn Check)
        if current_title in [None, "New Chat", ""]:
            primary_stds = result["retrieved_data"].get("primary_standards", [])
            if primary_stds and len(primary_stds) > 0:
                top_std = primary_stds[0]
                std_num = top_std.get("is_number", "")
                std_title = top_std.get("title", "")[:30]
                new_title = f"{std_num} - {std_title}".strip(" -")
            else:
                raw_prompt = query_text or "Document Procurement Query"
                new_title = raw_prompt[:35] + "..." if len(raw_prompt) > 35 else raw_prompt

            await session_service.update_session_title(conn, active_session_id, new_title)

        # 6. Log Assistant Synthesis
        await session_service.save_message(
            conn, 
            active_session_id, 
            "assistant", 
            structured_synthesis.model_dump_json(),
        )

        # 7. Construct & Return Final Output Payload
        return RecommendationOutput(
            session_id=active_session_id,
            user_id=verified_user_id,
            detected_language=detected_language,
            query_expansion_used=result["expanded_query"],
            allied_references=result["retrieved_data"]["allied_references"],
            structured_synthesis=structured_synthesis,
            execution_provider=result["execution_provider"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing procurement request: {str(e)}"
        )


@router.get("/export/message/{message_id}")
async def export_tender_message(
    message_id: str,
    format: str = "docx",
    conn: Connection = Depends(get_db_connection)
):
    """
    Direct alias endpoint to export a specific chat message/response by message_id
    into PDF, DOCX, TXT, or Markdown formats.
    """
    return await export_tender_schedule(identifier=message_id, format=format, conn=conn)


@router.get("/export/{identifier}")
async def export_tender_schedule(
    identifier: str,
    chat_id: Optional[str] = None,
    format: str = "docx",
    conn: Connection = Depends(get_db_connection)
):
    """
    Exports a BIS technical recommendation and tender specification schedule 
    as a downloadable PDF, Word (.docx), Plain Text (.txt), or Markdown (.md) document.

    Can accept:
    - identifier: either a specific chat_id/message_id (e.g. '12') OR a session UUID.
    - chat_id (optional query param): explicitly specifies which message/response turn to download.
    - format: 'pdf', 'docx', 'txt', or 'md' (default: 'docx')
    """
    # 1. Determine whether fetching a specific message (chat_id) or the latest message of a session
    target_message_id = None
    if chat_id and chat_id.strip():
        target_message_id = chat_id.strip()
    elif identifier.strip().isdigit():
        target_message_id = identifier.strip()

    if target_message_id is not None:
        # Fetch specific response turn by message ID
        query = """
            SELECT 
                cm.id, 
                cm.session_id, 
                cm.role, 
                cm.content, 
                COALESCE(cs.title, 'Tender BIS Specification Schedule') as title
            FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.session_id
            WHERE cm.id = $1::integer;
        """
        row = await conn.fetchrow(query, int(target_message_id))
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Chat message with ID '{target_message_id}' not found."
            )
        if row["role"] != "assistant":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message '{target_message_id}' is a user query, not an assistant recommendation."
            )
    else:
        # Fetch latest assistant recommendation for the session_id
        query = """
            SELECT 
                cm.id, 
                cm.session_id, 
                cm.role, 
                cm.content, 
                COALESCE(cs.title, 'Tender BIS Specification Schedule') as title
            FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.session_id
            WHERE cm.session_id = $1::uuid AND cm.role = 'assistant'
            ORDER BY cm.created_at DESC 
            LIMIT 1;
        """
        try:
            row = await conn.fetchrow(query, identifier)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid identifier '{identifier}'. Please provide a valid session UUID or message integer ID."
            )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No generated recommendation found for session '{identifier}'."
            )

    # 2. Parse synthesis content
    raw_content = row["content"]
    if isinstance(raw_content, str):
        try:
            content_data = json.loads(raw_content)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to parse saved session recommendation.")
    else:
        content_data = raw_content

    # 3. Format filename
    title = row["title"] or "Tender BIS Specification Schedule"
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")[:35] or "Tender_BIS_Spec"
    msg_id = row["id"]
    filename_base = f"{safe_title}_chat_{msg_id}"

    # 4. Generate requested format: PDF, DOCX, TXT, or MD
    fmt = format.lower().strip()
    if fmt == "pdf":
        pdf_bytes = tender_exporter.generate_pdf(content_data, title=title)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'}
        )
    elif fmt == "docx":
        docx_bytes = tender_exporter.generate_docx(content_data, title=title)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.docx"'}
        )
    elif fmt == "txt":
        txt_content = tender_exporter.generate_text(content_data, title=title)
        return Response(
            content=txt_content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.txt"'}
        )
    else:
        md_text = tender_exporter.generate_markdown(content_data, title=title)
        return Response(
            content=md_text,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.md"'}
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