from fastapi import APIRouter, Depends, HTTPException
from db.models import User
from crud.user import (
    create_user,
    update_user,
    delete_user,
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

# === USER ENDPOINTS ===


# USER CREATION
# Endpoint: Create a new user
# Description:
#   Registers a new user in the system, and sends a verification email after registration.
# Request Body:
#   - user (UserCreate): The user's information such as email, username, password, etc.
# Response:
#   - A confirmation message indicating successful registration, along with the user details.
#   - A verification email is sent to the user for account activation.
# Roles Required:
#   - None.
@router.post("/users/", response_model=dict)
async def create_new_user(user: UserCreate, db: db_dependency):
    db_user = await create_user(db=db, user=user)
    await send_verification_email(db_user.email, db_user)
    return {
        "msg": "User registered successfully. Please check your email to verify your account.",
        "details": UserResponse.from_orm(db_user).dict(),
    }


# PROFILE MANAGER
# Endpoint: Fetch the current user's profile information
# Description:
#   Retrieves the profile data (email, username, role) of the currently logged-in user.
# Response:
#   - The current user's profile data.
# Roles Required:
#   - None. Always refers to the logged-in user.
# Details:
#   This endpoint fetches the profile details of the authenticated user based on the current session or token.
@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# UPDATE USER PROFILE
# Endpoint: Update the profile of the currently logged-in user
# Description:
#   Allows the authenticated user to update their profile information, such as email or username.
# Request Body:
#   - user_update (UserUpdate): The new profile details to update.
# Response:
#   - The updated user profile data.
# Roles Required:
#   - None. Only the authenticated user can update their profile.
@router.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    updated_user = update_user(db, current_user.id, user_update)
    return updated_user


# DELETE USER ACCOUNT
# Endpoint: Delete the currently logged-in user's account
# Description:
#   Deletes the user’s account from the system. This action is irreversible.
# Response:
#   - A message confirming the account deletion.
# Roles Required:
#   - None. Only the authenticated user can delete their account.
@router.delete("/users/me", response_model=dict)
async def delete_user_account(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    await delete_user(db, current_user.id)
    return {"message": "User account deleted successfully"}


# === USER PASSWORD ENDPOINTS ===


# REQUEST PASSWORD RESET
# Endpoint: Request a password reset
# Description:
#   Allows a user to request a password reset by sending a reset email to their email address.
# Request Body:
#   - email (str): The email address of the user requesting the password reset.
# Response:
#   - A message confirming that the password reset email has been sent.
# Roles Required:
#   - None.
@router.post("/users/reset-password", response_model=dict)
async def request_password_reset(email: str, db: db_dependency):
    # Fetch the user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")
    await send_password_reset_email(user)
    return {"message": "Password reset instructions sent"}


# RESET PASSWORD CONFIRM
# Endpoint: Reset the password for the current user
# Description:
#   Allows the authenticated user to reset their password by verifying the current password.
# Request Body:
#   - current_password (str): The user's current password.
#   - new_password (str): The new password the user wishes to set.
# Response:
#   - A confirmation message indicating the password update was successful.
# Roles Required:
#   - None. Only the authenticated user can reset their password.
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
