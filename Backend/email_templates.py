from datetime import datetime


def _get_footer():
    current_year = datetime.now().year
    return f"""
    <div class="footer">
        <p>© {current_year} Sentinel Bank Ltd. All rights reserved.</p>
        <p>123 Banking Way, Digital City, NG.</p>
        <p>If you did not request this communication, please ignore this email or contact support.</p>
    </div>
    """


def get_otp_template(otp_code: str, verify_link: str = None):
    footer = _get_footer()
    magic_link_html = ""
    if verify_link:
        magic_link_html = f"""
        <div style="margin-top: 30px;">
            <p>Alternatively, click the button below to verify your account instantly:</p>
            <a href="{verify_link}" class="btn" style="color: #ffffff;">Verify Account</a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sentinel Bank Verification</title>
        <style>
            body {{ font-family: 'Inter', -apple-system, blinkmacsystemfont, 'Segoe UI', roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f7f9; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
            .header {{ background-color: #001F3F; color: #ffffff; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 1px; color: #FFD700; }}
            .content {{ padding: 40px; text-align: center; }}
            .otp-box {{ background: #f8f9fa; border: 1px dashed #001F3F; border-radius: 4px; padding: 20px; margin: 30px 0; display: inline-block; }}
            .otp-code {{ font-size: 36px; font-weight: bold; letter-spacing: 5px; color: #001F3F; margin: 0; }}
            .footer {{ background: #f8f9fa; color: #666; padding: 20px; text-align: center; font-size: 12px; }}
            .security-note {{ color: #d9534f; font-weight: bold; font-size: 13px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background-color: #001F3F; color: #ffffff; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SENTINEL BANK</h1>
            </div>
            <div class="content">
                <h2>Security Verification</h2>
                <p>Hello, thank you for choosing Sentinel Bank. To complete your request, please use the following One-Time Password (OTP):</p>
                
                <div class="otp-box">
                    <p class="otp-code">{otp_code}</p>
                </div>
                
                {magic_link_html}
                
                <p style="margin-top: 30px;">This code is valid for <strong>15 minutes</strong>. Please do not share this code with anyone.</p>
                <p class="security-note">Sentinel Bank will never ask for your password or OTP over the phone.</p>
            </div>
            {footer}
        </div>
    </body>
    </html>
    """


def get_password_reset_template(reset_link: str):
    footer = _get_footer()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sentinel Bank Password Reset</title>
        <style>
            body {{ font-family: 'Inter', -apple-system, blinkmacsystemfont, 'Segoe UI', roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f7f9; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
            .header {{ background-color: #001F3F; color: #ffffff; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 1px; color: #FFD700; }}
            .content {{ padding: 40px; text-align: center; }}
            .footer {{ background: #f8f9fa; color: #666; padding: 20px; text-align: center; font-size: 12px; }}
            .btn {{ display: inline-block; padding: 15px 30px; background-color: #001F3F; color: #ffffff !important; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 20px; border: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SENTINEL BANK</h1>
            </div>
            <div class="content">
                <h2>Reset Your Password</h2>
                <p>We received a request to reset the password for your Sentinel Bank account.</p>
                <p>Click the button below to choose a new password. This link will expire in 1 hour.</p>
                
                <a href="{reset_link}" class="btn">Reset Password</a>
                
                <p style="margin-top: 30px; font-size: 14px; color: #666;">
                    If the button doesn't work, copy and paste this URL into your browser: <br>
                    <a href="{reset_link}" style="color: #001F3F;">{reset_link}</a>
                </p>
                
                <p style="margin-top: 30px;">If you didn't request a password reset, you can safely ignore this email.</p>
            </div>
            {footer}
        </div>
    </body>
    </html>
    """


def get_complaint_confirmation_template(
    complaint_id: str, department: str, priority: str
):
    footer = _get_footer()
    priority_color = (
        "#d9534f"
        if priority.lower() == "high"
        else "#f0ad4e" if priority.lower() == "medium" else "#5bc0de"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sentinel Bank Complaint Received</title>
        <style>
            body {{ font-family: 'Inter', -apple-system, blinkmacsystemfont, 'Segoe UI', roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f7f9; }}
            .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
            .header {{ background-color: #001F3F; color: #ffffff; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 1px; color: #FFD700; }}
            .content {{ padding: 40px; }}
            .info-box {{ background: #f8f9fa; border-left: 4px solid #001F3F; padding: 20px; margin: 25px 0; }}
            .info-item {{ margin-bottom: 10px; font-size: 15px; }}
            .info-label {{ font-weight: bold; color: #555; width: 120px; display: inline-block; }}
            .priority-tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: #fff; background-color: {priority_color}; text-transform: uppercase; }}
            .footer {{ background: #f8f9fa; color: #666; padding: 20px; text-align: center; font-size: 12px; }}
            .status-update {{ text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SENTINEL BANK</h1>
            </div>
            <div class="content">
                <h2 style="text-align: center; color: #001F3F;">Complaint Received</h2>
                <p>Hello,</p>
                <p>We have received your email and our AI system has successfully categorized your complaint. Our specialized team has been notified and is currently reviewing the details.</p>
                
                <div class="info-box">
                    <div class="info-item">
                        <span class="info-label">Ticket ID:</span>
                        <span style="font-family: monospace; font-weight: bold;">{complaint_id}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Department:</span>
                        <span>{department}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Priority:</span>
                        <span class="priority-tag">{priority}</span>
                    </div>
                </div>
                
                <p>No further action is required from your side at this moment. You will receive an update as soon as there is progress on your case.</p>
                
                <div class="status-update">
                    Thank you for your patience and for choosing Sentinel Bank.
                </div>
            </div>
            {footer}
        </div>
    </body>
    </html>
    """
