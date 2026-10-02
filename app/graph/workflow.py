from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from app.graph.state import DecisionState
from app.core.llm import embeddings
from app.rag.retriever import hybrid_search
from app.tools.business import calculate_promotion_economics, inventory_coverage_days, approval_required
from app.tools.guardrails import validate_guardrails
from app.agents import merchandising, promotion, risk, synthesizer

memory = MemorySaver()


def retrieve(state: DecisionState):
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        req = state["request"]
        q = f"{req['category']} {req['objective']} {req['store_cluster']}"
        try:
            vector = embeddings().embed_query(q)
        except Exception:
            vector = None
        evidence = hybrid_search(db, q, vector, limit=6)
        return {"evidence": evidence}
    finally:
        db.close()


def deterministic_tools(state: DecisionState):
    req = state["request"]
    # Demo baseline data is intentionally deterministic and can be replaced by ERP/retail APIs.
    econ = calculate_promotion_economics(100.0, 55.0, min(15.0, req["constraints"]["max_discount_pct"]))
    coverage = inventory_coverage_days(1200, 45)
    return {"tool_results": {"promotion_economics": econ.model_dump(), "inventory_coverage_days": coverage}}


def merch(state: DecisionState):
    return {"agent_outputs": {**state.get("agent_outputs", {}), "merchandising": merchandising.run(state["request"], state["evidence"], state["tool_results"])}}


def promo(state: DecisionState):
    return {"agent_outputs": {**state.get("agent_outputs", {}), "promotion": promotion.run(state["request"], state["evidence"], state["tool_results"])}}


def risk_node(state: DecisionState):
    return {"agent_outputs": {**state.get("agent_outputs", {}), "risk": risk.run(state["request"], state["evidence"], state["agent_outputs"], state["tool_results"])}}


def synthesize(state: DecisionState):
    p = state["agent_outputs"]["promotion"]
    econ = state["tool_results"]["promotion_economics"]
    guard = validate_guardrails(p["discount_pct"], p["expected_margin_pct"], state["request"]["constraints"]["min_margin_pct"], state["request"]["constraints"]["max_discount_pct"])
    need, reason = approval_required(econ["revenue_lift_pct"], p["discount_pct"], state["request"]["constraints"]["max_discount_pct"])
    final = synthesizer.run(state["request"], state["evidence"], state["agent_outputs"], state["tool_results"], {**guard.model_dump(), "approval_required": need, "approval_reason": reason})
    final["requires_human_approval"] = need
    final["approval_reason"] = reason
    return {"final": final}


def route_after_synthesis(state: DecisionState):
    return "approval" if state["final"]["requires_human_approval"] else "persist"


def approval_node(state: DecisionState):
    decision = interrupt({"type": "HUMAN_APPROVAL", "decision_id": state["decision_id"], "message": "Review and approve this commercial decision before execution.", "decision": state["final"]})
    return {"approval_status": "APPROVED" if decision.get("approved") else "REJECTED"}


def route_after_approval(state: DecisionState):
    return "persist" if state.get("approval_status") == "APPROVED" else "rejected"


def persist(state: DecisionState):
    from app.db.session import SessionLocal
    from app.db.repository import save_result
    db = SessionLocal()
    try:
        save_result(db, state["decision_id"], state["final"], "APPROVED" if state.get("approval_status") == "APPROVED" else "COMPLETED")
    finally:
        db.close()
    return {}


def rejected(state: DecisionState):
    from app.db.session import SessionLocal
    from app.db.repository import save_result
    db = SessionLocal()
    try:
        save_result(db, state["decision_id"], state["final"], "REJECTED")
    finally:
        db.close()
    return {}


def build_graph():
    g = StateGraph(DecisionState)
    g.add_node("retrieve", retrieve)
    g.add_node("deterministic_tools", deterministic_tools)
    g.add_node("merch", merch)
    g.add_node("promo", promo)
    g.add_node("risk", risk_node)
    g.add_node("synthesize", synthesize)
    g.add_node("approval", approval_node)
    g.add_node("persist", persist)
    g.add_node("rejected", rejected)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "deterministic_tools")
    g.add_edge("deterministic_tools", "merch")
    g.add_edge("merch", "promo")
    g.add_edge("promo", "risk")
    g.add_edge("risk", "synthesize")
    g.add_conditional_edges("synthesize", route_after_synthesis, {"approval": "approval", "persist": "persist"})
    g.add_conditional_edges("approval", route_after_approval, {"persist": "persist", "rejected": "rejected"})
    g.add_edge("persist", END)
    g.add_edge("rejected", END)
    return g.compile(checkpointer=memory)

graph = build_graph()
