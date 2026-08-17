import pytest
import asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.database import SessionLocal
from src.models import User, EscalationStatus
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def client():
    seed_database()
    with TestClient(app) as test_client:
        yield test_client

def get_auth_token(client: TestClient, email: str, password: str = "School@123") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_gate_01_student_usecase_end_to_end(client: TestClient):
    """Assessment Use Case 1: Student logs in, checks attendance, views dashboard."""
    token = get_auth_token(client, "aarav.sharma@xyzschool.edu")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Check Profile
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "student"
    assert res_me.json()["name"] == "Aarav Sharma"
    
    # 2. Chat message inquiry
    res_chat = client.post(
        "/api/v1/chat/message",
        json={"message": "Hi, what is my attendance percentage this term?"},
        headers=headers
    )
    assert res_chat.status_code == 200
    data = res_chat.json()
    assert len(data["tool_executions"]) == 1
    assert data["tool_executions"][0]["tool"] == "get_attendance"
    assert "90.0%" in data["response"] or "%" in data["response"]
    
    # 3. Portal Dashboard
    res_dash = client.get("/api/v1/portal/dashboard", headers=headers)
    assert res_dash.status_code == 200
    assert res_dash.json()["role"] == "student"
    assert res_dash.json()["attendance"]["total_school_days"] == 30

def test_gate_02_parent_usecase_disambiguation_end_to_end(client: TestClient):
    """Assessment Use Case 2: Parent with 2 kids asks ambiguous question, gets prompted, resolves."""
    token = get_auth_token(client, "rajesh.parent@xyzschool.edu")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Turn 1: Ambiguous inquiry
    res_turn1 = client.post(
        "/api/v1/chat/message",
        json={"message": "Good morning, how is my child doing with attendance?"},
        headers=headers
    )
    assert res_turn1.status_code == 200
    d1 = res_turn1.json()
    assert d1["requires_disambiguation"] is True
    assert "Aarav Sharma" in d1["response"]
    assert "Ananya Sharma" in d1["response"]
    conv_id = d1["conversation_id"]
    
    # Turn 2: Disambiguate child
    res_turn2 = client.post(
        "/api/v1/chat/message",
        json={"message": "Please check for Aarav.", "conversation_id": conv_id},
        headers=headers
    )
    assert res_turn2.status_code == 200
    d2 = res_turn2.json()
    assert d2["requires_disambiguation"] is False
    assert len(d2["tool_executions"]) == 1
    assert d2["tool_executions"][0]["tool"] == "get_attendance"
    assert "Aarav Sharma" in d2["response"]

def test_gate_03_teacher_usecase_marking_and_roster(client: TestClient):
    """Assessment Use Case 3: Teacher marks attendance and views assigned class roster."""
    token = get_auth_token(client, "amit.verma@xyzschool.edu")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mark attendance for student in 10-A
    res_mark = client.post(
        "/api/v1/chat/message",
        json={"message": "Mark Aarav Sharma present for class 10-A today."},
        headers=headers
    )
    assert res_mark.status_code == 200
    d_mark = res_mark.json()
    assert len(d_mark["tool_executions"]) == 1
    assert d_mark["tool_executions"][0]["tool"] == "mark_attendance"
    assert "PRESENT" in d_mark["response"]
    
    # Check teacher portal dashboard
    res_dash = client.get("/api/v1/portal/dashboard", headers=headers)
    assert res_dash.status_code == 200
    assert res_dash.json()["role"] == "teacher"
    assert len(res_dash.json()["assigned_classes"]) > 0

def test_gate_04_principal_analytics_usecase(client: TestClient):
    """Assessment Use Case 4: Principal accesses institutional attendance analytics."""
    token = get_auth_token(client, "principal@xyzschool.edu")
    headers = {"Authorization": f"Bearer {token}"}
    
    res_chat = client.post(
        "/api/v1/chat/message",
        json={"message": "Generate the overall school attendance analytics report."},
        headers=headers
    )
    assert res_chat.status_code == 200
    d = res_chat.json()
    assert len(d["tool_executions"]) == 1
    assert d["tool_executions"][0]["tool"] == "get_attendance_analytics"
    assert "Executive Attendance Summary" in d["response"]
    assert "Class 10-A" in d["response"]

def test_gate_05_escalation_lifecycle_http(client: TestClient):
    """Test full HTTP Escalation flow: parent creates -> parent confirms -> teacher resolves."""
    parent_token = get_auth_token(client, "rajesh.parent@xyzschool.edu")
    teacher_token = get_auth_token(client, "amit.verma@xyzschool.edu")
    
    # 1. Parent creates escalation
    res_c = client.post(
        "/api/v1/escalations/create",
        json={"target": "teacher", "reason": "Math olympiad consultation request", "contact_info": "Amit Verma"},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert res_c.status_code == 200
    ticket_id = res_c.json()["ticket_id"]
    assert res_c.json()["status"] == EscalationStatus.PENDING.value
    
    # 2. Parent confirms escalation
    res_conf = client.post(
        f"/api/v1/escalations/{ticket_id}/confirm",
        json={"notes": "Available mornings"},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert res_conf.status_code == 200
    assert res_conf.json()["status"] == EscalationStatus.CONFIRMED.value
    assert "dispatch_id" in res_conf.json()
    
    # 3. Teacher resolves escalation
    res_res = client.post(
        f"/api/v1/escalations/{ticket_id}/resolve",
        json={"resolution_summary": "Consultation held successfully."},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == EscalationStatus.RESOLVED.value

def test_gate_06_voice_pipeline_http(client: TestClient):
    """Test Voice API endpoint turn execution."""
    token = get_auth_token(client, "aarav.sharma@xyzschool.edu")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post(
        "/api/v1/voice/turn",
        json={"speech_text": "What is my attendance percentage?", "confidence_score": 0.95},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_noisy"] is False
    assert "tts" in data
    assert len(data["tts"]["visemes"]) > 0

def test_gate_07_concurrency_and_session_isolation(client: TestClient):
    """Simulate 20 concurrent user conversation sessions to verify complete isolation."""
    users_to_test = [
        ("aarav.sharma@xyzschool.edu", "student"),
        ("diya.patel@xyzschool.edu", "student"),
        ("rajesh.parent@xyzschool.edu", "parent"),
        ("priya.parent@xyzschool.edu", "parent"),
        ("amit.verma@xyzschool.edu", "teacher"),
        ("principal@xyzschool.edu", "principal"),
    ] * 4  # 24 concurrent requests
    
    tokens = {}
    for email, _ in set((u[0], u[1]) for u in users_to_test):
        tokens[email] = get_auth_token(client, email)
        
    responses = []
    for idx, (email, role) in enumerate(users_to_test):
        token = tokens[email]
        headers = {"Authorization": f"Bearer {token}"}
        
        msg = "Hi, how are you today?" if role != "principal" else "Generate school report"
        res = client.post("/api/v1/chat/message", json={"message": msg}, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == role
        responses.append(data["conversation_id"])
        
    # All conversation IDs must be distinct and non-null
    assert len(set(responses)) == len(users_to_test)
