# === api/schemas/order.py ===

"""Pydantic schemas for order management in the Staff Service."""

from pydantic import BaseModel, Field
from api.models.order_status import OrderStatus


class OrderStatusUpdate(BaseModel):
    """Schema for updating the status of an order."""
    new_status: OrderStatus = Field(..., description="New status to assign to the order.")

class OrderItemOut(BaseModel):
    item_id: int
    quantity: int

class OrderOut(BaseModel):
    id: int
    table_number: str
    status: OrderStatus
    items: list[OrderItemOut]