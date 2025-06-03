import asyncio
import aio_pika

from fastapi import FastAPI, HTTPException
from .core.payu_client import PayUClient
from .schemas.payment import CreatePaymentRequest, CreateRefundRequest
from .core.exceptions import PayUError, OrderError
from .core import config

app = FastAPI()
payu_client = PayUClient()

RABBITMQ_URL = "amqp://admin:admin@rabbitmq:5672/"

async def on_order_message(message: aio_pika.IncomingMessage):
    async with message.process():
        order_id = message.body.decode()
        print(f"Received new order to pay: {order_id}")

async def consume_orders():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            queue = await channel.declare_queue("payments_queue")
            await queue.consume(on_order_message)
            # print("Started listening for payment orders...")
        except Exception as e:
            print("Connection error with rabbit mq: ", e)
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_orders())

@app.get("/payments/methods")
def list_payment_methods():
    try:
        methods = payu_client.get_payment_methods()
        return methods
    except PayUError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e #poprawić

@app.post("/payments")
def create_payment(payment: CreatePaymentRequest):
    try:
        order_data = {
            "notifyUrl": payment.notifyUrl,
            "customerIp": payment.customerIp,
            "merchantPosId": config.PAYU_MERCHANT_POS_ID,
            "description": payment.description,
            "currencyCode": payment.currencyCode,
            "totalAmount": payment.totalAmount,
            "buyer": payment.buyer.model_dump(),
            "products": [product.model_dump() for product in payment.products]
        }
        response = payu_client.create_order(order_data)
        return {
            "orderId": response.get("orderId"),
            "redirectUri": response.get("redirectUri")
        }
    except OrderError as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.get("/payments/{order_id}")
def get_payment_status(order_id: str):
    try:
        status = payu_client.get_order_status(order_id)
        return status
    except OrderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    
@app.delete("/payments/{order_id}")
def cancel_payment(order_id: str):
    try:
        status = payu_client.cancel_order(order_id)
        return status
    except OrderError as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/payments/{order_id}/refund")
def refund_payment(order_id: str, refund: CreateRefundRequest):
    try:
        refund_data = {
            "refund": {
                "description" : refund.description,
                "currencyCode" : refund.currencyCode
            }
        }
        response = payu_client.refund_order(order_id, refund_data)
        return response
    except PayUError as e:
        raise HTTPException(status_code=502, detail=str(e))
