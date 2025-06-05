# === api/routes/scan.py ===

"""
QR Code scanning endpoint for the Order Service.

This module defines an endpoint for scanning a QR code to:
- Retrieve the current menu for a table.
- Associate the authenticated user with the scanned table (via TableSession).

Authentication:
    - Requires a valid Bearer token in the Authorization header.

Endpoints:
    POST /order/scan_qr:
        -> Scan QR code, assign table to user session, and return available menu.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.db.deps import get_db
from api.models import MenuItem, TableSession
from api.utils.auth import extract_user_info
from api.schemas.qr import QRCodeMenuOut, MenuItemOut, QRCodeIn

router = APIRouter()


@router.post(
    "/scan_qr",
    response_model=QRCodeMenuOut,
    summary="Scan QR code",
    description=(
        "Scan a QR code to retrieve the table's menu and assign the table to the user session. "
        "Requires a valid JWT token in the Authorization header."
    ),
    tags=["QR & Menu"]
)
async def scan_qr(
    qr: QRCodeIn,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
) -> QRCodeMenuOut:
    """
    Assign a scanned table number to the authenticated user and return the current menu.

    This endpoint allows a logged-in user to scan a QR code to access the menu for a specific table.
    It also records the association between the user and the table in the database.

    Args:
        qr (QRCodeIn): QR code payload containing the table number.
        db (AsyncSession): Asynchronous database session.
        authorization (str): Bearer token for authentication.

    Returns:
        QRCodeMenuOut: Structured response containing the table number and the list of menu items.

    Raises:
        HTTPException: Raised if the QR code is invalid or if the menu is unavailable.
    """
    user_info = extract_user_info(authorization)
    user_id = user_info["sub"]

    table_number = qr.code.strip()
    if not table_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid QR code"
        )

    # Create or update the user's table session
    result = await db.execute(
        select(TableSession).where(TableSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()

    if session:
        session.table_number = table_number
        session.created_at = datetime.utcnow()
    else:
        db.add(TableSession(user_id=user_id, table_number=table_number))

    # Retrieve all available menu items
    result = await db.execute(select(MenuItem))
    menu_items = result.scalars().all()

    if not menu_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found."
        )

    await db.commit()

    return QRCodeMenuOut(
        message=(
            f"QR Code scanned successfully for table {table_number}. "
            f"Table assigned to user session."
        ),
        table_number=table_number,
        menu=[
            MenuItemOut(
                id=item.id,
                name=item.name,
                description=item.description,
                price=item.price
            ) for item in menu_items
        ]
    )
