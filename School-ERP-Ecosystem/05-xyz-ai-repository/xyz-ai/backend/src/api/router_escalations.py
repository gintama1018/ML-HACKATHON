from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User
from src.auth.dependencies import get_current_user
from src.escalation.escalation_service import escalation_service

router = APIRouter(prefix="/escalations", tags=["Escalations"])

class CreateEscalationRequest(BaseModel):
    target: str  # teacher, management
    reason: str
    contact_info: Optional[str] = None

class ConfirmEscalationRequest(BaseModel):
    notes: Optional[str] = None

class ResolveEscalationRequest(BaseModel):
    resolution_summary: str

@router.get("")
def list_escalations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List escalation tickets visible to the user."""
    return escalation_service.list_user_escalations(user, db)

@router.post("/create")
def create_escalation(
    req: CreateEscalationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate an escalation request (status=PENDING)."""
    try:
        return escalation_service.create_escalation_ticket(
            user=user,
            target=req.target,
            reason=req.reason,
            contact_info=req.contact_info,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{ticket_id}/confirm")
def confirm_escalation(
    ticket_id: str,
    req: ConfirmEscalationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm a pending escalation ticket and dispatch notifications."""
    try:
        return escalation_service.confirm_escalation_ticket(
            user=user,
            ticket_id=ticket_id,
            confirmation_notes=req.notes,
            db=db
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{ticket_id}/resolve")
def resolve_escalation(
    ticket_id: str,
    req: ResolveEscalationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an escalation ticket as resolved (Teacher or Principal only)."""
    try:
        return escalation_service.resolve_escalation_ticket(
            user=user,
            ticket_id=ticket_id,
            resolution_summary=req.resolution_summary,
            db=db
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
