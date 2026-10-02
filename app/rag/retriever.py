from sqlalchemy import select, func, or_
from app.db.models import Evidence


def lexical_search(db, query: str, limit: int = 8):
    terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 2][:8]
    if not terms:
        return []
    conditions = [func.lower(Evidence.content).contains(t) for t in terms]
    rows = db.execute(select(Evidence).where(or_(*conditions)).limit(limit)).scalars().all()
    return [{"id": r.id, "title": r.title, "content": r.content, "source_type": r.source_type, "metadata": r.metadata_json, "lexical_score": 1.0} for r in rows]


def vector_search(db, query_vector: list[float], limit: int = 8):
    distance = Evidence.embedding.cosine_distance(query_vector)
    rows = db.execute(select(Evidence, distance.label("distance")).where(Evidence.embedding.is_not(None)).order_by(distance).limit(limit)).all()
    return [{"id": r.Evidence.id, "title": r.Evidence.title, "content": r.Evidence.content, "source_type": r.Evidence.source_type, "metadata": r.Evidence.metadata_json, "vector_score": max(0.0, 1.0 - float(r.distance))} for r in rows]


def hybrid_search(db, query: str, query_vector: list[float] | None = None, limit: int = 6):
    lexical = lexical_search(db, query, limit=12)
    try:
        vector = vector_search(db, query_vector, limit=12) if query_vector else []
    except Exception:
        vector = []
    merged = {}
    for item in lexical:
        merged[item["id"]] = {**item, "score": 0.45 * item.get("lexical_score", 0)}
    for item in vector:
        if item["id"] not in merged:
            merged[item["id"]] = {**item, "score": 0.55 * item.get("vector_score", 0)}
        else:
            merged[item["id"]].update(item)
            merged[item["id"]]["score"] += 0.55 * item.get("vector_score", 0)
    return sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:limit]
