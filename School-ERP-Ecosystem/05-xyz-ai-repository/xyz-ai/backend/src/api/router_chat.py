from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Conversation, Message
from src.auth.dependencies import get_current_user
from src.conversation_engine.engine import conversation_engine
from src.conversation_engine.context_manager import context_manager

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language_pref: Optional[str] = None

@router.post("/message")
async def send_chat_message(
    req: ChatMessageRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a natural language message through the AI Conversation Engine."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    result = await conversation_engine.process_message(
        user=user,
        user_message=req.message,
        conversation_id=req.conversation_id,
        channel="chat",
        language_pref=req.language_pref,
        client_ip=client_ip,
        db=db
    )
    return result

@router.get("/history/{conversation_id}")
def get_conversation_history(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve message history for an active conversation."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or unauthorized"
        )
        
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp.asc()).all()
    
    return {
        "conversation_id": conv.id,
        "channel": conv.channel,
        "started_at": conv.started_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
                "intent": m.intent,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]
    }
