from sqlalchemy.orm import Session
from db.models import User
from schema.user import UserCreate, UserLogin
from core.security import (
    generate_hashed_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from datetime import datetime
from db.session import db_dependency
from fastapi import HTTPException, status
from core.mfa import verify_totp_code
from schema.token import Token
from schema.user import UserUpdate
from datetime import timedelta


# ---------------------------
# User Management Functions
# ---------------------------


# GET USER BY ID (ADMIN)
# - Retrieves a user by their ID.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `user_id (int)`: ID of the user to fetch.
# - Returns:
#   - `User`: The retrieved user if found; `None` otherwise.
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


# GET USER BY EMAIL
# - Retrieves a user by their email.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `email (str)`: Email of the user to fetch.
# - Returns:
#   - `User`: The retrieved user if found; `None` otherwise.
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


# CREATE USER
# - Creates a new user in the system.
# - Parameters:
#   - `user (UserCreate)`: The user data to create the new user.
#   - `db (db_dependency)`: Database session.
# - Returns:
#   - `User`: The newly created user object.
# - Raises:
#   - `HTTPException`: If the username or email already exists in the system.
async def create_user(
    user: UserCreate,
    db: db_dependency,
):

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        hashed_password=generate_hashed_password(user.password),
        role=user.role,
        is_active=True,
        created_at=datetime.now(),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# LOGIN USER
# - Authenticates a user and issues an access token.
# - Parameters:
#   - `db (db_dependency)`: Database session.
#   - `user_login (UserLogin)`: User login credentials.
#   - `totp_code (str)`: The TOTP code if two-factor authentication (2FA) is enabled.
# - Returns:
#   - `Token`: The generated access token.
# - Raises:
#   - `HTTPException`: If the credentials are invalid or the TOTP code is incorrect.
# NOTE: ENABLING 2FA IN CASE THERES AN ERROR
def login_user(
    db: db_dependency,
    user_login: UserLogin,  # Login request data
    totp_code: str,
) -> Token:
    # Check for user existence by email or username
    user = None
    if user_login.email:
        user = db.query(User).filter(User.email == user_login.email).first()
    elif user_login.username:
        user = db.query(User).filter(User.username == user_login.username).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either username or email",
        )

    # Verify password if user exists
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check if 2FA is enabled for the user
    if user.otp_secret:
        # If enabled, verify the provided TOTP code
        if not verify_totp_code(user.otp_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )
    else:
        # If 2FA is not enabled, skip TOTP verification
        print("2FA is not enabled for this user. Proceeding without TOTP verification.")

    # Generate an access token upon successful login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


# UPDATE USER
# - Updates a user's details based on the provided `UserUpdate` schema.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `user_id (int)`: ID of the user to update.
#   - `user_update (UserUpdate)`: Updated user data.
# - Returns:
#   - `User`: The updated user object.
# - Raises:
#   - `ValueError`: If the user is not found.
def update_user(db: Session, user_id: int, user_update: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# DELETE USER
# - Deletes a user by their ID.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `user_id (int)`: ID of the user to delete.
# - Returns:
#   - `None`: If the user is deleted successfully.
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return None


# ---------------------------
# Password Management Functions
# ---------------------------


# CHANGE USER PASSWORD
# - Changes a user's password.
# - Parameters:
#   - `db (Session)`: Database session.
#   - `user_id (int)`: ID of the user whose password is being changed.
#   - `new_password (str)`: The new password to set.
# - Returns:
#   - `User`: The updated user object with the new password.
# - Raises:
#   - `ValueError`: If the user is not found.
def change_user_password(db: Session, user_id: int, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.hashed_password = generate_hashed_password(new_password)
        db.commit()
        db.refresh(user)
    return user
