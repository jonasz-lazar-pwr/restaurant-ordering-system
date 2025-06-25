# === api/workers/producer.py ===

"""
RabbitMQ publishing utility for the Order Service.
"""

import json
import asyncio
import uuid
import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from api.core.config import settings
from api.models import Order, OrderItem
from api.utils.payment_payload_builder import build_payment_payload


async def publish_event(event_type: str, payload: dict, routing_key: str):
    """
    Publish a generic event message to RabbitMQ.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        message_body = {
            "event_type": event_type,
            "payload": payload
        }

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message_body).encode(),
                content_type="application/json",
            ),
            routing_key=routing_key
        )
        print(f"[OrderService Producer] Published event '{event_type}' to '{routing_key}' with payload: {payload}")


async def create_payment_request_and_wait_for_link(payment_payload: dict) -> str:
    """
    Publishes a payment request via RPC and waits for redirect_uri from Payment Service.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        reply_queue = await channel.declare_queue(
            exclusive=True,
            auto_delete=True
        )

        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def on_response(message: AbstractIncomingMessage):
            if message.correlation_id == correlation_id:
                future.set_result(message.body.decode())

        consumer_tag = await reply_queue.consume(on_response, no_ack=True)

        try:
            full_payload = {
                "event_type": "create_payment_request",
                "payload": payment_payload
            }

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(full_payload).encode(),
                    content_type="application/json",
                    correlation_id=correlation_id,
                    reply_to=reply_queue.name
                ),
                routing_key=settings.PAYMENT_QUEUE
            )

            response_body = await asyncio.wait_for(future, timeout=30.0)
            response_data = json.loads(response_body)
            redirect_uri = response_data.get("redirect_uri")

            if not redirect_uri:
                raise ValueError("Payment service did not return a redirect URI.")

            return redirect_uri

        except asyncio.TimeoutError:
            raise TimeoutError("Payment service did not respond in time.")
        except Exception as e:
            print(f"Error in RPC call to payment service: {e}")
            raise e
        finally:
            await reply_queue.cancel(consumer_tag)


async def send_order_status_notification(order_id: int, new_status: str, email: str) -> None:
    """
    Sends a notification message about order status change to Notification Service.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()

        payload = json.dumps({
            "order_id": order_id,
            "status": new_status
        }).encode()

        await channel.default_exchange.publish(
            aio_pika.Message(body=payload, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=settings.NOTIFICATION_QUEUE
        )
        print(f" [x] Sent status notification for order {order_id} to queue '{settings.NOTIFICATION_QUEUE}'")


async def send_payment_request(payment_payload: dict) -> None:
    """
    Sends a payment creation message to Payment Service without RPC response.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payment_payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=settings.PAYMENT_QUEUE
        )
        print(f" [x] Sent payment request for order '{payment_payload['description']}' to queue '{settings.PAYMENT_QUEUE}'")
