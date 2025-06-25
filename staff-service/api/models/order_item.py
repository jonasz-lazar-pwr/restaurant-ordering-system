# === api/models/order_item.py ===

"""SQLAlchemy model representing a single item within a customer order."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from ..core.config import settings


class OrderItem(Base):
    """
    Represents an item in a customer's order.

    Attributes:
        id (int): Unique identifier of the order item.
        order_id (int): Foreign key referencing the parent order.
        menu_item_id (int): ID of the menu item associated with this entry.
        quantity (int): Number of units ordered for the given item.
        order (Order): Relationship to the parent order.
    """

    __tablename__ = "order_items"
    __table_args__ = {"schema": settings.STAFF_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer,
        ForeignKey(f"{settings.STAFF_SERVICE_DB_SCHEMA}.orders.id", ondelete="CASCADE"),
        nullable=False
    )
    menu_item_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
