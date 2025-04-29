from fastapi import FastAPI, HTTPException
from .core.payu_client import PayUClient
from .schemas.payment import CreatePaymentRequest, CreateRefundRequest
from .core.exceptions import PayUError, OrderError
from .core import config

app = FastAPI()
payu_client = PayUClient()

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
