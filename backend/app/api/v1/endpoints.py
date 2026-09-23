import io
import zipfile
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from asyncpg import Connection, Pool
from typing import Dict, Optional, Any, List
from app.core.db import get_db_connection,get_db_pool
from app.schemas.response import RecommendationOutput,ChatHistoryResponse,CreateSessionRequest,CreateSessionResponse,SessionSummary,ChatMessageSchema
from app.services.session_service import session_service
from app.services.parser import document_parser
from app.services.ingester import bis_ingester
from app.agent.workflow import agent_executor

router = APIRouter()

@router.post("/recommend", response_model=RecommendationOutput)
async def recommend(
    session_id: str = Form(..., description="UUID of the active chat session"),
    user_id: str = Form(..., description="User ID associated with the session"),
    query_text: Optional[str] = Form(None, description="Optional text query or procurement prompt"),
    file: Optional[UploadFile] = File(None, description="Optional PDF or image tender document upload"),
    conn: Connection = Depends(get_db_connection)
):
    if not query_text and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a query text, attach a document (PDF/Image), or both."
        )

    extracted_file_text = ""
    
    # 1. Document Extraction
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

    # 2. Combine Inputs into Prompt
    combined_query_parts = []
    if query_text and query_text.strip():
        combined_query_parts.append(f"User Instruction: {query_text.strip()}")
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

        # 4. Invoke Agent Execution Graph
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

@router.post("/sessions", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: CreateSessionRequest,
    conn: Connection = Depends(get_db_connection)
):
    """
    Initializes a new user_id if not provided, creates a new chat session in Postgres,
    and returns the session details.
    """
    user_id = payload.user_id or str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    title = payload.title or "New Chat"

    # 1. Insert or ensure user exists in users table (if applicable)
    upsert_user_sql = """
        INSERT INTO users (user_id) 
        VALUES ($1) 
        ON CONFLICT (user_id) DO NOTHING;
    """
    await conn.execute(upsert_user_sql, user_id)

    # 2. Insert new session record
    create_session_sql = """
        INSERT INTO chat_sessions (session_id, user_id, title, created_at, updated_at)
        VALUES ($1, $2, $3, NOW(), NOW())
        RETURNING created_at;
    """
    created_at = await conn.fetchval(create_session_sql, session_id, user_id, title)

    return CreateSessionResponse(
        user_id=user_id,
        session_id=session_id,
        title=title,
        created_at=created_at
    )


@router.get("/users/{user_id}/sessions", response_model=List[SessionSummary])
async def get_user_sessions(
    user_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Retrieves all historical chat sessions for a specific user to populate the sidebar.
    """
    fetch_sessions_sql = """
        SELECT 
            session_id, 
            title, 
            created_at, 
            updated_at
        FROM chat_sessions
        WHERE user_id = $1
        ORDER BY updated_at DESC;
    """
    rows = await conn.fetch(fetch_sessions_sql, user_id)

    return [
        SessionSummary(
            session_id=row["session_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        for row in rows
    ]


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_session_chat_history(
    session_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Fetches the session title and all chronological chat messages for a specific thread.
    """
    # 1. Fetch session title and verify existence
    fetch_session_sql = """
        SELECT title FROM chat_sessions WHERE session_id = $1;
    """
    title = await conn.fetchval(fetch_session_sql, session_id)

    if title is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' was not found."
        )

    # 2. Fetch messages ordered chronologically
    fetch_messages_sql = """
        SELECT 
            message_id, 
            role, 
            content, 
            execution_provider, 
            created_at
        FROM chat_messages
        WHERE session_id = $1
        ORDER BY created_at ASC;
    """
    rows = await conn.fetch(fetch_messages_sql, session_id)

    messages = [
        ChatMessageSchema(
            message_id=row["message_id"],
            role=row["role"],
            content=row["content"],
            execution_provider=row["execution_provider"],
            created_at=row["created_at"]
        )
        for row in rows
    ]

    return ChatHistoryResponse(
        session_id=session_id,
        title=title,
        messages=messages
    )