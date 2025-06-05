# === api/models/table_session.py ===

"""SQLAlchemy model representing a user's assigned table after scanning a QR code."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime
from api.models.base import Base
from api.core.config import settings


class TableSession(Base):
    """
    Stores the table assignment for a user who scanned a QR code.

    Attributes:
        user_id (str): ID of the authenticated user.
        table_number (str): Number of the table scanned.
        created_at (datetime): Timestamp of session creation.
    """
    __tablename__ = "table_sessions"
    __table_args__ = {"schema": settings.ORDER_SERVICE_DB_SCHEMA}

    user_id = Column(String, primary_key=True, index=True)
    table_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
