# === api/schemas/order.py ===

"""Schemas for order creation and retrieval."""

from typing import List
from enum import Enum
from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    """Supported payment methods."""
    online = "online"
    cash = "cash"


class OrderItemIn(BaseModel):
    """Single menu item in an order request."""
    item_id: int = Field(..., description="ID of the menu item to be ordered.")
    quantity: int = Field(..., gt=0, description="Quantity of the item.")


class OrderRequest(BaseModel):
    """Payload for placing a new order."""
    items: List[OrderItemIn] = Field(..., description="List of menu items with quantities.")
    comment: str | None = Field(None, description="Optional comment for the order.")
    payment_method: PaymentMethod = Field(..., description="Chosen payment method.")


class OrderResponse(BaseModel):
    """Response after placing a new order."""
    message: str = Field(..., description="Success message including table number and email.")
    order_id: int = Field(..., description="ID of the newly created order.")


class OrderSummary(BaseModel):
    """Summary of a single ordered item."""
    order_id: int = Field(..., description="ID of the order.")
    status: str = Field(..., description="Status of the order.")
    item_name: str = Field(..., description="Name of the menu item.")
    quantity: int = Field(..., description="Ordered quantity.")
    price: float = Field(..., description="Unit price of the item.")


class OrderListResponse(BaseModel):
    """Response containing all orders for the currently assigned table."""
    table_number: str = Field(..., description="Assigned table number from session.")
    retrieved_by_user_id: str = Field(..., description="ID of the user requesting the orders.")
    orders: List[OrderSummary] = Field(..., description="List of order summaries.")


class OrderDeletedOut(BaseModel):
    """Response after a successful order cancellation."""
    message: str = Field(..., description="Confirmation message for deleted order")
    order_id: int = Field(..., description="ID of the cancelled order")
