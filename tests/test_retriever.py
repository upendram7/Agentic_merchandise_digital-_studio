import pytest

from app.rag import retriever


def test_hybrid_search_surfaces_vector_search_failure(monkeypatch):
    def fail_vector_search(_db, _query_vector, limit=8):
        raise RuntimeError("vector search failed")

    monkeypatch.setattr(retriever, "lexical_search", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(retriever, "vector_search", fail_vector_search)

    with pytest.raises(RuntimeError, match="vector search failed"):
        retriever.hybrid_search(None, "running shoes", [0.1, 0.2])
