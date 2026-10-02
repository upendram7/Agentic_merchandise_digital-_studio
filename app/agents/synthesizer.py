from app.core.llm import chat_model, invoke_structured
from app.agents.prompts import SYNTH_PROMPT
from app.api.schemas import DecisionOutput


def run(request: dict, evidence: list[dict], agents: dict, tools: dict, guardrails: dict):
    model = chat_model().with_structured_output(DecisionOutput)
    citations = [{"evidence_id": x["id"], "title": x["title"], "source_type": x["source_type"], "relevance": round(x.get("score", 0), 3)} for x in evidence]
    prompt = f"{SYNTH_PROMPT}\nRequest: {request}\nEvidence: {evidence}\nSpecialist outputs: {agents}\nTools: {tools}\nGuardrails: {guardrails}\nCitations available: {citations}"
    result = invoke_structured(model, prompt).model_dump()
    result["citations"] = citations
    result["guardrails_passed"] = bool(guardrails.get("passed"))
    return result
