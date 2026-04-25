"""Unit tests for _to_record() pure helpers across billing, enterprise,
notifications, and pattern repositories.

All these helpers map SQLAlchemy ORM model instances to frozen dataclasses.
The non-trivial invariant shared by all of them is the optional-field
None-safety contract:

    canceled_at=sub.canceled_at.isoformat() if sub.canceled_at else None

If a future refactor removes the None guard (e.g. unconditional .isoformat()),
the helper silently breaks in production whenever the optional field is null.
These tests pin that contract for each mapper.

Tests use MagicMock to avoid requiring a database session — each mapper is
a pure function that reads named attributes from its input.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
import uuid

from discipline.billing.repository import _subscription_to_record
from discipline.enterprise.repository import _link_to_record, _org_to_record
from discipline.notifications.repository import _nudge_to_record, _token_to_record
from discipline.pattern.repository import _pattern_to_record

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
_NOW_ISO = _NOW.isoformat()
_UUID = uuid.uuid4()


# ---------------------------------------------------------------------------
# _subscription_to_record — canceled_at is optional
# ---------------------------------------------------------------------------


def _sub(canceled_at=None) -> MagicMock:
    s = MagicMock()
    s.id = _UUID
    s.user_id = _UUID
    s.status = "active"
    s.tier = "plus"
    s.provider = "stripe"
    s.provider_subscription_id = "sub_123"
    s.current_period_start = _NOW
    s.current_period_end = _NOW
    s.canceled_at = canceled_at
    s.cancel_reason = None
    s.created_at = _NOW
    s.updated_at = _NOW
    return s


class TestSubscriptionToRecord:
    def test_canceled_at_none_maps_to_none(self) -> None:
        record = _subscription_to_record(_sub(canceled_at=None))
        assert record.canceled_at is None

    def test_canceled_at_present_maps_to_isoformat(self) -> None:
        record = _subscription_to_record(_sub(canceled_at=_NOW))
        assert record.canceled_at == _NOW_ISO

    def test_subscription_id_is_str(self) -> None:
        record = _subscription_to_record(_sub())
        assert isinstance(record.subscription_id, str)

    def test_user_id_is_str(self) -> None:
        record = _subscription_to_record(_sub())
        assert isinstance(record.user_id, str)


# ---------------------------------------------------------------------------
# _org_to_record — no optional fields, basic smoke test
# ---------------------------------------------------------------------------


def _org() -> MagicMock:
    o = MagicMock()
    o.id = _UUID
    o.name = "Acme Corp"
    o.slug = "acme-corp"
    o.tier = "enterprise"
    o.status = "active"
    o.created_at = _NOW
    o.updated_at = _NOW
    return o


class TestOrgToRecord:
    def test_org_id_is_str(self) -> None:
        record = _org_to_record(_org())
        assert isinstance(record.org_id, str)

    def test_name_propagated(self) -> None:
        record = _org_to_record(_org())
        assert record.name == "Acme Corp"

    def test_created_at_is_isoformat(self) -> None:
        record = _org_to_record(_org())
        assert record.created_at == _NOW_ISO


# ---------------------------------------------------------------------------
# _link_to_record — consented_at and revoked_at are optional
# ---------------------------------------------------------------------------


def _link(consented_at=None, revoked_at=None) -> MagicMock:
    lk = MagicMock()
    lk.id = _UUID
    lk.org_id = _UUID
    lk.clinician_user_id = _UUID
    lk.patient_user_id = _UUID
    lk.status = "active"
    lk.invited_at = _NOW
    lk.consented_at = consented_at
    lk.revoked_at = revoked_at
    lk.created_at = _NOW
    lk.updated_at = _NOW
    return lk


class TestLinkToRecord:
    def test_consented_at_none_maps_to_none(self) -> None:
        record = _link_to_record(_link(consented_at=None))
        assert record.consented_at is None

    def test_consented_at_present_maps_to_isoformat(self) -> None:
        record = _link_to_record(_link(consented_at=_NOW))
        assert record.consented_at == _NOW_ISO

    def test_revoked_at_none_maps_to_none(self) -> None:
        record = _link_to_record(_link(revoked_at=None))
        assert record.revoked_at is None

    def test_revoked_at_present_maps_to_isoformat(self) -> None:
        record = _link_to_record(_link(revoked_at=_NOW))
        assert record.revoked_at == _NOW_ISO

    def test_link_id_is_str(self) -> None:
        record = _link_to_record(_link())
        assert isinstance(record.link_id, str)


# ---------------------------------------------------------------------------
# _nudge_to_record — sent_at is optional
# ---------------------------------------------------------------------------


def _nudge(sent_at=None) -> MagicMock:
    n = MagicMock()
    n.id = _UUID
    n.user_id = _UUID
    n.nudge_type = "breathing"
    n.status = "pending"
    n.scheduled_at = _NOW
    n.sent_at = sent_at
    n.tool_variant = "box_4"
    n.message_copy = "Take a moment."
    n.created_at = _NOW
    return n


class TestNudgeToRecord:
    def test_sent_at_none_maps_to_none(self) -> None:
        record = _nudge_to_record(_nudge(sent_at=None))
        assert record.sent_at is None

    def test_sent_at_present_maps_to_isoformat(self) -> None:
        record = _nudge_to_record(_nudge(sent_at=_NOW))
        assert record.sent_at == _NOW_ISO

    def test_nudge_id_is_str(self) -> None:
        record = _nudge_to_record(_nudge())
        assert isinstance(record.nudge_id, str)

    def test_scheduled_at_is_isoformat(self) -> None:
        record = _nudge_to_record(_nudge())
        assert record.scheduled_at == _NOW_ISO


# ---------------------------------------------------------------------------
# _token_to_record — last_valid_at is optional
# ---------------------------------------------------------------------------


def _push_token(last_valid_at=None) -> MagicMock:
    t = MagicMock()
    t.id = _UUID
    t.user_id = _UUID
    t.platform = "ios"
    t.token_hash = "sha256hashvalue"
    t.created_at = _NOW
    t.last_valid_at = last_valid_at
    return t


class TestTokenToRecord:
    def test_last_valid_at_none_maps_to_none(self) -> None:
        record = _token_to_record(_push_token(last_valid_at=None))
        assert record.last_valid_at is None

    def test_last_valid_at_present_maps_to_isoformat(self) -> None:
        record = _token_to_record(_push_token(last_valid_at=_NOW))
        assert record.last_valid_at == _NOW_ISO

    def test_token_id_is_str(self) -> None:
        record = _token_to_record(_push_token())
        assert isinstance(record.token_id, str)


# ---------------------------------------------------------------------------
# _pattern_to_record — dismissed_at is optional; metadata_json copied
# ---------------------------------------------------------------------------


def _pattern(dismissed_at=None) -> MagicMock:
    p = MagicMock()
    p.id = _UUID
    p.user_id = _UUID
    p.pattern_type = "temporal"
    p.detector = "evening_spike_v1"
    p.confidence = 0.85
    p.description = "Evening urge spikes detected"
    p.metadata_json = {"hour": 21, "days": ["Mon", "Fri"]}
    p.status = "active"
    p.dismissed_at = dismissed_at
    p.dismiss_reason = None
    p.created_at = _NOW
    p.updated_at = _NOW
    return p


class TestPatternToRecord:
    def test_dismissed_at_none_maps_to_none(self) -> None:
        record = _pattern_to_record(_pattern(dismissed_at=None))
        assert record.dismissed_at is None

    def test_dismissed_at_present_maps_to_isoformat(self) -> None:
        record = _pattern_to_record(_pattern(dismissed_at=_NOW))
        assert record.dismissed_at == _NOW_ISO

    def test_metadata_json_is_a_copy(self) -> None:
        original_meta = {"hour": 21}
        p = _pattern()
        p.metadata_json = original_meta
        record = _pattern_to_record(p)
        # dict() creates a shallow copy — mutations to the original shouldn't
        # affect the record (and vice versa)
        record.metadata_json["injected"] = True  # type: ignore[index]
        assert "injected" not in original_meta

    def test_pattern_id_is_str(self) -> None:
        record = _pattern_to_record(_pattern())
        assert isinstance(record.pattern_id, str)
