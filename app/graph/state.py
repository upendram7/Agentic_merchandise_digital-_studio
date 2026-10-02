from typing import TypedDict, Any

class DecisionState(TypedDict, total=False):
    decision_id: str
    request: dict
    evidence: list[dict]
    tool_results: dict[str, Any]
    agent_outputs: dict[str, Any]
    final: dict
    approval_id: str | None
    approval_status: str | None
    errors: list[str]
    retry_count: int
