# === api/models/payment.py ===

"""SQLAlchemy ORM model for storing payment details."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base
from api.core.config import settings

class Payment(Base):
    """Represents a payment transaction.

    Attributes:
        id (UUID): Primary key.
        order_id (int): The internal order ID from the Order Service.
        payu_order_id (str): The order ID returned by PayU.
        status (str): The current status of the payment (e.g., "PENDING", "COMPLETED").
        payment_link (str): The redirect URL for the customer to complete payment.
        created_at (datetime): Timestamp of when the record was created.
    """
    __tablename__ = "payments"
    __table_args__ = {"schema": settings.PAYMENT_SERVICE_DB_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    payu_order_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    payment_link: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())