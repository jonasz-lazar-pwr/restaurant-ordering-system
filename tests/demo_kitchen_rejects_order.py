import httpx
import time
import jwt
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loads settings from the .env file."""
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
CUSTOMER_EMAIL = f"customer_refund_{int(time.time())}@example.com"
CHEF_EMAIL = "chef@example.com"

CUSTOMER_DATA = {
    "email": CUSTOMER_EMAIL,
    "password": "strongpassword123",
    "first_name": "Anna",
    "last_name": "Kowalska"
}
CHEF_REGISTER_DATA = {
    "email": CHEF_EMAIL,
    "password": "chefpassword",
    "first_name": "Gordon",
    "last_name": "Ramsay",
    "role": "chef"
}
CHEF_LOGIN_DATA = {
    "username": CHEF_EMAIL,
    "password": "chefpassword"
}

session_state = {}


def generate_qr_code_jwt(table_id: int) -> str:
    """Generates a JWT for a given table ID, simulating a QR code."""
    payload = {"table_id": table_id}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def run_kitchen_refund_demo():
    """
    Demonstrates the compensation flow where the kitchen initiates a refund for a paid order.
    """
    with httpx.Client(timeout=30.0) as client:
        # --- PART 0: Staff Registration ---
        print("\n[INFO] Registering chef...")
        client.post(f"{BASE_URL}/auth/register", json=CHEF_REGISTER_DATA)

        # --- PART 1: Client places and pays for the order ---

        # Step 1 - Customer registration and login
        print("\n[INFO] Registering customer...")
        client.post(f"{BASE_URL}/auth/register", json=CUSTOMER_DATA).raise_for_status()
        print("[SUCCESS] Customer registered.")

        print("\n[INFO] Logging in customer...")
        login_data = {"username": CUSTOMER_DATA["email"], "password": CUSTOMER_DATA["password"]}
        response = client.post(f"{BASE_URL}/auth/jwt/login", data=login_data)
        response.raise_for_status()
        session_state['customer_token'] = response.json()['access_token']
        customer_headers = {"Authorization": f"Bearer {session_state['customer_token']}"}
        print("[SUCCESS] Customer token saved.")

        # Step 2 - Scan QR and place an order
        print("\n[INFO] Customer scanning QR code (table 5)...")
        qr_jwt = generate_qr_code_jwt(table_id=5)
        client.post(f"{BASE_URL}/order/scan_qr", headers=customer_headers, json={"code": qr_jwt}).raise_for_status()
        print("[SUCCESS] Customer assigned to table.")

        print("\n[INFO] Customer placing an order...")
        order_data = {"items": [{"item_id": 1, "quantity": 1}], "payment_method": "online"}
        response = client.post(f"{BASE_URL}/order", headers=customer_headers, json=order_data)
        response.raise_for_status()

        response_data = response.json()
        session_state['order_id'] = response_data['order_id']
        order_id = session_state['order_id']
        print(f"[SUCCESS] Created an order with ID: {order_id}")

        # Step 2a - Poll for the payment link asynchronously
        print("\n[INFO] Polling for the payment link (it will be populated asynchronously)...")
        payment_link = None
        for i in range(15):  # Poll for up to 30 seconds
            print(f"   Polling attempt {i + 1}/15...")
            time.sleep(2)
            response = client.get(f"{BASE_URL}/order/my", headers=customer_headers)
            if response.status_code == 200:
                orders_summary = response.json().get('orders', [])
                current_order = next((o for o in orders_summary if o.get('order_id') == order_id), None)
                if current_order and current_order.get('payment_link'):
                    payment_link = current_order['payment_link']
                    break
            elif response.status_code != 404:
                response.raise_for_status()

        if not payment_link:
            print("\n[FAILURE] Did not receive payment link after polling. Aborting.")
            return

        print(f"\n[ACTION] Open the link below in a browser and complete the payment:")
        print(f"---------> {payment_link} <---------")

        # Step 3 - Wait for the order to be paid
        print("\n[INFO] Waiting for user to complete payment...")
        order_paid = False
        for i in range(24):
            response = client.get(f"{BASE_URL}/order/my", headers=customer_headers)
            order_summary = None
            if response.status_code == 200:
                order_summary = next((o for o in response.json().get('orders', []) if o.get('order_id') == order_id),
                                     None)

            if order_summary and order_summary.get('status') == 'paid':
                print(f"\n[SUCCESS] Order {order_id} has been paid!")
                order_paid = True
                break
            current_status = order_summary.get('status', 'unknown') if order_summary else "not_found"
            print(f"Attempt {i + 1}/24: Order status is still '{current_status}'...")
            time.sleep(5)

        if not order_paid:
            print("\n[FAILURE] Timeout waiting for payment. Aborting.")
            return

        # --- PART 2: Kitchen staff initiates a refund ---

        # Step 4 - Chef logs in
        print("\n[INFO] Logging in as chef...")
        response = client.post(f"{BASE_URL}/auth/jwt/login", data=CHEF_LOGIN_DATA)
        response.raise_for_status()
        session_state['chef_token'] = response.json()['access_token']
        chef_headers = {"Authorization": f"Bearer {session_state['chef_token']}"}
        print("[SUCCESS] Chef token saved.")

        # Step 5 - Chef orders a refund
        print(f"\n[ACTION] Chef is initiating a REFUND for paid order {order_id}...")
        refund_data = {"reason": "Item out of stock, refunding customer."}
        response = client.post(f"{BASE_URL}/staff/orders/{order_id}/refund", headers=chef_headers,
                               json=refund_data)
        response.raise_for_status()
        print(f"[SUCCESS] Refund requested for order {order_id}. The process will run asynchronously.")

        # --- PART 3: Final verification on the client's side ---
        print("\n[VERIFY] Client is verifying the final status of the order...")
        final_status_correct = False
        for i in range(12):
            time.sleep(2)
            response = client.get(f"{BASE_URL}/order/my", headers=customer_headers)
            response.raise_for_status()

            final_order = None
            if response.status_code == 200:
                final_order = next((o for o in response.json().get('orders', []) if o.get('order_id') == order_id),
                                   None)

            if final_order and final_order.get('status') == 'refunded':
                print(f"[PASS] Verification successful. Final status for order {order_id} is 'refunded'.")
                final_status_correct = True
                break
            else:
                current_status = final_order.get('status', 'unknown') if final_order else "not_found"
                print(f"Attempt {i + 1}/12: Expected status 'refunded', but current is '{current_status}'...")

        if not final_status_correct:
            print(f"\n[FAIL] Verification failed. Order status was not changed to 'refunded'.")
        else:
            print("\n[DEMO SUCCESS] The compensation flow for a kitchen refund worked correctly.")


if __name__ == "__main__":
    try:
        run_kitchen_refund_demo()
    except httpx.HTTPStatusError as e:
        print(f"\n[ERROR] Server error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"\n[ERROR] API communication error: {e}")
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}", exc_info=True)