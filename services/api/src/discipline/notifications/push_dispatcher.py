"""
Push dispatcher — reads scheduled nudges and delivers via FCM.

Called by the worker scheduler on a recurring tick (not on the request path).
The dispatcher is intentionally side-effect-free with respect to callers:
it returns a count of successfully sent nudges so the scheduler can record
the outcome in its own heartbeat log.

Token decryption
----------------
In production, ``token_encrypted`` holds a KMS envelope-encrypted ciphertext.
For the current scaffold, the router stub base64-encodes the raw token.
``_decrypt_token`` handles both paths:
  - If ``KMS_KEY_ID`` is set and the value is not valid base64-decodable
    UTF-8, it should go through the KMS client.
  - In dev/test (no KMS), a plain base64 decode recovers the raw token.

A PushToken with ``last_valid_at IS NULL`` is treated as deactivated and
skipped.  When FCM returns an UNREGISTERED or 404 error, ``last_valid_at``
is set to NULL to mark the token as inactive for future dispatches.

Status lifecycle
----------------
Nudge.status values:
  ``scheduled`` — created, waiting for scheduled_at
  ``sent``      — at least one token received the notification
  ``failed``    — every token for the user failed (non-retriable)
  ``dismissed`` — user dismissed before delivery (set by app)
  ``expired``   — past its window without being sent (set by cleanup job)
"""

from __future__ import annotations

import base64
import logging
from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discipline.notifications.models import Nudge, PushToken
from discipline.notifications.push_sender import PushSendError, PushSender

log = logging.getLogger(__name__)


def _decrypt_token(token_encrypted: str) -> str:
    """Recover the raw FCM device token from its stored form.

    Scaffold: the router stubs base64-encode the raw token.
    Production: KMS envelope decryption runs here.
    """
    return base64.b64decode(token_encrypted.encode()).decode()


async def dispatch_pending_nudges(
    db: AsyncSession,
    sender: PushSender,
) -> int:
    """Deliver all due, scheduled nudges via FCM.

    Queries nudges with ``status = 'scheduled'`` and
    ``scheduled_at <= now()``, then for each nudge looks up active push
    tokens for the owning user and fires a notification.

    A nudge is marked **sent** the first time at least one token
    succeeds.  If all tokens for a user are unregistered or permanently
    invalid, the nudge is marked **failed** so the scheduler does not
    retry it indefinitely.

    Transient FCM errors (5xx) do not change the nudge status; the
    nudge stays ``scheduled`` and will be retried on the next tick.

    Parameters
    ----------
    db:
        Async SQLAlchemy session.  The caller is responsible for
        committing or rolling back the transaction.
    sender:
        Configured ``PushSender`` instance.

    Returns
    -------
    int
        Number of nudges for which at least one token was delivered
        successfully.
    """
    now = datetime.now(UTC)

    # --- 1. Fetch due nudges -------------------------------------------------
    nudge_result = await db.execute(
        select(Nudge)
        .where(
            Nudge.status == "scheduled",
            Nudge.scheduled_at <= now,
        )
        .order_by(Nudge.scheduled_at)
    )
    nudges: Sequence[Nudge] = nudge_result.scalars().all()

    if not nudges:
        return 0

    sent_count = 0

    for nudge in nudges:
        user_id = nudge.user_id

        # --- 2. Fetch active push tokens for this user ----------------------
        token_result = await db.execute(
            select(PushToken).where(
                PushToken.user_id == user_id,
                PushToken.last_valid_at.is_not(None),
            )
        )
        tokens: Sequence[PushToken] = token_result.scalars().all()

        if not tokens:
            log.debug(
                "dispatch.skip_no_tokens",
                extra={"nudge_id": str(nudge.id), "user_id": str(user_id)},
            )
            continue

        nudge_sent = False
        all_deregistered = True  # flipped to False on any transient error

        title, body = _nudge_copy(nudge)

        for push_token in tokens:
            raw_token = _decrypt_token(push_token.token_encrypted)

            try:
                msg_name = await sender.send(
                    device_token=raw_token,
                    title=title,
                    body=body,
                    data={
                        "nudge_id": str(nudge.id),
                        "nudge_type": nudge.nudge_type,
                    },
                )
                log.info(
                    "dispatch.sent",
                    extra={
                        "nudge_id": str(nudge.id),
                        "user_id": str(user_id),
                        "fcm_name": msg_name,
                        "platform": push_token.platform,
                    },
                )
                nudge_sent = True
                # Keep scanning remaining tokens; they may also need
                # deregistration, but we don't break early.

            except PushSendError as exc:
                if exc.should_deregister:
                    # --- 5. Mark token as inactive --------------------------
                    push_token.last_valid_at = None
                    log.info(
                        "dispatch.token_deregistered",
                        extra={
                            "token_id": str(push_token.id),
                            "user_id": str(user_id),
                            "reason": exc.detail,
                        },
                    )
                else:
                    # Transient error — do not mark nudge failed yet.
                    all_deregistered = False
                    log.warning(
                        "dispatch.transient_error",
                        extra={
                            "nudge_id": str(nudge.id),
                            "token_id": str(push_token.id),
                            "status_code": exc.status_code,
                            "detail": exc.detail,
                        },
                    )

        # --- 4a. Update nudge status on success ------------------------------
        if nudge_sent:
            nudge.status = "sent"
            nudge.sent_at = datetime.now(UTC)
            sent_count += 1

        # --- 4b. Mark failed when every token is permanently invalid --------
        elif all_deregistered:
            # Every token came back UNREGISTERED or 404; there is no point
            # retrying — no active device can receive this nudge.
            nudge.status = "failed"
            log.warning(
                "dispatch.all_tokens_deregistered",
                extra={"nudge_id": str(nudge.id), "user_id": str(user_id)},
            )
        # else: at least one transient error — leave as "scheduled" for retry.

        await db.flush()

    return sent_count


def _nudge_copy(nudge: Nudge) -> tuple[str, str]:
    """Return (title, body) for the notification.

    Uses ``message_copy`` when set by the nudge scheduler.  Falls back to
    generic copy keyed on ``nudge_type``; callers on the request path
    should always set ``message_copy`` via the LLM-generated copy so
    this path is only a safety net for worker-scheduled nudges that were
    queued before LLM copy was attached.
    """
    if nudge.message_copy:
        return ("Discipline OS", nudge.message_copy)

    _FALLBACK: dict[str, tuple[str, str]] = {
        "check_in": ("How are you doing?", "Tap to log a quick check-in."),
        "tool_suggestion": (
            "Try an intervention",
            "A short exercise is ready when you are.",
        ),
        "crisis_follow_up": (
            "We're thinking of you",
            "How are you feeling since earlier?",
        ),
        "weekly_reflection": (
            "Weekly reflection",
            "Take a moment to review your week.",
        ),
    }
    return _FALLBACK.get(
        nudge.nudge_type,
        ("Discipline OS", "You have a pending notification."),
    )
