# === api/models/order_item.py ===

"""SQLAlchemy model representing a single item in a customer order."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from api.models.base import Base
from api.core.config import settings


class OrderItem(Base):
    """
    Represents a single menu item in a customer order.

    Attributes:
        id (int): Unique identifier for the order item.
        order_id (int): Foreign key linking to the parent order.
        menu_item_id (int): Foreign key linking to the ordered menu item.
        quantity (int): Number of units of the menu item ordered.
        order (Order): Relationship to the parent Order object.
        menu_item (MenuItem): Relationship to the MenuItem object.
    """
    __tablename__ = "order_items"
    __table_args__ = {"schema": settings.ORDER_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer,
        ForeignKey(f"{settings.ORDER_SERVICE_DB_SCHEMA}.orders.id"),
        nullable=False
    )
    menu_item_id = Column(
        Integer,
        ForeignKey(f"{settings.ORDER_SERVICE_DB_SCHEMA}.menu_items.id"),
        nullable=False
    )
    quantity = Column(Integer, default=1, nullable=False)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")
