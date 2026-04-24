"""
Push notification sender supporting FCM v1 (HTTP) for both Android and iOS.

FCM v1 API supports APNs passthrough natively — a single FCM token works for
both Android and iOS when using the Firebase Admin SDK or direct HTTP v1 API.
This avoids maintaining separate APNs certificates.

Configuration:
  FIREBASE_PROJECT_ID            — GCP project ID
  FIREBASE_SERVICE_ACCOUNT_JSON  — base64-encoded service account JSON
    OR
  GOOGLE_APPLICATION_DEFAULT_CREDENTIALS — uses GCP ADC (ECS task role)

Rate limits:
  FCM v1: 600k messages/minute per project (far above our needs)
  Per device: no documented hard limit; don't exceed 1/hour for nudges

JWT creation for the service account credential path uses the ``cryptography``
library (already a declared dependency) to sign the assertion so we avoid
adding the ``google-auth`` package just for this one module.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Optional

import httpx

log = logging.getLogger(__name__)

FCM_SEND_URL = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_TOKEN_TTL_SECONDS = 3600  # Google-issued tokens expire in 1h; we cache for 50 min


class PushSendError(Exception):
    """Raised when FCM rejects a send attempt."""

    def __init__(self, token: str, status_code: int, detail: str) -> None:
        super().__init__(f"FCM send failed ({status_code}): {detail}")
        self.token = token
        self.status_code = status_code
        self.detail = detail

    @property
    def should_deregister(self) -> bool:
        """True if the device token should be removed (invalid/unregistered).

        FCM returns 404 for unregistered tokens and 400 with
        ``UNREGISTERED`` in the error message for deactivated tokens.
        Both indicate the token will never receive messages and should be
        removed from the database rather than retried.
        """
        return self.status_code in (404, 400) and (
            self.status_code == 404 or "UNREGISTERED" in self.detail
        )


def _make_jwt(sa: dict[str, str]) -> str:
    """Create a signed JWT assertion for the Google OAuth2 token exchange.

    Uses RS256 signing via the ``cryptography`` library.  This avoids
    adding the ``google-auth`` package solely for FCM.
    """
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": sa["client_email"],
        "sub": sa["client_email"],
        "aud": _GOOGLE_TOKEN_URL,
        "iat": now,
        "exp": now + _TOKEN_TTL_SECONDS,
        "scope": _SCOPE,
    }

    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header_enc = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_enc = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_enc}.{payload_enc}".encode()

    private_key = serialization.load_pem_private_key(
        sa["private_key"].encode(),
        password=None,
    )
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[call-arg]
    return f"{header_enc}.{payload_enc}.{_b64url(signature)}"


class PushSender:
    """Sends push notifications via the FCM v1 HTTP API.

    Instantiate once per worker process and reuse across sends; the
    OAuth2 token cache avoids unnecessary round-trips to the token
    endpoint.

    Usage::

        sender = PushSender()
        msg_id = await sender.send(
            device_token="<FCM registration token>",
            title="Time for a check-in",
            body="Your 3 pm check-in is ready.",
        )
    """

    def __init__(self, project_id: Optional[str] = None) -> None:
        self.project_id = project_id or os.getenv("FIREBASE_PROJECT_ID", "")
        # Cache: (access_token, expires_at_utc)
        self._access_token_cache: Optional[tuple[str, datetime]] = None

    async def _get_access_token(self) -> str:
        """Return a valid OAuth2 bearer token for the FCM v1 API.

        Tokens are cached for 50 minutes (they expire in 60) to amortise
        the cost of the token exchange across many sends.

        Resolution order:
          1. ``FIREBASE_SERVICE_ACCOUNT_JSON`` env-var (base64-encoded
             service account JSON) — used on ECS tasks without Workload
             Identity, or in CI.
          2. GCP metadata server (``http://metadata.google.internal/…``)
             — used when the ECS task role has Workload Identity Federation
             configured.  Works transparently; no credentials to manage.
        """
        # Check cache first
        if self._access_token_cache is not None:
            token, expires_at = self._access_token_cache
            if datetime.now(UTC) < expires_at:
                return token

        sa_json_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        if sa_json_b64:
            token = await self._jwt_auth(
                json.loads(base64.b64decode(sa_json_b64))
            )
        else:
            # Use GCP ADC via the instance metadata server.
            # Works on GCE / Cloud Run / ECS + Workload Identity Federation.
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://metadata.google.internal/computeMetadata/v1"
                    "/instance/service-accounts/default/token",
                    headers={"Metadata-Flavor": "Google"},
                    timeout=5,
                )
                resp.raise_for_status()
                token = resp.json()["access_token"]

        self._access_token_cache = (
            token,
            datetime.now(UTC) + timedelta(minutes=50),
        )
        return token

    async def _jwt_auth(self, sa: dict[str, str]) -> str:
        """Exchange a signed JWT assertion for a Google OAuth2 access token."""
        assertion = _make_jwt(sa)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return str(resp.json()["access_token"])

    async def send(
        self,
        *,
        device_token: str,
        title: str,
        body: str,
        data: Optional[dict[str, str]] = None,
        badge: Optional[int] = None,
    ) -> str:
        """Send a push notification to a single device.

        Parameters
        ----------
        device_token:
            The FCM registration token for the target device.
        title:
            Notification title string (shown in the notification tray).
        body:
            Notification body text.
        data:
            Optional key-value pairs delivered to the app in the data
            payload.  All values **must** be strings (FCM requirement);
            non-string values are cast automatically.
        badge:
            iOS badge count.  Passed via the APNs ``aps.badge`` field.
            Ignored on Android.

        Returns
        -------
        str
            The FCM message name (``projects/{project}/messages/{msg_id}``).

        Raises
        ------
        PushSendError
            On any FCM error.  Check ``should_deregister`` to decide
            whether to remove the token from the database.
        """
        access_token = await self._get_access_token()

        message: dict[str, object] = {
            "token": device_token,
            "notification": {"title": title, "body": body},
        }
        if data:
            # FCM requires all data values to be strings.
            message["data"] = {k: str(v) for k, v in data.items()}
        if badge is not None:
            message["apns"] = {"payload": {"aps": {"badge": badge}}}

        url = FCM_SEND_URL.format(project_id=self.project_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={"message": message},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

        if not resp.is_success:
            try:
                error = resp.json().get("error", {})
                detail = error.get("message", "unknown")
            except Exception:
                detail = resp.text or "unknown"
            log.warning(
                "FCM send failed",
                extra={
                    "status_code": resp.status_code,
                    "detail": detail,
                    "token_prefix": device_token[:12],
                },
            )
            raise PushSendError(device_token, resp.status_code, detail)

        msg_name: str = resp.json()["name"]
        log.debug("FCM send ok", extra={"fcm_message_name": msg_name})
        return msg_name
