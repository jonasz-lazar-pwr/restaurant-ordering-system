# === tests/utils.py ===

import uuid

def generate_unique_user() -> tuple[str, str]:
    """
    Generate a unique email and password for testing purposes.

    Returns:
        tuple: (email, password)
    """
    unique_id = uuid.uuid4().hex[:8]
    email = f"user_{unique_id}@test.com"
    password = "StrongTestPassword123!"
    return email, password
