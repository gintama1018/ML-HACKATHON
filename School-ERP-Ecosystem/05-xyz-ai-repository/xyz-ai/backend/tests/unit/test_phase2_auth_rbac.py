import pytest
from datetime import timedelta
import jwt
from fastapi import HTTPException
from src.database import SessionLocal
from src.models import User, Student, ParentStudentLink, TeacherClassLink, AuditLog, AuditResult
from src.auth.jwt_handler import create_access_token, decode_access_token
from src.auth.auth_service import login_user, authenticate_user
from src.auth.rbac import enforce_permission, PermissionDeniedError
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    seed_database()
    session = SessionLocal()
    yield session
    session.close()

def test_user_authentication_success(db):
    """Test login with valid seed credentials."""
    # Principal login
    res = login_user(db, "principal@xyzschool.edu", "School@123")
    assert "access_token" in res
    assert res["user"]["role"] == "principal"
    assert res["user"]["name"] == "Dr. Sunita Sharma"

    # Teacher login
    res_t = login_user(db, "amit.verma@xyzschool.edu", "School@123")
    assert res_t["user"]["role"] == "teacher"
    assert len(res_t["user"]["assigned_classes"]) > 0

    # Parent login
    res_p = login_user(db, "rajesh.parent@xyzschool.edu", "School@123")
    assert res_p["user"]["role"] == "parent"
    assert len(res_p["user"]["linked_students"]) == 2

def test_user_authentication_invalid_password(db):
    """Test login fails with incorrect password."""
    with pytest.raises(HTTPException) as exc_info:
        login_user(db, "principal@xyzschool.edu", "WrongPassword@123")
    assert exc_info.value.status_code == 401

def test_jwt_tampering_and_expiration():
    """Test JWT tamper protection and expiration."""
    valid_token = create_access_token({"sub": "usr-123", "role": "student"})
    payload = decode_access_token(valid_token)
    assert payload["sub"] == "usr-123"
    
    # Tampered token
    tampered_token = valid_token[:-4] + "abcd"
    with pytest.raises(HTTPException) as exc_tamper:
        decode_access_token(tampered_token)
    assert exc_tamper.value.status_code == 401
    
    # Expired token
    expired_token = create_access_token({"sub": "usr-123", "role": "student"}, expires_delta=timedelta(seconds=-10))
    with pytest.raises(HTTPException) as exc_expire:
        decode_access_token(expired_token)
    assert exc_expire.value.status_code == 401

def test_student_rbac_boundaries(db):
    """Test Student role permissions and boundaries."""
    # Aarav Sharma (stu-101)
    student_user = db.query(User).filter(User.id == "usr-stu-101").first()
    assert student_user.role == "student"
    
    # 1. Allowed: View own attendance
    assert enforce_permission(student_user, "get_attendance", "attendance", "stu-101", db) is True
    
    # 2. Denied: Student attempting to view Diya Patel's attendance (stu-102)
    with pytest.raises(PermissionDeniedError):
        enforce_permission(student_user, "get_attendance", "attendance", "stu-102", db)
        
    # 3. Denied: Student attempting to mark attendance
    with pytest.raises(PermissionDeniedError):
        enforce_permission(student_user, "mark_attendance", "attendance", "stu-101", db)
        
    # 4. Denied: Student attempting to view aggregate analytics
    with pytest.raises(PermissionDeniedError):
        enforce_permission(student_user, "get_attendance_analytics", "analytics", None, db)

def test_parent_rbac_boundaries(db):
    """Test Parent role permissions and boundaries."""
    # Rajesh Sharma (usr-par-01) is parent of stu-101 and stu-501
    parent_user = db.query(User).filter(User.id == "usr-par-01").first()
    assert parent_user.role == "parent"
    
    # 1. Allowed: View linked child stu-101
    assert enforce_permission(parent_user, "get_attendance", "attendance", "stu-101", db) is True
    
    # 2. Allowed: View linked child stu-501
    assert enforce_permission(parent_user, "get_attendance", "attendance", "stu-501", db) is True
    
    # 3. Denied: View unlinked student stu-103 (Rohan Mehta)
    with pytest.raises(PermissionDeniedError):
        enforce_permission(parent_user, "get_attendance", "attendance", "stu-103", db)
        
    # 4. Denied: Parent attempting to mark attendance
    with pytest.raises(PermissionDeniedError):
        enforce_permission(parent_user, "mark_attendance", "attendance", "stu-101", db)

def test_teacher_rbac_boundaries(db):
    """Test Teacher role class-scoped permissions."""
    # Amit Verma (usr-teacher-10a) teaches 10-A
    teacher_user = db.query(User).filter(User.id == "usr-teacher-10a").first()
    assert teacher_user.role == "teacher"
    
    # 1. Allowed: View student in 10-A (stu-101)
    assert enforce_permission(teacher_user, "get_attendance", "attendance", "stu-101", db) is True
    
    # 2. Allowed: Mark attendance for student in 10-A (stu-101)
    assert enforce_permission(teacher_user, "mark_attendance", "attendance", "stu-101", db) is True
    
    # 3. Denied: Mark attendance for student in 10-B (stu-201, Ishaan Verma)
    with pytest.raises(PermissionDeniedError):
        enforce_permission(teacher_user, "mark_attendance", "attendance", "stu-201", db)
        
    # 4. Denied: View analytics for unassigned class / school-wide
    with pytest.raises(PermissionDeniedError):
        enforce_permission(teacher_user, "get_attendance_analytics", "analytics", None, db, {"scope": "school"})

def test_principal_rbac_boundaries(db):
    """Test Principal role institutional permissions."""
    principal_user = db.query(User).filter(User.id == "usr-principal-01").first()
    assert principal_user.role == "principal"
    
    # 1. Allowed: View school analytics
    assert enforce_permission(principal_user, "get_attendance_analytics", "analytics", None, db, {"scope": "school"}) is True
    
    # 2. Allowed: View any student profile / attendance
    assert enforce_permission(principal_user, "get_attendance", "attendance", "stu-101", db) is True
    assert enforce_permission(principal_user, "get_attendance", "attendance", "stu-401", db) is True
    
    # 3. Denied: Principal cannot directly tamper/mark individual student attendance
    with pytest.raises(PermissionDeniedError):
        enforce_permission(principal_user, "mark_attendance", "attendance", "stu-101", db)

def test_audit_logging_of_denials(db):
    """Verify that every authorization attempt (especially denials) generates an audit record in the database."""
    initial_denial_count = db.query(AuditLog).filter(AuditLog.result == AuditResult.DENIED.value).count()
    
    # Simulate unauthorized student action
    student_user = db.query(User).filter(User.id == "usr-stu-101").first()
    try:
        enforce_permission(student_user, "mark_attendance", "attendance", "stu-101", db)
    except PermissionDeniedError:
        pass
        
    new_denial_count = db.query(AuditLog).filter(AuditLog.result == AuditResult.DENIED.value).count()
    assert new_denial_count == initial_denial_count + 1
    
    # Check latest audit record
    latest = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
    assert latest.result == AuditResult.DENIED.value
    assert latest.user_id == student_user.id
    assert latest.action == "mark_attendance"

def test_bcrypt_per_user_salt_produces_unique_hashes():
    """Prove bcrypt uses per-user salt: same password → different hashes."""
    from src.auth.auth_service import hash_password, verify_password
    h1 = hash_password("School@123")
    h2 = hash_password("School@123")
    assert h1 != h2, "bcrypt hashes for the same password should differ (per-user salt)"
    assert verify_password("School@123", h1)
    assert verify_password("School@123", h2)

def test_principal_self_registration_rejected(client):
    """Principal role must not be self-registerable via the public /register endpoint."""
    resp = client.post("/api/v1/auth/register", json={
        "name": "Fake Principal",
        "email": "fake.principal@test.com",
        "password": "School@123",
        "role": "principal"
    })
    assert resp.status_code == 403

def test_student_self_registration_succeeds(client):
    """Students can self-register and immediately receive a valid JWT."""
    resp = client.post("/api/v1/auth/register", json={
        "name": "New Student Test",
        "email": "new.student.test@xyzschool.edu",
        "password": "School@123",
        "role": "student",
        "class_name": "10",
        "section": "C",
        "roll_no": "999"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "student"
    assert data["user"]["class_name"] == "10"

def test_teacher_self_registration_is_unverified(client):
    """Self-registered teachers start with is_verified=False."""
    resp = client.post("/api/v1/auth/register", json={
        "name": "New Teacher Test",
        "email": "new.teacher.test@xyzschool.edu",
        "password": "School@123",
        "role": "teacher"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["is_verified"] == False
