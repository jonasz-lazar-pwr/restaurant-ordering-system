"""Order endpoints for the Staff Service.

This module defines API routes that allow restaurant staff (chefs and waiters)
to view and update orders assigned to them.

Endpoints:
    - PUT /staff/orders/{order_id}/status
        Allows a staff member to update the status of a specific order.

    - GET /staff/orders
        Returns a filtered list of orders to be handled by the requesting staff member.

Authorization:
    All routes require a valid Bearer JWT token in the Authorization header.
    The user role (e.g., 'chef', 'waiter') determines access and permissions.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.db.deps import get_db
from api.models import Order, OrderStatus
from api.schemas.order import OrderStatusUpdate
from api.utils.auth import extract_user_info
from api.utils.permissions import validate_role_permission
from api.workers.producer import send_order_status_notification

router = APIRouter()


@router.put(
    "/orders/{order_id}/status",
    summary="Update order status",
    description=(
        "Update the status of an existing order. "
        "Only authorized staff members (chefs or waiters) can perform this action "
        "depending on their role and the target status."
    ),
    responses={
        200: {"description": "Order status successfully updated."},
        401: {"description": "Missing or invalid JWT token."},
        403: {"description": "Role not authorized to update to the requested status."},
        404: {"description": "Order not found."},
    },
)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> dict:
    """Update the status of a specific customer order.

    Depending on the user's role, this endpoint allows changing the order
    status to one of the allowed transitions (e.g., chef → 'in_progress', waiter → 'delivered').

    Args:
        order_id (int): Unique identifier of the order to update.
        payload (OrderStatusUpdate): Payload containing the new status to assign.
        db (AsyncSession): Asynchronous database session.
        authorization (str): Bearer token containing JWT with role info.

    Returns:
        dict: Confirmation message and the updated order ID.

    Raises:
        HTTPException: Raised when the user is unauthorized or the order does not exist.
    """
    user = extract_user_info(authorization)
    role = user.get("role")

    validate_role_permission(role, payload.new_status)

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.new_status
    await db.commit()
    await db.refresh(order)

    await send_order_status_notification(order.id, order.status.value)

    return {
        "message": f"Order status updated to '{order.status}'",
        "order_id": order.id,
    }


@router.get(
    "/orders",
    summary="List orders based on staff role",
    description=(
        "Returns a list of orders assigned to the authenticated staff member:\n\n"
        "- **Chef**: Sees all orders with status `'paid'` (awaiting preparation)\n"
        "- **Waiter**: Sees all orders with status `'ready'` (awaiting delivery)"
    ),
    responses={
        200: {"description": "List of matching orders returned successfully."},
        401: {"description": "Missing or invalid JWT token."},
        403: {"description": "Role not authorized to access this endpoint."},
    },
)
async def list_orders_for_staff(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> list[dict]:
    """Return a list of orders filtered based on the user's staff role.

    Chefs see orders ready to be prepared (status='paid'),
    while waiters see orders ready for delivery (status='ready').

    Args:
        db (AsyncSession): Asynchronous database session.
        authorization (str): Bearer token containing JWT with user role.

    Returns:
        list[dict]: List of orders including metadata and items.

    Raises:
        HTTPException: If the role is not authorized or JWT is invalid.
    """
    user = extract_user_info(authorization)
    role = user.get("role")

    if role == "chef":
        status_filter = OrderStatus.paid
    elif role == "waiter":
        status_filter = OrderStatus.ready
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' is not authorized to view orders."
        )

    result = await db.execute(
        select(Order)
        .where(Order.status == status_filter)
        .order_by(Order.created_at.asc())
    )
    orders = result.scalars().all()

    return [
        {
            "order_id": order.id,
            "table_number": order.table_number,
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "menu_item_id": item.menu_item_id,
                    "quantity": item.quantity,
                }
                for item in order.items
            ],
        }
        for order in orders
    ]
