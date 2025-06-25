# === order-service/api/workers/consumer.py ===

import json
from typing import cast
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.db.session import async_session
from api.models.order import Order
from api.core.config import settings

async def handle_message(payload: dict):
    """
    Handles an incoming message, dispatching to the correct logic
    based on the payload content (status update or payment link update).
    """
    async with async_session() as db:
        try:
            order_id = payload.get("order_id")
            if not order_id:
                print(f"[!] Invalid payload received (missing order_id): {payload}")
                return

            result = await db.execute(select(Order).filter(Order.id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                print(f"[!] Order with id {order_id} not found.")
                return

            # Dispatch based on payload keys
            if "status" in payload:
                new_status = payload["status"]
                print(f"[OrderConsumer] Updating order {order_id} status to '{new_status}'")
                order.status = new_status
            elif "payment_link" in payload:
                payment_link = payload["payment_link"]
                print(f"[OrderConsumer] Updating order {order_id} with payment link.")
                order.payment_link = payment_link
            else:
                print(f"[!] Unrecognized payload format: {payload}")
                return

            await db.commit()

        except Exception as e:
            print(f"Error during DB operation in order-service: {e}")
            await db.rollback()

async def start_order_consumer() -> None:
    """
    Starts the RabbitMQ consumer for the order service queue.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.ORDER_QUEUE, durable=True)
    print(f"[*] Waiting for messages on queue '{settings.ORDER_QUEUE}'. To exit press CTRL+C")

    async for raw_msg in queue.iterator():
        message = cast(AbstractIncomingMessage, raw_msg)
        async with message.process():
            try:
                payload = json.loads(message.body.decode("utf-8"))
                await handle_message(payload)
            except Exception as e:
                print(f"[!] Failed to process message from order queue: {e}")