import asyncpg
from typing import Optional, Dict, Any, List

class SessionService:
    async def get_or_create_session(
        self, 
        conn: asyncpg.Connection, 
        session_id: Optional[str] = None, 
        user_id: str = "anonymous_user"
    ) -> str:
        """Validates or creates a session UUID inside the chat_sessions table."""
        if session_id:
            row = await conn.fetchrow(
                "SELECT session_id FROM chat_sessions WHERE session_id = $1::uuid;", 
                session_id
            )
            if row:
                return str(row["session_id"])

        # Insert requires user_id as per schema constraint
        new_row = await conn.fetchrow(
            "INSERT INTO chat_sessions (user_id) VALUES ($1) RETURNING session_id;",
            user_id
        )
        return str(new_row["session_id"])

    async def save_message(self, conn: asyncpg.Connection, session_id: str, role: str, content: str):
        """Inserts a user query or assistant response into chat_messages."""
        await conn.execute(
            """
            INSERT INTO chat_messages (session_id, role, content)
            VALUES ($1::uuid, $2, $3);
            """,
            session_id, role, content
        )
        # Touch updated_at on the session
        await conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = $1::uuid;",
            session_id
        )

    async def get_recent_history(self, conn: asyncpg.Connection, session_id: str, limit: int = 6) -> List[Dict[str, str]]:
        """Fetches recent conversation turns using role and content columns."""
        rows = await conn.fetch(
            """
            SELECT role, content 
            FROM chat_messages 
            WHERE session_id = $1::uuid 
            ORDER BY created_at DESC 
            LIMIT $2;
            """,
            session_id, limit
        )
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

session_service = SessionService()