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


# SEND 2FA CODE
# Endpoint to send a Two-Factor Authentication (2FA) code to the user's email.
# Requires the user to have a valid role (e.g., admin, user, or vendor) using role-based access control (RBAC).
# Parameters:
# - `email`: The email address of the user requesting the 2FA code.
# - `db`: Database session dependency.
# Functionality:
# - Retrieves the user from the database by their email.
# - Checks if the user exists and has 2FA enabled (via `otp_secret`).
# - Sends a TOTP code to the user's email using the `send_otp_code` function.
# Returns:
# - A success message if the TOTP code is sent successfully.
# Raises:
# - `HTTPException` with status 400 if the user is not found or 2FA is not enabled.
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


# EMAIL VERIFICATION
# Endpoint to handle email verification using a token.
# Parameters:
# - `request`: The HTTP request object, used for rendering the template.
# - `token`: The email verification token sent to the user.
# - `db`: Database session dependency.
# - `response`: The HTTP response object for setting cookies.
# Functionality:
# - Verifies the provided token to extract the user's email.
# - Checks if the user exists in the database and if their account is inactive.
# - Activates the user's account (`is_active` set to True) and commits changes to the database.
# - Sets a secure cookie containing the verification token with an expiration time.
# - Returns an HTML page indicating successful verification using the `verification.html` template.
# Raises:
# - `HTTPException` with status 401 if the token is invalid or expired, or if the user is not found.
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
