import pytest

from app.graph.workflow import retrieve


def test_retrieve_surfaces_embedding_failure_and_closes_database(monkeypatch):
    class FakeDatabase:
        closed = False

        def close(self):
            self.closed = True

    class FailingEmbeddings:
        def embed_query(self, _query):
            raise RuntimeError("embedding request failed")

    db = FakeDatabase()
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: db)
    monkeypatch.setattr("app.graph.workflow.embeddings", FailingEmbeddings)

    with pytest.raises(RuntimeError, match="embedding request failed"):
        retrieve(
            {
                "request": {
                    "category": "shoes",
                    "objective": "improve margins",
                    "store_cluster": "urban",
                }
            }
        )

    assert db.closed
