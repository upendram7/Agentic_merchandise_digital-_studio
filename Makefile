install:
	pip install -r requirements.txt

db-up:
	docker compose up -d db

seed:
	python -m app.db.seed

run:
	uvicorn app.main:app --reload --port 8000

test:
	pytest -q

up:
	docker compose up --build

eval:
	python evals/run_eval.py
