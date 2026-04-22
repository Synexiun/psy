"""Async database layer.

Thin SQLAlchemy Core wrapper for Alembic migrations and module-level schema
modeling.  Hot-path queries use asyncpg directly (see 05_Backend_Services §6.1).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

# Lazy singleton — engine is created on first access so module import
# does not require env vars to be present (important for tests and
# tooling that import the package without a full environment).
_engine = None
_SessionLocal = None


def _get_engine() -> Any:
    global _engine
    if _engine is None:
        from discipline.config import get_settings

        _engine = create_async_engine(
            get_settings().database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_local() -> Any:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _SessionLocal


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an async SQLAlchemy session.

    Intended for use as a FastAPI dependency::

        from fastapi import Depends
        from discipline.shared.db import get_db_session

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)): ...
    """
    async with _get_session_local()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "get_db_session",
]
