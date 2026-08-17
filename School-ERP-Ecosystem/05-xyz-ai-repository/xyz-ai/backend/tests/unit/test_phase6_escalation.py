import pytest
from src.database import SessionLocal
from src.models import User, Escalation, EscalationStatus
from src.escalation.escalation_service import escalation_service
from seed.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    seed_database()
    session = SessionLocal()
    yield session
    session.close()

def test_escalation_lifecycle_state_machine(db):
    """Test full PENDING -> CONFIRMED -> RESOLVED progression."""
    parent = db.query(User).filter(User.id == "usr-par-01").first()
    teacher = db.query(User).filter(User.id == "usr-teacher-10a").first()
    
    # 1. Create ticket (status=PENDING)
    create_res = escalation_service.create_escalation_ticket(
        user=parent,
        target="teacher",
        reason="Inquiry regarding math olympiad preparation",
        contact_info="Amit Verma",
        db=db
    )
    assert create_res["status"] == EscalationStatus.PENDING.value
    assert create_res["requires_confirmation"] is True
    ticket_id = create_res["ticket_id"]
    
    # 2. Confirm ticket (status=CONFIRMED)
    confirm_res = escalation_service.confirm_escalation_ticket(
        user=parent,
        ticket_id=ticket_id,
        confirmation_notes="Parent prefers morning slot",
        db=db
    )
    assert confirm_res["status"] == EscalationStatus.CONFIRMED.value
    assert "dispatch_id" in confirm_res
    
    # 3. Resolve ticket (status=RESOLVED by Teacher)
    resolve_res = escalation_service.resolve_escalation_ticket(
        user=teacher,
        ticket_id=ticket_id,
        resolution_summary="Conducted 15-minute phone consultation. Shared syllabus.",
        db=db
    )
    assert resolve_res["status"] == EscalationStatus.RESOLVED.value
    assert resolve_res["resolved_by"] == teacher.name

def test_student_cannot_resolve_escalation(db):
    """Verify students cannot resolve escalation tickets."""
    student = db.query(User).filter(User.id == "usr-stu-101").first()
    ticket = db.query(Escalation).first()
    assert ticket is not None
    
    with pytest.raises(PermissionError):
        escalation_service.resolve_escalation_ticket(
            user=student,
            ticket_id=ticket.id,
            resolution_summary="Unauthorized resolution",
            db=db
        )

def test_list_user_escalations(db):
    """Test listing user tickets."""
    parent = db.query(User).filter(User.id == "usr-par-01").first()
    tickets = escalation_service.list_user_escalations(parent, db)
    assert isinstance(tickets, list)
    assert len(tickets) > 0
