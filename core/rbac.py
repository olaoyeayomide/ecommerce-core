from fastapi import Depends, HTTPException, status
from db.models import User
from core.security import get_current_user


# ROLE-BASED ACCESS CONTROL DEPENDENCY
# - Parameters:
#   - `required_roles` (list[str]): A list of roles that are allowed to access the endpoint.
# - Returns:
#   - A nested dependency function `role_checker` that validates the role of the current user.
# - Nested Function: `role_checker`
#   - Checks if the `current_user`'s role is in the `required_roles` list.
#   - Parameters:
#       - `current_user` (User): The currently authenticated user, retrieved using `get_current_user`.
#   - Raises:
#       - `HTTPException`: If the user's role is not in `required_roles`, a 403 Forbidden response is raised.
#   - Returns:
#       - The `current_user` object if the role validation succeeds.
# - Details:
#   - This dependency function can be used in FastAPI routes to enforce role-based access control.
#   - It is reusable and supports checking against multiple roles.
def has_role(required_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}.",
            )
        return current_user

    return role_checker
