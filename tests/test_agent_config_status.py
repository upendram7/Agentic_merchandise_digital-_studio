import httpx
import pytest
from openai import APIConnectionError, APIStatusError, AuthenticationError, NotFoundError, RateLimitError

from app.api import routes


def test_agent_config_status_reports_success(monkeypatch):
    class WorkingEmbeddings:
        def embed_query(self, _query):
            return [0.1, 0.2]

    monkeypatch.setattr(routes.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(routes, "embeddings", WorkingEmbeddings)

    assert routes.agent_config_status() == {
        "openai_api_problem": False,
        "api_key_problem": False,
        "network_error": False,
        "embedding_model_problem": False,
        "rate_limit": 0,
    }


def test_agent_config_status_reports_missing_api_key(monkeypatch):
    monkeypatch.setattr(routes.settings, "openai_api_key", "")

    assert routes.agent_config_status() == {
        "openai_api_problem": True,
        "api_key_problem": True,
        "network_error": False,
        "embedding_model_problem": False,
        "rate_limit": 0,
    }


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            AuthenticationError(
                "invalid key",
                response=httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com")),
                body=None,
            ),
            {"api_key_problem": True},
        ),
        (
            APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")),
            {"network_error": True},
        ),
        (
            NotFoundError(
                "model not found",
                response=httpx.Response(404, request=httpx.Request("POST", "https://api.openai.com")),
                body=None,
            ),
            {"embedding_model_problem": True},
        ),
        (
            RateLimitError(
                "rate limited",
                response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com")),
                body=None,
            ),
            {"rate_limit": 1},
        ),
        (
            APIStatusError(
                "rate limited",
                response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com")),
                body=None,
            ),
            {"rate_limit": 1},
        ),
    ],
)
def test_agent_config_status_classifies_embedding_failures(monkeypatch, error, expected):
    class FailingEmbeddings:
        def embed_query(self, _query):
            raise error

    monkeypatch.setattr(routes.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(routes, "embeddings", FailingEmbeddings)

    result = routes.agent_config_status()

    assert result["openai_api_problem"] is True
    for field, value in expected.items():
        assert result[field] == value
