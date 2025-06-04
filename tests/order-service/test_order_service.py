# tests/test_order_service.py

import pytest
import httpx
import json

BASE_URL = "http://localhost:8002"

# Mock user payload that the API Gateway would normally inject
MOCK_USER_PAYLOAD_CLIENT = {
    "sub": "user-id-client-for-order-tests",
    "role": "client",
    "first_name": "OrderTest",
    "last_name": "Client"
}

MOCK_USER_PAYLOAD_WAITER = {
    "sub": "user-id-waiter-for-order-tests",
    "role": "waiter",
    "first_name": "OrderTest",
    "last_name": "Waiter"
}

# Headers to simulate an authenticated client request via X-User-Payload
AUTH_HEADERS_CLIENT = {
    "X-User-Payload": json.dumps(MOCK_USER_PAYLOAD_CLIENT)
}

# Headers to simulate an authenticated waiter request via X-User-Payload
AUTH_HEADERS_WAITER = {
    "X-User-Payload": json.dumps(MOCK_USER_PAYLOAD_WAITER)
}


@pytest.fixture
def qr_data():
    """Provides QR code data for tests."""
    return {"code": "stolik_order_test_1"}

@pytest.fixture
def order_request_data(): # Renamed to avoid potential Pydantic model name clashes
    """Provides a sample order request payload."""
    # Assuming item_id 1 exists from your init_db.py script for MenuItem
    return {"qr_code": "stolik_order_test_1", "item_id": 1}


@pytest.mark.asyncio
async def test_scan_qr_public_endpoint(qr_data):
    """
    Test scanning a valid QR code. /order/scan_qr/ is assumed to be public.
    Should return menu and 200 status.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/order/scan_qr/", json=qr_data) # Assuming trailing slash if present in service
    assert response.status_code == 200
    data = response.json()
    assert "menu" in data
    assert isinstance(data["menu"], list)
    # Add more specific assertions if menu content is known, e.g., from init_db.py
    if data["menu"]:
        assert len(data["menu"]) > 0
    assert "message" in data


@pytest.mark.asyncio
async def test_order_item_as_client(order_request_data):
    """
    Test placing a valid order as a client.
    Order service expects X-User-Payload header.
    Should return 200/201 and confirmation message.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Optional: Call scan_qr first if it's a required step in your workflow
        # await client.post("/order/scan_qr/", json={"code": order_request_data["qr_code"]})
        response = await client.post("/order/", json=order_request_data, headers=AUTH_HEADERS_CLIENT)

    assert response.status_code in (200, 201) # 201 Created is also common for new resources
    data = response.json()
    assert "message" in data
    assert "order_id" in data
    assert MOCK_USER_PAYLOAD_CLIENT["sub"] in data["message"] # Check if user_id is in the message
    assert order_request_data["qr_code"] in data["message"]


@pytest.mark.asyncio
async def test_get_orders_as_waiter(qr_data, order_request_data):
    """
    Test retrieving orders for a specific table as a waiter.
    Assumes an order was successfully placed first.
    Order service expects X-User-Payload header.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Place an order first to ensure there's data to retrieve
        # Use client payload to place the order
        order_response = await client.post("/order/", json=order_request_data, headers=AUTH_HEADERS_CLIENT)
        assert order_response.status_code in (200, 201), f"Order placement failed: {order_response.text}"

        # Now, retrieve orders as a waiter
        response = await client.get(f"/order/{qr_data['code']}", headers=AUTH_HEADERS_WAITER)

    assert response.status_code == 200
    data = response.json()
    assert data["table"] == qr_data["code"]
    assert "orders" in data
    assert isinstance(data["orders"], list)
    if data["orders"]:
        assert len(data["orders"]) > 0
        assert data["orders"][0].get("item_name") == "Pizza Margherita" # Or based on your item_id 1


@pytest.mark.asyncio
async def test_order_item_missing_x_user_payload(order_request_data):
    """
    Test placing an order without the X-User-Payload header.
    Should return 401 Unauthorized from the order service.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/order/", json=order_request_data) # No auth headers

    assert response.status_code == 401
    data = response.json()
    assert "X-User-Payload header missing" in data["detail"]


@pytest.mark.asyncio
async def test_order_item_invalid_item_id(qr_data):
    """
    Test ordering an item that doesn't exist.
    Should return 404 Not Found.
    Requires X-User-Payload for the /order/ endpoint.
    """
    invalid_order_payload = {"qr_code": qr_data["code"], "item_id": 9999} # Non-existent item_id
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/order/", json=invalid_order_payload, headers=AUTH_HEADERS_CLIENT)

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Item not found"


@pytest.mark.asyncio
async def test_get_orders_for_non_existent_table():
    """
    Test retrieving orders for a non-existent table.
    Should return 404 Not Found.
    Requires X-User-Payload for the /order/{table_number} endpoint.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/order/non_existent_table_123xyz", headers=AUTH_HEADERS_WAITER)

    assert response.status_code == 404
    assert "No orders found" in response.json()["detail"]
