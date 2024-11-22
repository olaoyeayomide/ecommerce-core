from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from db.session import db_dependency

# from sqlalchemy.orm import Session
from schema.user import UserRole
from schema.token import Token, TokenData
from db.models import User
from dotenv import dotenv_values
from dotenv import load_dotenv

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


load_dotenv()
config_credential = dotenv_values(".env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# HASHING A PASSWORD
def generate_hashed_password(password):
    return pwd_context.hash(password)


# VERIFY PASSWORD AGAINST HASHED VERSION
def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


# CREATE PASSWORD RESET TOKEN
def create_password_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=1)  # token expires in 1 hour
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, config_credential["SECRET"], algorithm="HS256")


# TOKEN
# ACCESS TOKEN
def create_access_token(
    user_id: int, email: str, expires_delta: Optional[timedelta] = None
):
    to_encode = {"user_id": user_id, "email": email}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config_credential["SECRET"], algorithm=ALGORITHM
    )
    return encoded_jwt


# VERIFY ACCESS TOKEN
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, config_credential["SECRET"], algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid",
        )


# CREATE REFRESH TOKEN
def create_refresh_token(user_id: int, email: str):
    to_encode = {"user_id": user_id, "email": email, "type": "refresh"}
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    refresh_token = jwt.encode(
        to_encode, config_credential["SECRET"], algorithm=ALGORITHM
    )
    return refresh_token


# VERIFY REFRESH TOKEN
def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, config_credential["SECRET"], algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
        return payload
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from e


# USER AUTHENTICATION
# Get user
def get_user(db: db_dependency, identifier: str):
    return (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )


# Authenticate user
def authenticate_user(db: db_dependency, identifier: str, password: str):
    user = get_user(db, identifier)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


# DEPENDENCY TO GET CURRENT USER
async def get_current_user(db: db_dependency, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config_credential["SECRET"], algorithms=[ALGORITHM])
        email: str = payload.get("email")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id)
    except JWTError as exc:
        raise credentials_exception from exc
    user = get_user(db, identifier=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# ROLE-BASED ACCESS CONTROL (RBAC)
def check_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
