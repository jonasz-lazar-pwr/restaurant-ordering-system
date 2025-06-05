# === api/models/order.py ===

"""SQLAlchemy model representing a customer order in the restaurant system."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from api.core.config import settings
from api.models.base import Base
from api.models.order_status import OrderStatus
from api.schemas.order import PaymentMethod


class Order(Base):
    """
    Represents an order placed by a customer.

    Attributes:
        id (int): Unique identifier for the order.
        table_number (str): Identifier of the table where the order was placed.
        user_id (str): ID of the user who placed the order.
        status (OrderStatus): Current status of the order (e.g., pending, paid).
        payment_method (PaymentMethod): Selected method of payment (cash or online).
        comment (str): Optional comment or notes added by the customer.
        created_at (datetime): Timestamp of when the order was created.
        items (List[OrderItem]): List of ordered items in this order.
    """
    __tablename__ = "orders"
    __table_args__ = {"schema": settings.ORDER_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String, index=True)
    user_id = Column(String, index=True, nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.pending, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete")
