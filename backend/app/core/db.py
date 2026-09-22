import asyncpg
from app.core.config import settings
from typing import AsyncGenerator

class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=2,
            max_size=10
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()

async def get_db_pool() -> asyncpg.Pool:
    """Dependency helper to inject the connection pool into background workers."""
    if db.pool is None:
        raise RuntimeError("Database connection pool is not initialized.")
    return db.pool

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    if db.pool is None:
        raise RuntimeError("Database connection pool is not initialized.")
    async with db.pool.acquire() as connection:
        yield connection