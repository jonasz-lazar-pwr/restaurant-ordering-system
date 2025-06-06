# === tests/staff-service/test_list_orders.py ===

"""Tests for the GET /staff/orders endpoint of the Staff Service."""

import pytest
import httpx

from config import get_base_url, AUTH_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")
STAFF_BASE_URL = get_base_url("staff-service")


@pytest.mark.asyncio
async def test_list_orders_as_chef():
    """Register chef → login → GET /staff/orders → expect 200 and list."""
    email, password = generate_unique_user()
    user_data = {
        "email": email,
        "password": password,
        "first_name": "Gordon",
        "last_name": "Ramsay",
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

        # Pobranie zamówień do przygotowania
        response = await client.get(f"{STAFF_BASE_URL}/staff/orders", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

