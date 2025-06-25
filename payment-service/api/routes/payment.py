# === api/routes/payment.py ===

"""Payment-related HTTP routes for managing PayU transactions."""
import re
from fastapi import APIRouter, HTTPException, status, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.schemas.payment import CreateRefundRequest, CreatePaymentRequest, PaymentLinkOut
from api.services.payu import PayUClient
from api.core.exceptions import PayUError, OrderError
from api.workers.producer import publish_status_update
from api.models.payment import Payment
from api.db.deps import get_db
from api.core.config import settings

router = APIRouter()
payu_client = PayUClient()

def extract_order_id_from_description(description: str) -> str | None:
    """Extracts order ID like '#1' from 'Order #1 for table...'."""
    match = re.search(r"#(\d+)", description)
    return match.group(1) if match else None

@router.post(
    "",
    summary="Create a new payment",
    description="Creates a PayU payment order and returns a redirect link for the user.",
    response_model=PaymentLinkOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Payment"]
)
async def create_payment(
    payment_request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handles a request to create a new payment.
    - Calls PayU to create an order.
    - Saves payment details to the local database.
    - Returns the payment link to the calling service.
    """
    try:
        order_data = {
            "notifyUrl": payment_request.notifyUrl,
            "customerIp": payment_request.customerIp,
            "merchantPosId": settings.PAYU_MERCHANT_POS_ID,
            "description": payment_request.description,
            "currencyCode": payment_request.currencyCode,
            "totalAmount": payment_request.totalAmount,
            "buyer": payment_request.buyer.model_dump(),
            "products": [product.model_dump() for product in payment_request.products],
        }

        response = payu_client.create_order(order_data)
        redirect_uri = response.get("redirectUri")
        payu_order_id = response.get("orderId")

        internal_order_id_str = extract_order_id_from_description(payment_request.description)
        if not internal_order_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract internal order_id from payment description."
            )

        new_payment = Payment(
            order_id=int(internal_order_id_str),
            payu_order_id=payu_order_id,
            payment_link=redirect_uri,
            status="PENDING"
        )
        db.add(new_payment)
        await db.commit()

        return PaymentLinkOut(
            order_id=int(internal_order_id_str),
            payment_link=redirect_uri
        )

    except OrderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post(
    "/notify",
    summary="Handle PayU payment notification",
    status_code=status.HTTP_200_OK,
    tags=["Payment"]
)
async def handle_payu_notification(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handles the webhook from PayU. If payment is complete, it publishes
    a status update to the order, staff, and notification queues.
    """
    try:
        notification_data = await request.json()
        print(f"[PayU-Notify] Received notification: {notification_data}")

        order_info = notification_data.get("order", {})
        payu_order_id = order_info.get("orderId")
        order_status = order_info.get("status")

        if not payu_order_id:
            print("[!] PayU notification missing 'orderId'.")
            return {"status": "ok"}

        # Find our internal payment record using PayU's orderId
        result = await db.execute(select(Payment).where(Payment.payu_order_id == payu_order_id))
        payment_record = result.scalar_one_or_none()

        if not payment_record:
            print(f"[!] Received notification for unknown PayU orderId: {payu_order_id}")
            return {"status": "ok"}

        internal_order_id = payment_record.order_id
        publish_status = None

        if order_status == "COMPLETED":
            publish_status = "paid"
            payment_record.status = "COMPLETED"
        elif order_status in ["CANCELED", "REJECTED"]:
            publish_status = "cancelled"
            payment_record.status = "CANCELLED"
        else:
            print(f"[PayU-Notify] Received unhandled status '{order_status}' for order {internal_order_id}.")
            payment_record.status = order_status

        await db.commit()

        if publish_status:
            print(f"[PayU-Notify] Publishing '{publish_status}' status for internal order {internal_order_id}.")
            await publish_status_update(internal_order_id, publish_status)

    except Exception as e:
        print(f"[!] Error processing PayU notification: {e}")
        await db.rollback()

    return {"status": "ok"}

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