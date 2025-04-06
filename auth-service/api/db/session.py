# api/db/session.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from api.core.config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.AUTH_SERVICE_DB_USER}:{settings.AUTH_SERVICE_DB_PASSWORD}"
    f"@{settings.AUTH_SERVICE_DB_HOST}:{settings.AUTH_SERVICE_DB_PORT}/{settings.AUTH_SERVICE_DB_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)