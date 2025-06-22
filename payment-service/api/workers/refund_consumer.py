# === api/workers/refund_consumer.py ===
import json
import aio_pika
from sqlalchemy.future import select

from api.core.config import settings
from api.db.session import async_session
from api.models.payment import Payment
from api.services.payu import PayUClient
from api.workers.producer import publish_status_update

payu_client = PayUClient()


async def handle_refund_message(payload: dict):
    order_id = payload.get("order_id")
    reason = payload.get("reason", "Refund requested by staff")

    async with async_session() as session:
        result = await session.execute(select(Payment).where(Payment.order_id == order_id))
        payment = result.scalar_one_or_none()

        if not payment or not payment.payu_order_id:
            print(f"[RefundConsumer] Payment not found for order_id: {order_id}")
            return

        try:
            payu_client.refund_order(payment.payu_order_id, {"refund": {"description": reason}})
            payment.status = "REFUNDED"
            await session.commit()

            # Poinformuj inne serwisy o zwrocie
            await publish_status_update(order_id, "refunded")
            print(f"[RefundConsumer] Refund processed for order_id: {order_id}")
        except Exception as e:
            print(f"[RefundConsumer] Error processing refund for order {order_id}: {e}")


async def start_refund_consumer():
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    refund_queue_name = "refund_service_queue"
    queue = await channel.declare_queue(refund_queue_name, durable=True)

    async for message in queue.iterator():
        async with message.process():
            try:
                payload = json.loads(message.body.decode("utf-8"))
                await handle_refund_message(payload)
            except Exception as e:
                print(f"[!] Failed to process refund message: {e}")