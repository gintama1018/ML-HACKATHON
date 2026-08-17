from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from src.models import User
from src.tools.mock_erp_adapter import erp_adapter

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_attendance",
            "description": "Fetch attendance history and aggregate attendance statistics for a specific student.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The unique student ID (e.g. 'stu-101')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional start date in YYYY-MM-DD format."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional end date in YYYY-MM-DD format."
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_attendance",
            "description": "Mark or update the attendance status for a student on a specific date (Teacher only, assigned class only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The unique student ID to mark."
                    },
                    "attendance_date": {
                        "type": "string",
                        "description": "The date in YYYY-MM-DD format."
                    },
                    "status": {
                        "type": "string",
                        "enum": ["present", "absent", "late", "excused"],
                        "description": "Attendance status."
                    },
                    "remarks": {
                        "type": "string",
                        "description": "Optional notes or remarks regarding the attendance."
                    }
                },
                "required": ["student_id", "attendance_date", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_analytics",
            "description": "Retrieve aggregate attendance metrics, class-wise breakdown, and low attendance alerts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "enum": ["school", "class"],
                        "description": "The analytics scope: 'school' for whole-school (Principal only), or 'class' for class-specific analytics."
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Class name (e.g. '10', '9', '8') if querying class analytics."
                    },
                    "section": {
                        "type": "string",
                        "description": "Section (e.g. 'A', 'B') if querying class analytics."
                    }
                },
                "required": ["scope"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_profile",
            "description": "Fetch detailed profile of a student including class, section, roll number, and parent contact information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The unique student ID."
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_escalation",
            "description": "Initiate an escalation ticket to connect with a teacher or school management. Requires subsequent user confirmation before dispatch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "enum": ["teacher", "management"],
                        "description": "Target party for escalation: 'teacher' or 'management'."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Detailed reason or topic for the escalation."
                    },
                    "contact_info": {
                        "type": "string",
                        "description": "Optional contact details or teacher name."
                    }
                },
                "required": ["target", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_escalation",
            "description": "Confirm and officially dispatch a pending escalation ticket to the teacher or management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "escalation_id": {
                        "type": "string",
                        "description": "The unique escalation ticket ID to confirm."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional confirmation remarks or preferred call time."
                    }
                },
                "required": ["escalation_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_escalation_status",
            "description": "Check the current status and resolution details of an escalation ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "escalation_id": {
                        "type": "string",
                        "description": "The unique escalation ticket ID."
                    }
                },
                "required": ["escalation_id"]
            }
        }
    }
]

def get_tools_schema_for_role(role: str) -> List[Dict[str, Any]]:
    """Return tool schemas available for a given role (defense-in-depth is always enforced on execution)."""
    if role == "student":
        allowed = ["get_attendance", "get_student_profile", "create_escalation", "confirm_escalation", "get_escalation_status"]
    elif role == "parent":
        allowed = ["get_attendance", "get_student_profile", "create_escalation", "confirm_escalation", "get_escalation_status"]
    elif role == "teacher":
        allowed = ["get_attendance", "mark_attendance", "get_attendance_analytics", "get_student_profile", "create_escalation", "confirm_escalation", "get_escalation_status"]
    elif role == "principal":
        allowed = ["get_attendance", "get_attendance_analytics", "get_student_profile", "create_escalation", "confirm_escalation", "get_escalation_status"]
    else:
        allowed = []
        
    return [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed]

def execute_tool(user: User, tool_name: str, tool_args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Central tool invocation dispatcher.
    Executes real business logic with application-layer security checks.
    """
    try:
        if tool_name == "get_attendance":
            student_id = tool_args.get("student_id")
            s_date = date.fromisoformat(tool_args["start_date"]) if tool_args.get("start_date") else None
            e_date = date.fromisoformat(tool_args["end_date"]) if tool_args.get("end_date") else None
            return erp_adapter.get_attendance(user, student_id, s_date, e_date, db)
            
        elif tool_name == "mark_attendance":
            student_id = tool_args.get("student_id")
            att_date_raw = tool_args.get("attendance_date")
            att_date = date.fromisoformat(att_date_raw) if att_date_raw else date.today()
            status_val = tool_args.get("status")
            remarks = tool_args.get("remarks")
            return erp_adapter.mark_attendance(user, student_id, att_date, status_val, remarks, db)
            
        elif tool_name == "get_attendance_analytics":
            scope = tool_args.get("scope", "school")
            cls = tool_args.get("class_name")
            sec = tool_args.get("section")
            return erp_adapter.get_attendance_analytics(user, scope, cls, sec, db)
            
        elif tool_name == "get_student_profile":
            student_id = tool_args.get("student_id")
            return erp_adapter.get_student_profile(user, student_id, db)
            
        elif tool_name == "create_escalation":
            target = tool_args.get("target")
            reason = tool_args.get("reason")
            contact = tool_args.get("contact_info")
            return erp_adapter.create_escalation(user, target, reason, contact, db)
            
        elif tool_name == "confirm_escalation":
            escalation_id = tool_args.get("escalation_id")
            notes = tool_args.get("notes")
            return erp_adapter.confirm_escalation(user, escalation_id, notes, db)
            
        elif tool_name == "get_escalation_status":
            escalation_id = tool_args.get("escalation_id")
            return erp_adapter.get_escalation_status(user, escalation_id, db)
            
        else:
            return {"status": "error", "message": f"Unknown tool '{tool_name}'."}
            
    except Exception as e:
        return {"status": "error", "error_type": type(e).__name__, "message": str(e)}
