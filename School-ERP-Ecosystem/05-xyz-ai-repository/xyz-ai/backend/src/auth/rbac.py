from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models import (
    User, Student, ParentStudentLink, TeacherClassLink,
    Escalation, AuditLog, UserRole, AuditResult
)

class PermissionDeniedError(HTTPException):
    def __init__(self, detail: str = "Permission denied: unauthorized action on resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

def log_audit_event(
    db: Session,
    user_id: Optional[str],
    action: str,
    resource: str,
    result: str,
    details: str = "",
    ip_address: str = "127.0.0.1"
):
    """Write audit log entry into system of record."""
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        # Audit logging failure should not crash, but print warning
        print(f"[AUDIT LOGGING ERROR]: {e}")

class RBACManager:
    """Deterministic Application-Layer RBAC Engine."""
    
    @staticmethod
    def check_view_student_attendance(user: User, student_id: str, db: Session) -> Tuple[bool, str]:
        """Check if user has permission to view attendance for a specific student."""
        # 1. Student can only view own attendance
        if user.role == UserRole.STUDENT.value:
            if not user.student_profile or user.student_profile.id != student_id:
                return False, f"Student '{user.name}' (user_id={user.id}) cannot view attendance of other students (target={student_id})."
            return True, "Authorized: viewing own attendance."
            
        # 2. Parent can only view linked children's attendance
        elif user.role == UserRole.PARENT.value:
            link = db.query(ParentStudentLink).filter(
                ParentStudentLink.parent_id == user.id,
                ParentStudentLink.student_id == student_id
            ).first()
            if not link:
                return False, f"Parent '{user.name}' is not authorized to view unlinked student (target={student_id})."
            return True, f"Authorized: parent viewing linked child ({student_id})."
            
        # 3. Teacher can only view students in their assigned classes
        elif user.role == UserRole.TEACHER.value:
            target_student = db.query(Student).filter(Student.id == student_id).first()
            if not target_student:
                return False, f"Target student '{student_id}' does not exist."
            
            assigned = db.query(TeacherClassLink).filter(
                TeacherClassLink.teacher_id == user.id,
                TeacherClassLink.class_name == target_student.class_name,
                TeacherClassLink.section == target_student.section
            ).first()
            if not assigned:
                return False, f"Teacher '{user.name}' is not assigned to Class {target_student.class_name}-{target_student.section}."
            return True, f"Authorized: teacher viewing student in assigned class {target_student.class_name}-{target_student.section}."
            
        # 4. Principal can view any student attendance for institutional oversight
        elif user.role == UserRole.PRINCIPAL.value:
            return True, "Authorized: Principal oversight access."
            
        return False, f"Unknown or unauthorized role '{user.role}'."

    @staticmethod
    def check_mark_student_attendance(user: User, student_id: str, db: Session) -> Tuple[bool, str]:
        """Check if user has permission to mark attendance for a student (Teacher only, assigned class only)."""
        if user.role != UserRole.TEACHER.value:
            return False, f"Only teachers can mark attendance. Role '{user.role}' is not authorized."
            
        target_student = db.query(Student).filter(Student.id == student_id).first()
        if not target_student:
            return False, f"Target student '{student_id}' does not exist."
            
        assigned = db.query(TeacherClassLink).filter(
            TeacherClassLink.teacher_id == user.id,
            TeacherClassLink.class_name == target_student.class_name,
            TeacherClassLink.section == target_student.section
        ).first()
        if not assigned:
            return False, f"Teacher '{user.name}' cannot mark attendance for Class {target_student.class_name}-{target_student.section} (unassigned class)."
            
        return True, f"Authorized: teacher marking attendance for assigned class {target_student.class_name}-{target_student.section}."

    @staticmethod
    def check_view_analytics(user: User, scope: Optional[str], db: Session) -> Tuple[bool, str]:
        """Check if user can view aggregate school/class analytics."""
        if user.role == UserRole.PRINCIPAL.value:
            return True, "Authorized: Principal full institutional analytics access."
        elif user.role == UserRole.TEACHER.value:
            # Teacher can view analytics only for their class
            if scope and scope.startswith("class_"):
                class_sec = scope.replace("class_", "")
                parts = class_sec.split("-")
                if len(parts) == 2:
                    cls, sec = parts
                    assigned = db.query(TeacherClassLink).filter(
                        TeacherClassLink.teacher_id == user.id,
                        TeacherClassLink.class_name == cls,
                        TeacherClassLink.section == sec
                    ).first()
                    if assigned:
                        return True, f"Authorized: teacher viewing analytics for assigned class {class_sec}."
            return False, f"Teachers cannot view school-wide analytics or unassigned classes."
        else:
            return False, f"Role '{user.role}' is not authorized to view aggregate attendance analytics."

    @staticmethod
    def check_student_profile_access(user: User, student_id: str, db: Session) -> Tuple[bool, str]:
        """Check if user can view student profile (follows same rules as attendance view)."""
        return RBACManager.check_view_student_attendance(user, student_id, db)

    @staticmethod
    def check_escalation_confirmation(user: User, escalation_id: str, db: Session) -> Tuple[bool, str]:
        """Check if user has right to confirm/modify an escalation ticket."""
        esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            return False, f"Escalation ticket '{escalation_id}' not found."
            
        # Creator can confirm, or Principal/Management can confirm/resolve
        if esc.user_id == user.id or user.role == UserRole.PRINCIPAL.value:
            return True, "Authorized: user confirms own escalation or Principal resolves."
            
        return False, f"User '{user.name}' is not authorized to modify escalation ticket '{escalation_id}'."

def enforce_permission(
    user: User,
    action: str,
    resource: str,
    resource_id: Optional[str],
    db: Session,
    extra_params: Optional[Dict[str, Any]] = None
):
    """
    Central permission enforcement point.
    Audits the decision immediately and raises PermissionDeniedError on denial.
    """
    extra_params = extra_params or {}
    allowed = False
    reason = "Unknown action"
    
    if action == "get_attendance":
        allowed, reason = RBACManager.check_view_student_attendance(user, resource_id, db)
    elif action == "mark_attendance":
        allowed, reason = RBACManager.check_mark_student_attendance(user, resource_id, db)
    elif action == "get_attendance_analytics":
        scope = extra_params.get("scope", "school")
        allowed, reason = RBACManager.check_view_analytics(user, scope, db)
    elif action == "get_student_profile":
        allowed, reason = RBACManager.check_student_profile_access(user, resource_id, db)
    elif action == "create_escalation":
        allowed, reason = True, "Authorized: Any authenticated user can initiate escalation."
    elif action == "confirm_escalation":
        allowed, reason = RBACManager.check_escalation_confirmation(user, resource_id, db)
    elif action == "get_escalation_status":
        esc = db.query(Escalation).filter(Escalation.id == resource_id).first()
        if esc and (esc.user_id == user.id or user.role in [UserRole.PRINCIPAL.value, UserRole.TEACHER.value]):
            allowed, reason = True, "Authorized: ticket status access."
        else:
            allowed, reason = False, "Not authorized to view this ticket."
    else:
        allowed, reason = False, f"Unsupported action '{action}'."

    # Log to audit trail in database
    result_str = AuditResult.ALLOWED.value if allowed else AuditResult.DENIED.value
    log_audit_event(
        db=db,
        user_id=user.id,
        action=action,
        resource=f"{resource}:{resource_id or ''}",
        result=result_str,
        details=reason
    )
    
    if not allowed:
        raise PermissionDeniedError(detail=f"Security Policy Violation: {reason}")
    
    return True
