import pyotp
import qrcode
from db.models import User
from db.session import db_dependency
from fastapi import HTTPException
import io
import base64


# Generate TOTP Secret for a user
def generate_totp_secret():
    return pyotp.random_base32()


# ENABLE 2FA
def enable_2fa(db: db_dependency, user: User):
    """Enable 2FA by generating and saving an otp_secret for the user."""
    totp_secret = generate_totp_secret()
    user.otp_secret = totp_secret  # Generates a TOTP secret
    db.commit()
    db.refresh(user)
    return totp_secret


# DISABLE 2FA (This function is used to remove or reset the otp_secret assocated with the user authentication.)
def disable_2fa(db: db_dependency, user: User):
    """Disable 2FA by clearing the otp_secret."""
    if not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")
    user.otp_secret = None
    db.commit()
    db.refresh(user)
    return {"msg": "2FA disabled"}


# GENERATE TOTP CODE
def generate_totp_code(otp_secret: str, interval: int = 120) -> str:
    """Generates a TOTP code based on the user's otp_secret."""
    totp = pyotp.TOTP(otp_secret, interval=interval)
    totp_code = totp.now()  # Generate the TOTP code
    print(f"Generated TOTP code: {totp_code}")
    return totp.now()


# VERIFY TOTP CODE
def verify_totp_code(otp_secret, code: str, interval: int = 120) -> bool:
    """Verify a TOTP code using the user's otp_secret."""
    if not otp_secret:
        raise ValueError("2FA is not enabled for this user.")
    totp = pyotp.TOTP(otp_secret, interval=interval)
    expected_code = totp.now()
    print(f"Expected TOTP code:{expected_code}")
    return totp.verify(code)


# Generate a QR Code for the TOTP Secret(representing the totp_secret)
def generate_totp_qr_base64(user_email, totp_secret):
    totp_uri = pyotp.TOTP(totp_secret).provisioning_uri(
        user_email, issuer_name="YourAppName"
    )
    img = qrcode.make(totp_uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return qr_code_base64


# def generate_totp_qr(user_email, totp_secret):
#     """Generate a QR Code for TOTP setup in an authenticator app."""
#     totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
#         user_email, issuer_name="YourAppName"
#     )
#     img = qrcode.make(totp_uri)
#     img.save(f"{user_email}_qrcode.png")  # Save the QR code locally for demo
