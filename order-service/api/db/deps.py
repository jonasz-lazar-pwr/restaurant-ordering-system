# === api/db/deps.py ===

"""Database dependency injection utilities for FastAPI routes.

Provides asynchronous database session management using SQLAlchemy.
"""

from api.db.session import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import AsyncGenerator


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an asynchronous database session.

    This dependency is used in FastAPI routes to provide access
    to the database within a request scope. The session is
    automatically closed after the request is completed.

    Yields:
        AsyncSession: A SQLAlchemy asynchronous database session.
    """
    async with async_session() as session:
        yield session
