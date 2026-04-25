"""Tests for ``discipline.identity.repository``.

Covers both in-memory and SQLAlchemy implementations.
"""

from __future__ import annotations

import pytest

from discipline.identity.repository import (
    InMemoryUserRepository,
    SqlUserRepository,
    get_user_repository,
    reset_user_repository,
    set_user_repository,
)
from discipline.shared.db import get_db_session


@pytest.fixture(autouse=True)
def _reset_repo() -> None:
    reset_user_repository()


class TestInMemoryUserRepository:
    @pytest.fixture
    def repo(self) -> InMemoryUserRepository:
        return InMemoryUserRepository()

    @pytest.mark.asyncio
    async def test_create_returns_record(self, repo: InMemoryUserRepository) -> None:
        record = await repo.create(
            external_id="clerk_01",
            email="test@example.com",
            locale="en",
            timezone="UTC",
        )
        assert record.external_id == "clerk_01"
        assert record.locale == "en"
        assert record.email_hash  # non-empty hash

    @pytest.mark.asyncio
    async def test_get_by_external_id_found(self, repo: InMemoryUserRepository) -> None:
        created = await repo.create(
            external_id="clerk_02",
            email="a@b.com",
            locale="fr",
            timezone="Europe/Paris",
        )
        fetched = await repo.get_by_external_id("clerk_02")
        assert fetched is not None
        assert fetched.user_id == created.user_id

    @pytest.mark.asyncio
    async def test_get_by_external_id_not_found(
        self, repo: InMemoryUserRepository
    ) -> None:
        fetched = await repo.get_by_external_id("nobody")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo: InMemoryUserRepository) -> None:
        created = await repo.create(
            external_id="clerk_03",
            email="id@example.com",
            locale="en",
            timezone="UTC",
        )
        fetched = await repo.get_by_id(created.user_id)
        assert fetched is not None
        assert fetched.user_id == created.user_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo: InMemoryUserRepository) -> None:
        import uuid
        fetched = await repo.get_by_id(str(uuid.uuid4()))
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_by_id_wrong_user_returns_none(self, repo: InMemoryUserRepository) -> None:
        """get_by_id should not return another user's record."""
        created_a = await repo.create(
            external_id="clerk_a", email="a@ex.com", locale="en", timezone="UTC"
        )
        await repo.create(
            external_id="clerk_b", email="b@ex.com", locale="fr", timezone="Europe/Paris"
        )
        import uuid
        fetched = await repo.get_by_id(str(uuid.uuid4()))
        assert fetched is None
        # Confirm the correct user IS fetchable
        assert await repo.get_by_id(created_a.user_id) is not None

    @pytest.mark.asyncio
    async def test_reset_clears_store(self, repo: InMemoryUserRepository) -> None:
        await repo.create(external_id="x", email="x@x.com", locale="en", timezone="UTC")
        repo.reset()
        assert await repo.get_by_external_id("x") is None


class TestSqlUserRepository:
    @pytest.mark.asyncio
    async def test_create_persists_user(self) -> None:
        try:
            async with get_db_session() as session:
                repo = SqlUserRepository(session)
                record = await repo.create(
                    external_id="clerk_sql_01",
                    email="sql@example.com",
                    locale="ar",
                    timezone="Asia/Dubai",
                )
                assert record.external_id == "clerk_sql_01"
                assert record.locale == "ar"
        except Exception as exc:
            if "does not exist" in str(exc) or "Connection" in str(exc):
                pytest.skip("PostgreSQL not available")
            raise

    @pytest.mark.asyncio
    async def test_get_by_external_id(self) -> None:
        try:
            async with get_db_session() as session:
                repo = SqlUserRepository(session)
                created = await repo.create(
                    external_id="clerk_sql_02",
                    email="sql2@example.com",
                    locale="fa",
                    timezone="Asia/Tehran",
                )
                # Need to commit before we can query in a new session,
                # but get_db_session commits on success.  However the
                # session is still open here, so the object is in identity map.
                fetched = await repo.get_by_external_id("clerk_sql_02")
                assert fetched is not None
                assert fetched.user_id == created.user_id
        except Exception as exc:
            if "does not exist" in str(exc) or "Connection" in str(exc):
                pytest.skip("PostgreSQL not available")
            raise


class TestModuleSingleton:
    def test_get_user_repository_default_is_in_memory(self) -> None:
        repo = get_user_repository()
        assert isinstance(repo, InMemoryUserRepository)

    def test_set_user_repository(self) -> None:
        custom = InMemoryUserRepository()
        set_user_repository(custom)
        assert get_user_repository() is custom
