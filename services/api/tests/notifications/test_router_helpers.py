"""Unit tests for _hash_token() and _encrypt_token() pure helpers in
discipline.notifications.router.

_hash_token(token) → str
  SHA-256 hex digest of the token string.  Deterministic: same input
  always produces the same 64-character hex output.  Used to store a
  non-reversible reference to the push token without retaining the
  plaintext in the app database.

_encrypt_token(token) → str
  STUB for KMS envelope encryption; in production this calls AWS KMS.
  Current implementation: base64url-like encoding.  The stub is
  reversible (base64.b64decode), which is intentional for dev/test only.

Both helpers are pure functions with no I/O and no state.
"""

from __future__ import annotations

import base64
import hashlib

from discipline.notifications.router import _encrypt_token, _hash_token


# ---------------------------------------------------------------------------
# _hash_token — SHA-256 deterministic hex digest
# ---------------------------------------------------------------------------


class TestHashToken:
    def test_returns_64_char_hex_string(self) -> None:
        result = _hash_token("my-push-token")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic_same_input(self) -> None:
        assert _hash_token("token-abc") == _hash_token("token-abc")

    def test_different_tokens_different_hashes(self) -> None:
        assert _hash_token("token-a") != _hash_token("token-b")

    def test_matches_sha256_reference(self) -> None:
        token = "ExPoNeNtIaLpUsHtOkEn"
        expected = hashlib.sha256(token.encode()).hexdigest()
        assert _hash_token(token) == expected

    def test_empty_string_produces_known_sha256(self) -> None:
        # SHA-256("") is a fixed constant
        expected = hashlib.sha256(b"").hexdigest()
        assert _hash_token("") == expected

    def test_unicode_token_hashed(self) -> None:
        result = _hash_token("tökén-with-ünicode")
        assert isinstance(result, str)
        assert len(result) == 64


# ---------------------------------------------------------------------------
# _encrypt_token — base64 stub (production: KMS)
# ---------------------------------------------------------------------------


class TestEncryptToken:
    def test_returns_string(self) -> None:
        assert isinstance(_encrypt_token("my-token"), str)

    def test_result_is_base64_decodable(self) -> None:
        result = _encrypt_token("my-token")
        decoded = base64.b64decode(result).decode()
        assert decoded == "my-token"

    def test_roundtrip_recovers_original(self) -> None:
        original = "ExPoToken-XYZ-789"
        encoded = _encrypt_token(original)
        recovered = base64.b64decode(encoded).decode()
        assert recovered == original

    def test_deterministic(self) -> None:
        assert _encrypt_token("t") == _encrypt_token("t")

    def test_different_tokens_different_encodings(self) -> None:
        assert _encrypt_token("token-a") != _encrypt_token("token-b")
