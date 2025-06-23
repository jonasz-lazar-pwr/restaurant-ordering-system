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
        # Adjust the path to be relative to this script's location
        env_file = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
        env_file_encoding = 'utf-8'
        extra = 'ignore'


try:
    settings = Settings()
except Exception:
    print("[FATAL] Could not load settings. Ensure a '.env' file with JWT_SECRET_KEY exists in 'config/'.")
    exit(1)

# Basic configuration
BASE_URL = "http://localhost:8000"
CUSTOMER_EMAIL = f"customer_{int(time.time())}@example.com"

CUSTOMER_DATA = {
    "email": CUSTOMER_EMAIL,
    "password": "strongpassword123",
    "first_name": "John",
    "last_name": "Doe",
}
CHEF_DATA = {
    "email": "chef@example.com",
    "password": "chefpassword",
    "first_name": "Gordon",
    "last_name": "Ramsay",
    "role": "chef"
}
WAITER_REGISTER_DATA = {
    "email": "waiter@example.com",
    "password": "waiterpassword",
    "first_name": "Adam",
    "last_name": "Smith",
    "role": "waiter"
}
WAITER_DATA = {
    "username": "waiter@example.com",
    "password": "waiterpassword"
}

session_state = {}


def generate_qr_code_jwt(table_id: int) -> str:
    payload = {"table_id": table_id}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def run_demo():
    # PART 0 - Staff registration
    print("--- Staff registration (Chef and Waiter) ---")
    httpx.post(f"{BASE_URL}/auth/register", json=CHEF_DATA)
    httpx.post(f"{BASE_URL}/auth/register", json=WAITER_REGISTER_DATA)
    print("[INFO] Staff users created or already exist.")

    # PART 1 - Client
    print("\n--- Client Actions ---")
    # Step 1 - Registration
    print("1. Client registration...")
    response = httpx.post(f"{BASE_URL}/auth/register", json=CUSTOMER_DATA)
    response.raise_for_status()
    print("[SUCCESS] Client registered.")

    # Step 2 - Logging in
    print("\n2. Client logging in...")
    login_data = {"username": CUSTOMER_DATA["email"], "password": CUSTOMER_DATA["password"]}
    response = httpx.post(f"{BASE_URL}/auth/jwt/login", data=login_data)
    response.raise_for_status()
    session_state['customer_token'] = response.json()['access_token']
    print("[SUCCESS] Client token saved to session state.")
    headers = {"Authorization": f"Bearer {session_state['customer_token']}"}

    # Step 3 - Scanning QR code
    print("\n3. Client scanning QR code (table 12)...")
    qr_jwt = generate_qr_code_jwt(table_id=12)
    qr_data = {"code": qr_jwt}
    response = httpx.post(f"{BASE_URL}/order/scan_qr", headers=headers, json=qr_data)
    response.raise_for_status()
    print("[SUCCESS] QR code scanned and table assigned.")

    # Step 4 - Placing an order
    print("\n4. Client placing an order...")
    order_data = {
        "items": [{"item_id": 1, "quantity": 1}, {"item_id": 2, "quantity": 1}],
        "payment_method": "online"
    }
    response = httpx.post(f"{BASE_URL}/order", headers=headers, json=order_data)
    response.raise_for_status()
    order_response_data = response.json()
    session_state['order_id'] = order_response_data['order_id']
    print(f"[SUCCESS] Created an order with ID: {session_state['order_id']}")

    # Step 4a - Polling for the payment link
    print("\n4a. Polling for the payment link (it will be populated asynchronously)...")
    payment_link = None
    for i in range(15):
        print(f"   Polling attempt {i + 1}/15...")
        time.sleep(2)
        response = httpx.get(f"{BASE_URL}/order/my", headers=headers)
        if response.status_code == 200:
            order_summary = next(
                (o for o in response.json().get('orders', []) if o.get('order_id') == session_state['order_id']), None)
            if order_summary and order_summary.get("payment_link"):
                payment_link = order_summary["payment_link"]
                break
        elif response.status_code != 404:
            response.raise_for_status()

    if not payment_link:
        print("\n[FATAL] Payment link not received after polling. The async process may have failed. Aborting.")
        return

    print(f"\n[SUCCESS] Got PayU payment link via polling:")
    print(f"---------> {payment_link} <---------")

    # PART 2 - System and staff
    print("\n--- System and Staff Actions ---")
    # Step 5 - Wait for Payment and Verify Status by Polling
    print("\n5. Please open the link above and complete the test payment.")
    print("   The script will now poll to check the order status...")

    final_status = None
    for i in range(24):  # Poll for up to 2 minutes
        print(f"   Polling attempt {i + 1}/24...")
        time.sleep(5)
        response = httpx.get(f"{BASE_URL}/order/my", headers=headers)
        if response.status_code == 200:
            order_summary = next(
                (o for o in response.json().get('orders', []) if o.get('order_id') == session_state['order_id']), None)
            if order_summary:
                status = order_summary.get("status")
                print(f"   Current status: '{status}'")
                if status == 'paid':
                    print(f"\n[SUCCESS] Order {session_state['order_id']} has been paid!")
                    final_status = 'paid'
                    break
                elif status == 'cancelled':
                    print(f"\n[COMPENSATION SUCCESS] Payment was cancelled, and order status is correctly 'cancelled'.")
                    final_status = 'cancelled'
                    break
        elif response.status_code != 404:
            response.raise_for_status()

    if not final_status:
        print("\n[FAILURE] Timeout: Order status did not change to 'paid' or 'cancelled'. Aborting.")
        return
    if final_status == 'cancelled':
        return

    with httpx.Client() as client:
        # Step 6 - Chef logging in
        print("\n6. Chef logging in...")
        chef_login_data = {"username": CHEF_DATA["email"], "password": CHEF_DATA["password"]}
        response = client.post(f"{BASE_URL}/auth/jwt/login", data=chef_login_data)
        response.raise_for_status()
        chef_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        print("[SUCCESS] Chef logged in.")

        # Step 7 & 8 - Chef updates status
        print("\n7. Chef changing status to 'in_progress'...")
        response = client.put(f"{BASE_URL}/staff/orders/{session_state['order_id']}/status", headers=chef_headers,
                              json={"new_status": "in_progress"})
        response.raise_for_status()
        print("[SUCCESS] Status is 'in_progress'.")

        time.sleep(1)  # simulate work

        print("\n8. Chef changing status to 'ready'...")
        response = client.put(f"{BASE_URL}/staff/orders/{session_state['order_id']}/status", headers=chef_headers,
                              json={"new_status": "ready"})
        response.raise_for_status()
        print("[SUCCESS] Status is 'ready'.")

        # Step 9 - Waiter logging in
        print("\n9. Waiter logging in...")
        response = client.post(f"{BASE_URL}/auth/jwt/login", data=WAITER_DATA)
        response.raise_for_status()
        waiter_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        print("[SUCCESS] Waiter logged in.")

        # Step 10 & 11 - Waiter checks and delivers
        print("\n10. Waiter checks for ready orders...")
        response = client.get(f"{BASE_URL}/staff/orders", headers=waiter_headers)
        response.raise_for_status()
        print(f"[INFO] Waiter found orders: {response.json()}")

        print("\n11. Waiter delivers order and changes status to 'delivered'...")
        response = client.put(f"{BASE_URL}/staff/orders/{session_state['order_id']}/status", headers=waiter_headers,
                              json={"new_status": "delivered"})
        response.raise_for_status()
        print("[SUCCESS] Status is 'delivered'.")

    # PART 3 - Final verification
    print("\n--- Final Verification ---")
    # Step 12 - Client verifies final status
    print("\n12. Client verifies final order status...")
    time.sleep(2)  # Wait for event propagation
    response = httpx.get(f"{BASE_URL}/order/my", headers=headers)
    response.raise_for_status()
    final_order = next(
        (o for o in response.json().get('orders', []) if o.get('order_id') == session_state['order_id']), None)

    if final_order and final_order.get('status') == 'delivered':
        print(f"\n[PASS] Verified: Order {session_state['order_id']} has final status 'delivered'.")
        print("\n[DEMO SUCCESS] Full flow finished successfully!")
    else:
        status = final_order.get('status') if final_order else 'NOT FOUND'
        print(f"\n[FAIL] Verification failed. Expected 'delivered', but got '{status}'.")


if __name__ == "__main__":
    try:
        run_demo()
    except httpx.HTTPStatusError as e:
        print(f"\n[ERROR] Server error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"\n[ERROR] API communication error: {e}")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}")