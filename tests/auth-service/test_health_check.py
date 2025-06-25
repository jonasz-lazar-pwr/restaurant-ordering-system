# === tests/auth-service/test_health_check.py ===

"""Tests for the /auth/health endpoint of the Auth Service.

This test verifies that the health check endpoint responds with HTTP 200
and confirms the service is operational.
"""

import pytest
import httpx
from config import get_base_url, AUTH_ENDPOINTS

AUTH_BASE_URL = get_base_url("auth-service")


@pytest.mark.asyncio
async def test_health_check():
    """
    Ensure the /auth/health endpoint returns HTTP 200 and correct status message.

    Returns:
        None. Uses assertions to validate the behavior.
    """
    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.get(AUTH_ENDPOINTS["health"])

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
