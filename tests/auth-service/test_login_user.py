# === tests/auth-service/test_login_user.py ===

"""Tests for the /auth/jwt/login endpoint of the Auth Service.

These tests verify authentication with valid and invalid credentials,
as well as error handling for missing fields.
"""

import pytest
import httpx
from config import get_base_url, AUTH_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")


@pytest.mark.asyncio
async def test_login_valid_user():
    """
    Log in with correct credentials and expect 200 OK with access token.

    Flow:
        - Register a new user
        - Log in using valid credentials
        - Verify response contains access_token and token_type
    """
    email, password = generate_unique_user()

    registration_payload = {
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "User",
        "role": "client"
    }

    login_data = {
        "username": email,
        "password": password
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        await client.post(AUTH_ENDPOINTS["register"], json=registration_payload)
        response = await client.post(AUTH_ENDPOINTS["login"], data=login_data)

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password():
    """
    Try to log in with a valid email but incorrect password.

    Expected:
        HTTP 400 Bad Request.
    """
    email, password = generate_unique_user()
    wrong_password = "WrongPassword123"

    registration_payload = {
        "email": email,
        "password": password,
        "first_name": "John",
        "last_name": "Doe",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        await client.post(AUTH_ENDPOINTS["register"], json=registration_payload)
        response = await client.post(AUTH_ENDPOINTS["login"], data={
            "username": email,
            "password": wrong_password
        })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    """
    Try to log in with an email that was never registered.

    Expected:
        HTTP 400 Bad Request.
    """
    email, _ = generate_unique_user()
    data = {
        "username": email,
        "password": "AnyPassword123"
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.post(AUTH_ENDPOINTS["login"], data=data)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_missing_fields():
    """
    Try to log in with no form fields provided.

    Expected:
        HTTP 422 Unprocessable Entity.
    """
    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.post(AUTH_ENDPOINTS["login"], data={})

    assert response.status_code == 422
