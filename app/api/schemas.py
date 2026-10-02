from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Constraints(BaseModel):
    max_discount_pct: float = Field(20, ge=0, le=100)
    min_margin_pct: float = Field(25, ge=0, le=100)
    min_inventory_days: float = Field(7, ge=0)

class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: str = Field(min_length=2, max_length=120)
    objective: str = Field(min_length=5, max_length=1000)
    store_cluster: str = Field(min_length=2, max_length=100)
    horizon_days: int = Field(30, ge=7, le=365)
    requested_by: str = Field(min_length=2, max_length=200)
    constraints: Constraints = Constraints()

class ApprovalRequest(BaseModel):
    approved: bool
    approver: str = Field(min_length=2, max_length=200)
    comment: str | None = Field(default=None, max_length=1000)

class Citation(BaseModel):
    evidence_id: int
    title: str
    source_type: str
    relevance: float

class AssortmentRecommendation(BaseModel):
    action: Literal["ADD", "KEEP", "REDUCE", "REMOVE"]
    rationale: str
    expected_unit_lift_pct: float
    risk: Literal["LOW", "MEDIUM", "HIGH"]

class PromotionRecommendation(BaseModel):
    action: Literal["NO_PROMO", "MARKDOWN", "BUNDLE", "TARGETED_PROMO"]
    discount_pct: float = Field(ge=0, le=100)
    expected_margin_pct: float
    rationale: str
    risk: Literal["LOW", "MEDIUM", "HIGH"]

class DecisionOutput(BaseModel):
    recommendation: str
    assortment: AssortmentRecommendation
    promotion: PromotionRecommendation
    expected_revenue_lift_pct: float
    expected_margin_delta_pct: float
    requires_human_approval: bool
    approval_reason: str | None = None
    citations: list[Citation]
    guardrails_passed: bool


class RollbackRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=200)
    reason: str = Field(min_length=5, max_length=1000)
