import asyncio
from sqlalchemy import text

from api.db.session import engine, async_session
from api.models.base import Base
from api.models.models import Payment
from api.core.config import settings

async def init_db():
    async with engine.begin() as conn:
        # Ensure schema exists
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.PAYMENT_SERVICE_DB_SCHEMA}"'))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def insert_sample_payments():
    async with async_session() as session:
        sample_payments = [
            Payment(
                order_id="order_001",
                payu_order_id="payu_001",
                amount=100.00,
                currency="PLN",
                status="PENDING"
            ),
            Payment(
                order_id="order_002",
                payu_order_id="payu_002",
                amount=150.50,
                currency="PLN",
                status="COMPLETED"
            ),
        ]
        session.add_all(sample_payments)
        await session.commit()

async def main():
    await init_db()
    await insert_sample_payments()

if __name__ == "__main__":
    asyncio.run(main())
