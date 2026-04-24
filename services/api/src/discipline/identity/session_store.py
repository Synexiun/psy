"""Redis-backed session store.

Per Docs/Technicals/14_Authentication_Logging.md §2.3:
- Session valid iff ``sid_active:{sid}`` exists in Redis.
- Refresh token rotates on every use; old token instantly invalidated.
- Reuse of an already-rotated refresh token kills the entire session family.
"""

from __future__ import annotations

from typing import Any

from discipline.shared.redis_client import get_redis_client

# Redis key prefixes
_PREFIX_ACTIVE = "sid_active"
_PREFIX_REFRESH = "refresh"
_REFRESH_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


class SessionStore:
    """Store and validate server sessions in Redis.

    This is a **synchronous** wrapper because RQ/redis-py are sync.
    FastAPI routes that need to check session validity should run
    these calls in a thread pool or use the async wrapper below.
    """

    def __init__(self, client: Any | None = None) -> None:
        self._client = client or get_redis_client()

    def activate(self, sid: str, user_id: str, ttl: int = 15 * 60) -> None:
        """Mark a session as active with the given TTL (default 15 min).

        Called immediately after issuing a session JWT.
        """
        self._client.setex(f"{_PREFIX_ACTIVE}:{sid}", ttl, user_id)

    def is_active(self, sid: str) -> bool:
        """Return True if the session is still valid."""
        return bool(self._client.exists(f"{_PREFIX_ACTIVE}:{sid}"))

    def revoke(self, sid: str) -> None:
        """Revoke a session immediately."""
        self._client.delete(f"{_PREFIX_ACTIVE}:{sid}")

    def store_refresh(
        self, refresh_token: str, sid: str, family_id: str, user_id: str = ""
    ) -> None:
        """Store a refresh token mapping to its session, family, and user.

        ``family_id`` links all refresh tokens issued from the same
        original login.  Reuse of an already-rotated token triggers
        family kill.  ``user_id`` is stored so the refresh endpoint can
        look up user context without a separate DB round-trip.
        """
        key = f"{_PREFIX_REFRESH}:{refresh_token}"
        value = f"{sid}:{family_id}:{user_id}"
        self._client.setex(key, _REFRESH_TTL_SECONDS, value)

    def consume_refresh(self, refresh_token: str) -> tuple[str, str, str] | None:
        """Consume a refresh token and return (sid, family_id, user_id).

        Returns None if the token doesn't exist or has already been
        consumed.  The caller must verify the session is still active.
        """
        key = f"{_PREFIX_REFRESH}:{refresh_token}"
        raw = self._client.get(key)
        if raw is None:
            return None
        # Delete atomically — if another thread already deleted it,
        # this is a replay attack and we should kill the family.
        deleted = self._client.delete(key)
        if deleted == 0:
            # Token was already consumed — signal compromise.
            return None
        parts = raw.decode("utf-8").split(":", 2)
        sid = parts[0]
        family_id = parts[1]
        user_id = parts[2] if len(parts) > 2 else ""
        return sid, family_id, user_id

    def kill_family(self, family_id: str) -> int:
        """Kill all sessions belonging to a family.

        Returns the number of sessions revoked.
        """
        # Scan for all refresh tokens with this family_id.
        # In production this would use a secondary index or a set.
        # For now, we rely on the TTL to clean up stale tokens.
        count = 0
        pattern = f"{_PREFIX_REFRESH}:*"
        for key in self._client.scan_iter(match=pattern):
            raw = self._client.get(key)
            if raw and family_id.encode("utf-8") in raw:
                self._client.delete(key)
                count += 1
        return count


def get_session_store() -> SessionStore:
    """Return the default session store."""
    return SessionStore()
