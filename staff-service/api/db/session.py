# === api/db/session.py ===

"""Asynchronous SQLAlchemy session and engine configuration.

This module configures the SQLAlchemy async engine and session factory
used by the Staff Service. It ensures the correct schema is used via
PostgreSQL's search_path setting.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from api.core.config import settings

# PostgreSQL DSN with asyncpg driver
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Create an async engine with explicit schema search_path
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL echoing for debugging
    connect_args={
        "server_settings": {
            "search_path": settings.STAFF_SERVICE_DB_SCHEMA
        }
    },
)

# Session factory for creating async sessions
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
