# syntax=docker/dockerfile:1.7
#
# Multi-stage build for the Discipline OS FastAPI backend.
# Base image: python:3.12-slim (Debian Bookworm slim).
# Package manager: uv (fast, reproducible, lockfile-pinned).
#
# Security notes:
#   - Final image runs as non-root user `apiuser` (UID 1000).
#   - No build tools (gcc, git) survive into the final stage.
#   - Image is scanned on push by ECR Scan + Snyk (see 08_Infrastructure_DevOps §17).

# ── Builder stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv into the builder — we only need it to produce the venv.
# Pin to a specific release for reproducibility; bump deliberately.
RUN pip install --no-cache-dir uv==0.4.29

# Copy lockfile and project metadata first so Docker can cache the
# dependency-install layer independently of source changes.
COPY pyproject.toml uv.lock ./

# Install production dependencies into an isolated venv under /build/.venv.
# --no-dev:  exclude test/lint extras
# --frozen:  fail if uv.lock is out of sync with pyproject.toml
RUN uv sync --no-dev --frozen

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the pre-built venv from the builder — no compiler toolchain needed here.
COPY --from=builder /build/.venv /app/.venv

# Add venv to PATH so `python` / `uvicorn` resolve without the full path.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application source.
COPY src/ ./src/

# Non-root user — matches the UID convention used across ECS task definitions.
RUN useradd --create-home --uid 1000 apiuser
USER apiuser

EXPOSE 8000

# Health check used by ECS ALB target group health checks.
# /health is a lightweight endpoint (no DB query) defined in discipline.app.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# 4 Uvicorn workers; gunicorn as process manager for graceful shutdown signals.
# Worker count can be overridden via ECS task definition environment variable.
CMD ["gunicorn", "discipline.app:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
