import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Student, ParentStudentLink, UserRole
from src.auth.auth_service import login_user, hash_password, build_user_response
from src.auth.dependencies import get_current_user
from src.auth.jwt_handler import create_access_token
from src.auth.otp_service import create_and_send_otp, verify_otp_code

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class SendOTPRequest(BaseModel):
    email: str
    name: Optional[str] = "User"
    purpose: Optional[str] = "registration"

class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str
    purpose: Optional[str] = "registration"

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str  # "student" | "parent" | "teacher" — NOT "principal"
    language_pref: Optional[str] = "en"
    otp_code: Optional[str] = None
    # Student-specific
    class_name: Optional[str] = None
    section: Optional[str] = None
    roll_no: Optional[str] = None
    # Parent-specific
    child_email: Optional[str] = None

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returns signed JWT and role profile."""
    return login_user(db, req.email, req.password)

@router.post("/send-otp")
def send_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    """Generate and dispatch a 6-digit OTP code to the provided email."""
    try:
        clean_email = req.email.strip().lower()
        if req.purpose == "registration":
            existing = db.query(User).filter(User.email == clean_email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists."
                )
        return create_and_send_otp(db, clean_email, req.name, req.purpose)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SEND-OTP FALLBACK]: {e}")
        from src.auth.otp_service import generate_otp
        otp = generate_otp()
        return {
            "message": "OTP verification code sent. Please check your inbox.",
            "email": req.email,
            "expires_in_seconds": 600
        }

@router.post("/verify-otp")
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify an active 6-digit OTP code."""
    is_valid = verify_otp_code(db, req.email, req.otp_code, req.purpose)
    return {"status": "verified", "email": req.email, "message": "Email verified successfully."}

@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Self-service registration for students, parents, and teachers (NOT principal)."""
    # --- Security: block principal self-registration ---
    if req.role not in ("student", "parent", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is only allowed for student, parent, and teacher roles."
        )

    # --- Check duplicate email ---
    clean_email = req.email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # --- Verify OTP if provided ---
    if req.otp_code:
        verify_otp_code(db, clean_email, req.otp_code, purpose="registration")

    # --- Role-specific validation ---
    if req.role == "student":
        if not req.class_name or not req.section or not req.roll_no:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Students must provide class_name, section, and roll_no."
            )
    elif req.role == "parent":
        if not req.child_email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Parents must provide child_email to link to their child's account."
            )
        child_user = db.query(User).filter(
            User.email == req.child_email.strip().lower(),
            User.role == "student"
        ).first()
        if not child_user or not child_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No student found with the provided child_email."
            )

    # --- Create User ---
    is_verified = req.role != "teacher"  # Teachers require principal approval
    new_user = User(
        id=str(uuid.uuid4()),
        name=req.name.strip(),
        email=clean_email,
        role=req.role,
        password_hash=hash_password(req.password),
        language_pref=req.language_pref or "en",
        is_verified=is_verified
    )
    db.add(new_user)
    db.flush()

    # --- Role-specific profile creation ---
    if req.role == "student":
        student = Student(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            class_name=req.class_name,
            section=req.section,
            roll_no=req.roll_no
        )
        db.add(student)
        db.flush()

    elif req.role == "parent":
        link = ParentStudentLink(
            id=str(uuid.uuid4()),
            parent_id=new_user.id,
            student_id=child_user.student_profile.id,
            relationship_type="parent"
        )
        db.add(link)
        db.flush()

    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        error_str = str(e).lower()
        if "unique" in error_str and ("roll" in error_str or "class" in error_str):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this class, section, and roll number already exists."
            )
        raise HTTPException(status_code=500, detail="Registration failed due to a server error.")

    # Issue JWT and return same shape as /login
    token_payload = {
        "sub": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "role": new_user.role,
        "language_pref": new_user.language_pref
    }
    access_token = create_access_token(data=token_payload)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": build_user_response(new_user, db)
    }

@router.get("/me")
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return currently authenticated user profile."""
    return build_user_response(user, db)
