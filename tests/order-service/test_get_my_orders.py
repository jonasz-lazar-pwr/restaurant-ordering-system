# === order-service/test_get_my_orders.py ===

"""Tests for the GET /order/my endpoint of the Order Service."""

import uuid
import pytest
import httpx

from config import get_base_url, AUTH_ENDPOINTS, ORDER_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")
ORDER_BASE_URL = get_base_url("order-service")


@pytest.mark.asyncio
async def test_get_my_orders_success():
    """Test successful retrieval of orders after scanning QR and placing an order."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Alice",
        "last_name": "Viewer",
        "role": "client"
    }

    async with httpx.AsyncClient() as client:
        # Register and login
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login_response = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Scan QR code
        await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json={"code": "12"}, headers=headers)

        # Place an order
        await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json={
            "items": [{"item_id": 1, "quantity": 1}],
            "comment": "Test",
            "payment_method": "cash"
        }, headers=headers)

        # Fetch orders
        response = await client.get(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['get_my_orders']}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert len(data["orders"]) > 0


@pytest.mark.asyncio
async def test_get_my_orders_no_session_returns_400():
    """Test that order retrieval fails with 400 if QR scan session is missing."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "No",
        "last_name": "Session",
        "role": "client"
    }

    async with httpx.AsyncClient() as client:
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login_response = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['get_my_orders']}", headers=headers)
        assert response.status_code == 400
        assert response.json()["detail"] == "No active table session. Please scan QR code first."


@pytest.mark.asyncio
async def test_get_my_orders_no_orders_returns_404():
    """Test that order retrieval fails with 404 if no orders exist for the scanned table."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "No",
        "last_name": "Orders",
        "role": "client"
    }

    unique_table_code = f"test_table_{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient() as client:
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login_response = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Scan QR code for a unique, unused table
        await client.post(
            f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}",
            json={"code": unique_table_code},
            headers=headers
        )

        response = await client.get(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['get_my_orders']}", headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "No orders found for this table."
