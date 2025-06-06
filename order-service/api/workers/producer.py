# === api/utils/producer.py ===

"""
RabbitMQ publishing utility for the Order Service.

This module provides helper functions for sending messages
to other services via dedicated RabbitMQ queues (one per service).

Supported operations:
- Sending new order events to the payment service queue.
- Sending order status updates to the notification service queue.

Environment variables:
    - RABBITMQ_URL
    - PAYMENT_QUEUE
    - NOTIFICATION_QUEUE
"""

import json
import aio_pika

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.core.config import settings
from api.models import Order, OrderItem
from api.utils.payment_payload_builder import build_payment_payload


async def send_order_to_payment(order_id: int, db: AsyncSession, buyer_info: dict, customer_ip: str) -> None:
    """Send full payment payload to the payment service queue.

    Args:
        order_id (int): ID of the order to be paid.
        db (AsyncSession): SQLAlchemy async session.
        buyer_info (dict): Info about the buyer (email, phone, etc.).
        customer_ip (str): IP address of the customer placing the order.
    """
    # Load order and related items
    order = await db.get(Order, order_id)
    if not order:
        return

    result = await db.execute(
        select(OrderItem)
        .options(selectinload(OrderItem.menu_item))
        .where(OrderItem.order_id == order_id)
    )
    order_items = result.scalars().all()

    # Prepare menu item mapping
    menu_items = {item.menu_item_id: item.menu_item for item in order_items}

    # Build payment payload
    payment_payload = build_payment_payload(
        order=order,
        order_items=order_items,
        menu_items=menu_items,
        buyer=buyer_info,
        customer_ip=customer_ip,
        notify_url=settings.PAYMENT_NOTIFY_URL
    )

    # Publish to payment_service_queue
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()

        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(payment_payload).encode()),
            routing_key=settings.PAYMENT_QUEUE
        )


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
