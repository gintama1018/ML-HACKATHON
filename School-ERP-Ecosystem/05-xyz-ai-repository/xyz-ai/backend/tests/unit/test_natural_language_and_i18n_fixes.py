import pytest
from src.database import SessionLocal
from src.models import User
from src.conversation_engine.engine import conversation_engine
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    seed_database()
    session = SessionLocal()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_student_greeting_does_not_dump_attendance(db):
    """Verify Student saying 'Hello, how are you today?' receives a polite greeting without unsolicited attendance dumps."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    res = await conversation_engine.process_message(
        user=student,
        user_message="Hello, how are you today?",
        channel="chat",
        db=db
    )
    
    assert res["requires_disambiguation"] is False
    assert len(res["tool_executions"]) == 0  # No tool call fired!
    assert "Aarav" in res["response"]
    assert "doing well" in res["response"] or "doing great" in res["response"]
    assert "overall attendance is" not in res["response"].lower()

@pytest.mark.asyncio
async def test_student_homework_question_does_not_falsely_escalate(db):
    """Verify Student asking for homework assistance receives helpful advice rather than an accidental escalation ticket."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    res = await conversation_engine.process_message(
        user=student,
        user_message="Can you help me with my math homework problem?",
        channel="chat",
        db=db
    )
    
    assert len(res["tool_executions"]) == 0  # No escalation tool called!
    assert "study strategies" in res["response"] or "homework" in res["response"]
    assert "ticket" not in res["response"]

@pytest.mark.asyncio
async def test_teacher_mark_without_student_prompts_for_missing_info(db):
    """Verify Teacher saying 'mark attendance as absent for today' prompts for missing student rather than throwing raw error."""
    teacher = db.query(User).filter(User.id == "usr-teacher-10a").first()
    
    res = await conversation_engine.process_message(
        user=teacher,
        user_message="mark attendance as absent for today",
        channel="chat",
        db=db
    )
    
    assert res["requires_disambiguation"] is True
    assert len(res["tool_executions"]) == 0
    assert "Which student in Class 10-A would you like to mark as absent?" in res["response"]
    assert "Please provide the student's name or roll number" in res["response"]

@pytest.mark.asyncio
async def test_hindi_language_query_returns_authentic_hindi(db):
    """Verify Hindi query 'मेरी उपस्थिति क्या है?' or language_pref='hi' produces real Hindi synthesis."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    res = await conversation_engine.process_message(
        user=student,
        user_message="मेरी उपस्थिति क्या है?",
        channel="chat",
        db=db
    )
    
    assert len(res["tool_executions"]) == 1
    assert res["tool_executions"][0]["tool"] == "get_attendance"
    assert res["language"] == "hi"
    assert "उपस्थिति का विवरण" in res["response"]
    assert "%" in res["response"]

@pytest.mark.asyncio
async def test_tamil_and_bengali_language_preferences(db):
    """Verify Tamil and Bengali preferences return native language synthesis."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    # Tamil Turn
    res_ta = await conversation_engine.process_message(
        user=student,
        user_message="What is my attendance percentage?",
        language_pref="ta",
        channel="chat",
        db=db
    )
    assert res_ta["language"] == "ta"
    assert "வருகை விவரம்" in res_ta["response"] or "வருகை" in res_ta["response"]
    assert "%" in res_ta["response"]
    
    # Bengali Turn
    res_bn = await conversation_engine.process_message(
        user=student,
        user_message="What is my attendance percentage?",
        language_pref="bn",
        channel="chat",
        db=db
    )
    assert res_bn["language"] == "bn"
    assert "উপস্থিতির বিবরণ" in res_bn["response"] or "উপস্থিতি" in res_bn["response"]
    assert "%" in res_bn["response"]
