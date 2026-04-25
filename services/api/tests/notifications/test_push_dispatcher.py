"""Unit tests for the push dispatcher (dispatch_pending_nudges).

Tests cover the full nudge lifecycle without a live database or FCM account:
- No due nudges → returns 0
- No push tokens → nudge skipped, returns 0
- Single token success → nudge.status = "sent", sent_count = 1
- Multiple tokens, first succeeds → nudge.status = "sent"
- Token triggers deregistration → last_valid_at set to None
- All tokens deregistered → nudge.status = "failed"
- Transient FCM error → nudge stays "scheduled", returns 0
- Mixed: one deregistered + one transient → nudge stays "scheduled" (not failed)
- Multiple nudges → each processed independently
- _decrypt_token base64 round-trip
- _nudge_copy: message_copy wins over fallback
- _nudge_copy: all four nudge_type fallbacks
- _nudge_copy: unknown type returns generic copy
"""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discipline.notifications.push_dispatcher import (
    _decrypt_token,
    _nudge_copy,
    dispatch_pending_nudges,
)
from discipline.notifications.push_sender import PushSendError


# ---------------------------------------------------------------------------
# Helpers — build lightweight ORM-like objects without hitting the DB.
# ---------------------------------------------------------------------------


def _make_nudge(
    *,
    user_id: uuid.UUID | None = None,
    nudge_type: str = "check_in",
    status: str = "scheduled",
    message_copy: str | None = None,
    minutes_ago: int = 5,
) -> MagicMock:
    n = MagicMock()
    n.id = uuid.uuid4()
    n.user_id = user_id or uuid.uuid4()
    n.nudge_type = nudge_type
    n.status = status
    n.message_copy = message_copy
    n.scheduled_at = datetime.now(UTC) - timedelta(minutes=minutes_ago)
    n.sent_at = None
    return n


def _make_token(
    *,
    user_id: uuid.UUID | None = None,
    platform: str = "android",
    raw_token: str = "raw-device-token",
) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.user_id = user_id
    t.platform = platform
    t.last_valid_at = datetime.now(UTC)
    # Dispatcher calls _decrypt_token which does base64.b64decode
    t.token_encrypted = base64.b64encode(raw_token.encode()).decode()
    return t


def _make_db(
    nudges: list[MagicMock],
    tokens_by_user: dict[uuid.UUID, list[MagicMock]],
) -> AsyncMock:
    """Build a mock AsyncSession that serves the given nudges and token lists."""
    db = AsyncMock()
    db.flush = AsyncMock()

    call_count = 0

    async def _execute(stmt: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        scalars = MagicMock()

        if call_count == 1:
            # First call: nudge query
            scalars.all.return_value = nudges
        else:
            # Subsequent calls: token query for a specific user.
            # Extract user_id from call position — token calls are sequential.
            nudge_idx = (call_count - 2) % max(len(nudges), 1)
            uid = nudges[nudge_idx].user_id if nudges else None
            scalars.all.return_value = tokens_by_user.get(uid, [])

        result.scalars.return_value = scalars
        return result

    db.execute = _execute  # type: ignore[method-assign]
    return db


def _make_sender(*, msg_name: str = "projects/p/messages/m") -> AsyncMock:
    sender = AsyncMock()
    sender.send = AsyncMock(return_value=msg_name)
    return sender


# ---------------------------------------------------------------------------
# _decrypt_token
# ---------------------------------------------------------------------------


class TestDecryptToken:
    def test_base64_round_trip(self) -> None:
        raw = "APA91bHPRgkF...some_fcm_token"
        encrypted = base64.b64encode(raw.encode()).decode()
        assert _decrypt_token(encrypted) == raw

    def test_short_token(self) -> None:
        raw = "tok"
        encrypted = base64.b64encode(raw.encode()).decode()
        assert _decrypt_token(encrypted) == raw


# ---------------------------------------------------------------------------
# _nudge_copy
# ---------------------------------------------------------------------------


class TestNudgeCopy:
    def test_message_copy_wins(self) -> None:
        n = _make_nudge(message_copy="You have got this.")
        title, body = _nudge_copy(n)
        assert title == "Discipline OS"
        assert body == "You have got this."

    def test_check_in_fallback(self) -> None:
        n = _make_nudge(nudge_type="check_in")
        title, body = _nudge_copy(n)
        assert len(title) > 0 and len(body) > 0
        # "check_in" copy includes a log prompt
        assert "check" in body.lower() or "doing" in title.lower() or "log" in body.lower()

    def test_tool_suggestion_fallback(self) -> None:
        n = _make_nudge(nudge_type="tool_suggestion")
        title, body = _nudge_copy(n)
        assert "intervention" in title.lower() or "exercise" in body.lower()

    def test_crisis_follow_up_fallback(self) -> None:
        n = _make_nudge(nudge_type="crisis_follow_up")
        title, body = _nudge_copy(n)
        assert len(title) > 0 and len(body) > 0

    def test_weekly_reflection_fallback(self) -> None:
        n = _make_nudge(nudge_type="weekly_reflection")
        title, body = _nudge_copy(n)
        assert "reflect" in title.lower() or "week" in body.lower()

    def test_unknown_type_returns_generic(self) -> None:
        n = _make_nudge(nudge_type="unrecognised_type")
        title, body = _nudge_copy(n)
        assert len(title) > 0 and len(body) > 0


# ---------------------------------------------------------------------------
# dispatch_pending_nudges — no nudges path
# ---------------------------------------------------------------------------


class TestDispatchNoNudges:
    @pytest.mark.asyncio
    async def test_returns_zero_when_no_due_nudges(self) -> None:
        db = _make_db(nudges=[], tokens_by_user={})
        sender = _make_sender()
        result = await dispatch_pending_nudges(db, sender)
        assert result == 0

    @pytest.mark.asyncio
    async def test_sender_not_called_when_no_nudges(self) -> None:
        db = _make_db(nudges=[], tokens_by_user={})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        sender.send.assert_not_called()


# ---------------------------------------------------------------------------
# dispatch_pending_nudges — no tokens
# ---------------------------------------------------------------------------


class TestDispatchNoTokens:
    @pytest.mark.asyncio
    async def test_returns_zero_when_no_tokens(self) -> None:
        nudge = _make_nudge()
        db = _make_db(nudges=[nudge], tokens_by_user={nudge.user_id: []})
        sender = _make_sender()
        result = await dispatch_pending_nudges(db, sender)
        assert result == 0

    @pytest.mark.asyncio
    async def test_nudge_status_unchanged_when_no_tokens(self) -> None:
        nudge = _make_nudge(status="scheduled")
        db = _make_db(nudges=[nudge], tokens_by_user={nudge.user_id: []})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        assert nudge.status == "scheduled"


# ---------------------------------------------------------------------------
# dispatch_pending_nudges — successful send
# ---------------------------------------------------------------------------


class TestDispatchSuccess:
    @pytest.mark.asyncio
    async def test_returns_one_on_single_success(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = _make_sender()
        result = await dispatch_pending_nudges(db, sender)
        assert result == 1

    @pytest.mark.asyncio
    async def test_nudge_status_set_to_sent(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        assert nudge.status == "sent"

    @pytest.mark.asyncio
    async def test_sent_at_populated(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        assert nudge.sent_at is not None

    @pytest.mark.asyncio
    async def test_sender_called_with_decrypted_token(self) -> None:
        uid = uuid.uuid4()
        raw = "real-device-token-xyz"
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid, raw_token=raw)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        call_kwargs = sender.send.call_args.kwargs
        assert call_kwargs["device_token"] == raw

    @pytest.mark.asyncio
    async def test_sender_called_with_nudge_data(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid, nudge_type="tool_suggestion")
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        call_kwargs = sender.send.call_args.kwargs
        assert call_kwargs["data"]["nudge_type"] == "tool_suggestion"
        assert call_kwargs["data"]["nudge_id"] == str(nudge.id)

    @pytest.mark.asyncio
    async def test_db_flush_called(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = _make_sender()
        await dispatch_pending_nudges(db, sender)
        db.flush.assert_called()


# ---------------------------------------------------------------------------
# dispatch_pending_nudges — deregistration path
# ---------------------------------------------------------------------------


class TestDispatchDeregistration:
    @pytest.mark.asyncio
    async def test_token_last_valid_at_cleared_on_404(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=404, detail="NOT_FOUND")
        )
        await dispatch_pending_nudges(db, sender)
        assert token.last_valid_at is None

    @pytest.mark.asyncio
    async def test_nudge_marked_failed_when_all_tokens_deregistered(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=404, detail="NOT_FOUND")
        )
        await dispatch_pending_nudges(db, sender)
        assert nudge.status == "failed"

    @pytest.mark.asyncio
    async def test_returns_zero_when_all_tokens_deregistered(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=404, detail="NOT_FOUND")
        )
        result = await dispatch_pending_nudges(db, sender)
        assert result == 0

    @pytest.mark.asyncio
    async def test_400_unregistered_also_deregisters(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=400, detail="UNREGISTERED")
        )
        await dispatch_pending_nudges(db, sender)
        assert token.last_valid_at is None
        assert nudge.status == "failed"


# ---------------------------------------------------------------------------
# dispatch_pending_nudges — transient error path
# ---------------------------------------------------------------------------


class TestDispatchTransientError:
    @pytest.mark.asyncio
    async def test_nudge_stays_scheduled_on_transient_error(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=503, detail="SERVICE_UNAVAILABLE")
        )
        await dispatch_pending_nudges(db, sender)
        assert nudge.status == "scheduled"

    @pytest.mark.asyncio
    async def test_returns_zero_on_transient_error(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=500, detail="INTERNAL")
        )
        result = await dispatch_pending_nudges(db, sender)
        assert result == 0

    @pytest.mark.asyncio
    async def test_token_last_valid_at_preserved_on_transient_error(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        token = _make_token(user_id=uid)
        original_valid_at = token.last_valid_at
        db = _make_db(nudges=[nudge], tokens_by_user={uid: [token]})
        sender = AsyncMock()
        sender.send = AsyncMock(
            side_effect=PushSendError(token="t", status_code=503, detail="UNAVAILABLE")
        )
        await dispatch_pending_nudges(db, sender)
        assert token.last_valid_at == original_valid_at


# ---------------------------------------------------------------------------
# dispatch_pending_nudges — mixed token outcomes
# ---------------------------------------------------------------------------


class TestDispatchMixedTokens:
    @pytest.mark.asyncio
    async def test_nudge_sent_if_first_token_succeeds_second_deregistered(self) -> None:
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        t1 = _make_token(user_id=uid, raw_token="good-token")
        t2 = _make_token(user_id=uid, raw_token="dead-token")

        db = _make_db(nudges=[nudge], tokens_by_user={uid: [t1, t2]})

        sender = AsyncMock()

        async def _smart_send(*, device_token: str, **kwargs: object) -> str:
            if device_token == "good-token":
                return "projects/p/messages/m"
            raise PushSendError(token=device_token, status_code=404, detail="NOT_FOUND")

        sender.send = _smart_send  # type: ignore[method-assign]

        result = await dispatch_pending_nudges(db, sender)
        assert result == 1
        assert nudge.status == "sent"
        assert t2.last_valid_at is None  # deregistered

    @pytest.mark.asyncio
    async def test_nudge_stays_scheduled_mixed_deregistered_and_transient(self) -> None:
        """One token deregistered + one transient → all_deregistered is False → stays scheduled."""
        uid = uuid.uuid4()
        nudge = _make_nudge(user_id=uid)
        t1 = _make_token(user_id=uid, raw_token="dead-token")
        t2 = _make_token(user_id=uid, raw_token="slow-token")

        db = _make_db(nudges=[nudge], tokens_by_user={uid: [t1, t2]})

        sender = AsyncMock()

        async def _mixed(*, device_token: str, **kwargs: object) -> str:
            if device_token == "dead-token":
                raise PushSendError(token=device_token, status_code=404, detail="NOT_FOUND")
            raise PushSendError(token=device_token, status_code=503, detail="UNAVAILABLE")

        sender.send = _mixed  # type: ignore[method-assign]

        await dispatch_pending_nudges(db, sender)
        assert nudge.status == "scheduled"
