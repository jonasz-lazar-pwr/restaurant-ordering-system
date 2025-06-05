# === api/consumers/order_event_handlers.py ===
"""RabbitMQ event handlers for incoming order-related messages.

This module defines asynchronous message consumers for handling
order events such as "order.paid". Each handler processes a message,
updates the database, and optionally triggers follow-up actions.
"""

import json
from typing import Callable, Coroutine, Any

from aio_pika.abc import AbstractIncomingMessage

from api.db.session import async_session
from api.models import Order, OrderStatus
from api.utils.rabbitmq import send_order_status_notification


async def handle_order_paid_event(message: AbstractIncomingMessage) -> None:
    """Handle the 'order.paid' event from the RabbitMQ queue.

    This function updates the order status to 'paid' if the order exists
    and is currently in the 'pending' state. It also triggers a notification
    by publishing a follow-up message to the notification exchange.

    Args:
        message (AbstractIncomingMessage): The incoming RabbitMQ message.
    """
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            order_id = payload.get("order_id")
            if not order_id:
                return

            async with async_session() as db:
                order = await db.get(Order, order_id)
                if not order or order.status != OrderStatus.pending:
                    return

                order.status = OrderStatus.paid
                await db.commit()
                await db.refresh(order)
                await send_order_status_notification(order.id, order.status.value)

        except Exception as e:
            print(f"[order.paid] Failed to process message: {e}")


def get_handler_for_status(
    status: OrderStatus,
) -> Callable[[AbstractIncomingMessage], Coroutine[Any, Any, None]]:
    """Return the appropriate handler function for a given order status.

    This is used to map specific order status events (e.g. 'paid', 'cancelled')
    to their corresponding RabbitMQ consumer handler.

    Args:
        status (OrderStatus): The status to handle.

    Returns:
        Callable: The asynchronous handler function for the given status.

    Raises:
        NotImplementedError: If no handler exists for the provided status.
    """
    match status:
        case OrderStatus.paid:
            return handle_order_paid_event
        # Add more cases below (e.g. cancelled, failed) as needed.
        case _:
            raise NotImplementedError(f"No handler implemented for status: {status}")
