# === tests/staff-service/test_update_order_status.py ===

"""Tests for the PUT /staff/orders/{order_id}/status endpoint of the Staff Service."""

import pytest
import httpx

from config import get_base_url, AUTH_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")
STAFF_BASE_URL = get_base_url("staff-service")


@pytest.mark.asyncio
async def test_update_order_status_order_not_found():
    """Register chef → login → update non-existent order → expect 404."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Lina",
        "last_name": "Cook",
        "role": "chef"
    }

    async with httpx.AsyncClient() as client:
        # Rejestracja i logowanie
        await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['register']}", json=user_data)
        login = await client.post(f"{AUTH_BASE_URL}{AUTH_ENDPOINTS['login']}", data={
            "username": email,
            "password": password
        })

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Próba zmiany statusu nieistniejącego zamówienia
        payload = {"new_status": "in_progress"}
        response = await client.put(
            f"{STAFF_BASE_URL}/staff/orders/99999/status",
            json=payload,
            headers=headers
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"
