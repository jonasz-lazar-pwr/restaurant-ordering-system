# api/db/deps.py

from api.db.session import async_session

async def get_db():
    async with async_session() as session:
        yield session
