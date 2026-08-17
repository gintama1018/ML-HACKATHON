from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.tools.base import BaseSchoolERPAdapter
from src.models import (
    User, Student, Attendance, Escalation, ParentStudentLink, TeacherClassLink,
    AttendanceStatus, EscalationStatus, EscalationTarget, UserRole
)
from src.auth.rbac import enforce_permission

class MockSchoolERPAdapter(BaseSchoolERPAdapter):
    """
    Mock School ERP Adapter providing live SQL database backed school operations.
    Data is mocked/seeded; business logic, permission checks, and state machines are 100% real.
    """
    
    def get_attendance(
        self, user: User, student_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = None
    ) -> Dict[str, Any]:
        enforce_permission(user, "get_attendance", "attendance", student_id, db)
        
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"status": "error", "message": f"Student with ID '{student_id}' not found."}
            
        query = db.query(Attendance).filter(Attendance.student_id == student_id)
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
            
        records = query.order_by(Attendance.date.desc()).all()
        total_days = len(records)
        present_count = sum(1 for r in records if r.status == AttendanceStatus.PRESENT.value)
        absent_count = sum(1 for r in records if r.status == AttendanceStatus.ABSENT.value)
        late_count = sum(1 for r in records if r.status == AttendanceStatus.LATE.value)
        excused_count = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED.value)
        
        percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0.0
        
        return {
            "status": "success",
            "student_id": student.id,
            "student_name": student.user.name if student.user else "Unknown",
            "class_name": student.class_name,
            "section": student.section,
            "roll_no": student.roll_no,
            "summary": {
                "total_school_days": total_days,
                "present_days": present_count,
                "absent_days": absent_count,
                "late_days": late_count,
                "excused_days": excused_count,
                "attendance_percentage": percentage
            },
            "recent_records": [
                {
                    "date": r.date.isoformat(),
                    "status": r.status,
                    "remarks": r.remarks
                }
                for r in records[:10]  # Return last 10 days for concise context
            ]
        }

    def mark_attendance(
        self, user: User, student_id: str, attendance_date: date, status: str, remarks: Optional[str] = None, db: Session = None
    ) -> Dict[str, Any]:
        enforce_permission(user, "mark_attendance", "attendance", student_id, db)
        
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"status": "error", "message": f"Student with ID '{student_id}' not found."}
            
        status_clean = status.strip().lower()
        valid_statuses = [e.value for e in AttendanceStatus]
        if status_clean not in valid_statuses:
            return {"status": "error", "message": f"Invalid status '{status}'. Valid options: {valid_statuses}"}
            
        # Check if record already exists for this date
        att_record = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.date == attendance_date
        ).first()
        
        if att_record:
            att_record.status = status_clean
            att_record.marked_by = user.id
            att_record.marked_at = datetime.now(timezone.utc)
            att_record.remarks = remarks or att_record.remarks
        else:
            att_record = Attendance(
                id=f"att-{student_id}-{attendance_date.isoformat()}",
                student_id=student_id,
                date=attendance_date,
                status=status_clean,
                marked_by=user.id,
                marked_at=datetime.now(timezone.utc),
                remarks=remarks or f"Marked by Teacher {user.name}"
            )
            db.add(att_record)
            
        db.commit()
        db.refresh(att_record)
        
        return {
            "status": "success",
            "message": f"Attendance successfully marked as '{status_clean}' for student {student.user.name if student.user else student_id} on {attendance_date.isoformat()}.",
            "record": {
                "attendance_id": att_record.id,
                "student_id": student.id,
                "student_name": student.user.name if student.user else "",
                "class_section": f"{student.class_name}-{student.section}",
                "date": att_record.date.isoformat(),
                "status": att_record.status,
                "marked_by": user.name,
                "marked_at": att_record.marked_at.isoformat()
            }
        }

    def get_attendance_analytics(
        self, user: User, scope: str = "school", class_name: Optional[str] = None, section: Optional[str] = None, db: Session = None
    ) -> Dict[str, Any]:
        extra_scope = f"class_{class_name}-{section}" if class_name and section else scope
        enforce_permission(user, "get_attendance_analytics", "analytics", None, db, {"scope": extra_scope})
        
        if class_name and section:
            # Class-level analytics
            students = db.query(Student).filter(
                Student.class_name == class_name,
                Student.section == section
            ).all()
            
            student_stats = []
            class_total_present = 0
            class_total_records = 0
            
            for s in students:
                records = db.query(Attendance).filter(Attendance.student_id == s.id).all()
                tot = len(records)
                pres = sum(1 for r in records if r.status == AttendanceStatus.PRESENT.value)
                abs_cnt = sum(1 for r in records if r.status == AttendanceStatus.ABSENT.value)
                pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
                class_total_present += pres
                class_total_records += tot
                
                student_stats.append({
                    "student_id": s.id,
                    "name": s.user.name if s.user else "Unknown",
                    "roll_no": s.roll_no,
                    "attendance_percentage": pct,
                    "total_absences": abs_cnt,
                    "needs_attention": pct < 85.0
                })
                
            class_avg = round((class_total_present / class_total_records * 100), 1) if class_total_records > 0 else 0.0
            
            return {
                "status": "success",
                "scope": f"Class {class_name}-{section}",
                "total_students": len(students),
                "average_attendance_percentage": class_avg,
                "students_below_threshold": [s for s in student_stats if s["needs_attention"]],
                "class_roster_summary": student_stats
            }
        else:
            # School-wide analytics (Principal scope)
            all_students = db.query(Student).all()
            all_records = db.query(Attendance).all()
            
            total_students = len(all_students)
            total_records = len(all_records)
            total_present = sum(1 for r in all_records if r.status == AttendanceStatus.PRESENT.value)
            total_absent = sum(1 for r in all_records if r.status == AttendanceStatus.ABSENT.value)
            
            school_avg = round((total_present / total_records * 100), 1) if total_records > 0 else 0.0
            
            # Breakdown by class
            classes = [("10", "A"), ("10", "B"), ("9", "A"), ("9", "B"), ("8", "A")]
            class_breakdowns = []
            
            for c_name, sec in classes:
                c_students = [s for s in all_students if s.class_name == c_name and s.section == sec]
                c_s_ids = {s.id for s in c_students}
                c_recs = [r for r in all_records if r.student_id in c_s_ids]
                c_pres = sum(1 for r in c_recs if r.status == AttendanceStatus.PRESENT.value)
                c_pct = round((c_pres / len(c_recs) * 100), 1) if c_recs else 0.0
                
                class_breakdowns.append({
                    "class_name": c_name,
                    "section": sec,
                    "student_count": len(c_students),
                    "attendance_percentage": c_pct
                })
                
            return {
                "status": "success",
                "scope": "school_wide",
                "total_enrolled_students": total_students,
                "total_attendance_records": total_records,
                "school_average_attendance": school_avg,
                "total_absences_logged": total_absent,
                "class_wise_breakdown": class_breakdowns
            }

    def get_student_profile(
        self, user: User, student_id: str, db: Session = None
    ) -> Dict[str, Any]:
        enforce_permission(user, "get_student_profile", "student_profile", student_id, db)
        
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"status": "error", "message": f"Student with ID '{student_id}' not found."}
            
        parents = db.query(ParentStudentLink).filter(ParentStudentLink.student_id == student_id).all()
        parent_info = [
            {
                "parent_name": p.parent.name if p.parent else "Unknown",
                "phone": p.parent.phone if p.parent else "",
                "relationship": p.relationship_type
            }
            for p in parents
        ]
        
        return {
            "status": "success",
            "student_id": student.id,
            "name": student.user.name if student.user else "Unknown",
            "email": student.user.email if student.user else "",
            "class": student.class_name,
            "section": student.section,
            "roll_no": student.roll_no,
            "emergency_contact": student.emergency_contact,
            "parents": parent_info
        }

    def create_escalation(
        self, user: User, target: str, reason: str, contact_info: Optional[str] = None, db: Session = None
    ) -> Dict[str, Any]:
        enforce_permission(user, "create_escalation", "escalation", None, db)
        
        target_clean = target.strip().lower()
        if target_clean not in ["teacher", "management"]:
            return {"status": "error", "message": "Target must be 'teacher' or 'management'."}
            
        escalation = Escalation(
            user_id=user.id,
            target=target_clean,
            target_contact=contact_info or ("Assigned Class Teacher" if target_clean == "teacher" else "Principal Office"),
            reason=reason,
            status=EscalationStatus.PENDING.value,
            notes="Pending user confirmation."
        )
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        
        return {
            "status": "pending_confirmation",
            "escalation_id": escalation.id,
            "target": escalation.target,
            "target_contact": escalation.target_contact,
            "reason": escalation.reason,
            "ticket_status": escalation.status,
            "requires_confirmation": True,
            "confirmation_prompt": f"I have prepared an escalation request to {escalation.target} ({escalation.target_contact}) for reason: '{reason}'. Would you like me to confirm and submit this request?"
        }

    def confirm_escalation(
        self, user: User, escalation_id: str, notes: Optional[str] = None, db: Session = None
    ) -> Dict[str, Any]:
        enforce_permission(user, "confirm_escalation", "escalation", escalation_id, db)
        
        esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            return {"status": "error", "message": f"Escalation ticket '{escalation_id}' not found."}
            
        if esc.status == EscalationStatus.CONFIRMED.value:
            return {
                "status": "already_confirmed",
                "escalation_id": esc.id,
                "ticket_status": esc.status,
                "confirmed_at": esc.confirmed_at.isoformat() if esc.confirmed_at else "",
                "message": "This escalation ticket has already been confirmed and notified."
            }
            
        esc.status = EscalationStatus.CONFIRMED.value
        esc.confirmed_at = datetime.now(timezone.utc)
        esc.notes = (esc.notes or "") + f"\nConfirmed by {user.name} at {esc.confirmed_at.isoformat()}. Notes: {notes or 'None'}"
        db.commit()
        db.refresh(esc)
        
        # Real mock notification dispatch (simulating SMS/Email/Webhook dispatch log)
        notification_dispatch_id = f"notif-dispatch-{esc.id[:8]}"
        
        return {
            "status": "success",
            "escalation_id": esc.id,
            "ticket_status": esc.status,
            "target": esc.target,
            "target_contact": esc.target_contact,
            "confirmed_at": esc.confirmed_at.isoformat(),
            "notification_dispatch_id": notification_dispatch_id,
            "message": f"Your escalation request #{esc.id[:8]} has been officially confirmed and dispatched to {esc.target}."
        }

    def get_escalation_status(
        self, user: User, escalation_id: str, db: Session = None
    ) -> Dict[str, Any]:
        enforce_permission(user, "get_escalation_status", "escalation", escalation_id, db)
        
        esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            return {"status": "error", "message": f"Escalation ticket '{escalation_id}' not found."}
            
        return {
            "status": "success",
            "escalation_id": esc.id,
            "ticket_status": esc.status,
            "target": esc.target,
            "target_contact": esc.target_contact,
            "reason": esc.reason,
            "created_at": esc.created_at.isoformat(),
            "confirmed_at": esc.confirmed_at.isoformat() if esc.confirmed_at else None,
            "resolved_at": esc.resolved_at.isoformat() if esc.resolved_at else None
        }

erp_adapter = MockSchoolERPAdapter()
