# === api/schemas/qr.py ===

"""Schemas for QR code scanning and menu response."""

from pydantic import BaseModel, Field
from typing import List


class QRCodeIn(BaseModel):
    """Payload for scanning QR code."""
    code: str = Field(..., description="Scanned QR code representing the table number.")


class MenuItemOut(BaseModel):
    """Single item in the returned menu."""
    id: int = Field(..., description="ID of the menu item.")
    name: str = Field(..., description="Name of the menu item.")
    description: str = Field(..., description="Description of the menu item.")
    price: float = Field(..., description="Price of the menu item.")


class QRCodeMenuOut(BaseModel):
    """Response after scanning a QR code."""
    table_number: str = Field(..., description="Scanned table number.")
    message: str = Field(..., description="Confirmation message.")
    menu: List[MenuItemOut] = Field(..., description="List of menu items.")
