from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from src.models import User, Student, ParentStudentLink, TeacherClassLink, UserRole
from src.i18n.translator import multilingual_service

class DisambiguationEngine:
    """Detects ambiguity or missing parameters in parent, teacher, and student inquiries."""
    
    @staticmethod
    def check_parent_child_ambiguity(
        user: User, user_message: str, lang: str, db: Session
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
        
        # Check if message mentions any child's name, roll or class
        matched_students = []
        for l in links:
            s_name = (l.student.user.name if l.student and l.student.user else "").lower()
            first_name = s_name.split()[0] if s_name else ""
            roll_str = f"{l.student.roll_no}" if l.student else ""
            
            if (first_name and first_name in msg_lower) or (roll_str and f"roll {roll_str}" in msg_lower or f"#{roll_str}" in msg_lower):
                matched_students.append(l.student_id)
                
        if len(matched_students) == 1:
            return False, matched_students[0], None
            
        # If user is asking an attendance/profile inquiry and multiple children exist
        inquiry_keywords = [
            "attendance", "present", "absent", "status", "profile", "record", "how is", "classes", "report", "child", "kid",
            "उपस्थिति", "हाजिरी", "बच्चे", "வருகை", "பிள்ளை", "উপস্থিতি"
        ]
        is_inquiry = any(k in msg_lower or k in user_message for k in inquiry_keywords)
        
        if is_inquiry:
            children_names = [f"{l.student.user.name} (Class {l.student.class_name}-{l.student.section})" for l in links if l.student and l.student.user]
            prompt = multilingual_service.get_phrase(
                "disambiguation_parent",
                lang=lang,
                count=len(links),
                children=", ".join(children_names)
            )
            return True, None, prompt
            
        return False, None, None

    @staticmethod
    def check_teacher_marking_ambiguity(
        user: User, user_message: str, lang: str, db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if teacher is trying to mark attendance without providing a student name/ID.
        Returns: (is_ambiguous, detected_status, disambiguation_prompt)
        """
        if user.role != UserRole.TEACHER.value:
            return False, None, None
            
        msg_lower = user_message.lower()
        mark_keywords = ["mark", "record", "set", "mark attendance", "दर्ज", "பதிவு", "চিহ্নিত"]
        has_mark_intent = any(k in msg_lower or k in user_message for k in mark_keywords)
        
        if not has_mark_intent:
            return False, None, None
            
        # Detect requested status
        status_to_mark = "present"
        if "absent" in msg_lower or "अनुपस्थित" in user_message:
            status_to_mark = "absent"
        elif "late" in msg_lower or "विलंब" in user_message:
            status_to_mark = "late"
        elif "excused" in msg_lower:
            status_to_mark = "excused"
            
        # Check if student name or roll number is mentioned in the teacher's assigned classes
        classes = db.query(TeacherClassLink).filter(TeacherClassLink.teacher_id == user.id).all()
        if not classes:
            return False, None, None
            
        cls = classes[0]
        students = db.query(Student).filter(
            Student.class_name == cls.class_name,
            Student.section == cls.section
        ).all()
        
        matched_student = None
        for s in students:
            s_name = (s.user.name if s.user else "").lower()
            first_name = s_name.split()[0] if s_name else ""
            if (first_name and first_name in msg_lower) or (f"#{s.roll_no}" in msg_lower or f"roll {s.roll_no}" in msg_lower or f"{s.roll_no}" == msg_lower.strip()):
                matched_student = s.id
                break
                
        if matched_student:
            return False, status_to_mark, None
            
        # If no student is matched, prompt for missing student info
        prompt = multilingual_service.get_phrase(
            "disambiguation_teacher",
            lang=lang,
            class_name=cls.class_name,
            section=cls.section,
            status=status_to_mark
        )
        return True, status_to_mark, prompt
