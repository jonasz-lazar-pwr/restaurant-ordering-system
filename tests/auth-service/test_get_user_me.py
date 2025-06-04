# tests/auth-service/test_get_user_me.py

"""
Tests for the /auth/users/me endpoint of the Auth Service.

These tests verify authenticated access to the current user's profile information.
"""

import pytest
import httpx
import uuid
from config import get_base_url


BASE_URL = get_base_url("auth-service")
REGISTER_ENDPOINT = "/auth/register"
LOGIN_ENDPOINT = "/auth/jwt/login"
ME_ENDPOINT = "/auth/users/me"


@pytest.mark.asyncio
async def test_get_user_me_authenticated():
    """
    Verify that an authenticated user can retrieve their own profile.
    """
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "ValidP@ss123"
    payload = {
        "email": email,
        "password": password,
        "first_name": "Jane",
        "last_name": "Doe",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Register new user
        await client.post(REGISTER_ENDPOINT, json=payload)

        # Login to get token
        login_response = await client.post(LOGIN_ENDPOINT, data={
            "username": email,
            "password": password
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Request /me with valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(ME_ENDPOINT, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_get_user_me_no_token():
    """
    Try to access /me without a token. Expect 401 Unauthorized.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(ME_ENDPOINT)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_me_invalid_token():
    """
    Try to access /me with an invalid token. Expect 401 Unauthorized.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(ME_ENDPOINT, headers={
            "Authorization": "Bearer invalid.token.value"
        })

    assert response.status_code == 401
