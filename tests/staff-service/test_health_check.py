# tests/staff-service/test_health_check.py

"""
Tests for the /staff/health endpoint of the Staff Service.

These tests verify that the health check endpoint responds correctly and confirms
the service is up and running.
"""

import pytest
import httpx
from config import get_base_url

BASE_URL = get_base_url("staff-service")
HEALTH_ENDPOINT = "/staff/health"


@pytest.mark.asyncio
async def test_health_check():
    """Verify that /staff/health returns 200 and the correct response body."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(HEALTH_ENDPOINT)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
