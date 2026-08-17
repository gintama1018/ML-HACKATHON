from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.models import AuditLog, User

def query_audit_logs(
    db: Session,
    limit: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Query recent security and permission audit logs."""
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if result:
        query = query.filter(AuditLog.result == result)
        
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user.name if l.user else "System",
            "action": l.action,
            "resource": l.resource,
            "result": l.result,
            "details": l.details,
            "ip_address": l.ip_address,
            "timestamp": l.timestamp.isoformat()
        }
        for l in logs
    ]
