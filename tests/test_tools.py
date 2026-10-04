from app.tools.business import calculate_promotion_economics, inventory_coverage_days, approval_required
from app.tools.guardrails import validate_guardrails

def test_promotion_math():
    x = calculate_promotion_economics(100, 55, 10)
    assert x.margin_pct > 30
    assert x.revenue_lift_pct == 14

def test_inventory():
    assert inventory_coverage_days(100, 10) == 10

def test_approval_threshold():
    assert approval_required(15, 10, 20)[0] is True


def test_full_discount_does_not_divide_by_zero():
    result = calculate_promotion_economics(100, 55, 100)
    assert result.margin_pct == float("-inf")
    assert result.revenue_lift_pct == 140.0


def test_guardrail_failure():
    result = validate_guardrails(25, 20, 25, 20)
    assert not result.passed
    assert "discount_exceeds_max" in result.reasons
