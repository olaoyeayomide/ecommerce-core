from fastapi import Depends, APIRouter, HTTPException, status
from schema.token import Token
from fastapi.security import OAuth2PasswordRequestForm
from db.session import db_dependency
from schema.user import UserLogin
from crud.user import login_user
from core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    verify_refresh_token,
)
from core.rbac import has_role
from datetime import timedelta

router = APIRouter()


# USER LOGIN
# Endpoint to handle user login with two-factor authentication (TOTP).
# This function delegates the login process to the `login_user` function in the `crud.user` module.
# Parameters:
# - `user_login`: The login credentials (username and password) provided by the user.
# - `totp_code`: A time-based one-time password for 2FA validation.
# - `db`: Database session dependency.
# Returns a token if the credentials and TOTP code are valid.
@router.post("/login", response_model=Token)
def login(user_login: UserLogin, totp_code: str, db: db_dependency):
    return login_user(db=db, user_login=user_login, totp_code=totp_code)


# GENERATE JWT TOKEN
# Endpoint for obtaining a JWT access token after successful authentication of users.
# Uses OAuth2PasswordRequestForm to parse the user's username and password.
# Validates the credentials using the `authenticate_user` function.
# If authentication succeeds, generates a JWT access token with an expiration time.
# Parameters:
# - `db`: Database session dependency.
# - `form_data`: Dependency that handles OAuth2 form data.
# Returns:
# - A JSON object containing the `access_token` and its type if authentication is successful.
@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: db_dependency,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_id=user.id, email=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# REFRESH TOKEN
# Endpoint to refresh an expired JWT access token and issuing a new JWT token using a valid refresh token, with RBAC to limit access based on roles.
# Verifies the provided refresh token using the `verify_refresh_token` function.
# Generates a new JWT access token with the same user details if the refresh token is valid.
# Includes role-based access control (RBAC) to restrict access to users with specified roles.
# Parameters:
# - `refresh_token`: A valid refresh token provided by the user.
# Returns:
# - A JSON object containing the new `access_token` and its type if the refresh token is valid.
@router.post(
    "/refresh",
    response_model=Token,
    dependencies=[Depends(has_role(["admin", "user", "vendor"]))],
)
async def refresh_access_token(refresh_token: str):
    try:
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("user_id")
        email = payload.get("email")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            user_id=user_id, email=email, expires_delta=access_token_expires
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from e
