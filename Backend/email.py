import os
import resend
from dotenv import load_dotenv

from Backend.email_templates import (
    get_otp_template,
    get_password_reset_template,
    get_complaint_confirmation_template,
)

load_dotenv()

# Pre-requisite: RESEND_API_KEY must be in .env
resend.api_key = os.getenv("RESEND_API_KEY")


async def send_otp_email(to_email: str, otp_code: str):
    """Sends a premium HTML OTP email."""
    html_content = get_otp_template(otp_code)
    return await send_auth_email(
        to_email, "Verify your Sentinel Bank Account", html_content
    )


async def send_password_reset_email(to_email: str, reset_link: str):
    """Sends a premium HTML Password Reset email."""
    html_content = get_password_reset_template(reset_link)
    return await send_auth_email(
        to_email, "Reset your Sentinel Bank Password", html_content
    )


async def send_complaint_confirmation_email(
    to_email: str, complaint_id: str, department: str, priority: str
):
    """Sends a premium HTML Complaint Confirmation email."""
    html_content = get_complaint_confirmation_template(
        complaint_id, department, priority
    )
    return await send_auth_email(
        to_email, f"Sentinel Bank - Complaint Received ({complaint_id})", html_content
    )


async def send_auth_email(to_email: str, subject: str, content: str):
    """
    Sends an authentication-related email (OTP or Reset Link) using Resend.
    In development mode or if key is missing, it logs to console.
    """
    if not resend.api_key:
        print(f"\n[MOCK EMAIL SENT to {to_email}]")
        print(f"Subject: {subject}")
        print(f"Content: {content}\n")
        return True

    try:
        params = {
            "from": "Sentinel Bank <onboarding@resend.dev>",  # Adjust once domain is verified
            "to": [to_email],
            "subject": subject,
            "html": content,
        }

        email = resend.Emails.send(params)
        return email
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
