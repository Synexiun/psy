"""Shared pytest fixtures.

Sets dummy values for all Settings-required env vars so tests that construct
the FastAPI app (via ``discipline.app.create_app``) can import without a real
``.env`` file.  These values are deliberately un-real — any test that ends up
calling Clerk, Stripe, S3, or the DB must use mocks or an integration harness.
"""

from __future__ import annotations

import os
from typing import Final

_TEST_ENV: Final[dict[str, str]] = {
    "DISCIPLINE_ENV": "dev",
    "LOG_LEVEL": "WARNING",
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
    "TIMESCALE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_ts",
    "REDIS_URL": "redis://localhost:6379/0",
    "S3_VOICE_BUCKET": "test-voice-bucket",
    "S3_EXPORT_BUCKET": "test-export-bucket",
    "KMS_KEY_ID": "test-kms-key",
    "CLERK_SECRET_KEY": "sk_test_placeholder",
    "CLERK_JWT_ISSUER": "https://example.clerk.accounts.test",
    "SERVER_SESSION_SECRET": "test-server-session-secret-not-for-prod",
    "ANTHROPIC_API_KEY": "sk-ant-test-placeholder",
    "STRIPE_SECRET_KEY": "sk_test_stripe_placeholder",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_placeholder",
    "AUDIT_CHAIN_SECRET": "test-audit-chain-secret-not-for-prod",
}

for _k, _v in _TEST_ENV.items():
    os.environ.setdefault(_k, _v)
