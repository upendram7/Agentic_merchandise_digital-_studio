# Agentic Assortment & Promotion Decision Engine

Production-style reference implementation of a multi-agent retail decision system using LangGraph, hybrid RAG, deterministic Python tools, Pydantic validation, human approval, SQL persistence, tracing hooks, evaluation, and Docker.

## What it does

Given a product/category and business context, the workflow:

1. Validates the decision request.
2. Retrieves relevant product, policy, pricing, promotion and historical-performance evidence using hybrid lexical + vector retrieval.
3. Runs specialized agents:
   - **Merchandising Agent** – assortment recommendation.
   - **Promotion Agent** – promotion recommendation.
   - **Risk/Policy Agent** – policy and margin guardrails.
4. Runs deterministic calculators for margin, uplift, inventory coverage and promotion economics.
5. Synthesizes a structured decision with citations.
6. Routes high-risk / high-impact decisions to human approval.
7. Persists the decision, evidence, audit events and approval outcome.
8. Supports rollback of an approved decision before downstream execution.

This is intentionally an orchestration system, not a chatbot.

## Architecture

```text
                    +-----------------------+
                    |      FastAPI API      |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |   LangGraph Workflow   |
                    +-----------+-----------+
                                |
              +-----------------+------------------+
              |                 |                  |
              v                 v                  v
       Request Validator   Hybrid RAG        Deterministic Tools
                              |                  |
                       +------+-------+     +----+----------------+
                       |              |     | margin / uplift /  |
                    lexical        vector   | inventory / policy |
                       |              |     +---------------------+
                       +------+-------+
                              |
              +---------------+----------------+
              |                                |
              v                                v
      Merchandising Agent             Promotion Agent
              |                                |
              +---------------+----------------+
                              v
                       Risk / Policy Agent
                              |
                              v
                     Decision Synthesizer
                              |
                   +----------+-----------+
                   |                      |
                low risk               high risk
                   |                      |
                   v                      v
                Persist              Human Approval
                                          |
                                  +-------+-------+
                                  |               |
                               approve          reject
                                  |               |
                                  +-------+-------+
                                          v
                                     Persist/Audit
```

## Technology choices

- Python 3.12
- FastAPI + Uvicorn
- LangGraph for orchestration
- Pydantic v2 for contracts
- SQLAlchemy + PostgreSQL for application state/audit
- PostgreSQL full-text search + pgvector for hybrid retrieval
- OpenAI Responses API through `langchain-openai` (provider can be replaced)
- OpenTelemetry-compatible tracing hooks via LangChain/LangSmith environment variables
- Pytest for tests
- Docker Compose for local PostgreSQL/pgvector

OpenAI's current API direction is the Responses API; the legacy Assistants API was sunset in August 2026. See the migration documentation linked below. citehttps://platform.openai.com/docs/guides/migrate-to-responses

## Quick start

### 1. Start PostgreSQL + pgvector

```bash
docker compose up -d db
```

### 2. Create environment

```bash
cp .env.example .env
# set OPENAI_API_KEY
```

### 3. Install

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Seed demo data

```bash
python -m app.db.seed
```

### 5. Build vector embeddings

After seeding, with `OPENAI_API_KEY` configured:

```bash
python -m app.db.ingest
```

The API initializes LangGraph's PostgreSQL checkpoint tables during startup. Configure
`DATABASE_URL` to a persistent PostgreSQL database; approval interrupts are resumed
from these checkpoints, so in-process memory is not sufficient for serverless deploys.

### 6. Run API

```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` for the decision desk or `http://localhost:8000/docs` for API docs.

### Check agent configuration

The endpoint runs a small embedding request against the configured OpenAI embedding model.
It returns booleans for API, API key, network, and embedding-model problems, plus `rate_limit`
as `0` or `1` for the probe:

```bash
curl http://localhost:8000/v1/agentConfigStatus
```

### 7. Submit a decision

```bash
curl -X POST http://localhost:8000/v1/decisions \\
  -H "Content-Type: application/json" \\
  -d '{
    "category":"running shoes",
    "objective":"Improve gross margin without materially reducing unit sales",
    "store_cluster":"urban-premium",
    "horizon_days":30,
    "requested_by":"demo-user",
    "constraints":{"max_discount_pct":20,"min_margin_pct":25}
  }'
```

If approval is required, the response contains an `approval_id`. Approve/reject with:

```bash
curl -X POST http://localhost:8000/v1/approvals/<approval_id> \\
  -H "Content-Type: application/json" \\
  -d '{"approved":true,"approver":"merch-manager","comment":"Approved for pilot"}'
```

## Production hardening

Before production:

- monitor and size the PostgreSQL connection pool used by LangGraph's PostgreSQL checkpointer;
- use managed PostgreSQL + pgvector;
- move secrets to a cloud secret manager;
- enable OpenTelemetry/LangSmith tracing and PII redaction;
- add OAuth/OIDC/JWT and role-based approval policies;
- replace demo execution/rollback with the retailer's promotion and assortment APIs;
- add model gateway, rate limiting and circuit breakers;
- pin dependency versions after internal compatibility testing;
- add CI/CD, image scanning, SAST/DAST and dependency scanning;
- add offline evaluation datasets and regression gates;
- add a dedicated execution adapter with idempotency keys and a compensating-action rollback API;
- add a conversation/session table if users need multi-turn decision refinement.

### Evaluation

Run the deterministic retrieval smoke suite with `make eval`. The `evals/` folder is deliberately small; expand it into a versioned golden set with expected citations, guardrail outcomes and approval-routing labels.

### Observability

Set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT` to trace graph and LLM calls. The database audit table remains the business audit trail; tracing is operational telemetry, not the system of record.

### Recommended production regression dimensions: retrieval recall@k, citation support rate, structured-output validity, policy-violation rate, approval-routing accuracy, tool-calculation correctness, hallucination rate, latency and token cost.

## Repository structure

```text
app/
  agents/       specialized agents
  api/          FastAPI routes + schemas
  core/         configuration + LLM factory
  db/           SQLAlchemy models + seed
  graph/        LangGraph state and workflow
  rag/          hybrid retriever
  tools/        deterministic business tools
  main.py

data/          demo policy/product/evidence data

tests/          unit + workflow tests
Dockerfile
docker-compose.yml
requirements.txt
.env.example
```
