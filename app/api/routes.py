from uuid import uuid4
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from openai import APIConnectionError, APIStatusError, AuthenticationError, NotFoundError, RateLimitError
import httpx
from app.api.schemas import DecisionRequest, ApprovalRequest, RollbackRequest
from app.core.config import settings
from app.core.llm import embeddings
from app.db.session import SessionLocal
from app.db.repository import create_decision, create_approval, get_decision, decide_approval, rollback_decision
from app.graph.workflow import graph

router = APIRouter(prefix="/v1")

@router.get("/agentConfigStatus")
def agent_config_status():
    status = {
        "openai_api_problem": False,
        "api_key_problem": False,
        "network_error": False,
        "embedding_model_problem": False,
        "rate_limit": 0,
    }
    if not settings.openai_api_key:
        status["openai_api_problem"] = True
        status["api_key_problem"] = True
        return status

    try:
        embeddings().embed_query("agent configuration health check")
    except Exception as exc:
        status["openai_api_problem"] = True
        status["api_key_problem"] = isinstance(exc, AuthenticationError)
        status["network_error"] = isinstance(exc, (APIConnectionError, httpx.TransportError))
        status["embedding_model_problem"] = isinstance(exc, NotFoundError)
        status["rate_limit"] = int(
            isinstance(exc, RateLimitError)
            or (isinstance(exc, APIStatusError) and exc.status_code == 429)
        )
    return status


@router.post("/decisions")
def create_decision_route(request: DecisionRequest):
    db = SessionLocal()
    try:
        did = create_decision(db, request.model_dump())
    finally:
        db.close()
    config = {"configurable": {"thread_id": did}}
    try:
        result = graph.invoke({"decision_id": did, "request": request.model_dump(), "retry_count": 0}, config=config)
    except Exception as exc:
        raise HTTPException(500, detail=str(exc))
    if "__interrupt__" in result:
        db = SessionLocal()
        try:
            aid = create_approval(db, did)
        finally:
            db.close()
        return {"decision_id": did, "status": "PENDING_APPROVAL", "approval_id": aid, "decision": result["__interrupt__"][0].value}
    return {"decision_id": did, "status": "COMPLETED", "decision": result.get("final")}

@router.post("/approvals/{approval_id}")
def approval_route(approval_id: str, request: ApprovalRequest):
    db = SessionLocal()
    try:
        approval = decide_approval(db, approval_id, request.approved, request.approver, request.comment)
        decision_id = approval.decision_id
        row = get_decision(db, decision_id)
        if not row:
            raise HTTPException(404, "Decision not found")
        decision_request = row.request_json
    finally:
        db.close()
    config = {"configurable": {"thread_id": decision_id}}
    try:
        result = graph.invoke(Command(resume={"approved": request.approved, "comment": request.comment, "approver": request.approver}), config=config)
    except Exception as exc:
        raise HTTPException(500, detail=str(exc))
    return {"decision_id": decision_id, "status": "APPROVED" if request.approved else "REJECTED", "decision": result.get("final")}

@router.get("/decisions/{decision_id}")
def decision_route(decision_id: str):
    db = SessionLocal()
    try:
        row = get_decision(db, decision_id)
        if not row:
            raise HTTPException(404, "Decision not found")
        return {"decision_id": row.id, "status": row.status, "request": row.request_json, "result": row.result_json}
    finally:
        db.close()


@router.post("/decisions/{decision_id}/rollback")
def rollback_route(decision_id: str, request: RollbackRequest):
    db = SessionLocal()
    try:
        row = rollback_decision(db, decision_id, request.actor, request.reason)
        return {"decision_id": row.id, "status": row.status}
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    finally:
        db.close()
