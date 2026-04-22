"""Tests for ``discipline.shared.redis_client``.

Covers lazy pool initialization and the queue factory.
"""

from __future__ import annotations

from rq import Queue

from discipline.shared.redis_client import get_queue, get_redis_client, get_redis_pool, reset_pool


class TestGetRedisPool:
    def test_returns_connection_pool(self) -> None:
        pool = get_redis_pool()
        assert pool is not None

    def test_singleton_same_instance(self) -> None:
        p1 = get_redis_pool()
        p2 = get_redis_pool()
        assert p1 is p2


class TestGetRedisClient:
    def test_returns_redis_client(self) -> None:
        client = get_redis_client()
        assert client is not None


class TestGetQueue:
    def test_returns_rq_queue(self) -> None:
        queue = get_queue("default")
        assert isinstance(queue, Queue)
        assert queue.name == "default"

    def test_different_names(self) -> None:
        q1 = get_queue("high")
        q2 = get_queue("low")
        assert q1.name == "high"
        assert q2.name == "low"


class TestResetPool:
    def test_clears_pool(self) -> None:
        pool = get_redis_pool()
        reset_pool()
        new_pool = get_redis_pool()
        assert new_pool is not pool
