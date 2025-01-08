from core.mfa import verify_totp_code
from fastapi import HTTPException, APIRouter, Depends, status
from db.session import db_dependency
from db.models import User
from core.security import get_current_user
from core.mfa import enable_2fa, disable_2fa, generate_totp_qr_base64
from core.rbac import has_role

router = APIRouter()


# ENABLE 2FA
# Endpoint to enable Two-Factor Authentication (2FA) for the authenticated user.
# Parameters:
# - `db`: Database session dependency.
# - `current_user`: The currently authenticated user, obtained using `get_current_user`.
# Functionality:
# - Calls the `enable_2fa` function to enable 2FA for the user.
# - Returns the OTP secret associated with the user, which can be used to generate a QR code.
@router.post(
    "/users/enable-2fa",
    response_model=str,
    dependencies=[Depends(has_role(["admin", "user"]))],
)
async def enable_2fa_route(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    otp_secret = enable_2fa(db, current_user)
    return otp_secret


# DISABLE 2FA
# Endpoint to disable Two-Factor Authentication (2FA) for the authenticated user.
# Parameters:
# - `db`: Database session dependency.
# - `current_user`: The currently authenticated user, obtained using `get_current_user`.
# Functionality:
# - Calls the `disable_2fa` function to disable 2FA for the user.
# - Returns a success message or raises an exception in case of failure.
@router.post(
    "/users/disable-2fa",
    response_model=dict,
    dependencies=[Depends(has_role(["admin", "user"]))],
)
async def disable_2fa_route(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    try:
        result = disable_2fa(db=db, user=current_user)
        return result
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


# VERIFYING 2FA
# Endpoint to verify the TOTP code submitted by the user.
# Parameters:
# - `code`: The TOTP code submitted by the user for verification.
# - `current_user`: The currently authenticated user, obtained using `get_current_user`.
# Functionality:
# - Checks if the user has 2FA enabled by verifying the presence of an `otp_secret`.
# - Calls `verify_totp_code` to validate the submitted code against the user's `otp_secret`.
# - Returns a success message if the code is valid or raises an exception if it is invalid.
@router.post(
    "/users/verify-2fa", dependencies=[Depends(has_role(["admin", "user", "vendor"]))]
)
async def verify_2fa_route(
    code: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this user.",
        )
    if not verify_totp_code(current_user.otp_secret, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code.",
        )
    return {"msg": "2FA verification successful"}


# GET QR CODE
# Endpoint to retrieve the QR code for the user's TOTP setup as a Base64 string for the user's 2FA setup.
# Parameters:
# - `db`: Database session dependency.
# - `current_user`: The currently authenticated user, obtained using `get_current_user`.
# Functionality:
# - Validates if 2FA is enabled for the user by checking for an `otp_secret`.
# - Calls `generate_totp_qr_base64` to generate the QR code in Base64 format.
# - Returns the Base64 string representation of the QR code.
@router.post(
    "/users/get-qr-code", dependencies=[Depends(has_role(["admin", "user", "vendor"]))]
)
async def get_qr_code(current_user: User = Depends(get_current_user)):
    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")
    qr_code_base64 = generate_totp_qr_base64(
        current_user.email, current_user.otp_secret
    )
    return {"qr_code": qr_code_base64}
