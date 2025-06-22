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


import asyncio
import uuid
from aio_pika.abc import AbstractIncomingMessage


async def publish_event(event_type: str, payload: dict, routing_key: str):
    """
    Publish a generic event message to RabbitMQ.

    Args:
        event_type (str): A string indicating the type of event (e.g., "order_cancelled").
        payload (dict): The data associated with the event.
        routing_key (str): The RabbitMQ routing key for the message.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        message_body = {
            "event_type": event_type, # KLUCZ DO ROZRÓŻNIANIA WIADOMOŚCI
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


async def create_payment_request_and_wait_for_link(
    payment_payload: dict
) -> str: # Zwróci URL do płatności
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # Stwórz tymczasową (ekskluzywną) kolejkę dla odpowiedzi
        reply_queue = await channel.declare_queue(
            exclusive=True, # Ekskluzywna, usunięta po rozłączeniu
            auto_delete=True # Automatycznie usunięta, gdy nie ma konsumentów
        )

        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        # Funkcja callback do obsługi odpowiedzi
        def on_response(message: AbstractIncomingMessage):
            if message.correlation_id == correlation_id:
                future.set_result(message.body.decode()) # Zakładamy, że body to URL

        # Rozpocznij konsumowanie z kolejki zwrotnej
        consumer_tag = await reply_queue.consume(on_response, no_ack=True) # no_ack=True bo tymczasowa, nie potrzebujemy potwierdzeń

        try:
            full_payload = {
                "event_type": "create_payment_request", # <<< TUTAJ DEFINIUJEMY TYP DLA TWORZENIA PŁATNOŚCI
                "payload": payment_payload
            }

            # Opublikuj wiadomość z danymi płatności
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(full_payload).encode(),
                    content_type="application/json",
                    correlation_id=correlation_id,
                    reply_to=reply_queue.name # Ustaw nazwę kolejki zwrotnej
                ),
                routing_key=settings.PAYMENT_QUEUE
            )

            # Poczekaj na odpowiedź (z timeoutem, aby uniknąć zawieszenia)
            # Ustaw rozsądny timeout, np. 30 sekund
            response_body = await asyncio.wait_for(future, timeout=30.0)

            # Zakładamy, że odpowiedź to JSON z "redirect_uri"
            response_data = json.loads(response_body)
            redirect_uri = response_data.get("redirect_uri")

            if not redirect_uri:
                raise ValueError("Payment service did not return a redirect URI.")

            return redirect_uri

        except asyncio.TimeoutError:
            raise TimeoutError("Payment service did not respond in time.")
        except Exception as e:
            # Logowanie błędów, np. walidacji odpowiedzi
            print(f"Error in RPC call to payment service: {e}")
            raise e
        finally:
            # Zakończ konsumowanie z kolejki zwrotnej
            await reply_queue.cancel(consumer_tag)


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
