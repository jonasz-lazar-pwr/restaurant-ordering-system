# === tests/order-service/test_create_order.py ===

"""Tests for the POST /order/ endpoint of the Order Service."""

import pytest
import httpx

from config import get_base_url, AUTH_ENDPOINTS, ORDER_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")
ORDER_BASE_URL = get_base_url("order-service")


@pytest.mark.asyncio
async def test_order_creation_success():
    """Register + login → scan QR → place order → expect 200 and order ID."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Alice",
        "last_name": "Orderer",
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

        # Scan QR and place order
        await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json={"code": "12"}, headers=headers)
        payload = {
            "items": [{"item_id": 1, "quantity": 2}],
            "comment": "Extra spicy",
            "payment_method": "online"
        }

        response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json=payload, headers=headers)
        assert response.status_code == 200
        assert "order_id" in response.json()


@pytest.mark.asyncio
async def test_order_creation_invalid_menu_item():
    """Place order with invalid menu item → expect 404 Not Found."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Bob",
        "last_name": "InvalidMenu",
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

        await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json={"code": "12"}, headers=headers)

        payload = {
            "items": [{"item_id": 9999, "quantity": 1}],
            "comment": "Fake item",
            "payment_method": "cash"
        }

        response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json=payload, headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "One or more menu items not found."


@pytest.mark.asyncio
async def test_order_creation_without_table_session():
    """Place order without scanning QR → expect 400 Bad Request."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Carol",
        "last_name": "NoQR",
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

        payload = {
            "items": [{"item_id": 1, "quantity": 1}],
            "comment": "No QR",
            "payment_method": "cash"
        }

        response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json=payload, headers=headers)
        assert response.status_code == 400
        assert response.json()["detail"] == "No active table session. Please scan QR code first."


@pytest.mark.asyncio
async def test_order_creation_unauthorized():
    """Place order without token → expect 401 or 422."""
    payload = {
        "items": [{"item_id": 1, "quantity": 1}],
        "comment": "Missing token",
        "payment_method": "cash"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json=payload)

    assert response.status_code in (401, 422)
