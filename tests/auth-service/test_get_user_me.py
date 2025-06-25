# === tests/auth-service/test_get_user_me.py ===

"""Tests for the /auth/users/me endpoint of the Auth Service.

These tests verify authenticated access to the current user's profile information.
"""

import pytest
import httpx
from config import get_base_url, AUTH_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")


@pytest.mark.asyncio
async def test_get_user_me_authenticated():
    """
    Verify that an authenticated user can retrieve their own profile.

    Flow:
        - Register a new user
        - Log in to obtain a token
        - Access /auth/users/me with the token
        - Expect correct user profile fields
    """
    email, password = generate_unique_user()
    registration_payload = {
        "email": email,
        "password": password,
        "first_name": "Jane",
        "last_name": "Doe",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        await client.post(AUTH_ENDPOINTS["register"], json=registration_payload)

        login_response = await client.post(AUTH_ENDPOINTS["login"], data={
            "username": email,
            "password": password
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(AUTH_ENDPOINTS["me"], headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_get_user_me_no_token():
    """
    Try to access the /me endpoint without providing a token.

    Expected:
        HTTP 401 Unauthorized.
    """
    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.get(AUTH_ENDPOINTS["me"])

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_me_invalid_token():
    """
    Try to access the /me endpoint using an invalid token.

    Expected:
        HTTP 401 Unauthorized.
    """
    headers = {"Authorization": "Bearer invalid.token.value"}

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.get(AUTH_ENDPOINTS["me"], headers=headers)

    assert response.status_code == 401
