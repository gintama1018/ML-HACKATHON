import base64
import json
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from src.models import User, ChannelType
from src.conversation_engine.engine import conversation_engine

# Viseme mappings for speech visemes (matches 2D/3D avatar mouth shapes: 'rest', 'aa', 'ee', 'oo', 'ch', 'ff')
VISEME_MAP = {
    "a": "aa", "e": "ee", "i": "ee", "o": "oo", "u": "oo",
    "f": "ff", "v": "ff", "c": "ch", "s": "ch", "sh": "ch"
}

class VoiceService:
    """Unified Voice Pipeline: Audio In -> STT -> Conversation Brain -> TTS -> Visemes Audio Out."""
    
    CONFIDENCE_THRESHOLD: float = 0.65
    
    @staticmethod
    def process_stt_transcription(
        audio_base64: Optional[str] = None,
        raw_text_hint: Optional[str] = None,
        confidence_score: float = 0.95
    ) -> Tuple[Optional[str], float, bool]:
        """
        Process speech-to-text input.
        Returns: (transcribed_text, confidence_score, is_noisy)
        """
        # If low confidence or noisy audio detected
        if confidence_score < VoiceService.CONFIDENCE_THRESHOLD:
            return None, confidence_score, True
            
        transcribed_text = raw_text_hint or "Hello, check my attendance please."
        return transcribed_text, confidence_score, False

    @staticmethod
    def synthesize_tts_audio(
        text: str,
        language: str = "en",
        speaker_persona: str = "friendly_female"
    ) -> Dict[str, Any]:
        """
        Synthesize text-to-speech audio with timed viseme cue frames for avatar lip-sync.
        """
        # Generate simple viseme timeline based on vowels and syllables
        visemes = []
        time_cursor = 0.0
        words = text.split()
        
        for w in words:
            for char in w.lower():
                shape = VISEME_MAP.get(char, "rest")
                if shape != "rest":
                    visemes.append({
                        "time_ms": int(time_cursor * 1000),
                        "viseme": shape,
                        "intensity": 0.85
                    })
                time_cursor += 0.05
            time_cursor += 0.08  # Word pause
            
        # Simulated audio waveform envelope / data URI
        audio_mock_bytes = f"RIFF_WAV_SIMULATION_FOR_{len(text)}_CHARS_{language}".encode()
        audio_b64 = base64.b64encode(audio_mock_bytes).decode()
        
        return {
            "audio_format": "audio/wav",
            "audio_base64": f"data:audio/wav;base64,{audio_b64}",
            "duration_seconds": round(time_cursor, 2),
            "visemes": visemes,
            "speaker": speaker_persona,
            "language": language
        }

    @staticmethod
    async def handle_voice_turn(
        user: User,
        audio_base64: Optional[str] = None,
        raw_speech_text: Optional[str] = None,
        confidence_score: float = 0.95,
        conversation_id: Optional[str] = None,
        language_pref: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Full End-to-End Voice Turn:
        1. STT -> Transcript (with low-confidence retry check)
        2. Text into exact same Conversation Engine (Phase 4 brain)
        3. Response text -> TTS audio + Visemes
        """
        transcribed_text, conf, is_noisy = VoiceService.process_stt_transcription(
            audio_base64=audio_base64,
            raw_text_hint=raw_speech_text,
            confidence_score=confidence_score
        )
        
        # If noise/low-confidence was detected, request clarification instead of guessing
        if is_noisy or not transcribed_text:
            retry_prompt = "I'm sorry, I couldn't hear you clearly due to background noise. Could you please repeat that?"
            tts_data = VoiceService.synthesize_tts_audio(retry_prompt, language=language_pref or user.language_pref or "en")
            return {
                "conversation_id": conversation_id,
                "transcription": None,
                "confidence_score": conf,
                "is_noisy": True,
                "response": retry_prompt,
                "tts": tts_data,
                "channel": ChannelType.VOICE.value,
                "tool_executions": []
            }
            
        # Send through unified brain (same code path as chat!)
        engine_result = await conversation_engine.process_message(
            user=user,
            user_message=transcribed_text,
            conversation_id=conversation_id,
            channel=ChannelType.VOICE.value,
            language_pref=language_pref or user.language_pref,
            db=db
        )
        
        # Synthesize TTS and Visemes for the reply
        tts_data = VoiceService.synthesize_tts_audio(
            text=engine_result["response"],
            language=engine_result.get("language", "en")
        )
        
        return {
            "conversation_id": engine_result["conversation_id"],
            "transcription": transcribed_text,
            "confidence_score": conf,
            "is_noisy": False,
            "response": engine_result["response"],
            "tts": tts_data,
            "role": user.role,
            "channel": ChannelType.VOICE.value,
            "language": engine_result.get("language", "en"),
            "tool_executions": engine_result.get("tool_executions", [])
        }

voice_service = VoiceService()
