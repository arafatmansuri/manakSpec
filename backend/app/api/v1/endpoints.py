from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from asyncpg import Connection
from typing import Optional
from app.core.db import get_db_connection
from app.schemas.response import RecommendationOutput
from app.services.session_service import session_service
from app.services.parser import document_parser
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