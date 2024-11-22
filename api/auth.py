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
    # create_refresh_token,
    verify_refresh_token,
)

from core.rbac import has_role
from datetime import timedelta


router = APIRouter()


# LOGIN
@router.post("/login", response_model=Token)
def login(user_login: UserLogin, totp_code: str, db: db_dependency):
    return login_user(db=db, user_login=user_login, totp_code=totp_code)


# Login Router to generate JWT token
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
