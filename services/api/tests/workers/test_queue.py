"""Tests for ``discipline.workers.queue``.

Uses mocked RQ Queue so no Redis connection is required.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from discipline.workers.queue import enqueue_job, get_worker_queue


def dummy_task(x: int) -> int:
    return x * 2


class TestGetWorkerQueue:
    @patch("discipline.workers.queue.get_queue")
    def test_delegates_to_get_queue(self, mock_get_queue: Any) -> None:
        mock_q = MagicMock()
        mock_get_queue.return_value = mock_q
        q = get_worker_queue("high")
        mock_get_queue.assert_called_once_with("high")
        assert q is mock_q


class TestEnqueueJob:
    @patch("discipline.workers.queue.get_queue")
    async def test_enqueues_job_async(self, mock_get_queue: Any) -> None:
        mock_q = MagicMock()
        mock_job = MagicMock()
        mock_q.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_q

        job = await enqueue_job("default", dummy_task, 5)

        mock_get_queue.assert_called_once_with("default")
        mock_q.enqueue.assert_called_once_with(dummy_task, 5)
        assert job is mock_job

    @patch("discipline.workers.queue.get_queue")
    async def test_enqueues_with_kwargs(self, mock_get_queue: Any) -> None:
        mock_q = MagicMock()
        mock_job = MagicMock()
        mock_q.enqueue.return_value = mock_job
        mock_get_queue.return_value = mock_q

        job = await enqueue_job("default", dummy_task, 5, foo="bar")

        call_args = mock_q.enqueue.call_args
        assert call_args.args == (dummy_task, 5)
        assert call_args.kwargs == {"foo": "bar"}
        assert job is mock_job
