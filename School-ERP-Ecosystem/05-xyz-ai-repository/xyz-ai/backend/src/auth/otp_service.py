import os
import secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models import EmailOTP, utc_now
from src.auth.email_service import send_otp_email

def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"

def create_and_send_otp(db: Session, email: str, name: str = "User", purpose: str = "registration") -> dict:
    """
    Creates an OTP record in database with a 10-minute expiry and dispatches it via email service.
    """
    email_clean = email.strip().lower()
    
    # Invalidate previous unused OTPs for this email & purpose
    db.query(EmailOTP).filter(
        EmailOTP.email == email_clean,
        EmailOTP.purpose == purpose,
        EmailOTP.is_used == False
    ).update({"is_used": True})
    
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    record = EmailOTP(
        email=email_clean,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=expires_at,
        is_used=False
    )
    db.add(record)
    db.commit()
    
    success, msg = send_otp_email(email_clean, otp_code, name)
    return {
        "message": "OTP verification code sent. Please check your email inbox and spam folder.",
        "email": email_clean,
        "expires_in_seconds": 600
    }

def verify_otp_code(db: Session, email: str, otp_code: str, purpose: str = "registration") -> bool:
    """
    Verifies that the provided OTP matches the active unexpired OTP for the email.
    """
    email_clean = email.strip().lower()
    otp_clean = otp_code.strip()
    
    now = datetime.now(timezone.utc)
    
    otp_record = db.query(EmailOTP).filter(
        EmailOTP.email == email_clean,
        EmailOTP.otp_code == otp_clean,
        EmailOTP.purpose == purpose,
        EmailOTP.is_used == False,
        EmailOTP.expires_at >= now
    ).order_by(EmailOTP.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code. Please request a new verification code."
        )
    
    # Mark as used
    otp_record.is_used = True
    db.commit()
    return True
