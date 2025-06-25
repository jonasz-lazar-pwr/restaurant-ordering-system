# === api/db/init_db.py ===

"""Database initialization script for the Notification Service.

This module sets up the database schema and inserts initial sample menu items
for testing and development purposes.
"""

import asyncio
from sqlalchemy import text

from api.db.session import engine
from api.models.base import Base
from api.models.notification import Notification

async def init_db() -> None:
    """
    Initialize the database schema for the Notification Service.

    This function ensures that the required schema exists and
    creates all database tables defined by the SQLAlchemy models.
    """
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "notification"'))
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    """
    Entry point for initializing the database and inserting sample data.
    """
    await init_db()

if __name__ == "__main__":
    asyncio.run(main())
