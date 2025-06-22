# === api/workers/producer.py ===

"""
RabbitMQ publishing utility for the Order Service.
"""

import json
import aio_pika
from api.core.config import settings

async def send_order_status_notification(order_id: int, new_status: str, email: str) -> None:
    """Send a message to the notification service queue about an order status update.

    Args:
        order_id (int): The ID of the order being updated.
        new_status (str): The new status assigned to the order (e.g., "paid", "ready").
        email (str): Email address to notify about the order status change.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()

        payload = json.dumps({
            "order_id": order_id,
            "new_status": new_status,
            "email": email
        }).encode()

        await channel.default_exchange.publish(
            aio_pika.Message(body=payload),
            routing_key=settings.NOTIFICATION_QUEUE
        )