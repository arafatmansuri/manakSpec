from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid

from app.core.db import get_db_connection
from app.services.retrieval import search_relevant_standards
from app.services.llm_router import gemini_service
from app.services.extractor import extract_text_from_file_bytes

app = FastAPI(
    title="BIS Standards AI Procurement Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "BIS Standards Backend"}

@app.post("/api/agent/chat")
async def chat_endpoint(
    session_id: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    x_device_id: str = Header(default="anon_guest_device")
):
    """
    Accepts natural language text query, PDF file, or Image tender document.
    Extracted text is embedded and matched against Indian Standards in PostgreSQL.
    """
    # 1. Fallback for Session ID
    active_session_id = session_id or str(uuid.uuid4())
    user_query = message or ""

    # 2. Handle File Upload Processing (Online Extraction Engine)
    if file:
        try:
            file_bytes = await file.read()
            extracted_doc_text = extract_text_from_file_bytes(file_bytes, file.filename)
            # Combine user message with extracted PDF text
            if user_query:
                user_query = f"{user_query}\n\n[Uploaded Document Content - {file.filename}]:\n{extracted_doc_text}"
            else:
                user_query = f"[Uploaded Document Content - {file.filename}]:\n{extracted_doc_text}"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process document: {str(e)}")

    if not user_query.strip():
        raise HTTPException(status_code=400, detail="Please provide either a text query or a tender document.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 3. Store Anonymous Session State
        cursor.execute("""
            INSERT INTO chat_sessions (session_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (session_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;
        """, (active_session_id, x_device_id))

        # 4. Record User Message
        cursor.execute("""
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (%s, 'user', %s);
        """, (active_session_id, user_query))

        # 5. Retrieve Context Window (Last 4 Messages)
        cursor.execute("""
            SELECT role, content FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at DESC LIMIT 4;
        """, (active_session_id,))
        raw_history = cursor.fetchall()
        history_str = "\n".join([f"{r[0].capitalize()}: {r[1]}" for r in reversed(raw_history)])

        # 6. Real-time Query Vector Search (384-dim FastEmbed + HNSW pgvector)
        # Limit text length sent to embedding engine to avoid overflow
        query_for_embedding = user_query[:2000]
        db_results = search_relevant_standards(query_for_embedding)

        # 7. RAG Context Assembly
        context_str = f"--- CHAT HISTORY ---\n{history_str}\n\n--- RETRIEVED BIS STANDARDS ---\n"
        for std in db_results["primary_standards"]:
            context_str += f"- IS Code: {std['is_number']}\n  Title: {std['title']}\n  Mandatory QCO: {std['is_mandatory_qco']}\n  Scope: {std['scope_text']}\n"

        context_str += "\n--- NORMATIVE CROSS-REFERENCES ---\n"
        for rel in db_results["allied_references"]:
            context_str += f"- {rel['parent_is_number']} -> [{rel['relation_type']}] {rel['related_is_number']}: {rel['title_or_description']}\n"

        # 8. Gemini Synthesis
        llm_response = gemini_service.generate_response(user_query, context_str)

        # 9. Record Assistant Response
        cursor.execute("""
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (%s, 'assistant', %s);
        """, (active_session_id, llm_response))

        conn.commit()

        return {
            "session_id": active_session_id,
            "query_processed": user_query[:200] + ("..." if len(user_query) > 200 else ""),
            "retrieved_standards": db_results["primary_standards"],
            "allied_references": db_results["allied_references"],
            "recommendation": llm_response
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()