# === tests/payment-service/test_health_check.py ===

"""Health check test for the Payment Service.

Verifies that the /payment/health endpoint responds correctly,
indicating that the service is operational.
"""

import pytest
import httpx

from config import get_base_url, PAYMENT_ENDPOINTS

BASE_URL = get_base_url("payment-service")


@pytest.mark.asyncio
async def test_health_check():
    """Send GET to /payment/health → expect 200 OK and status response."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(PAYMENT_ENDPOINTS["health"])

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
