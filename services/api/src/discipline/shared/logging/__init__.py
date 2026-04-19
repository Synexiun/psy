"""Structured logging — stream-aware.

Re-exports the core primitives so `from discipline.shared.logging import configure_logging`
keeps working.  Stream-specific sinks live in `discipline.shared.logging.streams`.
See Docs/Technicals/14_Authentication_Logging.md §4 for the four-stream architecture
(app / audit / safety / security).
"""

from __future__ import annotations

import logging
import sys

import structlog

from .streams import (
    GENESIS_SENTINEL,
    LogStream,
    compute_chain_hash,
    get_stream_logger,
    reset_chain_state,
    verify_chain,
)


def configure_logging(level: str = "INFO") -> None:
    """Configure JSON structured logging for the ``app`` stream.

    The other three streams (audit / safety / security) are configured lazily via
    :func:`get_stream_logger`, each with its own sink, IAM boundary, and retention.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level.upper(),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Convenience — returns the application-stream logger for the given module."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]


__all__ = [
    "GENESIS_SENTINEL",
    "LogStream",
    "compute_chain_hash",
    "configure_logging",
    "get_logger",
    "get_stream_logger",
    "reset_chain_state",
    "verify_chain",
]
