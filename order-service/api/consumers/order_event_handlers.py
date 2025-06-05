# === api/consumers/order_event_handlers.py ===

import json
from aio_pika.abc import AbstractIncomingMessage
from typing import Callable, Coroutine, Any
from api.db.session import async_session
from api.models import Order, OrderStatus
from api.utils.rabbitmq import send_order_status_notification


async def handle_order_paid_event(message: AbstractIncomingMessage) -> None:
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


def get_handler_for_status(status: OrderStatus) -> Callable[[AbstractIncomingMessage], Coroutine[Any, Any, None]]:
    """Return the appropriate handler for a given OrderStatus."""
    match status:
        case OrderStatus.paid:
            return handle_order_paid_event
        # tutaj później dodasz inne, np. cancelled/failed
        case _:
            raise NotImplementedError(f"No handler implemented for status: {status}")
