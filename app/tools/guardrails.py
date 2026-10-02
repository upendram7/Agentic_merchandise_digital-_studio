from pydantic import BaseModel

class GuardrailResult(BaseModel):
    passed: bool
    reasons: list[str]


def validate_guardrails(discount_pct: float, margin_pct: float, min_margin_pct: float, max_discount_pct: float) -> GuardrailResult:
    reasons = []
    if discount_pct > max_discount_pct:
        reasons.append("discount_exceeds_max")
    if margin_pct < min_margin_pct:
        reasons.append("margin_below_minimum")
    return GuardrailResult(passed=not reasons, reasons=reasons)
