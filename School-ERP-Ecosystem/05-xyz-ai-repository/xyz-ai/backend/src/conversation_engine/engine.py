import json
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from src.models import User, Conversation, Message, ParentStudentLink, TeacherClassLink, MessageSender
from src.conversation_engine.personas import build_persona_system_prompt
from src.conversation_engine.context_manager import context_manager
from src.conversation_engine.disambiguation import DisambiguationEngine
from src.conversation_engine.llm_client import llm_client
from src.tools.tool_registry import execute_tool, get_tools_schema_for_role
from src.security.sanitizer import detect_prompt_injection, filter_sensitive_output
from src.security.rate_limiter import rate_limiter
from src.auth.rbac import log_audit_event
from src.i18n.translator import multilingual_service

class ConversationEngine:
    """Core AI Orchestrator: Multi-turn Memory, Intent Routing, Tool Execution, Disambiguation & Hardened Security."""
    
    async def process_message(
        self,
        user: User,
        user_message: str,
        conversation_id: Optional[str] = None,
        channel: str = "chat",
        language_pref: Optional[str] = None,
        client_ip: str = "127.0.0.1",
        db: Session = None
    ) -> Dict[str, Any]:
        # 0. Language resolution: Explicit request pref -> detected script -> fallback "en"
        detected_lang = multilingual_service.detect_script_language(user_message)
        target_lang = language_pref or detected_lang or "en"
        
        # 1. Rate Limiting Check
        is_limited, remaining = rate_limiter.is_rate_limited(user.id)
        if is_limited:
            log_audit_event(
                db=db,
                user_id=user.id,
                action="RATE_LIMIT_EXCEEDED",
                resource="conversation_engine",
                result="denied",
                details="User exceeded allowed requests per minute.",
                ip_address=client_ip
            )
            return {
                "conversation_id": conversation_id or "rate-limited",
                "response": multilingual_service.get_phrase("rate_limited", lang=target_lang),
                "role": user.role,
                "channel": channel,
                "language": target_lang,
                "requires_disambiguation": False,
                "is_rate_limited": True,
                "tool_executions": []
            }

        # 2. Prompt Injection & Jailbreak Defense
        is_injection, reason = detect_prompt_injection(user_message)
        if is_injection:
            log_audit_event(
                db=db,
                user_id=user.id,
                action="PROMPT_INJECTION_BLOCKED",
                resource="conversation_engine",
                result="denied",
                details=reason,
                ip_address=client_ip
            )
            conv = context_manager.get_or_create_conversation(user, conversation_id, channel, db)
            refusal_text = multilingual_service.get_phrase("security_refusal", lang=target_lang)
            context_manager.append_message(conv.id, MessageSender.USER.value, user_message, db=db)
            context_manager.append_message(conv.id, MessageSender.AI.value, refusal_text, intent="security_refusal", db=db)
            
            return {
                "conversation_id": conv.id,
                "response": refusal_text,
                "role": user.role,
                "channel": channel,
                "language": target_lang,
                "requires_disambiguation": False,
                "security_flag": True,
                "tool_executions": []
            }
        
        # 3. Get or create conversation session
        conv = context_manager.get_or_create_conversation(user, conversation_id, channel, db)
        
        # 4. Gather role-specific context metadata
        db_meta = self._gather_user_metadata(user, db)
        
        # 5. Disambiguation Check 1: Parent multi-child ambiguity
        is_ambiguous, resolved_student_id, parent_prompt = DisambiguationEngine.check_parent_child_ambiguity(
            user, user_message, target_lang, db
        )
        if is_ambiguous:
            context_manager.append_message(conv.id, MessageSender.USER.value, user_message, db=db)
            context_manager.append_message(conv.id, MessageSender.AI.value, parent_prompt, intent="disambiguate_child", db=db)
            
            return {
                "conversation_id": conv.id,
                "response": parent_prompt,
                "role": user.role,
                "channel": channel,
                "language": target_lang,
                "requires_disambiguation": True,
                "tool_executions": []
            }
            
        # 5b. Disambiguation Check 2: Teacher missing student parameter when marking
        is_teacher_ambiguous, mark_status, teacher_prompt = DisambiguationEngine.check_teacher_marking_ambiguity(
            user, user_message, target_lang, db
        )
        if is_teacher_ambiguous:
            context_manager.append_message(conv.id, MessageSender.USER.value, user_message, db=db)
            context_manager.append_message(conv.id, MessageSender.AI.value, teacher_prompt, intent="disambiguate_student", db=db)
            
            return {
                "conversation_id": conv.id,
                "response": teacher_prompt,
                "role": user.role,
                "channel": channel,
                "language": target_lang,
                "requires_disambiguation": True,
                "tool_executions": []
            }
            
        if resolved_student_id:
            context_manager.set_session_data(conv.id, "target_student_id", resolved_student_id)
        elif user.role == "student" and user.student_profile:
            context_manager.set_session_data(conv.id, "target_student_id", user.student_profile.id)

        # 6. Build role-specific persona system prompt
        system_prompt = build_persona_system_prompt(user, db_meta, language_pref=target_lang)
        
        # 7. Build conversation message payload
        history = context_manager.get_context_history(conv.id, limit=10, db=db)
        
        messages_payload = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages_payload.append(h)
        messages_payload.append({"role": "user", "content": user_message})
        
        # Record user message
        context_manager.append_message(conv.id, MessageSender.USER.value, user_message, db=db)
        
        # 8. Retrieve role-filtered tools
        tools = get_tools_schema_for_role(user.role)
        
        session_ctx = {
            "target_student_id": context_manager.get_session_data(conv.id, "target_student_id"),
            "pending_escalation_id": context_manager.get_session_data(conv.id, "pending_escalation_id"),
            "student_id": user.student_profile.id if user.student_profile else None,
            "assigned_classes": db_meta.get("assigned_classes", []),
            "date": "2026-08-17"
        }
        
        # 9. First LLM Turn: Detect intent & decide if tool call is needed
        first_resp = await llm_client.generate_response(messages_payload, tools, user, session_ctx, language=target_lang)
        
        tool_executions = []
        final_content = first_resp.content
        
        # 10. Tool Execution Loop if tool calls were triggered
        if first_resp.tool_calls:
            context_manager.append_message(
                conv.id,
                MessageSender.AI.value,
                content="",
                tool_calls=first_resp.tool_calls,
                db=db
            )
            
            tool_msgs_for_llm = []
            for t in first_resp.tool_calls:
                t_name = t["name"]
                t_args = t["arguments"]
                t_id = t["id"]
                
                # Execute tool with strict application-level authorization check
                t_result = execute_tool(user, t_name, t_args, db)
                
                if t_name == "create_escalation" and t_result.get("escalation_id"):
                    context_manager.set_session_data(conv.id, "pending_escalation_id", t_result["escalation_id"])
                elif t_name == "confirm_escalation":
                    context_manager.clear_session_data(conv.id, "pending_escalation_id")
                    
                tool_executions.append({
                    "tool": t_name,
                    "arguments": t_args,
                    "result_status": t_result.get("status", "completed"),
                    "output": t_result
                })
                
                context_manager.append_message(
                    conv.id,
                    MessageSender.TOOL.value,
                    content=json.dumps(t_result),
                    tool_call_id=t_id,
                    db=db
                )
                
                tool_msgs_for_llm.append({
                    "role": "tool",
                    "tool_call_id": t_id,
                    "name": t_name,
                    "content": json.dumps(t_result)
                })
                
            messages_payload.append({
                "role": "assistant",
                "content": "",
                "tool_calls": first_resp.tool_calls
            })
            for tm in tool_msgs_for_llm:
                messages_payload.append(tm)
                
            second_resp = await llm_client.generate_response(messages_payload, tools, user, session_ctx, language=target_lang)
            final_content = second_resp.content or "Your request has been processed."
            
        final_content = filter_sensitive_output(final_content or "")
        context_manager.append_message(conv.id, MessageSender.AI.value, final_content, db=db)
            
        return {
            "conversation_id": conv.id,
            "response": final_content,
            "role": user.role,
            "channel": channel,
            "language": target_lang,
            "requires_disambiguation": False,
            "tool_executions": tool_executions
        }

    def _gather_user_metadata(self, user: User, db: Session) -> Dict[str, Any]:
        meta = {}
        if user.role == "parent":
            links = db.query(ParentStudentLink).filter(ParentStudentLink.parent_id == user.id).all()
            meta["linked_children"] = [
                {
                    "student_id": l.student_id,
                    "name": l.student.user.name if l.student and l.student.user else "Child",
                    "class_name": l.student.class_name if l.student else "",
                    "section": l.student.section if l.student else "",
                    "roll_no": l.student.roll_no if l.student else ""
                }
                for l in links
            ]
        elif user.role == "teacher":
            classes = db.query(TeacherClassLink).filter(TeacherClassLink.teacher_id == user.id).all()
            meta["assigned_classes"] = [
                {
                    "class_name": c.class_name,
                    "section": c.section,
                    "subject": c.subject
                }
                for c in classes
            ]
        return meta

    def clear_session_memory(self, conversation_id: str):
        """Reset in-memory state for a conversation."""
        context_manager.clear_session_data(conversation_id, "target_student_id")
        context_manager.clear_session_data(conversation_id, "pending_escalation_id")

conversation_engine = ConversationEngine()
