# api/db/session.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
# from sqlalchemy.engine.url import URL
from api.core.config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Set the PostgreSQL search_path to use schema "order"
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"server_settings": {"search_path": settings.ORDER_SERVICE_DB_SCHEMA}},
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)