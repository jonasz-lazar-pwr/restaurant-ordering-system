# === api/models/order.py ===

"""SQLAlchemy model representing a customer order in the staff service."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import Base
from ..core.config import settings
from .order_status import OrderStatus


class Order(Base):
    """
    Represents a customer order visible to the restaurant staff.

    Attributes:
        id (int): Unique identifier of the order.
        table_number (str): Number of the table associated with the order.
        status (OrderStatus): Current status of the order.
        created_at (datetime): Timestamp when the order was created.
        items (List[OrderItem]): Items that belong to this order.
    """

    __tablename__ = "orders"
    __table_args__ = {"schema": settings.STAFF_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True)
    table_number = Column(String, index=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", lazy="selectin")
