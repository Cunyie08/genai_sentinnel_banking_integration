import asyncio
import logging
import os
import resend
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from Backend.email_templates import (
    get_otp_template,
    get_password_reset_template,
    get_complaint_confirmation_template,
    get_department_routing_template
)

load_dotenv()

# Environment config
from app.settings import APP_URL, EMAIL_FROM, RESEND_API_KEY

resend.api_key = RESEND_API_KEY


async def send_otp_email(to_email: str, otp_code: str):
    """Sends a premium HTML OTP email with a Magic Link."""
    verify_link = f"{APP_URL}/auth/verify-link?email={to_email}&otp_code={otp_code}&purpose=registration"
    html_content = get_otp_template(otp_code, verify_link)
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

async def send_department_routing_email(
    to_email: str, complaint_id: str, complaint_text: str, department: str, priority: str
):
    """Sends the actual complaint text to the department representative."""
    html_content = get_department_routing_template(
        complaint_id, complaint_text, department, priority
    )
    return await send_auth_email(
        to_email, f"New Routed Complaint: {department} ({complaint_id})", html_content
    )


async def send_auth_email(to_email: str, subject: str, content: str):
    """
    Sends an authentication-related email using Resend.
    Uses asyncio.to_thread so the blocking Resend SDK call does not stall the event loop.
    """
    if not resend.api_key:
        logger.info("[MOCK EMAIL] subject=%s", subject)
        return True

    try:
        params = {
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": content,
        }
        # resend.Emails.send() is synchronous — run in thread pool to avoid blocking
        email = await asyncio.to_thread(resend.Emails.send, params)
        return email
    except Exception as e:
        logger.error("Email send failed (%s): %s", type(e).__name__, e)
        return False
