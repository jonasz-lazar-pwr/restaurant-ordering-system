# api/db/init_db.py

import asyncio
from sqlalchemy import text
from api.db.session import engine
from api.models.base import Base
from api.models.user import User # Ten import jest potrzebny, żeby model się zarejestrował

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
