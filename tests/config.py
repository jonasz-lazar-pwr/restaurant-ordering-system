# === tests/config.py ===

"""Global test configuration for service integration testing.

This module defines shared constants and utility functions used across
test modules. It supports toggling between direct service calls and
requests routed through the Kong API Gateway.
"""

# === Kong Gateway and Local Service Routing ===

USE_KONG_GATEWAY = True  # Set to "False" to bypass Kong and call services directly.

KONG_GATEWAY_PORT = 8000  # Port where Kong Gateway is exposed.

LOCAL_SERVICES = {
    "auth-service": 8002,
    "order-service": 8003,
    "staff-service": 8004,
    "payment-service": 8005,
    "notification-service": 8006,
}

# === REST Endpoint Definitions ===

AUTH_ENDPOINTS = {
    "register": "/auth/register",
    "login": "/auth/jwt/login",
    "me": "/auth/users/me",
    "health": "/auth/health",
}

ORDER_ENDPOINTS = {
    "scan_qr": "/order/scan_qr",
    "create_order": "/order",
    "get_my_orders": "/order/my",
    "cancel_order": "/order",  # Append /{id} dynamically.
    "health": "/order/health",
}


def get_base_url(service_name: str) -> str:
    """Resolve the base URL for a given service.

    This function checks whether Kong Gateway is enabled. If so, it
    returns the gateway's base URL. Otherwise, it returns the local
    port of the specified service.

    Args:
        service_name (str): The name of the service (e.g., 'auth-service').

    Returns:
        str: The full base URL to use in test requests.

    Raises:
        ValueError: If the service name is not recognized.
    """
    if USE_KONG_GATEWAY:
        return f"http://localhost:{KONG_GATEWAY_PORT}"

    port = LOCAL_SERVICES.get(service_name)
    if port is None:
        raise ValueError(f"Unknown service: {service_name}")
    return f"http://localhost:{port}"


# === RabbitMQ Configuration ===

RABBITMQ_URL = "amqp://admin:admin@localhost:5672/"

# RabbitMQ exchange names
PAYMENTS_EXCHANGE_NAME = "payments_exchange"
NOTIFICATIONS_EXCHANGE_NAME = "notifications_exchange"

# RabbitMQ routing keys for event types
ROUTING_KEY_USER_CREATED = "user.created"
ROUTING_KEY_PAYMENT_INITIATED = "payment.initiated"
ROUTING_KEY_ORDER_PAID = "order.paid"
ROUTING_KEY_ORDER_CANCELLED = "order.cancelled"
ROUTING_KEY_ORDER_FAILED = "order.failed"
