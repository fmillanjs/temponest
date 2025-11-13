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
        """Create connection pool with optimized settings"""
        if not self.pool:
            # OPTIMIZED: Tuned connection pool for auth service (high traffic)
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=10,              # Increased from 5 (auth is high-traffic)
                max_size=50,              # Increased from 20 (handle bursts)
                max_queries=50000,        # NEW: Recycle connections after 50k queries
                max_inactive_connection_lifetime=300.0,  # NEW: Close idle connections after 5 min
                command_timeout=30,       # Reduced from 60 (fail fast)
                timeout=10.0,             # NEW: Max wait time for connection from pool
                setup=self._setup_connection  # NEW: Connection setup hook
            )
            print(f"✅ Database connected: {settings.DATABASE_URL.split('@')[1]} (pool: 10-50)")

    async def _setup_connection(self, conn: asyncpg.Connection):
        """Setup connection with optimized settings"""
        # Set statement timeout to prevent long-running queries
        await conn.execute("SET statement_timeout = '30s'")
        # Set idle_in_transaction_session_timeout to prevent blocking
        await conn.execute("SET idle_in_transaction_session_timeout = '60s'")

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
