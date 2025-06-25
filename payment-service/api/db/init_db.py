# === api/db/init_db.py ===

"""Database initialization script for the Payment Service.

Creates schema, tables and inserts development sample data if necessary.
"""

import asyncio
from sqlalchemy import text
from api.db.session import engine, async_session
from api.models.base import Base
from api.models.payment import Payment  # Ensure correct model import
from api.core.config import settings


async def init_db() -> None:
    """
    Initialize the database schema for the Payment Service.

    Ensures the required schema exists and creates all tables.
    """
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.PAYMENT_SERVICE_DB_SCHEMA}"'))
        await conn.run_sync(Base.metadata.create_all)


async def insert_sample_payments() -> None:
    """
    Insert example payment records into the database.
    """
    async with async_session() as session:
        sample_payments = [
            Payment(
                order_id="00",
                payu_order_id="payu_001",
                amount="10000",
                currency="PLN",
                status="NEW",
                table_number="00",
                user_id="00"
            ),
            Payment(
                order_id="01",
                payu_order_id="payu_002",
                amount="15050",
                currency="PLN",
                status="COMPLETED",
                table_number="01",
                user_id="01"
            ),
        ]
        session.add_all(sample_payments)
        await session.commit()


async def main() -> None:
    """
    Entry point for initializing the database.
    """
    print("Initializing payment service database...")
    await init_db()
    await insert_sample_payments()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
