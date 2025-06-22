# === api/routes/order.py ===

"""
Order endpoints for the Order Service.

This module defines API routes for placing, retrieving, updating, and canceling orders.

Endpoints:
    POST   /order/               -> Place a new order (requires JWT)
    GET    /order/me             -> Get all orders for a given table (requires JWT)
    DELETE /order/{id}           -> Cancel an order (requires JWT)

Features:
- Creating a new order with multiple items for a specific table.
- Retrieving all orders for a specific table with item and user details.
- Allowing clients to cancel orders that are still in "pending" status.
- QR code scanning to retrieve the current menu.

Authorization:
- All endpoints require a valid Bearer token (JWT) in the Authorization header,
  except for the QR scan endpoint, which is public.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.db.deps import get_db
from api.core.config import settings
from api.models import MenuItem, Order, OrderItem, OrderStatus, TableSession
from api.schemas.order import OrderRequest, OrderResponse, OrderListResponse, OrderSummary, OrderDeletedOut
from api.utils.auth import extract_user_info
# from api.workers.producer import send_order_to_payment, send_order_status_notification
from api.workers.producer import send_order_status_notification

from api.utils.payment_payload_builder import build_payment_payload
from api.workers.producer import create_payment_request_and_wait_for_link, publish_event
import asyncio

router = APIRouter()


@router.post(
    "",
    response_model=OrderResponse,
    summary="Place an order",
    description="Create a new order for a table with one or more menu items."
)
async def order_item(
    order_request: OrderRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
) -> OrderResponse:
    """Create a new order based on the provided QR code and menu item IDs.

    Args:
        order_request (OrderRequest): Payload containing QR code, menu item IDs, quantities, comment, and payment method.
        db (AsyncSession): SQLAlchemy async session.
        authorization (str): JWT Bearer token.

    Returns:
        OrderResponse: Confirmation message and order ID, potentially with payment redirect URL.

    Raises:
        HTTPException: If any of the menu items do not exist, no active session, or payment fails/timeouts.
    """
    user_info: Dict[str, Any] = extract_user_info(authorization)
    user_id = user_info["sub"]
    user_email = user_info.get("email")

    item_ids = [item.item_id for item in order_request.items]
    result = await db.execute(select(MenuItem).where(MenuItem.id.in_(item_ids)))
    menu_items = {item.id: item for item in result.scalars().all()}

    if len(menu_items) != len(item_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more menu items not found."
        )

    # Find table number from TableSession
    session_result = await db.execute(
        select(TableSession).where(TableSession.user_id == user_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active table session. Please scan QR code first."
        )
    table_number = session.table_number

    db_order = Order(
        table_number=table_number,
        user_id=user_id,
        comment=order_request.comment,
        payment_method=order_request.payment_method # Zakładamy, że to "online" dla płatności
    )

    db.add(db_order)
    await db.flush()  # Ensure order ID is available before adding items

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

    # --- NOWA LOGIKA DLA SYNCHRONICZNEGO RPC PŁATNOŚCI ---
    payment_redirect_uri = None # Domyślnie None
    try:
        # Pobierz IP klienta z żądania HTTP
        customer_ip = settings.DEFAULT_CUSTOMER_IP

        payment_payload = build_payment_payload(
            order=db_order,
            order_items=order_items,
            menu_items=menu_items,
            buyer={
                "email": user_info["email"],
                "phone": settings.DEFAULT_PHONE_NUMBER,
                "firstName": user_info.get("first_name"),
                "lastName": user_info.get("last_name"),
                "language": settings.DEFAULT_LANGUAGE
            },
            order_id=db_order.id,
            customer_ip=customer_ip,
            notify_url=settings.PAYMENT_NOTIFY_URL
        )

        # Wywołujemy funkcję RPC i czekamy na link
        payment_redirect_uri = await create_payment_request_and_wait_for_link(payment_payload)

        # Opcjonalnie: Zaktualizuj status zamówienia w bazie danych na "oczekuje na płatność"
        # db_order.status = "PENDING_PAYMENT"
        # await db.commit()

        # Opcjonalnie: Wyślij asynchroniczne powiadomienie o nowym zamówieniu/statusie
        await send_order_status_notification(
            order_id=db_order.id,
            new_status="PENDING_PAYMENT_REDIRECT",
            email=user_email
        )

    except asyncio.TimeoutError:
        # Płatność nie odpowiedziała w określonym czasie
        print(f"Payment service timed out for order {db_order.id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Payment initiation timed out. Please try again."
        )
    except Exception as e:
        # Inne błędy podczas komunikacji RPC lub przetwarzania płatności
        print(f"Error initiating payment for order {db_order.id}: {e}")
        # Możesz tutaj obsłużyć bardziej szczegółowo: czy anulować zamówienie? Czy oznaczyć jako błąd?
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate payment: {e}"
        )
    # --- KONIEC NOWEJ LOGIKI ---

    return OrderResponse(
        message=f"Order placed successfully for table {table_number}.",
        order_id=db_order.id,
        payment_redirect_uri=payment_redirect_uri
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

    The table is determined based on the last scanned QR code stored in the session.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        authorization (str): JWT Bearer token.

    Returns:
        OrderListResponse: All orders for the table with item summaries.

    Raises:
        HTTPException: If the user has no active session or no orders are found.
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

    Only the user who created the order can cancel it, and only if it is still pending.

    Args:
        order_id (int): ID of the order to cancel.
        db (AsyncSession): Async database session.
        authorization (str): Bearer JWT token.

    Returns:
        OrderDeletedOut: Confirmation message and cancelled order ID.

    Raises:
        HTTPException: If the order does not exist, does not belong to the user,
                       or is not in a cancellable state.
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

    # Find table number from TableSession
    session_result = await db.execute(
        select(TableSession).where(TableSession.user_id == user_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active table session. Please scan QR code first."
        )
    table_number = session.table_number

    try:
        await publish_event(
            event_type="cancel_payment_request", # <<< TYP WIADOMOŚCI DLA ANULOWANIA
            payload={
                "order_service_order_id": order_id,
                "table_number": str(table_number),
                "user_id": str(user_id),
                "reason": "Order cancelled by user in order-service"
            },
            routing_key=settings.PAYMENT_QUEUE
        )
    except Exception as e:
        print(f"[OrderService] Failed to publish payment cancellation message for order {order_id}: {e}")

    await send_order_status_notification(
        order_id=order.id,
        new_status=order.status.value,
        email=user_info["email"]
    )

    return OrderDeletedOut(message="Order cancelled successfully", order_id=order.id)

@router.delete(
    "/refund/{order_id}",
    response_model=OrderDeletedOut,
    summary="Refund order",
    description="Refund an order that already has been paid for."
)
async def refund_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> OrderDeletedOut:
    user_info = extract_user_info(authorization)
    user_id = user_info["sub"]

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only cancel your own orders")

    # ======= ODKOMENTOWAĆ, JEŻELI ORDER ZMIENIA STATUS ZAMÓWIENIA NA 'paid'
    # if order.status != OrderStatus.paid:
    #     raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")

    order.status = OrderStatus.refunded
    await db.commit()
    await db.refresh(order)

    # Find table number from TableSession
    session_result = await db.execute(
        select(TableSession).where(TableSession.user_id == user_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active table session. Please scan QR code first."
        )
    table_number = session.table_number

    try:
        await publish_event(
            event_type="refund_payment_request", # <<< TYP WIADOMOŚCI DLA REFUNDOWANIA
            payload={
                "order_service_order_id": order_id,
                "table_number": str(table_number),
                "user_id": str(user_id),
                "reason": "Paid order refunded by user in order-service"
            },
            routing_key=settings.PAYMENT_QUEUE
        )
    except Exception as e:
        print(f"[OrderService] Failed to publish payment refund message for order {order_id}: {e}")

    await send_order_status_notification(
        order_id=order.id,
        new_status=order.status.value,
        email=user_info["email"]
    )

    return OrderDeletedOut(message="Order refunded successfully", order_id=order.id)