# === api/utils/rabbitmq.py ===

"""
RabbitMQ publishing utility for the Order Service.

This module provides helper functions for publishing messages
to RabbitMQ exchanges used in inter-service communication.

Supported operations:
- Publishing a new order to the payments exchange for payment processing.
- Sending order status updates to the notifications exchange.

Environment variables:
    - RABBITMQ_URL
    - PAYMENTS_EXCHANGE_NAME
    - ROUTING_KEY_PAYMENT_INITIATED
    - NOTIFICATIONS_EXCHANGE_NAME
"""

import json
import aio_pika

from api.core.config import settings


async def send_order_to_payment(order_id: int) -> None:
    """Publish a message to the payments exchange indicating that payment is initiated.

    Args:
        order_id (int): The ID of the order to be paid.

    Raises:
        aio_pika.exceptions.AMQPError: If connection or publishing fails.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.get_exchange(settings.PAYMENTS_EXCHANGE_NAME, ensure=True)

    payload = json.dumps({"order_id": order_id}).encode()

    await exchange.publish(
        aio_pika.Message(body=payload),
        routing_key=settings.ROUTING_KEY_PAYMENT_INITIATED
    )

    await connection.close()


async def send_order_status_notification(order_id: int, new_status: str) -> None:
    """Publish a message to the notifications exchange about an order status change.

    This function dynamically builds a routing key as "order.<status>",
    e.g. "order.paid", "order.cancelled", etc.

    Args:
        order_id (int): The ID of the order whose status changed.
        new_status (str): The new status assigned to the order (must match OrderStatus enum).

    Raises:
        aio_pika.exceptions.AMQPError: If connection or publishing fails.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.get_exchange(settings.NOTIFICATIONS_EXCHANGE_NAME, ensure=True)

    routing_key = f"order.{new_status}"

    payload = json.dumps({
        "order_id": order_id,
        "new_status": new_status
    }).encode()

    await exchange.publish(
        aio_pika.Message(body=payload),
        routing_key=routing_key
    )

    await connection.close()
