from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User
from src.auth.auth_service import login_user
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returns signed JWT and role profile."""
    return login_user(db, req.email, req.password)

@router.get("/me")
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return currently authenticated user profile with linked permissions."""
    role_meta = {}
    if user.role == "student" and user.student_profile:
        role_meta["student_id"] = user.student_profile.id
        role_meta["class_name"] = user.student_profile.class_name
        role_meta["section"] = user.student_profile.section
        role_meta["roll_no"] = user.student_profile.roll_no
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "language_pref": user.language_pref,
        **role_meta
    }
