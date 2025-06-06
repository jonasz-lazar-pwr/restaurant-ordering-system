# === tests/staff-service/test_health_check.py ===

"""Health check test for the Staff Service.

Verifies that the /staff/health endpoint responds correctly,
indicating that the service is operational.
"""

import pytest
import httpx

from config import get_base_url, STAFF_ENDPOINTS

BASE_URL = get_base_url("staff-service")


@pytest.mark.asyncio
async def test_health_check():
    """Send GET to /staff/health → expect 200 OK and status response."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(STAFF_ENDPOINTS["health"])

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
