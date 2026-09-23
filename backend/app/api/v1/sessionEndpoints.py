import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, status
from asyncpg import Connection
from typing import List
from app.core.db import get_db_connection,get_db_pool
from app.schemas.response import ChatHistoryResponse,CreateSessionRequest,CreateSessionResponse,SessionSummary,ChatMessageSchema

router = APIRouter()
@router.post("/", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/{user_id}", response_model=List[SessionSummary])
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
            session_id=str(row["session_id"]),
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        for row in rows
    ]


@router.get("/chat/{session_id}", response_model=ChatHistoryResponse)
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
            id, 
            role, 
            content, 
            created_at
        FROM chat_messages
        WHERE session_id = $1
        ORDER BY created_at ASC;
    """
    rows = await conn.fetch(fetch_messages_sql, session_id)

    messages = [
        ChatMessageSchema(
            message_id=str(row["id"]),
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"]
        )
        for row in rows
    ]

    return ChatHistoryResponse(
        session_id=session_id,
        title=title,
        messages=messages
    )