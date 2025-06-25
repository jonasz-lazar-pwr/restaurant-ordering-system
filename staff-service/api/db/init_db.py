# === api/db/init_db.py ===

"""Database initialization script for the Staff Service.

This module sets up the database schema and inserts initial sample menu items
for testing and development purposes.
"""

import asyncio
from sqlalchemy import text

from api.db.session import engine, async_session
from api.models import Base
from api.models import Order
from api.models import OrderItem
from api.models import OrderStatus


async def init_db() -> None:
    """
    Initialize the database schema for the Staff Service.

    This function ensures that the required schema exists and
    creates all database tables defined by the SQLAlchemy models.
    """
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "staff"'))
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    """
    Entry point for initializing the database and inserting sample data.
    """
    await init_db()


if __name__ == "__main__":
    asyncio.run(main())
