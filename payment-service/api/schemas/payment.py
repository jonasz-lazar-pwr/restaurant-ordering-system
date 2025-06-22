# === api/schemas/payment.py ===

"""Schemas for PayU payment requests and responses.

Defines models for product details, buyer information, and request payloads
for creating and refunding orders via the PayU API.
"""

from typing import List
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Model representing a product in the order."""

    name: str = Field(..., description="Name of the product.")
    unitPrice: str = Field(..., description="Unit price of the product in minor currency unit (e.g., grosze).")
    quantity: str = Field(..., description="Quantity of the product.")


class Buyer(BaseModel):
    """Model representing the buyer information."""

    email: str = Field(..., description="Buyer's email address.")
    phone: str = Field(..., description="Buyer's phone number.")
    firstName: str = Field(..., alias="firstName", description="Buyer's first name.")
    lastName: str = Field(..., alias="lastName", description="Buyer's last name.")
    language: str = Field(..., description="Language code (e.g., 'pl').")

class CreatePaymentRequest(BaseModel):
    """Request schema for creating a payment order."""

    notifyUrl: str = Field(..., description="Notification URL for order status updates.")
    customerIp: str = Field(..., description="Customer's IP address.")
    description: str = Field(..., description="Description of the order.")
    currencyCode: str = Field(..., description="Currency code (e.g., 'PLN').")
    totalAmount: str = Field(..., description="Total amount of the order in minor currency unit (e.g., grosze).")
    buyer: Buyer = Field(..., description="Information about the buyer.")
    products: List[Product] = Field(..., description="List of products in the order.")
    tableNumber: str = Field(..., description="Number of the table from which the order was made.")
    userId: str = Field(..., description="Customer's unique ID.")


class CreateRefundRequest(BaseModel):
    """Request schema for creating a refund."""

    description: str = Field(..., description="Reason or description for the refund.")
    currencyCode: str = Field(..., description="Currency code for the refund (e.g., 'PLN').")
