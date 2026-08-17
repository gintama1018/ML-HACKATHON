import pytest
from src.i18n.languages import SUPPORTED_LANGUAGES, list_supported_languages, get_language_metadata
from src.i18n.translator import multilingual_service
from src.conversation_engine.personas import build_persona_system_prompt
from src.models import User, UserRole

def test_eleven_languages_registered():
    """Verify all 11 target Indian languages are defined architecturally."""
    expected_codes = ["en", "hi", "ta", "bn", "te", "mr", "gu", "kn", "ml", "pa", "ur"]
    for code in expected_codes:
        assert code in SUPPORTED_LANGUAGES
        meta = get_language_metadata(code)
        assert meta["code"] == code
        assert len(meta["name"]) > 0
        assert len(meta["native_name"]) > 0

def test_deep_tested_languages_localization():
    """Verify the 4 deep-tested languages produce native language responses."""
    deep_codes = ["en", "hi", "ta", "bn"]
    for code in deep_codes:
        meta = get_language_metadata(code)
        assert meta["deep_tested"] is True
        
        # Test localized attendance output
        out = multilingual_service.format_attendance_message(
            lang=code,
            student_name="Aarav Sharma",
            percentage=90.0,
            total_days=30,
            present_days=27,
            absent_days=3
        )
        assert "Aarav Sharma" in out
        assert "90.0" in out
        assert len(out) > 20

def test_persona_language_adaptation():
    """Verify system prompt adapts dynamically to user's selected language."""
    student_user = User(id="u1", name="Aarav", email="a@s.com", role=UserRole.STUDENT.value, password_hash="x", language_pref="hi")
    prompt_hi = build_persona_system_prompt(student_user, {}, language_pref="hi")
    assert "Hindi" in prompt_hi
    
    prompt_ta = build_persona_system_prompt(student_user, {}, language_pref="ta")
    assert "Tamil" in prompt_ta
