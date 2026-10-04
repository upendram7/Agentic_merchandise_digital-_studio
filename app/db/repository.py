from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from app.db.models import DecisionRecord, Approval, AuditEvent


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:20]}"


def create_decision(db, request: dict) -> str:
    did = new_id("dec")
    db.add(DecisionRecord(id=did, status="RUNNING", request_json=request))
    db.add(AuditEvent(decision_id=did, event_type="DECISION_STARTED", payload={}))
    db.commit()
    return did


def save_result(db, decision_id: str, result: dict, status: str):
    row = db.get(DecisionRecord, decision_id)
    row.result_json = result
    row.status = status
    db.add(AuditEvent(decision_id=decision_id, event_type=f"DECISION_{status}", payload={"status": status}))
    db.commit()


def create_approval(db, decision_id: str) -> str:
    aid = new_id("apr")

    decision = db.get(DecisionRecord, decision_id)
    if not decision:
        raise ValueError("Decision not found")

    decision.status = "PENDING_APPROVAL"

    db.add(
        Approval(
            id=aid,
            decision_id=decision_id,
            status="PENDING"
        )
    )

    db.add(
        AuditEvent(
            decision_id=decision_id,
            event_type="APPROVAL_REQUESTED",
            payload={"approval_id": aid}
        )
    )

    db.commit()
    return aid



def decide_approval(db, approval_id: str, approved: bool, approver: str, comment: str | None):
    row = db.get(Approval, approval_id)
    if not row:
        raise ValueError("Approval not found")
    row.status = "APPROVED" if approved else "REJECTED"
    row.approver = approver
    row.comment = comment
    row.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(AuditEvent(decision_id=row.decision_id, event_type=f"APPROVAL_{row.status}", payload={"approval_id": approval_id, "approver": approver, "comment": comment}))
    db.commit()
    return row


def get_decision(db, decision_id: str):
    return db.get(DecisionRecord, decision_id)


def rollback_decision(db, decision_id: str, actor: str, reason: str):
    row = db.get(DecisionRecord, decision_id)
    if not row:
        raise ValueError("Decision not found")
    if row.status != "APPROVED":
        raise ValueError("Only APPROVED decisions can be rolled back")
    row.status = "ROLLED_BACK"
    db.add(AuditEvent(decision_id=decision_id, event_type="DECISION_ROLLBACK", payload={"actor": actor, "reason": reason}))
    db.commit()
    return row
