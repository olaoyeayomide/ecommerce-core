from fastapi import Depends, HTTPException, status
from db.models import User
from core.security import get_current_user


def has_role(required_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}.",
            )
        return current_user

    return role_checker
