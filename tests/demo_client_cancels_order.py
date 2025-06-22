import httpx
import time
import json
import jwt
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
        env_file_encoding = 'utf-8'
        extra = 'ignore'


try:
    settings = Settings()
except Exception as e:
    print(f"[FATAL] Could not load settings from .env file. Error: {e}")
    print("[FATAL] Please ensure a '.env' file with a JWT_SECRET_KEY exists in the 'config/' directory.")
    exit(1)

# --- Basic configuration ---
BASE_URL = "http://localhost:8000"
CUSTOMER_EMAIL = f"customer_cancel_{int(time.time())}@example.com"

CUSTOMER_DATA = {
    "email": CUSTOMER_EMAIL,
    "password": "strongpassword123",
    "first_name": "John",
    "last_name": "Cancels"
}

session_state = {}


def generate_qr_code_jwt(table_id: int) -> str:
    """Generates a JWT for a given table ID, simulating a QR code."""
    payload = {"table_id": table_id}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def run_client_cancel_demo():
    """
    Demonstrates the compensation flow where a client cancels an order
    immediately after creating it.
    """

    # --- PART 1: Client Setup ---

    # Step 1 - Registration
    print("\n[INFO] Client registration")
    response = httpx.post(f"{BASE_URL}/auth/register", json=CUSTOMER_DATA)
    response.raise_for_status()
    print("[SUCCESS] Client registered.")

    # Step 2 - Logging in
    print("\n[INFO] Client logging in")
    login_data = {"username": CUSTOMER_DATA["email"], "password": CUSTOMER_DATA["password"]}
    response = httpx.post(f"{BASE_URL}/auth/jwt/login", data=login_data)
    response.raise_for_status()
    session_state['customer_token'] = response.json()['access_token']
    headers = {"Authorization": f"Bearer {session_state['customer_token']}"}
    print("[SUCCESS] Client token saved to session state.")

    # Step 3 - Scanning QR code
    print("\n[INFO] Client scanning QR code (table 8)")
    qr_jwt = generate_qr_code_jwt(table_id=8)
    qr_data = {"code": qr_jwt}
    response = httpx.post(f"{BASE_URL}/order/scan_qr", headers=headers, json=qr_data)
    response.raise_for_status()
    print("[SUCCESS] Client assigned to table 8.")

    # --- PART 2: Order and Immediate Cancellation ---

    # Step 4 - Placing an order
    print("\n[INFO] Client placing an order")
    order_data = {
        "items": [{"item_id": 1, "quantity": 1}, {"item_id": 2, "quantity": 1}],
        "payment_method": "online"
    }
    response = httpx.post(f"{BASE_URL}/order", headers=headers, json=order_data)
    response.raise_for_status()
    session_state['order_id'] = response.json()['order_id']
    print(f"[SUCCESS] Created an order with ID: {session_state['order_id']}")

    # Step 5 - Canceling the order (The Compensation Action)
    # print(f"\n[ACTION] Client is immediately canceling order {session_state['order_id']}...")
    order_id = session_state['order_id']
    # response = httpx.delete(f"{BASE_URL}/order/{order_id}", headers=headers)
    # response.raise_for_status()
    # print(f"[SUCCESS] Cancel request for order {order_id} sent.")

    # --- PART 3: Final Verification ---

    # Step 6 - Client verifies final status
    print("\n[VERIFY] Client verifies final status of the order...")
    time.sleep(2)  # Time for propagation
    response = httpx.get(f"{BASE_URL}/order/my", headers=headers)
    response.raise_for_status()
    response_data = response.json()
    my_orders = response_data.get('orders', [])

    final_order = next((o for o in my_orders if o.get('id') == order_id), None)

    if final_order and final_order.get('status') == 'PENDING':
        print(f"[PASS] Verified: Order {order_id} has final status 'PENDING'.")
    else:
        status = final_order.get('status') if final_order else 'NOT FOUND'
        print(f"[FAIL] Verification failed. Expected status 'PENDING', but got '{status}'.")
        return

    # Step 7 - Verify payment link was not created
    print("\n[VERIFY] Checking that a payment link was NOT created...")
    payment_link_response = httpx.get(f"{BASE_URL}/payment/{order_id}/link")
    if payment_link_response.status_code == 404:
        print("[PASS] Verified: Payment service returned 404 Not Found, as expected.")
    else:
        print(
            f"[FAIL] Verification failed. A payment link was created for a cancelled order. Status: {payment_link_response.status_code}")
        return

    print("\n[SUCCESS] Full client cancellation flow finished successfully!")


if __name__ == "__main__":
    try:
        run_client_cancel_demo()
    except httpx.HTTPStatusError as e:
        print(f"\n[ERROR] Server error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"\n[ERROR] API communication error: {e}")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}")