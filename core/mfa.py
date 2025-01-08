import pyotp
import qrcode
from db.models import User
from db.session import db_dependency
from fastapi import HTTPException
import io
import base64


# **Generate TOTP Secret**
# - Generates a random base32 secret for TOTP authentication.
# - This secret will be used to generate time-based one-time passwords (TOTP).
def generate_totp_secret():
    return pyotp.random_base32()


# ENABLE 2FA
# **Enable Two-Factor Authentication (2FA)**
# - Parameters:
#   - `db`: The database dependency for session management.
#   - `user`: The user object for whom 2FA is being enabled.
# - Response:
#   - The generated TOTP secret.
# - Details:
#   - This function generates a TOTP secret and saves it in the user's record.
#   - Ensures the user record is committed and refreshed.
def enable_2fa(db: db_dependency, user: User):
    """Enable 2FA by generating and saving an otp_secret for the user."""
    totp_secret = generate_totp_secret()
    user.otp_secret = totp_secret  # Generates a TOTP secret
    db.commit()
    db.refresh(user)
    return totp_secret


# DISABLE 2FA
# **Disable Two-Factor Authentication (2FA)**
# - Parameters:
#   - `db`: The database dependency for session management.
#   - `user`: The user object for whom 2FA is being disabled.
# - Response:
#   - A message indicating that 2FA has been disabled.
# - Details:
#   - This function clears the `otp_secret` field in the user's record.
#   - Raises an HTTPException if 2FA is not enabled.
def disable_2fa(db: db_dependency, user: User):
    """Disable 2FA by clearing the otp_secret."""
    if not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")
    user.otp_secret = None
    db.commit()
    db.refresh(user)
    return {"msg": "2FA disabled"}


# **GENERATE TOTP CODE**
# - Parameters:
#   - `otp_secret` (str): The user's TOTP secret.
#   - `interval` (int): The time interval for TOTP generation (default is 120 seconds).
# - Response:
#   - A TOTP code as a string.
# - Details:
#   - This function generates a time-sensitive one-time password using the TOTP secret.
def generate_totp_code(otp_secret: str, interval: int = 120) -> str:
    """Generates a TOTP code based on the user's otp_secret."""
    totp = pyotp.TOTP(otp_secret, interval=interval)
    totp_code = totp.now()  # Generate the TOTP code
    print(f"Generated TOTP code: {totp_code}")
    return totp.now()


# **VERIFY TOTP CODE**
# - Parameters:
#   - `otp_secret` (str): The user's TOTP secret.
#   - `code` (str): The TOTP code to be verified.
#   - `interval` (int): The time interval for TOTP validation (default is 120 seconds).
# - Response:
#   - A boolean indicating whether the code is valid.
# - Details:
#   - This function validates a given TOTP code against the user's TOTP secret.
#   - Raises a ValueError if the user does not have 2FA enabled.
def verify_totp_code(otp_secret, code: str, interval: int = 120) -> bool:
    """Verify a TOTP code using the user's otp_secret."""
    if not otp_secret:
        raise ValueError("2FA is not enabled for this user.")
    totp = pyotp.TOTP(otp_secret, interval=interval)
    expected_code = totp.now()
    print(f"Expected TOTP code:{expected_code}")
    return totp.verify(code)


# GENERATE QR CODE
# **Generate QR Code for TOTP Secret**
# - Parameters:
#   - `user_email` (str): The user's email address.
#   - `totp_secret` (str): The TOTP secret to be encoded into the QR code.
# - Response:
#   - A Base64-encoded string of the QR code image.
# - Details:
#   - This function generates a QR code representing the TOTP secret in URI format.
#   - Encodes the QR code image as a Base64 string for easy transmission and display.
def generate_totp_qr_base64(user_email, totp_secret):
    totp_uri = pyotp.TOTP(totp_secret).provisioning_uri(
        user_email, issuer_name="YourAppName"
    )
    img = qrcode.make(totp_uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return qr_code_base64
