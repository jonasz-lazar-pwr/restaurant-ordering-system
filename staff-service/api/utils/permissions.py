# === api/utils/permissions.py ===

"""
Permissions utility for role-based access control in the Staff Service.
"""

from fastapi import HTTPException, status, Header
from api.models.order_status import OrderStatus

from api.utils.auth import extract_user_info

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

def permission_dependency(roles: list[str]):
    """
    Dependency factory for checking user roles.
    Returns a dependency that verifies if the user's role is in the allowed list.
    """
    def check_roles(authorization: str = Header(...)) -> None:
        user_info = extract_user_info(authorization)
        user_role = user_info.get("role")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not authorized for this action. Allowed roles: {roles}"
            )
    return check_roles