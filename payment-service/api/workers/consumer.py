# === api/workers/consumer.py ===

import json
import re
from typing import cast

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractChannel
from sqlalchemy import select

from api.core.config import settings
from api.core.exceptions import OrderError
from api.db.session import async_session
from api.models.payment import Payment
from api.schemas.payment import CreatePaymentRequest
from api.services.payu import PayUClient

payu_client = PayUClient()

def extract_order_id_from_description(description: str) -> str | None:
    """Extracts order ID like '#1' from 'Order #1 for table...'."""
    match = re.search(r"#(\d+)", description)
    return match.group(1) if match else None


async def handle_payment_message(
    message: AbstractIncomingMessage,
    channel: AbstractChannel,
) -> None:
    async with async_session() as session:
        try:
            message_body = json.loads(message.body.decode("utf-8"))
            event_type = message_body.get("event_type")
            payload = message_body.get("payload")

            if not event_type:
                print("[!] Message received without 'event_type'. NACKing.")
                await message.nack(requeue=False)
                return

            if event_type == "create_payment_request":
                payment = CreatePaymentRequest(**payload)

                print(f"[PaymentConsumer] Creating payment: {payment.description}, amount: {payment.totalAmount}")

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

                print(f"[PaymentConsumer] PayU order created: {response.get('orderId')} → redirect: {response.get('redirectUri')}")

                new_payu_payment = Payment(
                    order_id=payment.orderId,
                    payu_order_id=response.get("orderId"),
                    amount=payment.totalAmount,
                    currency=payment.currencyCode,
                    status="NEW",
                    table_number=payment.tableNumber,
                    user_id=payment.userId,
                )
                session.add(new_payu_payment)
                await session.commit()
                await session.refresh(new_payu_payment)
                print(f"[PaymentConsumer] Payment saved to DB: {new_payu_payment.id}")

                if message.reply_to:
                    response_payload = {
                        "order_id": response.get("orderId"),
                        "redirect_uri": response.get("redirectUri"),
                    }
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(response_payload).encode(),
                            content_type="application/json",
                            correlation_id=message.correlation_id,
                        ),
                        routing_key=message.reply_to,
                    )

            elif event_type == "cancel_payment_request":
                order_id = payload.get("order_service_order_id")
                table_number = payload.get("table_number")
                user_id = payload.get("user_id")

                if not all([table_number, user_id]):
                    print(f"[!] Missing data in cancel_payment_request: {payload}")
                    await message.nack(requeue=False)
                    return

                print(f"[PaymentConsumer] Cancel request: order_id={order_id}, table={table_number}, user={user_id}")

                result = await session.execute(
                    select(Payment).where(
                        Payment.order_id == str(order_id),
                        Payment.table_number == str(table_number),
                        Payment.user_id == str(user_id),
                    )
                )
                payment_record = result.scalar_one_or_none()

                if not payment_record:
                    print("[PaymentConsumer] Payment not found in DB.")
                    await message.ack()
                    return

                payu_order_id = payment_record.payu_order_id

                try:
                    payu_client.cancel_order(payu_order_id)
                    print(f"[PaymentConsumer] PayU cancellation for {payu_order_id} OK.")

                    if payment_record.status == "COMPLETED":
                        payment_record.status = "REFUND_REQUESTED"
                    else:
                        payment_record.status = "CANCELLED"
                    await session.commit()
                    await session.refresh(payment_record)
                except OrderError as e:
                    print(f"[!] PayU cancel error: {e}")
                    payment_record.status = "CANCELLATION_FAILED_PAYU"
                    await session.commit()
                    await session.refresh(payment_record)
                    raise

            elif event_type == "refund_payment_request":
                order_id = payload.get("order_service_order_id")
                table_number = payload.get("table_number")
                user_id = payload.get("user_id")

                if not all([table_number, user_id]):
                    print(f"[!] Missing data in refund_payment_request: {payload}")
                    await message.nack(requeue=False)
                    return

                print(f"[PaymentConsumer] Refund request: order_id={order_id}, table={table_number}, user={user_id}")

                result = await session.execute(
                    select(Payment).where(
                        Payment.order_id == str(order_id),
                        Payment.table_number == str(table_number),
                        Payment.user_id == str(user_id),
                    )
                )
                payment_record = result.scalar_one_or_none()

                if not payment_record:
                    print("[PaymentConsumer] Payment not found in DB.")
                    await message.ack()
                    return

                payu_order_id = payment_record.payu_order_id
                refund_data = {
                    "refund": {
                        "description": payload.get("reason"),
                        "currencyCode": "PLN"
                    }
                }

                try:
                    payu_client.refund_order(payu_order_id, refund_data)
                    payment_record.status = "REFUNDED"
                    await session.commit()
                    await session.refresh(payment_record)
                    print(f"[PaymentConsumer] Payment {payu_order_id} marked as REFUNDED.")
                except OrderError as e:
                    print(f"[!] PayU refund error: {e}")
                    payment_record.status = "REFUND_FAILED_PAYU"
                    await session.commit()
                    await session.refresh(payment_record)
                    raise

            else:
                print(f"[PaymentConsumer] Unknown event_type: {event_type}")

        except Exception as e:
            print(f"[!] Exception during message processing: {e}")
            if message.reply_to:
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({"error": str(e), "status": "failed"}).encode(),
                        content_type="application/json",
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to,
                )
            raise


async def start_payment_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.PAYMENT_QUEUE, durable=True)

    async for raw_msg in queue.iterator():
        message = cast(AbstractIncomingMessage, raw_msg)
        async with message.process():
            try:
                await handle_payment_message(message, channel)
            except Exception as e:
                print(f"[!] Failed to process payment message: {e}")
