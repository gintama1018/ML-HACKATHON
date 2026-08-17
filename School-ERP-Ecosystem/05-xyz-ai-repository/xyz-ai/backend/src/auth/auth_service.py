import hashlib
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models import User, Student, ParentStudentLink, TeacherClassLink
from src.auth.jwt_handler import create_access_token

def hash_password(password: str) -> str:
    salt = "xyz_school_salt_2026"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

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
    
    # Extra role-specific metadata for frontend client bootstrapping
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
            for k in kids if k.student
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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "language_pref": user.language_pref,
            **role_meta
        }
    }
