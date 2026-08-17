from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from src.models import User, Student, ParentStudentLink, TeacherClassLink, UserRole

class DisambiguationEngine:
    """Detects ambiguity or missing parameters in parent, teacher, and student inquiries."""
    
    @staticmethod
    def check_parent_child_ambiguity(
        user: User, user_message: str, db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if parent is asking about a child without specifying which one.
        Returns: (is_ambiguous, target_student_id, disambiguation_prompt)
        """
        if user.role != UserRole.PARENT.value:
            return False, None, None
            
        links = db.query(ParentStudentLink).filter(ParentStudentLink.parent_id == user.id).all()
        if not links:
            return False, None, None
            
        # Single child -> No ambiguity, automatically resolve to this student
        if len(links) == 1:
            return False, links[0].student_id, None
            
        msg_lower = user_message.lower()
        
        # Check if message mentions any child's name or class
        matched_students = []
        for l in links:
            s_name = (l.student.user.name if l.student and l.student.user else "").lower()
            first_name = s_name.split()[0] if s_name else ""
            roll_str = f"roll {l.student.roll_no}" if l.student else ""
            class_str = f"{l.student.class_name}-{l.student.section}".lower() if l.student else ""
            
            if (first_name and first_name in msg_lower) or (roll_str and roll_str in msg_lower) or (class_str and class_str in msg_lower):
                matched_students.append(l.student_id)
                
        if len(matched_students) == 1:
            return False, matched_students[0], None
            
        # If user is asking an attendance/profile inquiry and multiple children exist
        keywords = ["attendance", "present", "absent", "status", "profile", "record", "how is", "classes", "report"]
        is_inquiry = any(k in msg_lower for k in keywords)
        
        if is_inquiry:
            children_names = [f"{l.student.user.name} (Class {l.student.class_name}-{l.student.section})" for l in links if l.student and l.student.user]
            prompt = (
                f"You have {len(links)} children registered with XYZ School: {', '.join(children_names)}. "
                "Which child would you like me to look up?"
            )
            return True, None, prompt
            
        return False, None, None

    @staticmethod
    def resolve_student_id_from_context(
        user: User, user_message: str, conversation_id: str, db: Session
    ) -> Optional[str]:
        """Attempt to extract student_id from user's current or immediate prior context."""
        if user.role == UserRole.STUDENT.value:
            return user.student_profile.id if user.student_profile else None
            
        if user.role == UserRole.PARENT.value:
            links = db.query(ParentStudentLink).filter(ParentStudentLink.parent_id == user.id).all()
            if len(links) == 1:
                return links[0].student_id
                
            # Check message for child name
            msg_lower = user_message.lower()
            for l in links:
                if l.student and l.student.user:
                    first_name = l.student.user.name.lower().split()[0]
                    if first_name in msg_lower or l.student_id.lower() in msg_lower:
                        return l.student_id
                        
        return None
