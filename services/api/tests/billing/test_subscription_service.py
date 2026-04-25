"""Tests for discipline.billing.repository (InMemory) and discipline.billing.service.

Covers:
- SubscriptionRecord frozen dataclass
- InMemorySubscriptionRepository.create: returns SubscriptionRecord with status=active
- create: subscription_id is a valid UUID
- create: user_id, tier, provider fields match input
- get_by_user: returns record for known user
- get_by_user: returns None for unknown user
- get_by_provider_subscription_id: lookup by provider ID
- update_status_by_provider_subscription_id: changes status
- update_status_by_provider_subscription_id: unknown ID returns None
- cancel: sets status=canceled, canceled_at populated
- cancel: cancel_reason stored
- cancel: unknown user returns None
- cancel_by_provider_subscription_id: cancels via provider ID
- reset_subscription_repository: returns fresh state
- SubscriptionService.create_subscription
- SubscriptionService.get_current
- SubscriptionService.upgrade: changes tier
- SubscriptionService.upgrade: returns None when no subscription
- SubscriptionService.cancel: delegates to repo
- SubscriptionService.cancel: reason=None is accepted
"""

from __future__ import annotations

import uuid

import pytest

from discipline.billing.repository import (
    InMemorySubscriptionRepository,
    SubscriptionRecord,
    reset_subscription_repository,
)
from discipline.billing.service import SubscriptionService


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_subscription_repository()


# ---------------------------------------------------------------------------
# SubscriptionRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestSubscriptionRecord:
    def test_can_be_constructed(self) -> None:
        rec = SubscriptionRecord(
            subscription_id="sid",
            user_id="uid",
            status="active",
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_123",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
            canceled_at=None,
            cancel_reason=None,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
        assert rec.subscription_id == "sid"

    def test_frozen(self) -> None:
        rec = SubscriptionRecord(
            subscription_id="sid",
            user_id="uid",
            status="active",
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_123",
            current_period_start="2026-01-01",
            current_period_end="2026-02-01",
            canceled_at=None,
            cancel_reason=None,
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        with pytest.raises((AttributeError, TypeError)):
            rec.status = "canceled"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# InMemorySubscriptionRepository.create
# ---------------------------------------------------------------------------


def _make_repo() -> InMemorySubscriptionRepository:
    return InMemorySubscriptionRepository()


class TestCreate:
    @pytest.mark.asyncio
    async def test_returns_subscription_record(self) -> None:
        repo = _make_repo()
        rec = await repo.create(
            user_id=str(uuid.uuid4()),
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        assert isinstance(rec, SubscriptionRecord)

    @pytest.mark.asyncio
    async def test_subscription_id_is_valid_uuid(self) -> None:
        repo = _make_repo()
        rec = await repo.create(
            user_id=str(uuid.uuid4()),
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        uuid.UUID(rec.subscription_id)

    @pytest.mark.asyncio
    async def test_status_is_active(self) -> None:
        repo = _make_repo()
        rec = await repo.create(
            user_id=str(uuid.uuid4()),
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        assert rec.status == "active"

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = _make_repo()
        uid = str(uuid.uuid4())
        rec = await repo.create(
            user_id=uid,
            tier="enterprise",
            provider="iap_apple",
            provider_subscription_id="sub_999",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        assert rec.user_id == uid
        assert rec.tier == "enterprise"
        assert rec.provider == "iap_apple"
        assert rec.provider_subscription_id == "sub_999"

    @pytest.mark.asyncio
    async def test_canceled_at_is_none_on_creation(self) -> None:
        repo = _make_repo()
        rec = await repo.create(
            user_id=str(uuid.uuid4()),
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        assert rec.canceled_at is None


# ---------------------------------------------------------------------------
# InMemorySubscriptionRepository.get_by_user
# ---------------------------------------------------------------------------


class TestGetByUser:
    @pytest.mark.asyncio
    async def test_returns_record_for_known_user(self) -> None:
        repo = _make_repo()
        uid = str(uuid.uuid4())
        await repo.create(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="s1",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await repo.get_by_user(uid)
        assert rec is not None
        assert rec.user_id == uid

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_user(self) -> None:
        repo = _make_repo()
        result = await repo.get_by_user("ghost-user")
        assert result is None


# ---------------------------------------------------------------------------
# InMemorySubscriptionRepository.get_by_provider_subscription_id
# ---------------------------------------------------------------------------


class TestGetByProviderSubscriptionId:
    @pytest.mark.asyncio
    async def test_returns_record_for_known_provider_id(self) -> None:
        repo = _make_repo()
        await repo.create(
            user_id=str(uuid.uuid4()), tier="pro", provider="stripe",
            provider_subscription_id="sub_abc",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await repo.get_by_provider_subscription_id("sub_abc")
        assert rec is not None
        assert rec.provider_subscription_id == "sub_abc"

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_provider_id(self) -> None:
        repo = _make_repo()
        result = await repo.get_by_provider_subscription_id("nonexistent_sub")
        assert result is None


# ---------------------------------------------------------------------------
# InMemorySubscriptionRepository.update_status_by_provider_subscription_id
# ---------------------------------------------------------------------------


class TestUpdateStatusByProviderSubscriptionId:
    @pytest.mark.asyncio
    async def test_updates_status(self) -> None:
        repo = _make_repo()
        await repo.create(
            user_id=str(uuid.uuid4()), tier="pro", provider="stripe",
            provider_subscription_id="sub_upd",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        updated = await repo.update_status_by_provider_subscription_id(
            "sub_upd", status="past_due"
        )
        assert updated is not None
        assert updated.status == "past_due"

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_provider_id(self) -> None:
        repo = _make_repo()
        result = await repo.update_status_by_provider_subscription_id(
            "nonexistent", status="active"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_period_dates_optionally_updated(self) -> None:
        repo = _make_repo()
        await repo.create(
            user_id=str(uuid.uuid4()), tier="pro", provider="stripe",
            provider_subscription_id="sub_dates",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        updated = await repo.update_status_by_provider_subscription_id(
            "sub_dates",
            status="active",
            current_period_start="2026-02-01T00:00:00+00:00",
            current_period_end="2026-03-01T00:00:00+00:00",
        )
        assert updated is not None
        assert "2026-02-01" in updated.current_period_start


# ---------------------------------------------------------------------------
# InMemorySubscriptionRepository.cancel
# ---------------------------------------------------------------------------


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_sets_status_canceled(self) -> None:
        repo = _make_repo()
        uid = str(uuid.uuid4())
        await repo.create(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="s1",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await repo.cancel(uid, reason="user_requested")
        assert rec is not None
        assert rec.status == "canceled"

    @pytest.mark.asyncio
    async def test_canceled_at_is_set(self) -> None:
        repo = _make_repo()
        uid = str(uuid.uuid4())
        await repo.create(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="s1",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await repo.cancel(uid, reason=None)
        assert rec is not None
        assert rec.canceled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_reason_stored(self) -> None:
        repo = _make_repo()
        uid = str(uuid.uuid4())
        await repo.create(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="s1",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await repo.cancel(uid, reason="too_expensive")
        assert rec is not None
        assert rec.cancel_reason == "too_expensive"

    @pytest.mark.asyncio
    async def test_cancel_unknown_user_returns_none(self) -> None:
        repo = _make_repo()
        result = await repo.cancel("ghost-user", reason=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_by_provider_subscription_id(self) -> None:
        repo = _make_repo()
        await repo.create(
            user_id=str(uuid.uuid4()), tier="pro", provider="stripe",
            provider_subscription_id="sub_cancel_by_pid",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await repo.cancel_by_provider_subscription_id(
            "sub_cancel_by_pid", reason="webhook_cancel"
        )
        assert rec is not None
        assert rec.status == "canceled"
        assert rec.cancel_reason == "webhook_cancel"

    @pytest.mark.asyncio
    async def test_cancel_by_provider_subscription_id_unknown_returns_none(self) -> None:
        repo = _make_repo()
        result = await repo.cancel_by_provider_subscription_id(
            "nonexistent_sub", reason=None
        )
        assert result is None


# ---------------------------------------------------------------------------
# SubscriptionService
# ---------------------------------------------------------------------------


class TestSubscriptionService:
    def _service(self) -> SubscriptionService:
        return SubscriptionService(repository=_make_repo())

    @pytest.mark.asyncio
    async def test_create_subscription_returns_record(self) -> None:
        svc = self._service()
        rec = await svc.create_subscription(
            user_id=str(uuid.uuid4()),
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_svc_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        assert isinstance(rec, SubscriptionRecord)
        assert rec.status == "active"

    @pytest.mark.asyncio
    async def test_get_current_returns_subscription(self) -> None:
        svc = self._service()
        uid = str(uuid.uuid4())
        await svc.create_subscription(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="sub_get_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await svc.get_current(uid)
        assert rec is not None
        assert rec.user_id == uid

    @pytest.mark.asyncio
    async def test_get_current_returns_none_when_no_subscription(self) -> None:
        svc = self._service()
        result = await svc.get_current("unknown-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_upgrade_changes_tier(self) -> None:
        svc = self._service()
        uid = str(uuid.uuid4())
        await svc.create_subscription(
            user_id=uid, tier="basic", provider="stripe",
            provider_subscription_id="sub_upg_001",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        updated = await svc.upgrade(uid, "pro")
        assert updated is not None
        assert updated.tier == "pro"

    @pytest.mark.asyncio
    async def test_upgrade_returns_none_when_no_subscription(self) -> None:
        svc = self._service()
        result = await svc.upgrade("unknown-user", "pro")
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_sets_status_canceled(self) -> None:
        svc = self._service()
        uid = str(uuid.uuid4())
        await svc.create_subscription(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="sub_cancel_svc",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await svc.cancel(uid, reason="user_requested")
        assert rec is not None
        assert rec.status == "canceled"

    @pytest.mark.asyncio
    async def test_cancel_reason_none_accepted(self) -> None:
        svc = self._service()
        uid = str(uuid.uuid4())
        await svc.create_subscription(
            user_id=uid, tier="pro", provider="stripe",
            provider_subscription_id="sub_cancel_no_reason",
            current_period_start="2026-01-01T00:00:00+00:00",
            current_period_end="2026-02-01T00:00:00+00:00",
        )
        rec = await svc.cancel(uid, reason=None)
        assert rec is not None
        assert rec.status == "canceled"
        assert rec.cancel_reason is None

    @pytest.mark.asyncio
    async def test_cancel_unknown_user_returns_none(self) -> None:
        svc = self._service()
        result = await svc.cancel("ghost", reason=None)
        assert result is None
