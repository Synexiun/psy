"""RQ worker entrypoint.

Usage::

    uv run python -m discipline.worker [--queue default] [--burst]

Or via the installed console script::

    discipline-worker --queue high --queue default
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

# Ensure src/ is on the path when run as a script.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discipline.shared.logging import configure_logging
from discipline.shared.redis_client import get_redis_client

# Import job modules so RQ can discover them.
from discipline.workers.audit_shipper import run_audit_shipper  # noqa: F401
from discipline.workers.report_generator import (  # noqa: F401
    generate_clinical_pdf,
    generate_enterprise_aggregate,
)
from discipline.workers.voice_purger import run_voice_purger  # noqa: F401


def main() -> int:
    parser = argparse.ArgumentParser(description="Discipline OS RQ worker")
    parser.add_argument(
        "--queue",
        action="append",
        default=[],
        help="Queue name(s) to listen on (default: default)",
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Run in burst mode (process jobs then exit)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level",
    )
    args = parser.parse_args()

    configure_logging(args.log_level)
    logging.getLogger(__name__).info(
        "Starting worker — queues=%s burst=%s",
        args.queue or ["default"],
        args.burst,
    )

    from rq import Worker

    queues = args.queue or ["default"]
    worker = Worker(queues, connection=get_redis_client())
    worker.work(burst=args.burst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
