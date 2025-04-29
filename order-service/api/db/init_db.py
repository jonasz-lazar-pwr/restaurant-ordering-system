# api/db/init_db.py

import asyncio
from sqlalchemy import text
from api.db.session import engine
from api.models.base import Base
from api.db.session import async_session
from api.models.models import MenuItem, Order

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "order"'))
        await conn.run_sync(Base.metadata.create_all)

async def insert_sample_items():
    async with async_session() as session:
        sample_items = [
            MenuItem(name="Pizza Margherita", description="Classic pizza with tomato, mozzarella, and basil", price=12.50),
            MenuItem(name="Spaghetti Carbonara", description="Spaghetti with creamy carbonara sauce and pancetta", price=14.00),
            MenuItem(name="Caesar Salad", description="Fresh salad with romaine, croutons, and Caesar dressing", price=8.00),
        ]
        session.add_all(sample_items)
        await session.commit()

async def main():
    await init_db()
    await insert_sample_items()

if __name__ == "__main__":
    asyncio.run(main())
