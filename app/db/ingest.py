from app.db.session import init_db, SessionLocal
from app.db.models import Evidence
from app.core.llm import embeddings

def main():
    init_db()
    db = SessionLocal()
    try:
        rows = db.query(Evidence).filter(Evidence.embedding.is_(None)).all()
        if not rows:
            print("No evidence requires embedding")
            return
        emb = embeddings()
        vectors = emb.embed_documents([r.content for r in rows])
        for row, vector in zip(rows, vectors):
            row.embedding = vector
        db.commit()
        print(f"Embedded {len(rows)} evidence records")
    finally:
        db.close()

if __name__ == "__main__":
    main()
