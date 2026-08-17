from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User
from src.auth.dependencies import get_current_user
from src.voice.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["Voice"])

class VoiceTurnRequest(BaseModel):
    audio_base64: Optional[str] = None
    speech_text: Optional[str] = None
    confidence_score: float = 0.95
    conversation_id: Optional[str] = None
    language_pref: Optional[str] = None

@router.post("/turn")
async def handle_voice_turn(
    req: VoiceTurnRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process speech input through unified conversation engine and return TTS with lip-sync visemes."""
    result = await voice_service.handle_voice_turn(
        user=user,
        audio_base64=req.audio_base64,
        raw_speech_text=req.speech_text,
        confidence_score=req.confidence_score,
        conversation_id=req.conversation_id,
        language_pref=req.language_pref,
        db=db
    )
    return result
