# === api/db/deps.py ===

"""Database dependency injection utilities for FastAPI routes."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from api.db.session import async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a new asynchronous database session.

    This dependency manages the session lifecycle for a single request.
    It automatically commits the transaction if the request is successful,
    or rolls it back if an exception occurs.
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