from pydantic import BaseModel, Field

class PromotionEconomics(BaseModel):
    list_price: float = Field(gt=0)
    cost: float = Field(gt=0)
    discount_pct: float = Field(ge=0, le=100)
    margin_pct: float
    revenue_lift_pct: float
    margin_delta_pct: float


def calculate_promotion_economics(list_price: float, cost: float, discount_pct: float, baseline_units: float = 100.0, elasticity: float = 1.4) -> PromotionEconomics:
    if list_price <= 0:
        raise ValueError("list_price must be greater than zero")
    if cost <= 0:
        raise ValueError("cost must be greater than zero")
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount_pct must be between 0 and 100")

    baseline_margin = (list_price - cost) / list_price * 100
    price = list_price * (1 - discount_pct / 100)
    if price <= 0:
        margin = float("-inf")
    else:
        margin = (price - cost) / price * 100
    revenue_lift = max(0.0, discount_pct * elasticity)
    margin_delta = margin - baseline_margin
    return PromotionEconomics(
        list_price=list_price,
        cost=cost,
        discount_pct=discount_pct,
        margin_pct=round(margin, 2) if margin != float("-inf") else float("-inf"),
        revenue_lift_pct=round(revenue_lift, 2),
        margin_delta_pct=round(margin_delta, 2) if margin_delta != float("-inf") else float("-inf"),
    )


def inventory_coverage_days(on_hand: float, avg_daily_units: float) -> float:
    if avg_daily_units <= 0:
        return 999.0
    return round(on_hand / avg_daily_units, 2)


def approval_required(expected_revenue_lift_pct: float, discount_pct: float, max_discount_pct: float) -> tuple[bool, str | None]:
    if discount_pct > max_discount_pct:
        return True, "Requested discount exceeds configured business constraint."
    if expected_revenue_lift_pct >= 15:
        return True, "Expected commercial impact is above the human-approval threshold."
    return False, None
