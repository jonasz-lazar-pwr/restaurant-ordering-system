# api/main.py

import aio_pika
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from api.core.config import settings
from api.core.middleware import add_middleware
from api.db.deps import get_db
from api.models.models import MenuItem, Order
from api.schemas.schemas import QRCode, OrderRequest
from api.utils import simulate_qr_scan
from sqlalchemy import select
from sqlalchemy.orm import selectinload


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up Order Service...")
    yield
    print("Shutting down Order Service...")

app = FastAPI(
    title="Order Service",
    description="Order Service API for managing orders and payments.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware for development
add_middleware(app)


async def send_order_to_payment(order_id: int):
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=str(order_id).encode()),
        routing_key="payments_queue"
    )
    await connection.close()

@app.get(
    "/order/health",
    summary="Health check",
    description="Basic health check endpoint",
    tags=["Health"]
)
def health_check():
    """Simple health check endpoint that returns 200 OK."""
    return {"status": "ok"}


# Endpoint to handle scanning QR code and showing menu
@app.post("/order/scan_qr/")
async def scan_qr(qr: QRCode, db: AsyncSession = Depends(get_db)):
    # Wersja z odczytem menu z bazy
    if simulate_qr_scan(qr.code):
        table_number = qr.code

        # Pobierz menu z bazy danych
        result = await db.execute(select(MenuItem))
        menu_from_db = result.scalars().all()

        if not menu_from_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found.")

        return {
            "message": f"QR Code scanned successfully for table {table_number}! Here's the menu:",
            "menu": [{"id": item.id, "name": item.name, "description": item.description, "price": item.price} for item
                     in menu_from_db]
        }
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QR code")


# Endpoint to handle orders
@app.post("/order/")
async def order_item(
        order_request: OrderRequest,
        db: AsyncSession = Depends(get_db),
        x_user_payload_str: Optional[str] = Header(None, alias="X-User-Payload")
):
    if not x_user_payload_str:
        # Ten błąd powinien być przechwycony przez API Gateway, ale jako zabezpieczenie
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Payload header missing. Authentication required via API Gateway."
        )

    try:
        user_payload: Dict[str, Any] = json.loads(x_user_payload_str)
        user_id = user_payload.get("sub")
        user_role = user_payload.get("role")
        user_email_from_payload = user_payload.get("email")
        if not user_id or not user_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Payload content.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed X-User-Payload header.")

    print(
        f"Order received from user_id: {user_id} (role: {user_role}) for table {order_request.qr_code}")

    result = await db.execute(
        select(MenuItem).where(MenuItem.id == order_request.item_id)
    )
    menu_item = result.scalar_one_or_none()

    if menu_item:
        db_order = Order(
            table_number=order_request.qr_code, # ZMIANA TUTAJ
            menu_item_id=menu_item.id,
            user_id=user_id
        )
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)

        # asyncio.create_task(send_order_to_payment(db_order.id))

        return {
            "message": f"Ordered '{menu_item.name}' for table {order_request.qr_code} by user with email {user_email_from_payload} successfully!",
            "order_id": db_order.id
        }
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


# Endpoint to check table's order
@app.get("/order/{table_number}")
async def get_orders(
        table_number: str,
        db: AsyncSession = Depends(get_db),
        x_user_payload_str: Optional[str] = Header(None, alias="X-User-Payload")
):
    if not x_user_payload_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Payload header missing. Authentication required via API Gateway."
        )

    try:
        user_payload: Dict[str, Any] = json.loads(x_user_payload_str)
        user_id = user_payload.get("sub")
        user_role = user_payload.get("role")

        if not user_id or not user_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Payload content.")

    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed X-User-Payload header.")

    print(f"User {user_id} (role: {user_role}) requesting orders for table {table_number}")

    # Uproszczona wersja bez filtrowania po user_id na razie:
    stmt = select(Order).options(selectinload(Order.menu_item)).where(Order.table_number == table_number)

    result_db_orders = await db.execute(stmt)  # Zmieniono nazwę
    orders_from_db = result_db_orders.scalars().all()

    if not orders_from_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found for this table.")

    ordered_items_details = []
    for o in orders_from_db:
        if o.menu_item:
            ordered_items_details.append({
                "order_id": o.id,
                "item_name": o.menu_item.name,
                "price": o.menu_item.price,
            })
        else:  # Powinno się rzadko zdarzyć, jeśli dane są spójne
            ordered_items_details.append({"order_id": o.id, "item_name": "Unknown item (data inconsistency)"})

    return {
        "table": table_number,
        "retrieved_by_user_id": user_id,
        "orders": ordered_items_details
    }
