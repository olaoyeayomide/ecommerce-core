from core.mfa import verify_totp_code
from fastapi import HTTPException, APIRouter, Depends, status
from db.session import db_dependency
from db.models import User
from core.security import get_current_user
from core.mfa import enable_2fa, disable_2fa, generate_totp_qr_base64
from core.rbac import has_role

router = APIRouter()


# ENABLE 2FA
@router.post(
    "/users/enable-2fa",
    response_model=str,
    dependencies=[Depends(has_role(["admin", "user"]))],
)
async def enable_2fa_route(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    """
    Enable 2FA for the authenticated user.
    Returns the otp_secret that can be used to generate QR codes for the user.
    """
    otp_secret = enable_2fa(db, current_user)
    return otp_secret


# DISABLE 2FA
@router.post(
    "/users/disable-2fa",
    response_model=dict,
    dependencies=[Depends(has_role(["admin", "user"]))],
)
async def disable_2fa_route(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    """API route to disable 2FA for the current user."""
    try:
        result = disable_2fa(db=db, user=current_user)
        return result
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# VERIFYING 2FA
@router.post(
    "/users/verify-2fa", dependencies=[Depends(has_role(["admin", "user", "vendor"]))]
)
async def verify_2fa_route(
    code: str,
    # db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    """
    Verify the TOTP code submitted by the user.
    """

    # Check if the user has 2FA enabled by verifying if they have an otp_secret
    if not current_user.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this user.",
        )

    # Verify the TOTP code using the user's otp_secret
    if not verify_totp_code(current_user.otp_secret, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code.",
        )

    return {"msg": "2FA verification successful"}


@router.post(
    "/users/get-qr-code", dependencies=[Depends(has_role(["admin", "user", "vendor"]))]
)
async def get_qr_code(
    db: db_dependency, current_user: User = Depends(get_current_user)
):
    """
    Returns the QR code for the user's TOTP setup as a Base64 string.
    """
    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    qr_code_base64 = generate_totp_qr_base64(
        current_user.email, current_user.otp_secret
    )

    return {"qr_code": qr_code_base64}
