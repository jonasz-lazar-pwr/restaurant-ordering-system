import asyncio
from api.db.session import engine
from api.models.base import Base
from api.models.user import User # Nie usuwać, bo jest potrzebny do utworzenia tabeli!!!

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
