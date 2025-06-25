# === api/db/init_db.py ===

"""Database initialization script for the Payment Service."""

import asyncio
from sqlalchemy import text

from api.db.session import engine
from api.models.base import Base
# Make sure all models are imported so Base knows about them
from api.models.payment import Payment

async def init_db() -> None:
    """
    Initialize the database schema for the Payment Service.

    This function ensures that the required schema exists and
    creates all database tables defined by the SQLAlchemy models.
    """
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "payment"'))
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    """
    Entry point for initializing the database.
    """
    print("Initializing payment service database...")
    await init_db()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())