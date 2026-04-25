"""Tests for discipline.billing.repository — subscription state in-memory store.

Covers:
- SubscriptionRecord frozen dataclass
- InMemorySubscriptionRepository.create: new subscription initialised with active status
- get_by_user: returns created record; returns None for unknown user
- get_by_provider_subscription_id: finds by provider id; returns None for unknown
- update: stores updated record, returns it
- update_status_by_provider_subscription_id: updates status fields; returns None for unknown
- cancel_by_provider_subscription_id: sets canceled status + timestamps; returns None for unknown
- cancel: sets canceled status by user_id; returns None for unknown
- reset_subscription_repository: replaces singleton, clears store
"""

from __future__ import annotations

import pytest

from discipline.billing.repository import (
    InMemorySubscriptionRepository,
    SubscriptionRecord,
    get_subscription_repository,
    reset_subscription_repository,
)

_PERIOD_START = "2026-04-01T00:00:00+00:00"
_PERIOD_END = "2026-05-01T00:00:00+00:00"


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_subscription_repository()


def _make_repo() -> InMemorySubscriptionRepository:
    return InMemorySubscriptionRepository()


async def _create(repo: InMemorySubscriptionRepository, *, user_id: str = "u-1") -> SubscriptionRecord:
    return await repo.create(
        user_id=user_id,
        tier="premium",
        provider="stripe",
        provider_subscription_id=f"sub_{user_id}",
        current_period_start=_PERIOD_START,
        current_period_end=_PERIOD_END,
    )


# ---------------------------------------------------------------------------
# SubscriptionRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestSubscriptionRecord:
    def test_can_be_constructed(self) -> None:
        r = SubscriptionRecord(
            subscription_id="id-1",
            user_id="u-1",
            status="active",
            tier="premium",
            provider="stripe",
            provider_subscription_id="sub_u-1",
            current_period_start=_PERIOD_START,
            current_period_end=_PERIOD_END,
            canceled_at=None,
            cancel_reason=None,
            created_at="2026-04-01T00:00:00+00:00",
            updated_at="2026-04-01T00:00:00+00:00",
        )
        assert r.user_id == "u-1"
        assert r.status == "active"

    def test_frozen(self) -> None:
        r = SubscriptionRecord(
            subscription_id="id-1", user_id="u-1", status="active", tier="premium",
            provider="stripe", provider_subscription_id="sub_u-1",
            current_period_start=_PERIOD_START, current_period_end=_PERIOD_END,
            canceled_at=None, cancel_reason=None,
            created_at="2026-04-01T00:00:00+00:00", updated_at="2026-04-01T00:00:00+00:00",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.status = "canceled"  # type: ignore[misc]

    def test_canceled_at_accepts_none(self) -> None:
        r = SubscriptionRecord(
            subscription_id="id-1", user_id="u-1", status="active", tier="free",
            provider="iap", provider_subscription_id="sub_x",
            current_period_start=_PERIOD_START, current_period_end=_PERIOD_END,
            canceled_at=None, cancel_reason=None,
            created_at="2026-04-01T00:00:00+00:00", updated_at="2026-04-01T00:00:00+00:00",
        )
        assert r.canceled_at is None
        assert r.cancel_reason is None


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_returns_record_with_active_status(self) -> None:
        repo = _make_repo()
        r = await _create(repo)
        assert r.status == "active"

    @pytest.mark.asyncio
    async def test_create_stores_user_id(self) -> None:
        repo = _make_repo()
        r = await _create(repo, user_id="u-42")
        assert r.user_id == "u-42"

    @pytest.mark.asyncio
    async def test_create_stores_tier(self) -> None:
        repo = _make_repo()
        r = await _create(repo)
        assert r.tier == "premium"

    @pytest.mark.asyncio
    async def test_create_stores_provider(self) -> None:
        repo = _make_repo()
        r = await _create(repo)
        assert r.provider == "stripe"

    @pytest.mark.asyncio
    async def test_create_assigns_uuid_subscription_id(self) -> None:
        repo = _make_repo()
        r = await _create(repo)
        assert len(r.subscription_id) == 36  # UUID string

    @pytest.mark.asyncio
    async def test_create_no_cancellation_fields(self) -> None:
        repo = _make_repo()
        r = await _create(repo)
        assert r.canceled_at is None
        assert r.cancel_reason is None


# ---------------------------------------------------------------------------
# get_by_user
# ---------------------------------------------------------------------------


class TestGetByUser:
    @pytest.mark.asyncio
    async def test_returns_created_record(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        fetched = await repo.get_by_user(created.user_id)
        assert fetched is not None
        assert fetched.subscription_id == created.subscription_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_user(self) -> None:
        repo = _make_repo()
        result = await repo.get_by_user("ghost")
        assert result is None

    @pytest.mark.asyncio
    async def test_different_users_independent(self) -> None:
        repo = _make_repo()
        a = await _create(repo, user_id="alice")
        b = await _create(repo, user_id="bob")
        assert (await repo.get_by_user("alice")) is not None
        assert (await repo.get_by_user("bob")) is not None
        assert a.subscription_id != b.subscription_id


# ---------------------------------------------------------------------------
# get_by_provider_subscription_id
# ---------------------------------------------------------------------------


class TestGetByProviderSubscriptionId:
    @pytest.mark.asyncio
    async def test_finds_by_provider_id(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        fetched = await repo.get_by_provider_subscription_id(created.provider_subscription_id)
        assert fetched is not None
        assert fetched.user_id == created.user_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_provider_id(self) -> None:
        repo = _make_repo()
        result = await repo.get_by_provider_subscription_id("sub_unknown")
        assert result is None


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update_stores_new_status(self) -> None:
        repo = _make_repo()
        original = await _create(repo)
        updated_record = SubscriptionRecord(
            subscription_id=original.subscription_id,
            user_id=original.user_id,
            status="past_due",
            tier=original.tier,
            provider=original.provider,
            provider_subscription_id=original.provider_subscription_id,
            current_period_start=original.current_period_start,
            current_period_end=original.current_period_end,
            canceled_at=None,
            cancel_reason=None,
            created_at=original.created_at,
            updated_at="2026-04-25T00:00:00+00:00",
        )
        result = await repo.update(updated_record)
        assert result.status == "past_due"

    @pytest.mark.asyncio
    async def test_update_returns_same_record(self) -> None:
        repo = _make_repo()
        original = await _create(repo)
        new_record = SubscriptionRecord(
            subscription_id=original.subscription_id,
            user_id=original.user_id,
            status="trialing",
            tier=original.tier,
            provider=original.provider,
            provider_subscription_id=original.provider_subscription_id,
            current_period_start=original.current_period_start,
            current_period_end=original.current_period_end,
            canceled_at=None,
            cancel_reason=None,
            created_at=original.created_at,
            updated_at="2026-04-25T00:00:00+00:00",
        )
        result = await repo.update(new_record)
        assert result is new_record

    @pytest.mark.asyncio
    async def test_subsequent_get_by_user_sees_updated_record(self) -> None:
        repo = _make_repo()
        original = await _create(repo)
        new_record = SubscriptionRecord(
            subscription_id=original.subscription_id,
            user_id=original.user_id,
            status="past_due",
            tier="free",
            provider=original.provider,
            provider_subscription_id=original.provider_subscription_id,
            current_period_start=original.current_period_start,
            current_period_end=original.current_period_end,
            canceled_at=None,
            cancel_reason=None,
            created_at=original.created_at,
            updated_at="2026-04-25T00:00:00+00:00",
        )
        await repo.update(new_record)
        fetched = await repo.get_by_user(original.user_id)
        assert fetched is not None
        assert fetched.status == "past_due"
        assert fetched.tier == "free"


# ---------------------------------------------------------------------------
# update_status_by_provider_subscription_id
# ---------------------------------------------------------------------------


class TestUpdateStatusByProviderSubscriptionId:
    @pytest.mark.asyncio
    async def test_updates_status(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.update_status_by_provider_subscription_id(
            created.provider_subscription_id,
            status="past_due",
        )
        assert result is not None
        assert result.status == "past_due"

    @pytest.mark.asyncio
    async def test_updates_period_dates_when_provided(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        new_end = "2026-06-01T00:00:00+00:00"
        result = await repo.update_status_by_provider_subscription_id(
            created.provider_subscription_id,
            status="active",
            current_period_end=new_end,
        )
        assert result is not None
        assert result.current_period_end == new_end

    @pytest.mark.asyncio
    async def test_preserves_existing_period_when_not_provided(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.update_status_by_provider_subscription_id(
            created.provider_subscription_id,
            status="active",
        )
        assert result is not None
        assert result.current_period_end == _PERIOD_END

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_provider_id(self) -> None:
        repo = _make_repo()
        result = await repo.update_status_by_provider_subscription_id(
            "sub_unknown",
            status="active",
        )
        assert result is None


# ---------------------------------------------------------------------------
# cancel_by_provider_subscription_id
# ---------------------------------------------------------------------------


class TestCancelByProviderSubscriptionId:
    @pytest.mark.asyncio
    async def test_sets_canceled_status(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.cancel_by_provider_subscription_id(
            created.provider_subscription_id,
            reason="user_requested",
        )
        assert result is not None
        assert result.status == "canceled"

    @pytest.mark.asyncio
    async def test_stores_cancel_reason(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.cancel_by_provider_subscription_id(
            created.provider_subscription_id,
            reason="payment_failed",
        )
        assert result is not None
        assert result.cancel_reason == "payment_failed"

    @pytest.mark.asyncio
    async def test_sets_canceled_at_timestamp(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.cancel_by_provider_subscription_id(
            created.provider_subscription_id,
            reason=None,
        )
        assert result is not None
        assert result.canceled_at is not None

    @pytest.mark.asyncio
    async def test_accepts_none_reason(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.cancel_by_provider_subscription_id(
            created.provider_subscription_id,
            reason=None,
        )
        assert result is not None
        assert result.cancel_reason is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_provider_id(self) -> None:
        repo = _make_repo()
        result = await repo.cancel_by_provider_subscription_id(
            "sub_unknown",
            reason=None,
        )
        assert result is None


# ---------------------------------------------------------------------------
# cancel (by user_id)
# ---------------------------------------------------------------------------


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_sets_canceled_status(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.cancel(created.user_id, reason="downgrade")
        assert result is not None
        assert result.status == "canceled"

    @pytest.mark.asyncio
    async def test_cancel_stores_reason(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        result = await repo.cancel(created.user_id, reason="downgrade")
        assert result is not None
        assert result.cancel_reason == "downgrade"

    @pytest.mark.asyncio
    async def test_cancel_returns_none_for_unknown_user(self) -> None:
        repo = _make_repo()
        result = await repo.cancel("ghost", reason=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_subsequent_get_by_user_sees_canceled(self) -> None:
        repo = _make_repo()
        created = await _create(repo)
        await repo.cancel(created.user_id, reason=None)
        fetched = await repo.get_by_user(created.user_id)
        assert fetched is not None
        assert fetched.status == "canceled"


# ---------------------------------------------------------------------------
# reset_subscription_repository
# ---------------------------------------------------------------------------


class TestReset:
    @pytest.mark.asyncio
    async def test_reset_clears_store(self) -> None:
        repo = _make_repo()
        await _create(repo)
        reset_subscription_repository()
        new_repo = get_subscription_repository()
        result = await new_repo.get_by_user("u-1")
        assert result is None

    def test_reset_returns_fresh_in_memory_instance(self) -> None:
        reset_subscription_repository()
        repo = get_subscription_repository()
        assert isinstance(repo, InMemorySubscriptionRepository)
