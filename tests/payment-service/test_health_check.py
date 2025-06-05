# tests/payment-service/test_health_check.py

"""
Tests for the /payment/health endpoint of the Payment Service.

These tests verify that the health check endpoint responds correctly and confirms
the service is up and running.
"""

import pytest
import httpx
from config import get_base_url

BASE_URL = get_base_url("payment-service")
HEALTH_ENDPOINT = "/payment/health"


@pytest.mark.asyncio
async def test_health_check():
    """Verify that /payment/health returns 200 and the correct response body."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(HEALTH_ENDPOINT)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
