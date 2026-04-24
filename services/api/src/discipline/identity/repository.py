"""Identity repository — user lookup and upsert.

Provides both an in-memory stub (for tests and pre-DB dev) and an
async SQLAlchemy implementation (for production).  The interface is
stable so callers don't change when the backend swaps.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discipline.identity.models import User


@dataclass(frozen=True, slots=True)
class UserRecord:
    """Plain data object returned by the repository."""

    user_id: str
    external_id: str
    email_hash: str
    locale: str
    timezone: str
    created_at: str | None = None


class UserRepository(Protocol):
    """Protocol for user storage backends."""

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        ...

    async def get_by_external_id(self, external_id: str) -> UserRecord | None:
        ...

    async def create(
        self,
        *,
        external_id: str,
        email: str | None,
        locale: str,
        timezone: str,
    ) -> UserRecord:
        ...


# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


class InMemoryUserRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}  # keyed by external_id
        self._users_by_id: dict[str, UserRecord] = {}  # keyed by user_id

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._users_by_id.get(user_id)

    async def get_by_external_id(self, external_id: str) -> UserRecord | None:
        return self._users.get(external_id)

    async def create(
        self,
        *,
        external_id: str,
        email: str | None,
        locale: str,
        timezone: str,
    ) -> UserRecord:
        email_hash = _hash_email(email or "")
        record = UserRecord(
            user_id=f"user_{external_id}",
            external_id=external_id,
            email_hash=email_hash,
            locale=locale,
            timezone=timezone,
        )
        self._users[external_id] = record
        self._users_by_id[record.user_id] = record
        return record

    def reset(self) -> None:
        self._users.clear()
        self._users_by_id.clear()


# ---------------------------------------------------------------------------
# SQLAlchemy async implementation
# ---------------------------------------------------------------------------


class SqlUserRepository:
    """PostgreSQL-backed user repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _user_to_record(row)

    async def get_by_external_id(self, external_id: str) -> UserRecord | None:
        result = await self._session.execute(
            select(User).where(User.external_id == external_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _user_to_record(row)

    async def create(
        self,
        *,
        external_id: str,
        email: str | None,
        locale: str,
        timezone: str,
    ) -> UserRecord:
        email_hash = _hash_email(email or "")
        # email_encrypted is a placeholder until KMS wiring lands.
        user = User(
            external_id=external_id,
            email_hash=email_hash,
            email_encrypted="placeholder",
            locale=locale,
            timezone=timezone,
        )
        self._session.add(user)
        await self._session.flush()
        return _user_to_record(user)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.encode("utf-8")).hexdigest()


def _user_to_record(user: User) -> UserRecord:
    return UserRecord(
        user_id=str(user.id),
        external_id=user.external_id,
        email_hash=user.email_hash,
        locale=user.locale,
        timezone=user.timezone,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


# ---------------------------------------------------------------------------
# Module-level singleton (default: in-memory)
# ---------------------------------------------------------------------------

_default_repo: UserRepository | None = None


def get_user_repository() -> UserRepository:
    global _default_repo
    if _default_repo is None:
        _default_repo = InMemoryUserRepository()
    return _default_repo


def set_user_repository(repo: UserRepository) -> None:
    global _default_repo
    _default_repo = repo


def reset_user_repository() -> None:
    global _default_repo
    if isinstance(_default_repo, InMemoryUserRepository):
        _default_repo.reset()
    _default_repo = None


__all__ = [
    "InMemoryUserRepository",
    "SqlUserRepository",
    "UserRecord",
    "UserRepository",
    "get_user_repository",
    "reset_user_repository",
    "set_user_repository",
]
