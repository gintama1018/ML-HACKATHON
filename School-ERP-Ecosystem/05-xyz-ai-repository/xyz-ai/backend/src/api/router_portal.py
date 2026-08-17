from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Student, Attendance, ParentStudentLink, TeacherClassLink, Escalation, UserRole
from src.auth.dependencies import get_current_user
from src.i18n.languages import list_supported_languages
from src.tools.mock_erp_adapter import erp_adapter

router = APIRouter(prefix="/portal", tags=["Portal Dashboards"])

@router.get("/languages")
def get_languages():
    """List all 11 supported languages and their localization capabilities."""
    return list_supported_languages()

@router.get("/dashboard")
def get_user_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieve real-time role-tailored dashboard data for frontend portals."""
    role = user.role
    
    if role == UserRole.STUDENT.value:
        if not user.student_profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        att_res = erp_adapter.get_attendance(user, user.student_profile.id, db=db)
        escalations = erp_adapter.get_escalation_status(user, "all", db) if False else []
        return {
            "role": "student",
            "student_profile": {
                "id": user.student_profile.id,
                "name": user.name,
                "class_name": user.student_profile.class_name,
                "section": user.student_profile.section,
                "roll_no": user.student_profile.roll_no,
                "emergency_contact": user.student_profile.emergency_contact
            },
            "attendance": att_res.get("summary", {}),
            "recent_records": att_res.get("recent_records", [])
        }
        
    elif role == UserRole.PARENT.value:
        links = db.query(ParentStudentLink).filter(ParentStudentLink.parent_id == user.id).all()
        children_data = []
        for l in links:
            if l.student:
                att_res = erp_adapter.get_attendance(user, l.student_id, db=db)
                children_data.append({
                    "student_id": l.student_id,
                    "name": l.student.user.name if l.student.user else "Child",
                    "class_name": l.student.class_name,
                    "section": l.student.section,
                    "roll_no": l.student.roll_no,
                    "summary": att_res.get("summary", {}),
                    "recent_records": att_res.get("recent_records", [])
                })
        return {
            "role": "parent",
            "parent_name": user.name,
            "children_count": len(children_data),
            "children": children_data
        }
        
    elif role == UserRole.TEACHER.value:
        classes = db.query(TeacherClassLink).filter(TeacherClassLink.teacher_id == user.id).all()
        class_rosters = []
        for c in classes:
            analytics = erp_adapter.get_attendance_analytics(user, scope="class", class_name=c.class_name, section=c.section, db=db)
            class_rosters.append({
                "class_name": c.class_name,
                "section": c.section,
                "subject": c.subject,
                "analytics": analytics
            })
        return {
            "role": "teacher",
            "teacher_name": user.name,
            "assigned_classes": class_rosters
        }
        
    elif role == UserRole.PRINCIPAL.value:
        analytics = erp_adapter.get_attendance_analytics(user, scope="school", db=db)
        recent_escalations = db.query(Escalation).order_by(Escalation.created_at.desc()).limit(10).all()
        return {
            "role": "principal",
            "principal_name": user.name,
            "school_analytics": analytics,
            "recent_escalations": [
                {
                    "ticket_id": e.id,
                    "user_name": e.user.name if e.user else "Unknown",
                    "target": e.target,
                    "reason": e.reason,
                    "status": e.status,
                    "created_at": e.created_at.isoformat()
                }
                for e in recent_escalations
            ]
        }
        
    raise HTTPException(status_code=400, detail="Unknown role")
