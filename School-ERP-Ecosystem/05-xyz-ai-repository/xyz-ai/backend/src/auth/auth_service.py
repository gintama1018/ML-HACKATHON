from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models import User, Student, ParentStudentLink, TeacherClassLink
from src.auth.jwt_handler import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt with per-user random salt (via passlib)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def build_user_response(user: User, db: Session) -> Dict[str, Any]:
    """Build the role-specific user profile dict for login/register responses."""
    role_meta = {}
    if user.role == "student" and user.student_profile:
        role_meta["student_id"] = user.student_profile.id
        role_meta["class_name"] = user.student_profile.class_name
        role_meta["section"] = user.student_profile.section
        role_meta["roll_no"] = user.student_profile.roll_no
    elif user.role == "parent":
        kids = db.query(ParentStudentLink).filter(ParentStudentLink.parent_id == user.id).all()
        role_meta["linked_students"] = [
            {
                "student_id": k.student_id,
                "name": k.student.user.name,
                "class_name": k.student.class_name,
                "section": k.student.section,
                "roll_no": k.student.roll_no
            }
            for k in kids if k.student and k.student.user
        ]
    elif user.role == "teacher":
        classes = db.query(TeacherClassLink).filter(TeacherClassLink.teacher_id == user.id).all()
        role_meta["assigned_classes"] = [
            {
                "class_name": c.class_name,
                "section": c.section,
                "subject": c.subject
            }
            for c in classes
        ]
        role_meta["is_verified"] = user.is_verified
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "language_pref": user.language_pref,
        "is_verified": user.is_verified,
        **role_meta
    }

def login_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token_payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "language_pref": user.language_pref
    }
    access_token = create_access_token(data=token_payload)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": build_user_response(user, db)
    }
