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


# Constants for token generation and validation
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Load environment variables
load_dotenv()
config_credential = dotenv_values(".env")

# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Password Bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ---------------------------
# Utility Functions
# ---------------------------


# HASHING A PASSWORD
# - Hashes a plain text password using bcrypt.
# - Parameters:
#   - `password` (str): The plain text password to hash.
# - Returns:
#   - (str): The hashed password.
def generate_hashed_password(password):
    return pwd_context.hash(password)


# VERIFY PASSWORD AGAINST HASHED VERSION
# - Verifies if a given plain text password matches a hashed password.
# - Parameters:
#   - `password` (str): The plain text password.
#   - `hashed_password` (str): The hashed password for comparison.
# - Returns:
#   - (bool): True if the passwords match; False otherwise.
def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


# ---------------------------
# Token Management Functions
# ---------------------------


# CREATE PASSWORD RESET TOKEN
# - Generates a JWT token for password reset purposes.
# - Parameters:
#   - `email` (str): The email of the user requesting a password reset.
# - Returns:
#   - (str): A JWT token that expires in 1 hour.
def create_password_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=1)  # token expires in 1 hour
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, config_credential["SECRET"], algorithm="HS256")


# CREATE ACCESS TOKEN
# - Generates an access token for user authentication.
# - Parameters:
#   - `user_id` (int): The user's ID.
#   - `email` (str): The user's email.
#   - `expires_delta` (Optional[timedelta]): Custom expiration duration (optional).
# - Returns:
#   - (str): A JWT access token.
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
# - Validates the provided access token.
# - Parameters:
#   - `token` (str): The JWT access token.
# - Returns:
#   - (str): The email of the token's owner if valid.
# - Raises:
#   - `HTTPException`: If the token is expired or invalid.
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
# - Generates a refresh token for renewing access tokens.
# - Parameters:
#   - `user_id` (int): The user's ID.
#   - `email` (str): The user's email.
# - Returns:
#   - (str): A JWT refresh token.
def create_refresh_token(user_id: int, email: str):
    to_encode = {"user_id": user_id, "email": email, "type": "refresh"}
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    refresh_token = jwt.encode(
        to_encode, config_credential["SECRET"], algorithm=ALGORITHM
    )
    return refresh_token


# VERIFY REFRESH TOKEN
# - Validates the provided refresh token.
# - Parameters:
#   - `token` (str): The JWT refresh token.
# - Returns:
#   - (dict): Decoded token payload if valid.
# - Raises:
#   - `HTTPException`: If the token is invalid or not a refresh token.
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


# ---------------------------
# User Authentication Functions
# ---------------------------


# GET USER BY IDENTIFIER
# - Retrieves a user from the database using email or username.
# - Parameters:
#   - `db` (db_dependency): The database session.
#   - `identifier` (str): The user's email or username.
# - Returns:
#   - (User): The user object if found; None otherwise.
def get_user(db: db_dependency, identifier: str):
    return (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )


# AUTHENTICATE USER
# - Verifies the user's credentials.
# - Parameters:
#   - `db` (db_dependency): The database session.
#   - `identifier` (str): The user's email or username.
#   - `password` (str): The user's password.
# - Returns:
#   - (User | bool): The authenticated user object if successful; False otherwise.
def authenticate_user(db: db_dependency, identifier: str, password: str):
    user = get_user(db, identifier)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


# DEPENDENCY TO GET CURRENT USER
# - Retrieves the currently authenticated user based on the token.
# - Parameters:
#   - `db` (db_dependency): The database session.
#   - `token` (str): The OAuth2 bearer token.
# - Returns:
#   - (User): The currently authenticated user.
# - Raises:
#   - `HTTPException`: If the token is invalid or the user does not exist.
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
