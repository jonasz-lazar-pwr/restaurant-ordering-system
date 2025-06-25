# === api/db/deps.py ===

"""Database dependency injection utilities for FastAPI routes.

Provides asynchronous database session management using SQLAlchemy.

The session is committed if the operation succeeds, or rolled back
and closed in case of an exception. This ensures transactional safety
within FastAPI request scopes.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.session import async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a new asynchronous database session.

    This dependency manages the session lifecycle for a single request.
    It automatically commits the transaction if the request is successful,
    or rolls it back if an exception occurs.

    Yields:
        AsyncSession: A SQLAlchemy asynchronous database session.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
