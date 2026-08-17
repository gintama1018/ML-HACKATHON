import pytest
from src.database import SessionLocal
from src.models import User, Conversation, Message, Escalation, EscalationStatus
from src.conversation_engine.engine import conversation_engine
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    seed_database()
    session = SessionLocal()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_student_attendance_conversation_flow(db):
    """Test Student conversational attendance inquiry."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    res = await conversation_engine.process_message(
        user=student,
        user_message="Hi! Can you please tell me what my current attendance percentage is?",
        channel="chat",
        db=db
    )
    
    assert res["requires_disambiguation"] is False
    assert len(res["tool_executions"]) == 1
    assert res["tool_executions"][0]["tool"] == "get_attendance"
    assert "90.0%" in res["response"] or "%" in res["response"]
    assert "Aarav" in res["response"]

@pytest.mark.asyncio
async def test_parent_multi_child_disambiguation_flow(db):
    """Test Parent with 2 children triggers disambiguation, then follow-up turn succeeds."""
    # Rajesh Sharma has 2 kids: Aarav (10-A) and Ananya (8-A)
    parent = db.query(User).filter(User.id == "usr-par-01").first()
    
    # Turn 1: Ambiguous inquiry
    res_turn1 = await conversation_engine.process_message(
        user=parent,
        user_message="Hello, I want to check my child's attendance record.",
        channel="chat",
        db=db
    )
    
    assert res_turn1["requires_disambiguation"] is True
    assert "Aarav Sharma" in res_turn1["response"]
    assert "Ananya Sharma" in res_turn1["response"]
    assert len(res_turn1["tool_executions"]) == 0
    conv_id = res_turn1["conversation_id"]
    
    # Turn 2: Disambiguating response
    res_turn2 = await conversation_engine.process_message(
        user=parent,
        user_message="Please check for Aarav.",
        conversation_id=conv_id,
        channel="chat",
        db=db
    )
    
    assert res_turn2["requires_disambiguation"] is False
    assert len(res_turn2["tool_executions"]) == 1
    assert res_turn2["tool_executions"][0]["tool"] == "get_attendance"
    assert "Aarav Sharma" in res_turn2["response"]
    assert "Overall Attendance" in res_turn2["response"]

@pytest.mark.asyncio
async def test_teacher_mark_attendance_conversation_flow(db):
    """Test Teacher natural language mark attendance."""
    teacher = db.query(User).filter(User.id == "usr-teacher-10a").first()
    
    res = await conversation_engine.process_message(
        user=teacher,
        user_message="Please mark Aarav Sharma present for today's class.",
        channel="chat",
        db=db
    )
    
    assert len(res["tool_executions"]) == 1
    assert res["tool_executions"][0]["tool"] == "mark_attendance"
    assert "PRESENT" in res["response"]

@pytest.mark.asyncio
async def test_principal_executive_analytics_flow(db):
    """Test Principal institutional analytics inquiry."""
    principal = db.query(User).filter(User.id == "usr-principal-01").first()
    
    res = await conversation_engine.process_message(
        user=principal,
        user_message="Give me the overall school attendance analytics report.",
        channel="chat",
        db=db
    )
    
    assert len(res["tool_executions"]) == 1
    assert res["tool_executions"][0]["tool"] == "get_attendance_analytics"
    assert "Executive Attendance Summary" in res["response"]
    assert "School-wide Average Attendance" in res["response"]

@pytest.mark.asyncio
async def test_multi_turn_escalation_confirmation_flow(db):
    """Test Multi-turn escalation confirmation sequence."""
    parent = db.query(User).filter(User.id == "usr-par-01").first()
    
    # Turn 1: Request escalation
    res1 = await conversation_engine.process_message(
        user=parent,
        user_message="I need to talk to teacher about my son's math homework difficulties.",
        channel="chat",
        db=db
    )
    
    assert len(res1["tool_executions"]) == 1
    assert res1["tool_executions"][0]["tool"] == "create_escalation"
    assert "Would you like me to confirm" in res1["response"]
    conv_id = res1["conversation_id"]
    
    # Turn 2: User confirms
    res2 = await conversation_engine.process_message(
        user=parent,
        user_message="Yes, please submit the request.",
        conversation_id=conv_id,
        channel="chat",
        db=db
    )
    
    assert len(res2["tool_executions"]) == 1
    assert res2["tool_executions"][0]["tool"] == "confirm_escalation"
    assert "officially confirmed" in res2["response"]
