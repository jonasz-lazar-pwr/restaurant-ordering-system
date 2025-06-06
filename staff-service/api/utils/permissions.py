# === api/utils/permissions.py ===

"""
Permissions utility for role-based access control in the Staff Service.
"""

from fastapi import HTTPException, status
from api.models.order_status import OrderStatus


# Allowed status transitions per role
ROLE_PERMISSIONS = {
    "chef": {
        OrderStatus.in_progress,
        OrderStatus.ready,
        OrderStatus.failed,
    },
    "waiter": {
        OrderStatus.delivered,
        OrderStatus.paid,
    },
}


def validate_role_permission(role: str, new_status: OrderStatus) -> None:
    """
    Validate if a given role is allowed to set the given status.

    Args:
        role (str): Role of the user (e.g., "chef", "waiter").
        new_status (OrderStatus): Status the user attempts to set.

    Raises:
        HTTPException: If the role is not authorized to set this status.
    """
    allowed_statuses = ROLE_PERMISSIONS.get(role, set())

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' is not allowed to set status '{new_status.value}'."
        )