# === api/routes/payment.py ===

"""Payment-related HTTP routes for managing PayU transactions."""

from fastapi import APIRouter, HTTPException, status

from api.schemas.payment import CreateRefundRequest
from api.services.payu import PayUClient
from api.core.exceptions import PayUError, OrderError

router = APIRouter()
payu_client = PayUClient()


@router.get(
    "/methods",
    summary="List available payment methods",
    description="Fetches all supported PayU payment methods for the current merchant.",
    response_model=dict,
    tags=["Payment"]
)
def list_payment_methods():
    """Get available payment methods from PayU."""
    try:
        return payu_client.get_payment_methods()
    except PayUError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e


@router.get(
    "/{order_id}",
    summary="Get payment status",
    description="Returns the current status of a PayU payment order by its ID.",
    response_model=dict,
    tags=["Payment"]
)
def get_payment_status(order_id: str):
    """Retrieve the status of an existing PayU order."""
    try:
        return payu_client.get_order_status(order_id)
    except OrderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.delete(
    "/{order_id}",
    summary="Cancel payment",
    description="Cancels an existing PayU payment order by its ID.",
    response_model=dict,
    tags=["Payment"]
)
def cancel_payment(order_id: str):
    """Cancel a PayU payment order."""
    try:
        return payu_client.cancel_order(order_id)
    except OrderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post(
    "/{order_id}/refund",
    summary="Refund payment",
    description="Issues a refund for a completed PayU order by order ID.",
    response_model=dict,
    tags=["Payment"]
)
def refund_payment(order_id: str, refund: CreateRefundRequest):
    """Create a refund for a given PayU order."""
    try:
        refund_data = {
            "refund": {
                "description": refund.description,
                "currencyCode": refund.currencyCode
            }
        }
        return payu_client.refund_order(order_id, refund_data)
    except PayUError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

# Już nie jest używane, bo konsument obsługuje płatności z RabbitMQ

# @app.post("/payments")
# def create_payment(payment: CreatePaymentRequest):
#     try:
#         order_data = {
#             "notifyUrl": payment.notifyUrl,
#             "customerIp": payment.customerIp,
#             "merchantPosId": settings.PAYU_MERCHANT_POS_ID,
#             "description": payment.description,
#             "currencyCode": payment.currencyCode,
#             "totalAmount": payment.totalAmount,
#             "buyer": payment.buyer.model_dump(),
#             "products": [product.model_dump() for product in payment.products]
#         }
#         response = payu_client.create_order(order_data)
#         return {
#             "orderId": response.get("orderId"),
#             "redirectUri": response.get("redirectUri")
#         }
#     except OrderError as e:
#         raise HTTPException(status_code=502, detail=str(e))
