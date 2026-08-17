from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, UserRole
from src.auth.dependencies import get_current_user
from src.audit.audit_service import query_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/logs")
def get_system_audit_logs(
    limit: int = 50,
    action: Optional[str] = None,
    result: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve immutable audit logs. Principal can view all; other roles see their own."""
    user_id_filter = None if user.role == UserRole.PRINCIPAL.value else user.id
    return query_audit_logs(db=db, limit=limit, user_id=user_id_filter, action=action, result=result)
