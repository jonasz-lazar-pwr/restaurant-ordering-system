# === api/workers/consumer.py ===

"""
RabbitMQ consumer for processing incoming notification events.

Consumes messages from the notification queue, deserializes the payload,
stores it in the database, and sends it via AWS SNS.
"""

import json
from typing import cast

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import async_session
from api.models.notification import Notification
from api.services.sns import send_notification_to_sns
from api.core.config import settings


async def handle_notification_message(payload: dict, db: AsyncSession) -> None:
    """Process a single notification message.

    Args:
        payload (dict): Incoming notification data.
        db (AsyncSession): Database session.
    """
    print(f"[DEBUG] Received payload: {payload}")

    test_email = settings.DEFAULT_NOTIFICATION_EMAIL

    # Sprawdź, czy klucz 'email' istnieje
    # if "email" not in payload:
    #     raise ValueError("Missing 'email' in payload")
    #
    # if "order_id" not in payload:
    #     raise ValueError("Missing 'order_id' in payload")
    #
    # if "new_status" not in payload:
    #     raise ValueError("Missing 'new_status' in payload")

    subject = f"Status update for order #{payload['order_id']}"
    message = f"Your order status changed to: {payload['status']}."
    print(f"[DEBUG] Constructed subject: {subject}")
    print(f"[DEBUG] Constructed message: {message}")

    notification = Notification(
        recipient_email=test_email,
        subject=subject,
        message=message,
        status="sent"
    )

    print(f"[DEBUG] Sending notification to SNS for email: {test_email}")
    send_notification_to_sns(test_email, notification.message)

    print(f"[DEBUG] Adding notification to DB: {notification}")
    db.add(notification)
    await db.commit()
    print("[DEBUG] Notification committed to DB.")


async def start_notification_consumer() -> None:
    """Start consuming messages from the RabbitMQ notification queue."""
    print("[INFO] Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.NOTIFICATION_QUEUE, durable=True)
    print(f"[INFO] Connected. Waiting for messages on queue: {settings.NOTIFICATION_QUEUE}")

    async with async_session() as db:
        async for raw_msg in queue.iterator():
            message = cast(AbstractIncomingMessage, raw_msg)
            async with message.process():
                try:
                    raw_body = message.body.decode("utf-8")
                    print(f"[DEBUG] Raw message body: {raw_body}")
                    payload = json.loads(raw_body)
                    await handle_notification_message(payload, db)
                except Exception as e:
                    print(f"[ERROR] Failed to process message: {e}")
