"""Tests for ``discipline.notifications.push_sender``.

All FCM HTTP calls are intercepted via ``unittest.mock.patch`` so no real
network traffic is generated.  Tests exercise:

  - Correct Authorization header construction
  - Message ID extraction from a successful response
  - ``PushSendError`` raised on FCM 404 (UNREGISTERED token)
  - ``should_deregister`` True for 404, False for 500
  - Data values cast to strings (FCM requirement)
  - Token cache hit avoids a second credential round-trip
  - Badge number appears in the APNs payload
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discipline.notifications.push_sender import PushSendError, PushSender

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FCM_PROJECT = "test-project-123"
FCM_URL = f"https://fcm.googleapis.com/v1/projects/{FCM_PROJECT}/messages:send"
FAKE_TOKEN = "fake-access-token-xyz"
DEVICE_TOKEN = "device_fcm_token_abcdef"
RETURNED_MSG_NAME = f"projects/{FCM_PROJECT}/messages/msg_001"


def _make_sender() -> PushSender:
    return PushSender(project_id=FCM_PROJECT)


def _mock_response(status_code: int, body: dict[str, Any]) -> MagicMock:
    """Build a minimal mock that quacks like an httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.json.return_value = body
    resp.text = json.dumps(body)
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sender_with_token(monkeypatch: pytest.MonkeyPatch) -> PushSender:
    """Return a PushSender with the access token pre-cached."""
    from datetime import UTC, datetime, timedelta

    s = _make_sender()
    # Pre-warm the cache so _get_access_token() is not called during tests
    # that focus purely on the send path.
    s._access_token_cache = (FAKE_TOKEN, datetime.now(UTC) + timedelta(hours=1))
    return s


# ---------------------------------------------------------------------------
# Test: successful send
# ---------------------------------------------------------------------------


class TestPushSenderSend:
    async def test_send_posts_to_fcm_url(
        self, sender_with_token: PushSender
    ) -> None:
        """POST goes to the correct FCM v1 endpoint."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="Hello",
                body="World",
            )

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert call_kwargs[0][0] == FCM_URL

    async def test_send_sets_authorization_header(
        self, sender_with_token: PushSender
    ) -> None:
        """The Authorization header must be ``Bearer <access_token>``."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="Hello",
                body="World",
            )

        _, kwargs = mock_client.post.call_args
        assert kwargs["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"

    async def test_send_returns_message_id(
        self, sender_with_token: PushSender
    ) -> None:
        """Returns the FCM message name on success."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            result = await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="Hello",
                body="World",
            )

        assert result == RETURNED_MSG_NAME

    async def test_send_embeds_device_token_in_payload(
        self, sender_with_token: PushSender
    ) -> None:
        """The FCM message body must include the device token."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="T",
                body="B",
            )

        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["message"]["token"] == DEVICE_TOKEN


# ---------------------------------------------------------------------------
# Test: error handling
# ---------------------------------------------------------------------------


class TestPushSendError:
    async def test_raises_push_send_error_on_404(
        self, sender_with_token: PushSender
    ) -> None:
        """FCM 404 (unregistered token) raises ``PushSendError``."""
        mock_resp = _mock_response(
            404, {"error": {"message": "Requested entity was not found."}}
        )

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            with pytest.raises(PushSendError) as exc_info:
                await sender_with_token.send(
                    device_token=DEVICE_TOKEN,
                    title="T",
                    body="B",
                )

        assert exc_info.value.status_code == 404
        assert exc_info.value.token == DEVICE_TOKEN

    async def test_should_deregister_true_for_404(
        self, sender_with_token: PushSender
    ) -> None:
        """``should_deregister`` is True when FCM returns 404."""
        mock_resp = _mock_response(
            404, {"error": {"message": "Requested entity was not found."}}
        )

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            with pytest.raises(PushSendError) as exc_info:
                await sender_with_token.send(
                    device_token=DEVICE_TOKEN,
                    title="T",
                    body="B",
                )

        assert exc_info.value.should_deregister is True

    async def test_should_deregister_true_for_400_unregistered(
        self, sender_with_token: PushSender
    ) -> None:
        """``should_deregister`` is True for 400 with UNREGISTERED message."""
        mock_resp = _mock_response(
            400,
            {"error": {"message": "The registration token is not a valid FCM registration token (UNREGISTERED)."}},
        )

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            with pytest.raises(PushSendError) as exc_info:
                await sender_with_token.send(
                    device_token=DEVICE_TOKEN,
                    title="T",
                    body="B",
                )

        assert exc_info.value.should_deregister is True

    async def test_should_deregister_false_for_500(
        self, sender_with_token: PushSender
    ) -> None:
        """``should_deregister`` is False for transient server errors."""
        mock_resp = _mock_response(
            500, {"error": {"message": "Internal server error"}}
        )

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            with pytest.raises(PushSendError) as exc_info:
                await sender_with_token.send(
                    device_token=DEVICE_TOKEN,
                    title="T",
                    body="B",
                )

        assert exc_info.value.should_deregister is False

    async def test_should_deregister_false_for_503(
        self, sender_with_token: PushSender
    ) -> None:
        """503 Service Unavailable is transient — do not deregister."""
        mock_resp = _mock_response(
            503, {"error": {"message": "Service unavailable"}}
        )

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            with pytest.raises(PushSendError) as exc_info:
                await sender_with_token.send(
                    device_token=DEVICE_TOKEN,
                    title="T",
                    body="B",
                )

        assert exc_info.value.should_deregister is False


# ---------------------------------------------------------------------------
# Test: data casting
# ---------------------------------------------------------------------------


class TestDataCasting:
    async def test_data_values_cast_to_strings(
        self, sender_with_token: PushSender
    ) -> None:
        """FCM requires all data values to be strings — integers must be cast."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="T",
                body="B",
                data={"count": "42", "score": "7"},  # type: ignore[arg-type]
            )

        _, kwargs = mock_client.post.call_args
        data_payload = kwargs["json"]["message"]["data"]
        for v in data_payload.values():
            assert isinstance(v, str), f"Expected str, got {type(v)}: {v!r}"

    async def test_data_non_string_values_are_coerced(
        self, sender_with_token: PushSender
    ) -> None:
        """Non-string data values (int, bool) are coerced to str."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            # Pass mixed-type dict — type: ignore needed since we're testing
            # the runtime coercion path.
            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="T",
                body="B",
                data={"count": 42, "flag": True},  # type: ignore[dict-item]
            )

        _, kwargs = mock_client.post.call_args
        data_payload = kwargs["json"]["message"]["data"]
        assert data_payload["count"] == "42"
        assert data_payload["flag"] == "True"

    async def test_no_data_key_absent_from_message(
        self, sender_with_token: PushSender
    ) -> None:
        """When ``data`` is not passed the ``data`` key is absent from the message."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="T",
                body="B",
            )

        _, kwargs = mock_client.post.call_args
        assert "data" not in kwargs["json"]["message"]


# ---------------------------------------------------------------------------
# Test: APNs badge
# ---------------------------------------------------------------------------


class TestBadge:
    async def test_badge_included_in_apns_payload(
        self, sender_with_token: PushSender
    ) -> None:
        """Badge count appears under ``apns.payload.aps.badge``."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="T",
                body="B",
                badge=3,
            )

        _, kwargs = mock_client.post.call_args
        apns = kwargs["json"]["message"]["apns"]
        assert apns["payload"]["aps"]["badge"] == 3

    async def test_no_badge_apns_key_absent(
        self, sender_with_token: PushSender
    ) -> None:
        """When ``badge`` is not supplied the ``apns`` key is absent."""
        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender_with_token.send(
                device_token=DEVICE_TOKEN,
                title="T",
                body="B",
            )

        _, kwargs = mock_client.post.call_args
        assert "apns" not in kwargs["json"]["message"]


# ---------------------------------------------------------------------------
# Test: token caching
# ---------------------------------------------------------------------------


class TestTokenCache:
    async def test_cached_token_reused_across_sends(self) -> None:
        """The access token is cached; the credential endpoint is hit once."""
        from datetime import UTC, datetime, timedelta

        sender = _make_sender()
        sender._access_token_cache = (
            FAKE_TOKEN,
            datetime.now(UTC) + timedelta(hours=1),
        )

        mock_resp = _mock_response(200, {"name": RETURNED_MSG_NAME})

        with patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            await sender.send(device_token=DEVICE_TOKEN, title="T1", body="B1")
            await sender.send(device_token=DEVICE_TOKEN, title="T2", body="B2")

        # Only two POST calls (both to FCM), no GET to the metadata/token server.
        assert mock_client.post.call_count == 2

    async def test_expired_cache_triggers_reauth(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An expired cache entry causes a new credential fetch.

        We stub ``_jwt_auth`` to avoid needing a real RSA key in tests
        while still exercising the cache-expiry and re-population path.
        """
        from datetime import UTC, datetime, timedelta

        sender = _make_sender()
        # Expired cache — any send should trigger a fresh token fetch.
        sender._access_token_cache = (
            "old-token",
            datetime.now(UTC) - timedelta(minutes=1),
        )

        new_token = "refreshed-access-token"

        # Stub _jwt_auth so the SA JSON env var triggers the service-account
        # path without needing a real private key.
        monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_JSON", "e30=")  # base64("{}")

        with (
            patch.object(
                PushSender,
                "_jwt_auth",
                new=AsyncMock(return_value=new_token),
            ) as mock_jwt_auth,
            patch("discipline.notifications.push_sender.httpx.AsyncClient") as mock_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(
                return_value=_mock_response(200, {"name": RETURNED_MSG_NAME})
            )
            mock_cls.return_value = mock_client

            await sender.send(device_token=DEVICE_TOKEN, title="T", body="B")

        # _jwt_auth was called exactly once to refresh the token.
        mock_jwt_auth.assert_called_once()
        # Cache was updated with the new token.
        assert sender._access_token_cache is not None
        assert sender._access_token_cache[0] == new_token


