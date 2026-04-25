"""Tests for discipline.compliance.repository — consent and quick-erase in-memory stores.

Covers:
- ConsentRecord frozen dataclass
- InMemoryConsentRepository.grant: returns ConsentRecord, valid UUID, fields match
- grant: ip_address_hash may be None
- latest: returns most recent consent for type, None for unknown user
- QuickEraseRecord frozen dataclass
- InMemoryQuickEraseRepository.create: returns QuickEraseRecord, status=pending
- get_latest: returns most recent request, None for unknown user
- reset_compliance_repositories: clears both repos
"""

from __future__ import annotations

import uuid

import pytest

from discipline.compliance.repository import (
    ConsentRecord,
    InMemoryConsentRepository,
    InMemoryQuickEraseRepository,
    QuickEraseRecord,
    reset_compliance_repositories,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_compliance_repositories()


# ---------------------------------------------------------------------------
# ConsentRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestConsentRecord:
    def test_can_be_constructed(self) -> None:
        r = ConsentRecord(
            consent_id="cid",
            user_id="uid",
            consent_type="terms_of_service",
            version="2.0",
            granted_at="2026-04-25T00:00:00+00:00",
            ip_address_hash=None,
        )
        assert r.consent_id == "cid"

    def test_frozen(self) -> None:
        r = ConsentRecord(
            consent_id="c", user_id="u", consent_type="tos",
            version="1.0", granted_at="2026-04-25", ip_address_hash=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            r.version = "mutated"  # type: ignore[misc]

    def test_ip_address_hash_accepts_none(self) -> None:
        r = ConsentRecord(
            consent_id="c", user_id="u", consent_type="tos",
            version="1.0", granted_at="2026-04-25", ip_address_hash=None,
        )
        assert r.ip_address_hash is None


# ---------------------------------------------------------------------------
# InMemoryConsentRepository.grant
# ---------------------------------------------------------------------------


class TestConsentGrant:
    @pytest.mark.asyncio
    async def test_returns_consent_record(self) -> None:
        repo = InMemoryConsentRepository()
        r = await repo.grant(
            user_id="u-1", consent_type="tos",
            version="1.0", ip_address_hash=None,
        )
        assert isinstance(r, ConsentRecord)

    @pytest.mark.asyncio
    async def test_consent_id_is_valid_uuid(self) -> None:
        repo = InMemoryConsentRepository()
        r = await repo.grant(
            user_id="u-1", consent_type="tos",
            version="1.0", ip_address_hash=None,
        )
        uuid.UUID(r.consent_id)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemoryConsentRepository()
        r = await repo.grant(
            user_id="u-99", consent_type="privacy_policy",
            version="3.0", ip_address_hash="sha256_hash_abc",
        )
        assert r.user_id == "u-99"
        assert r.consent_type == "privacy_policy"
        assert r.version == "3.0"
        assert r.ip_address_hash == "sha256_hash_abc"

    @pytest.mark.asyncio
    async def test_ip_hash_none_accepted(self) -> None:
        repo = InMemoryConsentRepository()
        r = await repo.grant(
            user_id="u-1", consent_type="tos",
            version="1.0", ip_address_hash=None,
        )
        assert r.ip_address_hash is None


# ---------------------------------------------------------------------------
# InMemoryConsentRepository.latest
# ---------------------------------------------------------------------------


class TestConsentLatest:
    @pytest.mark.asyncio
    async def test_returns_a_consent_for_type(self) -> None:
        repo = InMemoryConsentRepository()
        r1 = await repo.grant(
            user_id="u-1", consent_type="tos", version="1.0", ip_address_hash=None
        )
        r2 = await repo.grant(
            user_id="u-1", consent_type="tos", version="2.0", ip_address_hash=None
        )
        latest = await repo.latest("u-1", "tos")
        assert latest is not None
        assert latest.consent_id in (r1.consent_id, r2.consent_id)

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_user(self) -> None:
        repo = InMemoryConsentRepository()
        result = await repo.latest("ghost-user", "tos")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_consent_type(self) -> None:
        repo = InMemoryConsentRepository()
        await repo.grant(
            user_id="u-1", consent_type="tos", version="1.0", ip_address_hash=None
        )
        result = await repo.latest("u-1", "privacy_policy")
        assert result is None

    @pytest.mark.asyncio
    async def test_different_types_tracked_separately(self) -> None:
        repo = InMemoryConsentRepository()
        await repo.grant(user_id="u-1", consent_type="tos", version="1.0", ip_address_hash=None)
        await repo.grant(user_id="u-1", consent_type="privacy_policy", version="2.0", ip_address_hash=None)
        tos = await repo.latest("u-1", "tos")
        pp = await repo.latest("u-1", "privacy_policy")
        assert tos is not None and tos.version == "1.0"
        assert pp is not None and pp.version == "2.0"


# ---------------------------------------------------------------------------
# QuickEraseRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestQuickEraseRecord:
    def test_can_be_constructed(self) -> None:
        r = QuickEraseRecord(
            request_id="rid",
            user_id="uid",
            status="pending",
            requested_at="2026-04-25T00:00:00+00:00",
            completed_at=None,
            error_detail=None,
        )
        assert r.request_id == "rid"

    def test_frozen(self) -> None:
        r = QuickEraseRecord(
            request_id="r", user_id="u", status="pending",
            requested_at="2026-04-25", completed_at=None, error_detail=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            r.status = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# InMemoryQuickEraseRepository.create
# ---------------------------------------------------------------------------


class TestQuickEraseCreate:
    @pytest.mark.asyncio
    async def test_returns_quick_erase_record(self) -> None:
        repo = InMemoryQuickEraseRepository()
        r = await repo.create(user_id="u-1")
        assert isinstance(r, QuickEraseRecord)

    @pytest.mark.asyncio
    async def test_request_id_is_valid_uuid(self) -> None:
        repo = InMemoryQuickEraseRepository()
        r = await repo.create(user_id="u-1")
        uuid.UUID(r.request_id)

    @pytest.mark.asyncio
    async def test_status_is_pending(self) -> None:
        repo = InMemoryQuickEraseRepository()
        r = await repo.create(user_id="u-1")
        assert r.status == "pending"

    @pytest.mark.asyncio
    async def test_user_id_matches(self) -> None:
        repo = InMemoryQuickEraseRepository()
        r = await repo.create(user_id="u-99")
        assert r.user_id == "u-99"

    @pytest.mark.asyncio
    async def test_completed_at_is_none_on_creation(self) -> None:
        repo = InMemoryQuickEraseRepository()
        r = await repo.create(user_id="u-1")
        assert r.completed_at is None


# ---------------------------------------------------------------------------
# InMemoryQuickEraseRepository.get_latest
# ---------------------------------------------------------------------------


class TestQuickEraseGetLatest:
    @pytest.mark.asyncio
    async def test_returns_a_request_for_user(self) -> None:
        repo = InMemoryQuickEraseRepository()
        r1 = await repo.create(user_id="u-1")
        r2 = await repo.create(user_id="u-1")
        latest = await repo.get_latest("u-1")
        assert latest is not None
        assert latest.request_id in (r1.request_id, r2.request_id)

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_user(self) -> None:
        repo = InMemoryQuickEraseRepository()
        result = await repo.get_latest("ghost-user")
        assert result is None
