# === staff-service/api/workers/consumer.py ===

import json
from typing import cast
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.db.session import async_session
from api.models.order import Order
from api.core.config import settings

async def handle_status_update(payload: dict):
    """
    Handles a single order status update message asynchronously.
    It creates a new order record if it doesn't exist (on 'paid' status)
    or updates an existing one.
    """
    async with async_session() as db:
        try:
            order_id = payload.get("order_id")
            new_status = payload.get("status")

            if not order_id or not new_status:
                print(f"[!] Invalid payload received: {payload}")
                return

            result = await db.execute(select(Order).filter(Order.id == order_id))
            order = result.scalar_one_or_none()

            if order:
                print(f"[StaffConsumer] Updating order {order_id} status to '{new_status}'")
                order.status = new_status
            elif new_status == "paid":
                print(f"[StaffConsumer] Creating new order {order_id} with status '{new_status}'")
                new_order = Order(id=order_id, status=new_status)
                db.add(new_order)
            else:
                print(f"[!] Order with id {order_id} not found, ignoring status update '{new_status}'")
                return

            await db.commit()

        except Exception as e:
            print(f"Error during DB operation in staff-service: {e}")
            await db.rollback()

async def start_staff_consumer() -> None:
    """
    Starts the RabbitMQ consumer for the staff service queue.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.STAFF_QUEUE, durable=True)
    print(f"[*] Waiting for messages on queue '{settings.STAFF_QUEUE}'. To exit press CTRL+C")

    async for raw_msg in queue.iterator():
        message = cast(AbstractIncomingMessage, raw_msg)
        async with message.process():
            try:
                payload = json.loads(message.body.decode("utf-8"))
                await handle_status_update(payload)
            except Exception as e:
                print(f"[!] Failed to process message from staff queue: {e}")