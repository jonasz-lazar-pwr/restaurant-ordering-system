import asyncio
from sqlalchemy import text

from api.db.session import engine, async_session
from api.models.base import Base
from api.models.models import Payment
from api.core.config import settings

async def init_db() -> None:
    async with engine.begin() as conn:
        # Ensure schema exists
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.PAYMENT_SERVICE_DB_SCHEMA}"'))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def insert_sample_payments() -> None:
    async with async_session() as session:
        sample_payments = [
            Payment(
                payu_order_id="payu_001",
                amount="10000",
                currency="PLN",
                status="NEW",
                table_number = "99",
                user_id = "99"
            ),
            Payment(
                payu_order_id="payu_002",
                amount="15050",
                currency="PLN",
                status="COMPLETED",
                table_number = "00",
                user_id = "00"
            ),
        ]
        session.add_all(sample_payments)
        await session.commit()

async def main() -> None:
    await init_db()
    await insert_sample_payments()

if __name__ == "__main__":
    asyncio.run(main())
