# api/db/deps.py

from .session import async_session

async def get_db():
    async with async_session() as session:
        yield session
