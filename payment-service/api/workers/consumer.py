# === api/workers/consumer.py ===

"""RabbitMQ consumer for processing incoming payment requests.

Consumes messages from the payment queue and delegates processing
to the PayU client.
"""

import json
from typing import cast

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractChannel

from api.db.deps import get_db
from api.models.models import Payment
from sqlalchemy import select
from api.core.exceptions import OrderError

from api.schemas.payment import CreatePaymentRequest
from api.core.config import settings
from api.services.payu import PayUClient

payu_client = PayUClient()


# Zmieniamy funkcję, aby przyjmowała channel i message,
# potrzebne do odesłania odpowiedzi
async def handle_payment_message(
    message: AbstractIncomingMessage, # Teraz przyjmuje całą wiadomość
    channel: AbstractChannel, # Potrzebujemy kanału do publikacji odpowiedzi
) -> None:
    async with get_db() as session:
        try:
            message_body = json.loads(message.body.decode("utf-8"))
            event_type = message_body.get("event_type") # Wyciągamy typ zdarzenia
            payload = message_body.get("payload")     # Wyciągamy rzeczywisty payload

            if not event_type:
                print("[!] Message received without 'event_type'. Ignoring and NACKing.")
                await message.nack(requeue=False) # Nieznany format wiadomości, nie próbuj ponownie
                return

            # payload = json.loads(message.body.decode("utf-8"))
            # payment = CreatePaymentRequest(**payload)

            if event_type == "create_payment_request":
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

                # Zapis do bazy danych
                # Konwersja typów z CreatePaymentRequest (stringi) do modelu Payment (int, UUID)
                new_payu_payment = Payment(
                    order_id = payment.orderId,
                    payu_order_id = response.get('orderId'),
                    amount = payment.totalAmount,
                    currency = payment.currencyCode,
                    status = "NEW", # Początkowy status płatności w naszym systemie
                    table_number = payment.tableNumber, 
                    user_id = payment.userId
                )
                session.add(new_payu_payment)
                await session.commit()
                await session.refresh(new_payu_payment)
                print(f"[PaymentConsumer] PayU payment record saved to DB: {new_payu_payment.id}")

                # Odesłanie odpowiedzi
                if message.reply_to: # Sprawdź, czy nadawca oczekuje odpowiedzi
                    response_payload = {
                        "order_id": response.get("orderId"),
                        "redirect_uri": response.get("redirectUri")
                    }

                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(response_payload).encode(),
                            content_type="application/json",
                            correlation_id=message.correlation_id # Użyj tego samego correlation_id
                        ),
                        routing_key=message.reply_to # Wysyłamy na kolejkę zwrotną nadawcy
                    )
                
            elif event_type == "cancel_payment_request":
                order_id = payload.get("order_service_order_id") # <----- TO JEDNAK POTRZEBNE, USER I TABLE MOGĄ MIEĆ KILKA ZAMÓWIEŃ
                table_number = payload.get("table_number")
                user_id = payload.get("user_id")

                if not all([table_number, user_id]):
                        print(f"[!] 'cancel_payment_request' received with missing data. Payload: {payload}. Ignoring and NACKing.")
                        await message.nack(requeue=False)
                        return

                print(f"[PaymentConsumer] Processing 'cancel_payment_request' for order_id: {order_id}, table: {table_number}, user: {user_id}")

                 # === TUTAJ SZUKAMY PAYU_ORDER_ID W NASZEJ BAZIE ===
                payment_record_result = await session.execute(
                    select(Payment).where(
                        Payment.order_id == str(order_id),
                        Payment.table_number == str(table_number),
                        Payment.user_id == str(user_id)
                    )
                )
                payment_record = payment_record_result.scalar_one_or_none()

                if not payment_record:
                    print(f"[PaymentConsumer] Payment record not found in DB. Cannot cancel.")
                    await message.ack() # Potwierdź, bo nic więcej nie możemy zrobić
                    return
                
                payu_order_id = payment_record.payu_order_id
                print(f"[PaymentConsumer] Found PayU order ID: {payu_order_id} for cancellation.")

                # 1. Anuluj w PayU
                try:
                    payu_cancel_response = payu_client.cancel_order(payu_order_id)
                    print(f"[PaymentConsumer] PayU cancellation response for {payu_order_id}: {payu_cancel_response}")

                    # 2. Zaktualizuj status w lokalnej bazie danych payment-service
                    payment_record_result = await session.execute(
                        select(Payment).where(Payment.payu_order_id == payu_order_id)
                    )
                    payment_record = payment_record_result.scalar_one_or_none()

                    if payment_record:
                        #
                        # ========= ZAKTUALIZOWAĆ W ZALEŻNOŚCI OD ZMIANY STATUSÓW W BAZIE
                        #
                        if payment_record.status == "COMPLETED":
                            # Jeśli płatność była COMPLETED, anulowanie w PayU oznacza refund.
                            # PayU potwierdza refund asynchronicznie, więc na razie ustawiamy status prośby.
                            payment_record.status = "REFUND_REQUESTED"
                            print(f"[PaymentConsumer] Payment {payu_order_id} was COMPLETED, marked as REFUND_REQUESTED locally.")
                        else:
                            # Inne statusy (NEW, PENDING) mogą być bezpośrednio anulowane.
                            payment_record.status = "CANCELLED"
                            print(f"[PaymentConsumer] Payment {payu_order_id} marked as CANCELLED locally.")
                        await session.commit()
                        await session.refresh(payment_record)
                    else:
                        print(f"[PaymentConsumer] Payment record for PayU order ID {payu_order_id} not found in DB. PayU cancellation processed.")

                except OrderError as e:
                    print(f"[!] PayU client error during cancellation for {payu_order_id}: {e}")
                    # Możesz zapisać status jako 'CANCELLATION_FAILED_PAYU' w DB
                    if payment_record: # Jeśli znalazłeś rekord, zaktualizuj jego status błędu
                         payment_record.status = "CANCELLATION_FAILED_PAYU"
                         await session.commit()
                         await session.refresh(payment_record)
                    raise # Rethrow, żeby wiadomość mogła być ponownie przetworzona

            elif event_type == "refund_payment_request":
                order_id = payload.get("order_service_order_id") # <----- TO JEDNAK POTRZEBNE, USER I TABLE MOGĄ MIEĆ KILKA ZAMÓWIEŃ
                table_number = payload.get("table_number")
                user_id = payload.get("user_id")

                if not all([table_number, user_id]):
                        print(f"[!] 'refund_payment_request' received with missing data. Payload: {payload}. Ignoring and NACKing.")
                        await message.nack(requeue=False)
                        return

                print(f"[PaymentConsumer] Processing 'refund_payment_request' for order_id: {order_id}, table: {table_number}, user: {user_id}")

                 # === TUTAJ SZUKAMY PAYU_ORDER_ID W NASZEJ BAZIE ===
                payment_record_result = await session.execute(
                    select(Payment).where(
                        Payment.order_id == str(order_id),
                        Payment.table_number == str(table_number),
                        Payment.user_id == str(user_id)
                    )
                )
                payment_record = payment_record_result.scalar_one_or_none()

                if not payment_record:
                    print(f"[PaymentConsumer] Payment record not found in DB. Cannot refund.")
                    await message.ack() # Potwierdź, bo nic więcej nie możemy zrobić
                    return
                
                payu_order_id = payment_record.payu_order_id
                print(f"[PaymentConsumer] Found PayU order ID: {payu_order_id} for refund.")

                try:
                    refund_data = {
                        "refund": {
                            "description" : payload.get("reason"),
                            "currencyCode" : "PLN"
                        }
                    }
                    payu_refund_response = payu_client.refund_order(payu_order_id, refund_data)
                    print(f"[PaymentConsumer] PayU cancellation response for {payu_order_id}: {payu_refund_response}")

                    # Zaktualizuj status w lokalnej bazie danych payment-service
                    payment_record_result = await session.execute(
                        select(Payment).where(Payment.payu_order_id == payu_order_id)
                    )
                    payment_record = payment_record_result.scalar_one_or_none()

                    if payment_record:
                        #
                        # ========= ZAKTUALIZOWAĆ W ZALEŻNOŚCI OD ZMIANY STATUSÓW W BAZIE
                        #
                        # if payment_record.status == "COMPLETED":
                        #     payment_record.status = "REFUNDED"
                        #     print(f"[PaymentConsumer] Payment {payu_order_id} marked as REFUNDED locally.")
                        # else:
                        #     # Inne statusy (NEW, PENDING, ...) nie mogą być zrefundowane.
                        #     print(f"[PaymentConsumer] Payment {payu_order_id} cannot be REFUNDED due to its current status.")
                        payment_record.status = "REFUNDED"
                        print(f"[PaymentConsumer] Payment {payu_order_id} marked as REFUNDED locally.")
                        await session.commit()
                        await session.refresh(payment_record)
                    else:
                        print(f"[PaymentConsumer] Payment record for PayU order ID {payu_order_id} not found in DB. PayU refund processed.")

                except OrderError as e:
                    print(f"[!] PayU client error during refund for {payu_order_id}: {e}")
                    # Możesz zapisać status jako 'CANCELLATION_FAILED_PAYU' w DB
                    if payment_record: # Jeśli znalazłeś rekord, zaktualizuj jego status błędu
                         payment_record.status = "REFUND_FAILED_PAYU"
                         await session.commit()
                         await session.refresh(payment_record)
                    raise # Rethrow, żeby wiadomość mogła być ponownie przetworzona

            else:
                print(f"[PaymentConsumer] Unknown event_type received: {event_type}. Ignoring.")

        except Exception as e:
            print(f"[!] Failed to process payment message: {e}")
            # TUTAJ MOŻESZ DODAĆ PUBLIKACJĘ WIADOMOŚCI O BŁĘDZIE NA KOLEJKĘ ZWROTNĄ
            # ALBO DO SPECJALNEJ KOLEJKI BŁĘDÓW, JEŚLI POTRZEBUJESZ POWIADOMIĆ NADWCĘ O FAILE
            if message.reply_to:
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({"error": str(e), "status": "failed"}).encode(),
                        content_type="application/json",
                        correlation_id=message.correlation_id
                    ),
                    routing_key=message.reply_to
                )
            # Przetwarzaj wiadomość jako niepowodzenie, aby została ponownie dostarczona lub przeniesiona do DLQ
            raise # Pozwól message.process() odrzucić wiadomość



# Zaktualizuj start_payment_consumer, aby przekazywał channel i message do handle_payment_message
async def start_payment_consumer() -> None:
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel() # Deklarujemy channel tutaj, by był dostępny
    queue = await channel.declare_queue(settings.PAYMENT_QUEUE, durable=True)

    async for raw_msg in queue.iterator():
        message = cast(AbstractIncomingMessage, raw_msg)
        async with message.process():
            try:
                # Przekazujemy channel i message do handlera
                await handle_payment_message(message, channel) 
            except Exception as e:
                print(f"[!] Failed to process payment message: {e}")
                # Tutaj message.process() automatycznie odrzuci wiadomość (nack)
