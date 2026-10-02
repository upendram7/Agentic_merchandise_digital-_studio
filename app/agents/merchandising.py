from app.core.llm import chat_model, invoke_structured
from app.agents.prompts import MERCH_PROMPT
from app.api.schemas import AssortmentRecommendation


def run(request: dict, evidence: list[dict], tools: dict):
    model = chat_model().with_structured_output(AssortmentRecommendation)
    prompt = f"{MERCH_PROMPT}\nRequest: {request}\nEvidence: {evidence}\nDeterministic metrics: {tools}"
    return invoke_structured(model, prompt).model_dump()
