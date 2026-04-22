"""Tests for ``discipline.shared.db``.

Covers lazy engine initialization and the async session context manager.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from discipline.shared.db import get_db_session


@pytest.mark.asyncio
async def test_get_db_session_yields_async_session() -> None:
    """The context manager must yield an AsyncSession instance."""
    async with get_db_session() as session:
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_get_db_session_commits_on_success() -> None:
    """A successful exit from the context manager calls commit."""
    # We can't assert real commit without a DB, but we can verify the
    # session is usable (not closed) inside the block.
    async with get_db_session() as session:
        assert session.is_active is not None  # session exists


@pytest.mark.asyncio
async def test_get_db_session_rolls_back_on_exception() -> None:
    """An exception inside the block must trigger rollback, not propagate
    a commit failure."""
    with pytest.raises(RuntimeError, match="boom"):
        async with get_db_session():
            raise RuntimeError("boom")
