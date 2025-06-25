# === api/workers/producer.py ===
import json
import aio_pika
from api.core.config import settings

async def publish_status_update(order_id: int, status: str) -> None:
    """
    Publishes a status update message to the order, staff, and notification queues.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection.channel() as channel:
        queues_to_publish = [
            settings.ORDER_QUEUE,
            settings.STAFF_QUEUE,
            settings.NOTIFICATION_QUEUE
        ]

        message_body = json.dumps({"order_id": order_id, "status": status})
        message = aio_pika.Message(
            body=message_body.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        for queue_name in queues_to_publish:
            await channel.declare_queue(queue_name, durable=True)
            await channel.default_exchange.publish(message, routing_key=queue_name)
            print(f" [x] Sent status update for order {order_id}: '{status}' to queue '{queue_name}'")

async def publish_payment_link_update(order_id: int, payment_link: str) -> None:
    """
    Publishes a message with the payment link back to the order service queue.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection.channel() as channel:
        message_body = json.dumps({"order_id": order_id, "payment_link": payment_link})
        message = aio_pika.Message(
            body=message_body.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await channel.default_exchange.publish(message, routing_key=settings.ORDER_QUEUE)
        print(f" [x] Sent payment link for order {order_id} to queue '{settings.ORDER_QUEUE}'")