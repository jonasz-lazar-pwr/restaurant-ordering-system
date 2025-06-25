# === tests/order-service/test_scan_qr.py ===

"""Tests for the POST /order/scan_qr endpoint of the Order Service.

Covers the following scenarios:
- Valid QR scan by authenticated user
- QR scan with empty code
- QR scan without authorization token
"""

import uuid
import pytest
import httpx

from config import get_base_url, AUTH_ENDPOINTS, ORDER_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")
ORDER_BASE_URL = get_base_url("order-service")


@pytest.mark.asyncio
async def test_scan_qr_authenticated_user_success():
    """Register + login → scan valid QR code → expect 200 with table and menu info."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Alice",
        "last_name": "Tester",
        "role": "client"
    }

    async with httpx.AsyncClient() as client:
        # Register and login
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Scan QR
        payload = {"code": "12"}
        response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["table_number"] == "12"
        assert isinstance(data["menu"], list)
        if data["menu"]:
            assert all(k in data["menu"][0] for k in ("id", "name", "description", "price"))


@pytest.mark.asyncio
async def test_scan_qr_empty_code_returns_400():
    """Scan QR with empty code → expect 400 Bad Request and error message."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Bob",
        "last_name": "Tester",
        "role": "client"
    }

    async with httpx.AsyncClient() as client:
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        payload = {"code": ""}
        response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json=payload, headers=headers)

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid QR code"


@pytest.mark.asyncio
async def test_scan_qr_unauthorized_access():
    """Scan QR without token → expect 422 or 401 depending on FastAPI behavior."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}",
            json={"code": "5"}
        )

    assert response.status_code in (401, 422)
