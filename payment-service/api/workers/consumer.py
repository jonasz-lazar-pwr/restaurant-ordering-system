# === api/workers/consumer.py ===

"""RabbitMQ consumer for processing incoming payment requests.

Consumes messages from the payment queue and delegates processing
to the PayU client.
"""

import json
from typing import cast

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from api.schemas.payment import CreatePaymentRequest
from api.core.config import settings
from api.services.payu import PayUClient

payu_client = PayUClient()


async def handle_payment_message(payload: dict) -> None:
    """Handle a single payment message by creating a PayU order.

    Args:
        payload (dict): Parsed JSON payload representing a payment request.

    Raises:
        ValidationError: If payload does not conform to CreatePaymentRequest.
        PayUError: If PayU API call fails.
    """
    payment = CreatePaymentRequest(**payload)

    print(
        f"[PaymentConsumer] Creating payment: "
        f"{payment.description}, amount: {payment.totalAmount}"
    )

    order_data = {
        "notifyUrl": payment.notifyUrl,
        "customerIp": payment.customerIp,
        "merchantPosId": settings.PAYU_MERCHANT_POS_ID,
        "description": payment.description,
        "currencyCode": payment.currencyCode,
        "totalAmount": payment.totalAmount,
        "buyer": payment.buyer.model_dump(),
        "products": [product.model_dump() for product in payment.products],
    }

    response = payu_client.create_order(order_data)

    print(
        f"[PaymentConsumer] PayU order created: {response.get('orderId')} "
        f"→ redirect: {response.get('redirectUri')}"
    )


async def start_payment_consumer() -> None:
    """Start the RabbitMQ consumer for the payment queue.

    Continuously listens for new messages and delegates them
    to the `handle_payment_message` function.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.PAYMENT_QUEUE, durable=True)

    async for raw_msg in queue.iterator():
        message = cast(AbstractIncomingMessage, raw_msg)
        async with message.process():
            try:
                payload = json.loads(message.body.decode("utf-8"))
                await handle_payment_message(payload)
            except Exception as e:
                print(f"[!] Failed to process payment message: {e}")
