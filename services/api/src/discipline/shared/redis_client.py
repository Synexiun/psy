"""Shared Redis connection pool.

RQ (Redis Queue) uses the synchronous redis-py client.  This module provides
a lazily-initialized connection pool so the app and workers share the same
configuration.

For async Redis operations (caching, rate-limit counters), use aioredis or
redis.asyncio directly in the calling module.
"""

from __future__ import annotations

from typing import Any

import redis
from rq import Queue

from discipline.config import get_settings

_pool: redis.ConnectionPool | None = None


def get_redis_pool() -> redis.ConnectionPool:
    """Return the shared Redis connection pool (lazy singleton)."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = redis.ConnectionPool.from_url(settings.redis_url)
    return _pool


def get_redis_client() -> redis.Redis[Any]:
    """Return a Redis client bound to the shared pool."""
    return redis.Redis(connection_pool=get_redis_pool())


def get_queue(name: str = "default") -> Queue:
    """Return an RQ Queue backed by the shared Redis pool."""
    return Queue(name, connection=get_redis_client())


def reset_pool() -> None:
    """Close and clear the shared pool.

    Used in tests to ensure a fresh connection between test cases.
    """
    global _pool
    if _pool is not None:
        _pool.disconnect()
        _pool = None


__all__ = [
    "get_queue",
    "get_redis_client",
    "get_redis_pool",
    "reset_pool",
]
