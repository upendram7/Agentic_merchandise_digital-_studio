from app.core.llm import chat_model, invoke_structured
from app.agents.prompts import RISK_PROMPT
from pydantic import BaseModel, Field

class RiskOutput(BaseModel):
    risk: str
    issues: list[str] = Field(default_factory=list)
    approval_recommended: bool


def run(request: dict, evidence: list[dict], agents: dict, tools: dict):
    model = chat_model().with_structured_output(RiskOutput)
    prompt = f"{RISK_PROMPT}\nRequest: {request}\nEvidence: {evidence}\nAgent outputs: {agents}\nDeterministic metrics: {tools}"
    return invoke_structured(model, prompt).model_dump()
