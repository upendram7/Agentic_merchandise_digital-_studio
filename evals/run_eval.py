"""Offline smoke evaluation for retrieval/policy behavior.
Run after DB seed; embeddings are optional because lexical retrieval is evaluated here.
"""
import json
from app.db.session import init_db, SessionLocal
from app.rag.retriever import hybrid_search


def main():
    init_db()
    cases = json.load(open("evals/cases.json"))
    db = SessionLocal()
    try:
        passed = 0
        for case in cases:
            q = f"{case['category']} {case['objective']} {case['store_cluster']}"
            results = hybrid_search(db, q, None, limit=6)
            corpus = " ".join(r["content"].lower() for r in results)
            hit = all(term.lower() in corpus for term in case["expected_policy_terms"])
            print(f"{case['name']}: {'PASS' if hit else 'FAIL'}")
            passed += int(hit)
        print(f"score={passed}/{len(cases)}")
        raise SystemExit(0 if passed == len(cases) else 1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
