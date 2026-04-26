"""Unit tests for _hash_email() in discipline.identity.repository.

_hash_email(email) → str
  SHA-256 hex digest of the email address (UTF-8 encoded).
  Used as the lookup key stored in the database instead of the plaintext
  email address — the caller can hash a candidate email and compare
  hashes without storing recoverable PII.

Contracts:
  - Always returns a 64-character lowercase hex string.
  - Deterministic: same input → same output.
  - Different emails → different hashes (collision resistance at test scale).
  - Matches the hashlib.sha256 reference implementation.
  - Non-ASCII email addresses are handled via UTF-8 encoding.
"""

from __future__ import annotations

import hashlib

from discipline.identity.repository import _hash_email


class TestHashEmail:
    def test_returns_64_char_hex_string(self) -> None:
        result = _hash_email("user@example.com")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self) -> None:
        assert _hash_email("a@b.com") == _hash_email("a@b.com")

    def test_different_emails_different_hashes(self) -> None:
        assert _hash_email("alice@example.com") != _hash_email("bob@example.com")

    def test_matches_sha256_reference(self) -> None:
        email = "test@disciplineos.com"
        expected = hashlib.sha256(email.encode("utf-8")).hexdigest()
        assert _hash_email(email) == expected

    def test_case_sensitive(self) -> None:
        # Hash is case-sensitive: Alice@example.com ≠ alice@example.com
        assert _hash_email("Alice@example.com") != _hash_email("alice@example.com")

    def test_non_ascii_email_encoded_as_utf8(self) -> None:
        email = "üser@example.com"
        expected = hashlib.sha256(email.encode("utf-8")).hexdigest()
        assert _hash_email(email) == expected
