# === api/routes/order.py ===

"""
Order endpoints for the Order Service.
"""
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
from api.workers.producer import send_order_status_notification, publish_event
from api.utils.payment_payload_builder import build_payment_payload
from api.workers.producer import create_payment_request_and_wait_for_link
import asyncio

router = APIRouter()

@router.post(
    "",
    response_model=OrderResponse,
    summary="Place an order",
    description="Creates a new order. If payment is online, a request is sent to the payment service asynchronously."
)
async def create_order(
    order_request: OrderRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
) -> OrderResponse:
    """Create a new order based on the provided QR code and menu item IDs."""
    user_info: Dict[str, Any] = extract_user_info(authorization)
    user_id = user_info["sub"]

    # 1. Validate menu items
    item_ids = [item.item_id for item in order_request.items]
    result = await db.execute(select(MenuItem).where(MenuItem.id.in_(item_ids)))
    menu_items_dict = {item.id: item for item in result.scalars().all()}

    if len(menu_items_dict) != len(item_ids):
        raise HTTPException(status_code=404, detail="One or more menu items not found.")

    # 2. Get table session
    session_result = await db.execute(select(TableSession).where(TableSession.user_id == user_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=400, detail="No active table session. Please scan QR code first.")

    # 3. Create order
    db_order = Order(
        table_number=session.table_number,
        user_id=user_id,
        comment=order_request.comment,
        payment_method=order_request.payment_method,
        status=OrderStatus.pending
    )
    db.add(db_order)
    await db.flush()

    order_items = [
        OrderItem(order_id=db_order.id, menu_item_id=item.item_id, quantity=item.quantity)
        for item in order_request.items
    ]
    db.add_all(order_items)
    await db.commit()
    await db.refresh(db_order)

    payment_redirect_uri = None

    if order_request.payment_method == PaymentMethod.online:
        try:
            payment_payload = build_payment_payload(
                order=db_order,
                order_items=order_items,
                menu_items=menu_items_dict,
                buyer={
                    "email": user_info["email"],
                    "phone": settings.DEFAULT_PHONE_NUMBER,
                    "firstName": user_info.get("first_name"),
                    "lastName": user_info.get("last_name"),
                    "language": settings.DEFAULT_LANGUAGE,
                },
                order_id=db_order.id,
                customer_ip=settings.DEFAULT_CUSTOMER_IP,
                notify_url=settings.PAYMENT_NOTIFY_URL
            )

            payment_redirect_uri = await create_payment_request_and_wait_for_link(payment_payload)

            await send_order_status_notification(
                order_id=db_order.id,
                new_status="PENDING_PAYMENT_REDIRECT",
                email=user_info["email"]
            )

        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Payment initiation timed out.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initiate payment: {e}")

    return OrderResponse(
        message=f"Order placed successfully for table {session.table_number}.",
        order_id=db_order.id,
        payment_redirect_uri=payment_redirect_uri
    )


@router.get("/my", response_model=OrderListResponse)
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderListResponse:
    user_info: Dict[str, Any] = extract_user_info(authorization)
    user_id = user_info["sub"]

    result = await db.execute(select(TableSession).where(TableSession.user_id == user_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=400, detail="No active table session.")

    table_number = session.table_number

    stmt = select(Order).options(selectinload(Order.items).selectinload(OrderItem.menu_item)).where(
        Order.table_number == table_number
    )
    result = await db.execute(stmt)
    orders_from_db = result.scalars().all()

    if not orders_from_db:
        raise HTTPException(status_code=404, detail="No orders found.")

    summaries = []
    for order in orders_from_db:
        for item in order.items:
            summaries.append(OrderSummary(
                order_id=order.id,
                status=order.status.value,
                item_name=item.menu_item.name if item.menu_item else "Unknown",
                quantity=item.quantity,
                price=item.menu_item.price if item.menu_item else 0.0,
                payment_link=order.payment_link
            ))

    return OrderListResponse(
        table_number=table_number,
        retrieved_by_user_id=user_id,
        orders=summaries
    )


@router.delete("/{order_id}", response_model=OrderDeletedOut)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderDeletedOut:
    user_info = extract_user_info(authorization)
    user_id = user_info["sub"]

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found or unauthorized")

    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")

    order.status = OrderStatus.cancelled
    await db.commit()
    await db.refresh(order)

    session_result = await db.execute(select(TableSession).where(TableSession.user_id == user_id))
    session = session_result.scalar_one_or_none()
    table_number = session.table_number if session else None

    try:
        await publish_event(
            event_type="cancel_payment_request",
            payload={
                "order_service_order_id": order_id,
                "table_number": str(table_number),
                "user_id": str(user_id),
                "reason": "Order cancelled by user"
            },
            routing_key=settings.PAYMENT_QUEUE
        )
    except Exception as e:
        print(f"Error publishing cancellation event: {e}")

    await send_order_status_notification(
        order_id=order.id,
        new_status=order.status.value,
        email=user_info["email"]
    )

    return OrderDeletedOut(message="Order cancelled successfully", order_id=order.id)


@router.delete("/refund/{order_id}", response_model=OrderDeletedOut)
async def refund_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderDeletedOut:
    user_info = extract_user_info(authorization)
    user_id = user_info["sub"]

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found or unauthorized")

    # if order.status != OrderStatus.paid:
    #     raise HTTPException(status_code=400, detail="Only paid orders can be refunded")

    order.status = OrderStatus.refunded
    await db.commit()
    await db.refresh(order)

    session_result = await db.execute(select(TableSession).where(TableSession.user_id == user_id))
    session = session_result.scalar_one_or_none()
    table_number = session.table_number if session else None

    try:
        await publish_event(
            event_type="refund_payment_request",
            payload={
                "order_service_order_id": order_id,
                "table_number": str(table_number),
                "user_id": str(user_id),
                "reason": "Paid order refunded by user"
            },
            routing_key=settings.PAYMENT_QUEUE
        )
    except Exception as e:
        print(f"Error publishing refund event: {e}")

    await send_order_status_notification(
        order_id=order.id,
        new_status=order.status.value,
        email=user_info["email"]
    )

    return OrderDeletedOut(message="Order refunded successfully", order_id=order.id)
  