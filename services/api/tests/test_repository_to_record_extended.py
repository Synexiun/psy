"""Unit tests for _to_record() and _to_item() mappers across clinical,
compliance, identity, memory, resilience, signal, and enterprise modules.

Mirrors the pattern from test_repository_to_record.py: all helpers are pure
functions reading named attributes, tested via MagicMock without a DB session.

The non-trivial invariant shared by all is the optional-field None-safety:
  field.isoformat() if field else None
An unconditional .isoformat() call would raise AttributeError in production
whenever the optional field is null.  These tests pin that contract for each mapper.

Mappers tested:
  clinical/repository.py     — _relapse_to_record      (reviewed_at optional)
  compliance/repository.py   — _consent_to_record      (no optional datetime)
                             — _quick_erase_to_record  (completed_at optional)
  identity/repository.py     — _user_to_record         (created_at optional)
  memory/repository.py       — _journal_to_record      (no optional datetime)
                             — _voice_to_record        (finalized_at optional)
  resilience/repository.py   — _state_to_record        (continuous_streak_start optional)
  signal/repository.py       — _window_to_record       (no optional datetime)
                             — _estimate_to_record     (no optional datetime)
  enterprise/router.py       — _org_to_item            (no optional datetime)
                             — _link_to_item           (consented_at, revoked_at optional)
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
import uuid

from discipline.clinical.repository import _relapse_to_record
from discipline.compliance.repository import _consent_to_record, _quick_erase_to_record
from discipline.identity.repository import _user_to_record
from discipline.memory.repository import _journal_to_record, _voice_to_record
from discipline.resilience.repository import _state_to_record
from discipline.signal.repository import _estimate_to_record, _window_to_record
from discipline.enterprise.router import _link_to_item, _org_to_item

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
_NOW_ISO = _NOW.isoformat()
_UUID = uuid.uuid4()


# ---------------------------------------------------------------------------
# _relapse_to_record — reviewed_at is optional
# ---------------------------------------------------------------------------


def _relapse(reviewed_at=None) -> MagicMock:
    e = MagicMock()
    e.id = _UUID
    e.user_id = _UUID
    e.occurred_at = _NOW
    e.behavior = "substance_use"
    e.severity = "moderate"
    e.context_tags = ["social_situation", "work_stress"]
    e.compassion_message = "This is a step, not the whole journey."
    e.reviewed = False
    e.reviewed_at = reviewed_at
    e.reviewed_by = None
    e.created_at = _NOW
    return e


class TestRelapseToRecord:
    def test_reviewed_at_none_maps_to_none(self) -> None:
        record = _relapse_to_record(_relapse(reviewed_at=None))
        assert record.reviewed_at is None

    def test_reviewed_at_present_maps_to_isoformat(self) -> None:
        record = _relapse_to_record(_relapse(reviewed_at=_NOW))
        assert record.reviewed_at == _NOW_ISO

    def test_relapse_id_is_str(self) -> None:
        assert isinstance(_relapse_to_record(_relapse()).relapse_id, str)

    def test_user_id_is_str(self) -> None:
        assert isinstance(_relapse_to_record(_relapse()).user_id, str)

    def test_context_tags_is_list(self) -> None:
        record = _relapse_to_record(_relapse())
        assert isinstance(record.context_tags, list)

    def test_occurred_at_is_isoformat(self) -> None:
        assert _relapse_to_record(_relapse()).occurred_at == _NOW_ISO


# ---------------------------------------------------------------------------
# _consent_to_record — no optional datetime fields
# ---------------------------------------------------------------------------


def _consent() -> MagicMock:
    c = MagicMock()
    c.id = _UUID
    c.user_id = _UUID
    c.consent_type = "terms_of_service"
    c.version = "2026-01"
    c.granted_at = _NOW
    c.ip_address_hash = "sha256hexvalue"
    return c


class TestConsentToRecord:
    def test_consent_id_is_str(self) -> None:
        assert isinstance(_consent_to_record(_consent()).consent_id, str)

    def test_granted_at_is_isoformat(self) -> None:
        assert _consent_to_record(_consent()).granted_at == _NOW_ISO

    def test_consent_type_propagated(self) -> None:
        assert _consent_to_record(_consent()).consent_type == "terms_of_service"

    def test_version_propagated(self) -> None:
        assert _consent_to_record(_consent()).version == "2026-01"


# ---------------------------------------------------------------------------
# _quick_erase_to_record — completed_at is optional
# ---------------------------------------------------------------------------


def _erase_request(completed_at=None) -> MagicMock:
    r = MagicMock()
    r.id = _UUID
    r.user_id = _UUID
    r.status = "pending"
    r.requested_at = _NOW
    r.completed_at = completed_at
    r.error_detail = None
    return r


class TestQuickEraseToRecord:
    def test_completed_at_none_maps_to_none(self) -> None:
        record = _quick_erase_to_record(_erase_request(completed_at=None))
        assert record.completed_at is None

    def test_completed_at_present_maps_to_isoformat(self) -> None:
        record = _quick_erase_to_record(_erase_request(completed_at=_NOW))
        assert record.completed_at == _NOW_ISO

    def test_request_id_is_str(self) -> None:
        assert isinstance(_quick_erase_to_record(_erase_request()).request_id, str)

    def test_requested_at_is_isoformat(self) -> None:
        assert _quick_erase_to_record(_erase_request()).requested_at == _NOW_ISO


# ---------------------------------------------------------------------------
# _user_to_record — created_at is optional
# ---------------------------------------------------------------------------


def _user(created_at=_NOW) -> MagicMock:
    u = MagicMock()
    u.id = _UUID
    u.external_id = "clerk_user_abc"
    u.email_hash = "sha256hashofmail"
    u.locale = "en"
    u.timezone = "America/New_York"
    u.created_at = created_at
    return u


class TestUserToRecord:
    def test_created_at_none_maps_to_none(self) -> None:
        record = _user_to_record(_user(created_at=None))
        assert record.created_at is None

    def test_created_at_present_maps_to_isoformat(self) -> None:
        record = _user_to_record(_user(created_at=_NOW))
        assert record.created_at == _NOW_ISO

    def test_user_id_is_str(self) -> None:
        assert isinstance(_user_to_record(_user()).user_id, str)

    def test_locale_propagated(self) -> None:
        assert _user_to_record(_user()).locale == "en"

    def test_external_id_propagated(self) -> None:
        assert _user_to_record(_user()).external_id == "clerk_user_abc"


# ---------------------------------------------------------------------------
# _journal_to_record — no optional datetime fields
# ---------------------------------------------------------------------------


def _journal() -> MagicMock:
    j = MagicMock()
    j.id = _UUID
    j.user_id = _UUID
    j.title = "Today's reflection"
    j.body_encrypted = "base64ciphertext=="
    j.mood_score = 7
    j.created_at = _NOW
    j.updated_at = _NOW
    return j


class TestJournalToRecord:
    def test_journal_id_is_str(self) -> None:
        assert isinstance(_journal_to_record(_journal()).journal_id, str)

    def test_created_at_is_isoformat(self) -> None:
        assert _journal_to_record(_journal()).created_at == _NOW_ISO

    def test_title_propagated(self) -> None:
        assert _journal_to_record(_journal()).title == "Today's reflection"

    def test_mood_score_propagated(self) -> None:
        assert _journal_to_record(_journal()).mood_score == 7


# ---------------------------------------------------------------------------
# _voice_to_record — finalized_at is optional
# ---------------------------------------------------------------------------


def _voice(finalized_at=None) -> MagicMock:
    v = MagicMock()
    v.id = _UUID
    v.user_id = _UUID
    v.status = "processing"
    v.duration_seconds = 45
    v.s3_key = "voice/2026/01/15/abc.opus"
    v.transcription = None
    v.created_at = _NOW
    v.finalized_at = finalized_at
    v.hard_delete_at = _NOW
    return v


class TestVoiceToRecord:
    def test_finalized_at_none_maps_to_none(self) -> None:
        record = _voice_to_record(_voice(finalized_at=None))
        assert record.finalized_at is None

    def test_finalized_at_present_maps_to_isoformat(self) -> None:
        record = _voice_to_record(_voice(finalized_at=_NOW))
        assert record.finalized_at == _NOW_ISO

    def test_session_id_is_str(self) -> None:
        assert isinstance(_voice_to_record(_voice()).session_id, str)

    def test_hard_delete_at_is_isoformat(self) -> None:
        assert _voice_to_record(_voice()).hard_delete_at == _NOW_ISO

    def test_duration_seconds_propagated(self) -> None:
        assert _voice_to_record(_voice()).duration_seconds == 45


# ---------------------------------------------------------------------------
# _state_to_record — continuous_streak_start is optional
# ---------------------------------------------------------------------------


def _streak_state(continuous_streak_start=_NOW) -> MagicMock:
    s = MagicMock()
    s.user_id = _UUID
    s.continuous_days = 7
    s.continuous_streak_start = continuous_streak_start
    s.resilience_days = 30
    s.resilience_urges_handled_total = 5
    s.resilience_streak_start = _NOW
    s.updated_at = _NOW
    return s


class TestStateToRecord:
    def test_continuous_streak_start_none_maps_to_none(self) -> None:
        record = _state_to_record(_streak_state(continuous_streak_start=None))
        assert record.continuous_streak_start is None

    def test_continuous_streak_start_present_maps_to_isoformat(self) -> None:
        record = _state_to_record(_streak_state(continuous_streak_start=_NOW))
        assert record.continuous_streak_start == _NOW_ISO

    def test_resilience_streak_start_is_isoformat(self) -> None:
        # resilience_streak_start is non-optional — unconditionally .isoformat()
        assert _state_to_record(_streak_state()).resilience_streak_start == _NOW_ISO

    def test_user_id_is_str(self) -> None:
        assert isinstance(_state_to_record(_streak_state()).user_id, str)

    def test_resilience_days_propagated(self) -> None:
        assert _state_to_record(_streak_state()).resilience_days == 30


# ---------------------------------------------------------------------------
# _window_to_record — no optional datetime fields
# ---------------------------------------------------------------------------


def _signal_window() -> MagicMock:
    w = MagicMock()
    w.id = _UUID
    w.user_id = _UUID
    w.window_start = _NOW
    w.window_end = _NOW
    w.source = "hrv_sensor"
    w.samples_hash = "sha256ofsamples"
    w.created_at = _NOW
    return w


class TestWindowToRecord:
    def test_window_id_is_str(self) -> None:
        assert isinstance(_window_to_record(_signal_window()).window_id, str)

    def test_window_start_is_isoformat(self) -> None:
        assert _window_to_record(_signal_window()).window_start == _NOW_ISO

    def test_window_end_is_isoformat(self) -> None:
        assert _window_to_record(_signal_window()).window_end == _NOW_ISO

    def test_source_propagated(self) -> None:
        assert _window_to_record(_signal_window()).source == "hrv_sensor"


# ---------------------------------------------------------------------------
# _estimate_to_record — no optional datetime fields
# ---------------------------------------------------------------------------


def _state_estimate() -> MagicMock:
    e = MagicMock()
    e.id = _UUID
    e.user_id = _UUID
    e.state_label = "elevated"
    e.confidence = 0.78
    e.model_version = "v2.1.0"
    e.inferred_at = _NOW
    e.created_at = _NOW
    return e


class TestEstimateToRecord:
    def test_estimate_id_is_str(self) -> None:
        assert isinstance(_estimate_to_record(_state_estimate()).estimate_id, str)

    def test_inferred_at_is_isoformat(self) -> None:
        assert _estimate_to_record(_state_estimate()).inferred_at == _NOW_ISO

    def test_state_label_propagated(self) -> None:
        assert _estimate_to_record(_state_estimate()).state_label == "elevated"

    def test_confidence_propagated(self) -> None:
        assert _estimate_to_record(_state_estimate()).confidence == 0.78

    def test_model_version_propagated(self) -> None:
        assert _estimate_to_record(_state_estimate()).model_version == "v2.1.0"


# ---------------------------------------------------------------------------
# _org_to_item — enterprise router mapper (no optional datetime)
# ---------------------------------------------------------------------------


def _org_record() -> MagicMock:
    r = MagicMock()
    r.org_id = str(_UUID)
    r.name = "Acme Health"
    r.slug = "acme-health"
    r.tier = "enterprise"
    r.status = "active"
    r.created_at = _NOW_ISO
    r.updated_at = _NOW_ISO
    return r


class TestOrgToItem:
    def test_org_id_propagated(self) -> None:
        assert _org_to_item(_org_record()).org_id == str(_UUID)

    def test_name_propagated(self) -> None:
        assert _org_to_item(_org_record()).name == "Acme Health"

    def test_slug_propagated(self) -> None:
        assert _org_to_item(_org_record()).slug == "acme-health"

    def test_tier_propagated(self) -> None:
        assert _org_to_item(_org_record()).tier == "enterprise"

    def test_status_propagated(self) -> None:
        assert _org_to_item(_org_record()).status == "active"


# ---------------------------------------------------------------------------
# _link_to_item — enterprise router mapper (consented_at, revoked_at optional)
# ---------------------------------------------------------------------------


def _link_record(consented_at=None, revoked_at=None) -> MagicMock:
    r = MagicMock()
    r.link_id = str(_UUID)
    r.org_id = str(_UUID)
    r.clinician_user_id = str(_UUID)
    r.patient_user_id = str(_UUID)
    r.status = "active"
    r.invited_at = _NOW_ISO
    r.consented_at = consented_at
    r.revoked_at = revoked_at
    r.created_at = _NOW_ISO
    r.updated_at = _NOW_ISO
    return r


class TestLinkToItem:
    def test_consented_at_none_maps_to_none(self) -> None:
        result = _link_to_item(_link_record(consented_at=None))
        assert result.consented_at is None

    def test_consented_at_present_propagated(self) -> None:
        result = _link_to_item(_link_record(consented_at=_NOW_ISO))
        assert result.consented_at == _NOW_ISO

    def test_revoked_at_none_maps_to_none(self) -> None:
        result = _link_to_item(_link_record(revoked_at=None))
        assert result.revoked_at is None

    def test_revoked_at_present_propagated(self) -> None:
        result = _link_to_item(_link_record(revoked_at=_NOW_ISO))
        assert result.revoked_at == _NOW_ISO

    def test_link_id_propagated(self) -> None:
        assert _link_to_item(_link_record()).link_id == str(_UUID)

    def test_status_propagated(self) -> None:
        assert _link_to_item(_link_record()).status == "active"

    def test_invited_at_propagated(self) -> None:
        assert _link_to_item(_link_record()).invited_at == _NOW_ISO
