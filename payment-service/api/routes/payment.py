# === api/routes/payment.py ===

"""Payment-related HTTP routes for managing PayU transactions."""

from fastapi import APIRouter, HTTPException, status, Request

from api.schemas.payment import CreateRefundRequest
from api.services.payu import PayUClient
from api.core.exceptions import PayUError, OrderError
from api.workers.producer import publish_status_update
from api.workers.consumer import extract_order_id_from_description

router = APIRouter()
payu_client = PayUClient()

@router.post(
    "/notify",
    summary="Handle PayU payment notification",
    status_code=status.HTTP_200_OK,
    tags=["Payment"]
)
async def handle_payu_notification(request: Request):
    """
    Handles the webhook from PayU. If payment is complete, it publishes
    a status update to the order, staff, and notification queues.
    """
    # try:
    #     notification_data = await request.json()
    #     print(f"[PayU-Notify] Received notification: {notification_data}")
    #
    #     order_info = notification_data.get("order", {})
    #     order_status = order_info.get("status")
    #
    #     if order_status == "COMPLETED":
    #         description = order_info.get("description", "")
    #         order_id_str = extract_order_id_from_description(description)
    #
    #         if order_id_str:
    #             order_id = int(order_id_str)
    #             await publish_status_update(order_id, "paid")
    #         else:
    #             print(f"[!] Could not extract order_id from notification: {description}")
    #
    # except Exception as e:
    #     print(f"[!] Error processing PayU notification: {e}")
    try:
        notification_data = await request.json()
        print(f"[PayU-Notify] Received notification: {notification_data}")

        order_info = notification_data.get("order", {})
        order_status = order_info.get("status")
        description = order_info.get("description", "")
        order_id_str = extract_order_id_from_description(description)

        if not order_id_str:
            print(f"[!] Could not extract order_id from notification: {description}")
            return {"status": "ok"}

        order_id = int(order_id_str)

        if order_status == "COMPLETED":
            print(f"[PayU-Notify] Payment COMPLETED for order {order_id}. Publishing 'paid' status.")
            await publish_status_update(order_id, "paid")

        elif order_status in ["CANCELED", "REJECTED"]:
            print(f"[PayU-Notify] Payment {order_status} for order {order_id}. Publishing 'cancelled' status.")
            await publish_status_update(order_id, "cancelled")

        else:
            print(f"[PayU-Notify] Received unhandled status '{order_status}' for order {order_id}.")


    except Exception as e:
        print(f"[!] Error processing PayU notification: {e}")

    return {"status": "ok"}

@router.get(
    "/{order_id}/link",
    summary="Get payment link",
    description="Returns the PayU payment link for a given internal order ID.",
    response_model=dict,
    tags=["Payment"]
)
def get_payment_link(order_id: str, request: Request):
    """Retrieve the payment link from the in-memory store."""
    payment_links_db = request.app.state.payment_links_db
    link = payment_links_db.get(order_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment link for order_id '{order_id}' not found."
        )
    return {"order_id": order_id, "payment_link": link}


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
