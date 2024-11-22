from fastapi import APIRouter, Depends, HTTPException
from db.models import User
from crud.user import (
    create_user,
    update_user,
    delete_user,
    # get_user_by_email,
    change_user_password,
)
from schema.user import UserCreate, UserUpdate, UserResponse
from db.session import db_dependency
from core.security import (
    get_current_user,
    verify_password,
)
from core.email import send_password_reset_email, send_verification_email
from core.rbac import has_role

router = APIRouter()

# Sending a verification mail to our mail
# By creatng a button for confirmation
# Then by so doing redirecting us back to login since i am already a user
# This should also be applicable for changing password


# USER CREATION
# Endpoint to create a new user
@router.post("/users/", response_model=dict)
async def create_new_user(user: UserCreate, db: db_dependency):
    # try:
    db_user = await create_user(db=db, user=user)

    # Send verification email
    await send_verification_email(db_user.email, db_user)

    return {
        "msg": "User registered successfully. Please check your email to verify your account.",
        "details": UserResponse.from_orm(db_user).dict(),
    }


# PROFILE MANAGER
@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# UPDATE USER PROFILE
@router.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    updated_user = update_user(db, current_user.id, user_update)
    return updated_user


# DELETE USER ACCOUNT
@router.delete("/users/me", response_model=dict)
async def delete_user_account(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    delete_user(db, current_user.id)
    return {"message": "User account deleted successfully"}


# REQUEST PASSWORD RESET
@router.post("/users/reset-password", response_model=dict)
async def request_password_reset(email: str, db: db_dependency):
    """
    Endpoint to request a password reset.
    This function sends a password reset email to the user if their email is registered.
    """
    # Fetch the user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")

    # Send the password reset email asynchronously
    await send_password_reset_email(user)

    return {"message": "Password reset instructions sent"}


# RESET PASSWORD CONFIRM
@router.put("/users/me/change-password", response_model=dict)
async def reset_password_confirm(
    current_password: str,
    new_password: str,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    change_user_password(db, current_user.id, new_password)
    return {"message": "Password updated successfully"}
