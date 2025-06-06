# === api/utils/producer.py ===

"""
RabbitMQ publishing utility for the Staff Service.

This module defines helper functions for publishing messages
to RabbitMQ exchanges used for inter-service communication.

Supported operations:
- Sending order status updates (e.g. in_progress, ready, delivered).

Exchanges and routing keys are configured via environment variables:
- RABBITMQ_URL
- NOTIFICATIONS_EXCHANGE_NAME
- NOTIFICATIONS_ROUTING_KEY
"""

import json
import aio_pika

from api.core.config import settings


async def send_order_status_notification(order_id: int, new_status: str) -> None:
    """
    Publish a notification about an order status change.

    This function sends a message with the order ID and new status
    to the notifications exchange to inform other services (e.g. notification-service).

    Environment variables used:
        - RABBITMQ_URL
        - NOTIFICATIONS_EXCHANGE_NAME
        - NOTIFICATIONS_ROUTING_KEY

    Args:
        order_id (int): The ID of the order whose status has changed.
        new_status (str): The new status assigned to the order.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.get_exchange(
        settings.NOTIFICATIONS_EXCHANGE_NAME, ensure=True
    )

    payload = json.dumps({
        "order_id": order_id,
        "new_status": new_status
    }).encode()

    await exchange.publish(
        aio_pika.Message(body=payload),
        routing_key=settings.NOTIFICATIONS_ROUTING_KEY
    )

    await connection.close()
