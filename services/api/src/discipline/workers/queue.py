"""RQ queue helpers.

Provides a thin async wrapper around RQ's synchronous ``Queue.enqueue``
so FastAPI routes don't block the event loop.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from discipline.shared.redis_client import get_queue

if TYPE_CHECKING:
    from rq import Queue
    from rq.job import Job


def get_worker_queue(name: str = "default") -> Queue:
    """Return an RQ Queue by name."""
    return get_queue(name)


async def enqueue_job(
    queue_name: str,
    func: Any,
    *args: Any,
    **kwargs: Any,
) -> Job:
    """Enqueue a background job asynchronously.

    Runs the blocking ``Queue.enqueue`` call in a thread pool so the
    event loop stays unblocked.
    """
    queue = get_worker_queue(queue_name)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: queue.enqueue(func, *args, **kwargs),
    )


__all__ = [
    "enqueue_job",
    "get_worker_queue",
]
