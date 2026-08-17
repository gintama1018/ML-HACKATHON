import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models import (
    User, Student, ParentStudentLink, TeacherClassLink,
    Attendance, Conversation, Message, Escalation, AuditLog,
    UserRole, AttendanceStatus
)
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def test_db():
    seed_database()
    from src.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()

def test_user_roles_and_counts(test_db):
    """Verify all 4 roles exist in expected quantities in seed database."""
    users = test_db.query(User).all()
    roles = {u.role for u in users}
    
    assert UserRole.STUDENT.value in roles
    assert UserRole.PARENT.value in roles
    assert UserRole.TEACHER.value in roles
    assert UserRole.PRINCIPAL.value in roles
    
    principal_count = test_db.query(User).filter(User.role == UserRole.PRINCIPAL.value).count()
    teacher_count = test_db.query(User).filter(User.role == UserRole.TEACHER.value).count()
    student_count = test_db.query(User).filter(User.role == UserRole.STUDENT.value).count()
    parent_count = test_db.query(User).filter(User.role == UserRole.PARENT.value).count()
    
    assert principal_count == 1
    assert teacher_count == 5
    assert student_count == 25
    assert parent_count == 23

def test_parent_student_relationships(test_db):
    """Verify single and multi-child parent links are queryable."""
    # Multi-child parent: Rajesh Sharma (usr-par-01) -> Aarav Sharma (stu-101) & Ananya Sharma (stu-501)
    rajesh = test_db.query(User).filter(User.id == "usr-par-01").first()
    assert rajesh is not None
    assert len(rajesh.parent_links) == 2
    
    linked_student_ids = {link.student_id for link in rajesh.parent_links}
    assert "stu-101" in linked_student_ids
    assert "stu-501" in linked_student_ids
    
    # Query student profiles via links
    linked_students = [link.student for link in rajesh.parent_links]
    class_sections = {f"{s.class_name}-{s.section}" for s in linked_students}
    assert "10-A" in class_sections
    assert "8-A" in class_sections

def test_teacher_class_scoping(test_db):
    """Verify teachers are assigned to specific class/section and cannot access unassigned classes."""
    # Amit Verma (usr-teacher-10a) -> Class 10-A
    amit = test_db.query(User).filter(User.id == "usr-teacher-10a").first()
    assert amit is not None
    assert len(amit.teacher_links) == 1
    assert amit.teacher_links[0].class_name == "10"
    assert amit.teacher_links[0].section == "A"
    
    # Find students in teacher's assigned class
    students_in_10a = test_db.query(Student).filter(
        Student.class_name == amit.teacher_links[0].class_name,
        Student.section == amit.teacher_links[0].section
    ).all()
    assert len(students_in_10a) == 5
    
    # Find students in class 10-B (should NOT belong to Amit Verma)
    students_in_10b = test_db.query(Student).filter(
        Student.class_name == "10",
        Student.section == "B"
    ).all()
    assert len(students_in_10b) == 5
    assert set(s.id for s in students_in_10a).isdisjoint(set(s.id for s in students_in_10b))

def test_attendance_records_and_history(test_db):
    """Verify attendance history exists for all students."""
    total_attendance = test_db.query(Attendance).count()
    assert total_attendance == 25 * 30  # 25 students * 30 days = 750
    
    # Verify Aarav Sharma's attendance
    aarav_att = test_db.query(Attendance).filter(Attendance.student_id == "stu-101").all()
    assert len(aarav_att) == 30
    
    # Check statuses
    statuses = {a.status for a in aarav_att}
    assert AttendanceStatus.PRESENT.value in statuses
