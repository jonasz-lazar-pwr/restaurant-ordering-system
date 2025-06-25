# === api/db/init_db.py ===

"""Database initialization script for the Order Service.

This module sets up the database schema and inserts initial sample menu items
for testing and development purposes.
"""

import asyncio
from sqlalchemy import text

from api.db.session import engine, async_session
from api.models.base import Base
from api.models.menu_item import MenuItem
from api.models.order import Order
from api.models.order_item import OrderItem
from api.models.order_status import OrderStatus
from api.models.payment_method import PaymentMethod
from api.models.table_session import TableSession


async def init_db() -> None:
    """
    Initialize the database schema for the Order Service.

    This function ensures that the required schema exists and
    creates all database tables defined by the SQLAlchemy models.
    """
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "order"'))
        await conn.run_sync(Base.metadata.create_all)


async def insert_sample_items() -> None:
    """
    Insert predefined sample menu items into the database.

    This is useful for local testing or development purposes.
    """
    async with async_session() as session:
        sample_items = [
            MenuItem(
                name="Pizza Margherita",
                description="Classic pizza with tomato, mozzarella, and basil",
                price=12.50
            ),
            MenuItem(
                name="Spaghetti Carbonara",
                description="Spaghetti with creamy carbonara sauce and pancetta",
                price=14.00
            ),
            MenuItem(
                name="Caesar Salad",
                description="Fresh salad with romaine, croutons, and Caesar dressing",
                price=8.00
            ),
        ]
        session.add_all(sample_items)
        await session.commit()


async def main() -> None:
    """
    Entry point for initializing the database and inserting sample data.
    """
    await init_db()
    await insert_sample_items()


if __name__ == "__main__":
    asyncio.run(main())
