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


# GET USER BY ID(ADMIN)
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


# GET A USER BY E-MAIL
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


# CREATE USER
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


# Function to authenticate the user and issue a token


# ENABLING 2FA IN CASE THERES AN ERROR
# Function to authenticate the user and issue a token
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


# UPDATE_USER
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
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return None


# CHANGE USER PASSWORD
def change_user_password(db: Session, user_id: int, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.hashed_password = generate_hashed_password(new_password)
        db.commit()
        db.refresh(user)
    return user
