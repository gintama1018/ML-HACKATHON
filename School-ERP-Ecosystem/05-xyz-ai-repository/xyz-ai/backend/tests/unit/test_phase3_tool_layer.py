import pytest
from datetime import date
from src.database import SessionLocal
from src.models import User, Student, Attendance, Escalation, EscalationStatus
from src.tools.tool_registry import execute_tool, get_tools_schema_for_role
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    seed_database()
    session = SessionLocal()
    yield session
    session.close()

def test_tool_schemas_and_roles():
    """Verify tool schemas are properly registered and role-filtered."""
    student_tools = get_tools_schema_for_role("student")
    tool_names_student = [t["function"]["name"] for t in student_tools]
    assert "get_attendance" in tool_names_student
    assert "mark_attendance" not in tool_names_student
    assert "get_attendance_analytics" not in tool_names_student
    
    teacher_tools = get_tools_schema_for_role("teacher")
    tool_names_teacher = [t["function"]["name"] for t in teacher_tools]
    assert "mark_attendance" in tool_names_teacher
    assert "get_attendance" in tool_names_teacher
    
    principal_tools = get_tools_schema_for_role("principal")
    tool_names_principal = [t["function"]["name"] for t in principal_tools]
    assert "get_attendance_analytics" in tool_names_principal
    assert "mark_attendance" not in tool_names_principal

def test_tool_get_attendance_student_and_parent(db):
    """Test get_attendance tool execution for authorized student and parent."""
    # Student Aarav Sharma (usr-stu-101)
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    res = execute_tool(student, "get_attendance", {"student_id": "stu-101"}, db)
    assert res["status"] == "success"
    assert res["student_id"] == "stu-101"
    assert res["summary"]["total_school_days"] == 30
    assert res["summary"]["attendance_percentage"] > 0
    assert len(res["recent_records"]) > 0
    
    # Parent Rajesh Sharma (usr-par-01) for child stu-101 and stu-501
    parent = db.query(User).filter(User.id == "usr-par-01").first()
    res_p1 = execute_tool(parent, "get_attendance", {"student_id": "stu-101"}, db)
    assert res_p1["status"] == "success"
    res_p2 = execute_tool(parent, "get_attendance", {"student_id": "stu-501"}, db)
    assert res_p2["status"] == "success"
    
    # Parent attempts unauthorized access to unlinked student (stu-103)
    res_unauth = execute_tool(parent, "get_attendance", {"student_id": "stu-103"}, db)
    assert res_unauth["status"] == "error"
    assert "Permission" in res_unauth.get("error_type", "") or "403" in res_unauth.get("message", "")

def test_tool_mark_attendance_teacher(db):
    """Test mark_attendance tool execution for teacher on assigned vs unassigned class."""
    # Amit Verma (usr-teacher-10a) teaches 10-A
    teacher = db.query(User).filter(User.id == "usr-teacher-10a").first()
    
    # Mark attendance for 10-A student (stu-101) on today's date
    today_str = date.today().isoformat()
    res = execute_tool(teacher, "mark_attendance", {
        "student_id": "stu-101",
        "attendance_date": today_str,
        "status": "present",
        "remarks": "On-time arrival in morning assembly"
    }, db)
    
    assert res["status"] == "success"
    assert res["record"]["status"] == "present"
    
    # Verify in DB
    att_db = db.query(Attendance).filter(
        Attendance.student_id == "stu-101",
        Attendance.date == date.today()
    ).first()
    assert att_db is not None
    assert att_db.status == "present"
    
    # Attempt to mark attendance for 10-B student (stu-201) -> Denied
    res_unauth = execute_tool(teacher, "mark_attendance", {
        "student_id": "stu-201",
        "attendance_date": today_str,
        "status": "absent"
    }, db)
    assert res_unauth["status"] == "error"

def test_tool_attendance_analytics(db):
    """Test get_attendance_analytics tool for Principal and Teacher."""
    # Principal full school overview
    principal = db.query(User).filter(User.id == "usr-principal-01").first()
    res = execute_tool(principal, "get_attendance_analytics", {"scope": "school"}, db)
    assert res["status"] == "success"
    assert res["total_enrolled_students"] == 25
    assert len(res["class_wise_breakdown"]) == 5
    assert res["school_average_attendance"] > 0
    
    # Teacher class analytics
    teacher = db.query(User).filter(User.id == "usr-teacher-10a").first()
    res_t = execute_tool(teacher, "get_attendance_analytics", {
        "scope": "class",
        "class_name": "10",
        "section": "A"
    }, db)
    assert res_t["status"] == "success"
    assert res_t["total_students"] == 5
    assert len(res_t["class_roster_summary"]) == 5

def test_tool_escalation_lifecycle(db):
    """Test create_escalation -> confirm_escalation state transition."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    # Step 1: Create escalation (Pending)
    res_create = execute_tool(student, "create_escalation", {
        "target": "teacher",
        "reason": "Need guidance regarding advanced calculus assignment"
    }, db)
    
    assert res_create["status"] == "pending_confirmation"
    assert res_create["requires_confirmation"] is True
    assert "escalation_id" in res_create
    esc_id = res_create["escalation_id"]
    
    # Verify DB state is pending
    esc_db = db.query(Escalation).filter(Escalation.id == esc_id).first()
    assert esc_db.status == EscalationStatus.PENDING.value
    assert esc_db.confirmed_at is None
    
    # Step 2: Confirm escalation
    res_confirm = execute_tool(student, "confirm_escalation", {
        "escalation_id": esc_id,
        "notes": "Available tomorrow between 3 PM and 4 PM"
    }, db)
    
    assert res_confirm["status"] == "success"
    assert res_confirm["ticket_status"] == EscalationStatus.CONFIRMED.value
    assert "notification_dispatch_id" in res_confirm
    
    # Verify DB state is confirmed
    db.refresh(esc_db)
    assert esc_db.status == EscalationStatus.CONFIRMED.value
    assert esc_db.confirmed_at is not None
    
    # Step 3: Check status
    res_status = execute_tool(student, "get_escalation_status", {"escalation_id": esc_id}, db)
    assert res_status["status"] == "success"
    assert res_status["ticket_status"] == EscalationStatus.CONFIRMED.value
