import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.models import Conversation, Message, User, ChannelType, MessageSender

class ContextManager:
    """Manages multi-turn conversation memory with hybrid Cache + SQL persistence."""
    
    def __init__(self):
        # In-memory session cache (keyed by conversation_id)
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}
        # Pending context flags (e.g. pending escalation confirmation)
        self._session_metadata: Dict[str, Dict[str, Any]] = {}

    def get_or_create_conversation(
        self, user: User, conversation_id: Optional[str], channel: str, db: Session
    ) -> Conversation:
        """Retrieve existing active conversation or initialize a new one."""
        if conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
                Conversation.is_active == True
            ).first()
            if conv:
                return conv
                
        # Create new conversation
        conv = Conversation(
            user_id=user.id,
            channel=channel or ChannelType.CHAT.value,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def get_context_history(
        self, conversation_id: str, limit: int = 10, db: Session = None
    ) -> List[Dict[str, Any]]:
        """Retrieve the last N turns for the conversation."""
        if conversation_id in self._memory_store and len(self._memory_store[conversation_id]) > 0:
            return self._memory_store[conversation_id][-limit:]
            
        # Fallback to DB if not cached in memory
        if db:
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp.asc()).all()
            
            history = []
            for m in messages:
                role = "user" if m.sender == MessageSender.USER.value else "assistant"
                if m.sender == MessageSender.TOOL.value:
                    role = "tool"
                elif m.sender == MessageSender.SYSTEM.value:
                    role = "system"
                    
                msg_entry = {
                    "role": role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                if m.tool_calls_json:
                    msg_entry["tool_calls"] = json.loads(m.tool_calls_json)
                if m.tool_call_id:
                    msg_entry["tool_call_id"] = m.tool_call_id
                history.append(msg_entry)
                
            self._memory_store[conversation_id] = history
            return history[-limit:]
            
        return []

    def append_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        intent: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        db: Session = None
    ):
        """Append message to cache and persist to system-of-record SQL database."""
        role = "user" if sender == MessageSender.USER.value else "assistant"
        if sender == MessageSender.TOOL.value:
            role = "tool"
            
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if tool_calls:
            entry["tool_calls"] = tool_calls
        if tool_call_id:
            entry["tool_call_id"] = tool_call_id
            
        if conversation_id not in self._memory_store:
            self._memory_store[conversation_id] = []
        self._memory_store[conversation_id].append(entry)
        
        # Persist to database
        if db:
            db_msg = Message(
                conversation_id=conversation_id,
                sender=sender,
                content=content,
                intent=intent,
                tool_calls_json=json.dumps(tool_calls) if tool_calls else None,
                tool_call_id=tool_call_id,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(db_msg)
            
            # Update conversation timestamp
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
                
            db.commit()

    def set_session_data(self, conversation_id: str, key: str, value: Any):
        if conversation_id not in self._session_metadata:
            self._session_metadata[conversation_id] = {}
        self._session_metadata[conversation_id][key] = value

    def get_session_data(self, conversation_id: str, key: str, default: Any = None) -> Any:
        return self._session_metadata.get(conversation_id, {}).get(key, default)

    def clear_session_data(self, conversation_id: str, key: str):
        if conversation_id in self._session_metadata and key in self._session_metadata[conversation_id]:
            del self._session_metadata[conversation_id][key]

context_manager = ContextManager()
