# API — Discipline OS

FastAPI modular monolith. Single deployable, strict internal module boundaries.

See `Docs/Technicals/05_Backend_Services.md` for the full architecture.

## Stack

- **Python 3.12+**
- **FastAPI** with Pydantic v2
- **asyncpg** for DB access (no ORM in hot paths)
- **SQLAlchemy Core** for migration modeling + Alembic
- **Redis 7** for cache, rate limiting, worker queues
- **RQ** for background jobs
- **OpenTelemetry** for tracing

## Module layout (target)

```
src/discipline/
├── app.py                     FastAPI factory + router mount
├── config/                    Settings, env
├── shared/                    Logging, tracing, db, kms, http
├── identity/                  Users, auth, devices
├── billing/                   Subscriptions, Stripe, IAP
├── signal/                    Signal ingest, aggregation, state
├── intervention/              Urge lifecycle, bandit, tools
├── clinical/                  Relapse, AVE, abstinence policy
├── memory/                    Journals, voice, embeddings, search
├── pattern/                   Pattern miner, insights
├── resilience/                Streak state machine
├── enterprise/                Org admin, clinician links
├── compliance/                Audit logs, consent, retention
├── ml/                        Model serving, registry
├── llm/                       Anthropic client, prompt library
├── notifications/             Push, nudges, scheduler
├── exports/                   Data export builder
└── workers/                   Background jobs
```

Each module owns its DB tables. Cross-module calls must go through typed service interfaces in `<module>/service.py` — never raw DB access from outside the module. A CI lint rule enforces this.

## Running locally

```bash
# Install with uv (recommended) or pip
uv sync

# Copy env template
cp .env.example .env

# Start the local stack: Postgres + Redis + localstack S3
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Start API
uv run uvicorn discipline.app:app --reload --port 8000

# Start workers (separate terminal)
uv run rq worker --with-scheduler
```

## Test

```bash
uv run pytest -q                    # unit
uv run pytest -q tests/integration  # integration (requires docker compose)
uv run ruff check .                 # lint
uv run mypy src                     # typecheck
```

## Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "add_streak_state"

# Apply
uv run alembic upgrade head

# Rollback one
uv run alembic downgrade -1
```

All migrations require both `up` and `down`. Destructive migrations (drop column / drop table) require a two-step ship: deprecation PR, then removal PR ≥14 days later.

## Coverage bar

- Overall: 80%
- `intervention`, `clinical`, `resilience`, `compliance`: 95%
- T3 (SOS) path: 100% branch coverage

See `Docs/Technicals/09_Testing_QA.md` for the full testing strategy.
