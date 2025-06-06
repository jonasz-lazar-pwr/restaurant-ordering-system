# === api/utils/payment_payload_builder.py ===

"""
Helper for building a full payment request payload to be sent to the payment-service.

Used by order-service to generate a message conforming to CreatePaymentRequest schema.
"""

from typing import Any, Dict, List
from api.models import Order, OrderItem, MenuItem


def build_payment_payload(
    order: Order,
    order_items: List[OrderItem],
    menu_items: Dict[int, MenuItem],
    buyer: Dict[str, Any],
    customer_ip: str,
    notify_url: str
) -> Dict[str, Any]:
    """Construct a full payment payload from order data.

    Args:
        order (Order): The Order object.
        order_items (List[OrderItem]): List of items in the order.
        menu_items (Dict[int, MenuItem]): Mapping of menu_item_id to MenuItem.
        buyer (Dict[str, Any]): Dict with buyer info (email, phone, firstName, lastName, language).
        customer_ip (str): The IP address of the customer.
        notify_url (str): URL that PayU will notify after payment completion.

    Returns:
        Dict[str, Any]: Full payload compatible with CreatePaymentRequest model.
    """
    products = [
        {
            "name": menu_items[item.menu_item_id].name,
            "unitPrice": str(int(menu_items[item.menu_item_id].price * 100)),  # price in grosze
            "quantity": str(item.quantity)
        }
        for item in order_items
    ]

    total_amount = sum(
        int(menu_items[item.menu_item_id].price * 100) * item.quantity
        for item in order_items
    )

    return {
        "notifyUrl": notify_url,
        "customerIp": customer_ip,
        "description": f"Order #{order.id} for table {order.table_number}",
        "currencyCode": "PLN",
        "totalAmount": str(total_amount),
        "buyer": buyer,
        "products": products
    }
