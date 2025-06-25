# === api/schemas/notification.py ===

"""Pydantic schemas for validating and serializing email notification data.

Includes schemas used for:
- Creating new notifications (NotificationCreate)
- Reading stored notifications (NotificationRead)

These schemas are used for validating incoming data and serializing database
records returned by the notification service.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class NotificationCreate(BaseModel):
    """Schema for creating a new email notification.

    Attributes:
        recipient_email (EmailStr): Email address of the recipient.
        subject (str): Subject line of the notification email.
        message (str): Body content of the notification message.
    """

    recipient_email: EmailStr = Field(..., description="Target recipient's email address")
    subject: str = Field(..., max_length=255, description="Subject of the notification email")
    message: str = Field(..., description="Body content of the notification message")


class NotificationRead(BaseModel):
    """Schema for reading a stored email notification."""

    id: UUID = Field(..., description="Unique identifier of the notification")
    recipient_email: EmailStr = Field(..., description="Email address of the recipient")
    subject: str = Field(..., description="Subject of the notification")
    message: str = Field(..., description="Full message body")
    status: str = Field(..., description="Status of delivery (e.g., 'sent', 'failed')")
    created_at: datetime = Field(..., description="Timestamp of when the notification was created")

    class Config:
        from_attributes = True