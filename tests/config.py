# tests/config.py

"""
Global test configuration.

This module defines configuration flags and service endpoint mappings
used by all test modules to determine whether to run tests directly
against services or through the Kong API Gateway.
"""

USE_KONG_GATEWAY = True  # Set "False" to test services directly without Kong

# Local service ports (used if USE_KONG_GATEWAY is False)
LOCAL_SERVICES = {
    "auth-service": 8002,
    "order-service": 8003,
    "payment-service": 8004,
    "notification-service": 8005,
}

# Kong API Gateway port (used if USE_KONG_GATEWAY is True)
KONG_GATEWAY_PORT = 8000


def get_base_url(service_name: str) -> str:
    """
    Get the base URL for a given service.

    Args:
        service_name: The name of the service (e.g., "auth-service").

    Returns:
        A full URL string to use as a base for test requests.

    Raises:
        ValueError: If the service name is unknown.
    """
    if USE_KONG_GATEWAY:
        return f"http://localhost:{KONG_GATEWAY_PORT}"
    port = LOCAL_SERVICES.get(service_name)
    if port is None:
        raise ValueError(f"Unknown service: {service_name}")
    return f"http://localhost:{port}"
