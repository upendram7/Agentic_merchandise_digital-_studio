from app.db.session import init_db, SessionLocal
from app.db.models import Evidence

def main():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Evidence).count():
            print("Evidence already seeded")
            return
        rows = [
            ("policy", "POL-001", "Promotion margin policy", "Promotions must maintain at least 25% gross margin unless a category VP explicitly approves an exception.", {"category":"all"}),
            ("policy", "POL-002", "Markdown policy", "Markdowns above 20% require human approval and a documented commercial rationale.", {"category":"all"}),
            ("product", "SKU-RUN-001", "Performance running shoe", "Premium running shoe with strong urban-premium store demand and a standard list price of 100.", {"category":"running shoes"}),
            ("performance", "PERF-RUN-001", "Running shoe performance", "Urban-premium stores historically show higher unit velocity for premium running shoes during promotional periods.", {"category":"running shoes"}),
            ("assortment", "ASSORT-RUN-001", "Running assortment guideline", "Keep core sizes in stock; reduce long-tail sizes only when inventory coverage exceeds 45 days.", {"category":"running shoes"}),
            ("promotion", "PROMO-RUN-001", "Targeted promotion guidance", "Targeted promotions are preferred over blanket markdowns when demand response differs materially by store cluster.", {"category":"running shoes"}),
        ]
        for source_type, key, title, content, meta in rows:
            db.add(Evidence(source_type=source_type, source_key=key, title=title, content=content, metadata_json=meta))
        db.commit()
        print("Seeded demo evidence")
    finally:
        db.close()

if __name__ == "__main__":
    main()
