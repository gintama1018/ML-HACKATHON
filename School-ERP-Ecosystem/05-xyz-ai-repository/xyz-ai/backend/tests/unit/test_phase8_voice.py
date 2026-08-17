import pytest
from src.database import SessionLocal
from src.models import User
from src.voice.voice_service import voice_service
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    seed_database()
    session = SessionLocal()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_voice_noisy_input_handling(db):
    """Verify low confidence STT (noisy audio) prompts user to repeat rather than guessing."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    # Low confidence audio turn (0.42 < 0.65 threshold)
    res = await voice_service.handle_voice_turn(
        user=student,
        raw_speech_text="...garbled background noise...",
        confidence_score=0.42,
        db=db
    )
    
    assert res["is_noisy"] is True
    assert "couldn't hear you clearly" in res["response"]
    assert len(res["tool_executions"]) == 0
    assert "tts" in res
    assert res["channel"] == "voice"

@pytest.mark.asyncio
async def test_voice_clean_turn_with_tts_and_visemes(db):
    """Verify clean voice input executes unified conversation engine and produces TTS + visemes."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    
    res = await voice_service.handle_voice_turn(
        user=student,
        raw_speech_text="What is my attendance percentage?",
        confidence_score=0.96,
        db=db
    )
    
    assert res["is_noisy"] is False
    assert res["transcription"] == "What is my attendance percentage?"
    assert len(res["tool_executions"]) == 1
    assert res["tool_executions"][0]["tool"] == "get_attendance"
    
    # Verify TTS & Viseme generation
    tts = res["tts"]
    assert "audio_base64" in tts
    assert len(tts["visemes"]) > 0
    assert tts["duration_seconds"] > 0
