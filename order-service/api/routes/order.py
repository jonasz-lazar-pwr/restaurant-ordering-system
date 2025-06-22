# === api/routes/order.py ===

"""
Order endpoints for the Order Service.
"""
import httpx
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.db.deps import get_db
from api.core.config import settings
from api.models import MenuItem, Order, OrderItem, OrderStatus, TableSession
from api.schemas.order import OrderRequest, OrderResponse, OrderListResponse, OrderSummary, OrderDeletedOut, PaymentMethod
from api.utils.auth import extract_user_info
from api.workers.producer import send_order_status_notification
from api.utils.payment_payload_builder import build_payment_payload

router = APIRouter()

@router.post(
    "",
    response_model=OrderResponse,
    summary="Place an order",
    description="Create a new order. If payment method is 'online', it will synchronously call the payment service to get a payment link."
)
async def create_order(
    order_request: OrderRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderResponse:
    """Create a new order. For online payments, it synchronously contacts the
    Payment Service to generate and return a payment link.
    """
    user_info: Dict[str, Any] = extract_user_info(authorization)
    user_id = user_info["sub"]

    # --- 1. Validate menu items ---
    item_ids = [item.item_id for item in order_request.items]
    result = await db.execute(select(MenuItem).where(MenuItem.id.in_(item_ids)))
    menu_items_dict = {item.id: item for item in result.scalars().all()}

    if len(menu_items_dict) != len(item_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more menu items not found."
        )

    # --- 2. Get table session ---
    session_result = await db.execute(
        select(TableSession).where(TableSession.user_id == user_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active table session. Please scan QR code first."
        )

    # --- 3. Create Order and OrderItems in DB ---
    db_order = Order(
        table_number=session.table_number,
        user_id=user_id,
        comment=order_request.comment,
        payment_method=order_request.payment_method,
        status=OrderStatus.pending
    )
    db.add(db_order)
    await db.flush()  # To get db_order.id

    order_items = [
        OrderItem(
            order_id=db_order.id,
            menu_item_id=item.item_id,
            quantity=item.quantity
        ) for item in order_request.items
    ]
    db.add_all(order_items)
    await db.commit()
    await db.refresh(db_order)

    payment_link = None
    # --- 4. Handle Payment ---
    if order_request.payment_method == PaymentMethod.online:
        payment_payload = build_payment_payload(
            order=db_order,
            order_items=order_items,
            menu_items=menu_items_dict,
            buyer={
                "email": user_info["email"],
                "phone": settings.DEFAULT_PHONE_NUMBER,
                "firstName": user_info.get("first_name"),
                "lastName": user_info.get("last_name"),
                "language": settings.DEFAULT_LANGUAGE
            },
            customer_ip=settings.DEFAULT_CUSTOMER_IP,
            notify_url=settings.PAYMENT_NOTIFY_URL
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.PAYMENT_SERVICE_URL}/payment",
                    json=payment_payload
                )
                response.raise_for_status()
                payment_link = response.json().get("payment_link")
        except httpx.HTTPStatusError as e:
            # If payment service fails, we should ideally compensate (e.g., mark order as failed).
            db_order.status = OrderStatus.failed
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service failed: {e.response.text}"
            )
        except Exception as e:
            db_order.status = OrderStatus.failed
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while contacting payment service: {str(e)}"
            )

    return OrderResponse(
        message=f"Order placed successfully by {user_info.get('email')} for table {session.table_number}.",
        order_id=db_order.id,
        payment_link=payment_link
    )


@router.get(
    "/my",
    response_model=OrderListResponse,
    summary="Get orders for current user table",
    description="Retrieve all orders for the currently assigned table (based on QR code).",
    tags=["Order"]
)
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderListResponse:
    """
    Retrieve all orders for the table currently assigned to the authenticated user.
    """
    user_info: Dict[str, Any] = extract_user_info(authorization)
    user_id = user_info["sub"]

    # Retrieve table session
    result = await db.execute(
        select(TableSession).where(TableSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active table session. Please scan QR code first."
        )
    table_number = session.table_number

    # Retrieve orders for the table
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.menu_item))
        .where(Order.table_number == table_number)
    )
    result = await db.execute(stmt)
    orders_from_db = result.scalars().all()

    if not orders_from_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for this table."
        )

    order_summaries = []
    for order in orders_from_db:
        for item in order.items:
            order_summaries.append(OrderSummary(
                order_id=order.id,
                status=order.status.value,
                item_name=item.menu_item.name if item.menu_item else "Unknown",
                quantity=item.quantity,
                price=item.menu_item.price if item.menu_item else 0.0
            ))

    return OrderListResponse(
        table_number=table_number,
        retrieved_by_user_id=user_id,
        orders=order_summaries
    )


@router.delete(
    "/{order_id}",
    response_model=OrderDeletedOut,
    summary="Cancel order",
    description="Cancel an existing order if it is still pending."
)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderDeletedOut:
    """
    Cancel an existing order by setting its status to 'cancelled'.
    """
    user_info = extract_user_info(authorization)
    user_id = user_info["sub"]

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only cancel your own orders")

    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")

    order.status = OrderStatus.cancelled
    await db.commit()
    await db.refresh(order)

    await send_order_status_notification(
        order_id=order.id,
        new_status=order.status.value,
        email=user_info["email"]
    )

    return OrderDeletedOut(message="Order cancelled successfully", order_id=order.id)