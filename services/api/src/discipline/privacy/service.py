"""Privacy service — data collection and deletion scheduling.

Two public coroutines:
- :func:`collect_user_data`   — SELECT across all user-owned tables for DSAR export.
- :func:`schedule_deletion`   — mark ``users.deleted_at`` and ``users.purge_scheduled_at``.

Design notes
------------
Both functions accept an ``AsyncSession`` so the caller (the router) controls
the transaction boundary.  The service never commits; it only flushes.  The
router commits (or rolls back on error).

The data-collection query deliberately uses plain ``SELECT … WHERE user_id = ?``
with no cross-module ORM joins.  Each domain's data is fetched independently so
a missing table (during a migration) can be caught per-domain without aborting
the whole export.

TODO (next sprint): move export to an async job queue (SQS → ECS worker) and
return a presigned S3 URL instead of inline JSON.  The job should use the same
``collect_user_data`` function.  Wire in the S3_EXPORT_BUCKET setting from
``discipline.config.get_settings().s3_export_bucket`` when that path is active.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# GDPR Article 17 grace window before hard-delete executes.
GDPR_DELETION_GRACE_DAYS: int = 30


class PrivacyService:
    """Encapsulates DSAR and account-deletion logic."""

    # ------------------------------------------------------------------
    # Data export
    # ------------------------------------------------------------------

    async def collect_user_data(
        self,
        user_id: str,
        db: AsyncSession | None,
    ) -> dict[str, Any]:
        """Collect all user-owned rows from every relevant table.

        Returns a dict matching :class:`discipline.privacy.schemas.ExportData`.
        Each domain is fetched independently — a domain that raises is caught
        and returned as ``{"error": str(exc)}`` so the rest of the export still
        succeeds.  This is intentional: a partially-available export is better
        than a complete refusal for a data-subject rights request.

        PHI contract: the caller MUST NOT log the returned dict.  Only log
        that an export was requested, with the user_id for the audit trail.
        """
        if db is None:
            # No live DB session (dev/test path without a real database).
            # Return empty-but-valid structures so the export schema still
            # validates and the audit log entry is still written.
            return {
                "profile": {},
                "check_ins": [],
                "journal_entries": [],
                "assessment_sessions": [],
                "streak": {},
                "patterns": [],
                "consents": [],
            }

        profile = await self._fetch_profile(user_id, db)
        check_ins = await self._fetch_check_ins(user_id, db)
        journal_entries = await self._fetch_journals(user_id, db)
        assessment_sessions = await self._fetch_assessments(user_id, db)
        streak = await self._fetch_streak(user_id, db)
        patterns = await self._fetch_patterns(user_id, db)
        consents = await self._fetch_consents(user_id, db)

        return {
            "profile": profile,
            "check_ins": check_ins,
            "journal_entries": journal_entries,
            "assessment_sessions": assessment_sessions,
            "streak": streak,
            "patterns": patterns,
            "consents": consents,
        }

    # ------------------------------------------------------------------
    # Deletion scheduling
    # ------------------------------------------------------------------

    async def schedule_deletion(
        self,
        user_id: str,
        db: AsyncSession | None,
    ) -> datetime:
        """Soft-delete the user and schedule hard-delete after the grace window.

        Steps:
        1. Set ``users.deleted_at = now()`` — account is immediately inactive.
        2. Set ``users.purge_scheduled_at = now() + GDPR_DELETION_GRACE_DAYS``
           — the background worker picks this up and runs the hard-delete cascade.

        Returns the ``purge_scheduled_at`` timestamp so the router can include it
        in the response.

        The caller (router) is responsible for committing the session.

        Note on voice blobs: voice blobs are hard-deleted at 72h by S3 lifecycle
        + the nightly reconciliation worker (07_Security_Privacy §7).  That path
        is independent of this code and does not need to be triggered here — the
        lifecycle rule fires regardless of account state.
        """
        now = datetime.now(UTC)
        purge_at = now + timedelta(days=GDPR_DELETION_GRACE_DAYS)

        if db is None:
            # No live DB session — return the computed timestamp without
            # executing the UPDATE.  Used in tests and dev without a database.
            return purge_at

        await db.execute(
            text(
                """
                UPDATE users
                SET    deleted_at          = :deleted_at,
                       purge_scheduled_at  = :purge_at
                WHERE  external_id         = :external_id
                  AND  deleted_at          IS NULL
                """
            ),
            {
                "deleted_at": now,
                "purge_at": purge_at,
                "external_id": user_id,
            },
        )
        await db.flush()
        return purge_at

    # ------------------------------------------------------------------
    # Private helpers — one per data domain
    # ------------------------------------------------------------------

    async def _fetch_profile(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Users + user_profiles join."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT u.id,
                           u.external_id,
                           u.handle,
                           u.created_at,
                           u.last_active_at,
                           u.timezone,
                           u.locale,
                           u.calendar_preference,
                           u.digit_preference,
                           u.app_lock_enabled,
                           u.alt_icon_enabled,
                           u.mfa_enrolled,
                           up.target_behaviors,
                           up.baseline_severity,
                           up.ema_frequency,
                           up.local_hotline_country,
                           up.updated_at AS profile_updated_at
                    FROM   users u
                    LEFT JOIN user_profiles up ON up.user_id = u.id
                    WHERE  u.external_id = :external_id
                    LIMIT  1
                    """
                ),
                {"external_id": user_id},
            )
            row = result.mappings().first()
            if row is None:
                return {}
            return dict(row)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    async def _fetch_check_ins(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """signal_windows rows (aggregate biometric check-ins)."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT sw.ts,
                           sw.window_seconds,
                           sw.hrv_rmssd_ms,
                           sw.hr_bpm,
                           sw.respiration_rate,
                           sw.sleep_quality_score,
                           sw.phone_unlock_count,
                           sw.signal_source,
                           sw.device_confidence
                    FROM   signals_windows sw
                    JOIN   users u ON u.id = sw.user_id
                    WHERE  u.external_id = :external_id
                    ORDER BY sw.ts DESC
                    LIMIT  10000
                    """
                ),
                {"external_id": user_id},
            )
            return [dict(r) for r in result.mappings().all()]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc)}]

    async def _fetch_journals(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Journal metadata.  content_encrypted is excluded — the user already has
        the plaintext on their device; shipping encrypted bytes is unhelpful."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT j.id,
                           j.created_at,
                           j.kind,
                           j.word_count,
                           j.mood_score,
                           j.tags,
                           j.source
                    FROM   journals j
                    JOIN   users u ON u.id = j.user_id
                    WHERE  u.external_id = :external_id
                    ORDER BY j.created_at DESC
                    LIMIT  10000
                    """
                ),
                {"external_id": user_id},
            )
            return [dict(r) for r in result.mappings().all()]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc)}]

    async def _fetch_assessments(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Psychometric assessment sessions (PHQ-9, GAD-7, etc.)."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT ps.id,
                           ps.instrument,
                           ps.administered_at,
                           ps.total_score,
                           ps.severity_band,
                           ps.flagged_safety_item,
                           ps.completed
                    FROM   psychometric_sessions ps
                    JOIN   users u ON u.id = ps.user_id
                    WHERE  u.external_id = :external_id
                    ORDER BY ps.administered_at DESC
                    LIMIT  5000
                    """
                ),
                {"external_id": user_id},
            )
            return [dict(r) for r in result.mappings().all()]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc)}]

    async def _fetch_streak(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Resilience streak state (streak_state table)."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT ss.resilience_days,
                           ss.continuous_days,
                           ss.last_updated_at,
                           ss.behavior
                    FROM   streak_state ss
                    JOIN   users u ON u.id = ss.user_id
                    WHERE  u.external_id = :external_id
                    LIMIT  1
                    """
                ),
                {"external_id": user_id},
            )
            row = result.mappings().first()
            return dict(row) if row else {}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    async def _fetch_patterns(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Detected behavioral patterns."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT p.id,
                           p.kind,
                           p.summary,
                           p.confidence,
                           p.first_observed_at,
                           p.last_observed_at,
                           p.dismissed,
                           p.presented_count
                    FROM   patterns p
                    JOIN   users u ON u.id = p.user_id
                    WHERE  u.external_id = :external_id
                    ORDER BY p.first_observed_at DESC
                    """
                ),
                {"external_id": user_id},
            )
            return [dict(r) for r in result.mappings().all()]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc)}]

    async def _fetch_consents(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Consent records (type, version, when granted)."""
        try:
            result = await db.execute(
                text(
                    """
                    SELECT c.consent_type,
                           c.version,
                           c.granted_at
                    FROM   consents c
                    JOIN   users u ON u.id = c.user_id
                    WHERE  u.external_id = :external_id
                    ORDER BY c.granted_at DESC
                    """
                ),
                {"external_id": user_id},
            )
            return [dict(r) for r in result.mappings().all()]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc)}]


    # ------------------------------------------------------------------
    # Hard-delete cascade (GDPR Article 17 / DSAR)
    # ------------------------------------------------------------------

    async def run_pending_hard_deletes(
        self,
        cutoff: datetime,
        db: AsyncSession | None,
    ) -> list[str]:
        """Execute the hard-delete cascade for accounts past the grace window.

        Finds all users where ``purge_scheduled_at <= cutoff`` AND ``deleted_at
        IS NOT NULL`` (soft-deleted accounts), then deletes every row they own
        across all user-data tables.

        Returns a list of ``user_id`` strings that were hard-deleted so the
        calling worker can emit AUDIT log entries.

        PHI contract: callers MUST emit an AUDIT log entry per deleted user_id
        *before* calling this method — the audit entry must be committed before
        the data disappears so the retention stream is complete.

        Cascade order is explicit (foreign-key awareness):
          urge_sessions → psychometric_sessions → journals → signal_windows
          → streak_state → patterns → consents → user_profiles → users

        SQLAlchemy ON DELETE CASCADE handles some FK children, but we
        DELETE explicitly so the behaviour is testable without a live DB.
        """
        if db is None:
            return []

        # Find users due for hard-delete.
        result = await db.execute(
            text(
                """
                SELECT id, external_id
                FROM   users
                WHERE  deleted_at        IS NOT NULL
                  AND  purge_scheduled_at <= :cutoff
                LIMIT  500
                """
            ),
            {"cutoff": cutoff},
        )
        rows = result.mappings().all()
        user_ids = [str(r["id"]) for r in rows]

        if not user_ids:
            return []

        # Parameterised IN clause.  SQLAlchemy text() doesn't natively support
        # lists; use a subquery pattern so no f-string injection is possible.
        for user_id in user_ids:
            await self._hard_delete_one(user_id, db)

        await db.flush()
        return user_ids

    async def _hard_delete_one(self, user_id: str, db: AsyncSession) -> None:
        """Delete all rows owned by a single user_id (UUID string)."""
        # Each DELETE is scoped to the internal UUID — never the external_id —
        # so a clerk_sub collision cannot accidentally wipe the wrong account.
        for table in (
            "urge_sessions",
            "psychometric_sessions",
            "journals",
            "signals_windows",
            "streak_state",
            "patterns",
            "consents",
            "user_profiles",
        ):
            await db.execute(
                text(f"DELETE FROM {table} WHERE user_id = :uid"),  # noqa: S608
                {"uid": user_id},
            )

        await db.execute(
            text("DELETE FROM users WHERE id = :uid"),
            {"uid": user_id},
        )


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_service: PrivacyService | None = None


def get_privacy_service() -> PrivacyService:
    """Return (and lazily construct) the module-level PrivacyService singleton."""
    global _service
    if _service is None:
        _service = PrivacyService()
    return _service
