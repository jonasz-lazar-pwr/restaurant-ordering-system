# === tests/order-service/test_health_check.py ===

"""Health check test for the Order Service.

Verifies that the /order/health endpoint responds correctly,
indicating that the service is operational.
"""

import pytest
import httpx

from config import get_base_url, ORDER_ENDPOINTS

BASE_URL = get_base_url("order-service")


@pytest.mark.asyncio
async def test_health_check():
    """Send GET to /order/health → expect 200 OK and status response."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(ORDER_ENDPOINTS["health"])

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
