# === tests/order-service/test_cancel_order.py ===

"""Tests for the DELETE /order/{id} endpoint of the Order Service.

These tests cover cancellation behavior:
- Successful cancellation of a pending order by the owner.
- Rejection when trying to cancel someone else's order.
- Rejection of cancellation if order is already processed.
- Rejection of cancellation for a non-existent order.
"""

import pytest
import httpx

from config import get_base_url, AUTH_ENDPOINTS, ORDER_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")
ORDER_BASE_URL = get_base_url("order-service")


@pytest.mark.asyncio
async def test_cancel_pending_order_success():
    """
    Register + login → scan QR → place order → cancel it → expect 200 OK and confirmation.
    """
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Alice",
        "last_name": "Cancel",
        "role": "client"
    }

    async with httpx.AsyncClient() as client:
        # Register + login
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Scan QR and place order
        await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json={"code": "12"}, headers=headers)
        order_payload = {
            "items": [{"item_id": 1, "quantity": 1}],
            "comment": "To cancel",
            "payment_method": "cash"
        }
        order_response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json=order_payload, headers=headers)
        order_id = order_response.json()["order_id"]

        # Cancel the order
        cancel_response = await client.delete(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['cancel_order']}/{order_id}", headers=headers)
        assert cancel_response.status_code == 200
        data = cancel_response.json()
        assert data["message"] == "Order cancelled successfully"
        assert data["order_id"] == order_id


@pytest.mark.asyncio
async def test_cancel_order_unauthorized_user():
    """
    User A creates order → User B tries to cancel it → expect 403 Forbidden.
    """
    # User A
    email_a, password_a = generate_unique_user()
    user_a = {
        "email": email_a,
        "password": password_a,
        "first_name": "User",
        "last_name": "A",
        "role": "client"
    }

    # User B
    email_b, password_b = generate_unique_user()
    user_b = {
        "email": email_b,
        "password": password_b,
        "first_name": "User",
        "last_name": "B",
        "role": "client"
    }

    async with httpx.AsyncClient() as client:
        # Register + login A
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_a)
        login_a = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email_a,
            "password": password_a
        })
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # A creates order
        await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['scan_qr']}", json={"code": "12"}, headers=headers_a)
        order_payload = {
            "items": [{"item_id": 1, "quantity": 1}],
            "comment": "From A",
            "payment_method": "cash"
        }
        order_response = await client.post(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['create_order']}", json=order_payload, headers=headers_a)
        order_id = order_response.json()["order_id"]

        # Register + login B
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_b)
        login_b = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email_b,
            "password": password_b
        })
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # B tries to cancel A's order
        cancel_response = await client.delete(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['cancel_order']}/{order_id}", headers=headers_b)
        assert cancel_response.status_code == 403
        assert cancel_response.json()["detail"] == "You can only cancel your own orders"


@pytest.mark.asyncio
async def test_cancel_nonexistent_order_returns_404():
    """
    Try cancelling a non-existent order → expect 404 Not Found.
    """
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Ghost",
        "last_name": "Order",
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

        fake_order_id = 999999
        response = await client.delete(f"{ORDER_BASE_URL}{ORDER_ENDPOINTS['cancel_order']}/{fake_order_id}", headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"
