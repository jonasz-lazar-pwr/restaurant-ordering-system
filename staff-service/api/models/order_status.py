# === api/models/order_status.py ===

"""Enumeration of possible statuses for a customer order in the restaurant."""

import enum


class OrderStatus(enum.Enum):
    """
    Enum representing the status of an order.

    Attributes:
        pending (str): Order has been created but not yet paid.
        paid (str): Order has been paid and is queued for preparation.
        in_progress (str): Order is being prepared by the kitchen.
        ready (str): Order is ready for pickup by a waiter.
        delivered (str): Order has been delivered to the customer.
        cancelled (str): Order has been cancelled by user or staff.
        failed (str): Order processing failed due to an issue (e.g., payment).
    """

    pending = "pending"
    paid = "paid"
    in_progress = "in_progress"
    ready = "ready"
    delivered = "delivered"
    cancelled = "cancelled"
    failed = "failed"
    refunded = "refunded"