import pytest
from pydantic import ValidationError
from app.api.schemas import DecisionRequest

def test_request_validation():
    x = DecisionRequest(category="running shoes", objective="Improve margin", store_cluster="urban", requested_by="tester")
    assert x.constraints.max_discount_pct == 20

def test_extra_fields_rejected():
    with pytest.raises(ValidationError):
        DecisionRequest(category="x", objective="abcdef", store_cluster="urban", requested_by="tester", bad="x")
