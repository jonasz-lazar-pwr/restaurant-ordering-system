# tests/test_order_service_via_api_gateway.py

import pytest
import httpx
import secrets
import string

# BASE_URL for the API Gateway
BASE_URL = "http://localhost:8000"


# --- Helper function to generate unique email for tests ---
def generate_unique_email(prefix="testuser"):
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"{prefix}_{random_suffix}@example.com"


# --- Fixture to register and login a user, returning auth headers with JWT ---
@pytest.fixture(scope="function")  # function scope to get a fresh user & token for each test if needed
async def authenticated_client_headers():
    """
    Registers a new 'client' user via API Gateway, logs them in,
    and returns headers with the JWT Bearer token.
    """
    email = generate_unique_email("client_order_gw")
    user_data = {
        "email": email,
        "password": "testpassword123",
        "first_name": "Client",
        "last_name": "OrderGW",
        "role": "client"
    }
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Register user via API Gateway
        reg_response = await client.post("/api/auth/register", json=user_data)
        if reg_response.status_code not in (201, 400):  # 400 if user already exists
            pytest.fail(f"User registration via gateway failed: {reg_response.status_code} - {reg_response.text}")

        # 2. Login user via API Gateway to get token
        login_payload = {"username": user_data["email"], "password": user_data["password"]}
        login_response = await client.post(
            "/api/auth/jwt/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_response.status_code != 200:
            pytest.fail(f"User login via gateway failed: {login_response.status_code} - {login_response.text}")

        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, user_data  # Return headers and user_data for reference


@pytest.fixture(scope="function")
async def authenticated_waiter_headers():
    """
    Registers a new 'waiter' user via API Gateway, logs them in,
    and returns headers with the JWT Bearer token.
    """
    email = generate_unique_email("waiter_order_gw")
    user_data = {
        "email": email,
        "password": "testpassword123",
        "first_name": "Waiter",
        "last_name": "OrderGW",
        "role": "waiter"  # Crucial for waiter-specific tests
    }
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        reg_response = await client.post("/api/auth/register", json=user_data)
        if reg_response.status_code not in (201, 400):
            pytest.fail(f"Waiter registration via gateway failed: {reg_response.status_code} - {reg_response.text}")

        login_payload = {"username": user_data["email"], "password": user_data["password"]}
        login_response = await client.post(
            "/api/auth/jwt/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_response.status_code != 200:
            pytest.fail(f"Waiter login via gateway failed: {login_response.status_code} - {login_response.text}")

        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, user_data


@pytest.fixture
def qr_data_gw():  # Renamed to avoid conflict if run in same session as other tests
    """Provides QR code data for gateway tests."""
    return {"code": "stolik_gw_order_1"}


@pytest.fixture
def order_request_data_gw(qr_data_gw):  # Renamed and uses qr_data_gw
    """Provides a sample order request payload for gateway tests."""
    # Assuming item_id 1 exists from your init_db.py script for MenuItem
    return {"qr_code": qr_data_gw["code"], "item_id": 1}


# --- Test Cases ---

@pytest.mark.asyncio
async def test_scan_qr_via_gateway(qr_data_gw):
    """
    Test scanning a QR code via API Gateway.
    Assumes /api/order/scan_qr/ is public or accessible appropriately.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # If scan_qr is public through gateway, no auth headers needed.
        # If it requires auth, add `headers=await authenticated_client_headers()`
        response = await client.post("/api/order/scan_qr/", json=qr_data_gw)
    assert response.status_code == 200
    data = response.json()
    assert "menu" in data
    assert isinstance(data["menu"], list)
    if data["menu"]:
        assert len(data["menu"]) > 0
    assert "message" in data


@pytest.mark.asyncio
async def test_order_item_as_client_via_gateway(order_request_data_gw, authenticated_client_headers):
    auth_headers, client_user_data = await authenticated_client_headers
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/order/", json=order_request_data_gw, headers=auth_headers)

    assert response.status_code in (200, 201)
    data = response.json()
    assert "message" in data
    assert "order_id" in data
    assert client_user_data["email"] in data["message"]
    assert order_request_data_gw["qr_code"] in data["message"]


@pytest.mark.asyncio
async def test_get_orders_as_waiter_via_gateway(qr_data_gw, order_request_data_gw, authenticated_client_headers,
                                                authenticated_waiter_headers):
    """
    Test retrieving orders as a waiter via API Gateway.
    Requires JWT authentication.
    """
    client_auth_headers, _ = await authenticated_client_headers
    waiter_auth_headers, _ = await authenticated_waiter_headers

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # A client places an order
        order_response = await client.post("/api/order/", json=order_request_data_gw, headers=client_auth_headers)
        assert order_response.status_code in (200, 201), f"Order placement by client failed: {order_response.text}"

        # Waiter retrieves orders for that table
        response = await client.get(f"/api/order/{qr_data_gw['code']}", headers=waiter_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["table"] == qr_data_gw["code"]
    assert "orders" in data
    assert isinstance(data["orders"], list)
    if data["orders"]:
        assert len(data["orders"]) > 0
        # Example: Check if the item ordered by the client is present
        # This depends on init_db for item_id 1 and response structure of get_orders
        assert any(item.get("item_name") == "Pizza Margherita" for item in data["orders"])


@pytest.mark.asyncio
async def test_order_item_via_gateway_no_token(order_request_data_gw):
    """
    Test placing an order via API Gateway without a token.
    Should be blocked by API Gateway (401 or 403).
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/order/", json=order_request_data_gw)  # No auth headers

    assert response.status_code == 401  # API Gateway should return 401 if token is missing for protected route
    data = response.json()
    assert "Token is missing or invalid format" in data["detail"]


@pytest.mark.asyncio
async def test_order_item_invalid_item_id_via_gateway(qr_data_gw, authenticated_client_headers):
    """
    Test ordering a non-existent item via API Gateway.
    Should pass auth at Gateway, then order-service returns 404.
    """
    auth_headers, _ = await authenticated_client_headers
    invalid_order_payload = {"qr_code": qr_data_gw["code"], "item_id": 9999}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/order/", json=invalid_order_payload, headers=auth_headers)

    assert response.status_code == 404  # order-service should return this
    data = response.json()
    assert data["detail"] == "Item not found"


@pytest.mark.asyncio
async def test_get_orders_for_non_existent_table_via_gateway(authenticated_waiter_headers):
    """
    Test retrieving orders for a non-existent table via API Gateway.
    Should pass auth at Gateway, then order-service returns 404.
    """
    auth_headers, _ = await authenticated_waiter_headers
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/order/non_existent_table_xyz123", headers=auth_headers)

    assert response.status_code == 404  # order-service should return this
    assert "No orders found" in response.json()["detail"]
