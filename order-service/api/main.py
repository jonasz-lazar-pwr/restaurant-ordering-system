from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from .models import MenuItem, Order
from .schemas import QRCode, OrderRequest
from .core import simulate_qr_scan
from .init_db import get_db, init_db
from sqlalchemy.orm import selectinload
from collections import Counter

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_db()


# Temporary simulated menu
menu_items = [
    MenuItem(id=1, name="Pizza Margherita", description="Classic pizza with tomato, mozzarella, and basil",
             price=12.50),
    MenuItem(id=2, name="Spaghetti Carbonara", description="Spaghetti with creamy carbonara sauce and pancetta",
             price=14.00),
    MenuItem(id=3, name="Caesar Salad", description="Fresh salad with romaine, croutons, and Caesar dressing",
             price=8.00),
]

# Temporary simulated orders per table
orders = {}


# Endpoint to handle scanning QR code and showing menu
@app.post("/scan_qr/")
def scan_qr(qr: QRCode):
    # Check if qr code is correct
    if simulate_qr_scan(qr.code):
        table_number = qr.code
        if table_number not in orders:
            orders[table_number] = []  # Create an empty order
        return {"message": f"QR Code scanned successfully! Here's the menu for table {table_number}:",
                "menu": menu_items}
    raise HTTPException(status_code=400, detail="Invalid QR code")


# Endpoint to handle orders
@app.post("/order/")
async def order_item(order: OrderRequest, db: AsyncSession = Depends(get_db)):
    table_number = order.qr_code
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == order.item_id)
    )
    menu_item = result.scalar_one_or_none()

    if menu_item:
        db_order = Order(table_number=table_number, menu_item_id=menu_item.id)
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)
        return {"message": f"Ordered {menu_item.name} for table {table_number} successfully!"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


# Endpoint to check table's order
@app.get("/orders/{table_number}")
async def get_orders(table_number: str, db: AsyncSession = Depends(get_db)):
    result_orders = await db.execute(
        select(Order).options(selectinload(Order.menu_item)).where(Order.table_number == table_number)
    )
    orders = result_orders.scalars().all()

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found for this table")

    item_counter = Counter(order.menu_item_id for order in orders)

    ordered_items = []
    for order in orders:
        menu_item = order.menu_item
        ordered_items.append({
            "item": menu_item.name,
            "quantity": item_counter[menu_item.id]
        })

    return {
        "table": table_number,
        "orders": ordered_items
    }