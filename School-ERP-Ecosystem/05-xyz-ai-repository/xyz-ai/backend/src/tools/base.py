from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import date
from sqlalchemy.orm import Session
from src.models import User

class BaseSchoolERPAdapter(ABC):
    """Abstract interface for School ERP Adapter. Swappable for real ERP systems."""
    
    @abstractmethod
    def get_attendance(
        self, user: User, student_id: str, start_date: Optional[date], end_date: Optional[date], db: Session
    ) -> Dict[str, Any]:
        """Fetch attendance history for a student."""
        pass

    @abstractmethod
    def mark_attendance(
        self, user: User, student_id: str, attendance_date: date, status: str, remarks: Optional[str], db: Session
    ) -> Dict[str, Any]:
        """Mark or update attendance for a student."""
        pass

    @abstractmethod
    def get_attendance_analytics(
        self, user: User, scope: str, class_name: Optional[str], section: Optional[str], db: Session
    ) -> Dict[str, Any]:
        """Fetch school-wide or class-level aggregate attendance analytics."""
        pass

    @abstractmethod
    def get_student_profile(
        self, user: User, student_id: str, db: Session
    ) -> Dict[str, Any]:
        """Fetch student profile including class, section, roll number, and emergency contact."""
        pass

    @abstractmethod
    def create_escalation(
        self, user: User, target: str, reason: str, contact_info: Optional[str], db: Session
    ) -> Dict[str, Any]:
        """Initiate a pending escalation ticket."""
        pass

    @abstractmethod
    def confirm_escalation(
        self, user: User, escalation_id: str, notes: Optional[str], db: Session
    ) -> Dict[str, Any]:
        """Confirm an escalation and trigger dispatch."""
        pass

    @abstractmethod
    def get_escalation_status(
        self, user: User, escalation_id: str, db: Session
    ) -> Dict[str, Any]:
        """Query the real-time status of an escalation ticket."""
        pass
