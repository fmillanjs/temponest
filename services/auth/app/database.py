"""
Database connection and utilities.
"""

import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
from app.settings import settings


class Database:
    """PostgreSQL database connection manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            print(f"✅ Database connected: {settings.DATABASE_URL.split('@')[1]}")

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("🔌 Database disconnected")

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def execute(self, query: str, *args):
        """Execute a query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch a single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch a single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def set_tenant_context(self, conn: asyncpg.Connection, tenant_id: str):
        """Set tenant context for Row-Level Security"""
        await conn.execute("SET app.current_tenant = $1", tenant_id)


# Global database instance
db = Database()
