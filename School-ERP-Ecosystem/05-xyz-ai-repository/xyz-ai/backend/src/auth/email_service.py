import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple

# Environment configurations for real email sending
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "noreply@xyzschool.edu")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

def send_otp_email(to_email: str, otp_code: str, name: str = "User") -> Tuple[bool, str]:
    """
    Sends a 6-digit OTP email to the recipient.
    Supports:
    1. Resend API (if RESEND_API_KEY is provided)
    2. Standard TLS SMTP (Gmail App Password, Brevo, SendGrid, Amazon SES)
    3. Graceful fallback with clear logging if SMTP is not yet configured.
    """
    subject = f"Your XYZ AI Verification Code: {otp_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #FAF7EE; margin: 0; padding: 24px; color: #2D261A; }}
        .container {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #EAE4D5; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
        .header {{ text-align: center; border-bottom: 2px solid #FAF7EE; padding-bottom: 16px; margin-bottom: 24px; }}
        .brand {{ font-size: 24px; font-weight: 700; color: #9C5400; letter-spacing: -0.5px; }}
        .otp-box {{ background: #FFF3E6; border: 2px dashed #E87A1E; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
        .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #E87A1E; font-family: monospace; }}
        .footer {{ font-size: 12px; color: #78716C; text-align: center; margin-top: 24px; border-top: 1px solid #FAF7EE; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="brand">XYZ AI Assistant</div>
          <p style="margin:4px 0 0; font-size:14px; color:#78716C;">School ERP Authentication</p>
        </div>
        <p>Hello <strong>{name}</strong>,</p>
        <p>Use the following 6-digit verification code to complete your registration on XYZ AI School Assistant:</p>
        <div class="otp-box">
          <div class="otp-code">{otp_code}</div>
          <p style="margin:8px 0 0; font-size:12px; color:#C05621; font-weight:600;">Valid for 10 minutes</p>
        </div>
        <p style="font-size:13px; color:#57534E;">If you did not request this verification code, please ignore this email or notify school security.</p>
        <div class="footer">
          XYZ AI School Assistant Ecosystem • Secure RBAC Portal
        </div>
      </div>
    </body>
    </html>
    """
    
    text_content = f"Hello {name},\n\nYour XYZ AI verification code is: {otp_code}\nThis code is valid for 10 minutes.\n\nXYZ AI School Assistant"

    # 1. Attempt Resend API
    if RESEND_API_KEY:
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps({
                    "from": SMTP_FROM_EMAIL or "XYZ AI <onboarding@resend.dev>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    return True, "Email sent via Resend API"
        except Exception as e:
            print(f"[EMAIL ERROR via Resend]: {e}")

    # 2. Attempt Standard SMTP (Gmail, Brevo, SendGrid, SES)
    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"XYZ AI Assistant <{SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            if SMTP_PORT == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
                    
            print(f"[EMAIL SUCCESS] Real OTP {otp_code} delivered to {to_email} via {SMTP_HOST}")
            return True, f"OTP sent to {to_email}"
        except Exception as e:
            print(f"[EMAIL ERROR via SMTP]: {e}")
            return False, f"SMTP error: {str(e)}"
    
    # 3. Development / Mock Mode (When SMTP credentials are not yet configured in .env)
    print(f"\n=======================================================")
    print(f"📧 [DEV EMAIL SIMULATOR] To: {to_email}")
    print(f"🔑 OTP CODE: {otp_code}")
    print(f"💡 NOTE: To send REAL emails to Gmail inboxes, add SMTP_USER & SMTP_PASSWORD (e.g. Gmail App Password) to your .env or Vercel Environment Variables.")
    print(f"=======================================================\n")
    return True, "OTP generated (Configure SMTP_USER & SMTP_PASSWORD for real mail delivery)"
