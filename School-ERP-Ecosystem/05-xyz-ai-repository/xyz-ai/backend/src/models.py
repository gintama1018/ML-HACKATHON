import uuid
from datetime import datetime, timezone, date
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Boolean, Text, ForeignKey,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from src.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    PRINCIPAL = "principal"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class EscalationTarget(str, Enum):
    TEACHER = "teacher"
    MANAGEMENT = "management"

class EscalationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"

class AuditResult(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"

class ChannelType(str, Enum):
    CHAT = "chat"
    VOICE = "voice"

class MessageSender(str, Enum):
    USER = "user"
    AI = "ai"
    TOOL = "tool"
    SYSTEM = "system"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, index=True)  # student, parent, teacher, principal
    password_hash = Column(String(255), nullable=False)
    language_pref = Column(String(10), default="en", nullable=False)  # en, hi, ta, bn, etc.
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parent_links = relationship("ParentStudentLink", back_populates="parent", foreign_keys="ParentStudentLink.parent_id")
    teacher_links = relationship("TeacherClassLink", back_populates="teacher", foreign_keys="TeacherClassLink.teacher_id")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    class_name = Column(String(20), nullable=False, index=True)  # e.g., "10", "9", "8"
    section = Column(String(10), nullable=False, index=True)     # e.g., "A", "B"
    roll_no = Column(String(20), nullable=False)
    emergency_contact = Column(String(20), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    parent_links = relationship("ParentStudentLink", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("class_name", "section", "roll_no", name="uq_class_section_roll"),
    )

class ParentStudentLink(Base):
    __tablename__ = "parent_student_link"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), default="parent", nullable=False)  # father, mother, guardian
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    parent = relationship("User", back_populates="parent_links", foreign_keys=[parent_id])
    student = relationship("Student", back_populates="parent_links", foreign_keys=[student_id])
    
    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),
    )

class TeacherClassLink(Base):
    __tablename__ = "teacher_class_link"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_name = Column(String(20), nullable=False, index=True)
    section = Column(String(10), nullable=False, index=True)
    subject = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="teacher_links", foreign_keys=[teacher_id])
    
    __table_args__ = (
        UniqueConstraint("teacher_id", "class_name", "section", "subject", name="uq_teacher_class_section_subject"),
    )

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # present, absent, late, excused
    marked_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    marked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    remarks = Column(Text, nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    marker = relationship("User", foreign_keys=[marked_by])
    
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_date_attendance"),
        Index("ix_attendance_student_date", "student_id", "date"),
    )

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(20), default=ChannelType.CHAT.value, nullable=False)  # chat, voice
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # user, ai, tool, system
    content = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    tool_calls_json = Column(Text, nullable=True)
    tool_call_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target = Column(String(50), nullable=False)  # teacher, management
    target_contact = Column(String(100), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default=EscalationStatus.PENDING.value, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="escalations")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)
    result = Column(String(20), nullable=False, index=True)  # allowed, denied
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
