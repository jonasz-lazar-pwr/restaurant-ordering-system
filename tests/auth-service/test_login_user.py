# tests/auth-service/test_login_user.py

"""
Tests for the /auth/jwt/login endpoint of the Auth Service.

These tests verify authentication with valid and invalid credentials,
as well as error handling for missing fields.
"""

import pytest
import httpx
import uuid
from config import get_base_url

BASE_URL = get_base_url("auth-service")
LOGIN_ENDPOINT = "/auth/jwt/login"
REGISTER_ENDPOINT = "/auth/register"


def generate_unique_email() -> str:
    """Generate a unique email address for test user registration."""
    return f"testuser_{uuid.uuid4().hex}@example.com"


@pytest.mark.asyncio
async def test_login_valid_user():
    """Log in with correct credentials and expect 200 OK with access token."""
    email = generate_unique_email()
    password = "SecureP@ssw0rd"

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

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await client.post(REGISTER_ENDPOINT, json=registration_payload)
        response = await client.post(LOGIN_ENDPOINT, data=login_data)

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password():
    """Try to log in with a valid email but wrong password. Expect 400 Bad Request."""
    email = generate_unique_email()
    correct_password = "CorrectP@ss123"
    wrong_password = "WrongPassword123"

    registration_payload = {
        "email": email,
        "password": correct_password,
        "first_name": "John",
        "last_name": "Doe",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await client.post(REGISTER_ENDPOINT, json=registration_payload)
        response = await client.post(LOGIN_ENDPOINT, data={
            "username": email,
            "password": wrong_password
        })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    """Try to log in with a non-existent email. Expect 400 Bad Request."""
    email = generate_unique_email()
    data = {
        "username": email,
        "password": "AnyPassword123"
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(LOGIN_ENDPOINT, data=data)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_missing_fields():
    """Try to log in with missing form fields. Expect 422 Unprocessable Entity."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(LOGIN_ENDPOINT, data={})

    assert response.status_code == 422
