# === api/models/notification.py ===

"""SQLAlchemy ORM model for storing sent email notifications."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import Base


class Notification(Base):
    """Represents an email notification sent to a user.

    Attributes:
        id (UUID): Primary key.
        recipient_email (str): Email address of the recipient.
        subject (str): Subject line of the notification.
        message (str): Body content of the notification.
        status (str): Delivery status ("sent", "failed", etc.).
        created_at (datetime): Timestamp of when the notification was created.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
