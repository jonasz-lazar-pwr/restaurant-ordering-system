# === tests/config.py ===

"""Global test configuration for service integration testing.

This module defines shared constants and utility functions used across
test modules. It supports toggling between local service testing and
Kong API Gateway routing.
"""

USE_KONG_GATEWAY = True  # Set to "False" to test services directly without Kong.

# Kong API Gateway port (used when USE_KONG_GATEWAY is True).
KONG_GATEWAY_PORT = 8000

# Local service ports (used when USE_KONG_GATEWAY is False).
LOCAL_SERVICES = {
    "auth-service": 8002,
    "order-service": 8003,
    "staff-service": 8004,
    "payment-service": 8005,
    "notification-service": 8006,
}

# REST endpoint paths for the auth-service.
AUTH_ENDPOINTS = {
    "register": "/auth/register",
    "login": "/auth/jwt/login",
    "me": "/auth/users/me",
    "health": "/auth/health",
}

# REST endpoint paths for the order-service.
ORDER_ENDPOINTS = {
    "scan_qr": "/order/scan_qr",
    "create_order": "/order",
    "get_my_orders": "/order/my",
    "cancel_order": "/order",  # Append /{id} dynamically.
    "health": "/order/health",
}


def get_base_url(service_name: str) -> str:
    """Return the base URL for a given service.

    This function determines whether to route requests through Kong
    or directly to the service based on the global test configuration.

    Args:
        service_name: The unique name of the service (e.g., "auth-service").

    Returns:
        The full base URL as a string.

    Raises:
        ValueError: If the service name is not recognized.
    """
    if USE_KONG_GATEWAY:
        return f"http://localhost:{KONG_GATEWAY_PORT}"

    port = LOCAL_SERVICES.get(service_name)
    if port is None:
        raise ValueError(f"Unknown service: {service_name}")
    return f"http://localhost:{port}"
