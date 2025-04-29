import asyncio
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .models import Base, MenuItem, Order

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@database:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_schema():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS order_service"))
        print("Schema 'order_service' created (or already exists).")

async def init_db():
    await create_schema()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

async def main():
    await init_db()

async def get_db():
    async with SessionLocal() as db:
        yield db

if __name__ == "__main__":
    asyncio.run(main())
