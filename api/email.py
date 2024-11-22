from core.email import send_otp_code
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import HTMLResponse
from db.session import db_dependency
from db.models import User
from fastapi.templating import Jinja2Templates
from fastapi import status
from core.security import verify_access_token
from core.rbac import has_role


templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.post(
    "/users/send-2fa-code/",
    dependencies=[Depends(has_role(["admin", "user", "vendor"]))],
)
async def send_2fa_code(email: str, db: db_dependency):
    # Retrieve the user from the database
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.otp_secret:
        raise HTTPException(
            status_code=400, detail="User not found or 2FA not enabled."
        )

    # Send TOTP code to user's email
    await send_otp_code(user)
    return {"message": "TOTP code sent to user's email"}


@router.get("/verification", response_class=HTMLResponse)
async def send_email_verification(
    request: Request, token: str, db: db_dependency, response: Response
):
    email = verify_access_token(token)

    user = db.query(User).filter(User.email == email).first()

    if user and not user.is_active:
        user.is_active = True
        db.commit()

        response.set_cookie(
            key="verification_token",
            value=token,
            httponly=True,
            secure=True,
            max_age=3600,
            samesite="Strict",
        )

        return templates.TemplateResponse(
            "verification.html", {"request": request, "username": user.username}
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token user or expired token",
        headers={"WWW.Authenticate": "Bearer"},
    )
