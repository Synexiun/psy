#!/usr/bin/env bash
# Bootstrap the monorepo for local development.
# Idempotent — safe to run multiple times.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Checking required tools"
command -v node >/dev/null || { echo "Install Node 20+"; exit 1; }
command -v pnpm >/dev/null || { echo "Install pnpm 9+ (corepack enable pnpm)"; exit 1; }
command -v python3 >/dev/null || command -v python >/dev/null || { echo "Install Python 3.12+"; exit 1; }
command -v docker >/dev/null || { echo "Install Docker Desktop"; exit 1; }

echo "==> Installing pnpm workspace dependencies"
pnpm install

echo "==> Setting up API virtual env (services/api)"
cd "$ROOT/services/api"
if command -v uv >/dev/null; then
  uv sync
else
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -e ".[dev]"
fi

echo "==> Copying .env if missing"
[ -f .env ] || cp .env.example .env

cd "$ROOT"
echo "==> Starting local infra (postgres, timescale, redis, localstack, otel)"
docker compose up -d

echo ""
echo "Done. Next steps:"
echo "  cd services/api && uv run alembic upgrade head"
echo "  cd services/api && uv run uvicorn discipline.app:app --reload"
echo "  cd apps/mobile  && pnpm exec expo start"
