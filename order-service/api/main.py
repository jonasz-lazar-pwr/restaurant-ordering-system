from fastapi import FastAPI, HTTPException
from typing import List
from .models import MenuItem
from .schemas import QRCode, OrderRequest
from .core import simulate_qr_scan

app = FastAPI()

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
def order_item(order: OrderRequest):
    table_number = order.qr_code
    if table_number not in orders:
        raise HTTPException(status_code=400, detail="QR code not scanned yet or invalid.")

    # Find item in the menu
    item = next((item for item in menu_items if item.id == order.item_id), None)
    if item:
        orders[table_number].append(item)  # Add item to the order
        return {"message": f"Ordered {item.name} for table {table_number} successfully!"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


# Endpoint to check table's order
@app.get("/orders/{table_number}")
def get_orders(table_number: str):
    if table_number in orders:
        return {"table": table_number, "orders": orders[table_number]}
    raise HTTPException(status_code=404, detail="Table not found")
