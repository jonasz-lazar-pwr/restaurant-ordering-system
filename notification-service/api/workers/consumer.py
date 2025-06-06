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
    test_email = settings.DEFAULT_NOTIFICATION_EMAIL
    notification = Notification(
        recipient_email=payload["email"],
        subject=f"Status update for order #{payload['order_id']}",
        message=f"Your order status changed to: {payload['new_status']}.",
        status="sent"
    )

    send_notification_to_sns(test_email, notification.message)
    db.add(notification)
    await db.commit()


async def start_notification_consumer() -> None:
    """Start consuming messages from the RabbitMQ notification queue."""
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.NOTIFICATION_QUEUE, durable=True)

    async with async_session() as db:
        async for raw_msg in queue.iterator():
            message = cast(AbstractIncomingMessage, raw_msg)
            async with message.process():
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                    await handle_notification_message(payload, db)
                except Exception as e:
                    print(f"[!] Failed to process message: {e}")
