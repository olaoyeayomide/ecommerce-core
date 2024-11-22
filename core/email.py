import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi import HTTPException
from db.models import User
from core.security import create_password_reset_token, create_access_token
from core.mfa import generate_totp_code
from datetime import timedelta


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Your App Name",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_email(subject: str, recipient: str, body: str, subtype="plain"):
    """
    A reusable function to send an email.
    """
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=subtype,
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


async def send_otp_code(user: User):
    """
    Generates and sends a TOTP code to the user's email.
    Assumes the user has 2FA enabled and an `otp_secret` in the database.
    """
    if not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    totp_code = generate_totp_code(user.otp_secret)
    print(f"Sending TOTP code: {totp_code}")

    await send_email(
        subject="Your TOTP Code",
        recipient=user.email,
        body=f"Your TOTP code is {totp_code}. It will expire in 30 seconds.",
        subtype="plain",
    )
    return {"message": "TOTP code sent to email"}


async def send_verification_email(email: str, user: User):
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        expires_delta=timedelta(hours=1),
    )

    verification_link = f"""
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <div style=" display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <h3> Account Verification </h3>
                <br>
                <p>Thanks for choosing EasyShopas, please 
                click on the link below to verify your account</p> 

                <a style="margin-top:1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem; text-decoration: none; background: #0275d8; color: white;"
                 href="http://localhost:8000/verification/?token={token}">
                    Verify your email
                <a>

                <p style="margin-top:1rem;">If you did not register for EasyShopas, 
                please kindly ignore this email and nothing will happen. Thanks<p>
            </div>
        </body>
        </html>
    """

    await send_email(
        subject="Verify Your Email",
        recipient=email,
        body=verification_link,
        subtype="html",
    )


async def send_password_reset_email(user: User):
    reset_token = create_password_reset_token(user.email)

    # Create the reset link
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"

    # Compose the email body with a button
    email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <div style="display: flex; align-items: center; justify-content: center; flex-direction: column; font-family: Arial, sans-serif;">
                <h3>Password Reset Request</h3>
                <p>We received a request to reset your password. If you made this request, click the button below:</p>
                <a href="{reset_link}" 
                   style="margin-top: 1rem; padding: 1rem 2rem; border-radius: 0.5rem; font-size: 1rem; 
                          text-decoration: none; background-color: #007BFF; color: white; display: inline-block;">
                    Reset Password
                </a>
                <p style="margin-top: 1rem;">If you did not request a password reset, you can safely ignore this email.</p>
            </div>
        </body>
        </html>
    """

    # Send the email with the button included
    await send_email(
        subject="Password Reset Request",
        recipient=user.email,
        body=email_body,
        subtype="html",
    )
