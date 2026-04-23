"""Relapse router tests — compassion-first copy contract.

``POST /v1/relapses`` is clinical-QA-gated: the response copy is a signed
template (CLAUDE.md Rule #4) and the resilience streak must never communicate
a reset.  A failing test here is a clinical defect, not a copy-edit bug.
"""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.clinical.repository import reset_relapse_repository


@pytest.fixture(autouse=True)
def _clear_relapses() -> None:
    reset_relapse_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_URL = "/v1/relapses"
_IK_HEADER = {"Idempotency-Key": "test-idempotency-key"}

# Shame-adjacent tokens that MUST NOT appear anywhere in the relapse response.
# Clinical QA contract: this lexicon is drawn from Docs/bUSINESS/09_Brand_Positioning.md §voice
# and the compassion-first relapse framing rule in CLAUDE.md.
_SHAME_TOKENS: tuple[str, ...] = (
    "failed",
    "failure",
    "shame",
    "weak",
    "worthless",
    "reset",
    "broke",
    "lost",
    "gave up",
    "couldn't",
    "you should",
    "you must",
    "how could",
)


def _valid_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "occurred_at": "2026-04-19T10:00:00Z",
        "behavior": "alcohol_use",
        "severity": 3,
        "context_tags": [],
    }
    base.update(overrides)
    return base


def _collect_response_text(body: dict[str, object]) -> str:
    parts: list[str] = []
    for v in body.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(item for item in v if isinstance(item, str))
    return " ".join(parts).lower()


# =============================================================================
# TestRelapseHappyPath
# =============================================================================


class TestRelapseHappyPath:
    def test_happy_path_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER)
        assert response.status_code == 201

    def test_response_has_relapse_id(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        relapse_id = body["relapse_id"]
        assert isinstance(relapse_id, str)
        # Must be parseable as UUID
        uuid.UUID(relapse_id)

    def test_relapse_id_is_unique_across_calls(self, client: TestClient) -> None:
        id1 = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()["relapse_id"]
        id2 = client.post(_URL, json=_valid_payload(), headers={"Idempotency-Key": "key2"}).json()["relapse_id"]
        assert id1 != id2

    def test_response_has_next_steps_list(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert isinstance(body["next_steps"], list)
        assert len(body["next_steps"]) > 0

    def test_response_has_compassion_message_field(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert isinstance(body["compassion_message"], str)
        assert len(body["compassion_message"]) > 0

    def test_resilience_preserved_flag_is_true(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert body["resilience_preserved"] is True

    def test_reviewed_flag_is_false_by_default(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert body["reviewed"] is False

    def test_context_tags_defaults_to_empty_list(self, client: TestClient) -> None:
        """context_tags is optional; omitting it must still produce 201."""
        payload = {"occurred_at": "2026-04-19T10:00:00Z", "behavior": "alcohol_use", "severity": 2}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 201

    def test_context_tags_accepted_when_provided(self, client: TestClient) -> None:
        payload = _valid_payload(context_tags=["stress", "social_pressure"])
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 201


# =============================================================================
# TestCompassionFirstCopy  — non-negotiable clinical rule (CLAUDE.md Rule #4)
# =============================================================================


class TestCompassionFirstCopy:
    """Relapse copy must be compassion-first.  No shame, no 'you failed', no
    'streak reset' framing.  These tests must never be skipped or weakened —
    violating them is a clinical defect, not a style nitpick."""

    def test_message_contains_no_shame_tokens(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        text = _collect_response_text(body)
        for token in _SHAME_TOKENS:
            assert token not in text, (
                f"relapse copy leaked shame-adjacent token {token!r}: {text!r}"
            )

    def test_next_steps_contain_no_shame_tokens(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        steps_text = " ".join(body["next_steps"]).lower()
        for token in _SHAME_TOKENS:
            assert token not in steps_text, (
                f"next_steps leaked shame-adjacent token {token!r}"
            )

    def test_compassion_message_has_no_streak_reset_framing(self, client: TestClient) -> None:
        """Resilience streak never resets — CLAUDE.md Rule #3.  The relapse
        message must never use 'streak reset', 'reset your streak', etc."""
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        text = body["compassion_message"].lower()
        assert "streak reset" not in text
        assert "reset your streak" not in text
        assert "reset" not in text

    def test_compassion_message_has_no_future_relapse_prediction(self, client: TestClient) -> None:
        """P4 framing rule applies here too: no predictive language."""
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        text = body["compassion_message"].lower()
        for token in ("will relapse", "likely to", "predicted", "forecast"):
            assert token not in text, f"predictive token {token!r} in relapse message"

    def test_compassion_message_contains_no_better_worse_moral_framing(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        text = body["compassion_message"].lower()
        assert not re.search(r"\bbetter\b", text), "'better' is a moral frame in relapse copy"
        assert not re.search(r"\bworse\b", text), "'worse' is a moral frame in relapse copy"

    def test_next_steps_contains_review_prompt(self, client: TestClient) -> None:
        """The signed clinical template includes 'review_prompt' as a
        next-step — verifies the template hasn't been stripped."""
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert "review_prompt" in body["next_steps"]


# =============================================================================
# TestRelapseValidation
# =============================================================================


class TestRelapseValidation:
    def test_missing_idempotency_key_returns_422(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload())
        assert response.status_code == 422

    def test_severity_below_range_rejected(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(severity=0), headers=_IK_HEADER)
        assert response.status_code == 422

    def test_severity_above_range_rejected(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(severity=6), headers=_IK_HEADER)
        assert response.status_code == 422

    def test_severity_at_minimum_boundary_accepted(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(severity=1), headers=_IK_HEADER)
        assert response.status_code == 201

    def test_severity_at_maximum_boundary_accepted(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(severity=5), headers=_IK_HEADER)
        assert response.status_code == 201

    def test_missing_behavior_rejected(self, client: TestClient) -> None:
        payload = {"occurred_at": "2026-04-19T10:00:00Z", "severity": 3}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 422

    def test_missing_occurred_at_rejected(self, client: TestClient) -> None:
        payload = {"behavior": "alcohol_use", "severity": 3}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 422

    def test_empty_body_rejected(self, client: TestClient) -> None:
        response = client.post(_URL, json={}, headers=_IK_HEADER)
        assert response.status_code == 422

    def test_severity_as_float_string_rejected(self, client: TestClient) -> None:
        """Severity must be an integer, not a float or coercible string."""
        response = client.post(
            _URL,
            json=_valid_payload(severity="high"),
            headers=_IK_HEADER,
        )
        assert response.status_code == 422

    def test_all_severity_values_in_range_accepted(self, client: TestClient) -> None:
        """Boundary sweep: every valid severity value produces 201."""
        for sev in range(1, 6):
            response = client.post(_URL, json=_valid_payload(severity=sev), headers=_IK_HEADER)
            assert response.status_code == 201, f"severity={sev} should be accepted"
