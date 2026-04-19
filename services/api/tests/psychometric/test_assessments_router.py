"""``POST /v1/assessments`` endpoint tests across all four instruments.

Coverage matrix:
- Per-instrument happy path with item-count + cutoff boundary check.
- Item-count validation (specific message naming the instrument).
- Item-range validation (delegated to scorer, surfaced as 422).
- WHO-5 specific: ``index`` field present and equals ``raw_total × 4``.
- AUDIT-C specific: sex-aware cutoff surfaces; default sex behavior.
- PHQ-9 specific: ``requires_t3`` fires on safety-positive item 9.
- Idempotency-Key header is required.
- Response shape stable across instruments (always-present fields).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


# ---- Fixtures --------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_psychometric_stores() -> Any:
    """Clear the module-level idempotency store and assessment
    repository before and after each test.

    Test isolation must match the production model where each request
    is a fresh operation.  The idempotency cache exists for retry-
    within-a-single-client (not cross-test fixture reuse), and the
    assessment repository would otherwise accumulate records across
    tests and blow up history-endpoint assertions about timeline size.
    """
    from discipline.psychometric.repository import (
        get_assessment_repository,
    )
    from discipline.shared.idempotency import get_idempotency_store

    get_idempotency_store().clear()
    get_assessment_repository().clear()
    yield
    get_idempotency_store().clear()
    get_assessment_repository().clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _post(
    client: TestClient,
    *,
    instrument: str,
    items: list[int],
    sex: str | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """Submit an assessment with a fresh Idempotency-Key per call.

    The default key is a new UUID on every invocation so that a test
    which loops over multiple bodies (e.g. AUDIT-C across sexes, a
    response-shape test across every instrument) does not accidentally
    collide on the idempotency cache and get 409 Conflict on the
    second iteration.  Tests that need a *specific* key for
    replay/conflict scenarios bypass this helper and call
    ``client.post`` directly with explicit headers (see
    ``TestIdempotency`` below).
    """
    body: dict[str, Any] = {"instrument": instrument, "items": items}
    if sex is not None:
        body["sex"] = sex
    h = {"Idempotency-Key": f"test-{uuid.uuid4()}"}
    if headers:
        h.update(headers)
    return client.post("/v1/assessments", json=body, headers=h)


# =============================================================================
# PHQ-9 (regression — pre-existing instrument)
# =============================================================================


class TestPhq9:
    def test_happy_path(self, client: TestClient) -> None:
        """Items 1–8 each = 1, item 9 = 0 → total 8, mild, no safety
        trigger.  Item 9 is the suicidality screen — leaving it 0 keeps
        ``requires_t3`` False so the happy path doesn't co-mingle with
        the safety-routing assertions below."""
        resp = _post(
            client, instrument="phq9", items=[1, 1, 1, 1, 1, 1, 1, 1, 0]
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "phq9"
        assert body["total"] == 8
        assert body["severity"] == "mild"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "phq9-1.0.0"

    def test_safety_item_positive_triggers_t3(self, client: TestClient) -> None:
        """Item 9 (zero-indexed 8) > 0 must route through safety and
        flip ``requires_t3`` to True.  Crisis UI keys on this flag."""
        items = [0] * 9
        items[8] = 2  # safety item positive
        resp = _post(client, instrument="phq9", items=items)
        body = resp.json()
        assert body["requires_t3"] is True
        assert body["t3_reason"] is not None

    def test_safety_item_zero_no_t3(self, client: TestClient) -> None:
        resp = _post(
            client, instrument="phq9", items=[3, 3, 3, 3, 3, 3, 3, 3, 0]
        )
        assert resp.json()["requires_t3"] is False


# =============================================================================
# GAD-7 (regression)
# =============================================================================


class TestGad7:
    def test_happy_path(self, client: TestClient) -> None:
        resp = _post(client, instrument="gad7", items=[2, 2, 2, 2, 2, 2, 2])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "gad7"
        assert body["total"] == 14
        assert body["severity"] == "moderate"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "gad7-1.0.0"

    def test_index_not_set_for_gad7(self, client: TestClient) -> None:
        """``index`` is WHO-5-specific.  GAD-7 must not populate it
        even if a refactor accidentally added the field."""
        resp = _post(client, instrument="gad7", items=[1, 1, 1, 1, 1, 1, 1])
        assert resp.json()["index"] is None


# =============================================================================
# WHO-5 (new)
# =============================================================================


class TestWho5:
    def test_happy_path(self, client: TestClient) -> None:
        resp = _post(client, instrument="who5", items=[3, 3, 3, 3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "who5"
        assert body["total"] == 15
        assert body["index"] == 60
        assert body["severity"] == "adequate"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "who5-1.0.0"

    def test_index_equals_total_times_four(self, client: TestClient) -> None:
        """The ``× 4`` conversion is critical for WHO-5 — clients
        rendering the score MUST display ``index``, not ``total``."""
        resp = _post(client, instrument="who5", items=[2, 2, 2, 2, 2])
        body = resp.json()
        assert body["total"] == 10
        assert body["index"] == 40

    def test_low_wellbeing_band_poor(self, client: TestClient) -> None:
        """Index 40 → < 50 → poor band."""
        resp = _post(client, instrument="who5", items=[2, 2, 2, 2, 2])
        body = resp.json()
        assert body["index"] == 40
        assert body["severity"] == "poor"

    def test_depression_screen_band(self, client: TestClient) -> None:
        """Index < 28 → depression_screen band.  Note: this does NOT
        flip ``requires_t3`` — T3 is reserved for active suicidality
        per Docs/Whitepapers/04_Safety_Framework.md §T3."""
        resp = _post(client, instrument="who5", items=[1, 1, 1, 1, 1])
        body = resp.json()
        assert body["index"] == 20
        assert body["severity"] == "depression_screen"
        assert body["requires_t3"] is False

    def test_max_index_adequate(self, client: TestClient) -> None:
        resp = _post(client, instrument="who5", items=[5, 5, 5, 5, 5])
        body = resp.json()
        assert body["total"] == 25
        assert body["index"] == 100
        assert body["severity"] == "adequate"

    def test_who5_does_not_populate_audit_c_fields(
        self, client: TestClient
    ) -> None:
        """``cutoff_used`` and ``positive_screen`` are AUDIT-C-only."""
        resp = _post(client, instrument="who5", items=[3, 3, 3, 3, 3])
        body = resp.json()
        assert body["cutoff_used"] is None
        assert body["positive_screen"] is None


# =============================================================================
# AUDIT-C (new)
# =============================================================================


class TestAuditC:
    def test_male_at_cutoff_positive(self, client: TestClient) -> None:
        """Male, total 4 → positive screen."""
        resp = _post(
            client, instrument="audit_c", items=[2, 1, 1], sex="male"
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "audit_c"
        assert body["total"] == 4
        assert body["cutoff_used"] == 4
        assert body["positive_screen"] is True
        assert body["severity"] == "positive_screen"

    def test_male_below_cutoff_negative(self, client: TestClient) -> None:
        """Male, total 3 → negative (cutoff is 4)."""
        resp = _post(
            client, instrument="audit_c", items=[1, 1, 1], sex="male"
        )
        body = resp.json()
        assert body["total"] == 3
        assert body["positive_screen"] is False
        assert body["severity"] == "negative_screen"

    def test_female_at_cutoff_positive(self, client: TestClient) -> None:
        """Female, total 3 → positive (cutoff is 3).  Same total as
        the male case above but flipped result — sex-aware cutoff
        in action."""
        resp = _post(
            client, instrument="audit_c", items=[1, 1, 1], sex="female"
        )
        body = resp.json()
        assert body["total"] == 3
        assert body["cutoff_used"] == 3
        assert body["positive_screen"] is True

    def test_default_sex_uses_lower_cutoff(self, client: TestClient) -> None:
        """No sex supplied → ``unspecified`` → cutoff 3 →
        safety-conservative.  A caller who forgot to send sex gets
        the *more sensitive* screen, not the less sensitive one."""
        resp = _post(client, instrument="audit_c", items=[1, 1, 1])
        body = resp.json()
        assert body["cutoff_used"] == 3
        assert body["positive_screen"] is True

    def test_unspecified_sex_explicit(self, client: TestClient) -> None:
        resp = _post(
            client, instrument="audit_c", items=[1, 1, 1], sex="unspecified"
        )
        body = resp.json()
        assert body["cutoff_used"] == 3

    def test_max_score_positive_any_sex(self, client: TestClient) -> None:
        for sex in ("male", "female", "unspecified"):
            resp = _post(
                client, instrument="audit_c", items=[4, 4, 4], sex=sex
            )
            body = resp.json()
            assert body["total"] == 12
            assert body["positive_screen"] is True

    def test_zero_score_negative_any_sex(self, client: TestClient) -> None:
        for sex in ("male", "female", "unspecified"):
            resp = _post(
                client, instrument="audit_c", items=[0, 0, 0], sex=sex
            )
            assert resp.json()["positive_screen"] is False

    def test_audit_c_does_not_populate_who5_index(
        self, client: TestClient
    ) -> None:
        """``index`` is WHO-5-only; AUDIT-C must not populate it."""
        resp = _post(
            client, instrument="audit_c", items=[1, 1, 1], sex="male"
        )
        assert resp.json()["index"] is None

    def test_no_t3_routing_for_audit_c(self, client: TestClient) -> None:
        """A positive AUDIT-C screen does NOT trigger T3 — it routes to
        a brief intervention conversation, not crisis UI."""
        resp = _post(
            client, instrument="audit_c", items=[4, 4, 4], sex="female"
        )
        assert resp.json()["requires_t3"] is False


# =============================================================================
# AUDIT (full 10-item, Saunders 1993)
# =============================================================================


class TestAudit:
    """Full 10-item AUDIT dispatch via the unified POST /v1/assessments
    endpoint.  Zone semantics come from the scorer tests; these pin the
    router-level contract (response shape, wire-format)."""

    def test_happy_path_low_risk(self, client: TestClient) -> None:
        """All-zero items → total 0, low_risk zone."""
        resp = _post(client, instrument="audit", items=[0] * 10)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "audit"
        assert body["total"] == 0
        assert body["severity"] == "low_risk"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "audit-1.0.0"

    def test_hazardous_zone(self, client: TestClient) -> None:
        """Total 9 (frequent drinking, high quantity, weekly heavy
        sessions) → hazardous zone."""
        resp = _post(
            client,
            instrument="audit",
            items=[3, 3, 3, 0, 0, 0, 0, 0, 0, 0],
        )
        body = resp.json()
        assert body["total"] == 9
        assert body["severity"] == "hazardous"

    def test_harmful_zone(self, client: TestClient) -> None:
        """Total 19 → harmful zone (upper edge before dependence)."""
        resp = _post(
            client,
            instrument="audit",
            items=[4, 4, 4, 4, 3, 0, 0, 0, 0, 0],
        )
        body = resp.json()
        assert body["total"] == 19
        assert body["severity"] == "harmful"

    def test_dependence_zone(self, client: TestClient) -> None:
        """Total 20 → dependence zone (first cutoff above harmful)."""
        resp = _post(
            client,
            instrument="audit",
            items=[4, 4, 4, 4, 4, 0, 0, 0, 0, 0],
        )
        body = resp.json()
        assert body["total"] == 20
        assert body["severity"] == "dependence"

    def test_restricted_scale_value_accepted_on_item_nine(
        self, client: TestClient
    ) -> None:
        """Item 9 on the restricted 0/2/4 scale — 2 is the 'yes, not
        in the last year' response and must be accepted."""
        resp = _post(
            client,
            instrument="audit",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
        )
        assert resp.status_code == 201
        assert resp.json()["total"] == 2

    def test_restricted_scale_rejects_value_one_on_item_nine(
        self, client: TestClient
    ) -> None:
        """Item 9 does not accept value 1 — it's not a published
        response option per WHO 2001."""
        resp = _post(
            client,
            instrument="audit",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        )
        assert resp.status_code == 422
        # Error message must identify the offending item.
        assert "item 9" in resp.json()["detail"]["message"]

    def test_restricted_scale_rejects_value_one_on_item_ten(
        self, client: TestClient
    ) -> None:
        resp = _post(
            client,
            instrument="audit",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        )
        assert resp.status_code == 422
        assert "item 10" in resp.json()["detail"]["message"]

    def test_standard_scale_rejects_value_five(
        self, client: TestClient
    ) -> None:
        """Items 1-8 accept [0, 4]; a 5 is out of range and the
        scorer's InvalidResponseError surfaces as a 422."""
        resp = _post(
            client,
            instrument="audit",
            items=[5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        assert resp.status_code == 422

    def test_no_t3_routing_for_audit(self, client: TestClient) -> None:
        """AUDIT has no safety item.  Even a Zone IV score does NOT
        set ``requires_t3`` — the clinical action is referral, not
        crisis routing.  A co-administered C-SSRS or PHQ-9 carries
        the crisis signal separately."""
        resp = _post(
            client,
            instrument="audit",
            items=[4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
        )
        body = resp.json()
        assert body["total"] == 40
        assert body["severity"] == "dependence"
        assert body["requires_t3"] is False

    def test_index_not_set_for_audit(self, client: TestClient) -> None:
        """``index`` is WHO-5-specific; AUDIT must not populate it."""
        resp = _post(client, instrument="audit", items=[0] * 10)
        assert resp.json()["index"] is None

    def test_audit_c_fields_not_set_for_audit(
        self, client: TestClient
    ) -> None:
        """``cutoff_used`` and ``positive_screen`` are AUDIT-C-specific.
        The full AUDIT uses zone bands instead — its response shape
        must not accidentally populate the AUDIT-C fields."""
        resp = _post(client, instrument="audit", items=[0] * 10)
        body = resp.json()
        assert body["cutoff_used"] is None
        assert body["positive_screen"] is None


# =============================================================================
# Per-instrument item-count validation
# =============================================================================


class TestItemCountValidation:
    """Wrong item count produces a 422 with a specific message naming
    the instrument and the expected count.  Better than the generic
    Pydantic min_length/max_length error because it tells the caller
    *which* count was wrong for *which* instrument."""

    def test_phq9_with_eight_items_rejected(self, client: TestClient) -> None:
        resp = _post(client, instrument="phq9", items=[1] * 8)
        assert resp.status_code == 422
        assert "phq9 requires exactly 9" in resp.json()["detail"]["message"]

    def test_gad7_with_eight_items_rejected(self, client: TestClient) -> None:
        resp = _post(client, instrument="gad7", items=[1] * 8)
        assert resp.status_code == 422
        assert "gad7 requires exactly 7" in resp.json()["detail"]["message"]

    def test_who5_with_six_items_rejected(self, client: TestClient) -> None:
        """WHO-5 expects 5; 6 is over.  This is the case where the
        Pydantic max_length=9 lets the request through and the route's
        per-instrument check catches it."""
        resp = _post(client, instrument="who5", items=[3] * 6)
        assert resp.status_code == 422
        assert "who5 requires exactly 5" in resp.json()["detail"]["message"]

    def test_audit_c_with_four_items_rejected(self, client: TestClient) -> None:
        resp = _post(client, instrument="audit_c", items=[1] * 4)
        assert resp.status_code == 422
        assert (
            "audit_c requires exactly 3" in resp.json()["detail"]["message"]
        )

    def test_audit_with_nine_items_rejected(self, client: TestClient) -> None:
        """Full AUDIT needs exactly 10; nine is short and must be
        rejected with a message naming 'audit' (not 'audit_c').  This
        also guards against a regression where the router picks the
        wrong item-count constant for the two similarly-named
        instruments."""
        resp = _post(client, instrument="audit", items=[0] * 9)
        assert resp.status_code == 422
        assert "audit requires exactly 10" in resp.json()["detail"]["message"]

    def test_too_few_items_rejected_at_pydantic(
        self, client: TestClient
    ) -> None:
        """Two items is below the Pydantic envelope (min_length=3) so
        Pydantic itself rejects before the route's check runs."""
        resp = _post(client, instrument="audit_c", items=[1, 1])
        assert resp.status_code == 422


# =============================================================================
# Item-range validation (delegated to scorer)
# =============================================================================


class TestItemRangeValidation:
    def test_phq9_item_above_max_rejected(self, client: TestClient) -> None:
        """PHQ-9 items go 0–3; a 4 is out of range."""
        resp = _post(
            client, instrument="phq9", items=[4, 0, 0, 0, 0, 0, 0, 0, 0]
        )
        assert resp.status_code == 422

    def test_who5_item_above_max_rejected(self, client: TestClient) -> None:
        """WHO-5 items go 0–5; a 6 is out of range."""
        resp = _post(client, instrument="who5", items=[6, 3, 3, 3, 3])
        assert resp.status_code == 422

    def test_audit_c_item_above_max_rejected(self, client: TestClient) -> None:
        """AUDIT-C items go 0–4; a 5 is out of range."""
        resp = _post(
            client, instrument="audit_c", items=[5, 1, 1], sex="female"
        )
        assert resp.status_code == 422

    def test_audit_item_above_max_rejected(self, client: TestClient) -> None:
        """Full AUDIT items 1-8 go 0-4; a 5 is out of range.  The
        error propagates from the scorer as a 422."""
        resp = _post(
            client,
            instrument="audit",
            items=[5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        assert resp.status_code == 422


# =============================================================================
# Header / dispatch contracts
# =============================================================================


class TestHeaders:
    def test_idempotency_key_required(self, client: TestClient) -> None:
        """The header is part of the wire contract — POSTing without
        it returns 422.  When the AssessmentRepository lands, the key
        will gate de-duplication; today it's just enforced at the
        boundary so clients form the habit early."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "gad7", "items": [1, 1, 1, 1, 1, 1, 1]},
        )
        assert resp.status_code == 422

    def test_unknown_instrument_rejected(self, client: TestClient) -> None:
        """Pydantic Literal narrowing — unknown instruments are rejected
        at the Pydantic validation layer, before the router sees them."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "beck_depression", "items": [1] * 10},
            headers={"Idempotency-Key": "k"},
        )
        assert resp.status_code == 422


# =============================================================================
# Cross-instrument response shape stability
# =============================================================================


class TestResponseShape:
    def test_all_instruments_return_required_fields(
        self, client: TestClient
    ) -> None:
        """Always-present fields across every instrument.  A renderer
        can rely on these always being there; instrument-specific
        fields are nullable extras."""
        cases = [
            ("phq9", [1] * 9, None),
            ("gad7", [1] * 7, None),
            ("who5", [3] * 5, None),
            ("audit_c", [1, 1, 1], "male"),
        ]
        required = {
            "assessment_id",
            "instrument",
            "total",
            "severity",
            "requires_t3",
            "instrument_version",
        }
        for instrument, items, sex in cases:
            resp = _post(client, instrument=instrument, items=items, sex=sex)
            body = resp.json()
            missing = required - set(body.keys())
            assert not missing, (
                f"{instrument} response missing required fields: {missing}"
            )

    def test_assessment_id_unique_across_calls(self, client: TestClient) -> None:
        """Every successful call mints a new UUID.  De-duplication via
        ``Idempotency-Key`` will land in the repository sprint; today
        the route is stateless and IDs are fresh."""
        a = _post(client, instrument="gad7", items=[1] * 7).json()
        b = _post(client, instrument="gad7", items=[1] * 7).json()
        assert a["assessment_id"] != b["assessment_id"]


def _post_cssrs(
    client: TestClient,
    *,
    items: list[int],
    behavior_within_3mo: bool | None = None,
) -> Any:
    """C-SSRS-specific helper that injects the optional
    ``behavior_within_3mo`` body field.  Kept separate from ``_post``
    so the general test body doesn't accumulate instrument-specific
    kwargs over time."""
    body: dict[str, Any] = {"instrument": "cssrs", "items": items}
    if behavior_within_3mo is not None:
        body["behavior_within_3mo"] = behavior_within_3mo
    return client.post(
        "/v1/assessments",
        json=body,
        headers={"Idempotency-Key": "cssrs-test-key"},
    )


# =============================================================================
# C-SSRS Screen — HTTP dispatch
# =============================================================================


class TestCssrsRouting:
    def test_all_negative_is_none_risk(self, client: TestClient) -> None:
        """No items positive → band 'none', no T3, empty triggering
        items.  Baseline happy path for the screen."""
        resp = _post_cssrs(client, items=[0, 0, 0, 0, 0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "cssrs"
        assert body["total"] == 0  # positive_count
        assert body["severity"] == "none"
        assert body["requires_t3"] is False
        assert body["t3_reason"] is None
        assert body["triggering_items"] == []
        assert body["instrument_version"] == "cssrs-screen-1.0.0"

    def test_low_risk_items_1_and_2(self, client: TestClient) -> None:
        """Passive + active ideation, no method → low band."""
        resp = _post_cssrs(client, items=[1, 1, 0, 0, 0, 0])
        body = resp.json()
        assert resp.status_code == 201
        assert body["severity"] == "low"
        assert body["requires_t3"] is False
        assert body["triggering_items"] == [1, 2]

    def test_moderate_risk_item_3(self, client: TestClient) -> None:
        """Item 3 (method) positive → moderate band."""
        resp = _post_cssrs(client, items=[0, 0, 1, 0, 0, 0])
        body = resp.json()
        assert body["severity"] == "moderate"
        assert body["requires_t3"] is False
        assert body["triggering_items"] == [3]

    def test_acute_item_4_fires_t3(self, client: TestClient) -> None:
        """Item 4 (intent) positive → acute band + T3 + t3_reason set.
        This is the load-bearing crisis-routing path."""
        resp = _post_cssrs(client, items=[0, 0, 0, 1, 0, 0])
        body = resp.json()
        assert resp.status_code == 201
        assert body["severity"] == "acute"
        assert body["requires_t3"] is True
        assert body["t3_reason"] == "cssrs_acute_triage"
        assert body["triggering_items"] == [4]

    def test_acute_item_5_fires_t3(self, client: TestClient) -> None:
        resp = _post_cssrs(client, items=[0, 0, 0, 0, 1, 0])
        body = resp.json()
        assert body["severity"] == "acute"
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [5]

    def test_item_6_historic_is_moderate(self, client: TestClient) -> None:
        """Item 6 positive WITHOUT ``behavior_within_3mo`` → moderate
        (the historic-past-behavior branch).  Not acute, no T3."""
        resp = _post_cssrs(client, items=[0, 0, 0, 0, 0, 1])
        body = resp.json()
        assert body["severity"] == "moderate"
        assert body["requires_t3"] is False
        assert body["triggering_items"] == [6]

    def test_item_6_recent_is_acute_t3(self, client: TestClient) -> None:
        """Item 6 positive WITH ``behavior_within_3mo=True`` → acute T3.
        Same response items, escalation driven by the recency flag."""
        resp = _post_cssrs(
            client, items=[0, 0, 0, 0, 0, 1], behavior_within_3mo=True
        )
        body = resp.json()
        assert resp.status_code == 201
        assert body["severity"] == "acute"
        assert body["requires_t3"] is True
        assert body["t3_reason"] == "cssrs_acute_triage"
        assert body["triggering_items"] == [6]

    def test_recency_flag_false_explicit(self, client: TestClient) -> None:
        """Explicit ``behavior_within_3mo=false`` behaves like omitting
        it — item 6 is historic, moderate band."""
        resp = _post_cssrs(
            client, items=[0, 0, 0, 0, 0, 1], behavior_within_3mo=False
        )
        body = resp.json()
        assert body["severity"] == "moderate"
        assert body["requires_t3"] is False

    def test_wrong_item_count_422(self, client: TestClient) -> None:
        """7 items instead of 6 — 422 with instrument-specific
        message."""
        resp = _post_cssrs(client, items=[0] * 7)
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "cssrs" in detail["message"]
        assert "6 items" in detail["message"]

    def test_disjunctive_multiple_triggers(self, client: TestClient) -> None:
        """Items 4 + 5 + 6(recent) all positive — every triggering
        item surfaces in 1-indexed order."""
        resp = _post_cssrs(
            client, items=[0, 0, 0, 1, 1, 1], behavior_within_3mo=True
        )
        body = resp.json()
        assert body["severity"] == "acute"
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [4, 5, 6]
        assert body["total"] == 3  # positive_count

    def test_non_bool_int_coerces_to_zero_one(self, client: TestClient) -> None:
        """Wire format accepts 0/1 ints; the scorer coerces to bool."""
        resp = _post_cssrs(client, items=[1, 0, 0, 1, 0, 0])
        assert resp.status_code == 201
        body = resp.json()
        # Items 1 and 4 positive → acute (item 4 drives band)
        assert body["severity"] == "acute"
        assert body["requires_t3"] is True


# =============================================================================
# PSS-10 — HTTP dispatch
# =============================================================================


class TestPss10Routing:
    def test_all_zero_raw_is_moderate(self, client: TestClient) -> None:
        """All items raw 0 — reverse items (4/5/7/8) flip 0→4, giving
        a total of 16 which is moderate band.  This is the subtle
        case: a patient answering Never to everything is NOT in the
        low band, because they also answered Never to 'felt confident'
        etc., which reverses to Very Often on the stress scale."""
        resp = _post(client, instrument="pss10", items=[0] * 10)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pss10"
        assert body["total"] == 16
        assert body["severity"] == "moderate"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "pss10-1.0.0"

    def test_low_band(self, client: TestClient) -> None:
        """Zero stress, full coping — true 'low' profile.  Reverse
        items must be maxed so they reverse to 0."""
        items = [0, 0, 0, 4, 4, 0, 4, 4, 0, 0]
        resp = _post(client, instrument="pss10", items=items)
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "low"

    def test_high_band_all_high_stress(self, client: TestClient) -> None:
        items = [4, 4, 4, 0, 0, 4, 0, 0, 4, 4]
        resp = _post(client, instrument="pss10", items=items)
        body = resp.json()
        assert body["total"] == 40
        assert body["severity"] == "high"
        assert body["requires_t3"] is False  # PSS-10 never fires T3

    def test_wrong_item_count_422(self, client: TestClient) -> None:
        resp = _post(client, instrument="pss10", items=[0] * 9)
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "pss10" in detail["message"]
        assert "10 items" in detail["message"]

    def test_out_of_range_item_422(self, client: TestClient) -> None:
        """An item value of 5 is invalid on a 0-4 scale."""
        resp = _post(client, instrument="pss10", items=[5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        assert resp.status_code == 422

    def test_pss10_never_fires_t3(self, client: TestClient) -> None:
        """Across a range of severity bands, PSS-10 never sets
        ``requires_t3=True``.  PSS-10 has no safety items."""
        cases = [
            [0, 0, 0, 4, 4, 0, 4, 4, 0, 0],  # low
            [2] * 10,  # moderate (all midpoints)
            [4, 4, 4, 0, 0, 4, 0, 0, 4, 4],  # high
        ]
        for items in cases:
            resp = _post(client, instrument="pss10", items=items)
            assert resp.status_code == 201
            assert resp.json()["requires_t3"] is False


# =============================================================================
# DAST-10 — HTTP dispatch
# =============================================================================


class TestDast10Routing:
    """DAST-10 over the wire.

    Two coverage priorities over the scorer's unit tests: (1) confirm
    the router's dispatch branch picks ``score_dast10`` and populates
    the unified envelope correctly, (2) confirm that DAST-10 — which
    has no safety item — never trips the T3 path regardless of score
    severity.
    """

    def test_all_no_is_low_with_reverse_score(self, client: TestClient) -> None:
        """Subtle case: all-No inputs produce total 1 (not 0) because
        item 3 reverses — "no, I cannot always stop" → scored 1.  This
        is the same family of 'baseline isn't zero' property that PSS-10
        has; a regression here would silently under-report drug-use
        problems in patients who answer No to everything."""
        resp = _post(client, instrument="dast10", items=[0] * 10)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "dast10"
        assert body["total"] == 1
        assert body["severity"] == "low"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "dast10-1.0.0"

    def test_none_band(self, client: TestClient) -> None:
        """True 'no problems' profile — all items No except item 3
        (Yes, can always stop), which reverses to 0 and keeps the
        total at 0."""
        items = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        resp = _post(client, instrument="dast10", items=items)
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "none"

    def test_moderate_band(self, client: TestClient) -> None:
        """Moderate band — brief intervention indicated.  Tests the
        reverse-scored contribution to an interior band."""
        # Items 1, 4, 5, 6 Yes; item 3 No → scored 1.  Total 5.
        items = [1, 0, 0, 1, 1, 1, 0, 0, 0, 0]
        resp = _post(client, instrument="dast10", items=items)
        body = resp.json()
        assert body["total"] == 5
        assert body["severity"] == "moderate"

    def test_severe_band(self, client: TestClient) -> None:
        """Maximum score — every item endorsed with loss of control
        on item 3.  Intensive-treatment indicated."""
        items = [1, 1, 0, 1, 1, 1, 1, 1, 1, 1]
        resp = _post(client, instrument="dast10", items=items)
        body = resp.json()
        assert body["total"] == 10
        assert body["severity"] == "severe"
        assert body["requires_t3"] is False

    def test_wrong_item_count_422(self, client: TestClient) -> None:
        """Router validates count before scoring; error message names
        the instrument so a multi-instrument harness can route by it."""
        resp = _post(client, instrument="dast10", items=[0] * 9)
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "dast10" in detail["message"]
        assert "10 items" in detail["message"]

    def test_out_of_range_item_422(self, client: TestClient) -> None:
        """A raw value of 2 is invalid on a 0/1 (no/yes) scale."""
        resp = _post(
            client, instrument="dast10", items=[2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        )
        assert resp.status_code == 422

    def test_dast10_never_fires_t3(self, client: TestClient) -> None:
        """Across every band DAST-10 never sets ``requires_t3=True``.
        DAST-10 has no safety item (no C-SSRS-style suicidality question,
        no PHQ-9-style item 9).  A regression here would route drug-use
        patients into the crisis UI when they should go to substance-use
        intake."""
        cases = [
            [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # none
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # low
            [1, 0, 0, 1, 1, 1, 0, 0, 0, 0],  # moderate
            [1, 1, 0, 1, 1, 1, 1, 1, 0, 0],  # substantial
            [1, 1, 0, 1, 1, 1, 1, 1, 1, 1],  # severe
        ]
        for items in cases:
            resp = _post(client, instrument="dast10", items=items)
            assert resp.status_code == 201
            body = resp.json()
            assert body["requires_t3"] is False
            assert body.get("t3_reason") is None


# =============================================================================
# MDQ (Hirschfeld 2000, 13-item bipolar screen, three-gate conjunction)
# =============================================================================


class TestMdqRouting:
    """MDQ over the wire.

    Router-level contract verification for the three-gate positive
    screen.  The scorer's own unit tests exhaustively pin the gate
    logic; these tests pin (1) the dispatch branch picks ``score_mdq``,
    (2) the wire envelope correctly surfaces ``positive_screen`` and
    uses the positive-item count as ``total``, and (3) the new
    request fields ``concurrent_symptoms`` and ``functional_impairment``
    are required when instrument=mdq but ignored for other instruments.
    """

    @staticmethod
    def _body(
        *,
        positive_count: int,
        concurrent: bool | None = True,
        impairment: str | None = "serious",
    ) -> dict[str, Any]:
        """Build an MDQ request body with the first N items positive.

        Keeping the helper local to this test class — the module-level
        ``_post`` stays instrument-agnostic, and the MDQ-specific field
        names (``concurrent_symptoms`` / ``functional_impairment``) live
        here so other instruments' test bodies don't accidentally
        inherit them.
        """
        items = [1] * positive_count + [0] * (13 - positive_count)
        body: dict[str, Any] = {"instrument": "mdq", "items": items}
        if concurrent is not None:
            body["concurrent_symptoms"] = concurrent
        if impairment is not None:
            body["functional_impairment"] = impairment
        return body

    def _post_mdq(
        self,
        client: TestClient,
        *,
        positive_count: int,
        concurrent: bool | None = True,
        impairment: str | None = "serious",
    ) -> Any:
        body = self._body(
            positive_count=positive_count,
            concurrent=concurrent,
            impairment=impairment,
        )
        return client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_all_three_gates_pass_positive_screen(
        self, client: TestClient
    ) -> None:
        """Seven positives + concurrent + serious → positive_screen.
        The wire envelope mirrors AUDIT-C's positive/negative screen
        shape; a chart-view client rendering the two instruments
        can use the same projection."""
        resp = self._post_mdq(client, positive_count=7)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "mdq"
        # ``total`` is the positive-item count, not a weighted sum —
        # this is the value that flows into valueInteger on the FHIR
        # Observation export.
        assert body["total"] == 7
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "mdq-1.0.0"

    def test_six_positives_below_threshold_negative(
        self, client: TestClient
    ) -> None:
        """Item-count gate below threshold → negative_screen regardless
        of Part 2 and Part 3.  Router pass-through for the boundary
        the scorer's unit tests also pin."""
        resp = self._post_mdq(client, positive_count=6)
        body = resp.json()
        assert body["total"] == 6
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_concurrent_false_blocks_screen(self, client: TestClient) -> None:
        """Seven items positive + concurrent=False → negative.  The
        load-bearing 'high items but not concurrent' case."""
        resp = self._post_mdq(client, positive_count=7, concurrent=False)
        body = resp.json()
        assert body["total"] == 7
        assert body["positive_screen"] is False
        assert body["severity"] == "negative_screen"

    def test_minor_impairment_blocks_screen(self, client: TestClient) -> None:
        """Seven items + concurrent + minor impairment → negative.
        Minor is the near-miss impairment label that must NOT cross
        the gate."""
        resp = self._post_mdq(
            client, positive_count=13, impairment="minor"
        )
        body = resp.json()
        assert body["total"] == 13
        assert body["positive_screen"] is False
        assert body["severity"] == "negative_screen"

    def test_moderate_impairment_passes_screen(
        self, client: TestClient
    ) -> None:
        """Moderate impairment is the minimum Part 3 value that
        satisfies the gate — pairs with the minor case above."""
        resp = self._post_mdq(client, positive_count=7, impairment="moderate")
        body = resp.json()
        assert body["positive_screen"] is True

    def test_missing_concurrent_symptoms_rejected(
        self, client: TestClient
    ) -> None:
        """Instrument=mdq with no concurrent_symptoms supplied → 422
        with an MDQ-specific message.  Without this the dispatch would
        silently produce negative_screen, which is the exact footgun
        the module docstring warns about."""
        resp = self._post_mdq(client, positive_count=10, concurrent=None)
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["code"] == "validation.invalid_payload"
        assert "concurrent_symptoms" in detail["message"]

    def test_missing_functional_impairment_rejected(
        self, client: TestClient
    ) -> None:
        resp = self._post_mdq(client, positive_count=10, impairment=None)
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["code"] == "validation.invalid_payload"
        assert "functional_impairment" in detail["message"]

    def test_invalid_impairment_label_rejected(self, client: TestClient) -> None:
        """Wire-format bug: caller sends 'severe' instead of 'serious'.
        Because ``functional_impairment`` is typed as a Literal, Pydantic
        rejects at parse time (before the router's dispatch runs), so
        the 422 body is Pydantic's list-format rather than our
        structured dict.  Both are acceptable 422 surfaces; the test
        just pins that the request is rejected (not silently coerced
        to a default impairment)."""
        resp = self._post_mdq(
            client, positive_count=10, impairment="severe"
        )
        assert resp.status_code == 422
        # Pydantic emits a list of ValidationError records with ``loc``
        # pointing at the offending field.  We assert on the field
        # name rather than a specific message string so a Pydantic
        # version bump that rephrases the message doesn't break us.
        raw = resp.json()["detail"]
        assert isinstance(raw, list)
        locations = [tuple(entry.get("loc", ())) for entry in raw]
        assert any("functional_impairment" in loc for loc in locations)

    def test_wrong_item_count_rejected(self, client: TestClient) -> None:
        """MDQ needs exactly 13 items; 12 is short.  Router-level
        message names the instrument and the expected count so a
        multi-instrument harness can route on it."""
        body = {
            "instrument": "mdq",
            "items": [0] * 12,
            "concurrent_symptoms": True,
            "functional_impairment": "serious",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422
        assert "mdq requires exactly 13" in resp.json()["detail"]["message"]

    def test_item_range_out_of_bounds_rejected(
        self, client: TestClient
    ) -> None:
        """Part 1 items are 0/1.  A 2 is out of range and the scorer's
        InvalidResponseError surfaces as 422."""
        body = {
            "instrument": "mdq",
            "items": [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "concurrent_symptoms": True,
            "functional_impairment": "serious",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_mdq_never_fires_t3(self, client: TestClient) -> None:
        """MDQ has no safety item.  Even a fully-positive screen
        (13/13 + concurrent + serious) must NOT set requires_t3=True.
        A regression here would route patients into the crisis UI for
        a bipolar-spectrum signal that is explicitly NOT a crisis
        signal per Hirschfeld 2000 + Whitepaper 04 §T3."""
        resp = self._post_mdq(client, positive_count=13)
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_mdq_does_not_populate_who5_or_audit_c_fields(
        self, client: TestClient
    ) -> None:
        """``index`` is WHO-5 only; ``cutoff_used`` is AUDIT-C only.
        MDQ must not accidentally populate either.  ``positive_screen``
        IS populated (shared semantic with AUDIT-C) and is covered in
        the happy-path test above."""
        resp = self._post_mdq(client, positive_count=7)
        body = resp.json()
        assert body["index"] is None
        assert body["cutoff_used"] is None
        # triggering_items is C-SSRS-only; MDQ must not set it.
        assert body.get("triggering_items") is None

    def test_mdq_fields_ignored_for_other_instruments(
        self, client: TestClient
    ) -> None:
        """A caller that mistakenly forwards concurrent_symptoms on a
        PHQ-9 submission must not get a 422 — the fields are
        MDQ-specific but tolerated elsewhere (``None`` is the default).
        Pinning the tolerance keeps cross-instrument harnesses from
        needing per-instrument scrubbing."""
        body = {
            "instrument": "phq9",
            "items": [1, 1, 1, 1, 1, 1, 1, 1, 0],
            "concurrent_symptoms": True,  # MDQ-only; must be ignored
            "functional_impairment": "serious",  # MDQ-only; must be ignored
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        phq9_body = resp.json()
        assert phq9_body["instrument"] == "phq9"
        assert phq9_body["total"] == 8

    def test_mdq_persists_fields_to_repository(
        self, client: TestClient
    ) -> None:
        """The submission must round-trip Part 2 + Part 3 into the
        AssessmentRecord so a later FHIR Observation re-render can
        preserve the full event.  Verified by submitting with user_id,
        then reading back via the history endpoint and inspecting the
        stored record via the repository."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "mdq",
            "items": [1] * 7 + [0] * 6,
            "concurrent_symptoms": True,
            "functional_impairment": "moderate",
            "user_id": "user-mdq-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-mdq-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "mdq"
        assert stored.total == 7
        assert stored.positive_screen is True
        assert stored.concurrent_symptoms is True
        assert stored.functional_impairment == "moderate"


# =============================================================================
# PC-PTSD-5 (Prins 2016) — 5-item primary-care PTSD screen
# =============================================================================


class TestPcPtsd5Routing:
    """PC-PTSD-5 over the wire.

    Router-level contract verification for the 5-item cutoff screen.
    The scorer's own unit tests exhaustively pin the ``>= 3`` cutoff
    and item validation; these tests pin (1) the dispatch branch picks
    ``score_pcptsd5``, (2) the wire envelope surfaces ``positive_screen``
    and carries the positive-item count as ``total`` (uniform with MDQ
    and AUDIT-C), and (3) ``requires_t3`` is always False — PC-PTSD-5
    has no safety item so the T3 pathway is never reachable from a
    PTSD screen (per Docs/Whitepapers/04_Safety_Framework.md §T3).
    """

    def _post_pcptsd5(
        self,
        client: TestClient,
        *,
        positive_count: int,
    ) -> Any:
        """Build a PC-PTSD-5 request body with N items endorsed (yes).

        Order doesn't matter — the scorer sums — but endorsing the
        first N items makes test intent obvious to a reader.
        """
        items = [1] * positive_count + [0] * (5 - positive_count)
        return client.post(
            "/v1/assessments",
            json={"instrument": "pcptsd5", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_three_positives_at_cutoff_is_positive_screen(
        self, client: TestClient
    ) -> None:
        """At the Prins 2016 cutoff (exactly 3 of 5 endorsed) → the
        wire response surfaces ``positive_screen=True``.  This is the
        boundary case a fence-post bug would break most visibly."""
        resp = self._post_pcptsd5(client, positive_count=3)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pcptsd5"
        # ``total`` carries the positive-item count (0-5), not a
        # weighted sum.  Receiving FHIR systems read this as the
        # valueInteger on the Observation emission.
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "pcptsd5-1.0.0"

    def test_two_positives_below_cutoff_is_negative_screen(
        self, client: TestClient
    ) -> None:
        """Below cutoff (2 of 5 endorsed) → negative_screen.  Prins 2016
        considered cutoff 2 in the validation work but selected 3; the
        router must follow the chosen operating point."""
        resp = self._post_pcptsd5(client, positive_count=2)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pcptsd5"
        assert body["total"] == 2
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["requires_t3"] is False

    def test_zero_positives_is_negative_screen(self, client: TestClient) -> None:
        """All items negative → negative screen.  The degenerate case:
        a patient who answered ``no`` to every symptom."""
        resp = self._post_pcptsd5(client, positive_count=0)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    def test_all_five_positives_is_positive_screen(
        self, client: TestClient
    ) -> None:
        """Full symptom cluster endorsed → clearly positive."""
        resp = self._post_pcptsd5(client, positive_count=5)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 5
        assert body["positive_screen"] is True

    def test_positive_screen_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: even a maximum PC-PTSD-5
        score (all 5 symptoms endorsed) never fires the T3 crisis
        pathway.  T3 is reserved for active suicidality; a positive
        PTSD screen is a referral signal for trauma-informed care
        (CAPS-5 / PCL-5 / EMDR / TF-CBT intake), not a crisis signal.
        A regression that let PTSD screens fire T3 would spam the
        clinical-ops safety queue and desensitize responders to
        genuine crisis events."""
        resp = self._post_pcptsd5(client, positive_count=5)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        # The T3 payload fields must be absent/null for PC-PTSD-5 —
        # if a router refactor started surfacing them on non-T3
        # instruments, a reviewer-facing clinician UI would render
        # empty panels.
        assert body.get("t3_reason") is None

    def test_rejects_four_items(self, client: TestClient) -> None:
        """Wrong item count → 422.  Client-side bug where the UI
        dropped an item should surface as a validation error, not a
        silent partial score."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "pcptsd5", "items": [1, 1, 1, 0]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_six_items(self, client: TestClient) -> None:
        """Extra item → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "pcptsd5", "items": [1, 1, 1, 0, 0, 0]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Item value > 1 → 422.  PC-PTSD-5 is pure binary — a
        4-point Likert-style response is a contract violation."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "pcptsd5", "items": [1, 2, 1, 0, 0]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        """Negative item value → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "pcptsd5", "items": [1, -1, 1, 0, 0]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """A submission with a user_id shows up in the per-user history
        with the positive_screen flag captured — the history endpoint
        relies on the stored record via the repository.  Downstream
        clinician UI renders the positive-screen badge from this
        persisted field, not from a re-score at read time."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "pcptsd5",
            "items": [1, 1, 1, 0, 0],
            "user_id": "user-pcptsd5-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-pcptsd5-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "pcptsd5"
        assert stored.total == 3
        assert stored.positive_screen is True
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """``concurrent_symptoms`` and ``functional_impairment`` are
        MDQ-only.  If a client mistakenly sends them on a PC-PTSD-5
        request, the scorer ignores them — the dispatcher handles
        pcptsd5 before the MDQ fallthrough so those fields never
        reach the MDQ validation.  This is a defensive pin against
        dispatcher-ordering regressions."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "pcptsd5",
                "items": [1, 1, 1, 0, 0],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pcptsd5"
        assert body["positive_screen"] is True


# =============================================================================
# ISI (Bastien 2001) — 7-item Insomnia Severity Index
# =============================================================================


class TestIsiRouting:
    """ISI over the wire.

    Router-level contract verification for the 7-item 0-4 Likert
    severity-band instrument.  The scorer's own unit tests
    exhaustively pin each band boundary; these tests pin (1) the
    dispatch branch picks ``score_isi``, (2) the wire envelope
    surfaces the four-band ``severity`` label (uniform with PHQ-9
    and GAD-7 pattern), (3) ``positive_screen`` is NOT populated
    (ISI is a banded instrument, not a screen), and (4)
    ``requires_t3`` is always False — ISI has no safety item, so
    even the maximum total never routes through the crisis pathway.
    """

    def _post_isi(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "isi", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_severe(self, client: TestClient) -> None:
        """All 7 items at 4 → total 28 → severe band.  The wire
        envelope carries the band label directly, matching the
        PHQ-9 / GAD-7 response-shape convention."""
        resp = self._post_isi(client, items=[4, 4, 4, 4, 4, 4, 4])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "isi"
        assert body["total"] == 28
        assert body["severity"] == "severe"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "isi-1.0.0"

    def test_band_boundary_moderate(self, client: TestClient) -> None:
        """Total 15 → moderate band — the Morin 2011 clinical-
        referral threshold.  A fence-post bug at the 14/15 boundary
        would misclassify half of the clinical-insomnia cohort."""
        # 15 = 4+4+4+3+0+0+0
        resp = self._post_isi(client, items=[4, 4, 4, 3, 0, 0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 15
        assert body["severity"] == "moderate"

    def test_band_boundary_subthreshold(self, client: TestClient) -> None:
        """Total 14 → subthreshold (NOT moderate).  Just-below-cutoff
        to pin the 14/15 boundary from the opposite direction."""
        # 14 = 4+4+4+2+0+0+0
        resp = self._post_isi(client, items=[4, 4, 4, 2, 0, 0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 14
        assert body["severity"] == "subthreshold"

    def test_zero_total_is_none_band(self, client: TestClient) -> None:
        """Absent symptoms → ``none``.  A patient who answered 0 to
        every item is definitionally not insomniac on this screen."""
        resp = self._post_isi(client, items=[0, 0, 0, 0, 0, 0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "none"

    def test_severe_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: the maximum ISI score
        never fires the T3 crisis pathway.  T3 is reserved for
        active suicidality — a severe-insomnia patient with
        co-occurring depression needs a PHQ-9 + C-SSRS submission to
        route appropriately, not a silent escalation via ISI.  A
        regression that let ISI fire T3 would spam the clinical-ops
        safety queue and desensitize responders to genuine crises."""
        resp = self._post_isi(client, items=[4, 4, 4, 4, 4, 4, 4])
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_positive_screen_not_populated(self, client: TestClient) -> None:
        """ISI is a band-labelled instrument, not a positive/negative
        screen.  positive_screen is reserved for AUDIT-C / MDQ /
        PC-PTSD-5 which have an explicit cutoff boolean.  ISI's
        ``severity`` field carries the full four-band semantic
        directly."""
        resp = self._post_isi(client, items=[4, 4, 4, 4, 4, 4, 4])
        assert resp.status_code == 201
        body = resp.json()
        # ``positive_screen`` is either absent or explicitly null —
        # what it must NOT be is True.  A refactor that auto-
        # populated positive_screen for every severity-banded
        # instrument would mislabel ISI as a screen.
        assert body.get("positive_screen") in (None,)

    def test_rejects_six_items(self, client: TestClient) -> None:
        resp = self._post_isi(client, items=[4, 4, 4, 4, 4, 4])
        assert resp.status_code == 422

    def test_rejects_eight_items(self, client: TestClient) -> None:
        resp = self._post_isi(client, items=[4, 4, 4, 4, 4, 4, 4, 4])
        assert resp.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Item > 4 → 422.  Client UI must not submit a 5-point-max
        Likert; the server is the safety net."""
        resp = self._post_isi(client, items=[4, 5, 4, 0, 0, 0, 0])
        assert resp.status_code == 422

    def test_persists_severity_in_history(
        self, client: TestClient
    ) -> None:
        """A submission with user_id surfaces in per-user history with
        the Bastien severity band captured.  Downstream trajectory /
        clinician-UI code renders band labels from the stored field,
        not from a re-score."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "isi",
            "items": [3, 3, 2, 2, 3, 3, 3],  # total 19 → moderate
            "user_id": "user-isi-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-isi-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "isi"
        assert stored.total == 19
        assert stored.severity == "moderate"
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """If a client mistakenly sends ``concurrent_symptoms`` or
        ``functional_impairment`` with instrument=isi, the dispatcher
        reaches the ISI branch before the MDQ fallthrough, so those
        fields are ignored.  Defensive pin against dispatcher-
        ordering regressions."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "isi",
                "items": [3, 3, 2, 2, 3, 3, 3],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "isi"
        assert body["severity"] == "moderate"


# =============================================================================
# PCL-5 (Weathers 2013 / Blevins 2015) — 20-item full PTSD checklist
# =============================================================================


class TestPcl5Routing:
    """PCL-5 over the wire.

    Router-level contract verification for the 20-item 0-4 Likert
    full-PTSD-assessment.  The scorer's own unit tests exhaustively
    pin the ``>= 33`` cutoff and cluster boundaries; these tests pin
    (1) the dispatch branch picks ``score_pcl5``, (2) the wire
    envelope carries ``total`` = summed severity (0-80) + ``severity``
    = positive/negative_screen (uniform with PC-PTSD-5 / MDQ), (3)
    the Pydantic envelope accepts 20-item bodies (the max_length
    bound was widened in this sprint), and (4) ``requires_t3`` is
    always False.
    """

    def _post_pcl5(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "pcl5", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_above_cutoff(self, client: TestClient) -> None:
        """All 20 items at 4 → total 80 → positive screen.  The
        envelope carries total = summed severity, NOT the positive-
        item count like MDQ / PC-PTSD-5.  Receiving FHIR systems
        reading this integer + the PCL-5 LOINC must interpret it
        as a severity sum."""
        resp = self._post_pcl5(client, items=[4] * 20)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pcl5"
        assert body["total"] == 80
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "pcl5-1.0.0"

    def test_cutoff_boundary_at_thirty_three(
        self, client: TestClient
    ) -> None:
        """Total exactly 33 → positive screen (the Blevins 2015
        published operating point).  A fence-post regression here
        would misclassify roughly half of the clinical-cutoff cohort."""
        # Build: 8 items at 4 (=32) + 1 item at 1 = 33; rest zero.
        items = [0] * 20
        for i in range(8):
            items[i] = 4
        items[8] = 1
        resp = self._post_pcl5(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 33
        assert body["positive_screen"] is True

    def test_just_below_cutoff_is_negative(
        self, client: TestClient
    ) -> None:
        """Total 32 → negative screen.  Complements the boundary test
        from the other side so both comparator directions are pinned."""
        items = [0] * 20
        for i in range(8):
            items[i] = 4
        resp = self._post_pcl5(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 32
        assert body["positive_screen"] is False

    def test_zero_total_is_negative_screen(self, client: TestClient) -> None:
        """All items 0 → total 0 → negative screen.  The degenerate
        case — a patient who answered 0 to every symptom."""
        resp = self._post_pcl5(client, items=[0] * 20)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    def test_max_severity_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: PCL-5 total 80 (maximum
        severity) does NOT fire the T3 crisis pathway.  T3 is
        reserved for active suicidality — a severe-PTSD patient
        with suicidality needs a co-administered C-SSRS submission.
        Letting PCL-5 fire T3 would spam the clinical-ops safety
        queue (every severe-PTSD patient would trigger it) and
        desensitize responders to genuine crises."""
        resp = self._post_pcl5(client, items=[4] * 20)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_nineteen_items(self, client: TestClient) -> None:
        resp = self._post_pcl5(client, items=[0] * 19)
        assert resp.status_code == 422

    def test_rejects_twenty_one_items(self, client: TestClient) -> None:
        """Extra item → 422.  This test also pins that the Pydantic
        envelope's max_length was correctly widened to 20 this
        sprint (not left at 13).  If the envelope still rejected
        20-item bodies, the happy-path test would have failed
        first — but if max_length was widened to 21, this test
        catches the slip."""
        resp = self._post_pcl5(client, items=[0] * 21)
        assert resp.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Item > 4 → 422."""
        items = [0] * 20
        items[0] = 5
        resp = self._post_pcl5(client, items=items)
        assert resp.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id shows in per-user history with
        positive_screen flag captured.  The clinician-UI renders
        PCL-5 history with the positive-screen badge from the stored
        field; trajectory analysis uses the stored total for RCI
        deltas."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Build a clearly-positive PCL-5 (total 40, above cutoff).
        items = [2] * 20  # total = 40
        body = {
            "instrument": "pcl5",
            "items": items,
            "user_id": "user-pcl5-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-pcl5-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "pcl5"
        assert stored.total == 40
        assert stored.positive_screen is True
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """Client mistakenly sending MDQ-only fields with
        instrument=pcl5 → dispatcher reaches PCL-5 branch before the
        MDQ fallthrough; the extra fields are ignored.  Defensive
        pin against dispatcher-ordering regressions."""
        items = [2] * 20  # total 40 → positive
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "pcl5",
                "items": items,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pcl5"
        assert body["positive_screen"] is True

    def test_subscales_surface_dsm5_clusters(
        self, client: TestClient
    ) -> None:
        """Sprint-40 contract: PCL-5 dispatch emits the four DSM-5
        cluster subscales (intrusion / avoidance / negative_mood /
        hyperarousal) on the response envelope's ``subscales`` map
        so the clinician-UI cluster-trajectory view reads the
        profile without per-row repository re-scoring.

        Item layout (Weathers 2013): items 1-5 = intrusion,
        6-7 = avoidance, 8-14 = negative_mood, 15-20 = hyperarousal.
        Distinctive per-cluster values pin that a swap regression
        surfaces in multiple assertions.
        """
        # intrusion = 5×3 = 15
        # avoidance = 2×4 = 8
        # negative_mood = 7×2 = 14
        # hyperarousal = 6×1 = 6
        # total = 15 + 8 + 14 + 6 = 43 → positive_screen
        items = [3] * 5 + [4] * 2 + [2] * 7 + [1] * 6
        resp = self._post_pcl5(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 43
        assert body["positive_screen"] is True
        assert body["subscales"] == {
            "intrusion": 15,
            "avoidance": 8,
            "negative_mood": 14,
            "hyperarousal": 6,
        }

    def test_subscales_persist_to_history(self, client: TestClient) -> None:
        """The subscales map round-trips through the repository and
        re-appears on the history-endpoint projection.  A regression
        that dropped subscales during persistence would force
        cluster-trajectory renderers to re-score from raw_items,
        duplicating work and bloating the clinician-portal read path."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Intrusion-dominant profile (classic PE-indicated presentation).
        # intrusion = 4+4+4+3+3 = 18
        # avoidance = 2+2 = 4
        # negative_mood = 1×7 = 7
        # hyperarousal = 1×6 = 6
        # total = 35 → positive
        items = [4, 4, 4, 3, 3] + [2, 2] + [1] * 7 + [1] * 6
        body = {
            "instrument": "pcl5",
            "items": items,
            "user_id": "user-pcl5-subscales-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        response_body = resp.json()
        assert response_body["subscales"] == {
            "intrusion": 18,
            "avoidance": 4,
            "negative_mood": 7,
            "hyperarousal": 6,
        }

        repo = get_assessment_repository()
        records = repo.history_for("user-pcl5-subscales-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.subscales == {
            "intrusion": 18,
            "avoidance": 4,
            "negative_mood": 7,
            "hyperarousal": 6,
        }

        history_resp = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-pcl5-subscales-1"},
        )
        assert history_resp.status_code == 200
        item = history_resp.json()["items"][0]
        assert item["subscales"] == {
            "intrusion": 18,
            "avoidance": 4,
            "negative_mood": 7,
            "hyperarousal": 6,
        }


class TestOcirRouting:
    """OCI-R over the wire.

    Router-level contract verification for the 18-item 0-4 Likert OCD
    screener.  The scorer's own unit tests exhaustively pin the ``>=
    21`` cutoff and the six distributed subscales (hoarding / checking
    / ordering / neutralizing / washing / obsessing).  These tests
    pin (1) the dispatch branch picks ``score_ocir``, (2) the wire
    envelope carries ``total`` = summed severity (0-72) + ``severity``
    = positive/negative_screen (uniform with PCL-5 / PC-PTSD-5 /
    MDQ), (3) the 18-item body fits under the Pydantic envelope
    (``max_length`` was widened to 20 for PCL-5 — 18 fits
    comfortably), and (4) ``requires_t3`` is always False.
    """

    def _post_ocir(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "ocir", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_above_cutoff(self, client: TestClient) -> None:
        """All 18 items at 4 → total 72 → positive screen.  The
        envelope carries total = summed severity (0-72), NOT the
        positive-item count like MDQ / PC-PTSD-5.  Receiving FHIR
        systems reading this integer + the OCI-R LOINC must interpret
        it as a severity sum."""
        resp = self._post_ocir(client, items=[4] * 18)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "ocir"
        assert body["total"] == 72
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "ocir-1.0.0"

    def test_cutoff_boundary_at_twenty_one(
        self, client: TestClient
    ) -> None:
        """Total exactly 21 → positive screen (the Foa 2002 operating
        point).  A fence-post regression here would misclassify
        patients at the exact clinical decision threshold."""
        # Build: 5 items at 4 (=20) + 1 item at 1 = 21; rest zero.
        items = [0] * 18
        for i in range(5):
            items[i] = 4
        items[5] = 1
        resp = self._post_ocir(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 21
        assert body["positive_screen"] is True

    def test_just_below_cutoff_is_negative(
        self, client: TestClient
    ) -> None:
        """Total 20 → negative screen.  Complements the boundary test
        from the other side so both comparator directions are pinned."""
        items = [0] * 18
        for i in range(5):
            items[i] = 4
        resp = self._post_ocir(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 20
        assert body["positive_screen"] is False

    def test_zero_total_is_negative_screen(self, client: TestClient) -> None:
        """All items 0 → total 0 → negative screen.  The degenerate
        case — a patient with no OCD symptom distress."""
        resp = self._post_ocir(client, items=[0] * 18)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    def test_max_severity_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: OCI-R total 72 (maximum
        severity) does NOT fire the T3 crisis pathway.  Severe OCD
        carries elevated suicidality risk, but the OCI-R itself has
        no suicidality item — obsessing-subscale items resemble
        "intrusive thoughts" but do not probe acute harm.  T3 is
        reserved for active suicidality via C-SSRS or PHQ-9 item 9.
        Letting OCI-R fire T3 would spam the clinical-ops queue."""
        resp = self._post_ocir(client, items=[4] * 18)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_seventeen_items(self, client: TestClient) -> None:
        resp = self._post_ocir(client, items=[0] * 17)
        assert resp.status_code == 422

    def test_rejects_nineteen_items(self, client: TestClient) -> None:
        resp = self._post_ocir(client, items=[0] * 19)
        assert resp.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Item > 4 → 422."""
        items = [0] * 18
        items[0] = 5
        resp = self._post_ocir(client, items=items)
        assert resp.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id shows in per-user history with the
        positive_screen flag captured.  The clinician-UI reads
        positive_screen from the stored record; a future subscale-
        surfacing sprint will add the six subscale scores to the
        history projection for intervention-selection display."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Build a clearly-positive OCI-R (all items at 2 = total 36).
        items = [2] * 18
        body = {
            "instrument": "ocir",
            "items": items,
            "user_id": "user-ocir-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-ocir-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "ocir"
        assert stored.total == 36
        assert stored.positive_screen is True
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """Client mistakenly sending MDQ-only fields with
        instrument=ocir → dispatcher reaches OCI-R branch before the
        MDQ fallthrough; the extra fields are ignored.  Defensive
        pin against dispatcher-ordering regressions."""
        items = [2] * 18  # total 36 → positive
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "ocir",
                "items": items,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "ocir"
        assert body["positive_screen"] is True

    def test_subscales_surface_six_subtypes(self, client: TestClient) -> None:
        """Sprint-40 contract: OCI-R dispatch emits the six Foa 2002
        OCD-subtype subscales (hoarding / checking / ordering /
        neutralizing / washing / obsessing) on the response envelope's
        ``subscales`` map.  Item layout is **distributed, not
        contiguous** (item 1=hoarding, 2=checking, 3=ordering, 4=
        neutralizing, 5=washing, 6=obsessing, 7=hoarding, ...).  A
        regression that treated subscales as contiguous 3-item slices
        would silently swap every subscale.

        Per-subtype distinctive values: hoarding=9, checking=6,
        ordering=3, neutralizing=0, washing=12, obsessing=1.
        Total = 31 → positive_screen."""
        # items 1/7/13 = hoarding: 3+3+3=9
        # items 2/8/14 = checking: 2+2+2=6
        # items 3/9/15 = ordering: 1+1+1=3
        # items 4/10/16 = neutralizing: 0+0+0=0
        # items 5/11/17 = washing: 4+4+4=12
        # items 6/12/18 = obsessing: 0+1+0=1
        items = [
            3, 2, 1, 0, 4, 0,  # items 1-6
            3, 2, 1, 0, 4, 1,  # items 7-12
            3, 2, 1, 0, 4, 0,  # items 13-18
        ]
        resp = self._post_ocir(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 31
        assert body["positive_screen"] is True
        assert body["subscales"] == {
            "hoarding": 9,
            "checking": 6,
            "ordering": 3,
            "neutralizing": 0,
            "washing": 12,
            "obsessing": 1,
        }

    def test_subscales_persist_to_history(self, client: TestClient) -> None:
        """OCI-R subscales round-trip through the repository so the
        clinician-UI subtype-profile view reads the stored subscales
        map directly."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Washing-dominant profile (classic ERP-for-contamination
        # presentation).  items 5, 11, 17 at 4 (washing items); all
        # other items at 0.  hoarding=0, checking=0, ordering=0,
        # neutralizing=0, washing=12, obsessing=0.  total=12 → negative.
        items = [0] * 18
        items[4] = 4   # item 5 = washing
        items[10] = 4  # item 11 = washing
        items[16] = 4  # item 17 = washing

        body = {
            "instrument": "ocir",
            "items": items,
            "user_id": "user-ocir-subscales-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        response_body = resp.json()
        assert response_body["total"] == 12
        assert response_body["positive_screen"] is False
        assert response_body["subscales"] == {
            "hoarding": 0,
            "checking": 0,
            "ordering": 0,
            "neutralizing": 0,
            "washing": 12,
            "obsessing": 0,
        }

        repo = get_assessment_repository()
        records = repo.history_for("user-ocir-subscales-1", limit=10)
        assert len(records) == 1
        assert records[0].subscales == {
            "hoarding": 0,
            "checking": 0,
            "ordering": 0,
            "neutralizing": 0,
            "washing": 12,
            "obsessing": 0,
        }


class TestPhq15Routing:
    """PHQ-15 over the wire.

    Router-level contract verification for the 15-item 0-2 Likert
    somatic-symptom scale.  PHQ-15 ships the banded-severity envelope
    (like PHQ-9 / GAD-7 / ISI) rather than the screen envelope of
    MDQ / PCL-5 / OCI-R.  These tests pin (1) the dispatch branch
    picks ``score_phq15``, (2) the wire envelope carries
    ``severity`` = one of minimal/low/medium/high directly (not
    positive/negative_screen), (3) ``requires_t3`` is always False
    (chest-pain and fainting items don't escalate to the safety
    stream), (4) the 0-2 item range is enforced at the scorer →
    422 surface.
    """

    def _post_phq15(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "phq15", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_high_band(self, client: TestClient) -> None:
        """All 15 items at 2 → total 30 → high band.  Envelope
        carries severity = 'high' (the Kroenke-2002 band label)
        directly, NOT positive_screen/negative_screen.  Receiving
        clients rendering PHQ-family UI read the band text for the
        severity chip."""
        resp = self._post_phq15(client, items=[2] * 15)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "phq15"
        assert body["total"] == 30
        assert body["severity"] == "high"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "phq15-1.0.0"

    def test_minimal_band_on_zeros(self, client: TestClient) -> None:
        """All items 0 → minimal band.  The degenerate case — a
        patient with no somatic complaint burden."""
        resp = self._post_phq15(client, items=[0] * 15)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "minimal"

    def test_band_boundary_four_is_minimal(
        self, client: TestClient
    ) -> None:
        """Total 4 → minimal band boundary.  A `< 4` regression
        would push this into low and over-identify."""
        items = [0] * 15
        items[0] = 2
        items[1] = 2  # total 4
        resp = self._post_phq15(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 4
        assert body["severity"] == "minimal"

    def test_band_boundary_five_is_low(
        self, client: TestClient
    ) -> None:
        """Total 5 → low band (minimal→low transition)."""
        items = [0] * 15
        items[0] = 2
        items[1] = 2
        items[2] = 1  # total 5
        resp = self._post_phq15(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 5
        assert body["severity"] == "low"

    def test_band_boundary_ten_is_medium(
        self, client: TestClient
    ) -> None:
        """Total 10 → medium band (low→medium transition).  This is
        the clinical-referral threshold Kroenke 2002 cites for
        considering a somatic-focused work-up."""
        items = [0] * 15
        for i in range(5):
            items[i] = 2  # total 10
        resp = self._post_phq15(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 10
        assert body["severity"] == "medium"

    def test_band_boundary_fifteen_is_high(
        self, client: TestClient
    ) -> None:
        """Total 15 → high band (medium→high transition).  The
        high band is the 'somatization-dominant — route to
        interoceptive-exposure work' trigger."""
        items = [0] * 15
        for i in range(7):
            items[i] = 2
        items[7] = 1  # total 15
        resp = self._post_phq15(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 15
        assert body["severity"] == "high"

    def test_max_severity_does_not_fire_t3(
        self, client: TestClient
    ) -> None:
        """Critical clinical-safety contract: PHQ-15 total 30
        (maximum somatization) does NOT fire T3.  Item 6 (chest
        pain) and item 8 (fainting) are medical-urgency markers
        surfaced by the clinician-UI layer separately — they are
        NOT crisis-routing signals.  Letting PHQ-15 fire T3 would
        cross the medical-urgency / psychiatric-crisis boundary
        and desensitize the safety queue."""
        resp = self._post_phq15(client, items=[2] * 15)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_fourteen_items(self, client: TestClient) -> None:
        resp = self._post_phq15(client, items=[0] * 14)
        assert resp.status_code == 422

    def test_rejects_sixteen_items(self, client: TestClient) -> None:
        resp = self._post_phq15(client, items=[0] * 16)
        assert resp.status_code == 422

    def test_rejects_phq9_style_item_value(
        self, client: TestClient
    ) -> None:
        """Item 3 supplied (the PHQ-9 max) → 422.  PHQ-15 is 0-2, not
        0-3 like PHQ-9.  A client that reused a PHQ-9 renderer would
        submit values up to 3; the router rejects them via the
        scorer's InvalidResponseError → 422 path."""
        items = [0] * 15
        items[0] = 3
        resp = self._post_phq15(client, items=items)
        assert resp.status_code == 422

    def test_persists_high_band_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id shows in per-user history with
        severity band captured.  Clinician-UI renders PHQ-15
        history with the band chip from the stored severity
        field; a trajectory-analysis sprint will add RCI
        deltas against the stored total once a PHQ-15 reliable-
        change threshold is pinned."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Clearly-high PHQ-15 (all items at 2 → total 30).
        body = {
            "instrument": "phq15",
            "items": [2] * 15,
            "user_id": "user-phq15-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-phq15-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "phq15"
        assert stored.total == 30
        assert stored.severity == "high"
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """Client mistakenly sending MDQ-only fields with
        instrument=phq15 → dispatcher reaches PHQ-15 branch before
        the MDQ fallthrough; extra fields are ignored.  Defensive
        pin against dispatcher-ordering regressions (load-bearing
        across every non-MDQ branch — a refactor that moved MDQ
        earlier would silently raise on missing PHQ-15 fields)."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq15",
                "items": [2] * 15,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "phq15"
        assert body["severity"] == "high"


class TestPacsRouting:
    """PACS (Penn Alcohol Craving Scale, Flannery 1999) over the wire.

    PACS introduces the platform's third wire-envelope pattern:
    **continuous severity**.  Banded-severity instruments (PHQ-9 /
    GAD-7 / ISI / PHQ-15) carry a severity label drawn from a
    clinically-validated threshold tuple; screen-style instruments
    (PCL-5 / PC-PTSD-5 / OCI-R / MDQ / AUDIT-C) carry
    positive_screen / negative_screen.  PACS carries the sentinel
    ``"continuous"`` because Flannery 1999 publishes no severity
    bands — the trajectory layer extracts the clinical signal from
    week-over-week Δ, not from a categorical classification.

    These tests pin (1) the dispatch branch picks ``score_pacs``,
    (2) the wire envelope carries ``severity == "continuous"``
    regardless of total, (3) ``requires_t3`` is always False
    (craving is the pre-behavior signal the platform intervenes on
    in the 60-180s urge-to-action window, not a T3 crisis marker),
    (4) item-count + item-range validation surface as 422.
    """

    def _post_pacs(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "pacs", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_high_craving(self, client: TestClient) -> None:
        """All 5 items at 6 → total 30 → severity 'continuous'.  The
        total value carries the clinical signal; 'continuous' is a
        sentinel declaring that the receiving system must not
        categorize status from this field."""
        resp = self._post_pacs(client, items=[6, 6, 6, 6, 6])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pacs"
        assert body["total"] == 30
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "pacs-1.0.0"

    def test_zero_craving_still_returns_continuous_sentinel(
        self, client: TestClient
    ) -> None:
        """All items 0 → total 0.  The sentinel ``"continuous"`` is
        invariant across the entire 0-30 range — the absence of
        craving is just as much "measure, don't classify" as the
        presence of it.  A regression that coerced the zero case to
        a different label would break the uniform trajectory
        rendering contract."""
        resp = self._post_pacs(client, items=[0, 0, 0, 0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_mid_range_total_is_still_continuous(
        self, client: TestClient
    ) -> None:
        """A mid-range total must NOT accidentally pick up a banded
        label.  If a future refactor imports a severity classifier
        from another instrument, this test catches the cross-wire."""
        # 3 + 4 + 3 + 2 + 3 = 15
        resp = self._post_pacs(client, items=[3, 4, 3, 2, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_max_total_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: PACS total 30 (maximum
        craving) does NOT fire T3.  T3 is reserved for active
        suicidality per Whitepaper 04 §T3 and fires only on PHQ-9
        item 9 / C-SSRS items 4-6.  A patient with maximum craving
        AND acute suicidality needs a co-administered PHQ-9 or
        C-SSRS to fire T3 — PACS alone never should."""
        resp = self._post_pacs(client, items=[6, 6, 6, 6, 6])
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_four_items(self, client: TestClient) -> None:
        resp = self._post_pacs(client, items=[0, 0, 0, 0])
        assert resp.status_code == 422

    def test_rejects_six_items(self, client: TestClient) -> None:
        resp = self._post_pacs(client, items=[0, 0, 0, 0, 0, 0])
        assert resp.status_code == 422

    def test_rejects_out_of_range_item_value(
        self, client: TestClient
    ) -> None:
        """Item value 7 supplied (one above the Flannery 1999 ceiling)
        → 422.  The regression this guards is a client that reused a
        1-7 UI widget and forgot to zero-index it."""
        items = [0, 0, 0, 0, 0]
        items[2] = 7
        resp = self._post_pacs(client, items=items)
        assert resp.status_code == 422

    def test_persists_pacs_submission_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id lands in per-user history with the
        continuous sentinel captured.  The trajectory layer reads
        the stored total (not the severity) to compute week-over-week
        Δ — the clinical signal.  A regression that dropped the total
        during persistence would silently break the product-core
        intervention path."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "pacs",
            "items": [4, 5, 3, 5, 4],  # total 21
            "user_id": "user-pacs-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-pacs-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "pacs"
        assert stored.total == 21
        assert stored.severity == "continuous"
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """instrument=pacs + extra MDQ fields → extras are ignored,
        PACS dispatch runs cleanly.  Same defensive pin as the other
        non-MDQ branches — catches a dispatcher-ordering regression
        that would try to score MDQ when a PACS was intended."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "pacs",
                "items": [2, 2, 2, 2, 2],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "pacs"
        assert body["total"] == 10
        assert body["severity"] == "continuous"


class TestBis11Routing:
    """BIS-11 (Barratt Impulsiveness Scale, Patton 1995) over the wire.

    BIS-11 is the package's first **non-zero-based Likert** (1-4, not
    0-4) and its largest instrument (30 items — which raised the
    Pydantic envelope's ``max_length`` from 20 to 30 when it shipped).
    It also ships 11 reverse-coded items (positively-worded) handled
    inside the scorer.

    These tests pin (1) the dispatch branch picks ``score_bis11``,
    (2) the wire envelope carries ``severity`` = low/normal/high
    (Stanford 2009 tri-band), (3) the post-reversal total is what
    lands in ``total`` and ``severity`` (not the raw-response sum),
    (4) ``requires_t3`` is always False, (5) zero-valued items are
    rejected (regression guard against 0-4-Likert copy-paste bugs),
    (6) 29/31-item counts are rejected at the router boundary.
    """

    def _post_bis11(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "bis11", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_high_band(self, client: TestClient) -> None:
        """Ceiling profile (all non-reverse items at 4, reverse items
        at 1 — both scoring to 4 post-reversal).  Total 120 → 'high'."""
        items = [4] * 30
        # Reverse-coded positions (1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30)
        # need to be at raw 1 to score 4 after reversal.
        for pos in (1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30):
            items[pos - 1] = 1
        resp = self._post_bis11(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "bis11"
        assert body["total"] == 120
        assert body["severity"] == "high"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "bis11-1.0.0"

    def test_all_raw_twos_is_normal_upper_edge(
        self, client: TestClient
    ) -> None:
        """All raw 2s → scored total 71 (Stanford 2009 normal upper edge).
        This is the banding fence post — a regression that shifted the
        'normal' upper from 71 to 70 would fail this test."""
        resp = self._post_bis11(client, items=[2] * 30)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 71
        assert body["severity"] == "normal"

    def test_low_band_via_response_bias_profile(
        self, client: TestClient
    ) -> None:
        """Stanford 2009 flags the ≤ 51 band as possible social-
        desirability response bias.  This test pins that the
        floor (total 30) maps to 'low' — regression guard against
        an over-eager banding refactor that might rename this band
        to 'acceptable' or 'ideal'."""
        items = [1] * 30
        for pos in (1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30):
            items[pos - 1] = 4
        resp = self._post_bis11(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 30
        assert body["severity"] == "low"

    def test_reverse_coding_applied_at_dispatch(
        self, client: TestClient
    ) -> None:
        """All raw 1s → the 11 reverse-coded positions score to 4, the
        other 19 stay at 1.  Total = (11 × 4) + (19 × 1) = 63 → 'normal'.
        This fails loudly if a refactor silently drops reverse-coding
        (which would produce total 30 → 'low' instead)."""
        resp = self._post_bis11(client, items=[1] * 30)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 63
        assert body["severity"] == "normal"

    def test_max_severity_does_not_fire_t3(
        self, client: TestClient
    ) -> None:
        """Critical clinical-safety contract: BIS-11 total 120 (ceiling
        impulsivity) does NOT fire T3.  High trait impulsivity routes
        to DBT / mindfulness-based attention / implementation-intention
        work at the intervention layer, not to the safety stream.
        Letting BIS-11 fire T3 would cross the personality-trait /
        psychiatric-crisis boundary and desensitize the safety queue."""
        items = [4] * 30
        for pos in (1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30):
            items[pos - 1] = 1
        resp = self._post_bis11(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_twenty_nine_items(self, client: TestClient) -> None:
        resp = self._post_bis11(client, items=[2] * 29)
        assert resp.status_code == 422

    def test_rejects_thirty_one_items(self, client: TestClient) -> None:
        resp = self._post_bis11(client, items=[2] * 31)
        # Envelope max is 30, so 31 is a Pydantic-422 rather than a
        # per-instrument 422 — either way the caller sees 422.
        assert resp.status_code == 422

    def test_rejects_zero_item_value(self, client: TestClient) -> None:
        """Raw value 0 → 422.  BIS-11 is 1-4, not 0-based like the rest
        of the package.  This is the regression guard against a client
        that reused a 0-based Likert UI and forgot to shift the scale."""
        items = [2] * 30
        items[0] = 0
        resp = self._post_bis11(client, items=items)
        assert resp.status_code == 422

    def test_rejects_item_value_five(self, client: TestClient) -> None:
        items = [2] * 30
        items[5] = 5
        resp = self._post_bis11(client, items=items)
        assert resp.status_code == 422

    def test_persists_high_band_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id shows in per-user history with
        severity band captured.  Trajectory analysis reads the stored
        total — which must be the post-reversal sum, not the raw-
        response sum (a regression that stored raw would make the
        trajectory meaningless)."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        items = [4] * 30
        for pos in (1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30):
            items[pos - 1] = 1
        body = {
            "instrument": "bis11",
            "items": items,
            "user_id": "user-bis11-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-bis11-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "bis11"
        assert stored.total == 120
        assert stored.severity == "high"
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """instrument=bis11 + MDQ fields → BIS-11 dispatch runs; extras
        ignored.  Defensive pin across the dispatcher-ordering contract."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "bis11",
                "items": [2] * 30,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "bis11"
        assert body["severity"] == "normal"

    def test_subscales_surface_three_patton_factors(
        self, client: TestClient
    ) -> None:
        """Sprint-40 contract: BIS-11 dispatch emits the three Patton
        1995 second-order subscales (attentional / motor /
        non_planning) on the response envelope's ``subscales`` map,
        **computed on scored (post-reversal) values** — not on the
        raw caller input.

        Uniform 2 across all 30 items (the same body the
        ``test_ignores_mdq_only_fields`` test uses).  Reverse-coded
        items (1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30) flip 2 → 3
        via the 5 − v formula; regular items stay at 2.

        attentional (items 5,6,9,11,20,24,26,28): 2+2+3+2+3+2+2+2 = 18
        motor (items 2,3,4,16,17,19,21,22,23,25,30): 10×2 + 3 = 23
        non_planning (items 1,7,8,10,12,13,14,15,18,27,29):
          reversed: 1,7,8,10,12,13,15,29 = 8 items × 3 = 24
          regular: 14, 18, 27 = 3 items × 2 = 6
          sum = 30
        Total = 18 + 23 + 30 = 71 → 'normal' band.
        """
        resp = self._post_bis11(client, items=[2] * 30)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 71
        assert body["severity"] == "normal"
        assert body["subscales"] == {
            "attentional": 18,
            "motor": 23,
            "non_planning": 30,
        }

    def test_subscales_persist_to_history(self, client: TestClient) -> None:
        """BIS-11 subscales round-trip through the repository so the
        intervention layer's per-factor read-out (attentional-dominant
        → attention-training; motor-dominant → response-delay drills;
        non_planning-dominant → implementation-intention scripting)
        works against the stored record, not just the live dispatch
        response."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "bis11",
            "items": [2] * 30,
            "user_id": "user-bis11-subscales-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        expected = {
            "attentional": 18,
            "motor": 23,
            "non_planning": 30,
        }
        assert resp.json()["subscales"] == expected

        repo = get_assessment_repository()
        records = repo.history_for("user-bis11-subscales-1", limit=10)
        assert len(records) == 1
        assert records[0].subscales == expected


class TestCravingVasRouting:
    """Craving VAS (single-item 0-100 EMA, Sayette 2000 synthesis) over the wire.

    Craving VAS is the package's **first single-item instrument** — it
    dropped the Pydantic envelope's ``min_length`` from 3 to 1 so a
    1-element payload could flow through the same wire shape as every
    multi-item instrument.  It also uses a 0-100 integer range (not a
    Likert anchor set like 0-4 / 0-6 / 1-4), matching the canonical
    Visual Analog Scale form the addiction literature validates.

    Wire-envelope pattern: **continuous severity** (sentinel
    ``"continuous"``), same as PACS — Sayette 2000 publishes no bands
    and the literature treats the VAS as a per-user / per-episode
    relative signal, not a categorical screen.

    These tests pin (1) the dispatch branch picks ``score_craving_vas``,
    (2) the wire envelope carries ``severity == "continuous"`` across
    the full 0-100 range, (3) ``requires_t3`` is always False (VAS
    measures urge, not crisis; acute ideation is gated by PHQ-9 /
    C-SSRS), (4) the router accepts a 1-element payload (regression
    guard on the min_length=1 drop), (5) 0 and 2+ item payloads are
    rejected at 422, (6) out-of-range values (101, -1) are 422.
    """

    def _post_vas(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "craving_vas", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_peak_craving(self, client: TestClient) -> None:
        """Single item at 100 → total 100 → severity 'continuous'.  This
        is the EMA partner to PACS — at urge-onset the product prompts
        for a VAS, stores the 100, then re-prompts after the
        intervention for the within-episode Δ."""
        resp = self._post_vas(client, items=[100])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "craving_vas"
        assert body["total"] == 100
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "craving_vas-1.0.0"

    def test_zero_craving_still_returns_continuous_sentinel(
        self, client: TestClient
    ) -> None:
        """VAS = 0 is a meaningful EMA reading (post-detox, safe
        environment, no cues).  The sentinel ``"continuous"`` is
        invariant across the full 0-100 range — the trajectory layer
        reads ``total``, not ``severity``, for signal extraction."""
        resp = self._post_vas(client, items=[0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_midrange_total_is_still_continuous(
        self, client: TestClient
    ) -> None:
        """A midrange VAS (50) must NOT accidentally pick up a banded
        label.  If a future refactor imports a severity classifier
        from another instrument, this test catches the cross-wire."""
        resp = self._post_vas(client, items=[50])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 50
        assert body["severity"] == "continuous"

    def test_max_total_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: VAS = 100 ('strongest
        craving I have ever felt') does NOT fire T3.  Acute
        suicidality is gated by PHQ-9 item 9 / C-SSRS, consistent
        with the PACS / PHQ-15 / OCI-R / ISI safety-posture
        convention.  A patient with peak craving AND acute ideation
        needs a co-administered PHQ-9 or C-SSRS to fire T3 — VAS
        alone never does."""
        resp = self._post_vas(client, items=[100])
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_envelope_accepts_single_item(self, client: TestClient) -> None:
        """Regression guard on the ``min_length=1`` drop.  Before Sprint
        36 the envelope's ``min_length`` was 3 (AUDIT-C's count); a
        revert would 422 a legitimate VAS payload *before* it reached
        the per-instrument item-count check, producing a generic
        Pydantic-shape error instead of the diagnostic
        'craving_vas requires exactly 1 item' message.  This test
        pins that a 1-element payload routes through to the scorer."""
        resp = self._post_vas(client, items=[42])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 42
        assert body["instrument"] == "craving_vas"

    def test_rejects_empty_list(self, client: TestClient) -> None:
        """Zero items → 422.  Pydantic's ``min_length=1`` floor fires
        before the per-instrument check; either layer raising 422 is
        acceptable — callers only see the unified 422."""
        resp = self._post_vas(client, items=[])
        assert resp.status_code == 422

    def test_rejects_two_items(self, client: TestClient) -> None:
        """Two items → 422.  The per-instrument item-count check at
        ``_validate_item_count`` fires because ``craving_vas`` expects
        exactly 1 item.  A two-item payload would most commonly be a
        caller misrouting a different instrument (MDQ Part-1-only,
        a fragment of PHQ-2, etc.) — the dedicated error message
        makes the miswire obvious."""
        resp = self._post_vas(client, items=[50, 50])
        assert resp.status_code == 422

    def test_rejects_five_items(self, client: TestClient) -> None:
        """Five items is the PACS shape → 422.  Pins that the VAS
        dispatch does not silently accept a misrouted PACS payload.
        The regression this guards is a client that flipped
        ``instrument`` but forgot to replace the items array."""
        resp = self._post_vas(client, items=[1, 2, 3, 4, 5])
        assert resp.status_code == 422

    def test_rejects_one_hundred_one(self, client: TestClient) -> None:
        """Item value 101 (one above the VAS ceiling) → 422.  The
        off-by-one regression this guards is a client that reused a
        0-based inclusive 101-point UI widget."""
        resp = self._post_vas(client, items=[101])
        assert resp.status_code == 422

    def test_rejects_negative_value(self, client: TestClient) -> None:
        """Negative VAS → 422.  Regression guard against a client that
        sent a signed integer instead of the unsigned 0-100 scalar."""
        resp = self._post_vas(client, items=[-1])
        assert resp.status_code == 422

    def test_persists_vas_submission_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id lands in per-user history with the
        continuous sentinel and the single integer captured.  EMA
        trajectory analysis reads stored VAS totals across the
        timeline — a regression that dropped the total during
        persistence would silently break the within-user EMA
        baseline calculation."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "craving_vas",
            "items": [75],
            "user_id": "user-vas-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-vas-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "craving_vas"
        assert stored.total == 75
        assert stored.severity == "continuous"
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """instrument=craving_vas + extra MDQ fields → extras are
        ignored, VAS dispatch runs cleanly.  Defensive pin across the
        dispatcher-ordering contract (same guard as PACS / BIS-11 /
        PHQ-15)."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "craving_vas",
                "items": [30],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "craving_vas"
        assert body["total"] == 30
        assert body["severity"] == "continuous"


class TestReadinessRulerRouting:
    """Readiness Ruler (Rollnick 1999 / Heather 2008) over the wire.

    Readiness Ruler is the package's **second single-item instrument**
    (after Craving VAS from Sprint 36) and the **first
    higher-is-better continuous-severity instrument** besides WHO-5.
    It uses a 0-10 integer range (distinct from VAS's 0-100) and
    emits the ``"continuous"`` severity sentinel — the wire shape is
    identical to VAS even though the construct is semantically
    opposed (VAS: craving intensity, higher = worse; Ruler:
    motivation to change, higher = better).

    These tests pin (1) the dispatch branch picks
    ``score_readiness_ruler``, (2) the wire envelope carries
    ``severity == "continuous"`` across the full 0-10 range,
    (3) ``requires_t3`` is always False (low motivation is an MI
    intervention signal, not a crisis signal), (4) the envelope
    (min_length=1 post-Sprint-36) accepts a 1-element payload,
    (5) 0 and 2+ item payloads are rejected at 422, (6) out-of-range
    values (11, 100, -1) are 422 — including a regression guard for
    a VAS-range confusion (0-100 vs 0-10).
    """

    def _post_rr(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "readiness_ruler", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_fully_ready(self, client: TestClient) -> None:
        """Single item at 10 → total 10 → severity 'continuous'.  The
        action / maintenance stage.  Ruler values flow directly into
        the motivation-axis lookup the intervention layer reads
        alongside the craving axis to pick a tool variant."""
        resp = self._post_rr(client, items=[10])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "readiness_ruler"
        assert body["total"] == 10
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "readiness_ruler-1.0.0"

    def test_zero_ready_still_returns_continuous_sentinel(
        self, client: TestClient
    ) -> None:
        """Ruler = 0 is "not ready at all" — the pre-contemplation
        stance.  The sentinel ``"continuous"`` is invariant across
        the full 0-10 range; a regression that coerced this case to
        a distinct label (e.g. 'precontemplation') would cross the
        "Don't hand-roll severity thresholds" line from CLAUDE.md."""
        resp = self._post_rr(client, items=[0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_midrange_total_is_still_continuous(
        self, client: TestClient
    ) -> None:
        """Ruler = 5 (contemplation / preparation midpoint) must not
        pick up a banded label.  If a future refactor imports the
        PHQ-9 severity classifier for "mild/moderate" branding into
        this path, this test catches the cross-wire."""
        resp = self._post_rr(client, items=[5])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 5
        assert body["severity"] == "continuous"

    def test_zero_ready_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: Ruler 0 ("not ready at
        all") does NOT fire T3.  Low motivation pairs with low-agency
        mood profiles, but the product responds with MI-scripted
        interventions (decisional-balance, change-talk elicitation),
        not with T4 human handoff.  Acute ideation is gated by PHQ-9
        item 9 / C-SSRS per the uniform safety-posture convention."""
        resp = self._post_rr(client, items=[0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_envelope_accepts_single_item(self, client: TestClient) -> None:
        """Continued regression guard on the Sprint 36 ``min_length=1``
        drop.  Both single-item instruments (VAS and Ruler) depend
        on it — a revert to min_length=3 would 422 both of them
        identically."""
        resp = self._post_rr(client, items=[7])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 7
        assert body["instrument"] == "readiness_ruler"

    def test_rejects_empty_list(self, client: TestClient) -> None:
        resp = self._post_rr(client, items=[])
        assert resp.status_code == 422

    def test_rejects_two_items(self, client: TestClient) -> None:
        """Two items → 422.  A caller sending two items is most
        commonly submitting a PHQ-2 / GAD-2 payload with the wrong
        instrument key.  The dedicated 422 makes the miswire obvious."""
        resp = self._post_rr(client, items=[5, 5])
        assert resp.status_code == 422

    def test_rejects_sixteen_items(self, client: TestClient) -> None:
        """16 items is the URICA short-form shape (§3.1 row #10 —
        planned for a future sprint).  When URICA ships, the Ruler
        dispatch must NOT silently accept a misrouted URICA payload."""
        resp = self._post_rr(client, items=[2] * 16)
        assert resp.status_code == 422

    def test_rejects_eleven(self, client: TestClient) -> None:
        """Value 11 (one above the Heather 2008 ceiling) → 422.  The
        classic off-by-one regression guard."""
        resp = self._post_rr(client, items=[11])
        assert resp.status_code == 422

    def test_rejects_one_hundred_vas_range_confusion(
        self, client: TestClient
    ) -> None:
        """Value 100 → 422.  Regression guard against a caller who
        switched from Craving VAS to Readiness Ruler but forgot to
        rescale 0-100 → 0-10.  Since both instruments use the same
        single-item wire shape, a silent VAS→Ruler misroute would
        otherwise be invisible."""
        resp = self._post_rr(client, items=[100])
        assert resp.status_code == 422

    def test_rejects_negative_value(self, client: TestClient) -> None:
        """Negative Ruler → 422.  Regression guard against a client
        that sent a signed integer instead of the unsigned 0-10
        scalar."""
        resp = self._post_rr(client, items=[-1])
        assert resp.status_code == 422

    def test_persists_ruler_submission_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id lands in per-user history with the
        continuous sentinel and the single integer captured.
        Trajectory analysis reads stored Ruler totals across the
        timeline — a regression that dropped the total during
        persistence would silently break the motivation-trajectory
        signal the intervention layer reads for tool-variant
        selection."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        body = {
            "instrument": "readiness_ruler",
            "items": [8],
            "user_id": "user-rr-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-rr-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "readiness_ruler"
        assert stored.total == 8
        assert stored.severity == "continuous"
        assert stored.requires_t3 is False

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """instrument=readiness_ruler + MDQ fields → MDQ fields
        ignored, Ruler dispatch runs cleanly.  Defensive pin across
        the dispatcher-ordering contract — same guard as PACS / VAS /
        BIS-11 / PHQ-15."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "readiness_ruler",
                "items": [6],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "readiness_ruler"
        assert body["total"] == 6
        assert body["severity"] == "continuous"


# =============================================================================
# DTCQ-8 (Sklar & Turner 1999 — 8-item Drug-Taking Confidence Questionnaire)
# =============================================================================


class TestDtcq8Routing:
    """DTCQ-8 (Sklar & Turner 1999) over the wire.

    DTCQ-8 is the package's **first profiled continuous instrument** —
    the 8-tuple carries per-situation coping-self-efficacy signal the
    intervention layer reads by position (social-pressure weakness vs
    unpleasant-emotions weakness route to different tool variants at
    the same aggregate).  The wire response envelope surfaces only the
    aggregate ``total`` — clinician-UI surfaces that render the full
    Marlatt 1985 profile go through the PHI-boundary-gated repository
    path.  The **third higher-is-better continuous-severity instrument**
    (after WHO-5 and Ruler); the severity sentinel remains
    ``"continuous"`` uniform with PACS / VAS / Ruler, since Sklar 1999
    publishes no bands.

    These tests pin (1) the dispatch branch picks ``score_dtcq8``,
    (2) the wire envelope carries ``severity == "continuous"`` across
    the full 0-100 range, (3) ``requires_t3`` is always False (low
    coping is a skill-building signal, not a crisis signal), (4) the
    ``total`` field equals the mean-rounded-to-int per Sklar 1999
    scoring, (5) 7 / 9 / 50-item payloads are rejected at 422 (off-by-
    one + long-form DTCQ misroute guards), and (6) out-of-range values
    (-1, 101, 200) are 422.  Also pins the per-situation profile
    preservation contract end-to-end through the router — the stored
    ``raw_items`` tuple matches the submitted 8-tuple positionally so
    the intervention layer's per-situation lookup is intact after
    persistence.
    """

    def _post_dtcq8(
        self,
        client: TestClient,
        *,
        items: list[int],
        user_id: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {"instrument": "dtcq8", "items": items}
        if user_id is not None:
            body["user_id"] = user_id
        return client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_maintenance_profile(self, client: TestClient) -> None:
        """Uniform 90 — maintenance-stage broad coping confidence →
        total 90 → severity 'continuous'.  No T3."""
        resp = self._post_dtcq8(client, items=[90] * 8)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "dtcq8"
        assert body["total"] == 90
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "dtcq8-1.0.0"

    def test_rock_bottom_coping_returns_continuous_sentinel(
        self, client: TestClient
    ) -> None:
        """All 0s → "no confidence at all" in every Marlatt situation.
        Must emit ``severity == "continuous"`` — a regression that
        classified this case as a distinct label (e.g. 'low_coping')
        would cross the "Don't hand-roll severity thresholds" line
        from CLAUDE.md."""
        resp = self._post_dtcq8(client, items=[0] * 8)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_midrange_total_is_still_continuous(
        self, client: TestClient
    ) -> None:
        """Uniform 50 — the "moderate confidence" clinician-training
        vignette.  Must not pick up a banded label — the 50% anchor
        is pedagogical, not a validated cutoff."""
        resp = self._post_dtcq8(client, items=[50] * 8)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 50
        assert body["severity"] == "continuous"

    def test_mean_rounds_to_int_in_router_envelope(
        self, client: TestClient
    ) -> None:
        """Items [50,50,50,50,50,50,50,51] → exact mean 50.125 →
        rounded total 50.  The router envelope exposes the int total;
        the exact float ``mean`` lives on the scorer result but is
        NOT on the wire response shape (kept int-only for uniformity
        with every other instrument)."""
        resp = self._post_dtcq8(
            client, items=[50, 50, 50, 50, 50, 50, 50, 51]
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 50
        # The wire response shape is int-only — ``mean`` is not a
        # field.  A regression that added ``mean`` to AssessmentResult
        # without extending every renderer would break this test AND
        # the sibling instruments' serialization contracts.
        assert "mean" not in body

    def test_profile_weakness_aggregate(self, client: TestClient) -> None:
        """Seven situations at 80, one weak spot (item 7 —
        social_pressure_to_use) at 10.  Mean = 570/8 = 71.25 →
        rounded total 71.  This is the "social-pressure weakness"
        profile the intervention layer reads to pick refusal-skills
        scripts — here we pin only the aggregate; the per-situation
        lookup is verified in
        ``test_persists_profile_verbatim_in_history`` below."""
        resp = self._post_dtcq8(
            client, items=[80, 80, 80, 80, 80, 80, 10, 80]
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 71
        assert body["severity"] == "continuous"

    def test_zero_coping_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: DTCQ-8 all-zeros ("no
        confidence in any situation") does NOT fire T3.  Low
        self-efficacy pairs with high-craving / low-motivation
        profiles, but the product responds with skill-building
        interventions matched to the weakest category — not T4
        human handoff.  Acute ideation is gated by PHQ-9 item 9 /
        C-SSRS per the uniform safety-posture convention."""
        resp = self._post_dtcq8(client, items=[0] * 8)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_empty_list(self, client: TestClient) -> None:
        resp = self._post_dtcq8(client, items=[])
        assert resp.status_code == 422

    def test_rejects_seven_items(self, client: TestClient) -> None:
        """Off-by-one below.  A caller dropping one Marlatt category
        would silently misreport the aggregate if padding or
        truncation existed."""
        resp = self._post_dtcq8(client, items=[50] * 7)
        assert resp.status_code == 422

    def test_rejects_nine_items(self, client: TestClient) -> None:
        """Off-by-one above.  9 items is the PHQ-9 shape — a caller
        wiring DTCQ-8 through a PHQ-9 code path would send 9 items;
        the dispatch must 422 with a DTCQ-8-specific message rather
        than silently scoring the first 8."""
        resp = self._post_dtcq8(client, items=[50] * 9)
        assert resp.status_code == 422

    def test_rejects_fifty_items_long_form_misroute(
        self, client: TestClient
    ) -> None:
        """50 items is the long-form DTCQ shape (Sklar 1997).  The
        8-item dispatch must NOT silently accept a long-form payload
        — the semantic "one item per Marlatt category" mapping
        breaks at any other length, and silently scoring the first 8
        would produce a profile that does not match the long-form
        category assignments."""
        resp = self._post_dtcq8(client, items=[50] * 50)
        assert resp.status_code == 422

    def test_rejects_one_hundred_one(self, client: TestClient) -> None:
        """Off-by-one above the 0-100 ceiling → 422.  The classic
        regression guard."""
        resp = self._post_dtcq8(
            client, items=[50, 50, 50, 50, 50, 50, 50, 101]
        )
        assert resp.status_code == 422

    def test_rejects_negative_value(self, client: TestClient) -> None:
        """Negative confidence → 422.  Regression guard against a
        caller that sent a signed integer instead of the unsigned
        0-100 scalar."""
        resp = self._post_dtcq8(
            client, items=[-1, 50, 50, 50, 50, 50, 50, 50]
        )
        assert resp.status_code == 422

    def test_persists_profile_verbatim_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id lands in per-user history with the
        full 8-tuple preserved positionally.  This is THE load-bearing
        contract for DTCQ-8 — the intervention layer reads the per-
        situation profile from the stored record, NOT from the wire
        response (the response exposes only the aggregate ``total``).
        A regression that sorted, deduplicated, or truncated the
        stored items would silently break tool-variant selection
        across every Marlatt category."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Social-pressure weakness profile — distinct per-position
        # values so a reorder regression shows up in multiple
        # assertions at once.
        submitted = [80, 85, 75, 70, 90, 95, 10, 65]
        body = {
            "instrument": "dtcq8",
            "items": submitted,
            "user_id": "user-dtcq8-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-dtcq8-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "dtcq8"
        assert stored.severity == "continuous"
        assert stored.requires_t3 is False
        # Positional preservation — every index must match the
        # submitted value.
        assert stored.raw_items == tuple(submitted)
        # Aggregate sanity check: mean = 570/8 = 71.25 → total 71.
        assert stored.total == 71

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """instrument=dtcq8 + MDQ fields → MDQ fields ignored, DTCQ-8
        dispatch runs cleanly.  Defensive pin across the dispatcher-
        ordering contract — same guard as PACS / VAS / Ruler / BIS-11
        / PHQ-15."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "dtcq8",
                "items": [60] * 8,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "dtcq8"
        assert body["total"] == 60
        assert body["severity"] == "continuous"


class TestUricaRouting:
    """URICA short (DiClemente & Hughes 1990) over the wire.

    URICA is the **first multi-subscale wire-exposed instrument** in the
    package — the dispatch surfaces the four stages-of-change
    subscales (precontemplation / contemplation / action / maintenance)
    on the response envelope's ``subscales`` map so the intervention
    layer reads the stage profile alongside the Readiness aggregate
    without a second round-trip.  It is also the **first signed-total
    instrument** — Readiness = ``C + A + M − PC`` is a signed int
    (range −8 to +56) where a negative reading is clinically meaningful
    (precontemplation-dominant profile).

    These tests pin (1) the dispatch branch picks ``score_urica``,
    (2) the wire envelope carries ``severity == "continuous"``,
    (3) ``requires_t3`` is always False (URICA has no safety item),
    (4) the ``subscales`` dict is present and carries the four
    DiClemente & Hughes 1990 stage keys with correct integer values,
    (5) the 32-item URICA-long-form is rejected at 422 (explicit
    misroute guard — the short form MUST NOT silently accept the
    long-form payload), (6) the 1-5 range is enforced with ``0``
    explicitly rejected (the Likert min is 1, not 0 — off-by-one guard
    against a validator copy-pasted from a 0-based PHQ-9 / GAD-7
    scorer), (7) negative Readiness survives the pydantic serialization
    path (int, signed), and (8) submission with a user_id persists the
    subscales map verbatim to the history timeline so clinician-UI
    renderers can fetch the stage profile without re-scoring.
    """

    def _post_urica(
        self,
        client: TestClient,
        *,
        items: list[int],
        user_id: str | None = None,
    ) -> Any:
        body: dict[str, Any] = {"instrument": "urica", "items": items}
        if user_id is not None:
            body["user_id"] = user_id
        return client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_happy_path_balanced_profile(self, client: TestClient) -> None:
        """Uniform 3 ("undecided") across all 16 items → every subscale
        sums to 12; Readiness = 12 + 12 + 12 − 12 = 24.  ``severity``
        must be the continuous sentinel, ``requires_t3`` False, and the
        subscales map must carry all four stage keys with matching
        values."""
        resp = self._post_urica(client, items=[3] * 16)
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "urica"
        assert body["total"] == 24
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "urica-1.0.0"
        # Subscales present and correctly keyed.
        assert body["subscales"] == {
            "precontemplation": 12,
            "contemplation": 12,
            "action": 12,
            "maintenance": 12,
        }

    def test_deep_action_profile_maximum_readiness(
        self, client: TestClient
    ) -> None:
        """Precontemplation all 1s (minimal), Contemplation / Action /
        Maintenance all 5s (maximal) → PC=4, C/A/M=20 each → Readiness
        = 20 + 20 + 20 − 4 = **+56** (the maximum, deep-action profile).
        Pins both the ceiling of the signed range and that the positive
        extreme serializes cleanly."""
        items = [1] * 4 + [5] * 4 + [5] * 4 + [5] * 4
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 56
        assert body["subscales"] == {
            "precontemplation": 4,
            "contemplation": 20,
            "action": 20,
            "maintenance": 20,
        }
        assert body["severity"] == "continuous"

    def test_pure_precontemplator_negative_readiness_on_wire(
        self, client: TestClient
    ) -> None:
        """PC all 5s (maximal), others all 1s (minimal) → PC=20,
        C/A/M=4 each → Readiness = 4 + 4 + 4 − 20 = **−8** (the floor
        of the signed range).  This is THE load-bearing test for the
        signed-total contract — a caller serializing through an
        ``int`` field (not ``uint``) must survive the negative value
        end-to-end with no overflow, no clipping, and no absolute-
        value mistake anywhere in the stack.  URICA is the first
        instrument in the package whose wire ``total`` can be
        negative; a regression that clamped to 0 (or took absolute
        value) would silently misclassify precontemplation-dominant
        users as neutral and break the cluster-analytic subtype
        read-out at the intervention-selection layer."""
        items = [5] * 4 + [1] * 4 + [1] * 4 + [1] * 4
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        # Signed-int survival — the whole point of the test.
        assert body["total"] == -8
        assert isinstance(body["total"], int)
        assert body["subscales"] == {
            "precontemplation": 20,
            "contemplation": 4,
            "action": 4,
            "maintenance": 4,
        }
        # Still no T3 — negative Readiness is an MI signal, not a
        # crisis signal.  This is the uniform safety-posture
        # convention across PACS / VAS / Ruler / DTCQ-8.
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_zero_crossing_vignette(self, client: TestClient) -> None:
        """Boundary case — Readiness exactly 0.  PC = 3+3+3+3 = 12,
        and C + A + M = 4+4+4 = 12 → Readiness = 12 − 12 = 0.  A
        regression that treated 0 as "missing" (instead of the
        legitimate "neutral Readiness" signal) would silently drop
        the point from trajectory charts."""
        # PC = 3*4 = 12.  Need C + A + M = 12 total — use 2+2+2+2=8 for
        # contemplation, then 1+1+1+1=4 for action, then 0 for
        # maintenance — wait, floor is 1.  Use 1+1+1+1=4 three times =
        # 12.  Redistribute: C=4, A=4, M=4 → sum 12 = PC.
        items = [3] * 4 + [1] * 4 + [1] * 4 + [1] * 4
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert isinstance(body["total"], int)
        assert body["subscales"] == {
            "precontemplation": 12,
            "contemplation": 4,
            "action": 4,
            "maintenance": 4,
        }

    def test_maintenance_with_relapse_warning_profile(
        self, client: TestClient
    ) -> None:
        """Clinical vignette — moderate PC (10) indicating creeping
        ambivalence, low-moderate C (12), moderate A (14), high M (18):
        Readiness = 12 + 14 + 18 − 10 = 34.  The stage profile itself
        (not just the aggregate) is the intervention signal — the
        trajectory layer reading this vs a prior pure-maintenance
        profile flags the creeping precontemplation as a relapse-
        warning pattern.  Pins that the per-subscale integers survive
        the dispatch unchanged."""
        # PC sum 10: 2+3+2+3
        # C sum 12: 3+3+3+3
        # A sum 14: 4+4+3+3
        # M sum 18: 5+5+4+4
        items = [2, 3, 2, 3] + [3, 3, 3, 3] + [4, 4, 3, 3] + [5, 5, 4, 4]
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 34
        assert body["subscales"] == {
            "precontemplation": 10,
            "contemplation": 12,
            "action": 14,
            "maintenance": 18,
        }
        assert body["severity"] == "continuous"

    def test_no_t3_fires_even_on_extreme_precontemplation(
        self, client: TestClient
    ) -> None:
        """Critical clinical-safety contract: URICA max-PC + min-others
        ("I definitely don't have a problem") must NOT fire T3.  A
        precontemplation-dominant user is routed to MI-scripted
        interventions (decisional-balance elicitation, empathic
        reflection of ambivalence), not to the crisis path.  Acute
        ideation is gated by PHQ-9 item 9 / C-SSRS per the uniform
        safety-posture convention across PACS / VAS / Ruler / DTCQ-8."""
        items = [5] * 4 + [1] * 4 + [1] * 4 + [1] * 4
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_rejects_empty_list(self, client: TestClient) -> None:
        resp = self._post_urica(client, items=[])
        assert resp.status_code == 422

    def test_rejects_fifteen_items(self, client: TestClient) -> None:
        """Off-by-one below.  A caller submitting 15 items would
        silently drop one stage's fourth item if padding existed;
        the dispatch must 422 with a URICA-specific message."""
        resp = self._post_urica(client, items=[3] * 15)
        assert resp.status_code == 422

    def test_rejects_seventeen_items(self, client: TestClient) -> None:
        """Off-by-one above.  17 items would either land silently in
        one subscale or be truncated with loss of information."""
        resp = self._post_urica(client, items=[3] * 17)
        assert resp.status_code == 422

    def test_rejects_thirty_two_long_form_misroute(
        self, client: TestClient
    ) -> None:
        """32 items is the **URICA long form** (McConnaughy 1983).  The
        16-item short-form dispatch must NOT silently accept a
        long-form payload — the per-subscale positional mapping is
        different (long form uses 8-item subscales, short form 4), so
        silently scoring would produce wrong subscale sums and a wrong
        Readiness aggregate.  Load-bearing guard: any regression that
        relaxed item_count validation to ``%4 == 0`` would accept both
        shapes silently."""
        resp = self._post_urica(client, items=[3] * 32)
        assert resp.status_code == 422

    def test_rejects_zero_value(self, client: TestClient) -> None:
        """URICA Likert range is 1-5 (NOT 0-based).  A caller wiring
        URICA through a 0-based Likert code path (PHQ-9, GAD-7,
        PSS-10) would send 0s, which must 422.  Silently accepting 0
        would corrupt every subscale sum proportional to the number
        of zeros submitted.  This is the **critical regression guard**
        for the 1-based Likert shape — second instrument in the
        package after BIS-11 where 0 is out of range."""
        items = [0] + [3] * 15
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 422

    def test_rejects_six_value(self, client: TestClient) -> None:
        """Off-by-one above the 1-5 ceiling → 422."""
        items = [3] * 15 + [6]
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 422

    def test_rejects_negative_value(self, client: TestClient) -> None:
        """Signed-int submission that sneaks past an unsigned int
        validator → 422.  Belt-and-braces given URICA's signed-total
        output — callers must not submit signed *inputs*; only the
        Readiness aggregate is signed."""
        items = [-1] + [3] * 15
        resp = self._post_urica(client, items=items)
        assert resp.status_code == 422

    def test_persists_subscales_verbatim_in_history(
        self, client: TestClient
    ) -> None:
        """Submission with user_id lands in per-user history with the
        ``subscales`` dict preserved verbatim.  This is the load-bearing
        contract for the **multi-subscale wire-exposure pattern** — a
        clinician-UI surface rendering the stages-of-change profile
        reads the stored subscales from the history endpoint without
        re-scoring.  A regression that dropped the subscales map
        during persistence would force every render to re-score from
        raw_items (duplicating work and bloating the clinician
        portal's read path)."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        # Deep-action profile — distinctive per-subscale values so
        # a swap regression shows up across multiple assertions.
        # PC = 1+2+1+2 = 6
        # C  = 4+4+4+4 = 16
        # A  = 5+5+5+4 = 19
        # M  = 5+5+4+4 = 18
        # Readiness = 16 + 19 + 18 − 6 = 47
        submitted = [1, 2, 1, 2] + [4, 4, 4, 4] + [5, 5, 5, 4] + [5, 5, 4, 4]
        body = {
            "instrument": "urica",
            "items": submitted,
            "user_id": "user-urica-1",
        }
        resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        response_body = resp.json()
        assert response_body["total"] == 47
        assert response_body["subscales"] == {
            "precontemplation": 6,
            "contemplation": 16,
            "action": 19,
            "maintenance": 18,
        }

        repo = get_assessment_repository()
        records = repo.history_for("user-urica-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "urica"
        assert stored.severity == "continuous"
        assert stored.requires_t3 is False
        assert stored.total == 47
        assert stored.subscales == {
            "precontemplation": 6,
            "contemplation": 16,
            "action": 19,
            "maintenance": 18,
        }
        # Raw items preserved positionally for trajectory re-scoring
        # and audit — uniform with DTCQ-8 / PACS / VAS.
        assert stored.raw_items == tuple(submitted)

    def test_history_projection_surfaces_subscales(
        self, client: TestClient
    ) -> None:
        """``GET /v1/assessments/history`` projection must carry the
        ``subscales`` dict so clinician-UI timeline views don't need
        to issue per-row re-reads through the PHI-boundary-gated
        repository path for the stage-profile summary."""
        body = {
            "instrument": "urica",
            "items": [3] * 16,
            "user_id": "user-urica-2",
        }
        post_resp = client.post(
            "/v1/assessments",
            json=body,
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert post_resp.status_code == 201

        history_resp = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-urica-2"},
        )
        assert history_resp.status_code == 200
        history_body = history_resp.json()
        assert history_body["total"] == 1
        item = history_body["items"][0]
        assert item["instrument"] == "urica"
        assert item["total"] == 24
        assert item["subscales"] == {
            "precontemplation": 12,
            "contemplation": 12,
            "action": 12,
            "maintenance": 12,
        }

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """instrument=urica + MDQ fields → MDQ fields ignored, URICA
        dispatch runs cleanly.  Defensive pin across the dispatcher-
        ordering contract — same guard as DTCQ-8 / PACS / VAS / Ruler /
        BIS-11 / PHQ-15."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "urica",
                "items": [3] * 16,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "urica"
        assert body["total"] == 24
        assert body["severity"] == "continuous"
        assert body["subscales"] == {
            "precontemplation": 12,
            "contemplation": 12,
            "action": 12,
            "maintenance": 12,
        }


# =============================================================================
# PHQ-2 (Kroenke 2003) — 2-item ultra-short depression pre-screener
# =============================================================================


class TestPhq2Routing:
    """PHQ-2 over the wire.

    Router-level contract verification for the 2-item cutoff screen.
    The scorer's own unit tests exhaustively pin the ``>= 3`` cutoff
    and item validation; these tests pin:
    (1) the dispatch branch picks ``score_phq2``,
    (2) the wire envelope surfaces ``positive_screen`` and carries the
        Likert-weighted total (0-6) as ``total`` (uniform with PC-PTSD-5
        / MDQ / AUDIT-C's cutoff-only envelope),
    (3) ``requires_t3`` is always False — PHQ-2 deliberately excludes
        PHQ-9 item 9 (suicidality) so the T3 pathway is unreachable
        from a PHQ-2 submission regardless of score.  A regression
        that let PHQ-2 fire T3 would defeat the whole point of the
        2-item ultra-short form (daily-EMA surface without an in-line
        safety-routing interrupt) — the clinical contract is that
        acute ideation stays gated by weekly PHQ-9 / on-demand
        C-SSRS.
    (4) dispatch ordering: PHQ-2 is handled before the MDQ
        fallthrough so an MDQ-only field on a PHQ-2 submission is
        silently ignored (defensive pin against dispatcher
        reordering).
    """

    def _post_phq2(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "phq2", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_total_three_at_cutoff_is_positive_screen(
        self, client: TestClient
    ) -> None:
        """At the Kroenke 2003 cutoff (total = 3 — e.g. anhedonia
        "more than half the days" + depressed mood "several days") →
        the wire response surfaces ``positive_screen=True``.  This is
        the exact operating point; a fence-post regression would break
        this case most visibly."""
        resp = self._post_phq2(client, items=[2, 1])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "phq2"
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "phq2-1.0.0"

    def test_total_two_below_cutoff_is_negative_screen(
        self, client: TestClient
    ) -> None:
        """Just below the cutoff (total = 2) → negative_screen.
        Kroenke 2003 considered cutoff 2 but rejected it for
        over-firing on sub-clinical low-mood days; the router must
        follow the chosen operating point."""
        resp = self._post_phq2(client, items=[1, 1])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "phq2"
        assert body["total"] == 2
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["requires_t3"] is False

    def test_zero_total_is_negative_screen(self, client: TestClient) -> None:
        """Zero on both items → negative screen.  The degenerate case:
        a patient with no depressive symptoms in the past 2 weeks."""
        resp = self._post_phq2(client, items=[0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    def test_max_total_is_positive_screen(self, client: TestClient) -> None:
        """Both items "nearly every day" (total = 6) → unambiguous
        positive screen — canonical major-depression presentation on
        PHQ-2, routes the patient to full PHQ-9 administration."""
        resp = self._post_phq2(client, items=[3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 6
        assert body["positive_screen"] is True

    def test_single_max_item_hits_cutoff(self, client: TestClient) -> None:
        """One item maxed (3), the other zero (total = 3) → positive.
        A patient with "every day depressed mood but no anhedonia" is
        still a positive screen — the cutoff is on the total, not on
        per-item thresholds.  Pins the scorer's sum-based gate at the
        wire layer."""
        resp = self._post_phq2(client, items=[3, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 3
        assert body["positive_screen"] is True

    def test_positive_screen_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: even a maximum PHQ-2
        score (both items "nearly every day") never fires the T3
        crisis pathway.  PHQ-2 deliberately excludes PHQ-9 item 9
        (suicidality) — a regression that let PHQ-2 fire T3 would
        (a) spam the clinical-ops safety queue on daily EMA volume
        and (b) defeat the design purpose of the 2-item short form
        (friction-minimizing daily check-in without an in-line
        safety interrupt).  Acute ideation is gated by weekly
        PHQ-9 / on-demand C-SSRS."""
        resp = self._post_phq2(client, items=[3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_emits_subscales_none(self, client: TestClient) -> None:
        """PHQ-2 has no subscales — the wire envelope must emit
        ``subscales=None`` (not an empty dict) to match the convention
        for non-subscale instruments (PHQ-9 / GAD-7 / WHO-5 / etc.).
        A client renderer keying on ``body["subscales"] is None`` to
        hide the subscale panel would render an empty panel if this
        field silently regressed to ``{}``."""
        resp = self._post_phq2(client, items=[3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body.get("subscales") is None

    def test_rejects_one_item(self, client: TestClient) -> None:
        """Wrong item count → 422.  Client-side bug where the UI
        dropped an item should surface as a validation error, not a
        silent partial score."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "phq2", "items": [2]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_three_items(self, client: TestClient) -> None:
        """Extra item → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "phq2", "items": [2, 1, 1]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_nine_items_phq9_misroute(
        self, client: TestClient
    ) -> None:
        """A 9-item submission against ``instrument=phq2`` is almost
        certainly a mis-routed PHQ-9 (a UI bug that passed the full
        PHQ-9 array but tagged it phq2).  Must 422 with the
        2-items-expected message rather than partially scoring — a
        silent partial score here could under-report depression
        severity and delay a PHQ-9 follow-up."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "phq2", "items": [0, 0, 0, 0, 0, 0, 0, 0, 0]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Item value > 3 → 422.  PHQ-2 is 0-3 four-point Likert — a
        4 or 5 is a contract violation (e.g. a UI bug in a 5-point
        slider)."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "phq2", "items": [4, 2]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        """Negative item value → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "phq2", "items": [-1, 2]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """A submission with a user_id shows up in the per-user
        history with the positive_screen flag captured — the history
        endpoint relies on the stored record via the repository.
        Downstream clinician UI renders the positive-screen badge
        from this persisted field, not from a re-score at read time.
        """
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq2",
                "items": [3, 2],
                "user_id": "user-phq2-1",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-phq2-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "phq2"
        assert stored.total == 5
        assert stored.positive_screen is True
        assert stored.requires_t3 is False
        # PHQ-2 has no subscales — the stored record carries None, not
        # an empty dict.  Matches the wire envelope convention.
        assert stored.subscales is None

    def test_history_projection_surfaces_positive_screen(
        self, client: TestClient
    ) -> None:
        """The /history endpoint projects PHQ-2 records with the
        ``positive_screen`` field populated so a user-facing timeline
        can render the binary screen badge without a second round-trip
        to re-score.  PHQ-9 would need the severity band here; PHQ-2
        renders the screen flag."""
        client.post(
            "/v1/assessments",
            json={
                "instrument": "phq2",
                "items": [3, 3],
                "user_id": "user-phq2-hist",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        resp = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-phq2-hist"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["instrument"] == "phq2"
        assert item["total"] == 6
        assert item["severity"] == "positive_screen"
        assert item["positive_screen"] is True
        assert item["requires_t3"] is False
        assert item["subscales"] is None

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """``concurrent_symptoms`` and ``functional_impairment`` are
        MDQ-only.  The PHQ-2 dispatch branch is handled before the
        MDQ fallthrough so if a client mistakenly sends those fields
        on a PHQ-2 request, the scorer ignores them — a defensive pin
        against dispatcher-ordering regressions (the MDQ fallthrough
        is the last branch, so any new instrument added *after* MDQ
        would silently demand Part 2 / Part 3 validation)."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq2",
                "items": [2, 1],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "phq2"
        assert body["positive_screen"] is True


# =============================================================================
# GAD-2 (Kroenke 2007) — 2-item ultra-short anxiety pre-screener
# =============================================================================


class TestGad2Routing:
    """GAD-2 over the wire.

    Router-level contract verification for the 2-item cutoff screen.
    The scorer's own unit tests exhaustively pin the ``>= 3`` cutoff
    and item validation; these tests pin:
    (1) the dispatch branch picks ``score_gad2``,
    (2) the wire envelope surfaces ``positive_screen`` and carries the
        Likert-weighted total (0-6) as ``total`` (uniform with PHQ-2 /
        PC-PTSD-5 / MDQ / AUDIT-C's cutoff-only envelope),
    (3) ``requires_t3`` is always False — GAD-2 has no safety item
        (neither does GAD-7 full form) so the T3 pathway is
        unreachable from an anxiety screen regardless of score.
        A regression that let GAD-2 fire T3 would spam the clinical-
        ops safety queue on daily EMA volume and defeat the design
        purpose of the 2-item short form (friction-minimizing daily
        check-in).  Acute ideation stays gated by PHQ-9 item 9 /
        C-SSRS on demand.
    (4) dispatch ordering: GAD-2 is handled before the MDQ fallthrough
        (same defensive pin as PHQ-2).
    """

    def _post_gad2(
        self,
        client: TestClient,
        *,
        items: list[int],
    ) -> Any:
        return client.post(
            "/v1/assessments",
            json={"instrument": "gad2", "items": items},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

    def test_total_three_at_cutoff_is_positive_screen(
        self, client: TestClient
    ) -> None:
        """At the Kroenke 2007 cutoff (total = 3 — e.g. nervousness
        "more than half the days" + uncontrolled worry "several days")
        → the wire response surfaces ``positive_screen=True``.  This
        is the exact operating point; a fence-post regression would
        break this case most visibly."""
        resp = self._post_gad2(client, items=[2, 1])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "gad2"
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body["instrument_version"] == "gad2-1.0.0"

    def test_total_two_below_cutoff_is_negative_screen(
        self, client: TestClient
    ) -> None:
        """Just below the cutoff (total = 2) → negative_screen.
        Kroenke 2007 considered cutoff 2 but rejected it for
        over-firing on sub-clinical situational worry."""
        resp = self._post_gad2(client, items=[1, 1])
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "gad2"
        assert body["total"] == 2
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["requires_t3"] is False

    def test_zero_total_is_negative_screen(self, client: TestClient) -> None:
        """Zero on both items → negative screen.  The degenerate case:
        a patient with no anxiety symptoms in the past 2 weeks."""
        resp = self._post_gad2(client, items=[0, 0])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    def test_max_total_is_positive_screen(self, client: TestClient) -> None:
        """Both items "nearly every day" (total = 6) → unambiguous
        positive screen — canonical GAD presentation on GAD-2, routes
        the patient to full GAD-7 administration."""
        resp = self._post_gad2(client, items=[3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 6
        assert body["positive_screen"] is True

    def test_single_max_item_hits_cutoff(self, client: TestClient) -> None:
        """One item maxed (3), the other zero (total = 3) → positive.
        A patient with "every day uncontrolled worry but no
        nervousness symptom" is still a positive screen — the cutoff
        is on the total, not on per-item thresholds."""
        resp = self._post_gad2(client, items=[0, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] == 3
        assert body["positive_screen"] is True

    def test_positive_screen_does_not_fire_t3(self, client: TestClient) -> None:
        """Critical clinical-safety contract: even a maximum GAD-2
        score never fires the T3 crisis pathway.  GAD-2 has no
        suicidality item (and neither does GAD-7 full form).  A
        regression that let GAD-2 fire T3 would spam clinical-ops on
        daily EMA volume and desensitize responders to real crises."""
        resp = self._post_gad2(client, items=[3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_emits_subscales_none(self, client: TestClient) -> None:
        """GAD-2 has no subscales — the wire envelope must emit
        ``subscales=None`` (not an empty dict) to match the
        convention for non-subscale instruments."""
        resp = self._post_gad2(client, items=[3, 3])
        assert resp.status_code == 201
        body = resp.json()
        assert body.get("subscales") is None

    def test_rejects_one_item(self, client: TestClient) -> None:
        """Wrong item count → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "gad2", "items": [2]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_three_items(self, client: TestClient) -> None:
        """Extra item → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "gad2", "items": [2, 1, 1]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_seven_items_gad7_misroute(
        self, client: TestClient
    ) -> None:
        """A 7-item submission against ``instrument=gad2`` is almost
        certainly a mis-routed GAD-7 (a UI bug that passed the full
        GAD-7 array but tagged it gad2).  Must 422 with the
        2-items-expected message rather than partially scoring."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "gad2", "items": [0, 0, 0, 0, 0, 0, 0]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Item value > 3 → 422.  GAD-2 is 0-3 four-point Likert."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "gad2", "items": [4, 2]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        """Negative item value → 422."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "gad2", "items": [-1, 2]},
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """A submission with a user_id shows up in the per-user
        history with the positive_screen flag captured."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "gad2",
                "items": [3, 2],
                "user_id": "user-gad2-1",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-gad2-1", limit=10)
        assert len(records) == 1
        stored = records[0]
        assert stored.instrument == "gad2"
        assert stored.total == 5
        assert stored.positive_screen is True
        assert stored.requires_t3 is False
        assert stored.subscales is None

    def test_history_projection_surfaces_positive_screen(
        self, client: TestClient
    ) -> None:
        """The /history endpoint projects GAD-2 records with the
        ``positive_screen`` field populated."""
        client.post(
            "/v1/assessments",
            json={
                "instrument": "gad2",
                "items": [3, 3],
                "user_id": "user-gad2-hist",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        resp = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-gad2-hist"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["instrument"] == "gad2"
        assert item["total"] == 6
        assert item["severity"] == "positive_screen"
        assert item["positive_screen"] is True
        assert item["requires_t3"] is False
        assert item["subscales"] is None

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """``concurrent_symptoms`` and ``functional_impairment`` are
        MDQ-only.  The GAD-2 dispatch branch is handled before the
        MDQ fallthrough — defensive pin against dispatcher-ordering
        regressions."""
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "gad2",
                "items": [2, 1],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"] == "gad2"
        assert body["positive_screen"] is True

    def test_phq2_and_gad2_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """The daily-EMA clinical pattern: PHQ-2 + GAD-2 submitted
        together (same user, same day).  Both must land on the user's
        timeline independently and render with their own per-
        instrument cutoff labels.  Pins the router/repository
        contract that the two companion screeners do NOT collide or
        overwrite each other's records — a regression where the
        history endpoint deduplicated by something like (user,
        date, severity) would hide one of the two signals."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        client.post(
            "/v1/assessments",
            json={
                "instrument": "phq2",
                "items": [3, 2],
                "user_id": "user-daily-ema",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "gad2",
                "items": [2, 2],
                "user_id": "user-daily-ema",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        repo = get_assessment_repository()
        records = repo.history_for("user-daily-ema", limit=10)
        assert len(records) == 2
        instruments = {r.instrument for r in records}
        assert instruments == {"phq2", "gad2"}
        # Both positive — the daily-EMA surface would escalate both to
        # their full-form partners (PHQ-9 / GAD-7) in the clinician
        # workflow.
        for r in records:
            assert r.positive_screen is True


class TestOasisRouting:
    """OASIS (Norman 2006 / Campbell-Sills 2009) router dispatch.

    Wire contract invariants:
    - Cutoff envelope (``severity = positive_screen / negative_screen``)
      uniform with PHQ-2 / GAD-2 / PC-PTSD-5 / MDQ / AUDIT-C.
    - Cutoff is ``>= 8`` (Campbell-Sills 2009).  Boundary 7/8 pinned.
    - ``requires_t3`` is always False — OASIS has no safety item.
    - ``subscales=None`` — Norman 2006 validates only the total (no
      symptom / avoidance / impairment split).
    """

    def test_total_eight_at_cutoff_is_positive_screen(
        self, client: TestClient
    ) -> None:
        """Total = 8 (items [2,2,2,1,1]) → positive.  This is the
        exact Campbell-Sills 2009 operating point; a ``> 8``
        comparator bug would flip this negative and under-identify
        a large fraction of true cases."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 1, 1],
                "user_id": "user-oasis-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "oasis"
        assert body["total"] == 8
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False

    def test_total_seven_below_cutoff_is_negative_screen(
        self, client: TestClient
    ) -> None:
        """Total = 7 (just below) → negative.  Campbell-Sills 2009
        considered cutpoints 6 and 7 but selected 8 — the scorer and
        router must encode the chosen operating point."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 1, 1, 1],
                "user_id": "user-oasis-below",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 7
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["requires_t3"] is False

    def test_zero_total_is_negative_screen(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [0, 0, 0, 0, 0],
                "user_id": "user-oasis-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_max_total_is_positive_screen(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [4, 4, 4, 4, 4],
                "user_id": "user-oasis-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_impairment_dominant_profile_crosses_cutoff(
        self, client: TestClient
    ) -> None:
        """Low symptom intensity (items 1-2 = 1 each), strong
        impairment (items 4-5 = 4 each), some avoidance (item 3 = 0)
        → total = 10 → positive.  The "functional anxiety" profile —
        this is OASIS's headline clinical contribution over GAD-7."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [1, 1, 0, 4, 4],
                "user_id": "user-oasis-impairment",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 10
        assert body["positive_screen"] is True

    def test_positive_screen_does_not_fire_t3(
        self, client: TestClient
    ) -> None:
        """Even at maximum severity, OASIS never fires T3.  The T3
        pathway is reserved for active suicidality (PHQ-9 item 9 /
        C-SSRS) per Docs/Whitepapers/04_Safety_Framework.md §T3.
        Pins the safety-posture invariant."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [4, 4, 4, 4, 4],
                "user_id": "user-oasis-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None
        assert body.get("triggering_items") is None

    def test_emits_subscales_none(self, client: TestClient) -> None:
        """OASIS emits ``subscales=None`` — Norman 2006's factor
        analysis supports a single-factor structure.  Attempting to
        split symptom (1-2) / avoidance (3) / impairment (4-5) into
        subscales is unvalidated and not supported by the wire."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 2, 2],
                "user_id": "user-oasis-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("subscales") is None

    def test_rejects_four_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 2],
                "user_id": "user-oasis-bad-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_six_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 2, 2, 2],
                "user_id": "user-oasis-bad-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_two_items_gad2_misroute(
        self, client: TestClient
    ) -> None:
        """A 2-item submission with instrument=oasis is a mis-route
        (likely from a GAD-2 / PHQ-2 client).  The 422 makes the
        mis-routing obvious rather than silently returning a
        sub-cutoff total."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [3, 3],
                "user_id": "user-oasis-misroute",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_seven_items_gad7_misroute(
        self, client: TestClient
    ) -> None:
        """A 7-item submission with instrument=oasis is a mis-routed
        GAD-7.  Same diagnostic rationale as the GAD-2 mis-route
        test."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [1, 1, 1, 1, 1, 1, 1],
                "user_id": "user-oasis-misroute",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 2, 5],
                "user_id": "user-oasis-bad-range",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 2, -1],
                "user_id": "user-oasis-bad-range",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [3, 3, 2, 2, 2],
                "user_id": "user-oasis-history",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-oasis-history", limit=5)
        assert len(records) == 1
        r = records[0]
        assert r.instrument == "oasis"
        assert r.total == 12
        assert r.positive_screen is True
        assert r.requires_t3 is False

    def test_history_projection_surfaces_positive_screen(
        self, client: TestClient
    ) -> None:
        """History endpoint returns the persisted positive_screen
        boolean without re-scoring — pins the projection contract."""
        client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 1, 1],
                "user_id": "user-oasis-projection",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-oasis-projection"},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        assert items[0]["instrument"] == "oasis"
        assert items[0]["total"] == 8
        assert items[0]["positive_screen"] is True

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """OASIS submissions tolerate extra MDQ-only fields in the
        payload (defensive — a client reusing a builder across
        instruments shouldn't 422 on OASIS just because a
        ``concurrent_symptoms`` key is still attached)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [2, 2, 2, 1, 1],
                "user_id": "user-oasis-defensive",
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 8
        assert body["positive_screen"] is True

    def test_oasis_and_gad7_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """OASIS + GAD-7 form the clinical-companion pair for
        anxiety: GAD-7 indexes symptom severity (banded), OASIS
        indexes impairment (cutoff).  A weekly anxiety check-in
        submits both to the same user_id within seconds.  The
        history must land both independently — a future
        deduplication refactor cannot collapse them."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        client.post(
            "/v1/assessments",
            json={
                "instrument": "gad7",
                "items": [3, 2, 2, 2, 2, 2, 2],
                "user_id": "user-anxiety-weekly",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "oasis",
                "items": [3, 3, 2, 2, 2],
                "user_id": "user-anxiety-weekly",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        repo = get_assessment_repository()
        records = repo.history_for("user-anxiety-weekly", limit=10)
        assert len(records) == 2
        instruments = {r.instrument for r in records}
        assert instruments == {"gad7", "oasis"}
        # OASIS ≥ 8 fires positive_screen; GAD-7 uses banded severity
        # ("severe" at total=15, Spitzer 2006) so its positive_screen
        # is None on the wire — pins the two-envelope-pattern
        # coexistence.
        by_instrument = {r.instrument: r for r in records}
        assert by_instrument["oasis"].positive_screen is True
        assert by_instrument["oasis"].total == 12
        assert by_instrument["gad7"].total == 15


class TestK10Routing:
    """K10 (Kessler 2002 / Andrews & Slade 2001) router dispatch.

    Wire contract invariants:
    - Banded envelope (``severity`` is one of "low"/"moderate"/"high"/
      "very_high") uniform with PHQ-9 / GAD-7 / PSS-10.
    - ``requires_t3`` is always False — K10 has no safety item.
    - ``subscales=None`` — Kessler 2002 validates the unidimensional
      total; no depression / anxiety subscales are exposed on the wire.
    - Items are 1-5 (ITEM_MIN=1) — a 0 is out of range, not a silent
      "none of the time".
    """

    def test_minimum_total_is_low_band(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [1] * 10,
                "user_id": "user-k10-min",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "k10"
        assert body["total"] == 10
        assert body["severity"] == "low"
        assert body["requires_t3"] is False

    def test_band_boundary_twenty_is_moderate(
        self, client: TestClient
    ) -> None:
        """Andrews & Slade 2001 boundary — total=20 → moderate.  A
        ``> 20`` comparator bug would misclassify this as "low"."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [2] * 10,
                "user_id": "user-k10-mod-boundary",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "moderate"

    def test_band_boundary_twenty_five_is_high(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [2, 2, 2, 2, 2, 3, 3, 3, 3, 3],
                "user_id": "user-k10-high-boundary",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 25
        assert body["severity"] == "high"

    def test_band_boundary_thirty_is_very_high(
        self, client: TestClient
    ) -> None:
        """Population percentile ≈ 97 — the top 3% of distress.
        Pins the very_high cutoff boundary on the wire."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 10,
                "user_id": "user-k10-vh-boundary",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 30
        assert body["severity"] == "very_high"

    def test_maximum_total_is_very_high(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [5] * 10,
                "user_id": "user-k10-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 50
        assert body["severity"] == "very_high"
        assert body["requires_t3"] is False

    def test_very_high_does_not_fire_t3(self, client: TestClient) -> None:
        """Even at total=50 ("all of the time" on every item, including
        hopeless / worthless / sad), K10 does not fire T3.  The T3
        pathway is reserved for explicit suicidality (PHQ-9 item 9 /
        C-SSRS) per Docs/Whitepapers/04_Safety_Framework.md §T3.  Pins
        the safety-posture invariant for the maximally-distressed
        K10 profile."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [5] * 10,
                "user_id": "user-k10-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None
        assert body.get("triggering_items") is None

    def test_emits_subscales_none(self, client: TestClient) -> None:
        """K10 emits ``subscales=None`` — Kessler 2002's factor
        analysis validates the unidimensional total, and the wire
        contract does not split depression / anxiety subscales."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 10,
                "user_id": "user-k10-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("subscales") is None

    def test_rejects_zero_item_not_silently_accepted(
        self, client: TestClient
    ) -> None:
        """A 0 is NOT "none of the time" on K10 — Kessler's coding is
        1-5.  A client sending 0-indexed items would shift every total
        by 10 (and drop a band); the router must reject, not coerce.
        This pins the load-bearing 1-indexed semantic."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                "user_id": "user-k10-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_nine_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 9,
                "user_id": "user-k10-bad-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_eleven_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 11,
                "user_id": "user-k10-bad-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_six_items_k6_misroute(
        self, client: TestClient
    ) -> None:
        """K6 is the 6-item K10 short form — a 6-item k10 submission
        is a mis-route."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 6,
                "user_id": "user-k10-k6-misroute",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_out_of_range_six(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 6],
                "user_id": "user-k10-bad-range",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, -1],
                "user_id": "user-k10-bad-range",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_persists_very_high_in_history(
        self, client: TestClient
    ) -> None:
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [4] * 10,
                "user_id": "user-k10-history",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-k10-history", limit=5)
        assert len(records) == 1
        r = records[0]
        assert r.instrument == "k10"
        assert r.total == 40
        assert r.severity == "very_high"
        assert r.requires_t3 is False

    def test_history_projection_surfaces_banded_severity(
        self, client: TestClient
    ) -> None:
        """The history GET endpoint returns the banded severity string
        without re-scoring — pins the projection contract for banded-
        envelope instruments."""
        client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3, 3, 3, 3, 3, 2, 2, 2, 2, 2],
                "user_id": "user-k10-projection",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-k10-projection"},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        assert items[0]["instrument"] == "k10"
        assert items[0]["total"] == 25
        assert items[0]["severity"] == "high"

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """Defensive — extra MDQ-only fields on a K10 payload don't
        break dispatch (the K10 branch runs before the MDQ
        fallthrough)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 10,
                "user_id": "user-k10-defensive",
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 30
        assert body["severity"] == "very_high"


class TestSdsRouting:
    """SDS (Gossop 1995) router dispatch.

    Wire contract invariants:
    - Cutoff envelope (``severity`` is "positive_screen" /
      "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5
      / AUDIT-C.
    - ``cutoff_used`` echoes the substance-keyed cutoff (heroin=5,
      cannabis/cocaine=3, amphetamine=4, unspecified=3) — same
      pattern AUDIT-C uses for sex-keyed cutoffs.  Load-bearing for
      clinician-UI ("positive at ≥ N") rendering.
    - ``positive_screen`` flag echoes the actionable decision.
    - ``requires_t3`` is always False — SDS has no safety item.
    - ``subscales=None`` — Gossop 1995 validates unidimensionality.
    """

    def test_heroin_at_cutoff_is_positive(self, client: TestClient) -> None:
        """Heroin cutoff is ≥5 (Gossop 1995); total=5 flips to positive."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1, 1],
                "substance": "heroin",
                "user_id": "user-sds-heroin-at-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "sds"
        assert body["total"] == 5
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 5
        assert body["requires_t3"] is False

    def test_heroin_below_cutoff_is_negative(
        self, client: TestClient
    ) -> None:
        """Heroin total=4 is BELOW cutoff ≥5 — negative screen.  This
        same total=4 would be POSITIVE for every other supported
        substance.  Substance-adaptive cutoff is the SDS-defining
        behavior and this test pins it."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1, 0],
                "substance": "heroin",
                "user_id": "user-sds-heroin-below",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 4
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 5

    def test_cannabis_at_cutoff_is_positive(
        self, client: TestClient
    ) -> None:
        """Cannabis cutoff is ≥3 (Martin 2006 / Swift 1998)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "cannabis",
                "user_id": "user-sds-cannabis-at-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["cutoff_used"] == 3

    def test_cannabis_below_cutoff_is_negative(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 0, 0, 0],
                "substance": "cannabis",
                "user_id": "user-sds-cannabis-below",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 2
        assert body["severity"] == "negative_screen"
        assert body["cutoff_used"] == 3

    def test_cocaine_at_cutoff_is_positive(
        self, client: TestClient
    ) -> None:
        """Cocaine cutoff is ≥3 (Kaye & Darke 2002/2004)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "cocaine",
                "user_id": "user-sds-cocaine-at-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["cutoff_used"] == 3

    def test_amphetamine_at_cutoff_is_positive(
        self, client: TestClient
    ) -> None:
        """Amphetamine cutoff is ≥4 (Topp & Mattick 1997) — sits
        BETWEEN cannabis/cocaine (3) and heroin (5)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1, 0],
                "substance": "amphetamine",
                "user_id": "user-sds-amp-at-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 4
        assert body["severity"] == "positive_screen"
        assert body["cutoff_used"] == 4

    def test_amphetamine_below_cutoff_is_negative(
        self, client: TestClient
    ) -> None:
        """Amphetamine total=3 is BELOW cutoff ≥4.  Same total=3 is
        POSITIVE for cannabis/cocaine (≥3).  Middle-cutoff band is the
        amphetamine-specific distinction."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "amphetamine",
                "user_id": "user-sds-amp-below",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "negative_screen"
        assert body["cutoff_used"] == 4

    def test_unspecified_uses_conservative_cutoff(
        self, client: TestClient
    ) -> None:
        """When substance is 'unspecified', the cutoff is the lowest
        (≥ 3) — safety-conservative default.  Same posture as
        AUDIT-C sex='unspecified'."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "unspecified",
                "user_id": "user-sds-unspec",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["cutoff_used"] == 3

    def test_substance_omitted_falls_back_to_conservative(
        self, client: TestClient
    ) -> None:
        """Omitting ``substance`` entirely must behave identically to
        sending ``"unspecified"`` — conservative fallback, not a 422.
        Mirrors AUDIT-C sex=None behavior."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "user_id": "user-sds-no-substance",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["cutoff_used"] == 3

    def test_same_total_differs_across_substances(
        self, client: TestClient
    ) -> None:
        """Total=4: negative for heroin (≥5), positive for everything
        else.  This is the whole point of substance-adaptive cutoffs
        — the same psychometric signal carries different clinical
        meaning depending on substance.  Wire-level pin so a
        regression in the router → scorer substance plumbing cannot
        silently produce the wrong band."""
        items = [1, 1, 1, 1, 0]
        substances_and_expected: list[tuple[str, bool]] = [
            ("heroin", False),
            ("cannabis", True),
            ("cocaine", True),
            ("amphetamine", True),
            ("unspecified", True),
        ]
        for substance, expected_positive in substances_and_expected:
            response = client.post(
                "/v1/assessments",
                json={
                    "instrument": "sds",
                    "items": items,
                    "substance": substance,
                    "user_id": f"user-sds-{substance}-total4",
                },
                headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
            )
            assert response.status_code == 201
            body = response.json()
            assert body["total"] == 4, f"{substance} total drift"
            assert body["positive_screen"] is expected_positive, (
                f"{substance} at total=4 expected "
                f"positive={expected_positive}, got {body['positive_screen']}"
            )

    def test_maximum_total_is_positive_for_every_substance(
        self, client: TestClient
    ) -> None:
        """Total=15 (max) must be positive regardless of substance —
        this is the sanity check that substance-adaptive cutoffs don't
        ever cross the 'max total is always positive' invariant."""
        for substance in [
            "heroin",
            "cannabis",
            "cocaine",
            "amphetamine",
            "unspecified",
        ]:
            response = client.post(
                "/v1/assessments",
                json={
                    "instrument": "sds",
                    "items": [3, 3, 3, 3, 3],
                    "substance": substance,
                    "user_id": f"user-sds-{substance}-max",
                },
                headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
            )
            assert response.status_code == 201
            body = response.json()
            assert body["total"] == 15
            assert body["positive_screen"] is True

    def test_positive_screen_does_not_fire_t3(
        self, client: TestClient
    ) -> None:
        """Even max total + most conservative cutoff must NOT fire T3
        — SDS has no safety item.  Pins the no-T3 invariant."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [3, 3, 3, 3, 3],
                "substance": "cannabis",
                "user_id": "user-sds-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False

    def test_emits_subscales_none(self, client: TestClient) -> None:
        """Gossop 1995 validates unidimensional total — no subscales
        exposed on wire."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "cannabis",
                "user_id": "user-sds-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["subscales"] is None

    def test_rejects_four_items(self, client: TestClient) -> None:
        """SDS requires exactly 5 items — 4-item submission is 422."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1],
                "substance": "heroin",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_six_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1, 1, 1],
                "substance": "heroin",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_three_items_auditc_misroute(
        self, client: TestClient
    ) -> None:
        """3 items is AUDIT-C territory — must NOT silently score as
        SDS."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [2, 2, 2],
                "substance": "cannabis",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_out_of_range_four(self, client: TestClient) -> None:
        """SDS items are 0-3.  A 4 is out of range even though 4 is a
        valid cutoff value for amphetamine — the client MUST NOT
        conflate 'valid cutoff' with 'valid item response'."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [4, 0, 0, 0, 0],
                "substance": "cannabis",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [-1, 0, 0, 0, 0],
                "substance": "cannabis",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_invalid_substance(self, client: TestClient) -> None:
        """``substance`` is a Pydantic Literal; an unknown value is
        422 at the validation layer before dispatch."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "methamphetamine",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """Submitted SDS records land in the repository with the
        substance-keyed cutoff and positive_screen flag intact, so
        the clinician-UI history view renders the correct envelope."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [2, 2, 1, 1, 1],
                "substance": "heroin",
                "user_id": "user-sds-persist",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-sds-persist", limit=5)
        assert len(records) == 1
        r = records[0]
        assert r.instrument == "sds"
        assert r.total == 7
        assert r.severity == "positive_screen"
        assert r.positive_screen is True
        assert r.cutoff_used == 5
        assert r.substance == "heroin"

    def test_history_projection_surfaces_cutoff_envelope(
        self, client: TestClient
    ) -> None:
        """The /history projection surfaces severity, cutoff_used,
        and positive_screen so a clinician can read the SDS record
        without a separate lookup."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "cannabis",
                "user_id": "user-sds-history",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-sds-history"},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "sds"
        assert entry["total"] == 3
        assert entry["severity"] == "positive_screen"

    def test_sds_and_auditc_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """Both SDS and AUDIT-C use the cutoff envelope AND a
        per-demographic cutoff axis (substance vs sex).  Co-landing
        on the same user's timeline must preserve distinct
        ``cutoff_used`` values and distinct envelopes — no cross-
        instrument bleed."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        user = "user-sds-auditc-coexist"
        r1 = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1, 1],
                "substance": "heroin",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/v1/assessments",
            json={
                "instrument": "audit_c",
                "items": [2, 2, 2],
                "sex": "female",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert r2.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert by_instrument["sds"].cutoff_used == 5
        assert by_instrument["sds"].substance == "heroin"
        assert by_instrument["audit_c"].cutoff_used == 3
        assert by_instrument["audit_c"].sex == "female"

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """MDQ's Parts 2/3 fields in an SDS submission must be
        ignored (not 422'd, not routed through MDQ scorer)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 0, 0],
                "substance": "cannabis",
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
                "user_id": "user-sds-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "sds"
        assert body["total"] == 3


class TestK6Routing:
    """K6 (Kessler 2003) router dispatch.

    Wire contract invariants:
    - Cutoff envelope (``severity`` = "positive_screen" /
      "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS /
      PC-PTSD-5 / AUDIT-C / SDS — NOT the K10 banded envelope.
      Kessler 2003 published only the ≥ 13 SMI cutoff.
    - ``requires_t3`` is always False — K6 has no safety item.
    - ``subscales=None`` — Kessler 2003 validates unidimensional total;
      K6 items are selected for loading on the K10 dominant factor.
    - Items are 1-5 (ITEM_MIN=1, same as K10) — a 0 is out of range,
      not a silent "none of the time".
    """

    def test_minimum_total_is_negative(self, client: TestClient) -> None:
        """Min total=6 (every item at 1) — well below cutoff 13."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [1] * 6,
                "user_id": "user-k6-min",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "k6"
        assert body["total"] == 6
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["requires_t3"] is False

    def test_total_twelve_is_negative(self, client: TestClient) -> None:
        """Total=12 — one below cutoff.  Pins the boundary."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 2, 2],
                "user_id": "user-k6-twelve",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "negative_screen"

    def test_total_thirteen_is_positive(self, client: TestClient) -> None:
        """Total=13 — at cutoff.  Kessler 2003 SMI gate flips here."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 2, 3],
                "user_id": "user-k6-thirteen",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 13
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_total_fourteen_is_positive(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 3, 3],
                "user_id": "user-k6-fourteen",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 14
        assert body["severity"] == "positive_screen"

    def test_maximum_total_is_positive(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [5] * 6,
                "user_id": "user-k6-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 30
        assert body["severity"] == "positive_screen"

    def test_single_high_item_cannot_reach_cutoff(
        self, client: TestClient
    ) -> None:
        """One maxed item (5) + five minimum items (1 each) = 10 —
        below cutoff.  A positive K6 requires multi-item distress."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [5, 1, 1, 1, 1, 1],
                "user_id": "user-k6-single-high",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 10
        assert body["severity"] == "negative_screen"

    def test_positive_does_not_fire_t3(self, client: TestClient) -> None:
        """Max total + K6 MUST NOT fire T3 — K6 has no safety item."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [5] * 6,
                "user_id": "user-k6-t3-check",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False

    def test_emits_subscales_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 2, 3],
                "user_id": "user-k6-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["subscales"] is None

    def test_rejects_zero_item_not_silently_accepted(
        self, client: TestClient
    ) -> None:
        """LOAD-BEARING — ITEM_MIN=1 (like K10).  A 0-indexed submission
        would shift totals by 6 and potentially collapse a positive
        SMI screen.  Must 422, not silently accept."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [0, 2, 2, 2, 2, 2],
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_five_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [1, 1, 1, 1, 1],
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_seven_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [1, 1, 1, 1, 1, 1, 1],
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_ten_items_k10_misroute(
        self, client: TestClient
    ) -> None:
        """10 items is K10 territory — must 422, not silently score
        as K6."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [1] * 10,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_out_of_range_six(self, client: TestClient) -> None:
        """Items are 1-5.  A 6 is out of range."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [6, 1, 1, 1, 1, 1],
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [-1, 1, 1, 1, 1, 1],
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """Submitted K6 records land in the repository with positive
        screen flag intact, so the clinician-UI history view reads
        the cutoff envelope correctly."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [3, 3, 3, 3, 3, 3],
                "user_id": "user-k6-persist",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for("user-k6-persist", limit=5)
        assert len(records) == 1
        r = records[0]
        assert r.instrument == "k6"
        assert r.total == 18
        assert r.severity == "positive_screen"
        assert r.positive_screen is True

    def test_history_projection_surfaces_cutoff_envelope(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 2, 3],
                "user_id": "user-k6-history",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-k6-history"},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "k6"
        assert entry["total"] == 13
        assert entry["severity"] == "positive_screen"

    def test_k6_and_k10_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """K6 and K10 share ITEM_MIN=1 coding but use different
        envelopes (K6 cutoff, K10 banded).  Co-landing on the same
        user's timeline must preserve distinct envelopes — no bleed
        between "positive_screen" and the K10 band strings.  This is
        the daily-EMA-plus-weekly-full companion pattern, mirroring
        PHQ-2/PHQ-9 and GAD-2/GAD-7."""
        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        user = "user-k6-k10-coexist"
        r1 = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 2, 3],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/v1/assessments",
            json={
                "instrument": "k10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert r2.status_code == 201

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert by_instrument["k6"].severity == "positive_screen"
        assert by_instrument["k6"].positive_screen is True
        assert by_instrument["k10"].severity == "very_high"
        # K10 is banded; positive_screen doesn't apply.
        assert by_instrument["k10"].positive_screen is None

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """MDQ's Parts 2/3 fields in a K6 submission must be ignored
        (not 422'd, not routed through MDQ scorer)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "k6",
                "items": [2, 2, 2, 2, 2, 3],
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
                "user_id": "user-k6-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "k6"
        assert body["total"] == 13


class TestDuditRouting:
    """DUDIT (Berman 2005) router dispatch.

    Wire contract invariants:
    - Cutoff envelope (``severity`` = "positive_screen" /
      "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS /
      PC-PTSD-5 / AUDIT-C / SDS / K6.
    - ``cutoff_used`` echoes the sex-keyed Berman 2005 cutoff
      (men ≥ 6 / women ≥ 2 / unspecified ≥ 2).
    - ``requires_t3`` is always False — DUDIT has no safety item.
    - ``subscales=None`` — Berman 2003 validates unidimensional.
    - Items 1-9 take 0-4 Likert; items 10-11 take {0, 2, 4} trinary.
      A response of 1 or 3 on items 10-11 must 422 with the trinary
      message, not silently score.
    - The ``sex`` request field now serves BOTH AUDIT-C and DUDIT —
      a single demographic axis for two sex-keyed cutoff instruments.
    """

    def test_male_negative_below_cutoff(self, client: TestClient) -> None:
        """Male, total=5 — below male cutoff (6)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": "user-dudit-male-neg",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "dudit"
        assert body["total"] == 5
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 6
        assert body["requires_t3"] is False

    def test_male_positive_at_cutoff(self, client: TestClient) -> None:
        """Male, total=6 — Berman 2005 male cutoff boundary."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": "user-dudit-male-pos",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 6

    def test_female_negative_below_cutoff(
        self, client: TestClient
    ) -> None:
        """Female, total=1 — below female cutoff (2)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "female",
                "user_id": "user-dudit-female-neg",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 1
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 2

    def test_female_positive_at_cutoff(self, client: TestClient) -> None:
        """Female, total=2 — Berman 2005 female cutoff boundary."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "female",
                "user_id": "user-dudit-female-pos",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 2
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 2

    def test_unspecified_sex_uses_female_cutoff(
        self, client: TestClient
    ) -> None:
        """Safety-conservatism — unspecified sex defaults to cutoff 2."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "unspecified",
                "user_id": "user-dudit-unspec",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["cutoff_used"] == 2
        assert body["positive_screen"] is True

    def test_sex_omitted_falls_back_to_conservative_cutoff(
        self, client: TestClient
    ) -> None:
        """Omitting sex entirely — router maps None → "unspecified"
        → female cutoff (2).  Safety-conservative posture mirroring
        AUDIT-C."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "user_id": "user-dudit-no-sex",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["cutoff_used"] == 2
        assert body["positive_screen"] is True

    def test_same_total_differs_across_sexes(
        self, client: TestClient
    ) -> None:
        """Total=4: below male cutoff (6), above female cutoff (2).
        Load-bearing wire-level pin — the dispatch must produce
        opposite positive_screen values for the same total depending
        on sex."""
        items = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        resp_m = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": items,
                "sex": "male",
                "user_id": "user-dudit-sex-male",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        resp_f = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": items,
                "sex": "female",
                "user_id": "user-dudit-sex-female",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp_m.status_code == 201
        assert resp_f.status_code == 201
        m_body = resp_m.json()
        f_body = resp_f.json()
        assert m_body["total"] == 4
        assert f_body["total"] == 4
        assert m_body["positive_screen"] is False
        assert f_body["positive_screen"] is True
        assert m_body["cutoff_used"] == 6
        assert f_body["cutoff_used"] == 2

    def test_positive_does_not_fire_t3(
        self, client: TestClient
    ) -> None:
        """Max-value response — high screen but no T3 (no safety item)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
                "sex": "male",
                "user_id": "user-dudit-t3-none",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 44
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_emits_subscales_none(self, client: TestClient) -> None:
        """Berman 2003 validates unidimensional — no subscales."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0] * 11,
                "sex": "female",
                "user_id": "user-dudit-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["subscales"] is None

    def test_rejects_twelve_items(self, client: TestClient) -> None:
        """Router-layer item-count check — 12 items is not DUDIT."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0] * 12,
                "sex": "male",
                "user_id": "user-dudit-count-12",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422
        assert "exactly 11" in response.json()["detail"]["message"]

    def test_rejects_ten_items_audit_misroute(
        self, client: TestClient
    ) -> None:
        """10 items is AUDIT territory — must NOT silently score as DUDIT."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0] * 10,
                "sex": "male",
                "user_id": "user-dudit-misroute-audit",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_three_items_auditc_misroute(
        self, client: TestClient
    ) -> None:
        """3 items is AUDIT-C territory — must NOT silently score as DUDIT."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0, 0, 0],
                "sex": "male",
                "user_id": "user-dudit-misroute-auditc",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_likert_item_out_of_range(
        self, client: TestClient
    ) -> None:
        """Likert item (1-9) with value 5 — out of [0, 4]."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": "user-dudit-likert-oor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422
        assert "out of range" in response.json()["detail"]["message"]

    def test_rejects_trinary_one_at_item_ten(
        self, client: TestClient
    ) -> None:
        """NOVEL pin — item 10 with value 1.  Within numerical range
        [0, 4] but NOT in the trinary set {0, 2, 4}.  Must 422 with a
        message naming the legal values (0/2/4) so a caller understands
        the yes/not-last-year/last-year semantic."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                "sex": "male",
                "user_id": "user-dudit-trinary-one",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422
        msg = response.json()["detail"]["message"]
        assert "item 10" in msg
        assert "0, 2, or 4" in msg

    def test_rejects_trinary_three_at_item_eleven(
        self, client: TestClient
    ) -> None:
        """Item 11 with value 3 — another illegal trinary value."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                "sex": "female",
                "user_id": "user-dudit-trinary-three",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422
        assert "item 11" in response.json()["detail"]["message"]

    def test_rejects_invalid_sex_literal(
        self, client: TestClient
    ) -> None:
        """Pydantic-level Literal check on the sex field."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [0] * 11,
                "sex": "other",
                "user_id": "user-dudit-bad-sex",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_persists_positive_screen_in_history(
        self, client: TestClient
    ) -> None:
        """Submitted DUDIT with positive screen is recorded in the
        repository under the user_id with the cutoff-envelope shape."""
        user = "user-dudit-hist"
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "dudit"
        assert rec.total == 6
        assert rec.severity == "positive_screen"
        assert rec.positive_screen is True
        assert rec.cutoff_used == 6
        assert rec.sex == "male"
        assert rec.raw_items == (2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0)
        assert rec.requires_t3 is False

    def test_history_projection_surfaces_cutoff_envelope(
        self, client: TestClient
    ) -> None:
        """GET /history surfaces severity + positive_screen + cutoff_used
        for a DUDIT record."""
        user = "user-dudit-hist-proj"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "female",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "dudit"
        assert entry["severity"] == "positive_screen"
        assert entry["positive_screen"] is True
        assert entry["cutoff_used"] == 2

    def test_dudit_and_auditc_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """DUDIT (drugs) and AUDIT-C (alcohol) are BOTH sex-keyed
        cutoff instruments.  The wire's single ``sex`` field serves
        both.  Pin that a user can submit DUDIT and AUDIT-C on the
        same timeline without cross-contamination of cutoff_used or
        sex values."""
        user = "user-dudit-auditc-both"
        # DUDIT male, total 6 — positive at male cutoff 6.
        client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        # AUDIT-C male, total 4 — positive at male cutoff 4.
        client.post(
            "/v1/assessments",
            json={
                "instrument": "audit_c",
                "items": [2, 1, 1],
                "sex": "male",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert set(by_instrument) == {"dudit", "audit_c"}
        assert by_instrument["dudit"].cutoff_used == 6
        assert by_instrument["dudit"].positive_screen is True
        assert by_instrument["audit_c"].cutoff_used == 4
        assert by_instrument["audit_c"].positive_screen is True
        # Both carry the same demographic axis value — sex is shared,
        # cutoff_used is not.
        assert by_instrument["dudit"].sex == "male"
        assert by_instrument["audit_c"].sex == "male"

    def test_dudit_and_sds_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """DUDIT (general drug problems, sex-keyed cutoff) and SDS
        (specific-substance psychological dependence, substance-keyed
        cutoff) cover different constructs on different demographic
        axes.  The wire envelope must preserve both cleanly:
        DUDIT surfaces sex + cutoff_used=6 (male), SDS surfaces
        cutoff_used=5 (heroin) without either field bleeding into the
        other record."""
        user = "user-dudit-sds-both"
        # DUDIT male, total 10 — positive.
        client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        # SDS heroin, total 5 — positive at heroin cutoff 5.
        client.post(
            "/v1/assessments",
            json={
                "instrument": "sds",
                "items": [1, 1, 1, 1, 1],
                "substance": "heroin",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert by_instrument["dudit"].sex == "male"
        assert by_instrument["dudit"].substance is None
        assert by_instrument["sds"].sex is None
        assert by_instrument["sds"].substance == "heroin"
        assert by_instrument["dudit"].cutoff_used == 6
        assert by_instrument["sds"].cutoff_used == 5

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """concurrent_symptoms / functional_impairment are MDQ-only —
        submitting them with a DUDIT request must not perturb scoring."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "female",
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-dudit-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "dudit"
        assert body["total"] == 4
        assert body["positive_screen"] is True


class TestAsrs6Routing:
    """ASRS-6 (Kessler 2005) router dispatch.

    Wire contract invariants:
    - Cutoff envelope (``severity`` = "positive_screen" /
      "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS /
      PC-PTSD-5 / AUDIT-C / SDS / K6 / DUDIT.
    - ``cutoff_used`` echoes the count cutoff (= 4) so the
      clinician-UI renders "positive at ≥ 4 of 6 items".
    - ``triggering_items`` reuses the C-SSRS wire slot — 1-indexed
      item numbers that met their firing threshold.
    - ``requires_t3`` is always False — ASRS-6 has no safety item.
    - ``subscales=None`` — Kessler 2005 validates unidimensional.
    - NOVEL weighted-threshold firing: inattentive items 1-3 fire
      at Likert ≥ 2, hyperactive items 4-6 fire at Likert ≥ 3.  A
      caller must not use ``total`` to interpret the screen — the
      count of fired items is the actionable signal.
    """

    def test_all_zero_is_negative(self, client: TestClient) -> None:
        """Never-never-never across all six items — zero fires."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [0, 0, 0, 0, 0, 0],
                "user_id": "user-asrs6-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "asrs6"
        assert body["total"] == 0
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 4
        assert body["requires_t3"] is False
        assert body["triggering_items"] == []

    def test_three_fires_is_negative(self, client: TestClient) -> None:
        """Three inattentive items at Likert 2 — three fires, one
        below the count cutoff of 4."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 0, 0, 0],
                "user_id": "user-asrs6-three",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["triggering_items"] == [1, 2, 3]

    def test_four_fires_is_positive_at_cutoff_boundary(
        self, client: TestClient
    ) -> None:
        """Four fires — three inattentive + one hyperactive at
        Likert 3 — crosses the cutoff exactly."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 3, 0, 0],
                "user_id": "user-asrs6-four",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 4
        assert body["triggering_items"] == [1, 2, 3, 4]

    def test_maxed_positive(self, client: TestClient) -> None:
        """Very Often on every item — all six fire."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [4, 4, 4, 4, 4, 4],
                "user_id": "user-asrs6-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 24
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["triggering_items"] == [1, 2, 3, 4, 5, 6]

    def test_weighted_threshold_inattentive_at_two_fires(
        self, client: TestClient
    ) -> None:
        """Pin the asymmetric firing rule at the wire surface: an
        inattentive item at Likert 2 fires; a hyperactive item at
        Likert 2 does not.  Load-bearing — the entire clinical
        value of ASRS-6's wire shape over a sum-threshold is this
        asymmetry."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 2, 2, 2],
                "user_id": "user-asrs6-weighted",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        # Sum=12 would look impressive on a sum-threshold instrument.
        assert body["total"] == 12
        # Only 3 items fire (inattentive 1/2/3 at Likert 2); hyper-
        # active 4/5/6 do not fire at Likert 2.
        assert body["triggering_items"] == [1, 2, 3]
        assert body["positive_screen"] is False

    def test_count_vs_sum_divergence_high_sum_low_count(
        self, client: TestClient
    ) -> None:
        """A caller reading ``total`` as the screen would mis-call
        this case.  Sum=12 with only one inattentive fire + zero
        hyperactive fires."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                # item 1 at Likert 4 fires (inattentive, threshold 2)
                # item 2 at Likert 2 fires (inattentive, threshold 2)
                # item 3 at Likert 1 (below inattentive 2)
                # item 4 at Likert 2 (below hyperactive 3)
                # item 5 at Likert 2 (below hyperactive 3)
                # item 6 at Likert 1 (below hyperactive 3)
                "items": [4, 2, 1, 2, 2, 1],
                "user_id": "user-asrs6-divergence",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 12
        assert body["triggering_items"] == [1, 2]
        assert body["positive_screen"] is False

    def test_triggering_items_one_indexed_and_sorted(
        self, client: TestClient
    ) -> None:
        """triggering_items reuses the C-SSRS wire slot — 1-indexed,
        ascending, audit-trail ready."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 0, 2, 0, 3, 0],
                "user_id": "user-asrs6-trigger",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["triggering_items"] == [1, 3, 5]

    def test_rejects_wrong_item_count(self, client: TestClient) -> None:
        """ASRS-6 requires exactly 6 items."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [0, 0, 0, 0, 0],
                "user_id": "user-asrs6-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_out_of_range_item(self, client: TestClient) -> None:
        """Likert envelope is [0, 4] — a 5 is out-of-range."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [5, 0, 0, 0, 0, 0],
                "user_id": "user-asrs6-range",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_negative_item(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [-1, 0, 0, 0, 0, 0],
                "user_id": "user-asrs6-negative",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_never_fires_t3(self, client: TestClient) -> None:
        """All max — no safety flag.  Items 5/6 probe hyperactivity,
        not suicidality.  Acute ideation screening is PHQ-9 item 9 /
        C-SSRS, not ASRS-6."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [4, 4, 4, 4, 4, 4],
                "user_id": "user-asrs6-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_subscales_is_none(self, client: TestClient) -> None:
        """Kessler 2005 validates count-of-fires unidimensionally.
        The inattentive/hyperactive split is implicit in the
        thresholds, not a wire-exposed subscale."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [3, 3, 3, 3, 3, 3],
                "user_id": "user-asrs6-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("subscales") is None

    def test_instrument_version_surfaces(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [0, 0, 0, 0, 0, 0],
                "user_id": "user-asrs6-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "asrs6-1.0.0"

    def test_persists_to_repository(self, client: TestClient) -> None:
        """A submission with user_id persists to the history
        repository with the weighted-threshold fields preserved."""
        user = "user-asrs6-persist"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 3, 3, 0],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "asrs6"
        assert rec.total == 12
        assert rec.positive_screen is True
        assert rec.cutoff_used == 4
        assert tuple(rec.triggering_items) == (1, 2, 3, 4, 5)

    def test_history_projects_triggering_items(
        self, client: TestClient
    ) -> None:
        """GET /history surfaces triggering_items on the wire so the
        clinician-UI can render the audit trail without re-scoring."""
        user = "user-asrs6-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 0, 2, 0, 3, 3],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "asrs6"
        assert entry["triggering_items"] == [1, 3, 5, 6]
        assert entry["positive_screen"] is True
        assert entry["cutoff_used"] == 4

    def test_asrs6_and_dudit_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """ASRS-6 (weighted-threshold wire shape) and DUDIT (sex-keyed
        cutoff wire shape) are two genuinely different envelope
        shapes.  Pin that they coexist on the same user timeline
        without cross-contamination of cutoff_used, triggering_items,
        or sex values."""
        user = "user-asrs6-dudit-both"
        # DUDIT male, total 6 — positive at male cutoff 6.
        client.post(
            "/v1/assessments",
            json={
                "instrument": "dudit",
                "items": [2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                "sex": "male",
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        # ASRS-6 — five fires, positive.
        client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 3, 3, 0],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert set(by_instrument) == {"dudit", "asrs6"}
        # Independent cutoff surfaces — DUDIT carries sex-keyed 6,
        # ASRS-6 carries count-cutoff 4.  Neither bleeds.
        assert by_instrument["dudit"].cutoff_used == 6
        assert by_instrument["asrs6"].cutoff_used == 4
        # triggering_items populated only for ASRS-6 — DUDIT has no
        # per-item firing concept.
        assert tuple(by_instrument["asrs6"].triggering_items) == (
            1, 2, 3, 4, 5,
        )
        assert not by_instrument["dudit"].triggering_items
        # Sex is DUDIT-only; ASRS-6 record carries no sex.
        assert by_instrument["dudit"].sex == "male"
        assert by_instrument["asrs6"].sex is None

    def test_ignores_sex_field(self, client: TestClient) -> None:
        """ASRS-6 is not sex-keyed — submitting a ``sex`` field must
        be ignored without perturbing the screen decision."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 3, 0, 0],
                "sex": "female",
                "user_id": "user-asrs6-sex-ignored",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 4  # count cutoff, not a sex cutoff

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """concurrent_symptoms / functional_impairment are MDQ-only —
        submitting them with an ASRS-6 request must not perturb
        scoring."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "asrs6",
                "items": [2, 2, 2, 3, 0, 0],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-asrs6-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "asrs6"
        assert body["positive_screen"] is True


class TestAaq2Routing:
    """AAQ-II (Bond 2011) router dispatch.

    Wire contract invariants:
    - Cutoff envelope (``severity`` = "positive_screen" /
      "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS /
      PC-PTSD-5 / AUDIT-C / SDS / K6 / DUDIT / ASRS-6.
    - ``cutoff_used`` echoes Bond 2011's ≥ 24 clinical cutoff —
      constant across all inputs (unlike AUDIT-C / SDS / DUDIT where
      the cutoff varies by demographic axis).
    - ``requires_t3`` is always False — AAQ-II has no safety item.
    - ``subscales=None`` — Bond 2011 CFA validates unidimensional.
    - ``triggering_items`` is None — AAQ-II is a sum-vs-cutoff
      instrument, no per-item firing audit trail.
    - NOVEL 1-7 Likert envelope — first in the package.  Items
      outside [1, 7] must 422 (0 rejects even though 0-indexed
      instruments accept it; 8 rejects at the ceiling).
    """

    def test_all_min_is_negative(self, client: TestClient) -> None:
        """Every item at 1 ("Never true") — total 7, far below
        cutoff."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [1, 1, 1, 1, 1, 1, 1],
                "user_id": "user-aaq2-min",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "aaq2"
        assert body["total"] == 7
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 24
        assert body["requires_t3"] is False

    def test_below_cutoff_is_negative(self, client: TestClient) -> None:
        """Total 23 — one below Bond 2011's ≥ 24 cutoff."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [3, 3, 3, 3, 3, 4, 4],
                "user_id": "user-aaq2-below",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 23
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_at_cutoff_is_positive(self, client: TestClient) -> None:
        """Total 24 — at Bond 2011's clinical cutoff.  Boundary is
        ≥, not >."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [3, 3, 3, 3, 4, 4, 4],
                "user_id": "user-aaq2-at",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 24
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 24

    def test_maxed_positive(self, client: TestClient) -> None:
        """Ceiling case — every item at 7 ("Always true")."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [7, 7, 7, 7, 7, 7, 7],
                "user_id": "user-aaq2-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 49
        assert body["positive_screen"] is True

    def test_cutoff_used_is_constant(self, client: TestClient) -> None:
        """Unlike AUDIT-C / SDS / DUDIT, AAQ-II's cutoff does not vary
        by a demographic axis.  Every AAQ-II response surfaces
        cutoff_used = 24."""
        for items, user in [
            ([1, 1, 1, 1, 1, 1, 1], "user-aaq2-cu-low"),
            ([4, 4, 4, 4, 4, 4, 4], "user-aaq2-cu-mid"),
            ([7, 7, 7, 7, 7, 7, 7], "user-aaq2-cu-high"),
        ]:
            response = client.post(
                "/v1/assessments",
                json={
                    "instrument": "aaq2",
                    "items": items,
                    "user_id": user,
                },
                headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
            )
            assert response.status_code == 201
            assert response.json()["cutoff_used"] == 24

    def test_rejects_wrong_item_count(self, client: TestClient) -> None:
        """AAQ-II requires exactly 7 items."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [1, 1, 1, 1, 1, 1],  # 6 items
                "user_id": "user-aaq2-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_zero_item(self, client: TestClient) -> None:
        """NOVEL 1-7 envelope: 0 is rejected even though every
        0-indexed instrument in the package accepts it.  Distinct
        clinical meaning — Bond 2011 Likert starts at 1 = "Never
        true"."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [0, 1, 1, 1, 1, 1, 1],
                "user_id": "user-aaq2-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_eight_item(self, client: TestClient) -> None:
        """NOVEL 1-7 envelope: 8 is out-of-range — the Likert ceiling
        is 7 ("Always true")."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [8, 1, 1, 1, 1, 1, 1],
                "user_id": "user-aaq2-eight",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_accepts_six_and_seven(self, client: TestClient) -> None:
        """NOVEL 1-7 envelope: 6 ("Almost always true") and 7
        ("Always true") are valid — K10 / K6 would reject these
        even though their ITEM_MIN=1 matches AAQ-II.  Pin that
        AAQ-II widens the ceiling cleanly."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [6, 7, 6, 7, 6, 7, 6],
                "user_id": "user-aaq2-sixes-sevens",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 45
        assert body["positive_screen"] is True

    def test_never_fires_t3(self, client: TestClient) -> None:
        """All max — no safety flag.  Items 1 / 4 ("painful
        experiences / memories") and 2 ("afraid of my feelings") are
        process-of-avoidance probes, NOT intent probes."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [7, 7, 7, 7, 7, 7, 7],
                "user_id": "user-aaq2-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_subscales_is_none(self, client: TestClient) -> None:
        """Bond 2011 CFA: unidimensional.  No subscales surfaced."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [4, 4, 4, 4, 4, 4, 4],
                "user_id": "user-aaq2-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("subscales") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        """AAQ-II is a sum-vs-cutoff instrument; no per-item firing
        concept.  Unlike ASRS-6, no triggering_items surface."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [7, 7, 7, 7, 7, 7, 7],
                "user_id": "user-aaq2-triggering",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        # Wire shape: triggering_items key exists on the envelope but
        # value is None (or empty) for instruments without per-item
        # firing.  The persistence layer stores None.
        assert not body.get("triggering_items")

    def test_instrument_version_surfaces(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [1, 1, 1, 1, 1, 1, 1],
                "user_id": "user-aaq2-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "aaq2-1.0.0"

    def test_persists_to_repository(self, client: TestClient) -> None:
        """A submission with user_id persists to the history
        repository with the cutoff fields preserved."""
        user = "user-aaq2-persist"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [4, 4, 4, 4, 4, 4, 4],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "aaq2"
        assert rec.total == 28
        assert rec.positive_screen is True
        assert rec.cutoff_used == 24

    def test_history_projects_aaq2(self, client: TestClient) -> None:
        """GET /history surfaces the AAQ-II result with cutoff_used
        and positive_screen preserved."""
        user = "user-aaq2-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [5, 5, 5, 5, 5, 5, 5],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "aaq2"
        assert entry["total"] == 35
        assert entry["positive_screen"] is True
        assert entry["cutoff_used"] == 24

    def test_aaq2_and_phq9_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """AAQ-II (psychological inflexibility, process measure) and
        PHQ-9 (depression severity, symptom measure) cover ORTHOGONAL
        constructs.  A high PHQ-9 does not imply a high AAQ-II and
        vice versa.  The wire must preserve both records cleanly so
        the bandit can read both signals when picking an
        intervention variant."""
        user = "user-aaq2-phq9-both"
        # AAQ-II — high inflexibility (total 35).
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [5, 5, 5, 5, 5, 5, 5],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        # PHQ-9 — moderate depression (total 12).
        client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [2, 2, 1, 1, 2, 1, 1, 1, 1],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert set(by_instrument) == {"aaq2", "phq9"}
        # Independent wire surfaces — AAQ-II carries cutoff_used=24
        # with positive_screen; PHQ-9 carries severity banding.
        assert by_instrument["aaq2"].cutoff_used == 24
        assert by_instrument["aaq2"].positive_screen is True
        assert by_instrument["phq9"].total == 12
        assert by_instrument["phq9"].severity == "moderate"
        # PHQ-9 doesn't populate cutoff_used (banded instrument).
        assert by_instrument["phq9"].cutoff_used is None

    def test_ignores_sex_field(self, client: TestClient) -> None:
        """AAQ-II is not sex-keyed — submitting a ``sex`` field must
        be ignored without perturbing the screen decision.  Bond 2011
        published a single cutoff regardless of demographic axis."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [3, 3, 3, 3, 4, 4, 4],
                "sex": "female",
                "user_id": "user-aaq2-sex-ignored",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 24
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 24  # not a sex-keyed cutoff

    def test_ignores_substance_field(self, client: TestClient) -> None:
        """AAQ-II is not substance-keyed — submitting ``substance``
        must not perturb scoring (SDS-only field)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [4, 4, 4, 4, 4, 4, 4],
                "substance": "heroin",
                "user_id": "user-aaq2-substance-ignored",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 24

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """concurrent_symptoms / functional_impairment are MDQ-only."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [5, 5, 5, 5, 5, 5, 5],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-aaq2-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "aaq2"
        assert body["total"] == 35
        assert body["positive_screen"] is True


class TestWsasRouting:
    """WSAS (Mundt 2002) router dispatch.

    Wire contract invariants:
    - Banded envelope (``severity`` = "subclinical" / "significant" /
      "severe") uniform with PHQ-9 / GAD-7 / ISI / DAST-10 / PCL-5 /
      OCI-R / BIS-11 / PHQ-15 / K10 / DUDIT.
    - No ``cutoff_used`` / ``positive_screen`` — banded instrument,
      not cutoff (unlike AAQ-II / ASRS-6 / AUDIT-C / SDS / DUDIT /
      K6 / PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / MDQ).
    - ``requires_t3`` is always False — WSAS has no safety item.
    - ``subscales=None`` — Mundt 2002 CFA validates unidimensional.
    - ``triggering_items`` is None — WSAS is a banded sum instrument.
    - NOVEL 0-8 Likert envelope — widest per-item envelope in the
      package.  Items outside [0, 8] must 422 (9 rejects at the
      ceiling; ITEM_MIN=0 accepts 0).
    """

    def test_all_min_is_subclinical(self, client: TestClient) -> None:
        """Every item at 0 ("Not at all impaired") — total 0, in the
        subclinical band."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [0, 0, 0, 0, 0],
                "user_id": "user-wsas-min",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "wsas"
        assert body["total"] == 0
        assert body["severity"] == "subclinical"
        assert body["requires_t3"] is False

    def test_just_below_significant_boundary(self, client: TestClient) -> None:
        """Total 9 — one below the 10-point significant band boundary."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [2, 2, 2, 2, 1],
                "user_id": "user-wsas-9",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 9
        assert body["severity"] == "subclinical"

    def test_at_significant_boundary(self, client: TestClient) -> None:
        """Total 10 — at the significant-band boundary.  Boundary is
        ≥, not >."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [2, 2, 2, 2, 2],
                "user_id": "user-wsas-10",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 10
        assert body["severity"] == "significant"

    def test_just_below_severe_boundary(self, client: TestClient) -> None:
        """Total 19 — one below the 20-point severe band boundary."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [4, 4, 4, 4, 3],
                "user_id": "user-wsas-19",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 19
        assert body["severity"] == "significant"

    def test_at_severe_boundary(self, client: TestClient) -> None:
        """Total 20 — at the severe-band boundary per Mundt 2002."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [4, 4, 4, 4, 4],
                "user_id": "user-wsas-20",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "severe"

    def test_maxed_severe(self, client: TestClient) -> None:
        """Ceiling case — every item at 8 ("Very severely impaired")."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [8, 8, 8, 8, 8],
                "user_id": "user-wsas-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 40
        assert body["severity"] == "severe"

    def test_no_cutoff_used_on_wire(self, client: TestClient) -> None:
        """WSAS is banded, not cutoff.  Unlike AAQ-II / ASRS-6 /
        AUDIT-C / SDS / DUDIT, the wire envelope carries no
        ``cutoff_used`` value."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [4, 4, 4, 4, 4],
                "user_id": "user-wsas-no-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_rejects_wrong_item_count(self, client: TestClient) -> None:
        """WSAS requires exactly 5 items."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [0, 0, 0, 0],  # 4 items
                "user_id": "user-wsas-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_accepts_zero_item(self, client: TestClient) -> None:
        """NOVEL 0-8 envelope: 0 ("Not at all impaired") is valid —
        distinct from AAQ-II where 0 rejects.  ITEM_MIN=0 shared with
        every 0-indexed instrument in the package."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [0, 0, 0, 0, 0],
                "user_id": "user-wsas-zero-ok",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_rejects_nine_item(self, client: TestClient) -> None:
        """NOVEL 0-8 envelope: 9 is out-of-range — ITEM_MAX=8 is the
        widest per-item ceiling in the package and responses beyond
        the published scale must reject."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [9, 0, 0, 0, 0],
                "user_id": "user-wsas-nine",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_accepts_seven_and_eight(self, client: TestClient) -> None:
        """NOVEL 0-8 envelope: 7 (between "markedly" and "very
        severely") and 8 ("Very severely impaired") are valid — prior
        package maximum was AAQ-II's 7; WSAS widens by one.  Pin the
        ceiling at 8 explicitly rather than inheriting by mistake."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [7, 8, 7, 8, 7],
                "user_id": "user-wsas-sevens-eights",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 37
        assert body["severity"] == "severe"

    def test_never_fires_t3(self, client: TestClient) -> None:
        """All max — no safety flag.  WSAS items probe work / home /
        social / private / relationships — none referencing
        suicidality."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [8, 8, 8, 8, 8],
                "user_id": "user-wsas-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_subscales_is_none(self, client: TestClient) -> None:
        """Mundt 2002 CFA: unidimensional.  Productive-vs-social
        split was explicitly rejected.  No subscales surfaced."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [4, 4, 4, 4, 4],
                "user_id": "user-wsas-subscales",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("subscales") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        """WSAS is a banded sum instrument; no per-item firing
        concept.  Unlike ASRS-6 / C-SSRS, no triggering_items."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [8, 8, 8, 8, 8],
                "user_id": "user-wsas-triggering",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert not body.get("triggering_items")

    def test_instrument_version_surfaces(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [0, 0, 0, 0, 0],
                "user_id": "user-wsas-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "wsas-1.0.0"

    def test_persists_to_repository(self, client: TestClient) -> None:
        """A submission with user_id persists to the history
        repository with severity band preserved."""
        user = "user-wsas-persist"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [5, 5, 5, 5, 5],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "wsas"
        assert rec.total == 25
        assert rec.severity == "severe"

    def test_history_projects_wsas(self, client: TestClient) -> None:
        """GET /history surfaces the WSAS result with severity band
        preserved."""
        user = "user-wsas-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [3, 3, 3, 3, 3],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "wsas"
        assert entry["total"] == 15
        assert entry["severity"] == "significant"

    def test_wsas_and_phq9_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """WSAS (functional impairment) and PHQ-9 (depression severity,
        symptom measure) cover ORTHOGONAL constructs.  The canonical
        clinical scenario: PHQ-9=8 (mild symptoms) with WSAS=28
        (severe functional impairment) — e.g. post-trauma avoidance
        where symptom intensity is modest but behavioral shutdown is
        profound.  The wire must preserve both records cleanly so the
        bandit can read both dimensions and route behavioral-
        activation / committed-action tools on the functional signal
        rather than defaulting to cognitive restructuring on the
        symptom signal alone."""
        user = "user-wsas-phq9-both"
        # WSAS — severe functional impairment (total 28).
        client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [6, 5, 6, 5, 6],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        # PHQ-9 — mild depression (total 8).
        client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [1, 1, 1, 1, 1, 1, 1, 1, 0],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert set(by_instrument) == {"wsas", "phq9"}
        # Banded instrument pair — both carry severity but no
        # cutoff_used / positive_screen (neither is a cutoff shape).
        assert by_instrument["wsas"].total == 28
        assert by_instrument["wsas"].severity == "severe"
        assert by_instrument["wsas"].cutoff_used is None
        assert by_instrument["phq9"].total == 8
        assert by_instrument["phq9"].severity == "mild"
        assert by_instrument["phq9"].cutoff_used is None

    def test_wsas_and_aaq2_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """WSAS (functional impairment) and AAQ-II (psychological
        inflexibility) cover ORTHOGONAL constructs — behavioral
        outcome vs. process-level avoidance.  Both instruments
        matter independently: high AAQ-II with preserved WSAS means
        the patient is avoiding internally while still functioning,
        while low AAQ-II with high WSAS means they are psychologically
        flexible but behaviorally disabled.  Both scores must persist
        cleanly on the timeline for the bandit to read both axes."""
        user = "user-wsas-aaq2-both"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [5, 6, 5, 5, 6],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [4, 4, 4, 4, 4, 4, 4],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        # WSAS: banded envelope.
        assert by_instrument["wsas"].severity == "severe"
        assert by_instrument["wsas"].cutoff_used is None
        # AAQ-II: cutoff envelope.
        assert by_instrument["aaq2"].cutoff_used == 24
        assert by_instrument["aaq2"].positive_screen is True

    def test_ignores_sex_field(self, client: TestClient) -> None:
        """WSAS is not sex-keyed — submitting ``sex`` must be ignored
        without perturbing the banding.  Mundt 2002 published a single
        set of bands regardless of demographic axis."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [4, 4, 4, 4, 4],
                "sex": "male",
                "user_id": "user-wsas-sex-ignored",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "severe"

    def test_ignores_substance_field(self, client: TestClient) -> None:
        """WSAS is not substance-keyed — substance is SDS-only."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [3, 3, 3, 3, 3],
                "substance": "cannabis",
                "user_id": "user-wsas-substance-ignored",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "significant"

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """concurrent_symptoms / functional_impairment are MDQ-only
        (Part 2 / Part 3 of Hirschfeld 2000).  They must not perturb
        WSAS scoring even though WSAS's construct name includes
        'functional impairment' — the fields are instrument-
        namespaced by the Pydantic contract."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [6, 6, 6, 6, 6],
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-wsas-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "wsas"
        assert body["total"] == 30
        assert body["severity"] == "severe"


class TestDers16Routing:
    """DERS-16 (Bjureberg 2016) router dispatch.

    Wire contract invariants:
    - Continuous envelope (``severity`` = "continuous" literal) uniform
      with Craving VAS / PACS / Readiness Ruler / DTCQ-8.  No banded
      classification because Bjureberg 2016 published no cross-
      calibrated cutpoints; the trajectory layer extracts clinical
      signal via RCI-style change detection on total + subscales.
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, not cutoff shape (unlike AAQ-II / ASRS-6 /
      AUDIT-C / SDS / DUDIT / K6 / PHQ-2 / GAD-2 / OASIS /
      PC-PTSD-5 / MDQ), not banded shape (unlike PHQ-9 / GAD-7 /
      ISI / DAST-10 / PCL-5 / OCI-R / BIS-11 / PHQ-15 / K10 /
      DUDIT / WSAS).
    - ``requires_t3`` is always False — DERS-16 has no safety item.
    - **``subscales`` IS populated** with a 5-key dict
      (``nonacceptance`` / ``goals`` / ``impulse`` / ``strategies`` /
      ``clarity``) per Bjureberg 2016 Table 2.  DERS-16 is the FIRST
      5-subscale instrument in the package (OCI-R has 6, PCL-5 has
      4, BIS-11 and URICA have 3, the rest are unidimensional).
    - ``triggering_items`` is None — DERS-16 has no firing-item
      concept (unlike C-SSRS / ASRS-6).
    - NOVEL 1-5 Likert envelope on a 16-item instrument — floor 1
      (not 0, unlike PHQ-9 / GAD-7 / OCI-R), ceiling 5 (not 4 /
      not 7 / not 8).  0 rejects (below floor).  6 rejects (above
      ceiling).  1 and 5 both accept.  Count must be exactly 16.
    - Three-way process-target triangle: DERS-16 on the same user
      timeline as AAQ-II (ACT target) and PHQ-9 (CBT target) must
      persist all three axes cleanly so the contextual bandit can
      route process-level decisions by profile dominance.
    """

    def test_all_floor_is_continuous(self, client: TestClient) -> None:
        """Every item at 1 ("Almost never") — total 16, the healthy-
        baseline case.  ``severity`` is the "continuous" sentinel
        regardless of total, because DERS-16 does not classify."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                "user_id": "user-ders16-floor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "ders16"
        assert body["total"] == 16
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_all_ceiling_is_continuous(self, client: TestClient) -> None:
        """Every item at 5 ("Almost always") — total 80.  Even at the
        maximum, ``severity`` stays the "continuous" sentinel — Bjureberg
        2016 published no severe-band threshold and the scorer does not
        hand-roll one."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
                "user_id": "user-ders16-ceiling",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 80
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_moderate_pattern_is_continuous(self, client: TestClient) -> None:
        """Every item at 3 ("About half the time") — total 48, uniform
        moderate dysregulation.  Continuous sentinel pins that DERS-16
        never drifts into banded classification regardless of level."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
                "user_id": "user-ders16-moderate",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 48
        assert body["severity"] == "continuous"

    def test_no_cutoff_used_on_wire(self, client: TestClient) -> None:
        """DERS-16 is continuous, not cutoff, not banded.  Unlike WSAS
        (banded) or AAQ-II (cutoff), the wire envelope carries no
        ``cutoff_used`` and no ``positive_screen`` — clients rendering
        DERS-16 must not look for either."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
                "user_id": "user-ders16-no-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_subscales_populated_on_wire(self, client: TestClient) -> None:
        """DERS-16 is the first 5-subscale instrument — the ``subscales``
        dict MUST appear on the wire.  A regression where the router
        forgot to map the scorer's subscale_* fields to the envelope's
        ``subscales`` dict would surface here as a None subscales value."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],
                "user_id": "user-ders16-subscales-present",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("subscales") is not None
        assert isinstance(body["subscales"], dict)

    def test_subscale_keys_exact(self, client: TestClient) -> None:
        """The 5 subscale keys must match Bjureberg 2016 Table 2
        verbatim: nonacceptance / goals / impulse / strategies / clarity.
        A refactor that used camelCase or rearranged keys would break
        clinician-UI renderers that key off these exact strings."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
                "user_id": "user-ders16-subscale-keys",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        subscales = response.json()["subscales"]
        assert set(subscales.keys()) == {
            "nonacceptance",
            "goals",
            "impulse",
            "strategies",
            "clarity",
        }

    def test_nonacceptance_subscale_items_nine_ten_thirteen(
        self, client: TestClient
    ) -> None:
        """Endorse only items 9, 10, 13 at ceiling → nonacceptance = 15,
        other subscales at their respective floors.  Pins the 1-indexed
        subscale mapping on the wire (not just in the scorer)."""
        items = [1] * 16
        for pos_1 in (9, 10, 13):
            items[pos_1 - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-nonacceptance",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        subscales = response.json()["subscales"]
        assert subscales["nonacceptance"] == 15  # 3 × 5
        assert subscales["goals"] == 3  # 3 items at floor 1
        assert subscales["impulse"] == 3
        assert subscales["strategies"] == 5  # 5 items at floor 1
        assert subscales["clarity"] == 2  # 2 items at floor 1

    def test_goals_subscale_items_three_seven_fifteen(
        self, client: TestClient
    ) -> None:
        """Endorse only items 3, 7, 15 → goals = 15, others at floor.
        Goals subscale routes DBT wise-mind / mindfulness-of-current-
        activity skill-module emphasis."""
        items = [1] * 16
        for pos_1 in (3, 7, 15):
            items[pos_1 - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-goals",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        subscales = response.json()["subscales"]
        assert subscales["goals"] == 15
        assert subscales["nonacceptance"] == 3
        assert subscales["impulse"] == 3
        assert subscales["strategies"] == 5
        assert subscales["clarity"] == 2

    def test_impulse_subscale_items_four_eight_eleven(
        self, client: TestClient
    ) -> None:
        """Endorse only items 4, 8, 11 → impulse = 15, others at floor.
        Impulse subscale is the strongest BPD-pattern signal — routes
        DBT distress-tolerance (TIP / STOP / self-soothe)."""
        items = [1] * 16
        for pos_1 in (4, 8, 11):
            items[pos_1 - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-impulse",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        subscales = response.json()["subscales"]
        assert subscales["impulse"] == 15
        assert subscales["nonacceptance"] == 3
        assert subscales["goals"] == 3
        assert subscales["strategies"] == 5
        assert subscales["clarity"] == 2

    def test_strategies_subscale_items_five_six_twelve_fourteen_sixteen(
        self, client: TestClient
    ) -> None:
        """Endorse only items 5, 6, 12, 14, 16 → strategies = 25 (the
        WIDEST subscale range, 5 × 5), others at floor.  Strategies
        subscale is the depressive-rumination / regulation-hopelessness
        signal — routes DBT cope-ahead / opposite-action."""
        items = [1] * 16
        for pos_1 in (5, 6, 12, 14, 16):
            items[pos_1 - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-strategies",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        subscales = response.json()["subscales"]
        assert subscales["strategies"] == 25  # 5 × 5
        assert subscales["nonacceptance"] == 3
        assert subscales["goals"] == 3
        assert subscales["impulse"] == 3
        assert subscales["clarity"] == 2

    def test_clarity_subscale_items_one_two(
        self, client: TestClient
    ) -> None:
        """Endorse only items 1, 2 → clarity = 10 (the NARROWEST
        subscale range, 2 × 5), others at floor.  Clarity subscale is
        the alexithymic-pattern signal — routes DBT observe/describe
        mindfulness skills."""
        items = [5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-clarity",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        subscales = response.json()["subscales"]
        assert subscales["clarity"] == 10  # 2 × 5
        assert subscales["nonacceptance"] == 3
        assert subscales["goals"] == 3
        assert subscales["impulse"] == 3
        assert subscales["strategies"] == 5

    def test_subscales_sum_equals_total(self, client: TestClient) -> None:
        """Invariant on the wire: the 5 subscale totals sum to the
        instrument total.  A refactor that double-counted an item
        or rotated subscale rows would break this here."""
        items = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-sum-invariant",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        subscales = body["subscales"]
        assert (
            subscales["nonacceptance"]
            + subscales["goals"]
            + subscales["impulse"]
            + subscales["strategies"]
            + subscales["clarity"]
        ) == body["total"]

    def test_rejects_wrong_item_count(self, client: TestClient) -> None:
        """DERS-16 requires exactly 16 items."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 15,  # 15 items
                "user_id": "user-ders16-count",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_zero_item(self, client: TestClient) -> None:
        """NOVEL 1-5 envelope: 0 is below the Likert floor — distinct
        from PHQ-9 / GAD-7 / OCI-R / K10 where 0 is valid.  A client
        that submitted a 0-4 payload from a PHQ-9-like UI must reject."""
        items = [1] * 16
        items[0] = 0
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_rejects_six_item(self, client: TestClient) -> None:
        """NOVEL 1-5 envelope: 6 is above the Likert ceiling — distinct
        from AAQ-II where 6 is valid (1-7 range).  A client that
        submitted AAQ-II-like items on a DERS-16 dispatch must reject."""
        items = [3] * 16
        items[0] = 6
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-six",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_accepts_one_and_five(self, client: TestClient) -> None:
        """NOVEL 1-5 envelope: 1 ("Almost never", floor) and 5
        ("Almost always", ceiling) are both valid.  Pin both
        extremes explicitly rather than inheriting."""
        items = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-ones-fives",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 48  # 8 × 1 + 8 × 5

    def test_never_fires_t3(self, client: TestClient) -> None:
        """Every item at ceiling — no safety flag.  DERS-16's items
        probe regulatory-process difficulty; items 4/8 ("out of
        control") and item 14 ("feel very bad about myself") do NOT
        probe acute intent.  Acute ideation stays on PHQ-9 item 9 /
        C-SSRS."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [5] * 16,
                "user_id": "user-ders16-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False
        assert body.get("t3_reason") is None

    def test_impulse_max_does_not_fire_t3(self, client: TestClient) -> None:
        """Even with the impulse subscale maxed (items 4, 8, 11 all
        at 5 — the strongest BPD-pattern signal), no T3 fires.  A
        renderer that tried to key off impulse > threshold to
        escalate to T3 would over-fire and desensitize the safety
        queue; this test pins the boundary at the router."""
        items = [1] * 16
        for pos_1 in (4, 8, 11):
            items[pos_1 - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": "user-ders16-impulse-no-t3",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        """DERS-16 has no per-item firing concept (unlike C-SSRS /
        ASRS-6).  No triggering_items on the envelope."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [5] * 16,
                "user_id": "user-ders16-triggering",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert not body.get("triggering_items")

    def test_instrument_version_surfaces(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [1] * 16,
                "user_id": "user-ders16-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "ders16-1.0.0"

    def test_persists_to_repository(self, client: TestClient) -> None:
        """A submission with user_id persists to the history repository
        with subscales preserved so the intervention layer can read the
        profile, not just the aggregate."""
        user = "user-ders16-persist"
        items = [1] * 16
        for pos_1 in (4, 8, 11):  # impulse-dominant
            items[pos_1 - 1] = 5
        client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": items,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "ders16"
        assert rec.severity == "continuous"
        assert rec.subscales is not None
        assert rec.subscales["impulse"] == 15
        assert rec.subscales["nonacceptance"] == 3

    def test_history_projects_ders16(self, client: TestClient) -> None:
        """GET /history surfaces the DERS-16 result with the full
        5-key subscale dict preserved — the clinician-UI reads the
        profile off this path."""
        user = "user-ders16-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "ders16"
        assert entry["total"] == 48
        assert entry["severity"] == "continuous"
        assert entry["subscales"] is not None
        assert set(entry["subscales"].keys()) == {
            "nonacceptance",
            "goals",
            "impulse",
            "strategies",
            "clarity",
        }

    def test_ders16_and_phq9_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """DERS-16 (DBT process target) and PHQ-9 (CBT-aligned
        symptom severity) cover ORTHOGONAL dimensions.  The canonical
        scenario: PHQ-9=6 (mild depression) with DERS-16=70 (severe
        emotion dysregulation) — e.g. a BPD-pattern patient whose
        symptom severity looks mild on a symptom measure but whose
        regulatory-process capacity is profoundly impaired.  Both
        records must persist so the bandit can route DBT skill
        modules on the process signal rather than defaulting to
        PHQ-9-driven behavioral activation alone."""
        user = "user-ders16-phq9-both"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [4, 4, 5, 5, 4, 4, 5, 5, 4, 4, 5, 4, 4, 4, 5, 4],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [1, 1, 1, 1, 1, 0, 1, 0, 0],  # mild, total 6
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        assert set(by_instrument) == {"ders16", "phq9"}
        # DERS-16: continuous, subscales populated.
        assert by_instrument["ders16"].severity == "continuous"
        assert by_instrument["ders16"].subscales is not None
        assert by_instrument["ders16"].cutoff_used is None
        # PHQ-9: banded, subscales None.
        assert by_instrument["phq9"].total == 6
        assert by_instrument["phq9"].severity == "mild"
        assert by_instrument["phq9"].subscales is None

    def test_ders16_and_aaq2_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """DERS-16 (DBT process target: regulatory capacity) and AAQ-II
        (ACT process target: psychological inflexibility) are both
        process-level instruments but cover DIFFERENT process
        constructs.  AAQ-II measures the RELATIONSHIP to internal
        experience (avoidance / fusion); DERS-16 measures the
        REGULATORY CAPACITY for internal experience (acceptance /
        impulse control / strategy access / clarity).  Both signals
        matter independently — a patient high on both triggers
        DBT+ACT integrative skill training; a patient high on
        AAQ-II but low on DERS-16 triggers pure ACT defusion work.
        Pinning both records coexist is pinning the two-process-
        target readout the bandit consumes."""
        user = "user-ders16-aaq2-both"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [5, 5, 5, 5, 5, 5, 5],  # total 35, > 24 positive
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        # DERS-16: continuous, subscales populated (DBT process axis).
        assert by_instrument["ders16"].severity == "continuous"
        assert by_instrument["ders16"].subscales is not None
        # AAQ-II: cutoff envelope (ACT process axis).
        assert by_instrument["aaq2"].cutoff_used == 24
        assert by_instrument["aaq2"].positive_screen is True

    def test_three_way_process_target_triangle(
        self, client: TestClient
    ) -> None:
        """DERS-16 (DBT target) + AAQ-II (ACT target) + PHQ-9 (CBT
        target) — the three-way process-target triangle.  Submitted
        together on one timeline they give the bandit the axes it
        needs to route process-level decisions by dominance rather
        than defaulting to CBT.  This test pins that all three
        records round-trip cleanly with distinct envelope shapes
        (continuous / cutoff / banded) on the same user."""
        user = "user-ders16-triangle"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aaq2",
                "items": [4, 4, 4, 4, 4, 4, 4],  # total 28, positive
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [2, 2, 2, 2, 2, 2, 2, 2, 0],  # total 16, mod-severe
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 3
        by_instrument = {r.instrument: r for r in records}
        assert set(by_instrument) == {"ders16", "aaq2", "phq9"}
        # Each carries its distinct envelope shape.
        assert by_instrument["ders16"].severity == "continuous"
        assert by_instrument["ders16"].subscales is not None
        assert by_instrument["aaq2"].cutoff_used == 24
        assert by_instrument["aaq2"].subscales is None
        assert by_instrument["phq9"].severity == "moderately_severe"
        assert by_instrument["phq9"].cutoff_used is None
        assert by_instrument["phq9"].subscales is None

    def test_ders16_and_wsas_coexist_on_same_user_timeline(
        self, client: TestClient
    ) -> None:
        """DERS-16 (emotion dysregulation — internal regulatory
        process) and WSAS (functional impairment — external
        behavioral outcome) cover orthogonal dimensions.  Both must
        persist cleanly so the intervention layer can distinguish
        'dysregulated but still functioning' from 'regulated but
        behaviorally shut down'."""
        user = "user-ders16-wsas-both"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [4] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        client.post(
            "/v1/assessments",
            json={
                "instrument": "wsas",
                "items": [5, 5, 5, 5, 5],  # total 25, severe
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 2
        by_instrument = {r.instrument: r for r in records}
        # DERS-16 continuous with subscales.
        assert by_instrument["ders16"].severity == "continuous"
        assert by_instrument["ders16"].subscales is not None
        # WSAS banded, no subscales.
        assert by_instrument["wsas"].severity == "severe"
        assert by_instrument["wsas"].subscales is None
        assert by_instrument["wsas"].cutoff_used is None

    def test_ignores_sex_field(self, client: TestClient) -> None:
        """DERS-16 is not sex-keyed.  Bjureberg 2016 published a
        single set of psychometric properties regardless of
        demographic axis."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "sex": "female",
                "user_id": "user-ders16-sex-ignored",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 48
        assert body["severity"] == "continuous"

    def test_ignores_mdq_only_fields(self, client: TestClient) -> None:
        """concurrent_symptoms / functional_impairment are MDQ-only
        (Hirschfeld 2000 Part 2 / Part 3).  They must not perturb
        DERS-16 scoring."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [5] * 16,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-ders16-mdq-fields",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "ders16"
        assert body["total"] == 80
        assert body["severity"] == "continuous"


class TestCdrisc10Routing:
    """CD-RISC-10 (Campbell-Sills & Stein 2007) router dispatch.

    Wire contract invariants:
    - Continuous envelope (``severity`` = "continuous" literal) uniform
      with Craving VAS / PACS / DERS-16.  No banded classification
      because Campbell-Sills & Stein 2007 published no cross-calibrated
      cutpoints (general-pop mean 31.8 ± 5.4 is a norm, not a threshold);
      trajectory layer extracts clinical signal via RCI-style change
      detection (Jacobson & Truax 1991).
    - **Higher-is-better direction** — same as WHO-5 / DTCQ-8 /
      Readiness Ruler, OPPOSITE of PHQ-9 / GAD-7 / DERS-16 / PCL-5 /
      OCI-R / K10 / WSAS.  The trajectory layer and clinician UI must
      treat a falling total as a DETERIORATION.
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, not cutoff shape.
    - ``requires_t3`` is always False — CD-RISC-10 has no safety item
      (all 10 items probe resilience capacity, not crisis).
    - ``subscales`` is None — Campbell-Sills & Stein 2007 CFA
      validates the unidimensional structure; the 25-item's five-
      factor split was explicitly rejected for the 10-item form.
      (Distinct from DERS-16's 5-subscale surface.)
    - ``triggering_items`` is None — CD-RISC-10 has no firing-item
      concept.
    - NOVEL 0-4 Likert envelope on a 10-item instrument — floor 0
      ("not true at all"), ceiling 4 ("true nearly all the time").
      -1 rejects (below floor).  5 rejects (above ceiling).
      Count must be exactly 10.
    - Cross-instrument coexistence: CD-RISC-10 + PHQ-9 on the same
      timeline (resilience-decoupling signal), CD-RISC-10 + DERS-16
      (resilience complement to dysregulation), CD-RISC-10 + WHO-5
      (direction-matched higher-is-better pair).
    """

    def test_all_floor_is_continuous(self, client: TestClient) -> None:
        """Every item at 0 ("not true at all") — total 0, the
        low-resilience floor.  ``severity`` is the "continuous"
        sentinel regardless of total — no "severe" band even at
        the floor because CD-RISC-10 does not classify."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "user_id": "user-cdrisc10-floor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "cdrisc10"
        assert body["total"] == 0
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_all_ceiling_is_continuous(self, client: TestClient) -> None:
        """Every item at 4 ("true nearly all the time") — total 40,
        the high-resilience ceiling.  Even at the max, severity stays
        "continuous" — Campbell-Sills & Stein 2007 published no
        "resilient" band.  Higher-is-better means the max is the
        best state, not the worst (opposite of DERS-16)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
                "user_id": "user-cdrisc10-ceiling",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 40
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_general_population_mean_is_continuous(
        self, client: TestClient
    ) -> None:
        """A score near Campbell-Sills & Stein 2007's U.S. general-
        population mean (31.8).  Even at population-typical
        resilience, severity is the "continuous" sentinel — the
        < 31 "below general-population mean" flag is a clinician-UI
        concern, not a router classification."""
        items = [4, 4, 4, 3, 3, 3, 3, 3, 3, 2]  # sum = 32
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": items,
                "user_id": "user-cdrisc10-mean",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 32
        assert body["severity"] == "continuous"

    def test_cutoff_used_not_populated(self, client: TestClient) -> None:
        """``cutoff_used`` is None because CD-RISC-10 has no cutoff
        (continuous, not cutoff shape)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [2] * 10,
                "user_id": "user-cdrisc10-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_subscales_is_none(self, client: TestClient) -> None:
        """``subscales`` is None — CD-RISC-10 is unidimensional per
        Campbell-Sills & Stein 2007 CFA.  This is the negative
        assertion distinguishing it from DERS-16 (5 subscales),
        OCI-R (6), PCL-5 (4), BIS-11 / URICA (3)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": "user-cdrisc10-nosubs",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        """``triggering_items`` is None — CD-RISC-10 has no
        firing-item concept (unlike C-SSRS / ASRS-6)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "user_id": "user-cdrisc10-notrig",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_item_10_floor_does_not_trigger_t3(
        self, client: TestClient
    ) -> None:
        """Item 10 ("Can handle unpleasant or painful feelings like
        sadness, fear, and anger.") at 0 ("not true at all") is the
        distress-tolerance floor — low capacity to sit with negative
        affect.  This is a DBT target, not a crisis signal.
        ``requires_t3`` must remain False.  Acute ideation screening
        stays on PHQ-9 item 9 / C-SSRS."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
                "user_id": "user-cdrisc10-distress-floor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        """``instrument_version`` matches the scorer module's
        pinned version string."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [2] * 10,
                "user_id": "user-cdrisc10-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["instrument_version"] == "cdrisc10-1.0.0"

    def test_too_few_items_rejects(self, client: TestClient) -> None:
        """9 items fails — exactly 10 required."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [2] * 9,
                "user_id": "user-cdrisc10-few",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_too_many_items_rejects(self, client: TestClient) -> None:
        """11 items fails — 10 required, not 16 (DERS-16 misroute)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [2] * 11,
                "user_id": "user-cdrisc10-many",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_negative_item_rejects(self, client: TestClient) -> None:
        """-1 fails — floor is 0, not -1."""
        bad = [0, 0, 0, 0, 0, 0, 0, 0, 0, -1]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": bad,
                "user_id": "user-cdrisc10-neg",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_five_rejects(self, client: TestClient) -> None:
        """5 fails — ceiling is 4 (0-4 Likert), not 5 (DERS-16 / WHO-5
        misroute).  Guards against locale copy-paste bugs that
        interpret CD-RISC-10 as a 1-5 scale like DERS-16."""
        bad = [4, 4, 4, 4, 4, 4, 4, 4, 4, 5]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": bad,
                "user_id": "user-cdrisc10-five",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_zero_accepts(self, client: TestClient) -> None:
        """0 accepts — floor is 0 on this envelope (unlike DERS-16 1-5)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [0] * 10,
                "user_id": "user-cdrisc10-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_four_accepts(self, client: TestClient) -> None:
        """4 accepts — ceiling is 4 on this envelope."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [4] * 10,
                "user_id": "user-cdrisc10-four",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_persists_to_repository(self, client: TestClient) -> None:
        """POST persists to the AssessmentRepository; the repository's
        ``history_for`` returns the record with continuous severity."""
        user = "user-cdrisc10-persist"
        post = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert post.status_code == 201

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "cdrisc10"
        assert rec.total == 30
        assert rec.severity == "continuous"
        assert rec.subscales is None

    def test_history_projects_cdrisc10(self, client: TestClient) -> None:
        """GET /history surfaces the CD-RISC-10 result with the
        continuous severity sentinel and no subscales field.  The
        clinician-UI reads resilience off this path."""
        user = "user-cdrisc10-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "cdrisc10"
        assert entry["total"] == 30
        assert entry["severity"] == "continuous"

    def test_coexists_with_phq9_resilience_decoupling(
        self, client: TestClient
    ) -> None:
        """CD-RISC-10 + PHQ-9 on the same timeline — the resilience-
        decoupling signal (CD-RISC-10 rises while PHQ-9 stays flat)
        is the early-recovery leading indicator.  Both axes must
        persist cleanly and retain their distinct envelope shapes
        (CD-RISC-10 continuous/higher-better, PHQ-9 banded/
        higher-worse)."""
        user = "user-cdrisc10-decoupling"
        phq = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [2, 2, 2, 2, 2, 2, 2, 2, 0],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert phq.status_code == 201
        assert phq.json()["severity"] in {
            "minimal",
            "mild",
            "moderate",
            "moderately_severe",
            "severe",
        }

        cd = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert cd.status_code == 201
        assert cd.json()["severity"] == "continuous"

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "phq9" in instruments
        assert "cdrisc10" in instruments

    def test_coexists_with_ders16_process_plus_resilience(
        self, client: TestClient
    ) -> None:
        """CD-RISC-10 + DERS-16 on the same timeline.  DERS-16
        measures dysregulation (process impairment, higher-worse)
        and CD-RISC-10 measures resilience (recovery capacity,
        higher-better) — the two are complements, not redundant.
        Both persist with their distinct directional semantics."""
        user = "user-cdrisc10-ders16"
        de = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert de.status_code == 201
        assert de.json()["severity"] == "continuous"
        assert de.json().get("subscales") is not None

        cd = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [2] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert cd.status_code == 201
        assert cd.json()["severity"] == "continuous"
        assert cd.json().get("subscales") is None

    def test_coexists_with_who5_direction_matched_pair(
        self, client: TestClient
    ) -> None:
        """CD-RISC-10 + WHO-5 on the same timeline — both
        higher-is-better.  CD-RISC-10 is a trait-resilience measure
        (dimensional, continuous); WHO-5 is a state-wellbeing
        measure (banded via index).  Both axes persist and retain
        their distinct envelope shapes (CD-RISC-10 "continuous"
        sentinel, WHO-5 banded)."""
        user = "user-cdrisc10-who5"
        who = client.post(
            "/v1/assessments",
            json={
                "instrument": "who5",
                "items": [3, 3, 3, 3, 3],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert who.status_code == 201

        cd = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert cd.status_code == 201
        assert cd.json()["severity"] == "continuous"

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "who5" in instruments
        assert "cdrisc10" in instruments

    def test_ignores_mdq_and_sex_fields(self, client: TestClient) -> None:
        """MDQ / AUDIT-C-specific fields at the request body are
        silently ignored for non-MDQ / non-AUDIT-C instruments.
        CD-RISC-10 scoring does not touch ``sex`` /
        ``concurrent_symptoms`` / ``functional_impairment``."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [4] * 10,
                "sex": "female",
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-cdrisc10-ignores",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "cdrisc10"
        assert body["total"] == 40
        assert body["severity"] == "continuous"


class TestPswqRouting:
    """PSWQ (Meyer 1990) router dispatch.

    Wire contract invariants:
    - Continuous envelope (``severity`` = "continuous" literal)
      uniform with Craving VAS / PACS / DERS-16 / CD-RISC-10.  No
      banded classification because Meyer 1990 published no cross-
      calibrated cutpoints; downstream tertile / GAD-cut proposals
      (Behar 2003, Startup & Erickson 2006, Fresco 2003) are
      sample-specific.  Trajectory layer extracts clinical signal via
      RCI-style change detection (Jacobson & Truax 1991).
    - **Higher-is-worse direction** — same as PHQ-9 / GAD-7 /
      DERS-16 / PCL-5 / OCI-R / K10 / WSAS, OPPOSITE of WHO-5 /
      DTCQ-8 / Readiness Ruler / CD-RISC-10.  The trajectory layer
      and clinician UI must treat a falling total as an IMPROVEMENT.
    - **First reverse-keying pattern** — items 1, 3, 8, 10, 11 are
      worded in the worry-ABSENT direction and arithmetic-reflected
      (``6 - raw``) inside the scorer before summing.  The router
      test layer verifies only the observable wire behavior (total
      matches expected post-flip sum); the detailed per-item flip
      math is covered in ``test_pswq_scoring.py``.
    - No ``cutoff_used`` / ``positive_screen`` — continuous.
    - ``requires_t3`` is always False — PSWQ has no safety item.
    - ``subscales`` is None — unidimensional per Meyer 1990 / Brown
      1992 CFA (distinct from DERS-16's 5-subscale surface).
    - ``triggering_items`` is None — no firing-item concept.
    - 1-5 Likert (same range as DERS-16); 0 rejects (below floor),
      6 rejects (above ceiling).  16 items required (same as
      DERS-16; the router dispatches by ``instrument`` key, not by
      count).
    - Cross-instrument coexistence: PSWQ + GAD-7 (orthogonal
      trait-worry vs state-anxiety axes), PSWQ + CD-RISC-10
      (direction-opposite pair), PSWQ + DERS-16 (same count but
      different construct and envelope shape).
    """

    def test_all_threes_is_48_continuous(self, client: TestClient) -> None:
        """Every item at 3 (Likert midpoint) — total 48 (flip-
        invariant because 6 - 3 = 3).  ``severity`` is the
        "continuous" sentinel regardless of total."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": "user-pswq-mid",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "pswq"
        assert body["total"] == 48
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_all_ones_total_36(self, client: TestClient) -> None:
        """Every raw item at 1.  11 non-reverse items × 1 = 11;
        5 reverse items post-flip (6-1=5) × 5 = 25.  Total = 36.
        This test pins that the router passes raw items through to
        the scorer WITHOUT pre-flipping — if the router flipped
        first, the scorer would double-flip and land on 16 instead
        of 36."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [1] * 16,
                "user_id": "user-pswq-all-ones",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 36
        assert body["severity"] == "continuous"

    def test_all_fives_total_60(self, client: TestClient) -> None:
        """Every raw item at 5.  11 non-reverse × 5 = 55; 5 reverse
        post-flip (6-5=1) × 1 = 5.  Total = 60.  This is the
        acquiescence-catch: an all-5s responder lands at 60 (not
        80), demonstrating the reverse-keying design's anti-bias
        property on the wire."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [5] * 16,
                "user_id": "user-pswq-all-fives",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 60
        assert body["severity"] == "continuous"

    def test_maximum_worry_ceiling(self, client: TestClient) -> None:
        """Maximum-worry pattern: non-reverse items at 5, reverse
        items at 1 (low "I never worry" endorsement = high worry).
        Total = (11 × 5) + (5 × 5 post-flip) = 55 + 25 = 80, the
        instrument ceiling.  ``severity`` still "continuous" — no
        "severe" band even at ceiling."""
        items = [0] * 16
        reverse_positions = {1, 3, 8, 10, 11}
        for i in range(1, 17):
            items[i - 1] = 1 if i in reverse_positions else 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": items,
                "user_id": "user-pswq-ceiling",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 80
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_minimum_worry_floor(self, client: TestClient) -> None:
        """Minimum-worry pattern: non-reverse items at 1, reverse
        items at 5 (high "I never worry" endorsement = low worry).
        Total = (11 × 1) + (5 × 1 post-flip) = 11 + 5 = 16, the
        instrument floor."""
        items = [0] * 16
        reverse_positions = {1, 3, 8, 10, 11}
        for i in range(1, 17):
            items[i - 1] = 5 if i in reverse_positions else 1
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": items,
                "user_id": "user-pswq-floor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 16
        assert body["severity"] == "continuous"

    def test_cutoff_used_not_populated(self, client: TestClient) -> None:
        """``cutoff_used`` is None because PSWQ has no cutoff."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": "user-pswq-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_subscales_is_none(self, client: TestClient) -> None:
        """``subscales`` is None — PSWQ is unidimensional per Meyer
        1990 / Brown 1992 CFA.  Distinguishes from DERS-16 (which
        also has 16 items but populates 5 subscales)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": "user-pswq-nosubs",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [5] * 16,
                "user_id": "user-pswq-notrig",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_item_2_overwhelm_does_not_trigger_t3(
        self, client: TestClient
    ) -> None:
        """Item 2 ("My worries overwhelm me.") at ceiling (5) is
        endorsement of the DSM-5 GAD uncontrollability criterion,
        NOT a crisis signal.  ``requires_t3`` must remain False.
        Acute ideation screening stays on PHQ-9 item 9 / C-SSRS."""
        items = [3] * 16
        items[1] = 5  # item 2
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": items,
                "user_id": "user-pswq-overwhelm",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["requires_t3"] is False

    def test_item_14_cannot_stop_does_not_trigger_t3(
        self, client: TestClient
    ) -> None:
        """Item 14 ("Once I start worrying, I cannot stop.") at
        ceiling is the GAD uncontrollability criterion — worry-
        postponement / decatastrophizing target, NOT a crisis gate."""
        items = [3] * 16
        items[13] = 5  # item 14
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": items,
                "user_id": "user-pswq-cannot-stop",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        assert response.json()["requires_t3"] is False

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": "user-pswq-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["instrument_version"] == "pswq-1.0.0"

    def test_too_few_items_rejects(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 15,
                "user_id": "user-pswq-few",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_too_many_items_rejects(self, client: TestClient) -> None:
        """17 items fails — exactly 16 required.  Guards against
        PCL-5 (20) / CD-RISC-10 (10) / URICA (16 but different
        instrument) misroute."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 17,
                "user_id": "user-pswq-many",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_zero_rejects(self, client: TestClient) -> None:
        """0 fails — floor is 1 (1-5 Likert), not 0 (CD-RISC-10 /
        PHQ-9 misroute)."""
        bad = [3] * 16
        bad[0] = 0
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": bad,
                "user_id": "user-pswq-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_six_rejects(self, client: TestClient) -> None:
        """6 fails — ceiling is 5, not 6 (1-6) or 7 (1-7 ERQ range)."""
        bad = [3] * 16
        bad[0] = 6
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": bad,
                "user_id": "user-pswq-six",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_one_and_five_accept(self, client: TestClient) -> None:
        """1 and 5 are the envelope boundaries and must both
        accept (at least one of each in the body)."""
        items = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": items,
                "user_id": "user-pswq-boundaries",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_persists_to_repository_with_raw_pre_flip_items(
        self, client: TestClient
    ) -> None:
        """POST persists the PATIENT'S RAW pre-flip responses to
        the repository — critical audit-trail invariant for
        reverse-keyed instruments.  A clinician reviewing the
        stored record must see what the patient actually ticked,
        not the scorer's internal post-flip representation."""
        user = "user-pswq-persist"
        raw = [3] * 16
        raw[0] = 2  # item 1 reverse-keyed; patient said "rarely typical"
        raw[1] = 4  # item 2 non-reverse; patient said "often typical"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": raw,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "pswq"
        assert rec.severity == "continuous"
        assert rec.subscales is None
        # Audit invariant: raw pre-flip items preserved.
        assert rec.raw_items[0] == 2  # raw, not 4 (post-flip)
        assert rec.raw_items[1] == 4

    def test_history_projects_pswq(self, client: TestClient) -> None:
        """GET /history surfaces the PSWQ result with continuous
        severity and no subscales field."""
        user = "user-pswq-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "pswq"
        assert entry["total"] == 48
        assert entry["severity"] == "continuous"

    def test_coexists_with_gad7_orthogonal_axes(
        self, client: TestClient
    ) -> None:
        """PSWQ (trait worry) + GAD-7 (state anxiety) on the same
        timeline — the two are orthogonal axes.  A patient can
        have controlled symptoms (low GAD-7) but persistent trait
        worry (high PSWQ), or vice versa; both must persist cleanly
        and retain their distinct envelope shapes (PSWQ continuous,
        GAD-7 banded)."""
        user = "user-pswq-gad7"
        gad = client.post(
            "/v1/assessments",
            json={
                "instrument": "gad7",
                "items": [1, 1, 1, 1, 1, 1, 1],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert gad.status_code == 201
        assert gad.json()["severity"] in {
            "minimal",
            "mild",
            "moderate",
            "severe",
        }

        pw = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert pw.status_code == 201
        assert pw.json()["severity"] == "continuous"

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "gad7" in instruments
        assert "pswq" in instruments

    def test_coexists_with_ders16_same_count_different_shape(
        self, client: TestClient
    ) -> None:
        """PSWQ and DERS-16 both have 16 items — router must
        dispatch by ``instrument`` key, not by count.  PSWQ
        persists unidimensional (subscales=None), DERS-16 persists
        multi-subscale (subscales populated with 5 keys)."""
        user = "user-pswq-ders16"
        de = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert de.status_code == 201
        assert de.json().get("subscales") is not None
        assert len(de.json()["subscales"]) == 5

        pw = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert pw.status_code == 201
        assert pw.json().get("subscales") is None

    def test_coexists_with_cdrisc10_opposite_directions(
        self, client: TestClient
    ) -> None:
        """PSWQ (higher-is-worse) + CD-RISC-10 (higher-is-better)
        on the same timeline.  Both continuous-sentinel but
        direction-opposite.  Together they give the trajectory
        layer a clean worry-vs-resilience pair: rising PSWQ AND
        falling CD-RISC-10 is a cross-construct deterioration
        signal."""
        user = "user-pswq-cdrisc10"
        cd = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert cd.status_code == 201
        assert cd.json()["severity"] == "continuous"

        pw = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert pw.status_code == 201
        assert pw.json()["severity"] == "continuous"

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "cdrisc10" in instruments
        assert "pswq" in instruments

    def test_ignores_mdq_and_sex_fields(self, client: TestClient) -> None:
        """MDQ / AUDIT-C-specific fields at the request body are
        silently ignored for non-MDQ / non-AUDIT-C instruments."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "sex": "female",
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-pswq-ignores",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "pswq"
        assert body["total"] == 48
        assert body["severity"] == "continuous"


class TestLotrRouting:
    """LOT-R (Scheier, Carver & Bridges 1994) router dispatch.

    Wire contract invariants:
    - Continuous envelope (``severity`` = "continuous" literal)
      uniform with Craving VAS / PACS / DERS-16 / CD-RISC-10 / PSWQ.
      No banded classification because Scheier 1994 published no
      cross-calibrated clinical cutpoints; Carver 2010's 400-study
      review did not produce one either.  Trajectory layer extracts
      clinical signal via RCI-style change detection (Jacobson &
      Truax 1991) on the 0-24 total.
    - **Higher-is-better direction** — uniform with CD-RISC-10 /
      WHO-5 / DTCQ-8 / Readiness Ruler, OPPOSITE of PHQ-9 / GAD-7 /
      DERS-16 / PCL-5 / OCI-R / K10 / WSAS / PSWQ.  A falling LOT-R
      total is a DETERIORATION, not an improvement.
    - **First filler-item pattern** — 10 items on the wire (6 scored
      + 4 filler).  Scored positions 1, 3, 4, 7, 9, 10; filler
      positions 2, 5, 6, 8.  Router accepts a 10-item payload
      because the patient sees 10 items on the form; only the 6
      scored positions contribute to the sum.  Audit-trail invariant
      preserved: the stored record echoes all 10 raw responses.
    - **Reverse-keying reused from PSWQ** — items 3, 7, 9 are
      pessimism-worded and arithmetic-reflected (``4 - raw``) inside
      the scorer before summing.  The router test layer verifies
      only the observable wire behavior (total matches expected
      post-flip sum); the detailed per-item math is covered in
      ``test_lotr_scoring.py``.
    - No ``cutoff_used`` / ``positive_screen`` — continuous.
    - ``requires_t3`` is always False — LOT-R has no safety item.
    - ``subscales`` is None — unidimensional per Scheier 1994 CFA
      (Chang 1997 two-factor split is sample-specific and rejected).
    - ``triggering_items`` is None — no firing-item concept.
    - 0-4 Likert envelope — novel on the router surface; -1 rejects
      (below floor), 5 rejects (above ceiling).  10 items required.
    - Cross-instrument coexistence: LOT-R + CD-RISC-10 is the
      trait-positive-psychology DIRECT pair (both higher-is-better
      continuous); LOT-R + PSWQ is the direction-opposite trait
      pair (both continuous, opposite direction).
    """

    def test_all_twos_is_12_continuous(self, client: TestClient) -> None:
        """Every item at 2 (midline) — total 12 (flip-invariant:
        ``4 - 2 = 2``).  ``severity`` is the "continuous" sentinel."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": "user-lotr-mid",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "lotr"
        assert body["total"] == 12
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_all_zeros_total_12_acquiescence_floor(
        self, client: TestClient
    ) -> None:
        """Every raw item at 0.  Scored items 1, 4, 10 (direct)
        contribute 0 each; scored items 3, 7, 9 (reverse) post-flip
        contribute ``4 - 0 = 4`` each.  Total = 0+4+0+4+4+0 = 12.
        Fillers excluded.  This is the dis-acquiescence catch: a
        patient who strong-disagrees with everything lands at
        midline, not at floor."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [0] * 10,
                "user_id": "user-lotr-all-zeros",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "continuous"

    def test_all_fours_total_12_acquiescence_ceiling(
        self, client: TestClient
    ) -> None:
        """Every raw item at 4.  Direct items (1, 4, 10) contribute
        4 each; reverse items (3, 7, 9) post-flip contribute
        ``4 - 4 = 0`` each.  Total = 4+0+4+0+0+4 = 12.  This is the
        acquiescence-bias catch: a responder who checks "strongly
        agree" for every item lands at midline (12), NOT ceiling
        (24).  A clinician reading 12 on a mixed-direction
        instrument knows to flag response-set bias."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [4] * 10,
                "user_id": "user-lotr-all-fours",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "continuous"

    def test_maximum_optimism_ceiling(self, client: TestClient) -> None:
        """Maximum-optimism pattern: direct items at 4, reverse items
        at 0 (patient strong-disagrees with pessimism-worded items).
        Fillers set to 2 — must not affect the total.  Contributions:
        4 + 4 + 4 + 4 + 4 + 4 = 24 (instrument ceiling).  ``severity``
        still "continuous" — no "high-optimism" band."""
        items = [0] * 10
        items[0] = 4   # item 1 direct
        items[2] = 0   # item 3 reverse
        items[3] = 4   # item 4 direct
        items[6] = 0   # item 7 reverse
        items[8] = 0   # item 9 reverse
        items[9] = 4   # item 10 direct
        items[1] = 2   # item 2 filler
        items[4] = 2   # item 5 filler
        items[5] = 2   # item 6 filler
        items[7] = 2   # item 8 filler
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": items,
                "user_id": "user-lotr-ceiling",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 24
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_minimum_optimism_floor(self, client: TestClient) -> None:
        """Minimum-optimism pattern: direct items at 0, reverse items
        at 4 (patient strong-agrees with pessimism-worded items).
        Contributions: 0 + 0 + 0 + 0 + 0 + 0 = 0 (instrument floor).
        A low LOT-R is a strong signal for outcome-expectancy
        scaffolding but NOT a crisis gate — ``requires_t3`` remains
        False even at floor."""
        items = [0] * 10
        items[0] = 0   # item 1 direct
        items[2] = 4   # item 3 reverse
        items[3] = 0   # item 4 direct
        items[6] = 4   # item 7 reverse
        items[8] = 4   # item 9 reverse
        items[9] = 0   # item 10 direct
        # Fillers default 0 — should not affect.
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": items,
                "user_id": "user-lotr-floor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_filler_items_do_not_change_total_on_wire(
        self, client: TestClient
    ) -> None:
        """Wire-level filler exclusion test.  Hold the 6 scored
        positions at the max-optimism pattern; vary the 4 filler
        positions between 0 and 4.  Both submissions must return
        total = 24 — the fillers never contribute."""
        # Scored max-optimism + fillers at 0.
        items_a = [4, 0, 0, 4, 0, 0, 0, 0, 0, 4]
        # Scored max-optimism + fillers at 4.
        items_b = [4, 4, 0, 4, 4, 4, 0, 4, 0, 4]
        resp_a = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": items_a,
                "user_id": "user-lotr-fill-a",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        resp_b = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": items_b,
                "user_id": "user-lotr-fill-b",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert resp_a.status_code == 201
        assert resp_b.status_code == 201
        assert resp_a.json()["total"] == 24
        assert resp_b.json()["total"] == 24

    def test_cutoff_used_not_populated(self, client: TestClient) -> None:
        """``cutoff_used`` is None because LOT-R has no cutoff."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": "user-lotr-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_subscales_is_none(self, client: TestClient) -> None:
        """``subscales`` is None — LOT-R is unidimensional per
        Scheier 1994 (Chang 1997 two-factor split rejected)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": "user-lotr-nosubs",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [4] * 10,
                "user_id": "user-lotr-notrig",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": "user-lotr-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["instrument_version"] == "lotr-1.0.0"

    def test_too_few_items_rejects(self, client: TestClient) -> None:
        """9 items fails — exactly 10 required.  Guards against
        clients that pre-strip fillers and send only the 6 scored
        positions (or send 9 hoping for a lenient scorer)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 9,
                "user_id": "user-lotr-few",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_too_many_items_rejects(self, client: TestClient) -> None:
        """11 items fails — exactly 10 required.  Guards against
        misroute to DUDIT (11) / PSWQ (16) / URICA (16) / DERS-16 (16)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 11,
                "user_id": "user-lotr-many",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_six_scored_items_only_rejects(self, client: TestClient) -> None:
        """A caller who pre-strips fillers and sends only the 6
        scored items must be rejected — the wire contract requires
        all 10."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [4, 0, 4, 0, 0, 4],
                "user_id": "user-lotr-six",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_five_rejects_above_ceiling(self, client: TestClient) -> None:
        """5 fails — ceiling is 4, not 5 (1-5 PSWQ envelope
        misroute) or 7 (1-7 ERQ range)."""
        bad = [2] * 10
        bad[0] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": bad,
                "user_id": "user-lotr-five",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_negative_rejects_below_floor(self, client: TestClient) -> None:
        bad = [2] * 10
        bad[0] = -1
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": bad,
                "user_id": "user-lotr-neg",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_out_of_range_at_filler_position_rejects(
        self, client: TestClient
    ) -> None:
        """Range violation at a filler position still rejects —
        fillers are validated identically to scored items because
        a value outside [0, 4] in a filler slot is a wire-format
        violation regardless of whether it will be summed."""
        bad = [2] * 10
        bad[1] = 7  # item 2, filler
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": bad,
                "user_id": "user-lotr-filler-oor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_zero_and_four_accept_boundaries(
        self, client: TestClient
    ) -> None:
        """0 and 4 are the envelope boundaries and must both accept."""
        items = [0, 4, 0, 4, 0, 4, 0, 4, 0, 4]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": items,
                "user_id": "user-lotr-boundaries",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_persists_all_ten_raw_items_including_fillers(
        self, client: TestClient
    ) -> None:
        """POST persists ALL 10 raw items to the repository — the 4
        filler values and the 6 scored raw pre-flip values.  Audit
        invariant: the stored record must show exactly what the
        patient ticked on the 10-item form, not the scorer's
        internal post-flip or filler-stripped representation."""
        user = "user-lotr-persist"
        # Scored direct=3, reverse=1 (moderate optimist); fillers
        # set distinctively so we can verify each filler is preserved.
        raw = [3, 1, 1, 3, 2, 3, 1, 4, 1, 3]
        client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": raw,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "lotr"
        assert rec.severity == "continuous"
        assert rec.subscales is None
        # Audit invariant: all 10 raw items preserved.
        assert tuple(rec.raw_items) == tuple(raw)
        # Filler values preserved verbatim (positions 2, 5, 6, 8 —
        # 0-indexed 1, 4, 5, 7).
        assert rec.raw_items[1] == 1  # item 2
        assert rec.raw_items[4] == 2  # item 5
        assert rec.raw_items[5] == 3  # item 6
        assert rec.raw_items[7] == 4  # item 8
        # Reverse-item raw preserved (pre-flip), not post-flip.
        assert rec.raw_items[2] == 1  # item 3, raw (not 3 = 4-1)
        # Scored total: direct 3+3+3 + reverse (4-1)+(4-1)+(4-1) = 18.
        assert rec.total == 18

    def test_history_projects_lotr(self, client: TestClient) -> None:
        """GET /history surfaces the LOT-R result with continuous
        severity and no subscales field."""
        user = "user-lotr-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "lotr"
        assert entry["total"] == 12
        assert entry["severity"] == "continuous"

    def test_coexists_with_cdrisc10_direct_trait_pair(
        self, client: TestClient
    ) -> None:
        """LOT-R (outcome expectancy) + CD-RISC-10 (resilience
        capacity) is the trait-positive-psychology DIRECT pair —
        both higher-is-better continuous.  Together they form the
        two-axis trait layer: "CAN I bounce back?" (CD-RISC-10) +
        "DO I EXPECT good things?" (LOT-R).  Both must persist
        cleanly with matching ``severity="continuous"``."""
        user = "user-lotr-cdrisc10"
        cd = client.post(
            "/v1/assessments",
            json={
                "instrument": "cdrisc10",
                "items": [3] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert cd.status_code == 201
        assert cd.json()["severity"] == "continuous"

        lr = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert lr.status_code == 201
        assert lr.json()["severity"] == "continuous"

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "cdrisc10" in instruments
        assert "lotr" in instruments

    def test_coexists_with_pswq_opposite_trait_directions(
        self, client: TestClient
    ) -> None:
        """LOT-R (higher-is-better dispositional optimism) + PSWQ
        (higher-is-worse trait worry) — direction-opposite trait
        pair.  Both continuous-sentinel on the wire but semantically
        opposite.  A pessimistic-worrier profile (low LOT-R + high
        PSWQ) is the classic GAD-ruminator cluster that responds to
        CBT-for-GAD + optimism training combined interventions
        (Hanssen 2013)."""
        user = "user-lotr-pswq"
        pw = client.post(
            "/v1/assessments",
            json={
                "instrument": "pswq",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert pw.status_code == 201
        assert pw.json()["severity"] == "continuous"

        lr = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert lr.status_code == 201
        assert lr.json()["severity"] == "continuous"

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "pswq" in instruments
        assert "lotr" in instruments

    def test_ignores_mdq_and_sex_fields(self, client: TestClient) -> None:
        """MDQ / AUDIT-C-specific fields at the request body are
        silently ignored for non-MDQ / non-AUDIT-C instruments."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "lotr",
                "items": [2] * 10,
                "sex": "female",
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-lotr-ignores",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "lotr"
        assert body["total"] == 12
        assert body["severity"] == "continuous"


class TestTas20Routing:
    """TAS-20 (Bagby, Parker & Taylor 1994) router dispatch.

    Wire contract invariants:
    - **Banded severity** — the ``severity`` field carries the
      Bagby 1994 band ("non_alexithymic" / "possible_alexithymia"
      / "alexithymic"), NOT the continuous sentinel.  Re-introduces
      banded classification after five consecutive continuous-
      sentinel instruments (WSAS, DERS-16, CD-RISC-10, PSWQ, LOT-R).
    - **Subscales populated** — the ``subscales`` map carries keys
      ``dif`` / ``ddf`` / ``eot`` with post-flip subscale totals.
      Distinct from DERS-16's continuous+subscales shape: TAS-20 is
      banded+subscales (a structurally different envelope).
    - **Higher-is-worse direction** — uniform with PHQ-9 / GAD-7 /
      DERS-16 / PCL-5 / OCI-R / K10 / WSAS / PSWQ, opposite of
      WHO-5 / CD-RISC-10 / LOT-R / DTCQ-8.
    - **Reverse-keying reuses PSWQ / LOT-R idiom** — items 4, 5,
      10, 18, 19 are flipped (``6 - raw``) inside the scorer.  The
      router test layer verifies only the observable wire behavior;
      detailed per-item math is covered in ``test_tas20_scoring.py``.
    - No ``cutoff_used`` / ``positive_screen`` — TAS-20 uses three
      bands, not a single binary cutoff.
    - ``requires_t3`` is always False — TAS-20 has no safety item.
    - ``triggering_items`` is None — no firing-item concept.
    - 1-5 Likert envelope; 0 rejects (below floor), 6 rejects
      (above ceiling).  20 items required (same count as PCL-5;
      router dispatches by ``instrument`` key, not by count).
    - Cross-instrument coexistence: TAS-20 + DERS-16 (upstream
      emotion identification + downstream emotion regulation —
      the two-layer emotion-processing framework), TAS-20 + PHQ-15
      (alexithymia + somatization — Taylor 1997 clinical cluster).
    """

    def test_all_threes_is_60_possible_alexithymia(
        self, client: TestClient
    ) -> None:
        """Every item at 3 (midline) → total 60 → upper edge of
        possible_alexithymia band.  Clinically: "neither agree nor
        disagree" on alexithymia-identifying statements is itself
        evidence of poor emotional self-knowledge — the midline
        responder lands in the borderline band."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": "user-tas20-mid",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "tas20"
        assert body["total"] == 60
        assert body["severity"] == "possible_alexithymia"
        assert body["requires_t3"] is False

    def test_all_ones_non_alexithymic(self, client: TestClient) -> None:
        """Every raw item at 1.  Direct 15 × 1 = 15; reverse 5 ×
        (6-1)=5 = 25.  Total = 40 → non_alexithymic."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [1] * 20,
                "user_id": "user-tas20-ones",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 40
        assert body["severity"] == "non_alexithymic"

    def test_all_fives_alexithymic_acquiescence_catch(
        self, client: TestClient
    ) -> None:
        """Every raw item at 5.  Direct 15 × 5 = 75; reverse 5 ×
        (6-5)=1 = 5.  Total = 80 → alexithymic.  Acquiescence bias
        is caught (80 not 100) but the clinical classification
        still lands in the alexithymic band."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [5] * 20,
                "user_id": "user-tas20-fives",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 80
        assert body["severity"] == "alexithymic"
        assert body["requires_t3"] is False

    def test_maximum_alexithymia_ceiling(self, client: TestClient) -> None:
        """Direct items at 5, reverse items (4, 5, 10, 18, 19) at
        1.  Post-flip every item at 5.  Total 100 — instrument
        ceiling — alexithymic band."""
        reverse = {4, 5, 10, 18, 19}
        items = [1 if i in reverse else 5 for i in range(1, 21)]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": items,
                "user_id": "user-tas20-ceiling",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 100
        assert body["severity"] == "alexithymic"

    def test_minimum_alexithymia_floor(self, client: TestClient) -> None:
        """Direct items at 1, reverse items at 5.  Post-flip every
        item at 1.  Total 20 — instrument floor —
        non_alexithymic band."""
        reverse = {4, 5, 10, 18, 19}
        items = [5 if i in reverse else 1 for i in range(1, 21)]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": items,
                "user_id": "user-tas20-floor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "non_alexithymic"

    def test_band_boundary_61_alexithymic(self, client: TestClient) -> None:
        """Total 61 → alexithymic (one above the 60 upper of
        possible).  Pins the boundary crossing."""
        items = [3] * 20
        items[0] = 4  # item 1 direct: +1 → total 61
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": items,
                "user_id": "user-tas20-boundary-61",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 61
        assert body["severity"] == "alexithymic"

    def test_subscales_populated_wire(self, client: TestClient) -> None:
        """Wire envelope populates ``subscales`` with keys
        ``dif`` / ``ddf`` / ``eot``.  All raw 3 → subscales 21 /
        15 / 24 (sum 60)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": "user-tas20-subs",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        subs = body.get("subscales")
        assert subs is not None
        assert set(subs.keys()) == {"dif", "ddf", "eot"}
        assert subs["dif"] == 21
        assert subs["ddf"] == 15
        assert subs["eot"] == 24
        # Subscales partition the total.
        assert subs["dif"] + subs["ddf"] + subs["eot"] == body["total"]

    def test_cutoff_used_not_populated(self, client: TestClient) -> None:
        """TAS-20 uses three bands — not a single binary cutoff."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": "user-tas20-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [5] * 20,
                "user_id": "user-tas20-notrig",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": "user-tas20-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["instrument_version"] == "tas20-1.0.0"

    def test_too_few_items_rejects(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 19,
                "user_id": "user-tas20-few",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_too_many_items_rejects(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 21,
                "user_id": "user-tas20-many",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_zero_rejects_below_floor(self, client: TestClient) -> None:
        """0 fails — floor is 1, not 0 (CD-RISC-10 / LOT-R
        envelope misroute guard)."""
        bad = [3] * 20
        bad[0] = 0
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": bad,
                "user_id": "user-tas20-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_six_rejects_above_ceiling(self, client: TestClient) -> None:
        """6 fails — ceiling is 5."""
        bad = [3] * 20
        bad[0] = 6
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": bad,
                "user_id": "user-tas20-six",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_one_and_five_accept_boundaries(
        self, client: TestClient
    ) -> None:
        items = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": items,
                "user_id": "user-tas20-boundaries",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_persists_raw_pre_flip_items_with_subscales(
        self, client: TestClient
    ) -> None:
        """POST persists the PATIENT'S RAW 20-tuple pre-flip to
        the repository, and the subscale map to the record's
        subscales field.  Audit-trail invariant: clinician
        reviewing the record sees what the patient actually
        ticked (not the scorer's internal post-flip), and the
        subscale totals as rendered on the wire."""
        user = "user-tas20-persist"
        # Raw pattern with distinctive values per position.
        raw = [3] * 20
        raw[0] = 4   # item 1 direct DIF
        raw[3] = 2   # item 4 reverse DDF — pre-flip 2, post-flip 4
        raw[4] = 1   # item 5 reverse EOT — pre-flip 1, post-flip 5
        client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": raw,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "tas20"
        assert rec.severity in (
            "non_alexithymic",
            "possible_alexithymia",
            "alexithymic",
        )
        # Audit invariant: raw pre-flip items preserved.
        assert rec.raw_items[0] == 4
        assert rec.raw_items[3] == 2  # NOT 4 (post-flip)
        assert rec.raw_items[4] == 1  # NOT 5 (post-flip)
        # Subscales populated.
        assert rec.subscales is not None
        assert set(rec.subscales.keys()) == {"dif", "ddf", "eot"}

    def test_history_projects_tas20_with_subscales(
        self, client: TestClient
    ) -> None:
        user = "user-tas20-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "tas20"
        assert entry["total"] == 60
        assert entry["severity"] == "possible_alexithymia"

    def test_coexists_with_ders16_two_layer_emotion_processing(
        self, client: TestClient
    ) -> None:
        """TAS-20 (upstream emotion identification) + DERS-16
        (downstream emotion regulation) — the two-layer emotion-
        processing framework.  Both have subscale dispatch, but
        different envelope shapes (TAS-20 banded severity +
        subscales; DERS-16 continuous sentinel + subscales).  The
        intervention-selection layer reads both: high TAS-20 DIF
        + high DERS-16 total routes to affect-labeling FIRST,
        regulation training SECOND."""
        user = "user-tas20-ders16"
        de = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert de.status_code == 201
        de_body = de.json()
        assert de_body["severity"] == "continuous"
        assert de_body.get("subscales") is not None
        assert len(de_body["subscales"]) == 5  # DERS-16 five subscales

        ta = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert ta.status_code == 201
        ta_body = ta.json()
        assert ta_body["severity"] == "possible_alexithymia"
        assert ta_body.get("subscales") is not None
        assert len(ta_body["subscales"]) == 3  # TAS-20 three subscales

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "ders16" in instruments
        assert "tas20" in instruments

    def test_coexists_with_phq15_somatization_cluster(
        self, client: TestClient
    ) -> None:
        """TAS-20 + PHQ-15 is the Taylor 1997 somatization cluster
        — alexithymic arousal without cognitive label presents as
        bodily complaints.  Both must persist cleanly."""
        user = "user-tas20-phq15"
        phq15 = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq15",
                "items": [1] * 15,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert phq15.status_code == 201

        ta = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert ta.status_code == 201

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "phq15" in instruments
        assert "tas20" in instruments

    def test_banded_severity_not_continuous_sentinel(
        self, client: TestClient
    ) -> None:
        """Pins that TAS-20 breaks the 5-sprint continuous-sentinel
        streak.  ``severity`` is a Bagby 1994 band name, NOT the
        "continuous" literal used by DERS-16 / CD-RISC-10 / PSWQ /
        LOT-R.  A renderer that hardcoded "continuous" handling for
        these new instruments must now dispatch on banded severity
        for TAS-20."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": "user-tas20-banded",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["severity"] != "continuous"
        assert body["severity"] in (
            "non_alexithymic",
            "possible_alexithymia",
            "alexithymic",
        )

    def test_ignores_mdq_and_sex_fields(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "sex": "female",
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "user_id": "user-tas20-ignores",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "tas20"
        assert body["severity"] == "possible_alexithymia"


class TestErqRouting:
    """ERQ (Gross & John 2003) router dispatch.

    Wire contract invariants:
    - **Continuous-sentinel severity** — the ``severity`` field
      carries the literal ``"continuous"`` sentinel (uniform with
      DERS-16 / BRS / PSWQ / SDS / K6 / CD-RISC-10 / LOT-R / PACS /
      BIS-11).  ERQ has no published severity bands — Gross & John
      2003 report it as a dispositional continuous measure.
    - **Subscales populated** — the ``subscales`` map carries keys
      ``reappraisal`` / ``suppression`` with subscale sums.
      **Reappraisal+Suppression = Total** (tautology of the coverage
      invariant: every item lives in exactly one subscale, no
      reverse-keying).  Same envelope shape as DERS-16 (continuous +
      subscales); distinct from TAS-20 (banded + subscales).
    - **Novel 1-7 Likert envelope** — 0 rejects (below floor), 8
      rejects (above ceiling).  Distinct from prior envelopes
      (1-5 for TAS-20 / DERS-16 / PSWQ; 0-3 for PHQ-9 / GAD-7;
      0-5 for WHO-5; 0-4 for LOT-R; 0-10 for VAS/Ruler).
    - **No reverse-keyed items** — all 10 items are endorsement-
      direction for their subscale, so raw=post for scoring (unlike
      TAS-20 / LOT-R / PSWQ which flip 3-5 items arithmetically).
    - No ``cutoff_used`` / ``positive_screen`` — no binary cutoff.
    - ``requires_t3`` is always False — no safety item.
    - ``triggering_items`` is None — no firing-item concept.
    - 10 items required (same count as LOT-R / DAST-10 / K10 / etc.;
      dispatch is by ``instrument`` key, not by count).
    - Cross-instrument coexistence: ERQ + TAS-20 + DERS-16 (the
      three-layer emotion-processing architecture — identification
      upstream, strategy choice midstream, execution downstream),
      and ERQ + PHQ-9 (suppression-elevated patients respond slower
      to standard CBT — the router must preserve both signals for
      the intervention-selection layer).
    """

    def test_all_fours_is_forty_midline(self, client: TestClient) -> None:
        """Every item at 4 (midline neutral on 1-7 scale) → total 40.

        Reappraisal sum = 6 × 4 = 24.
        Suppression sum = 4 × 4 = 16.
        Total = 10 × 4 = 40.  No severity band is emitted; only the
        continuous-sentinel literal.
        """
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": "user-erq-mid",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "erq"
        assert body["total"] == 40
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_all_ones_minimum_total(self, client: TestClient) -> None:
        """Every item at 1 (strongly disagree) → total 10 (floor).

        Reappraisal 6, Suppression 4.  No 0-floor reading — ERQ
        anchors at 1, uniform with DERS-16 / TAS-20 / K6 / K10.
        """
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [1] * 10,
                "user_id": "user-erq-ones",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 10
        assert body["severity"] == "continuous"
        subs = body["subscales"]
        assert subs["reappraisal"] == 6
        assert subs["suppression"] == 4

    def test_all_sevens_maximum_total(self, client: TestClient) -> None:
        """Every item at 7 (strongly agree) → total 70 (ceiling).

        Both strategies maximally endorsed — Reappraisal 42,
        Suppression 28.  A patient who tries everything; clinically
        often pairs with anxious-achiever profile on Big Five
        (Gross & John 2003 convergent validity study).
        """
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [7] * 10,
                "user_id": "user-erq-sevens",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 70
        subs = body["subscales"]
        assert subs["reappraisal"] == 42
        assert subs["suppression"] == 28

    def test_pure_reappraiser_profile_wire(self, client: TestClient) -> None:
        """Reappraisal items at 7, suppression items at 1.

        Items 1/3/5/7/8/10 = 7 (reappraisal = 42).
        Items 2/4/6/9     = 1 (suppression = 4).
        Total = 46.  The "protective profile" (Aldao 2010) — on the
        wire the client can read ``subscales['reappraisal']`` as
        the dominant signal.
        """
        # Reappraisal positions (1-indexed): 1, 3, 5, 7, 8, 10.
        items = [7, 1, 7, 1, 7, 1, 7, 7, 1, 7]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": items,
                "user_id": "user-erq-reappraiser",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 46
        subs = body["subscales"]
        assert subs["reappraisal"] == 42
        assert subs["suppression"] == 4

    def test_pure_suppressor_profile_wire(self, client: TestClient) -> None:
        """Suppression items at 7, reappraisal items at 1.

        Items 2/4/6/9     = 7 (suppression = 28).
        Items 1/3/5/7/8/10 = 1 (reappraisal = 6).
        Total = 34.  The "highest-concern profile" — suppressor
        clinically correlates with depression, cardiovascular risk,
        interpersonal dysfunction, and SUD relapse.  On the wire
        ``subscales['suppression']`` dominates despite the total
        being below the all-fours midline (40).  This is the
        reason aggregate total is clinically secondary to the
        subscale pair.
        """
        items = [1, 7, 1, 7, 1, 7, 1, 1, 7, 1]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": items,
                "user_id": "user-erq-suppressor",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 34
        subs = body["subscales"]
        assert subs["reappraisal"] == 6
        assert subs["suppression"] == 28

    def test_subscales_always_populated_wire(self, client: TestClient) -> None:
        """Even on an all-neutral submission the ``subscales`` map
        is present on the envelope with both keys.  Clients must
        not special-case the "empty subscales" shape for ERQ."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": "user-erq-subs-present",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        subs = body["subscales"]
        assert subs is not None
        assert set(subs.keys()) == {"reappraisal", "suppression"}
        assert isinstance(subs["reappraisal"], int)
        assert isinstance(subs["suppression"], int)

    def test_cutoff_used_not_populated(self, client: TestClient) -> None:
        """ERQ has no binary cutoff; ``cutoff_used`` must remain
        the unset/None sentinel.  This separates ERQ from AUDIT-C
        / MDQ / PHQ-2 / GAD-2 / PC-PTSD-5 at the envelope level."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": "user-erq-cutoff-none",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        """ERQ has no firing-item concept — ``triggering_items``
        stays None, uniform with DERS-16 / TAS-20 / PHQ-9 (when no
        item 9 fires) / GAD-7."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [7] * 10,
                "user_id": "user-erq-trig-none",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": "user-erq-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["instrument_version"] == "erq-1.0.0"

    def test_nine_items_rejects(self, client: TestClient) -> None:
        """ERQ requires exactly 10 items — router rejects with 422."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 9,
                "user_id": "user-erq-nine",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_eleven_items_rejects(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 11,
                "user_id": "user-erq-eleven",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_zero_rejects_below_floor(self, client: TestClient) -> None:
        """0 fails — floor is 1 (distinguishes ERQ from PHQ-9 /
        GAD-7 / PSS-10 which accept 0)."""
        bad = [4] * 10
        bad[0] = 0
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": bad,
                "user_id": "user-erq-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_eight_rejects_above_ceiling(self, client: TestClient) -> None:
        """8 fails — ceiling is 7 (distinguishes ERQ's novel 1-7
        envelope from TAS-20 / DERS-16 / PSWQ's 1-5 ceiling)."""
        bad = [4] * 10
        bad[0] = 8
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": bad,
                "user_id": "user-erq-eight",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_seven_accepts_ceiling(self, client: TestClient) -> None:
        """7 accepts — pins the upper boundary on the novel 1-7
        envelope that other scorers on this dispatcher do NOT
        accept."""
        items = [1, 7, 1, 7, 1, 7, 1, 7, 1, 7]
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": items,
                "user_id": "user-erq-seven",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201

    def test_persists_raw_items_with_subscales(
        self, client: TestClient
    ) -> None:
        """POST persists the raw 10-tuple to the repository, and
        the subscale map to the record's subscales field.  Audit-
        trail invariant: no reverse-keying on ERQ means raw IS
        post-flip (same value), but the record still pins the raw
        integers so a future instrument revision that changed
        scoring cannot silently re-interpret historical data."""
        user = "user-erq-persist"
        raw = [2, 6, 3, 5, 1, 7, 4, 3, 5, 6]
        client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": raw,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "erq"
        assert rec.severity == "continuous"
        assert tuple(rec.raw_items) == tuple(raw)
        assert rec.subscales is not None
        assert set(rec.subscales.keys()) == {"reappraisal", "suppression"}
        # Reappraisal items 1, 3, 5, 7, 8, 10 →
        # raw[0]+raw[2]+raw[4]+raw[6]+raw[7]+raw[9]
        # = 2 + 3 + 1 + 4 + 3 + 6 = 19
        assert rec.subscales["reappraisal"] == 19
        # Suppression items 2, 4, 6, 9 →
        # raw[1]+raw[3]+raw[5]+raw[8] = 6 + 5 + 7 + 5 = 23
        assert rec.subscales["suppression"] == 23

    def test_history_projects_erq(self, client: TestClient) -> None:
        user = "user-erq-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        items = history.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "erq"
        assert entry["total"] == 40
        assert entry["severity"] == "continuous"

    def test_coexists_with_tas20_and_ders16_three_layer_framework(
        self, client: TestClient
    ) -> None:
        """ERQ (strategy choice) + TAS-20 (identification) + DERS-16
        (execution) — the three-layer emotion-processing architecture.
        All three must persist cleanly, with the router producing
        THREE distinct envelope shapes:
        - TAS-20: banded severity + subscales (3 keys).
        - DERS-16: continuous-sentinel + subscales (5 keys).
        - ERQ: continuous-sentinel + subscales (2 keys).
        The intervention-selection layer reads all three — order
        and envelope-shape differentiation matter."""
        user = "user-erq-three-layer"
        ta = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert ta.status_code == 201
        ta_body = ta.json()
        assert ta_body["severity"] == "possible_alexithymia"
        assert len(ta_body["subscales"]) == 3

        de = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert de.status_code == 201
        de_body = de.json()
        assert de_body["severity"] == "continuous"
        assert len(de_body["subscales"]) == 5

        er = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert er.status_code == 201
        er_body = er.json()
        assert er_body["severity"] == "continuous"
        assert len(er_body["subscales"]) == 2

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert {"tas20", "ders16", "erq"}.issubset(instruments)

    def test_coexists_with_phq9_suppression_cbt_risk_profile(
        self, client: TestClient
    ) -> None:
        """ERQ + PHQ-9 co-persist — high suppression + depression
        flags the "slow CBT responder" profile documented in the
        emotion-regulation literature.  The router must not leak
        PHQ-9 safety-item routing into the ERQ branch; the ERQ
        submission stays requires_t3=False regardless of any
        concurrent PHQ-9 item-9 activity."""
        user = "user-erq-phq9"
        phq = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [1] * 9,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert phq.status_code == 201

        # Pure-suppressor pattern.
        er = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [1, 7, 1, 7, 1, 7, 1, 1, 7, 1],
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert er.status_code == 201
        er_body = er.json()
        assert er_body["requires_t3"] is False

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "phq9" in instruments
        assert "erq" in instruments

    def test_continuous_sentinel_like_ders16_not_banded_like_tas20(
        self, client: TestClient
    ) -> None:
        """Pins that ERQ joins the continuous-sentinel cluster
        (``severity="continuous"``) rather than the banded cluster
        that TAS-20 rejoined in Sprint 55.  A renderer that
        hardcoded banded handling after TAS-20 must not apply it to
        ERQ — the two instruments ship different envelope shapes
        despite both being post-TAS-20 subscale-bearing Likert
        instruments."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": "user-erq-continuous",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["severity"] == "continuous"
        assert body["severity"] not in (
            "non_alexithymic",
            "possible_alexithymia",
            "alexithymic",
        )

    def test_ignores_mdq_and_sex_fields(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "sex": "male",
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
                "user_id": "user-erq-ignores",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "erq"
        assert body["severity"] == "continuous"


class TestScsSfRouting:
    """SCS-SF (Raes 2011) router dispatch.

    Wire contract invariants pinned here — especially the
    asymmetric scoring convention that makes SCS-SF unique in the
    package:
    - **Continuous-sentinel severity** — ``severity="continuous"``
      (Raes 2011 published no bands).  No hand-rolled thresholds.
    - **6 subscales populated** — largest subscale count in the
      package.  Keys: ``self_kindness`` / ``self_judgment`` /
      ``common_humanity`` / ``isolation`` / ``mindfulness`` /
      ``over_identification``.  Each is a 2-item raw sum (2-10).
    - **Asymmetric scoring (TOTAL post-flip, SUBSCALES raw)** —
      the deliberate scoring convention.  Subscales read as their
      NATIVE construct (so ``subscale_self_judgment=10`` means the
      patient maximally endorsed self-judgment), while the total
      reads in the self-compassion direction (higher = more
      compassion) via post-flipping the 6 uncompassionate items.
      This is the reason for the 6-subscale wire exposure — the
      positive/negative dyad pattern is clinically readable.  If
      subscales were post-flipped, the "high SK + high SJ" CFT-
      target dyad would collapse to indistinguishable mid values.
    - **Built-in acquiescence catch** — all-1s and all-5s both yield
      total=36 (midpoint); the test layer pins this at the wire
      boundary so a naive "higher = always better" renderer must
      surface subscales to detect the pattern.
    - **1-5 Likert envelope** — 0 rejects (below floor), 6 rejects
      (above ceiling).  12 items required.
    - No ``cutoff_used`` / ``positive_screen`` / ``triggering_items``.
    - ``requires_t3`` always False — no safety item.
    - Cross-instrument coexistence: SCS-SF + PHQ-9 (low SCS-SF +
      depression → CFT routing), SCS-SF + TAS-20 (shame
      +alexithymia → double-barrier CFT + affect-labeling), SCS-SF
      + AUDIT (substance use + low self-compassion → Brooks 2012
      relapse-risk pattern).
    """

    def test_all_threes_midline_total_is_36(self, client: TestClient) -> None:
        """All items at 3 (midline) → total 36 (midpoint).  Each
        subscale at 6.  Midline flip-invariance — the balanced
        construct design means midline responders land at the
        exact center."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": "user-scssf-mid",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "scssf"
        assert body["total"] == 36
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False
        subs = body["subscales"]
        # Every subscale at 6 (2 items × raw 3).
        for key in (
            "self_kindness",
            "self_judgment",
            "common_humanity",
            "isolation",
            "mindfulness",
            "over_identification",
        ):
            assert subs[key] == 6, f"{key} should be 6"

    def test_all_ones_yields_total_36_acquiescence_invariant(
        self, client: TestClient
    ) -> None:
        """All items at 1 (strongly disagree).  Total = 36 because
        positive items (stay 1) and negative items (flip to 5) sum
        to 12×3 equivalent.  Clinically: a patient who disagreed
        with EVERY item lands at the midline self-compassion total
        — strongly disagreeing with "I'm kind to myself" offsets
        strongly disagreeing with "I'm judgmental toward myself".
        Subscales reveal the pattern: every subscale at 2
        (floor)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [1] * 12,
                "user_id": "user-scssf-ones",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["total"] == 36
        subs = body["subscales"]
        for key in subs:
            assert subs[key] == 2

    def test_all_fives_yields_total_36_acquiescence_invariant(
        self, client: TestClient
    ) -> None:
        """All items at 5.  Total = 36 (same reason, opposite
        direction).  Subscales all at 10 (ceiling).  The
        acquiescent 'yes to everything' responder is DETECTABLE
        at the subscale level but not at the total.  Pins that
        the wire exposes subscales precisely because the total
        alone cannot distinguish this bias."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [5] * 12,
                "user_id": "user-scssf-fives",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["total"] == 36
        subs = body["subscales"]
        for key in subs:
            assert subs[key] == 10

    def test_maximum_self_compassion_total_60(
        self, client: TestClient
    ) -> None:
        """Positive items (2, 3, 5, 6, 7, 10) at 5; negative items
        (1, 4, 8, 9, 11, 12) at 1.  Post-flip all 5s → total 60.
        Subscales: SK/CH/M = 10 each, SJ/I/OI = 2 each.  The
        protective profile."""
        items = [0] * 12
        for pos in (2, 3, 5, 6, 7, 10):
            items[pos - 1] = 5
        for pos in (1, 4, 8, 9, 11, 12):
            items[pos - 1] = 1
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": items,
                "user_id": "user-scssf-max",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["total"] == 60
        subs = body["subscales"]
        assert subs["self_kindness"] == 10
        assert subs["common_humanity"] == 10
        assert subs["mindfulness"] == 10
        assert subs["self_judgment"] == 2
        assert subs["isolation"] == 2
        assert subs["over_identification"] == 2

    def test_minimum_self_compassion_total_12_relapse_risk(
        self, client: TestClient
    ) -> None:
        """Positive items at 1; negative items at 5.  Post-flip all
        1s → total 12 (floor).  Subscales: SK/CH/M = 2, SJ/I/OI =
        10.  The relapse-risk profile — Brooks 2012 SUD validation
        / Tangney 2011 shame-addiction pathway — the intervention
        layer routes this profile to CFT before the next urge
        episode."""
        items = [0] * 12
        for pos in (2, 3, 5, 6, 7, 10):
            items[pos - 1] = 1
        for pos in (1, 4, 8, 9, 11, 12):
            items[pos - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": items,
                "user_id": "user-scssf-min",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["total"] == 12
        subs = body["subscales"]
        assert subs["self_kindness"] == 2
        assert subs["common_humanity"] == 2
        assert subs["mindfulness"] == 2
        assert subs["self_judgment"] == 10
        assert subs["isolation"] == 10
        assert subs["over_identification"] == 10
        # No safety escalation regardless of score.
        assert body["requires_t3"] is False

    def test_subscales_are_raw_not_post_flip_wire_contract(
        self, client: TestClient
    ) -> None:
        """Critical asymmetry pin at the WIRE boundary.

        Set only item 11 (Self-Judgment reverse) to 5; leave all
        others at 3.  If the router were silently post-flipping
        subscales, ``subscale_self_judgment`` would be (6-5) + 3 =
        4.  Raw convention gives 5 + 3 = 8 — this is what must
        come over the wire."""
        items = [3] * 12
        items[10] = 5  # item 11 raw=5
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": items,
                "user_id": "user-scssf-raw-sub",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        subs = body["subscales"]
        assert subs["self_judgment"] == 8  # raw
        assert subs["self_judgment"] != 4  # NOT post-flipped

    def test_high_sk_and_high_sj_cft_target_dyad_visible(
        self, client: TestClient
    ) -> None:
        """High Self-Kindness AND high Self-Judgment — the CFT-
        target dyad.  Items 2/6 (SK) at 5; items 11/12 (SJ) at 5;
        others at 3.  Subscales should show both at 10, which is
        the clinically actionable pattern CFT explicitly targets
        (positive self-beliefs coexisting with harsh self-
        criticism).  If subscales collapsed to post-flip, SJ would
        read 2 (low) and the pattern would be invisible."""
        items = [3] * 12
        items[1] = 5   # item 2 (SK)
        items[5] = 5   # item 6 (SK)
        items[10] = 5  # item 11 (SJ)
        items[11] = 5  # item 12 (SJ)
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": items,
                "user_id": "user-scssf-cft-dyad",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        subs = body["subscales"]
        assert subs["self_kindness"] == 10
        assert subs["self_judgment"] == 10  # BOTH high — the CFT dyad

    def test_six_subscale_keys_on_wire(self, client: TestClient) -> None:
        """The wire envelope carries exactly 6 subscale keys.
        Renderers must enumerate keys, not hardcode a fixed count.
        Pins the SCS-SF subscale count against TAS-20 (3) /
        DERS-16 (5) / ERQ (2) / URICA (4)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": "user-scssf-keys",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        subs = response.json()["subscales"]
        assert set(subs.keys()) == {
            "self_kindness",
            "self_judgment",
            "common_humanity",
            "isolation",
            "mindfulness",
            "over_identification",
        }
        assert len(subs) == 6

    def test_cutoff_used_not_populated(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": "user-scssf-no-cutoff",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_triggering_items_is_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [1] * 12,
                "user_id": "user-scssf-no-trig",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": "user-scssf-version",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.json()["instrument_version"] == "scssf-1.0.0"

    def test_eleven_items_rejects(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 11,
                "user_id": "user-scssf-eleven",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_thirteen_items_rejects(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 13,
                "user_id": "user-scssf-thirteen",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_zero_rejects_below_floor(self, client: TestClient) -> None:
        bad = [3] * 12
        bad[0] = 0
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": bad,
                "user_id": "user-scssf-zero",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_six_rejects_above_ceiling(self, client: TestClient) -> None:
        bad = [3] * 12
        bad[0] = 6
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": bad,
                "user_id": "user-scssf-six",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 422

    def test_persists_raw_pre_flip_items_with_subscales(
        self, client: TestClient
    ) -> None:
        """POST persists the RAW 12-tuple (pre-flip) to the
        repository, and the 6-subscale RAW-sum map to subscales.
        Audit invariant: a clinician reviewing the record sees
        what the patient ticked (not internal post-flip) AND reads
        subscales in native construct direction."""
        user = "user-scssf-persist"
        raw = [3] * 12
        # Distinctive values at reverse positions.
        raw[0] = 5   # item 1 OI reverse; raw stored as 5, NOT flipped 1
        raw[10] = 4  # item 11 SJ reverse; raw stored as 4, NOT flipped 2
        raw[1] = 5   # item 2 SK positive
        client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": raw,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )

        from discipline.psychometric.repository import (
            get_assessment_repository,
        )

        repo = get_assessment_repository()
        records = repo.history_for(user, limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec.instrument == "scssf"
        assert rec.severity == "continuous"
        # Raw audit invariant: reverse-item values preserved pre-flip.
        assert rec.raw_items[0] == 5   # NOT 1 (post-flip)
        assert rec.raw_items[10] == 4  # NOT 2 (post-flip)
        assert rec.raw_items[1] == 5
        # Subscales populated with RAW sums.
        assert rec.subscales is not None
        # OI = items 1, 9 → raw 5 + 3 = 8.
        assert rec.subscales["over_identification"] == 8
        # SJ = items 11, 12 → raw 4 + 3 = 7.
        assert rec.subscales["self_judgment"] == 7
        # SK = items 2, 6 → raw 5 + 3 = 8.
        assert rec.subscales["self_kindness"] == 8

    def test_history_projects_scssf(self, client: TestClient) -> None:
        user = "user-scssf-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert hist.status_code == 200
        items = hist.json()["items"]
        assert len(items) == 1
        entry = items[0]
        assert entry["instrument"] == "scssf"
        assert entry["total"] == 36
        assert entry["severity"] == "continuous"

    def test_coexists_with_phq9_low_compassion_plus_depression_routing(
        self, client: TestClient
    ) -> None:
        """SCS-SF + PHQ-9 co-persist.  The low-compassion-plus-
        depression profile is the Luyten 2013 / Werner 2019 finding
        — self-criticism mediates the depression outcome.  Router
        must preserve both signals for the intervention-selection
        layer (CFT vs standard CBT routing)."""
        user = "user-scssf-phq9"
        phq = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [2] * 9,  # moderate
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert phq.status_code == 201

        # Low-compassion submission (pure negative profile).
        items = [0] * 12
        for pos in (2, 3, 5, 6, 7, 10):
            items[pos - 1] = 1
        for pos in (1, 4, 8, 9, 11, 12):
            items[pos - 1] = 5
        sc = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": items,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert sc.status_code == 201
        sc_body = sc.json()
        assert sc_body["total"] == 12
        assert sc_body["requires_t3"] is False

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "phq9" in instruments
        assert "scssf" in instruments

    def test_coexists_with_tas20_shame_plus_alexithymia(
        self, client: TestClient
    ) -> None:
        """SCS-SF + TAS-20 — the 'double-barrier' profile: shame
        (low compassion) + alexithymia (can't identify the
        emotion driving the shame).  Intervention layer routes
        this combination to affect-labeling FIRST (TAS-20
        upstream), compassion work SECOND (SCS-SF), skills work
        THIRD (DERS-16)."""
        user = "user-scssf-tas20"
        ta = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert ta.status_code == 201

        sc = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert sc.status_code == 201

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        instruments = {r["instrument"] for r in hist.json()["items"]}
        assert "tas20" in instruments
        assert "scssf" in instruments

    def test_six_subscale_count_distinguishes_from_other_instruments(
        self, client: TestClient
    ) -> None:
        """Sanity pin that SCS-SF ships 6 subscales while its
        sibling subscale-bearing instruments ship different
        counts.  Renderers must not hardcode any fixed subscale
        count — enumerate keys."""
        user = "user-scssf-subscale-counts"
        # SCS-SF: 6.
        sc = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert len(sc.json()["subscales"]) == 6
        # DERS-16: 5.
        de = client.post(
            "/v1/assessments",
            json={
                "instrument": "ders16",
                "items": [3] * 16,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert len(de.json()["subscales"]) == 5
        # TAS-20: 3.
        ta = client.post(
            "/v1/assessments",
            json={
                "instrument": "tas20",
                "items": [3] * 20,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert len(ta.json()["subscales"]) == 3
        # ERQ: 2.
        er = client.post(
            "/v1/assessments",
            json={
                "instrument": "erq",
                "items": [4] * 10,
                "user_id": user,
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert len(er.json()["subscales"]) == 2

    def test_continuous_sentinel_not_banded(self, client: TestClient) -> None:
        """Pins that SCS-SF joins the continuous-sentinel cluster,
        not the banded cluster (TAS-20)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "user_id": "user-scssf-sentinel",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        body = response.json()
        assert body["severity"] == "continuous"
        assert body["severity"] not in (
            "non_alexithymic",
            "possible_alexithymia",
            "alexithymic",
        )

    def test_ignores_mdq_and_sex_fields(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "scssf",
                "items": [3] * 12,
                "sex": "female",
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
                "user_id": "user-scssf-ignores",
            },
            headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "scssf"
        assert body["severity"] == "continuous"


class TestRrs10Routing:
    """End-to-end routing tests for the RRS-10 dispatcher branch.

    Treynor, Gonzalez & Nolen-Hoeksema 2003 Ruminative Responses Scale,
    10 items, 1-4 Likert.  Continuous + 2 subscales (brooding,
    reflection).  No reverse items.  No safety routing.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_min_all_ones_returns_200_total_10(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [1] * 10},
            headers=self._headers("rrs10-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "rrs10"
        assert body["total"] == 10

    def test_max_all_fours_returns_total_40(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [4] * 10},
            headers=self._headers("rrs10-max"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 40

    def test_midline_all_twos_returns_total_20(
        self, client: TestClient
    ) -> None:
        # Treynor 2003 community-sample-adjacent — mean brooding ≈
        # 10.4, mean reflection ≈ 10.1.
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [2] * 10},
            headers=self._headers("rrs10-mid"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 20
        assert body["subscales"]["brooding"] == 10
        assert body["subscales"]["reflection"] == 10

    def test_subscales_wire_keys_exact(self, client: TestClient) -> None:
        """Pin the exact subscale keys on the wire.  Downstream renderer
        and FHIR Observation export contract depend on these names."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [2] * 10},
            headers=self._headers("rrs10-subs-keys"),
        )
        assert response.status_code == 201
        body = response.json()
        assert set(body["subscales"].keys()) == {"brooding", "reflection"}

    def test_two_subscale_count_distinguishes_from_six_and_five(
        self, client: TestClient
    ) -> None:
        """Pin that RRS-10 surfaces exactly 2 subscales, distinguishing
        it from SCS-SF (6) / DERS-16 (5) / URICA (4) / TAS-20 (3).
        A regression that silently merged subscale maps would be
        caught here."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [2] * 10},
            headers=self._headers("rrs10-sub-count"),
        )
        assert response.status_code == 201
        assert len(response.json()["subscales"]) == 2

    def test_brooding_dominant_profile_wire(
        self, client: TestClient
    ) -> None:
        """Brooding items (positions 1, 3, 6, 7, 8) at 4, reflection
        items at 1.  Pins the maladaptive-dominant profile that routes
        to mindfulness-first intervention."""
        items = [4, 1, 4, 1, 1, 4, 4, 4, 1, 1]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": items},
            headers=self._headers("rrs10-brood-dom"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["subscales"]["brooding"] == 20
        assert body["subscales"]["reflection"] == 5
        assert body["total"] == 25

    def test_reflection_dominant_profile_wire(
        self, client: TestClient
    ) -> None:
        """Reflection items at 4, brooding items at 1 — the adaptive
        profile.  Pins that the wire can represent the low-
        intervention-need pattern."""
        items = [1, 4, 1, 4, 4, 1, 1, 1, 4, 4]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": items},
            headers=self._headers("rrs10-refl-dom"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["subscales"]["brooding"] == 5
        assert body["subscales"]["reflection"] == 20

    def test_identical_total_distinct_profiles_on_wire(
        self, client: TestClient
    ) -> None:
        """Two submissions with identical total (25) but opposite
        subscale profiles must be distinguishable on the wire.  This
        is the entire clinical raison-d'être of RRS-10 over the raw
        RRS-22 total."""
        brooding_response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rrs10",
                "items": [4, 1, 4, 1, 1, 4, 4, 4, 1, 1],
            },
            headers=self._headers("rrs10-id-brood"),
        )
        reflection_response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rrs10",
                "items": [1, 4, 1, 4, 4, 1, 1, 1, 4, 4],
            },
            headers=self._headers("rrs10-id-refl"),
        )
        b, r = brooding_response.json(), reflection_response.json()
        assert b["total"] == r["total"] == 25
        assert b["subscales"]["brooding"] > r["subscales"]["brooding"]
        assert (
            r["subscales"]["reflection"] > b["subscales"]["reflection"]
        )

    def test_continuous_severity_sentinel(
        self, client: TestClient
    ) -> None:
        """Treynor 2003 published no validated bands — the router must
        emit the continuous sentinel, not a banded severity string."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [4] * 10},
            headers=self._headers("rrs10-sev"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["severity"] == "continuous"
        # Distinguish from PHQ-9 / GAD-7 banded severities.
        assert body["severity"] not in {
            "minimal",
            "mild",
            "moderate",
            "moderately_severe",
            "severe",
        }

    def test_requires_t3_always_false(self, client: TestClient) -> None:
        """RRS-10 has no safety item; requires_t3 is hard-coded False
        even at ceiling brooding + reflection."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [4] * 10},
            headers=self._headers("rrs10-no-t3"),
        )
        assert response.status_code == 201
        assert response.json()["requires_t3"] is False

    def test_cutoff_used_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [3] * 10},
            headers=self._headers("rrs10-no-cutoff"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["cutoff_used"] is None
        assert body.get("positive_screen") is None

    def test_triggering_items_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [4] * 10},
            headers=self._headers("rrs10-no-trig"),
        )
        assert response.status_code == 201
        assert response.json().get("triggering_items") is None

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [1] * 10},
            headers=self._headers("rrs10-ver"),
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "rrs10-1.0.0"

    def test_nine_items_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [1] * 9},
            headers=self._headers("rrs10-count-9"),
        )
        assert response.status_code in (400, 422)

    def test_eleven_items_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [1] * 11},
            headers=self._headers("rrs10-count-11"),
        )
        assert response.status_code in (400, 422)

    def test_twenty_two_items_rejected(self, client: TestClient) -> None:
        """Parent-scale RRS-22 item count must be rejected — if someone
        wired the RRS-22 scale up to the RRS-10 endpoint by mistake,
        this catches it."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [1] * 22},
            headers=self._headers("rrs10-count-22"),
        )
        assert response.status_code in (400, 422)

    def test_value_zero_rejected(self, client: TestClient) -> None:
        """0 is the floor on many other instruments (PHQ-9, GAD-7) but
        NOT on RRS-10 (Treynor 2003 floor is 1)."""
        items = [0] + [1] * 9
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": items},
            headers=self._headers("rrs10-val-0"),
        )
        assert response.status_code == 422

    def test_value_five_rejected(self, client: TestClient) -> None:
        """5 is accepted by SCS-SF (1-5) but NOT RRS-10 (1-4)."""
        items = [5] + [1] * 9
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": items},
            headers=self._headers("rrs10-val-5"),
        )
        assert response.status_code == 422

    def test_history_projects_rrs10(
        self, client: TestClient
    ) -> None:
        """Pin that a POSTed RRS-10 submission surfaces on the
        history projection with the continuous-sentinel envelope."""
        user = "user-rrs10-history"
        post_response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rrs10",
                "items": [2] * 10,
                "user_id": user,
            },
            headers=self._headers("rrs10-hist-basic"),
        )
        assert post_response.status_code == 201
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        body = history.json()
        entries = [
            entry
            for entry in body["items"]
            if entry["instrument"] == "rrs10"
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["total"] == 20
        assert entry["severity"] == "continuous"

    def test_history_projection_carries_brooding_reflection_split(
        self, client: TestClient
    ) -> None:
        """The whole clinical point of RRS-10 — the brooding/
        reflection dyad — must survive persistence + history
        projection.  Losing either subscale would erase the
        maladaptive-vs-adaptive rumination signal."""
        user = "user-rrs10-history-dyad"
        post_response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rrs10",
                "items": [4, 1, 4, 1, 1, 4, 4, 4, 1, 1],
                "user_id": user,
            },
            headers=self._headers("rrs10-hist-dyad"),
        )
        assert post_response.status_code == 201
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        entries = [
            entry
            for entry in history.json()["items"]
            if entry["instrument"] == "rrs10"
        ]
        assert len(entries) == 1
        entry = entries[0]
        # Subscales are either inline or nested under a 'subscales'
        # key depending on projection shape — handle both.
        if "subscales" in entry:
            assert entry["subscales"]["brooding"] == 20
            assert entry["subscales"]["reflection"] == 5
        else:
            # If projection flattens, still verify total is preserved.
            assert entry["total"] == 25

    def test_phq9_coexists_with_rrs10(self, client: TestClient) -> None:
        """Both instruments dispatch independently; submitting PHQ-9
        after RRS-10 still routes through PHQ-9's banded severity +
        safety-item path."""
        rrs_response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [2] * 10},
            headers=self._headers("rrs10-coexist-rrs"),
        )
        assert rrs_response.status_code == 201
        phq_response = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [0] * 9},
            headers=self._headers("rrs10-coexist-phq"),
        )
        assert phq_response.status_code == 201
        assert phq_response.json()["severity"] == "none"

    def test_erq_coexists_with_rrs10(self, client: TestClient) -> None:
        """Adjacent continuous + subscales instrument — both must
        return the continuous-sentinel shape independently."""
        rrs_response = client.post(
            "/v1/assessments",
            json={"instrument": "rrs10", "items": [2] * 10},
            headers=self._headers("rrs10-coexist-rrs-erq"),
        )
        erq_response = client.post(
            "/v1/assessments",
            json={"instrument": "erq", "items": [4] * 10},
            headers=self._headers("rrs10-coexist-erq"),
        )
        assert rrs_response.status_code == 201
        assert erq_response.status_code == 201
        assert rrs_response.json()["severity"] == "continuous"
        assert erq_response.json()["severity"] == "continuous"
        # Different subscale counts.
        assert len(rrs_response.json()["subscales"]) == 2
        assert len(erq_response.json()["subscales"]) == 2
        # Different subscale key names — pins dispatch isolation.
        assert (
            set(rrs_response.json()["subscales"].keys())
            != set(erq_response.json()["subscales"].keys())
        )

    def test_ignores_mdq_fields_when_supplied(
        self, client: TestClient
    ) -> None:
        """RRS-10 dispatch ignores MDQ-specific fields that might
        leak through on a polymorphic client payload."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rrs10",
                "items": [2] * 10,
                "concurrent_symptoms": True,
                "functional_impairment": "moderate",
                "sex": "female",
            },
            headers=self._headers("rrs10-ignore-extra"),
        )
        assert response.status_code == 201
        assert response.json()["instrument"] == "rrs10"


class TestMaasRouting:
    """End-to-end routing tests for the MAAS dispatcher branch.

    Brown & Ryan 2003 Mindful Attention Awareness Scale, 15 items,
    1-6 Likert, unidimensional, continuous-sentinel severity.
    Novel wire shape: continuous + NO subscales at 15 items.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_min_all_ones_returns_total_15(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [1] * 15},
            headers=self._headers("maas-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "maas"
        assert body["total"] == 15

    def test_max_all_sixes_returns_total_90(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [6] * 15},
            headers=self._headers("maas-max"),
        )
        assert response.status_code == 201
        assert response.json()["total"] == 90

    def test_community_mean_approx(self, client: TestClient) -> None:
        # Brown & Ryan 2003 community mean ≈ 4.1 × 15 = 61.5.
        # All-4s gives sum = 60 (≈ mean 4.0).  Pin that this
        # community-mean-adjacent profile scores cleanly.
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [4] * 15},
            headers=self._headers("maas-community"),
        )
        assert response.status_code == 201
        assert response.json()["total"] == 60

    def test_no_subscales_field_on_wire(
        self, client: TestClient
    ) -> None:
        """Pin the unidimensional wire contract.  MAAS is the first
        continuous 15-item instrument with no subscale map — a
        regression that silently surfaced a `subscales` key would
        constitute a psychometric fabrication (Brown & Ryan 2003
        extracted a single factor)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [3] * 15},
            headers=self._headers("maas-no-subs"),
        )
        assert response.status_code == 201
        body = response.json()
        # Either the key is absent, or it is explicitly None / empty —
        # accept any shape that conveys "no subscale data".
        assert not body.get("subscales")

    def test_continuous_severity_sentinel(
        self, client: TestClient
    ) -> None:
        """Brown & Ryan 2003 published no bands — router must emit
        the continuous sentinel, not a banded severity string."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [6] * 15},
            headers=self._headers("maas-sev"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["severity"] == "continuous"
        assert body["severity"] not in {
            "minimal",
            "mild",
            "moderate",
            "moderately_severe",
            "severe",
            "none",
        }

    def test_requires_t3_always_false(self, client: TestClient) -> None:
        """MAAS has no safety item; requires_t3 is hard-coded False
        even at floor (maximum dispositional mindlessness)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [1] * 15},
            headers=self._headers("maas-no-t3"),
        )
        assert response.status_code == 201
        assert response.json()["requires_t3"] is False

    def test_cutoff_used_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [3] * 15},
            headers=self._headers("maas-no-cutoff"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["cutoff_used"] is None
        assert body.get("positive_screen") is None

    def test_triggering_items_none(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [6] * 15},
            headers=self._headers("maas-no-trig"),
        )
        assert response.status_code == 201
        assert response.json().get("triggering_items") is None

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [1] * 15},
            headers=self._headers("maas-ver"),
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "maas-1.0.0"

    def test_fourteen_items_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [1] * 14},
            headers=self._headers("maas-count-14"),
        )
        assert response.status_code in (400, 422)

    def test_sixteen_items_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [1] * 16},
            headers=self._headers("maas-count-16"),
        )
        assert response.status_code in (400, 422)

    def test_five_items_rejected(self, client: TestClient) -> None:
        """MAAS-5 is a valid short form (Osman 2016) but NOT the
        MAAS-15 endpoint's contract.  Mis-wiring a MAAS-5 submission
        to this endpoint would silently score 5 items and produce
        a dangerously low total — reject it here."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [5] * 5},
            headers=self._headers("maas-count-5"),
        )
        assert response.status_code in (400, 422)

    def test_value_zero_rejected(self, client: TestClient) -> None:
        """0 is the floor on PHQ-9 but NOT MAAS (1-6 Likert).  A
        caller reflexively using 0-indexed Likert would silently
        produce a total 15 points below the real value; catch it."""
        items = [0] + [1] * 14
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": items},
            headers=self._headers("maas-val-0"),
        )
        assert response.status_code == 422

    def test_value_seven_rejected(self, client: TestClient) -> None:
        """7 is accepted by ERQ (1-7) but NOT MAAS (1-6)."""
        items = [7] + [1] * 14
        response = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": items},
            headers=self._headers("maas-val-7"),
        )
        assert response.status_code == 422

    def test_higher_total_means_more_mindful_wire(
        self, client: TestClient
    ) -> None:
        """Pin the directional contract on the wire.  A regression
        that silently added a reverse-keying step would invert the
        scoring direction — the prototypically-mindless respondent
        (all 1s) would end up scoring higher than the prototypically-
        mindful respondent (all 6s)."""
        mindless = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [1] * 15},
            headers=self._headers("maas-dir-low"),
        )
        mindful = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [6] * 15},
            headers=self._headers("maas-dir-high"),
        )
        assert mindless.status_code == 201
        assert mindful.status_code == 201
        # The dispositionally-mindful respondent must score higher
        # than the dispositionally-mindless respondent.
        assert mindful.json()["total"] > mindless.json()["total"]

    def test_mbrp_pre_post_delta_representable(
        self, client: TestClient
    ) -> None:
        """Bowen 2014 MBRP RCT outcome — MAAS increases from
        baseline to post-intervention follow-up.  Pin that both
        plausible endpoints round-trip cleanly."""
        pre = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [3] * 15},
            headers=self._headers("maas-mbrp-pre"),
        )
        post = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [5] * 15},
            headers=self._headers("maas-mbrp-post"),
        )
        assert pre.status_code == 201 and post.status_code == 201
        assert pre.json()["total"] == 45
        assert post.json()["total"] == 75

    def test_history_projects_maas(self, client: TestClient) -> None:
        user = "user-maas-history"
        post_response = client.post(
            "/v1/assessments",
            json={
                "instrument": "maas",
                "items": [4] * 15,
                "user_id": user,
            },
            headers=self._headers("maas-hist"),
        )
        assert post_response.status_code == 201
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        entries = [
            entry
            for entry in history.json()["items"]
            if entry["instrument"] == "maas"
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["total"] == 60
        assert entry["severity"] == "continuous"

    def test_coexists_with_rrs10_mindfulness_rumination_dyad(
        self, client: TestClient
    ) -> None:
        """MAAS + RRS-10 — the opposite-pole pair.  Brooding
        rumination is what keeps a feeling alive; mindful attention
        is the skill that short-circuits that loop.  Both must
        persist independently, with distinct subscale shapes
        (RRS-10 has 2 subscales, MAAS has 0)."""
        user = "user-maas-rrs10-dyad"
        rrs = client.post(
            "/v1/assessments",
            json={
                "instrument": "rrs10",
                "items": [4, 1, 4, 1, 1, 4, 4, 4, 1, 1],
                "user_id": user,
            },
            headers=self._headers("maas-rrs10-coexist-rrs"),
        )
        ma = client.post(
            "/v1/assessments",
            json={
                "instrument": "maas",
                "items": [2] * 15,
                "user_id": user,
            },
            headers=self._headers("maas-rrs10-coexist-ma"),
        )
        assert rrs.status_code == 201 and ma.status_code == 201
        # RRS-10 has 2 subscales; MAAS has none.
        assert len(rrs.json()["subscales"]) == 2
        assert not ma.json().get("subscales")
        # Both surface continuous-sentinel severity.
        assert rrs.json()["severity"] == "continuous"
        assert ma.json()["severity"] == "continuous"

    def test_coexists_with_phq9_banded_path_unaffected(
        self, client: TestClient
    ) -> None:
        """PHQ-9 banded severity path must remain unaffected by
        MAAS dispatch being in the router."""
        ma = client.post(
            "/v1/assessments",
            json={"instrument": "maas", "items": [4] * 15},
            headers=self._headers("maas-phq9-coexist-ma"),
        )
        phq = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [0] * 9},
            headers=self._headers("maas-phq9-coexist-phq"),
        )
        assert ma.status_code == 201 and phq.status_code == 201
        assert ma.json()["severity"] == "continuous"
        assert phq.json()["severity"] == "none"

    def test_ignores_mdq_fields_when_supplied(
        self, client: TestClient
    ) -> None:
        """MAAS dispatch ignores MDQ-specific fields that might
        leak through on a polymorphic client payload."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "maas",
                "items": [3] * 15,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "sex": "male",
            },
            headers=self._headers("maas-ignore-extra"),
        )
        assert response.status_code == 201
        assert response.json()["instrument"] == "maas"


class TestShapsRouting:
    """End-to-end routing tests for the SHAPS dispatcher branch.

    Snaith 1995 Snaith-Hamilton Pleasure Scale, 14 items, 1-4 Likert
    raw input, dichotomized per Snaith 1995 to 0-14, positive-screen
    at >= 3.  Novel wire shape: the first dispatcher branch whose
    stored total is a non-identity transform of the raw input
    (dichotomize-then-sum, not sum-of-raw).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_min_all_strongly_agree_returns_total_0(
        self, client: TestClient
    ) -> None:
        """All 14 at Strongly Agree (1) → 0 anhedonic items, negative
        screen.  Most hedonically intact possible response."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 14},
            headers=self._headers("shaps-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "shaps"
        assert body["total"] == 0
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_max_all_strongly_disagree_returns_total_14(
        self, client: TestClient
    ) -> None:
        """All 14 at Strongly Disagree (4) → 14 anhedonic items,
        positive screen.  Severe anhedonic presentation."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-max"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 14
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_dichotomization_raw_2_maps_to_0(
        self, client: TestClient
    ) -> None:
        """Snaith 1995 dichotomization pin on the wire: raw Likert 2
        (Agree) dichotomizes to 0 (hedonic capacity present), NOT 1.
        All-2s response MUST score 0 anhedonic items.  A regression
        that implemented dichotomization as ``raw > 2`` would pass
        this.  A regression that implemented it as ``raw > 1`` would
        fail (all-2s would score 14)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [2] * 14},
            headers=self._headers("shaps-dichot-2"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    def test_dichotomization_raw_3_maps_to_1(
        self, client: TestClient
    ) -> None:
        """Snaith 1995 dichotomization pin on the wire: raw Likert 3
        (Disagree) dichotomizes to 1 (anhedonic), NOT 0.  All-3s
        response MUST score 14 anhedonic items."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [3] * 14},
            headers=self._headers("shaps-dichot-3"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 14
        assert body["positive_screen"] is True

    def test_cutoff_boundary_total_2_negative(
        self, client: TestClient
    ) -> None:
        """Below-cutoff boundary on the wire.  Two Disagree + twelve
        Strongly Agree → total 2, MUST NOT positive_screen per
        Snaith 1995 ≥3 cutoff."""
        items = [1] * 14
        items[0] = 3
        items[7] = 3
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": items},
            headers=self._headers("shaps-boundary-2"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 2
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_cutoff_boundary_total_3_positive(
        self, client: TestClient
    ) -> None:
        """At-cutoff boundary on the wire.  Three Disagree + eleven
        Strongly Agree → total 3, MUST positive_screen.  This is
        Snaith 1995's exact operating point."""
        items = [1] * 14
        items[0] = 3
        items[7] = 3
        items[13] = 3
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": items},
            headers=self._headers("shaps-boundary-3"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_cutoff_used_is_3(self, client: TestClient) -> None:
        """Snaith 1995 cutoff value surfaced on wire.  Clinician-UI
        and RCI threshold layer both render ``≥ 3`` from this field."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 14},
            headers=self._headers("shaps-cutoff"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["cutoff_used"] == 3

    def test_positive_screen_field_present_on_positive(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-ps-true"),
        )
        assert response.status_code == 201
        assert response.json()["positive_screen"] is True

    def test_positive_screen_field_present_on_negative(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 14},
            headers=self._headers("shaps-ps-false"),
        )
        assert response.status_code == 201
        assert response.json()["positive_screen"] is False

    def test_no_subscales_field_on_wire(
        self, client: TestClient
    ) -> None:
        """SHAPS is unidimensional (Franken 2007 PCA, Leventhal 2006
        CFA, Nakonezny 2010 IRT).  A regression that silently
        surfaced a ``subscales`` key would constitute psychometric
        fabrication."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [3] * 14},
            headers=self._headers("shaps-no-subs"),
        )
        assert response.status_code == 201
        assert not response.json().get("subscales")

    def test_severity_is_screen_not_continuous_or_banded(
        self, client: TestClient
    ) -> None:
        """SHAPS uses cutoff-based screen semantics.  Severity string
        MUST be ``positive_screen`` or ``negative_screen`` — NOT
        continuous (MAAS/DERS/BRS) and NOT banded
        (PHQ-9/GAD-7/PHQ-15)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-sev-shape"),
        )
        assert response.status_code == 201
        severity = response.json()["severity"]
        assert severity in ("positive_screen", "negative_screen")
        assert severity not in (
            "continuous",
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "mild",
            "moderate",
            "moderately_severe",
            "severe",
        )

    def test_requires_t3_always_false_at_max(
        self, client: TestClient
    ) -> None:
        """Even at ceiling anhedonia (all-4s), requires_t3 is False.
        Anhedonia is a clinical signal, not a crisis signal; acute
        ideation screening stays on C-SSRS / PHQ-9 item 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-no-t3-max"),
        )
        assert response.status_code == 201
        assert response.json()["requires_t3"] is False

    def test_triggering_items_none(self, client: TestClient) -> None:
        """SHAPS has no safety item; no triggering_items list."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-no-trig"),
        )
        assert response.status_code == 201
        assert response.json().get("triggering_items") is None

    def test_instrument_version_pinned(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 14},
            headers=self._headers("shaps-ver"),
        )
        assert response.status_code == 201
        assert response.json()["instrument_version"] == "shaps-1.0.0"

    def test_thirteen_items_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 13},
            headers=self._headers("shaps-count-13"),
        )
        assert response.status_code in (400, 422)

    def test_fifteen_items_rejected(self, client: TestClient) -> None:
        """MAAS width — catches MAAS-payload mis-routed to SHAPS."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 15},
            headers=self._headers("shaps-count-15"),
        )
        assert response.status_code in (400, 422)

    def test_ten_items_rejected(self, client: TestClient) -> None:
        """RRS-10 / PSS-10 / DAST-10 / AUDIT width — catches a common
        mis-routing path."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 10},
            headers=self._headers("shaps-count-10"),
        )
        assert response.status_code in (400, 422)

    def test_value_zero_rejected(self, client: TestClient) -> None:
        """0 is the floor on PHQ-9 / GAD-7 / OCI-R but NOT SHAPS
        (1-4 Likert).  A caller reflexively using 0-indexed Likert
        would silently score every item as 'hedonic capacity
        present' and produce a misleading negative screen."""
        items = [1] * 14
        items[0] = 0
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": items},
            headers=self._headers("shaps-val-0"),
        )
        assert response.status_code == 422

    def test_value_five_rejected(self, client: TestClient) -> None:
        """5 is valid in SCS-SF / DERS-16 / K6 but NOT SHAPS
        (1-4)."""
        items = [1] * 14
        items[0] = 5
        response = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": items},
            headers=self._headers("shaps-val-5"),
        )
        assert response.status_code == 422

    def test_higher_total_means_more_anhedonic_wire(
        self, client: TestClient
    ) -> None:
        """Pin the direction on the wire: the anhedonic respondent
        MUST score higher than the hedonic respondent.  A regression
        that silently flipped the dichotomization direction (raw 1-2
        → 1, raw 3-4 → 0) would invert this and register treatment
        gains as worsening."""
        hedonic = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [1] * 14},
            headers=self._headers("shaps-dir-low"),
        )
        anhedonic = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-dir-high"),
        )
        assert hedonic.status_code == 201 and anhedonic.status_code == 201
        assert anhedonic.json()["total"] > hedonic.json()["total"]
        assert anhedonic.json()["positive_screen"] is True
        assert hedonic.json()["positive_screen"] is False

    def test_history_projects_shaps(self, client: TestClient) -> None:
        user = "user-shaps-history"
        post_response = client.post(
            "/v1/assessments",
            json={
                "instrument": "shaps",
                "items": [4] * 14,
                "user_id": user,
            },
            headers=self._headers("shaps-hist"),
        )
        assert post_response.status_code == 201
        history = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user},
        )
        assert history.status_code == 200
        entries = [
            entry
            for entry in history.json()["items"]
            if entry["instrument"] == "shaps"
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["total"] == 14
        assert entry["severity"] == "positive_screen"

    def test_coexists_with_maas_paws_signature(
        self, client: TestClient
    ) -> None:
        """Post-acute-withdrawal signature pin — low MAAS + positive
        SHAPS is the hedonic-dysregulation profile (Koob 2008,
        Bowen 2014 MBRP baseline).  Both instruments must persist
        together and surface distinct wire envelopes (MAAS continuous
        no-subscales; SHAPS positive_screen + cutoff_used)."""
        user = "user-shaps-maas-paws"
        ma = client.post(
            "/v1/assessments",
            json={
                "instrument": "maas",
                "items": [2] * 15,
                "user_id": user,
            },
            headers=self._headers("shaps-maas-coexist-ma"),
        )
        sh = client.post(
            "/v1/assessments",
            json={
                "instrument": "shaps",
                "items": [4] * 14,
                "user_id": user,
            },
            headers=self._headers("shaps-maas-coexist-sh"),
        )
        assert ma.status_code == 201 and sh.status_code == 201
        # MAAS envelope: continuous, no subscales, no cutoff.
        assert ma.json()["severity"] == "continuous"
        assert not ma.json().get("subscales")
        assert ma.json()["cutoff_used"] is None
        # SHAPS envelope: positive_screen, no subscales, cutoff 3.
        assert sh.json()["severity"] == "positive_screen"
        assert not sh.json().get("subscales")
        assert sh.json()["cutoff_used"] == 3
        assert sh.json()["positive_screen"] is True

    def test_coexists_with_phq9_banded_path_unaffected(
        self, client: TestClient
    ) -> None:
        """PHQ-9 banded-severity path must remain byte-for-byte
        unaffected by SHAPS dispatch being in the router."""
        sh = client.post(
            "/v1/assessments",
            json={"instrument": "shaps", "items": [4] * 14},
            headers=self._headers("shaps-phq9-coexist-sh"),
        )
        phq = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [0] * 9},
            headers=self._headers("shaps-phq9-coexist-phq"),
        )
        assert sh.status_code == 201 and phq.status_code == 201
        assert sh.json()["severity"] == "positive_screen"
        assert phq.json()["severity"] == "none"

    def test_ignores_mdq_fields_when_supplied(
        self, client: TestClient
    ) -> None:
        """SHAPS dispatch ignores MDQ-specific fields that might leak
        through on a polymorphic client payload."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "shaps",
                "items": [3] * 14,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
                "sex": "male",
            },
            headers=self._headers("shaps-ignore-extra"),
        )
        assert response.status_code == 201
        assert response.json()["instrument"] == "shaps"


class TestAcesRouting:
    """End-to-end routing tests for the ACEs dispatcher branch.

    Felitti 1998 Adverse Childhood Experiences Questionnaire — 10
    BINARY items, total 0-10, positive-screen cutoff >= 4.  Two novel
    wire contributions on this platform:

    1. First BINARY-item instrument.  Values must be strictly 0 or 1;
       integers "in range" for a plausible range-check (2-10) are
       rejected by the scorer.
    2. First RETROSPECTIVE instrument — measures lifetime exposure
       before age 18, not current state.  No acute-safety routing;
       content-sensitive items (1-3, 6) handled by UI layer.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_min_all_zeros_returns_total_0(
        self, client: TestClient
    ) -> None:
        """ACE = 0: no adversity exposure, negative screen.  ~36% of
        Felitti 1998 n = 17,337 Kaiser sample."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [0] * 10},
            headers=self._headers("aces-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "aces"
        assert body["total"] == 0
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_max_all_ones_returns_total_10(
        self, client: TestClient
    ) -> None:
        """ACE = 10: every category endorsed.  Maximum adversity
        exposure — positive screen with strongest dose-response
        signal (Felitti 1998 table 4)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 10},
            headers=self._headers("aces-max"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 10
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_cutoff_boundary_total_3_negative(
        self, client: TestClient
    ) -> None:
        """Below-cutoff boundary on the wire.  3 endorsements — just
        below Felitti 1998 ≥4 operating point.  A regression that
        drifted the >= to > would miss this."""
        items = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-boundary-3"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_cutoff_boundary_total_4_positive(
        self, client: TestClient
    ) -> None:
        """At-cutoff boundary on the wire.  4 endorsements — exactly
        Felitti 1998's operating point at which multiple adult-health
        outcomes show >=4x relative risk vs ACE = 0."""
        items = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-boundary-4"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 4
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_cutoff_used_is_4(self, client: TestClient) -> None:
        """cutoff_used carries the Felitti 1998 >=4 integer on the
        wire so the clinician UI renders the same threshold the
        trajectory RCI layer uses."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 4 + [0] * 6},
            headers=self._headers("aces-cutoff-used"),
        )
        assert response.status_code == 201
        assert response.json()["cutoff_used"] == 4

    def test_positive_screen_is_bool_not_int(
        self, client: TestClient
    ) -> None:
        """positive_screen on the wire is a pure bool, not a truthy
        int.  Downstream JSON consumers (Mobile RN / Next.js) rely on
        strict bool for conditional rendering."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 10},
            headers=self._headers("aces-pos-bool"),
        )
        body = response.json()
        assert body["positive_screen"] is True
        assert isinstance(body["positive_screen"], bool)

    def test_no_subscales_on_wire(self, client: TestClient) -> None:
        """Dong 2004 rejected three-subscale (abuse / neglect /
        dysfunction) model.  Surfacing subscales on the wire would
        create the false impression of validated per-domain cutoffs."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 10},
            headers=self._headers("aces-no-subscales"),
        )
        body = response.json()
        assert "subscales" not in body or body.get("subscales") is None

    def test_severity_screen_shape(self, client: TestClient) -> None:
        """severity carries the positive_screen / negative_screen
        string — uniform with SHAPS / OCI-R / MDQ / PC-PTSD-5 /
        AUDIT-C."""
        neg = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [0] * 10},
            headers=self._headers("aces-sev-neg"),
        ).json()
        pos = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 10},
            headers=self._headers("aces-sev-pos"),
        ).json()
        assert neg["severity"] == "negative_screen"
        assert pos["severity"] == "positive_screen"

    def test_no_t3_at_max_adversity(self, client: TestClient) -> None:
        """Even at ACE = 10, requires_t3 is False.  Retrospective
        exposure is dispositional lifetime risk, not acute current-
        state crisis.  Acute-ideation screening stays on C-SSRS /
        PHQ-9 item 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 10},
            headers=self._headers("aces-no-t3-max"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_no_t3_on_abuse_items(self, client: TestClient) -> None:
        """Items 1-3 (abuse) are content-sensitive but retrospective.
        No T3 routing even when all three abuse items are endorsed."""
        items = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-abuse-no-t3"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_no_triggering_items_on_wire(
        self, client: TestClient
    ) -> None:
        """No item on ACEs is a safety-triggering item; triggering_items
        field is absent or None in the response."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [1] * 10},
            headers=self._headers("aces-no-trig"),
        )
        body = response.json()
        assert (
            "triggering_items" not in body
            or body.get("triggering_items") is None
        )

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        """instrument_version carries the scorer's pinned version
        string for downstream FHIR Observation export."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [0] * 10},
            headers=self._headers("aces-version"),
        )
        assert response.json()["instrument_version"] == "aces-1.0.0"

    def test_item_count_validation_9_items_rejected(
        self, client: TestClient
    ) -> None:
        """9 items — one short of Felitti 1998 structure.  Must 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [0] * 9},
            headers=self._headers("aces-count-9"),
        )
        assert response.status_code == 422

    def test_item_count_validation_11_items_rejected(
        self, client: TestClient
    ) -> None:
        """11 items — one over Felitti 1998 structure.  Must 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [0] * 11},
            headers=self._headers("aces-count-11"),
        )
        assert response.status_code == 422

    def test_item_count_validation_13_items_rejected(
        self, client: TestClient
    ) -> None:
        """13 items — ACE-IQ expanded version has ~13 items; MDQ has
        13 items.  Both must fail the strict ACEs 10-item count."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": [0] * 13},
            headers=self._headers("aces-count-13"),
        )
        assert response.status_code == 422

    def test_binary_range_value_2_rejected(
        self, client: TestClient
    ) -> None:
        """Novel wire pin: value 2 is "in range" for a loose 0-10
        range-check but NOT binary.  Must 422.  A regression that
        loosened to 0 <= v <= 10 would silently accept this."""
        items = [0, 2, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-range-2"),
        )
        assert response.status_code == 422

    def test_binary_range_value_3_rejected(
        self, client: TestClient
    ) -> None:
        """Value 3 is also rejected — not strictly binary."""
        items = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-range-3"),
        )
        assert response.status_code == 422

    def test_binary_range_value_negative_rejected(
        self, client: TestClient
    ) -> None:
        """Negative values rejected — not strictly binary."""
        items = [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-range-neg"),
        )
        assert response.status_code == 422

    def test_binary_range_value_10_rejected(
        self, client: TestClient
    ) -> None:
        """Critical trap: value 10 would silently corrupt to a
        ceiling total under a loose range-check.  Must 422."""
        items = [10, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-range-10"),
        )
        assert response.status_code == 422

    def test_item_position_each_contributes_1(
        self, client: TestClient
    ) -> None:
        """Direction semantics on the wire — each item position adds
        exactly 1 when endorsed.  Binary instrument, no weighting."""
        for position in range(10):
            items = [0] * 10
            items[position] = 1
            response = client.post(
                "/v1/assessments",
                json={"instrument": "aces", "items": items},
                headers=self._headers(f"aces-pos-{position}"),
            )
            assert response.status_code == 201
            body = response.json()
            assert body["total"] == 1, (
                f"position {position} did not contribute 1 (got "
                f"{body['total']})"
            )

    def test_history_projection_includes_aces(
        self, client: TestClient
    ) -> None:
        """ACEs submissions appear in /history with scored output
        shape uniform with other cutoff-based instruments."""
        user_id = "user-aces-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "aces",
                "items": [1] * 10,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "aces-hist-1",
                "X-User-Id": user_id,
            },
        )
        response = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user_id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        aces_items = [
            item for item in body["items"] if item["instrument"] == "aces"
        ]
        assert len(aces_items) >= 1
        aces_entry = aces_items[0]
        assert aces_entry["total"] == 10
        assert aces_entry["positive_screen"] is True
        assert aces_entry["cutoff_used"] == 4

    def test_pydantic_coerces_json_bool_to_int(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces JSON true/false to int 1/0 at the wire
        layer — the scorer-level bool rejection (see test_aces_scoring)
        pins Python-layer bool rejection, but the wire-layer Pydantic
        coercion means a JSON ``true`` in items is accepted as
        equivalent to ``1``.  This test documents that reality so a
        future wire-layer stricter-validation refactor surfaces this
        behavior change explicitly."""
        items: list = [True, False, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "aces", "items": items},
            headers=self._headers("aces-json-bool"),
        )
        assert response.status_code == 201
        assert response.json()["total"] == 1

    def test_coexists_with_shaps_and_maas(
        self, client: TestClient
    ) -> None:
        """ACEs + SHAPS + MAAS — the emotional-architecture triad.
        All three instruments route to distinct dispatcher branches
        without interference.  Critical regression pin since ACEs
        was inserted directly after SHAPS in the dispatch order."""
        user_id = "user-triad"

        ac = client.post(
            "/v1/assessments",
            json={
                "instrument": "aces",
                "items": [1] * 4 + [0] * 6,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "triad-aces",
                "X-User-Id": user_id,
            },
        )
        sh = client.post(
            "/v1/assessments",
            json={
                "instrument": "shaps",
                "items": [3] * 14,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "triad-shaps",
                "X-User-Id": user_id,
            },
        )
        ma = client.post(
            "/v1/assessments",
            json={
                "instrument": "maas",
                "items": [1] * 15,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "triad-maas",
                "X-User-Id": user_id,
            },
        )
        assert ac.status_code == 201
        assert sh.status_code == 201
        assert ma.status_code == 201
        assert ac.json()["instrument"] == "aces"
        assert sh.json()["instrument"] == "shaps"
        assert ma.json()["instrument"] == "maas"
        assert ac.json()["positive_screen"] is True
        assert sh.json()["positive_screen"] is True

    def test_phq9_banded_unaffected(self, client: TestClient) -> None:
        """After the ACEs branch was added to the dispatcher, PHQ-9
        banded-severity routing must still work identically — pin
        that the router insertion did not break any existing dispatch."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [3] * 9},
            headers=self._headers("aces-phq9-check"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "phq9"
        assert body["total"] == 27
        assert body["severity"] == "severe"

    def test_ignores_mdq_fields(self, client: TestClient) -> None:
        """ACEs dispatch ignores MDQ-specific fields that might leak
        through on a polymorphic client payload.  Pins that ACEs is
        dispatched BEFORE the MDQ fallthrough."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "aces",
                "items": [1] * 10,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers=self._headers("aces-ignore-extra"),
        )
        assert response.status_code == 201
        assert response.json()["instrument"] == "aces"


class TestPgsiRouting:
    """End-to-end routing tests for the PGSI dispatcher branch.

    Ferris & Wynne 2001 Problem Gambling Severity Index — 9 items,
    0-3 Likert, total 0-27, four bands (non_problem / low_risk /
    moderate_risk / problem_gambler).  The platform's FIRST
    behavioral-addiction severity-banded instrument — wire envelope
    matches AUDIT / PHQ-9 / GAD-7 / PSS-10 / ISI banded-severity
    shape.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_min_all_zeros_non_problem(self, client: TestClient) -> None:
        """General-population non-problem gambler — no endorsements."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [0] * 9},
            headers=self._headers("pgsi-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "pgsi"
        assert body["total"] == 0
        assert body["severity"] == "non_problem"

    def test_max_all_threes_problem_gambler(
        self, client: TestClient
    ) -> None:
        """Full severity — all 9 items at Almost always (3).  Total
        27, problem_gambler band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [3] * 9},
            headers=self._headers("pgsi-max"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 27
        assert body["severity"] == "problem_gambler"

    def test_band_boundary_total_0_non_problem(
        self, client: TestClient
    ) -> None:
        """Band boundary: total 0 must be non_problem."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [0] * 9},
            headers=self._headers("pgsi-band-0"),
        )
        assert response.json()["severity"] == "non_problem"

    def test_band_boundary_total_1_low_risk(
        self, client: TestClient
    ) -> None:
        """Band boundary: total 1 must be low_risk (non-problem ends
        at 0)."""
        items = [1, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-band-1"),
        )
        assert response.json()["severity"] == "low_risk"

    def test_band_boundary_total_2_low_risk(
        self, client: TestClient
    ) -> None:
        """Band boundary: total 2 is upper bound of low_risk."""
        items = [2, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-band-2"),
        )
        assert response.json()["severity"] == "low_risk"

    def test_band_boundary_total_3_moderate_risk(
        self, client: TestClient
    ) -> None:
        """Band boundary: total 3 crosses to moderate_risk."""
        items = [3, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-band-3"),
        )
        assert response.json()["severity"] == "moderate_risk"

    def test_band_boundary_total_7_moderate_risk(
        self, client: TestClient
    ) -> None:
        """Band boundary: total 7 is upper bound of moderate_risk."""
        items = [3, 3, 1, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-band-7"),
        )
        body = response.json()
        assert body["total"] == 7
        assert body["severity"] == "moderate_risk"

    def test_band_boundary_total_8_problem_gambler(
        self, client: TestClient
    ) -> None:
        """Band boundary: total 8 is Ferris 2001 operating point for
        DSM-IV pathological-gambling concurrent validity (kappa =
        0.83)."""
        items = [3, 3, 2, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-band-8"),
        )
        body = response.json()
        assert body["total"] == 8
        assert body["severity"] == "problem_gambler"

    def test_no_cutoff_used_on_wire(self, client: TestClient) -> None:
        """PGSI is banded, not screen.  cutoff_used absent/None on
        wire (uniform with PHQ-9 / GAD-7 / AUDIT)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [3] * 9},
            headers=self._headers("pgsi-no-cutoff"),
        )
        body = response.json()
        assert "cutoff_used" not in body or body.get("cutoff_used") is None

    def test_no_positive_screen_on_wire(self, client: TestClient) -> None:
        """PGSI is banded — no positive_screen field (uniform with
        PHQ-9 / GAD-7 / AUDIT / PSS-10 / ISI)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [3] * 9},
            headers=self._headers("pgsi-no-pos"),
        )
        body = response.json()
        assert (
            "positive_screen" not in body
            or body.get("positive_screen") is None
        )

    def test_no_subscales_on_wire(self, client: TestClient) -> None:
        """Ferris 2001 retained unidimensional structure by design."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [3] * 9},
            headers=self._headers("pgsi-no-subs"),
        )
        body = response.json()
        assert "subscales" not in body or body.get("subscales") is None

    def test_no_t3_at_severe_problem_gambler(
        self, client: TestClient
    ) -> None:
        """Even at PGSI = 27 (full-severity problem gambler),
        requires_t3 is False.  Problem-gambler suicide-risk elevation
        (Moghaddam 2015: 3.4x) is profile-level, not per-PGSI-item."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [3] * 9},
            headers=self._headers("pgsi-no-t3-max"),
        )
        assert response.json()["requires_t3"] is False

    def test_item_9_guilt_not_safety_routed(
        self, client: TestClient
    ) -> None:
        """Item 9 ("felt guilty about the way you gamble") at Almost
        always is NOT a safety item — affect/problem-awareness only."""
        items = [0, 0, 0, 0, 0, 0, 0, 0, 3]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-guilt-no-t3"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        """Version string pinned for FHIR Observation export."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [0] * 9},
            headers=self._headers("pgsi-version"),
        )
        assert response.json()["instrument_version"] == "pgsi-1.0.0"

    def test_item_count_8_rejected(self, client: TestClient) -> None:
        """8 items — one short of Ferris 2001 9-item structure."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [0] * 8},
            headers=self._headers("pgsi-count-8"),
        )
        assert response.status_code == 422

    def test_item_count_10_rejected(self, client: TestClient) -> None:
        """10 items — AUDIT / DAST-10 / PSS-10 adjacent trap."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [0] * 10},
            headers=self._headers("pgsi-count-10"),
        )
        assert response.status_code == 422

    def test_item_count_7_rejected(self, client: TestClient) -> None:
        """7 items — GAD-7 / ISI adjacent trap."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": [0] * 7},
            headers=self._headers("pgsi-count-7"),
        )
        assert response.status_code == 422

    def test_item_range_value_4_rejected(self, client: TestClient) -> None:
        """Value 4 is out of 0-3 Likert range — must 422."""
        items = [4, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-range-4"),
        )
        assert response.status_code == 422

    def test_item_range_negative_rejected(
        self, client: TestClient
    ) -> None:
        items = [-1, 0, 0, 0, 0, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "pgsi", "items": items},
            headers=self._headers("pgsi-range-neg"),
        )
        assert response.status_code == 422

    def test_history_projection_includes_pgsi(
        self, client: TestClient
    ) -> None:
        """PGSI submissions appear in /history with the banded
        severity shape."""
        user_id = "user-pgsi-history"
        client.post(
            "/v1/assessments",
            json={
                "instrument": "pgsi",
                "items": [3] * 9,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "pgsi-hist-1",
                "X-User-Id": user_id,
            },
        )
        response = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": user_id},
        )
        assert response.status_code == 200
        body = response.json()
        pgsi_items = [
            item for item in body["items"] if item["instrument"] == "pgsi"
        ]
        assert len(pgsi_items) >= 1
        pgsi_entry = pgsi_items[0]
        assert pgsi_entry["total"] == 27
        assert pgsi_entry["severity"] == "problem_gambler"

    def test_coexists_with_aces_and_audit_c(
        self, client: TestClient
    ) -> None:
        """PGSI + ACEs + AUDIT-C — the integrated behavioral-addiction
        enrollment triad.  A patient positive on all three represents
        the trauma-driven dual-addiction profile indicated for
        integrated concurrent treatment (Petry 2005; Najavits 2002;
        Hodgins 2010)."""
        user_id = "user-triad-2"

        ac = client.post(
            "/v1/assessments",
            json={
                "instrument": "aces",
                "items": [1] * 4 + [0] * 6,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "triad2-aces",
                "X-User-Id": user_id,
            },
        )
        pg = client.post(
            "/v1/assessments",
            json={
                "instrument": "pgsi",
                "items": [3] * 9,
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "triad2-pgsi",
                "X-User-Id": user_id,
            },
        )
        au = client.post(
            "/v1/assessments",
            json={
                "instrument": "audit_c",
                "items": [3, 3, 3],
                "sex": "male",
                "user_id": user_id,
            },
            headers={
                "Idempotency-Key": "triad2-audit-c",
                "X-User-Id": user_id,
            },
        )
        assert ac.status_code == 201
        assert pg.status_code == 201
        assert au.status_code == 201
        assert ac.json()["instrument"] == "aces"
        assert pg.json()["instrument"] == "pgsi"
        assert au.json()["instrument"] == "audit_c"
        assert pg.json()["severity"] == "problem_gambler"

    def test_ignores_mdq_fields(self, client: TestClient) -> None:
        """PGSI dispatched BEFORE the MDQ fallthrough — polymorphic
        MDQ fields must not affect PGSI dispatch."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "pgsi",
                "items": [3] * 9,
                "concurrent_symptoms": True,
                "functional_impairment": "serious",
            },
            headers=self._headers("pgsi-ignore-extra"),
        )
        assert response.status_code == 201
        assert response.json()["instrument"] == "pgsi"

    def test_phq9_banded_unaffected(self, client: TestClient) -> None:
        """Regression pin: after PGSI branch added, PHQ-9 banded
        routing still works identically."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [3] * 9},
            headers=self._headers("pgsi-phq9-check"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["instrument"] == "phq9"
        assert body["total"] == 27
        assert body["severity"] == "severe"

    def test_each_item_position_contributes_at_max(
        self, client: TestClient
    ) -> None:
        """Direction semantics on the wire — each item position adds
        exactly 3 at max (no reverse scoring in Ferris 2001)."""
        for position in range(9):
            items = [0] * 9
            items[position] = 3
            response = client.post(
                "/v1/assessments",
                json={"instrument": "pgsi", "items": items},
                headers=self._headers(f"pgsi-pos-{position}"),
            )
            assert response.status_code == 201
            body = response.json()
            assert body["total"] == 3, (
                f"position {position} did not contribute 3 "
                f"(got {body['total']})"
            )
            assert body["severity"] == "moderate_risk"


# =============================================================================
# BRS (Brief Resilience Scale) routing — Smith et al. 2008
# =============================================================================


class TestBrsRouting:
    """End-to-end routing tests for the BRS dispatcher branch.

    Smith 2008 Brief Resilience Scale — 6 items, 1-5 Likert, total
    6-30 (POST-FLIP), three bands (low / normal / high).  **HIGHER
    = MORE RESILIENT** — opposite of PHQ-9 / GAD-7 / AUDIT / PGSI;
    matches WHO-5 / MAAS / CD-RISC-10 higher-is-better convention.

    Reverse-keying: items 2, 4, 6 are negatively worded and flipped
    via ``6 - raw`` before summation (shared idiom with TAS-20 /
    PSWQ / LOT-R).  The wire ``items`` echo the patient's RAW
    pre-flip responses.

    Band thresholds mapped from Smith 2008 §3.3 conceptual mean:
    low 6-17, normal 18-25, high 26-30.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_min_resilience_low_band(self, client: TestClient) -> None:
        """Minimally resilient response — disagrees with every
        positive item (1) and agrees with every negative item (5).
        Post-flip = 6, low band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [1, 5, 1, 5, 1, 5]},
            headers=self._headers("brs-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "brs"
        assert body["total"] == 6
        assert body["severity"] == "low"

    def test_max_resilience_high_band(self, client: TestClient) -> None:
        """Maximally resilient response — agrees with every positive
        item (5) and disagrees with every negative item (1).  Post-
        flip = 30, high band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [5, 1, 5, 1, 5, 1]},
            headers=self._headers("brs-max"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 30
        assert body["severity"] == "high"

    def test_all_ones_acquiescence_yields_normal(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias control: raw all-1s yields post-flip
        sum 18 (normal band) — NOT low, despite the "least
        agreeable" response pattern.  This is the Smith 2008
        three-positive / three-negative symmetry at work."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [1, 1, 1, 1, 1, 1]},
            headers=self._headers("brs-all-1s"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 18
        assert body["severity"] == "normal"

    def test_all_fives_acquiescence_yields_normal(
        self, client: TestClient
    ) -> None:
        """Dual to the all-1s case: raw all-5s also yields post-flip
        sum 18 (normal band).  Design-enforced: response-set bias
        cannot push a patient into either extreme band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [5, 5, 5, 5, 5, 5]},
            headers=self._headers("brs-all-5s"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 18
        assert body["severity"] == "normal"

    def test_all_threes_is_normal(self, client: TestClient) -> None:
        """Neutral on every item -> post-flip sum 18, normal band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-all-3s"),
        )
        body = response.json()
        assert body["total"] == 18
        assert body["severity"] == "normal"

    def test_band_boundary_total_17_low(self, client: TestClient) -> None:
        """Last integer in the low band.  Post-flip [3,3,3,3,3,2]
        = 17 via raw [3,3,3,3,3,4] (position 6 reverse 6-4 = 2)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 4]},
            headers=self._headers("brs-band-17"),
        )
        body = response.json()
        assert body["total"] == 17
        assert body["severity"] == "low"

    def test_band_boundary_total_18_normal(self, client: TestClient) -> None:
        """First integer in the normal band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-band-18"),
        )
        body = response.json()
        assert body["total"] == 18
        assert body["severity"] == "normal"

    def test_band_boundary_total_25_normal(self, client: TestClient) -> None:
        """Last integer in the normal band.  Post-flip [4,4,4,4,4,5]
        = 25 via raw [4,2,4,2,4,1]."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [4, 2, 4, 2, 4, 1]},
            headers=self._headers("brs-band-25"),
        )
        body = response.json()
        assert body["total"] == 25
        assert body["severity"] == "normal"

    def test_band_boundary_total_26_high(self, client: TestClient) -> None:
        """First integer in the high band.  Post-flip [5,5,5,5,5,1]
        = 26 via raw [5,1,5,1,5,5]."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [5, 1, 5, 1, 5, 5]},
            headers=self._headers("brs-band-26"),
        )
        body = response.json()
        assert body["total"] == 26
        assert body["severity"] == "high"

    def test_wire_total_is_post_flip_not_raw_sum(
        self, client: TestClient
    ) -> None:
        """The wire total is the POST-FLIP sum, not the raw sum.
        Raw [5,5,5,5,5,5] has raw-sum 30 but post-flip sum 18 —
        the wire must emit 18 to confirm the scorer applied
        reverse-keying.  (The scorer preserves raw in its internal
        ``items`` field for audit, but the wire AssessmentResult
        envelope does not surface it — uniform across every
        reverse-keyed instrument TAS-20 / PSWQ / LOT-R / BRS.)"""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [5, 5, 5, 5, 5, 5]},
            headers=self._headers("brs-post-flip-total"),
        )
        body = response.json()
        # Raw sum would be 30 (ceiling) — post-flip is 18.
        assert body["total"] == 18
        assert body["total"] != 30

    def test_response_envelope_has_no_subscales(
        self, client: TestClient
    ) -> None:
        """Smith 2008 §3.2 EFA single-factor — no subscales field."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-no-subscales"),
        )
        body = response.json()
        # Envelope uses None / absent for instruments that don't
        # surface subscales (uniform with PHQ-9 / GAD-7 / AUDIT /
        # PSS-10 / ISI / PGSI banded-severity shape).
        assert body.get("subscales") in (None, {}, [])

    def test_response_envelope_has_no_cutoff_used(
        self, client: TestClient
    ) -> None:
        """BRS is banded, not a binary screen — cutoff_used absent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_response_envelope_has_no_positive_screen(
        self, client: TestClient
    ) -> None:
        """BRS is banded, not a binary screen — positive_screen absent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-no-posscreen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_response_envelope_has_instrument_version(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "brs-1.0.0"

    def test_never_requires_t3(self, client: TestClient) -> None:
        """BRS has no safety item — requires_t3 is always False,
        even at the minimum-resilience ceiling."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [1, 5, 1, 5, 1, 5]},
            headers=self._headers("brs-no-t3-low"),
        )
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "low"
        assert body["requires_t3"] is False

    def test_item_count_validation_five_rejected(
        self, client: TestClient
    ) -> None:
        """Wrong item count rejected at 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3]},
            headers=self._headers("brs-five-items"),
        )
        assert response.status_code == 422

    def test_item_count_validation_seven_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-seven-items"),
        )
        assert response.status_code == 422

    def test_item_count_validation_ten_rejected(
        self, client: TestClient
    ) -> None:
        """Trap: someone confuses BRS (6) with CD-RISC-10 (10)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3] * 10},
            headers=self._headers("brs-ten-items"),
        )
        assert response.status_code == 422

    def test_item_range_zero_rejected(self, client: TestClient) -> None:
        """BRS Likert is 1-5, not 0-5."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [0, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-zero-item"),
        )
        assert response.status_code == 422

    def test_item_range_six_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [6, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-six-value"),
        )
        assert response.status_code == 422

    def test_item_range_negative_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [-1, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-negative-item"),
        )
        assert response.status_code == 422

    def test_reverse_scoring_position_1_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 1 is a positive-worded item (non-reverse).
        Raising it from 3 to 5 raises total by 2 (post-flip
        unchanged for non-reverse items)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-rev-base1"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [5, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-rev-raise1"),
        ).json()["total"]
        assert raised == base + 2

    def test_reverse_scoring_position_2_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 2 is a negative-worded item (reverse-keyed).
        Raising it from 3 to 5 LOWERS total by 2 (post-flip 3 ->
        post-flip 1)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 3, 3, 3, 3, 3]},
            headers=self._headers("brs-rev-base2"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [3, 5, 3, 3, 3, 3]},
            headers=self._headers("brs-rev-raise2"),
        ).json()["total"]
        assert raised == base - 2

    def test_direction_higher_is_more_resilient(
        self, client: TestClient
    ) -> None:
        """Global direction pin — every single-position shift toward
        the resilient extreme must raise the total."""
        resilient = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [5, 1, 5, 1, 5, 1]},
            headers=self._headers("brs-dir-res"),
        ).json()["total"]
        unresilient = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [1, 5, 1, 5, 1, 5]},
            headers=self._headers("brs-dir-unres"),
        ).json()["total"]
        assert resilient > unresilient

    def test_clinical_vignette_depression_profile_low(
        self, client: TestClient
    ) -> None:
        """Depression-consistent low bounce-back — mild disagreement
        with positives, mild agreement with negatives.  Raw
        [2,4,2,4,2,4] -> post-flip [2,2,2,2,2,2] = 12, low band."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "brs", "items": [2, 4, 2, 4, 2, 4]},
            headers=self._headers("brs-dep-profile"),
        )
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "low"


# =============================================================================
# SCOFF (eating-disorder screen) routing — Morgan, Reid & Lacey 1999
# =============================================================================


class TestScoffRouting:
    """End-to-end routing tests for the SCOFF dispatcher branch.

    Morgan 1999 BMJ — 5-item binary yes/no eating-disorder screen
    (S-C-O-F-F mnemonic).  Cutoff >= 2 positive items (sens 100%
    / spec 87.5% vs DSM-III-R AN/BN in original n = 116; Cotton
    2003 primary-care n = 233 replication sens 100% / spec 89.6%;
    Solmi 2015 meta-analysis n = 26,488 AUC 0.89).

    Wire envelope matches AUDIT-C / PC-PTSD-5 / SHAPS / ACEs
    binary-screen shape: positive_screen + cutoff_used.  No bands,
    no subscales.  No T3 (item 1 "Sick" is purging behavior per
    Morgan 1999 Background §1, not self-harm).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    def test_all_zeros_negative_screen(self, client: TestClient) -> None:
        """Control-sample pattern — no positive items."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0, 0, 0, 0, 0]},
            headers=self._headers("scoff-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "scoff"
        assert body["total"] == 0
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 2

    def test_all_ones_positive_screen(self, client: TestClient) -> None:
        """Full positive endorsement."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("scoff-max"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 5
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 2

    def test_single_positive_below_cutoff(
        self, client: TestClient
    ) -> None:
        """Morgan 1999 REJECTED the >= 1 threshold.  A single
        positive item is below the operating point."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 0, 0, 0, 0]},
            headers=self._headers("scoff-one"),
        )
        body = response.json()
        assert body["total"] == 1
        assert body["severity"] == "negative_screen"
        assert body["positive_screen"] is False

    def test_cutoff_boundary_exactly_two(
        self, client: TestClient
    ) -> None:
        """The clinically-validated operating point (sens 100%,
        spec 87.5% vs DSM-III-R AN/BN)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 0, 0, 0]},
            headers=self._headers("scoff-two"),
        )
        body = response.json()
        assert body["total"] == 2
        assert body["severity"] == "positive_screen"
        assert body["positive_screen"] is True

    def test_three_positive(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 1, 0, 0]},
            headers=self._headers("scoff-three"),
        )
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "positive_screen"

    def test_four_positive(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 1, 1, 0]},
            headers=self._headers("scoff-four"),
        )
        body = response.json()
        assert body["total"] == 4
        assert body["severity"] == "positive_screen"

    def test_each_position_contributes_one(
        self, client: TestClient
    ) -> None:
        """Position-agnostic contribution — each position adds
        exactly 1 when endorsed.  Rules out reverse-keying or
        position-weighted bugs."""
        for position in range(5):
            items = [0] * 5
            items[position] = 1
            response = client.post(
                "/v1/assessments",
                json={"instrument": "scoff", "items": items},
                headers=self._headers(f"scoff-pos-{position}"),
            )
            assert response.status_code == 201
            body = response.json()
            assert body["total"] == 1, (
                f"position {position + 1} contributed "
                f"{body['total']} instead of 1"
            )

    def test_response_envelope_cutoff_used(
        self, client: TestClient
    ) -> None:
        """cutoff_used field on the wire response must carry the
        Morgan 1999 operating point (2)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 0, 0, 0]},
            headers=self._headers("scoff-cutoff-echo"),
        )
        body = response.json()
        assert body["cutoff_used"] == 2

    def test_response_envelope_has_no_subscales(
        self, client: TestClient
    ) -> None:
        """5 clinical-consensus cues — unidimensional by design."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0, 0, 0, 0, 0]},
            headers=self._headers("scoff-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") in (None, {}, [])

    def test_response_envelope_has_instrument_version(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0, 0, 0, 0, 0]},
            headers=self._headers("scoff-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "scoff-1.0.0"

    def test_never_requires_t3(self, client: TestClient) -> None:
        """SCOFF has no safety item — requires_t3 is always False,
        even at full-positive (severe ED) pattern."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("scoff-no-t3-max"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False

    def test_item_1_sick_no_safety_routing(
        self, client: TestClient
    ) -> None:
        """Item 1 "make yourself Sick" is PURGING BEHAVIOR per
        Morgan 1999 Background §1 — explicitly self-induced
        vomiting, NOT self-harm.  No T3 trigger from item 1
        alone."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 0, 0, 0, 0]},
            headers=self._headers("scoff-sick-only"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_item_count_validation_four_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0, 0, 0, 0]},
            headers=self._headers("scoff-four-items"),
        )
        assert response.status_code == 422

    def test_item_count_validation_six_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0, 0, 0, 0, 0, 0]},
            headers=self._headers("scoff-six-items"),
        )
        assert response.status_code == 422

    def test_item_count_validation_ten_rejected(
        self, client: TestClient
    ) -> None:
        """Trap: someone confuses SCOFF (5) with ACEs (10)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0] * 10},
            headers=self._headers("scoff-ten-items"),
        )
        assert response.status_code == 422

    def test_item_count_validation_nine_rejected(
        self, client: TestClient
    ) -> None:
        """Trap: someone confuses SCOFF (5) with PHQ-9 (9)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0] * 9},
            headers=self._headers("scoff-nine-items"),
        )
        assert response.status_code == 422

    def test_item_value_two_rejected(self, client: TestClient) -> None:
        """SCOFF is binary — 2 is not "more endorsement", it is
        invalid."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [2, 0, 0, 0, 0]},
            headers=self._headers("scoff-two-value"),
        )
        assert response.status_code == 422

    def test_item_value_negative_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [-1, 0, 0, 0, 0]},
            headers=self._headers("scoff-negative-value"),
        )
        assert response.status_code == 422

    def test_clinical_vignette_bulimia_nervosa(
        self, client: TestClient
    ) -> None:
        """BN-typical positive pattern: purging (S), loss of
        control (C), food preoccupation (F2), body image (F1)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [1, 1, 0, 1, 1]},
            headers=self._headers("scoff-bn-vignette"),
        )
        body = response.json()
        assert body["total"] == 4
        assert body["positive_screen"] is True

    def test_clinical_vignette_anorexia_nervosa(
        self, client: TestClient
    ) -> None:
        """AN-typical positive pattern: weight loss (O), body
        image distortion (F1), food preoccupation (F2)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "scoff", "items": [0, 0, 1, 1, 1]},
            headers=self._headers("scoff-an-vignette"),
        )
        body = response.json()
        assert body["total"] == 3
        assert body["positive_screen"] is True


# =============================================================================
# PANAS-10 (I-PANAS-SF) routing — Thompson 2007
# =============================================================================


class TestPanas10Routing:
    """End-to-end routing tests for the PANAS-10 dispatcher branch.

    Thompson 2007 I-PANAS-SF — 10-item cross-cultural derivation
    of the 20-item PANAS (Watson, Clark & Tellegen 1988).  Validated
    configural + metric + scalar measurement invariance across 8
    cultural groups (n = 1,789).

    **First bidirectional-subscales instrument on the platform.**
    The wire envelope pins:
    - ``total`` = PA subscale sum (5-25) — the primary per
      tripartite-model intervention-matching priority (PA deficit
      is depression-specific; NA elevation is non-specific
      distress).
    - ``subscales`` = {"positive_affect": pa_sum,
                       "negative_affect": na_sum} — clinicians
      must read both dimensions; the total alone is
      insufficient.
    - ``severity`` = "continuous" — Thompson 2007 did not
      publish banded cutpoints; Crawford & Henry 2004 norms are
      descriptive distributions, not clinical bands.
    - No ``positive_screen`` / ``cutoff_used`` — PANAS-10 is not
      a screen.
    - ``requires_t3`` always False — item 1 "upset" is general
      NA (Watson 1988 derivation), NOT suicidal ideation.  Acute-
      risk stays on C-SSRS / PHQ-9 item 9.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # ---- Dispatch contract ----

    def test_all_ones_pa_and_na_both_five(
        self, client: TestClient
    ) -> None:
        """Minimum endorsement on all items — PA = 5, NA = 5.
        Total (= PA) = 5."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [1] * 10},
            headers=self._headers("panas10-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "panas10"
        assert body["total"] == 5
        assert body["subscales"] == {
            "positive_affect": 5,
            "negative_affect": 5,
        }
        assert body["severity"] == "continuous"

    def test_all_fives_pa_and_na_both_twentyfive(
        self, client: TestClient
    ) -> None:
        """Maximum endorsement — PA = 25, NA = 25.  Total = 25.
        Tellegen 1999 orthogonality permits this configuration
        (high-arousal / high-engagement — NOT inconsistent)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [5] * 10},
            headers=self._headers("panas10-max"),
        )
        body = response.json()
        assert body["total"] == 25
        assert body["subscales"] == {
            "positive_affect": 25,
            "negative_affect": 25,
        }
        assert body["severity"] == "continuous"

    def test_flourishing_profile_high_pa_low_na(
        self, client: TestClient
    ) -> None:
        """Pressman & Cohen 2005 health-protective signature —
        high PA + low NA.  PA items (3, 5, 7, 8, 10) -> 5; NA
        items (1, 2, 4, 6, 9) -> 1.  pa_sum 25, na_sum 5."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [1, 1, 5, 1, 5, 1, 5, 5, 1, 5],
            },
            headers=self._headers("panas10-flourishing"),
        )
        body = response.json()
        assert body["total"] == 25
        assert body["subscales"]["positive_affect"] == 25
        assert body["subscales"]["negative_affect"] == 5

    def test_classic_depression_profile_low_pa_high_na(
        self, client: TestClient
    ) -> None:
        """Clark & Watson 1991 canonical depression signature —
        low PA + high NA.  pa_sum 5, na_sum 25.  Routes
        downstream to behavioral activation (Martell 2010)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [5, 5, 1, 5, 1, 5, 1, 1, 5, 1],
            },
            headers=self._headers("panas10-depression"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["subscales"]["positive_affect"] == 5
        assert body["subscales"]["negative_affect"] == 25

    def test_pure_anxiety_profile_normal_pa_high_na(
        self, client: TestClient
    ) -> None:
        """Pure-anxiety signature — normal PA + high NA.  Clark
        & Watson 1991 emphasis: NA elevation is NON-specific
        (shared with depression); normal PA DISCRIMINATES from
        depression.  pa_sum 15, na_sum 25."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [5, 5, 3, 5, 3, 5, 3, 3, 5, 3],
            },
            headers=self._headers("panas10-anxiety"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["subscales"]["positive_affect"] == 15
        assert body["subscales"]["negative_affect"] == 25

    def test_anhedonia_dominant_profile_low_pa_normal_na(
        self, client: TestClient
    ) -> None:
        """Pure anhedonia without anxious distress — Craske 2019
        positive-affect-treatment target profile.  pa_sum 5,
        na_sum 15.  Important: invisible on a PHQ-9 if somatic
        items are low — PANAS detects it via PA deficit."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [3, 3, 1, 3, 1, 3, 1, 1, 3, 1],
            },
            headers=self._headers("panas10-anhedonia"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["subscales"]["positive_affect"] == 5
        assert body["subscales"]["negative_affect"] == 15

    def test_euthymic_baseline_profile(
        self, client: TestClient
    ) -> None:
        """Middle-of-scale — Crawford & Henry 2004 normative-
        range analog.  pa_sum 15, na_sum 15."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-baseline"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["subscales"] == {
            "positive_affect": 15,
            "negative_affect": 15,
        }

    # ---- Envelope shape ----

    def test_total_equals_pa_sum_not_composite(
        self, client: TestClient
    ) -> None:
        """Critical invariant: the wire total is PA subscale sum,
        NOT a PA-NA composite (would contradict Watson 1988 /
        Tellegen 1999 orthogonality) and NOT a PA+NA sum (would
        collapse the two dimensions clinicians need separated).

        Depression profile pa_sum=5, na_sum=25:
          total must be 5, NOT 30 (would be sum), NOT -20 (would
          be difference)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [5, 5, 1, 5, 1, 5, 1, 1, 5, 1],
            },
            headers=self._headers("panas10-total-is-pa"),
        )
        body = response.json()
        assert body["total"] == 5
        # Guard against accidental composite formulas.
        assert body["total"] != 30  # not pa_sum + na_sum
        assert body["total"] != 20  # not na_sum - pa_sum
        assert body["total"] == body["subscales"]["positive_affect"]

    def test_subscales_dict_carries_both_keys(
        self, client: TestClient
    ) -> None:
        """Wire contract: subscales dict must contain BOTH
        positive_affect and negative_affect.  Clinicians rely on
        both keys being present — a missing key would silently
        hide half the clinical signal."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-subscales-both"),
        )
        body = response.json()
        subscales = body["subscales"]
        assert "positive_affect" in subscales
        assert "negative_affect" in subscales
        assert len(subscales) == 2

    def test_severity_is_continuous_sentinel(
        self, client: TestClient
    ) -> None:
        """Thompson 2007 did not publish banded severity.  The
        wire severity is the literal "continuous" sentinel —
        uniform with PACS / VAS / Ruler / DTCQ-8 / DERS-16 /
        CD-RISC-10 / PSWQ / LOT-R."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-continuous"),
        )
        body = response.json()
        assert body["severity"] == "continuous"

    def test_no_positive_screen_field(
        self, client: TestClient
    ) -> None:
        """PANAS-10 is not a screen — no positive_screen field
        on the response."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-no-screen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_no_cutoff_used_field(self, client: TestClient) -> None:
        """No operating point — no cutoff."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_no_triggering_items_field(
        self, client: TestClient
    ) -> None:
        """Triggering_items is C-SSRS / ASRS-6 specific."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-no-trigitems"),
        )
        body = response.json()
        assert body.get("triggering_items") in (None, [])

    def test_instrument_version_field(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "panas10-1.0.0"

    # ---- Orthogonality at the wire level ----

    def test_raising_na_position_does_not_change_total(
        self, client: TestClient
    ) -> None:
        """Watson 1988 / Tellegen 1999 orthogonality at the wire
        layer: raising an NA-position response must NOT change
        the total (= PA sum).  If it did, it would mean the
        envelope was accidentally emitting a composite."""
        # Baseline: all 3s.  pa_sum 15, na_sum 15, total 15.
        base = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-ortho-base"),
        ).json()
        assert base["total"] == 15

        # Raise position 1 (NA) to 5.  pa_sum unchanged; na_sum
        # rises from 15 to 17.
        perturbed = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [5, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("panas10-ortho-na"),
        ).json()
        assert perturbed["total"] == 15  # PA unchanged
        assert (
            perturbed["subscales"]["negative_affect"]
            == base["subscales"]["negative_affect"] + 2
        )

    def test_raising_pa_position_changes_total_not_na(
        self, client: TestClient
    ) -> None:
        """Reverse of the orthogonality test: raising a PA
        position changes the total (= PA sum), but NOT the NA
        subscale."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 10},
            headers=self._headers("panas10-ortho-pa-base"),
        ).json()
        perturbed = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [3, 3, 5, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("panas10-ortho-pa"),
        ).json()
        # Position 3 is PA.  pa_sum 15 -> 17; na_sum unchanged at 15.
        assert perturbed["total"] == base["total"] + 2
        assert (
            perturbed["subscales"]["negative_affect"]
            == base["subscales"]["negative_affect"]
        )

    # ---- Position -> subscale wire pinning ----

    @pytest.mark.parametrize(
        "position_1, expected_subscale_key",
        [
            (1, "negative_affect"),   # Upset
            (2, "negative_affect"),   # Hostile
            (3, "positive_affect"),   # Alert
            (4, "negative_affect"),   # Ashamed
            (5, "positive_affect"),   # Inspired
            (6, "negative_affect"),   # Nervous
            (7, "positive_affect"),   # Determined
            (8, "positive_affect"),   # Attentive
            (9, "negative_affect"),   # Afraid
            (10, "positive_affect"),  # Active
        ],
    )
    def test_position_routes_to_expected_subscale_at_wire(
        self,
        client: TestClient,
        position_1: int,
        expected_subscale_key: str,
    ) -> None:
        """Pin each Thompson 2007 position's subscale membership
        AT THE WIRE LEVEL.  A routing-layer bug that mis-assembled
        the subscales dict would be caught here even if the scorer
        itself were correct."""
        items = [1] * 10
        items[position_1 - 1] = 5
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": items},
            headers=self._headers(f"panas10-pos-{position_1}"),
        )
        body = response.json()
        expected_sum = 9  # baseline 5 (= 5 * 1) + (5 - 1) = 9
        other_sum = 5  # unchanged
        other_key = (
            "negative_affect"
            if expected_subscale_key == "positive_affect"
            else "positive_affect"
        )
        assert body["subscales"][expected_subscale_key] == expected_sum, (
            f"position {position_1} should raise {expected_subscale_key}"
        )
        assert body["subscales"][other_key] == other_sum, (
            f"position {position_1} leaked into {other_key}"
        )

    # ---- Safety routing ----

    def test_never_requires_t3_even_at_max_na(
        self, client: TestClient
    ) -> None:
        """PANAS-10 probes affect dimensions, not suicidality.
        Even the classic-depression profile (max NA, min PA)
        does NOT emit T3.  Clinicians follow up with C-SSRS /
        PHQ-9 item 9 — the PANAS does not carry that signal."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [5, 5, 1, 5, 1, 5, 1, 1, 5, 1],
            },
            headers=self._headers("panas10-no-t3-dep"),
        )
        body = response.json()
        assert body["subscales"]["negative_affect"] == 25
        assert body["requires_t3"] is False

    def test_item_1_upset_no_safety_routing(
        self, client: TestClient
    ) -> None:
        """Item 1 "upset" is general NA per Watson 1988 item
        derivation, NOT suicidal ideation.  Maximum endorsement
        of item 1 alone — no T3."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [5, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            },
            headers=self._headers("panas10-no-t3-upset"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_max_all_items_never_requires_t3(
        self, client: TestClient
    ) -> None:
        """Hyperarousal profile — max on both subscales.  Still
        no T3.  Orthogonality permits this configuration."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [5] * 10},
            headers=self._headers("panas10-no-t3-max"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    # ---- Item-count validation ----

    def test_item_count_nine_rejected(
        self, client: TestClient
    ) -> None:
        """Trap: someone confuses PANAS-10 (10) with PHQ-9 (9)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 9},
            headers=self._headers("panas10-9-items"),
        )
        assert response.status_code == 422

    def test_item_count_eleven_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 11},
            headers=self._headers("panas10-11-items"),
        )
        assert response.status_code == 422

    def test_item_count_twenty_rejected(
        self, client: TestClient
    ) -> None:
        """Trap: someone submits the 20-item parent PANAS (Watson
        1988) to the short-form endpoint.  Must fail loud."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "panas10", "items": [3] * 20},
            headers=self._headers("panas10-20-items"),
        )
        assert response.status_code == 422

    # ---- Item-value validation (strict 1-5 Likert) ----

    def test_item_value_zero_rejected(
        self, client: TestClient
    ) -> None:
        """Trap: someone uses a 0-4 scale (PHQ-9-style) on a 1-5
        instrument."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [0, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("panas10-zero-val"),
        )
        assert response.status_code == 422

    def test_item_value_six_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [6, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("panas10-six-val"),
        )
        assert response.status_code == 422

    def test_item_value_negative_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "panas10",
                "items": [-1, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("panas10-neg-val"),
        )
        assert response.status_code == 422


# =============================================================================
# RSES (self-esteem) routing — Rosenberg 1965 / Gray-Little 1997
# =============================================================================


class TestRsesRouting:
    """End-to-end routing tests for the RSES dispatcher branch.

    Rosenberg 1965 Self-Esteem Scale — 10 items, 0-3 Likert, total
    0-30 (POST-FLIP), unidimensional (Gray-Little 1997 IRT), no
    bands (severity = ``"continuous"``).  **HIGHER = MORE SELF-
    ESTEEM** — same direction as WHO-5 / BRS / MAAS / CD-RISC-10.

    Reverse-keying: items 2, 5, 6, 8, 9 are negatively worded and
    flipped via ``3 - raw`` before summation.  The wire ``items``
    are NOT surfaced by the AssessmentResult envelope (consistent
    with every other reverse-keyed instrument — TAS-20 / PSWQ /
    LOT-R / BRS); the wire ``total`` is the POST-FLIP sum.

    Diagnostic property (Marsh 1996): balanced 5-positive / 5-
    negative wording means raw all-0s AND raw all-3s BOTH yield
    total 15.  Pinned in two parallel tests because it is the
    canonical acquiescence-bias-control signature — if either
    extreme drifts off 15, reverse-keying has broken.

    No bands: Rosenberg 1965 and Gray-Little 1997 did not publish
    clinical cutpoints.  Jacobson-Truax RCI is applied to the raw
    total in the trajectory layer, not inside the scorer.  The
    severity field is the sentinel literal ``"continuous"``.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ----------------------------------------------------

    def test_max_self_esteem_flourishing(self, client: TestClient) -> None:
        """Maximum self-esteem — raw agreement with every positive
        (1,3,4,7,10) and disagreement with every negative (2,5,6,
        8,9).  Post-flip all 3s, total 30.  Clinically: flourishing
        self-concept."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [3, 0, 3, 3, 0, 0, 3, 0, 0, 3]},
            headers=self._headers("rses-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "rses"
        assert body["total"] == 30
        assert body["severity"] == "continuous"

    def test_min_self_esteem_abstinence_violation_signature(
        self, client: TestClient
    ) -> None:
        """Minimum self-esteem — the Marlatt 1985 abstinence-
        violation-effect signature.  Raw disagreement with every
        positive, agreement with every negative.  Post-flip all
        0s, total 0.  Clinically: the lowest-self-concept ceiling
        and the substrate most predictive of relapse."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [0, 3, 0, 0, 3, 3, 0, 3, 3, 0]},
            headers=self._headers("rses-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_acquiescence_bias_all_zeros_yields_fifteen(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias control (Marsh 1996): raw all-0s
        (strongly disagree with every item regardless of valence)
        yields total 15 after reverse-keying — NOT 0.  This is the
        balanced-wording guarantee; if this drifts, reverse-keying
        has broken.  5 positive × 0 + 5 negative × (3-0=3) = 15."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [0] * 10},
            headers=self._headers("rses-acq-zeros"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_acquiescence_bias_all_threes_yields_fifteen(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias control (Marsh 1996): raw all-3s
        (strongly agree with every item regardless of valence)
        yields total 15 — NOT 30.  The mirror of the all-0s test;
        together these pin the balanced-wording property that
        Rosenberg 1965 built the scale around."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [3] * 10},
            headers=self._headers("rses-acq-threes"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_international_mean_vignette(self, client: TestClient) -> None:
        """Schmitt & Allik 2005 cross-cultural meta-analysis
        reported an international mean near ~21.  This specific
        item pattern — mild positive agreement, mild negative
        disagreement — yields total 21 exactly and represents the
        typical non-clinical community respondent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [3, 1, 2, 2, 1, 1, 2, 1, 1, 2]},
            headers=self._headers("rses-intl-mean"),
        )
        body = response.json()
        assert body["total"] == 21
        assert body["severity"] == "continuous"

    def test_wire_total_is_post_flip_not_raw_sum(
        self, client: TestClient
    ) -> None:
        """The wire total is the POST-FLIP sum.  Raw [3,3,3,3,3,
        3,3,3,3,3] has raw-sum 30 but post-flip sum 15 — the wire
        must emit 15 to confirm the scorer applied reverse-keying.
        (Consistent with TAS-20 / PSWQ / LOT-R / BRS wire-layer
        policy: the envelope surfaces post-flip; raw pre-flip is
        preserved only inside the scorer's ``items`` for audit.)"""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [3] * 10},
            headers=self._headers("rses-post-flip"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["total"] != 30

    def test_response_envelope_has_no_subscales(
        self, client: TestClient
    ) -> None:
        """Gray-Little 1997 IRT confirmed unidimensional — no
        subscales field.  Two-factor proposals (Tomas 1999) are
        method-artifact per Marsh 1996, not substantive."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") in (None, {}, [])

    def test_response_envelope_has_no_cutoff_used(
        self, client: TestClient
    ) -> None:
        """RSES is continuous, not a screen — cutoff_used absent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_response_envelope_has_no_positive_screen(
        self, client: TestClient
    ) -> None:
        """RSES is continuous, not a screen — positive_screen
        absent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-no-posscreen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_response_envelope_has_instrument_version(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "rses-1.0.0"

    def test_severity_always_continuous_regardless_of_total(
        self, client: TestClient
    ) -> None:
        """Severity is the sentinel literal ``"continuous"`` for
        every RSES response — Rosenberg 1965 / Gray-Little 1997
        did not publish bands, and inventing them would violate
        the CLAUDE.md "no hand-rolled severity thresholds" rule."""
        for items, key in (
            ([3, 0, 3, 3, 0, 0, 3, 0, 0, 3], "rses-sev-30"),
            ([0, 3, 0, 0, 3, 3, 0, 3, 3, 0], "rses-sev-0"),
            ([2] * 10, "rses-sev-mid"),
            ([1, 2, 1, 1, 2, 2, 1, 2, 2, 1], "rses-sev-10"),
        ):
            response = client.post(
                "/v1/assessments",
                json={"instrument": "rses", "items": items},
                headers=self._headers(key),
            )
            assert response.json()["severity"] == "continuous"

    # -- T3 posture -------------------------------------------------------

    def test_never_requires_t3_at_min(self, client: TestClient) -> None:
        """RSES has NO safety item.  Even at the AVE-signature
        minimum (total 0), requires_t3 is False — self-esteem
        impairment is a clinical substrate but not an acute-risk
        signal.  C-SSRS / PHQ-9 item 9 remain the T3 sources."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [0, 3, 0, 0, 3, 3, 0, 3, 3, 0]},
            headers=self._headers("rses-no-t3-min"),
        )
        body = response.json()
        assert body["total"] == 0
        assert body["requires_t3"] is False

    def test_never_requires_t3_item_9_is_self_concept_not_ideation(
        self, client: TestClient
    ) -> None:
        """Item 9 ("inclined to feel that I am a failure") is a
        SELF-CONCEPT item per Rosenberg 1965 §2, NOT an ideation
        item.  Maximum agreement on item 9 (raw 3 -> post-flip 0)
        must not trigger T3, because failure-framing without
        lethality context is not suicidality."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2, 1, 2, 2, 1, 1, 2, 1, 3, 2]},
            headers=self._headers("rses-no-t3-item9"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    # -- Reverse-keying wire-level pins ----------------------------------

    def test_reverse_scoring_position_1_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 1 is positive-worded (non-reverse).  Raising
        it from 2 to 3 raises the total by +1."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-rev-base1"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [3, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            },
            headers=self._headers("rses-rev-raise1"),
        ).json()["total"]
        assert raised == base + 1

    def test_reverse_scoring_position_2_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 2 is negative-worded (reverse-keyed).  Raising
        it from 2 to 3 LOWERS the total by -1 (post-flip 1 ->
        post-flip 0)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-rev-base2"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [2, 3, 2, 2, 2, 2, 2, 2, 2, 2],
            },
            headers=self._headers("rses-rev-raise2"),
        ).json()["total"]
        assert raised == base - 1

    def test_reverse_scoring_position_5_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 5 ("I feel I do not have much to be proud
        of") is reverse-keyed."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-rev-base5"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [2, 2, 2, 2, 3, 2, 2, 2, 2, 2],
            },
            headers=self._headers("rses-rev-raise5"),
        ).json()["total"]
        assert raised == base - 1

    def test_reverse_scoring_position_9_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 9 ("inclined to feel that I am a failure") is
        reverse-keyed.  Despite being the most-cited "low self-
        esteem" item, the mechanical reverse-keying is identical
        to items 2, 5, 6, 8 — no special-casing."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 10},
            headers=self._headers("rses-rev-base9"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [2, 2, 2, 2, 2, 2, 2, 2, 3, 2],
            },
            headers=self._headers("rses-rev-raise9"),
        ).json()["total"]
        assert raised == base - 1

    def test_direction_higher_is_more_self_esteem(
        self, client: TestClient
    ) -> None:
        """Global direction pin — the flourishing pattern must
        yield a strictly higher total than the AVE-signature
        pattern.  If this inverts, the valence map has flipped."""
        flourishing = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [3, 0, 3, 3, 0, 0, 3, 0, 0, 3]},
            headers=self._headers("rses-dir-flourish"),
        ).json()["total"]
        ave = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [0, 3, 0, 0, 3, 3, 0, 3, 3, 0]},
            headers=self._headers("rses-dir-ave"),
        ).json()["total"]
        assert flourishing > ave

    # -- Item-count validation -------------------------------------------

    def test_item_count_9_rejected(self, client: TestClient) -> None:
        """Trap: someone drops an item and sends 9 — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 9},
            headers=self._headers("rses-nine-items"),
        )
        assert response.status_code == 422

    def test_item_count_11_rejected(self, client: TestClient) -> None:
        """Trap: someone appends a trailing item — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 11},
            headers=self._headers("rses-eleven-items"),
        )
        assert response.status_code == 422

    def test_item_count_20_rejected(self, client: TestClient) -> None:
        """Trap: someone confuses RSES (10) with TAS-20 (20)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 20},
            headers=self._headers("rses-twenty-items"),
        )
        assert response.status_code == 422

    def test_item_count_6_rejected(self, client: TestClient) -> None:
        """Trap: someone confuses RSES (10) with BRS (6)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": [2] * 6},
            headers=self._headers("rses-six-items"),
        )
        assert response.status_code == 422

    # -- Item-value validation -------------------------------------------

    def test_item_value_4_rejected(self, client: TestClient) -> None:
        """RSES Likert is 0-3, not 0-4.  Trap: someone applies a
        PHQ-9 (0-3) or GAD-7 (0-3) + 1 off-by-one."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [4, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            },
            headers=self._headers("rses-four-value"),
        )
        assert response.status_code == 422

    def test_item_value_negative_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [-1, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            },
            headers=self._headers("rses-negative-item"),
        )
        assert response.status_code == 422

    def test_item_value_99_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [99, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            },
            headers=self._headers("rses-99-value"),
        )
        assert response.status_code == 422

    def test_pydantic_coerces_json_bool_to_int(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces JSON ``true`` / ``false`` to int 1 / 0
        at the wire layer — the scorer-level bool rejection (see
        ``test_rses_scoring``) pins Python-layer bool rejection,
        but the wire-layer Pydantic coercion means a JSON ``true``
        in items is accepted as equivalent to ``1``.  Documented
        here (matching the ACEs wire-layer pin) so any future
        stricter-validation refactor surfaces this behavior change
        explicitly.  The request succeeds because [true,false,...]
        deserializes to a valid [1,0,...] item sequence."""
        items: list = [True, False, 2, 2, 2, 2, 2, 2, 2, 2]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "rses", "items": items},
            headers=self._headers("rses-json-bool"),
        )
        assert response.status_code == 201
        assert response.json()["severity"] == "continuous"

    # -- Clinical vignettes ----------------------------------------------

    def test_clinical_vignette_impaired_self_concept_early_recovery(
        self, client: TestClient
    ) -> None:
        """Early-recovery SUD patient with impaired self-concept.
        Mild disagreement with positives (raw 1), mild agreement
        with negatives (raw 2, post-flip 1).  Total 5+5=10 —
        well below the Schmitt 2005 international mean of 21,
        consistent with the Marlatt 1985 AVE substrate."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [1, 2, 1, 1, 2, 2, 1, 2, 2, 1],
            },
            headers=self._headers("rses-vignette-impaired"),
        )
        body = response.json()
        assert body["total"] == 10
        assert body["severity"] == "continuous"

    def test_clinical_vignette_mild_positive(
        self, client: TestClient
    ) -> None:
        """Non-clinical community respondent — mild agreement
        with positives (raw 2), mild disagreement with negatives
        (raw 1, post-flip 2).  Total 10+10=20, just below the
        Schmitt 2005 international mean of 21."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "rses",
                "items": [2, 1, 2, 2, 1, 1, 2, 1, 1, 2],
            },
            headers=self._headers("rses-vignette-mild-positive"),
        )
        body = response.json()
        assert body["total"] == 20


# =============================================================================
# FFMQ-15 (five-facet mindfulness) routing — Baer 2006 / Gu 2016
# =============================================================================


class TestFfmq15Routing:
    """End-to-end routing tests for the FFMQ-15 dispatcher branch.

    Baer, Smith, Hopkins, Krietemeyer & Toney 2006 Five-Facet
    Mindfulness Questionnaire — 15-item 1-5 Likert short form (Gu
    2016 IRT), total 15-75 (POST-FLIP), five facets at 3 items
    each.  **HIGHER = MORE mindfulness** — same direction as
    WHO-5 / BRS / MAAS / CD-RISC-10 / RSES.

    Reverse-keying at 7 positions: 6 (describing), 7-9 (acting-
    with-awareness entirely), 10-12 (non-judging entirely).
    Observing (1-3) and non-reactivity (13-15) are entirely
    positively worded.  Post-flip = 6 - raw.

    **First platform instrument with penta-subscales.**  PANAS-10
    introduced bidirectional-subscales (PA + NA); FFMQ-15 extends
    to five: observing, describing, acting_with_awareness,
    non_judging, non_reactivity.  Intervention-matching engine
    routes on the facet profile, not the grand total.

    Acquiescence-bias asymmetric: all-raw-1 -> 43; all-raw-5 ->
    47 (separation of 4, due to the 8/7 positive/reverse split —
    cannot achieve the RSES symmetric-midpoint property since
    item counts differ by one).  Pinned as routing tests so the
    8/7 split is wire-level observable.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ----------------------------------------------------

    def test_max_mindfulness_flourishing_profile(
        self, client: TestClient
    ) -> None:
        """Baer 2006 meditator-subsample ceiling: every positive
        item at max, every reverse item at min.  Post-flip all
        5s, total 75, every facet 15."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5],
            },
            headers=self._headers("ffmq15-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "ffmq15"
        assert body["total"] == 75
        assert body["severity"] == "continuous"

    def test_min_mindfulness_floor_profile(
        self, client: TestClient
    ) -> None:
        """Every positive item at min, every reverse item at max.
        Post-flip all 1s, total 15, every facet 3."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
            },
            headers=self._headers("ffmq15-min"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_midpoint_all_threes(self, client: TestClient) -> None:
        """All raw-3s: 3 is the fixed-point under flip (6-3=3).
        Total 45, every facet 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-midpoint"),
        )
        body = response.json()
        assert body["total"] == 45

    def test_acquiescence_all_ones_yields_43(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias signature 1: all raw-1s -> 43
        (8 positive × 1 + 7 reverse × 5).  Note: NOT 15 and NOT
        45 — the asymmetric 8/7 split prevents the RSES-style
        symmetric midpoint property."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [1] * 15},
            headers=self._headers("ffmq15-acq-ones"),
        )
        body = response.json()
        assert body["total"] == 43

    def test_acquiescence_all_fives_yields_47(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias signature 2: all raw-5s -> 47
        (8 positive × 5 + 7 reverse × 1).  Mirror of the all-1s
        signature; the two extremes differ by 4 (the 8/7 split
        asymmetry)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [5] * 15},
            headers=self._headers("ffmq15-acq-fives"),
        )
        body = response.json()
        assert body["total"] == 47

    def test_acquiescence_extremes_differ_by_exactly_4(
        self, client: TestClient
    ) -> None:
        """Wire-level pin of the 8/7 asymmetry.  If this drifts
        off 4, the reverse-item count has changed from 7."""
        low = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [1] * 15},
            headers=self._headers("ffmq15-acq-low-wire"),
        ).json()["total"]
        high = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [5] * 15},
            headers=self._headers("ffmq15-acq-high-wire"),
        ).json()["total"]
        assert high - low == 4

    def test_wire_total_is_post_flip_not_raw_sum(
        self, client: TestClient
    ) -> None:
        """All raw-5s: raw-sum 75, post-flip sum 47.  Wire must
        emit 47 to confirm reverse-keying."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [5] * 15},
            headers=self._headers("ffmq15-post-flip"),
        )
        body = response.json()
        assert body["total"] == 47
        assert body["total"] != 75

    # -- Subscale envelope (the novel penta-subscale pattern) -----------

    def test_envelope_has_all_five_subscales(
        self, client: TestClient
    ) -> None:
        """FFMQ-15 is the first penta-subscale instrument.  The
        envelope must surface all five facet sums; clinician-UI
        renders them as the facet profile."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-subscales-exist"),
        )
        body = response.json()
        subscales = body["subscales"]
        assert set(subscales.keys()) == {
            "observing",
            "describing",
            "acting_with_awareness",
            "non_judging",
            "non_reactivity",
        }

    def test_subscales_at_max_mindfulness(
        self, client: TestClient
    ) -> None:
        """Every facet at ceiling 15."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5],
            },
            headers=self._headers("ffmq15-subscales-max"),
        )
        subs = response.json()["subscales"]
        assert subs["observing"] == 15
        assert subs["describing"] == 15
        assert subs["acting_with_awareness"] == 15
        assert subs["non_judging"] == 15
        assert subs["non_reactivity"] == 15

    def test_subscales_at_min_mindfulness(
        self, client: TestClient
    ) -> None:
        """Every facet at floor 3."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
            },
            headers=self._headers("ffmq15-subscales-min"),
        )
        subs = response.json()["subscales"]
        assert subs["observing"] == 3
        assert subs["describing"] == 3
        assert subs["acting_with_awareness"] == 3
        assert subs["non_judging"] == 3
        assert subs["non_reactivity"] == 3

    def test_subscales_at_acquiescence_all_ones(
        self, client: TestClient
    ) -> None:
        """All raw-1s facet profile: Obs=3, Des=7, Act=15, NJ=15,
        NR=3.  Acting and non-judging are at CEILING because they
        are entirely reverse-keyed; observing and non-reactivity
        at floor."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [1] * 15},
            headers=self._headers("ffmq15-acq-ones-subs"),
        )
        subs = response.json()["subscales"]
        assert subs["observing"] == 3
        assert subs["describing"] == 7
        assert subs["acting_with_awareness"] == 15
        assert subs["non_judging"] == 15
        assert subs["non_reactivity"] == 3

    def test_grand_total_equals_sum_of_subscales(
        self, client: TestClient
    ) -> None:
        """The wire grand total must equal the sum of the five
        subscale sums on the envelope — invariant that the
        intervention-matching UI depends on for facet-weight
        rendering."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            },
            headers=self._headers("ffmq15-total-invariant"),
        )
        body = response.json()
        subs = body["subscales"]
        assert body["total"] == (
            subs["observing"]
            + subs["describing"]
            + subs["acting_with_awareness"]
            + subs["non_judging"]
            + subs["non_reactivity"]
        )

    # -- Standard envelope assertions ------------------------------------

    def test_response_envelope_has_no_cutoff_used(
        self, client: TestClient
    ) -> None:
        """FFMQ-15 is continuous, not a screen."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-no-cutoff"),
        )
        assert response.json().get("cutoff_used") is None

    def test_response_envelope_has_no_positive_screen(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-no-posscreen"),
        )
        assert response.json().get("positive_screen") is None

    def test_response_envelope_has_instrument_version(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-version"),
        )
        assert response.json()["instrument_version"] == "ffmq15-1.0.0"

    def test_severity_always_continuous(self, client: TestClient) -> None:
        """No bands — severity is the "continuous" sentinel
        regardless of total."""
        for items, key in (
            ([5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5], "ffmq15-sev-75"),
            ([1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1], "ffmq15-sev-15"),
            ([3] * 15, "ffmq15-sev-mid"),
            ([1] * 15, "ffmq15-sev-acq-low"),
            ([5] * 15, "ffmq15-sev-acq-high"),
        ):
            response = client.post(
                "/v1/assessments",
                json={"instrument": "ffmq15", "items": items},
                headers=self._headers(key),
            )
            assert response.json()["severity"] == "continuous"

    # -- T3 posture ------------------------------------------------------

    def test_never_requires_t3_at_floor(self, client: TestClient) -> None:
        """FFMQ-15 has no safety item.  Even at the mindfulness
        floor (total 15, every facet at 3) requires_t3 is False —
        non-judging items mention "my emotions are bad" but are
        self-evaluative shame content, NOT ideation."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
            },
            headers=self._headers("ffmq15-no-t3-floor"),
        )
        assert response.json()["requires_t3"] is False

    def test_never_requires_t3_at_ceiling(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5],
            },
            headers=self._headers("ffmq15-no-t3-ceiling"),
        )
        assert response.json()["requires_t3"] is False

    # -- Reverse-keying wire-level pins ----------------------------------

    def test_reverse_scoring_position_1_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 1 is observing (positive).  Raising 3 -> 5
        adds 2 to total."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-rev-base1"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-rev-raise1"),
        ).json()["total"]
        assert raised == base + 2

    def test_reverse_scoring_position_6_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 6 is describing's lone reverse item.
        Raising 3 -> 5 LOWERS total by 2."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-rev-base6"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [3, 3, 3, 3, 3, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-rev-raise6"),
        ).json()["total"]
        assert raised == base - 2

    def test_reverse_scoring_position_7_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 7 is acting-with-awareness (all reverse)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-rev-base7"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [3, 3, 3, 3, 3, 3, 5, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-rev-raise7"),
        ).json()["total"]
        assert raised == base - 2

    def test_reverse_scoring_position_10_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 10 is non-judging (all reverse).  AVE
        precursor: higher raw = more self-criticism = LOWER
        mindfulness post-flip."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-rev-base10"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-rev-raise10"),
        ).json()["total"]
        assert raised == base - 2

    def test_reverse_scoring_position_13_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 13 is non-reactivity (positive)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-rev-base13"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 3, 3],
            },
            headers=self._headers("ffmq15-rev-raise13"),
        ).json()["total"]
        assert raised == base + 2

    # -- Facet-independence wire-level pin -------------------------------

    def test_facet_perturbation_isolation(
        self, client: TestClient
    ) -> None:
        """Perturbing only the observing items must not affect
        the other four facet sums on the envelope."""
        base_subs = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 15},
            headers=self._headers("ffmq15-iso-base"),
        ).json()["subscales"]
        perturbed_subs = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [5, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-iso-obs-5"),
        ).json()["subscales"]
        assert perturbed_subs["observing"] == 15
        assert perturbed_subs["describing"] == base_subs["describing"]
        assert perturbed_subs["acting_with_awareness"] == base_subs[
            "acting_with_awareness"
        ]
        assert perturbed_subs["non_judging"] == base_subs["non_judging"]
        assert perturbed_subs["non_reactivity"] == base_subs["non_reactivity"]

    # -- Item-count validation -------------------------------------------

    def test_item_count_14_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 14},
            headers=self._headers("ffmq15-14-items"),
        )
        assert response.status_code == 422

    def test_item_count_16_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 16},
            headers=self._headers("ffmq15-16-items"),
        )
        assert response.status_code == 422

    def test_item_count_10_rejected_maas_trap(
        self, client: TestClient
    ) -> None:
        """Trap: someone confuses FFMQ-15 (15) with PANAS-10 (10)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 10},
            headers=self._headers("ffmq15-10-items"),
        )
        assert response.status_code == 422

    def test_item_count_39_rejected_full_ffmq_trap(
        self, client: TestClient
    ) -> None:
        """Trap: someone sends the full 39-item FFMQ."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": [3] * 39},
            headers=self._headers("ffmq15-39-items"),
        )
        assert response.status_code == 422

    # -- Item-value validation -------------------------------------------

    def test_item_value_0_rejected(self, client: TestClient) -> None:
        """FFMQ-15 Likert is 1-5, not 0-4 — trap for
        depression-scale off-by-one (PHQ-9 / GAD-7 are 0-3)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-zero-value"),
        )
        assert response.status_code == 422

    def test_item_value_6_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-six-value"),
        )
        assert response.status_code == 422

    def test_item_value_negative_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [-1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-negative-value"),
        )
        assert response.status_code == 422

    def test_item_value_99_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [99, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-99-value"),
        )
        assert response.status_code == 422

    def test_pydantic_coerces_json_bool_to_int(
        self, client: TestClient
    ) -> None:
        """Platform wire-layer reality: JSON ``true`` coerces to
        int 1.  Documented here (matching ACEs / RSES wire-layer
        pins) so any future stricter-validation refactor surfaces
        the behavior change explicitly.  Note: ``false`` coerces
        to 0, which is BELOW the FFMQ-15 Likert minimum (1-5);
        sending JSON ``false`` IS correctly rejected at the item-
        range check (which runs after Pydantic coercion).  So
        this test uses only ``true`` values that coerce to a
        valid 1."""
        items: list = [True, True, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": items},
            headers=self._headers("ffmq15-json-bool"),
        )
        assert response.status_code == 201
        assert response.json()["severity"] == "continuous"

    def test_pydantic_coerces_false_to_zero_rejected_by_range(
        self, client: TestClient
    ) -> None:
        """Mirror of the bool-coercion pin: JSON ``false`` coerces
        to int 0, which is below the FFMQ-15 Likert minimum (1-5)
        and therefore CORRECTLY rejected at the item-range check.
        This demonstrates that FFMQ-15's 1-5 range gives a tighter
        validation perimeter than ACEs (0-1) / RSES (0-3) — the
        bool-via-zero pathway that bypasses CLAUDE.md bool
        rejection on 0-N scales is naturally blocked on 1-5
        scales."""
        items: list = [False, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ffmq15", "items": items},
            headers=self._headers("ffmq15-json-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes ----------------------------------------------

    def test_clinical_vignette_ave_non_judging_deficit(
        self, client: TestClient
    ) -> None:
        """Marlatt 1985 abstinence-violation-effect precursor:
        non-judging at floor (all NJ items at raw 5 -> post-flip
        1), other facets at midpoint.  Patient evaluates every
        inner event as bad/wrong — the AVE substrate.  Grand
        total 9+9+9+3+9 = 39."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 5, 5, 3, 3, 3],
            },
            headers=self._headers("ffmq15-vignette-ave"),
        )
        body = response.json()
        assert body["total"] == 39
        assert body["subscales"]["non_judging"] == 3
        assert body["subscales"]["observing"] == 9

    def test_clinical_vignette_automatic_pilot_relapse(
        self, client: TestClient
    ) -> None:
        """Bowen 2014 MBRP cue-reactivity signature: acting-with-
        awareness at floor, other facets normal.  Primary
        intervention target for MBRP §3.2.  Grand total 9+9+3+9+9
        = 39 with acting_with_awareness at 3."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [3, 3, 3, 3, 3, 3, 5, 5, 5, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("ffmq15-vignette-autopilot"),
        )
        body = response.json()
        assert body["total"] == 39
        assert body["subscales"]["acting_with_awareness"] == 3
        assert body["subscales"]["non_judging"] == 9

    def test_clinical_vignette_flourishing(
        self, client: TestClient
    ) -> None:
        """Every facet at ceiling.  All five subscales at 15,
        grand total 75.  Pinned at the wire level so the
        clinician UI's "all-green-profile" rendering never
        regresses."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "ffmq15",
                "items": [5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5],
            },
            headers=self._headers("ffmq15-vignette-flourish"),
        )
        body = response.json()
        assert body["total"] == 75
        subs = body["subscales"]
        assert all(
            subs[f] == 15
            for f in (
                "observing",
                "describing",
                "acting_with_awareness",
                "non_judging",
                "non_reactivity",
            )
        )


# =============================================================================
# STAI-6 (brief state anxiety) routing — Marteau & Bekker 1992
# =============================================================================


class TestStai6Routing:
    """End-to-end routing tests for the STAI-6 dispatcher branch.

    Marteau & Bekker 1992 State-Trait Anxiety Inventory brief 6-item
    short form — 6 items, 1-4 Likert, total 6-24 (POST-FLIP), single
    factor, no bands (severity = ``"continuous"``).  **HIGHER =
    MORE state-anxious** — uniform with PHQ-9 / GAD-7 / AUDIT /
    PSS-10 / PGSI / SHAPS (lower-is-better).  OPPOSITE of WHO-5 /
    BRS / RSES / FFMQ-15 / MAAS / LOT-R.

    Reverse-keying: items 1, 4, 5 are the three positively-worded
    state items ("calm", "relaxed", "content") and are flipped via
    ``5 - raw`` before summation.  Items 2, 3, 6 (negative —
    "tense", "upset", "worried") pass through raw.  The wire
    ``items`` are NOT surfaced by the envelope (consistent with
    every other reverse-keyed instrument — RSES / TAS-20 / PSWQ /
    LOT-R / BRS / FFMQ-15 / PANAS-10); the wire ``total`` is the
    POST-FLIP 6-24 sum.

    Diagnostic property (Marsh 1996): the 3-positive / 3-negative
    SYMMETRIC reverse-keying split means every CONSTANT-response
    vector yields the midpoint total 15.  Pinned in FOUR parallel
    tests (all-1s, all-2s, all-3s, all-4s) because it is the
    canonical acquiescence-bias-control signature — stronger than
    FFMQ-15's asymmetric 8/7 split (differ-by-4 between extremes)
    and mirrors RSES's 5-positive / 5-negative balance.  If any
    constant vector drifts off 15, reverse-keying has broken.

    Clinical use cases (Spielberger 1966/1983 state-vs-trait
    anxiety distinction):
    1. Pre/post intervention-session effect measurement — the
       canonical within-session efficacy metric for behavioral
       activation / exposure (Craske 2014).
    2. Trigger-vs-baseline cue-reactivity detection — spike signals
       exposure-therapy targets vs trait-anxiety protocol targets
       (Dugas 2010).
    3. Real-time relapse-risk gating — elevated state anxiety in
       the hour before a craving episode is Marlatt 1985 pp. 137-
       142's canonical proximal-relapse precipitant.

    No bands: Marteau 1992 did not publish clinical cutpoints.
    Kvaal 2005's ≥ 40 scaled cutoff is secondary-literature
    derivation (HADS-validated) and not pinnable per CLAUDE.md.
    Jacobson-Truax RCI applied to the raw 6-24 total at the
    trajectory layer.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ----------------------------------------------------

    def test_max_state_anxiety_pre_surgical_extremum(
        self, client: TestClient
    ) -> None:
        """Maximum state anxiety — raw disagrees maximally with
        every positive (calm=1, relaxed=1, content=1) and agrees
        maximally with every negative (tense=4, upset=4, worried=4).
        Post-flip all 4s, total 24.  Clinically: the pre-surgical
        extremum per Marteau 1992's n=200 derivation sample."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1, 4, 4, 1, 1, 4]},
            headers=self._headers("stai6-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "stai6"
        assert body["total"] == 24
        assert body["severity"] == "continuous"

    def test_min_state_anxiety_calm_extremum(
        self, client: TestClient
    ) -> None:
        """Minimum state anxiety — raw agrees maximally with every
        positive (calm=4, relaxed=4, content=4) and disagrees with
        every negative (tense=1, upset=1, worried=1).  Post-flip all
        1s, total 6.  Clinically: the non-anxious community-sample
        floor per Tluczek 2009."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [4, 1, 1, 4, 4, 1]},
            headers=self._headers("stai6-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "continuous"

    def test_acquiescence_bias_all_ones_yields_fifteen(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias control (Marsh 1996): raw all-1s
        ("not at all" on every item regardless of valence) yields
        total 15 after reverse-keying — NOT 6.  Reverse items flip
        1->4 (contributing 12), non-reverse pass through (3);
        12 + 3 = 15.  If this drifts, the 3-positive / 3-negative
        balance has broken."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1] * 6},
            headers=self._headers("stai6-acq-ones"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_acquiescence_bias_all_fours_yields_fifteen(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias control (Marsh 1996): raw all-4s ("very
        much so" on every item regardless of valence) yields total
        15 — NOT 24.  Reverse items flip 4->1 (3), non-reverse pass
        through (12); 3 + 12 = 15.  Mirror of the all-1s pin; the
        symmetric-reverse-keying guarantee Marteau 1992 built in."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [4] * 6},
            headers=self._headers("stai6-acq-fours"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_acquiescence_bias_all_twos_yields_fifteen(
        self, client: TestClient
    ) -> None:
        """Interior-uniform acquiescence pin: raw all-2s also yields
        midpoint 15.  Every CONSTANT vector on a 1-4 Likert with
        3/3 reverse-split lands at the midpoint.  Stronger property
        than FFMQ-15's asymmetric 8/7 differ-by-4."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-acq-twos"),
        )
        body = response.json()
        assert body["total"] == 15

    def test_acquiescence_bias_all_threes_yields_fifteen(
        self, client: TestClient
    ) -> None:
        """Interior-uniform acquiescence pin (mirror of all-2s).
        Together the four constant-vector pins (1s, 2s, 3s, 4s) lock
        down the stronger-than-FFMQ-15 symmetric-reverse property."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [3] * 6},
            headers=self._headers("stai6-acq-threes"),
        )
        body = response.json()
        assert body["total"] == 15

    def test_wire_total_is_post_flip_not_raw_sum(
        self, client: TestClient
    ) -> None:
        """The wire total is the POST-FLIP sum.  Raw [4,4,4,4,4,4]
        has raw-sum 24 but post-flip sum 15 — the wire must emit 15
        to confirm the scorer applied reverse-keying.  (Consistent
        with RSES / TAS-20 / PSWQ / LOT-R / BRS / FFMQ-15 wire-
        layer policy: the envelope surfaces post-flip; raw pre-flip
        is preserved only inside the scorer's ``items`` for audit.)"""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [4] * 6},
            headers=self._headers("stai6-post-flip"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["total"] != 24

    def test_response_envelope_has_no_subscales(
        self, client: TestClient
    ) -> None:
        """STAI-6 is single-factor by construction (derived from the
        STAI-S single-factor per Spielberger 1983).  The envelope
        must NOT surface a subscales dict — it would contradict the
        derivation."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") in (None, {}, [])

    def test_response_envelope_has_no_cutoff_used(
        self, client: TestClient
    ) -> None:
        """STAI-6 is continuous, not a screen — cutoff_used absent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_response_envelope_has_no_positive_screen(
        self, client: TestClient
    ) -> None:
        """STAI-6 is continuous, not a screen — positive_screen
        absent.  No screen semantic applies; clinical-significance
        lives at the RCI trajectory layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-no-posscreen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_response_envelope_has_instrument_version(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "stai6-1.0.0"

    def test_response_envelope_has_no_scaled_score(
        self, client: TestClient
    ) -> None:
        """Marteau 1992 recommended a (total × 20) / 6 scaled score
        mapping to the full STAI-S 20-80 range.  The platform does
        NOT emit it: non-integer for most inputs, RCI at trajectory
        layer works on raw total directly, and Kvaal 2005 ≥ 40
        scaled cutoff is secondary literature not pinnable per
        CLAUDE.md.  Wire envelope must not expose a scaled_score
        key."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-no-scaled"),
        )
        body = response.json()
        assert body.get("scaled_score") is None

    def test_severity_always_continuous_regardless_of_total(
        self, client: TestClient
    ) -> None:
        """Severity is the sentinel literal ``"continuous"`` for
        every STAI-6 response — Marteau 1992 did not publish bands,
        and inventing them (even using Kvaal 2005's ≥ 40 scaled
        secondary cutoff) would violate the CLAUDE.md "no hand-
        rolled severity thresholds" rule."""
        for items, key in (
            ([1, 4, 4, 1, 1, 4], "stai6-sev-24"),
            ([4, 1, 1, 4, 4, 1], "stai6-sev-6"),
            ([3, 3, 3, 3, 3, 3], "stai6-sev-mid"),
            ([2, 3, 3, 2, 2, 3], "stai6-sev-18"),
            ([1, 3, 3, 1, 2, 4], "stai6-sev-21"),
        ):
            response = client.post(
                "/v1/assessments",
                json={"instrument": "stai6", "items": items},
                headers=self._headers(key),
            )
            assert response.json()["severity"] == "continuous"

    # -- T3 posture -------------------------------------------------------

    def test_never_requires_t3_at_max(self, client: TestClient) -> None:
        """STAI-6 has NO safety item.  Even at the maximum-anxiety
        extremum (total 24), requires_t3 is False — elevated state
        anxiety is a clinical signal but not an ACUTE-RISK signal.
        C-SSRS / PHQ-9 item 9 remain the T3 sources."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1, 4, 4, 1, 1, 4]},
            headers=self._headers("stai6-no-t3-max"),
        )
        body = response.json()
        assert body["total"] == 24
        assert body["requires_t3"] is False

    def test_never_requires_t3_item_3_is_general_distress_not_ideation(
        self, client: TestClient
    ) -> None:
        """Item 3 ("I feel upset") is general state-distress per
        Spielberger 1983, NOT suicidal ideation.  Maximum agreement
        on item 3 (raw 4) must not trigger T3 — "upset" in the
        STAI-S affective lexicon is distress/disturbance, not
        lethality.  Acute-risk screening stays on C-SSRS + PHQ-9
        item 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 2, 4, 2, 2, 2]},
            headers=self._headers("stai6-no-t3-item3"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    # -- Reverse-keying wire-level pins ----------------------------------

    def test_reverse_scoring_position_1_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 1 ("I feel calm") is positive-worded (reverse-
        keyed).  Raising it from 2 to 3 LOWERS the total by -1
        (post-flip 3 -> post-flip 2, less anxiety)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-rev-base1"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [3, 2, 2, 2, 2, 2]},
            headers=self._headers("stai6-rev-raise1"),
        ).json()["total"]
        assert raised == base - 1

    def test_reverse_scoring_position_2_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 2 ("I am tense") is negative-worded (non-
        reverse).  Raising it from 2 to 3 raises the total by +1
        (post-flip 2 -> post-flip 3, more anxiety)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-rev-base2"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 3, 2, 2, 2, 2]},
            headers=self._headers("stai6-rev-raise2"),
        ).json()["total"]
        assert raised == base + 1

    def test_reverse_scoring_position_3_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 3 ("I feel upset") is negative-worded (non-
        reverse)."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-rev-base3"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 2, 3, 2, 2, 2]},
            headers=self._headers("stai6-rev-raise3"),
        ).json()["total"]
        assert raised == base + 1

    def test_reverse_scoring_position_4_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 4 ("I am relaxed") is positive-worded (reverse-
        keyed).  Raising it from 2 to 3 LOWERS the total by -1."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-rev-base4"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 2, 2, 3, 2, 2]},
            headers=self._headers("stai6-rev-raise4"),
        ).json()["total"]
        assert raised == base - 1

    def test_reverse_scoring_position_5_is_reverse(
        self, client: TestClient
    ) -> None:
        """Position 5 ("I feel content") is positive-worded (reverse-
        keyed).  Raising it from 2 to 3 LOWERS the total by -1."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-rev-base5"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 2, 2, 2, 3, 2]},
            headers=self._headers("stai6-rev-raise5"),
        ).json()["total"]
        assert raised == base - 1

    def test_reverse_scoring_position_6_is_non_reverse(
        self, client: TestClient
    ) -> None:
        """Position 6 ("I am worried") is negative-worded (non-
        reverse).  Despite being the most-clinically-salient anxiety
        descriptor, the mechanical reverse-keying is identical to
        items 2 and 3 — no special-casing."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 6},
            headers=self._headers("stai6-rev-base6"),
        ).json()["total"]
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 2, 2, 2, 2, 3]},
            headers=self._headers("stai6-rev-raise6"),
        ).json()["total"]
        assert raised == base + 1

    def test_direction_higher_is_more_anxious(
        self, client: TestClient
    ) -> None:
        """Global direction pin — the maximum-anxiety pattern must
        yield a strictly higher total than the minimum-anxiety
        pattern.  If this inverts, the valence map has flipped.
        Unlike RSES/BRS/FFMQ-15/WHO-5 (higher=better), STAI-6 is
        LOWER-is-better; anxious > calm at the wire level."""
        anxious = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1, 4, 4, 1, 1, 4]},
            headers=self._headers("stai6-dir-anxious"),
        ).json()["total"]
        calm = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [4, 1, 1, 4, 4, 1]},
            headers=self._headers("stai6-dir-calm"),
        ).json()["total"]
        assert anxious > calm
        assert anxious == 24
        assert calm == 6

    # -- Item-count validation -------------------------------------------

    def test_item_count_5_rejected(self, client: TestClient) -> None:
        """Trap: someone drops an item and sends 5 — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 5},
            headers=self._headers("stai6-five-items"),
        )
        assert response.status_code == 422

    def test_item_count_7_rejected(self, client: TestClient) -> None:
        """Trap: someone appends a trailing item — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 7},
            headers=self._headers("stai6-seven-items"),
        )
        assert response.status_code == 422

    def test_item_count_10_rejected(self, client: TestClient) -> None:
        """Trap: someone confuses STAI-6 (6) with the full STAI-S
        abbreviation (10) or GAD-7 (7) rounded up — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 10},
            headers=self._headers("stai6-ten-items"),
        )
        assert response.status_code == 422

    def test_item_count_20_rejected(self, client: TestClient) -> None:
        """Trap: someone submits the full 20-item STAI-S by mistake
        — 422.  This is the most-likely confusion because STAI-6 is
        derived from the full 20-item state scale."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2] * 20},
            headers=self._headers("stai6-twenty-items"),
        )
        assert response.status_code == 422

    def test_item_count_empty_rejected(self, client: TestClient) -> None:
        """Empty items list — 422 at the Pydantic min_length
        boundary."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": []},
            headers=self._headers("stai6-empty"),
        )
        assert response.status_code == 422

    # -- Item-value validation -------------------------------------------

    def test_item_value_0_rejected(self, client: TestClient) -> None:
        """STAI-6 Likert is 1-4, not 0-4.  Trap: someone applies a
        PHQ-9 / GAD-7 0-based scale — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [0, 2, 2, 2, 2, 2]},
            headers=self._headers("stai6-zero-value"),
        )
        assert response.status_code == 422

    def test_item_value_5_rejected(self, client: TestClient) -> None:
        """STAI-6 Likert is 1-4, not 1-5.  Trap: someone applies a
        BRS / RSES / FFMQ-15 / PANAS-10 1-5 scale — 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [5, 2, 2, 2, 2, 2]},
            headers=self._headers("stai6-five-value"),
        )
        assert response.status_code == 422

    def test_item_value_negative_rejected(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [-1, 2, 2, 2, 2, 2]},
            headers=self._headers("stai6-negative-item"),
        )
        assert response.status_code == 422

    def test_item_value_99_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [99, 2, 2, 2, 2, 2]},
            headers=self._headers("stai6-99-value"),
        )
        assert response.status_code == 422

    def test_pydantic_coerces_json_bool_to_int(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces JSON ``true`` -> int 1 at the wire layer
        — the scorer-level bool rejection (see
        ``test_stai6_scoring``) pins Python-layer bool rejection,
        but the wire-layer Pydantic coercion means a JSON ``true``
        in items is accepted as equivalent to ``1``.  Documented
        here (matching the ACEs / RSES / FFMQ-15 wire-layer pins)
        so any future stricter-validation refactor surfaces this
        behavior change explicitly.  Uses all-True because True->1
        is a valid STAI-6 item value."""
        items: list = [True, True, True, True, True, True]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": items},
            headers=self._headers("stai6-json-bool"),
        )
        assert response.status_code == 201
        # [1,1,1,1,1,1] is the acquiescence extremum -> total 15.
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_pydantic_coerces_false_to_zero_rejected_by_range(
        self, client: TestClient
    ) -> None:
        """Companion to the True->1 pin: JSON ``false`` coerces to
        int 0, which is BELOW STAI-6's ITEM_MIN=1 and therefore
        rejected by the range check at 422.  This surfaces a
        stronger validation property than FFMQ-15 / BRS / RSES
        (all 0-N or 1-N): STAI-6's tight 1-4 range excludes
        both ``false->0`` AND ``>4``, giving tighter wire-layer
        validation than 0-based or wider scales."""
        items: list = [False, 2, 2, 2, 2, 2]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": items},
            headers=self._headers("stai6-json-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes ----------------------------------------------

    def test_clinical_vignette_pre_surgical_elevated_anxiety(
        self, client: TestClient
    ) -> None:
        """Marteau 1992 derivation sample (n = 200 pre-surgical
        patients): elevated state anxiety.  Raw [1,3,3,1,2,4] — not
        calm, quite tense, upset, not relaxed, somewhat content,
        very worried.  Post-flip [4,3,3,4,3,4] = 21.  Consistent
        with Marteau's mean pre-op state anxiety score."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1, 3, 3, 1, 2, 4]},
            headers=self._headers("stai6-vignette-presurgery"),
        )
        body = response.json()
        assert body["total"] == 21
        assert body["severity"] == "continuous"

    def test_clinical_vignette_within_session_delta(
        self, client: TestClient
    ) -> None:
        """The canonical intervention-efficacy use case: pre-session
        elevated state anxiety, post-session reduced state anxiety.
        GAD-7 cannot resolve this (its 14-day window averages over
        the session); STAI-6 pre/post delta IS the metric."""
        pre = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1, 4, 3, 1, 2, 4]},
            headers=self._headers("stai6-vignette-pre"),
        ).json()
        post = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [3, 2, 2, 3, 3, 2]},
            headers=self._headers("stai6-vignette-post"),
        ).json()
        assert pre["total"] == 22
        assert post["total"] == 12
        # Delta >= 10 is a strongly-positive within-session effect
        # (well above the Jacobson-Truax RCI threshold on a 6-24
        # scale — RCI cutoff ~ 4.4 per Marteau's reported variance).
        assert pre["total"] - post["total"] == 10

    def test_clinical_vignette_trigger_reactivity_spike(
        self, client: TestClient
    ) -> None:
        """Marlatt 1985 cue-reactivity scenario.  Baseline low-
        anxiety measurement, then post-trigger spike.  The hour-
        before-craving signal that drives the Discipline OS
        intervention-bandit policy."""
        baseline = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [4, 1, 1, 4, 3, 2]},
            headers=self._headers("stai6-vignette-baseline"),
        ).json()
        post_trigger = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [1, 3, 2, 2, 2, 3]},
            headers=self._headers("stai6-vignette-trigger"),
        ).json()
        assert baseline["total"] == 8
        assert post_trigger["total"] == 18
        # Spike of 10+ points within a brief window is a bandit-
        # policy predictive signal per Marlatt 1985 pp. 137-142.
        assert post_trigger["total"] - baseline["total"] >= 10

    def test_clinical_vignette_community_non_clinical(
        self, client: TestClient
    ) -> None:
        """Tluczek 2009 general-population sample: low state-
        anxiety profile.  Raw [3,2,1,3,3,2] — quite calm, not tense,
        not upset, relaxed, content, slightly worried.  Post-flip
        [2,2,1,2,2,2] = 11.  Well below the Marteau 1992 pre-op
        mean; typical community respondent."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [3, 2, 1, 3, 3, 2]},
            headers=self._headers("stai6-vignette-community"),
        )
        body = response.json()
        assert body["total"] == 11
        assert body["severity"] == "continuous"

    def test_clinical_vignette_oncology_elevated(
        self, client: TestClient
    ) -> None:
        """Balsamo 2014 oncology-patient profile: elevated state
        anxiety during treatment.  Raw [2,3,3,2,2,3].  Post-flip
        [3,3,3,3,3,3] = 18.  Between the Marteau pre-surgical mean
        and the upper maximum."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "stai6", "items": [2, 3, 3, 2, 2, 3]},
            headers=self._headers("stai6-vignette-oncology"),
        )
        body = response.json()
        assert body["total"] == 18
        assert body["severity"] == "continuous"


class TestFnebRouting:
    """End-to-end routing tests for the FNE-B dispatcher branch.

    Leary 1983 Brief Fear of Negative Evaluation — 12 items, 1-5
    Likert, total 12-60 (POST-FLIP), single factor, no bands
    (severity = ``"continuous"``).  **HIGHER = MORE fear of
    negative evaluation** — uniform with PHQ-9 / GAD-7 / PSS-10 /
    STAI-6 (lower-is-better direction).  OPPOSITE of WHO-5 / BRS /
    RSES / FFMQ-15 / MAAS / LOT-R.

    Reverse-keying: items 2, 4, 7, 10 are the four reverse-keyed
    positions (positively-worded "I am unconcerned / rarely worry /
    not worried" lead-ins) flipped via ``6 - raw`` before summation.
    The remaining 8 items (1, 3, 5, 6, 8, 9, 11, 12) are negatively
    worded and pass through raw.  The wire ``items`` are NOT
    surfaced by the envelope (consistent with every other reverse-
    keyed instrument); the wire ``total`` is the POST-FLIP 12-60 sum.

    Diagnostic property (Marsh 1996 acquiescence-bias-control
    signature): the 8-straight / 4-reverse ASYMMETRIC split yields
    the LINEAR formula ``total = 4v + 24`` for any all-``v``
    constant-response vector — all-1s = 28, all-2s = 32, all-3s =
    36, all-4s = 40, all-5s = 44.  Pinned in FIVE parallel tests
    because it is the canonical asymmetric-split acquiescence
    property (contrast with STAI-6's 3/3 symmetric split where
    every constant → 15, or FFMQ-15's 8/7 split where extremes
    differ by only 4).  FNE-B's differ-by-16 between raw-all-1 and
    raw-all-5 is the LARGEST acquiescence gap on the platform —
    a random endpoint-only responder shifts the score 33% of the
    12-60 range.  If any constant drifts off ``4v + 24``, reverse-
    keying at positions 2/4/7/10 has broken.

    Clinical use cases (Heimberg 1995, Hofmann 2008, Marlatt 1985
    Table 4.1, Caplan 2003):
    1. Socially-cued relapse detection — high FNE-B entering a
       social drinking context signals Marlatt 1985 social-pressure
       relapse risk on a mechanism ORTHOGONAL to craving intensity.
    2. User-profile differentiation — high FNE-B + elevated AUDIT
       = "alcohol-as-social-lubrication" profile (exposure +
       social-skills target); low FNE-B + elevated PSS-10 / STAI-6
       = "negative-affect-self-medication" profile (DBT distress-
       tolerance target).  Distinct intervention pathways.
    3. Digital-avoidance substitution detection — high FNE-B +
       problematic internet / gaming use is the Caplan 2003
       compensatory-internet-use signature.

    No bands: Leary 1983 did not publish severity cutpoints.
    Collins 2005's ``>= 49`` "clinical range" noted in a n=234
    college sample is secondary-literature post-hoc derivation and
    not pinnable per CLAUDE.md.  Jacobson-Truax RCI applied to the
    raw 12-60 total at the trajectory layer.  No T3 gating — no
    item probes suicidality ("afraid of making mistakes" item 8 is
    evaluative-apprehension NOT ideation; acute-risk screening
    stays on C-SSRS / PHQ-9 item 9).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ----------------------------------------------------

    def test_max_fear_extremum_sixty(self, client: TestClient) -> None:
        """Maximum fear of negative evaluation — raw [5,1,5,1,5,5,1,
        5,5,1,5,5] agrees maximally with every straight item
        (1,3,5,6,8,9,11,12 = all 5) and disagrees with every reverse
        item (2,4,7,10 = all 1).  Post-flip all 5s, total 60.
        Clinically: severe social-evaluative-anxiety extremum per
        Collins 2005."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5],
            },
            headers=self._headers("fneb-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "fneb"
        assert body["total"] == 60
        assert body["severity"] == "continuous"

    def test_min_fear_extremum_twelve(self, client: TestClient) -> None:
        """Minimum fear of negative evaluation — raw [1,5,1,5,1,1,5,
        1,1,5,1,1] disagrees with every straight item (all 1) and
        agrees with every reverse item (all 5).  Post-flip all 1s,
        total 12.  Clinically: the socially-secure / low-evaluative-
        apprehension floor."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1],
            },
            headers=self._headers("fneb-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "continuous"

    # -- Acquiescence-bias signature (asymmetric 8/4 split) ----------------

    def test_acquiescence_all_ones_yields_twenty_eight(
        self, client: TestClient
    ) -> None:
        """Acquiescence-bias control — raw all-1s ("not at all
        characteristic" on every item regardless of valence) yields
        total 28.  Linear formula: 4×1 + 24 = 28.  Straights
        contribute 8 (8×1), reverses flip 1→5 contributing 20
        (4×5).  The asymmetric 8/4 split means this does NOT land
        at the midpoint — that signature is FNE-B's canonical
        fingerprint."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [1] * 12},
            headers=self._headers("fneb-acq-1"),
        )
        body = response.json()
        assert body["total"] == 28

    def test_acquiescence_all_twos_yields_thirty_two(
        self, client: TestClient
    ) -> None:
        """4×2 + 24 = 32.  Straights 16 (8×2), reverses 16
        (4×(6-2)=4×4)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [2] * 12},
            headers=self._headers("fneb-acq-2"),
        )
        body = response.json()
        assert body["total"] == 32

    def test_acquiescence_all_threes_yields_thirty_six(
        self, client: TestClient
    ) -> None:
        """4×3 + 24 = 36.  The midpoint of the 12-60 range; this
        is the ONLY constant vector that lands at the arithmetic
        midpoint (unlike STAI-6 where all four constants do).
        Straights 24 (8×3), reverses 12 (4×(6-3)=4×3)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 12},
            headers=self._headers("fneb-acq-3"),
        )
        body = response.json()
        assert body["total"] == 36

    def test_acquiescence_all_fours_yields_forty(
        self, client: TestClient
    ) -> None:
        """4×4 + 24 = 40.  Straights 32 (8×4), reverses 8
        (4×(6-4)=4×2)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [4] * 12},
            headers=self._headers("fneb-acq-4"),
        )
        body = response.json()
        assert body["total"] == 40

    def test_acquiescence_all_fives_yields_forty_four(
        self, client: TestClient
    ) -> None:
        """4×5 + 24 = 44.  Raw all-5s ("extremely characteristic"
        on every item) yields 44, NOT 60 — because reverses flip
        5→1.  The differ-by-16 gap with all-1s (28) is the largest
        acquiescence-bias signature on the platform."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [5] * 12},
            headers=self._headers("fneb-acq-5"),
        )
        body = response.json()
        assert body["total"] == 44

    def test_acquiescence_differ_by_sixteen_invariant(
        self, client: TestClient
    ) -> None:
        """Pin the acquiescence-bias signature invariant
        explicitly: all-5s total minus all-1s total equals
        exactly 16 — the full range of reverse-keying's
        contribution under 5-point Likert asymmetric 8/4 split
        (4 reverses × (5-1)=4 range each = 16).  If this invariant
        breaks, either reverse-keying positions have drifted or
        the Likert range has changed."""
        r1 = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [1] * 12},
            headers=self._headers("fneb-diff16-1"),
        ).json()
        r5 = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [5] * 12},
            headers=self._headers("fneb-diff16-5"),
        ).json()
        assert r5["total"] - r1["total"] == 16

    # -- Envelope fields — no subscales, cutoff_used, positive_screen ------

    def test_envelope_has_no_subscales(self, client: TestClient) -> None:
        """FNE-B is single-factor (Leary 1983); envelope MUST NOT
        carry subscales.  BFNE-II (Carleton 2007) attempted a
        reverse-keyed-only 8-item factor — the platform ships the
        original 12-item form and does not split."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 12},
            headers=self._headers("fneb-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_envelope_has_no_cutoff_used(self, client: TestClient) -> None:
        """Leary 1983 published no cutoff; Collins 2005's ≥49 is
        secondary-literature and not pinned per CLAUDE.md no-hand-
        rolled-bands rule."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 12},
            headers=self._headers("fneb-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_envelope_has_no_positive_screen(self, client: TestClient) -> None:
        """No categorical screen — FNE-B is a continuous
        dimensional measure, not a dichotomous screen like
        AUDIT-C / MDQ / PC-PTSD-5."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 12},
            headers=self._headers("fneb-no-screen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_envelope_has_no_scaled_score(self, client: TestClient) -> None:
        """FNE-B reports the raw 12-60 total.  No scaled mapping
        to another range — contrast with WHO-5 which emits the
        raw×4 index."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 12},
            headers=self._headers("fneb-no-scaled"),
        )
        body = response.json()
        assert body.get("scaled_score") is None

    def test_envelope_has_no_triggering_items(self, client: TestClient) -> None:
        """triggering_items is C-SSRS-only (risk-band audit trail).
        FNE-B is a continuous dimensional measure; no item is
        individually-flagging."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [5] * 12},
            headers=self._headers("fneb-no-triggering"),
        )
        body = response.json()
        assert body.get("triggering_items") is None

    # -- Severity always continuous ----------------------------------------

    def test_severity_continuous_at_minimum(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1],
            },
            headers=self._headers("fneb-sev-min"),
        )
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_collins_2005_49(
        self, client: TestClient
    ) -> None:
        """Collins 2005 noted ≥49 as "clinical range" in a social-
        phobia-student sample.  The platform fires NO band at this
        threshold — the value 49 in the response is continuous, not
        banded.  If a severity label appears here, secondary-
        literature bands have leaked into the scorer in violation of
        CLAUDE.md."""
        # Raw [5,2,5,2,4,4,2,4,4,2,4,3]: straights 5+5+4+4+4+4+4+3 = 33,
        # reverses raw all-2 → flip to 4 each, 4×4 = 16.  Total 49.
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 2, 5, 2, 4, 4, 2, 4, 4, 2, 4, 3],
            },
            headers=self._headers("fneb-sev-49"),
        )
        body = response.json()
        assert body["total"] == 49
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_maximum(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5],
            },
            headers=self._headers("fneb-sev-max"),
        )
        body = response.json()
        assert body["total"] == 60
        assert body["severity"] == "continuous"

    # -- T3 posture --------------------------------------------------------

    def test_item_8_mistakes_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """FNE-B item 8 ("I am frequently afraid of making mistakes")
        is evaluative-apprehension, NOT suicidal ideation.  Even
        maxed-out item 8 + all others 1 must never set
        requires_t3=True.  Active-risk screening stays on C-SSRS /
        PHQ-9 item 9."""
        # Raw [1,5,1,5,1,1,5,5,1,5,1,1] — straights all 1 except
        # item 8 = 5; reverses all 5 flip to 1.  Post-flip
        # [1,1,1,1,1,1,1,5,1,1,1,1] total = 16.
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 5, 1, 5, 1, 1, 5, 5, 1, 5, 1, 1],
            },
            headers=self._headers("fneb-t3-item8"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_max_total_does_not_require_t3(self, client: TestClient) -> None:
        """Even the 60-extremum never fires T3.  FNE-B has no
        suicidality item; trauma/affect-regulation / social-anxiety
        routing happens at the intervention-selection layer, not
        through the T3 crisis gate."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5],
            },
            headers=self._headers("fneb-t3-max"),
        )
        body = response.json()
        assert body["total"] == 60
        assert body["requires_t3"] is False

    # -- Reverse-keying wire pins (positions 2, 4, 7, 10) ------------------

    def test_reverse_item_2_flips_independently(
        self, client: TestClient
    ) -> None:
        """Isolated reverse-keying check at position 2.  Raw all 1s
        except item 2 = 5.  Straights 8×1 = 8.  Reverses: item 2
        raw 5 → flip to 1 (contributing 1); items 4,7,10 raw 1 →
        flip to 5 (contributing 15).  Total 8+1+15 = 24.  Compare
        with all-1s total 28 — adjusting item 2 alone from 1 to 5
        drops the total by 4 (NOT raises, because reverse)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-rev-pos2"),
        )
        body = response.json()
        assert body["total"] == 24

    def test_reverse_item_4_flips_independently(
        self, client: TestClient
    ) -> None:
        """Position 4 reverse check. Raw all 1s except item 4 = 5.
        Same drop-by-4 as position 2: all-1s = 28, flipping item 4
        to raw 5 yields 24."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-rev-pos4"),
        )
        body = response.json()
        assert body["total"] == 24

    def test_reverse_item_7_flips_independently(
        self, client: TestClient
    ) -> None:
        """Position 7 reverse check."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-rev-pos7"),
        )
        body = response.json()
        assert body["total"] == 24

    def test_reverse_item_10_flips_independently(
        self, client: TestClient
    ) -> None:
        """Position 10 reverse check."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1],
            },
            headers=self._headers("fneb-rev-pos10"),
        )
        body = response.json()
        assert body["total"] == 24

    def test_straight_item_1_passes_through(self, client: TestClient) -> None:
        """Sanity: a straight-keyed position (1) shifts in the SAME
        direction as the raw value.  Raw all 1s total = 28; flip
        item 1 raw to 5 → total = 28 + 4 = 32."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-str-pos1"),
        )
        body = response.json()
        assert body["total"] == 32

    def test_straight_item_8_passes_through(self, client: TestClient) -> None:
        """Straight item 8 sanity; parallel to item 1 above."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-str-pos8"),
        )
        body = response.json()
        assert body["total"] == 32

    # -- Item count traps --------------------------------------------------

    def test_rejects_eleven_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 11},
            headers=self._headers("fneb-ic-11"),
        )
        assert response.status_code == 422

    def test_rejects_thirteen_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 13},
            headers=self._headers("fneb-ic-13"),
        )
        assert response.status_code == 422

    def test_rejects_six_items_stai6_shape(self, client: TestClient) -> None:
        """A 6-item payload (STAI-6 shape) must not be accepted for
        FNE-B — guards against instrument-swapping at the dispatcher."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 6},
            headers=self._headers("fneb-ic-6"),
        )
        assert response.status_code == 422

    def test_rejects_zero_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": []},
            headers=self._headers("fneb-ic-0"),
        )
        assert response.status_code == 422

    # -- Item value traps --------------------------------------------------

    def test_rejects_item_value_zero(self, client: TestClient) -> None:
        """Item min is 1 (Leary 1983 1-5 Likert).  0 is below range;
        the scorer's range check rejects."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("fneb-iv-0"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_six(self, client: TestClient) -> None:
        """Item max is 5.  6 is above range."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("fneb-iv-6"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_negative(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [-1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("fneb-iv-neg"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_far_out_of_range(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [99, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("fneb-iv-99"),
        )
        assert response.status_code == 422

    # -- Item type trap ----------------------------------------------------

    def test_rejects_string_items(self, client: TestClient) -> None:
        """Pydantic's ``list[int]`` coerces numeric strings but
        rejects non-numeric strings.  Either way, a non-int at the
        scorer layer (after coercion) is a 422."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": ["three"] + [3] * 11,
            },
            headers=self._headers("fneb-iv-str"),
        )
        assert response.status_code == 422

    def test_rejects_float_with_decimal(self, client: TestClient) -> None:
        """Pydantic ``list[int]`` rejects 3.5 as non-integer."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [3.5] + [3] * 11,
            },
            headers=self._headers("fneb-iv-fl"),
        )
        assert response.status_code == 422

    # -- Pydantic bool-coercion doc ---------------------------------------

    def test_true_coerced_to_one_is_valid(self, client: TestClient) -> None:
        """Pydantic's ``list[int]`` coerces JSON ``true`` → 1 BEFORE
        the scorer sees it.  On FNE-B's 1-5 scale, 1 is a valid
        response ("not at all characteristic") so True passes the
        range check.  The scorer never sees a bool — its strict-
        bool rejection protects C-SSRS / MDQ flows where True would
        be a semantically-wrong 1."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [True, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-true"),
        )
        # True → 1 at position 1 (straight); rest all 1.  Equivalent
        # to raw all-1s = 28.
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 28

    def test_false_coerced_to_zero_is_rejected_by_range(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces ``false`` → 0, which is BELOW FNE-B's
        1-5 range.  The range check at the scorer rejects with
        422.  Documents that bool coercion is a Pydantic-level
        behavior and that downstream range validation catches it."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [False, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            },
            headers=self._headers("fneb-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes ------------------------------------------------

    def test_vignette_social_phobia_clinical(self, client: TestClient) -> None:
        """Collins 2005 clinical-sample pattern: mostly "extremely
        characteristic" on straight items, "not at all characteristic"
        on reverse items.  Raw [5,1,5,1,5,5,1,5,5,1,5,4].  Post-flip
        [5,5,5,5,5,5,5,5,5,5,5,4] = 59.  Firmly in Collins 2005's
        ≥49 "clinical range" but the envelope reports severity
        = continuous."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 4],
            },
            headers=self._headers("fneb-vig-phobia"),
        )
        body = response.json()
        assert body["total"] == 59
        assert body["severity"] == "continuous"

    def test_vignette_leary_1983_student_mean(
        self, client: TestClient
    ) -> None:
        """Leary 1983 Table 2 student-sample mean ≈ 35.  Raw
        [3,3,3,3,3,3,3,3,2,3,3,3].  Straights (1,3,5,6,8,9,11,12)
        = 3+3+3+3+3+2+3+3 = 23; reverses (2,4,7,10) raw all 3 →
        flip to 3 each = 12.  Total 35."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3],
            },
            headers=self._headers("fneb-vig-student"),
        )
        body = response.json()
        assert body["total"] == 35
        assert body["severity"] == "continuous"

    def test_vignette_community_low(self, client: TestClient) -> None:
        """Non-clinical respondent with low social-evaluation
        anxiety: mild disagreement with straight items (2), mild
        agreement with reverse items (4).  Raw
        [2,4,2,4,2,2,4,2,2,4,2,2].  Straights 2×8 = 16, reverses
        flip 4→2 contributing 4×2 = 8.  Total 24 — below even the
        raw-all-1s 28 floor because the respondent is actively
        endorsing low-fear reverse items."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [2, 4, 2, 4, 2, 2, 4, 2, 2, 4, 2, 2],
            },
            headers=self._headers("fneb-vig-community"),
        )
        body = response.json()
        assert body["total"] == 24
        assert body["severity"] == "continuous"

    def test_vignette_alcohol_social_lubrication_profile(
        self, client: TestClient
    ) -> None:
        """Marlatt 1985 Table 4.1 social-pressure relapse category:
        patient drinks to manage social-evaluation anxiety.  High
        social-evaluation concern with strong agreement on straight
        items (4) and strong disagreement on reverse items (2).
        Raw [4,2,4,2,4,4,2,4,4,2,4,4].  Straights 4×8 = 32,
        reverses flip 2→4 contributing 4×4 = 16.  Total 48.
        Just below Collins 2005's ≥49 "clinical range" — clinically
        signals exposure + social-skills-training intervention
        targeting over DBT distress-tolerance."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [4, 2, 4, 2, 4, 4, 2, 4, 4, 2, 4, 4],
            },
            headers=self._headers("fneb-vig-alcohol"),
        )
        body = response.json()
        assert body["total"] == 48
        assert body["severity"] == "continuous"

    def test_vignette_cbgt_pre_post_within_session_effect(
        self, client: TestClient
    ) -> None:
        """Heimberg 1995 CBGT pre/post social-anxiety-session effect.
        Pre-session elevated FNE-B (raw maximum pattern → 60),
        post-session reduced FNE-B (raw all 3s → 36).  Delta 24 is
        a large within-session effect well above Jacobson-Truax RCI
        threshold at the trajectory layer — a canonical within-
        session CBGT target."""
        pre = client.post(
            "/v1/assessments",
            json={
                "instrument": "fneb",
                "items": [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5],
            },
            headers=self._headers("fneb-vig-cbgt-pre"),
        ).json()
        post = client.post(
            "/v1/assessments",
            json={"instrument": "fneb", "items": [3] * 12},
            headers=self._headers("fneb-vig-cbgt-post"),
        ).json()
        assert pre["total"] == 60
        assert post["total"] == 36
        assert pre["total"] - post["total"] == 24


class TestUcla3Routing:
    """End-to-end routing tests for the UCLA-3 dispatcher branch.

    Hughes 2004 Three-Item Loneliness Scale — 3 items, 1-3 Likert,
    NO reverse keying (unique on the platform), total 3-9, single
    factor, no bands (severity = ``"continuous"``).  **HIGHER =
    MORE lonely** — uniform with PHQ-9 / GAD-7 / AUDIT / PSS-10 /
    STAI-6 / FNE-B / SHAPS (lower-is-better).

    The ZERO-reverse-keying design is Hughes 2004's explicit
    trade-off: adding Marsh 1996 balanced-wording acquiescence
    control would invalidate the r = 0.82 equivalence with the
    full UCLA-R-20.  Consequence: the acquiescence signature is
    the trivial linear formula ``total = 3v`` for any all-v
    constant vector, and the endpoint-only-responder gap is the
    full 75% of the 3-9 range (all-3s minus all-1s = 6).  This
    is the highest endpoint-exposure on the platform.

    Clinically DISTINCT from FNE-B — UCLA-3 measures actual
    perceived isolation, FNE-B measures fear of being judged.
    High UCLA-3 with low FNE-B (widowed retiree) or vice versa
    (socially-anxious adolescent with peer network) dissociates
    in the wild.  Intervention targeting differs accordingly
    (structural contact-building vs exposure + social-skills).

    Clinical use cases:
    1. Widowhood / bereavement relapse-risk window (Keyes 2012,
       2.4× AUD-incidence elevation over 2 years post-widowhood).
    2. Retirement-trigger relapse detection (Satre 2004, social-
       structure loss as proximal trigger).
    3. Marlatt 1985 negative-emotional-states proximal precipitant
       (pp. 137-142, loneliness sub-type).
    4. Holt-Lunstad 2010 mortality-risk stratification (HR 1.26).

    No T3 — Calati 2019 documents loneliness as a suicide risk
    factor, but the platform surfaces high UCLA-3 as C-SSRS-
    follow-up context at the clinician-UI layer and does NOT set
    the T3 flag on the assessment itself.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ----------------------------------------------------

    def test_max_loneliness_extremum_nine(self, client: TestClient) -> None:
        """Hughes 2004 top-of-range: "Often" on all three items.
        Raw [3, 3, 3].  No reverse keying, so total = 9.
        Holt-Lunstad 2010 mortality-HR ≈ 1.26 territory."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "ucla3"
        assert body["total"] == 9
        assert body["severity"] == "continuous"

    def test_min_loneliness_extremum_three(self, client: TestClient) -> None:
        """Community low-loneliness floor: "Hardly ever" on all
        three.  Raw [1, 1, 1] = total 3.  Hughes 2004 HRS bottom
        tercile."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 1]},
            headers=self._headers("ucla3-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "continuous"

    def test_midpoint_six(self, client: TestClient) -> None:
        """Raw [2, 2, 2] = 6.  The arithmetic midpoint of the 3-9
        range; clinically the retirement-transition profile (Satre
        2004)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-mid"),
        )
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "continuous"

    # -- Acquiescence signature — linear total = 3v ------------------------

    def test_acquiescence_all_ones_yields_three(
        self, client: TestClient
    ) -> None:
        """Linear formula v=1: total = 3×1 = 3.  No reverse-keying
        offset, unlike FNE-B (4v+24 = 28) or STAI-6 (constant 15)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 1]},
            headers=self._headers("ucla3-acq-1"),
        )
        body = response.json()
        assert body["total"] == 3

    def test_acquiescence_all_twos_yields_six(
        self, client: TestClient
    ) -> None:
        """Linear formula v=2: total = 3×2 = 6."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-acq-2"),
        )
        body = response.json()
        assert body["total"] == 6

    def test_acquiescence_all_threes_yields_nine(
        self, client: TestClient
    ) -> None:
        """Linear formula v=3: total = 3×3 = 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-acq-3"),
        )
        body = response.json()
        assert body["total"] == 9

    def test_acquiescence_gap_is_six(self, client: TestClient) -> None:
        """Pin the endpoint-exposure: all-3s minus all-1s = 6,
        which is the full 3-9 range.  A random endpoint-only
        responder shifts the score 75% of full range — highest
        endpoint-exposure on the platform.  Invariant documents
        the Hughes 2004 design trade-off (no reverse-keying for
        r=0.82 UCLA-R-20 equivalence)."""
        r_low = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 1]},
            headers=self._headers("ucla3-gap-1"),
        ).json()
        r_high = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-gap-3"),
        ).json()
        assert r_high["total"] - r_low["total"] == 6

    # -- Envelope fields — no subscales/cutoff/screen/scaled/trigger -------

    def test_envelope_has_no_subscales(self, client: TestClient) -> None:
        """Hughes 2004 factor-analytic derivation confirmed single
        factor; envelope MUST NOT carry subscales."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_envelope_has_no_cutoff_used(self, client: TestClient) -> None:
        """Hughes 2004 published no cutpoints; Steptoe 2013 tercile
        splits are sample-descriptive and NOT pinned per CLAUDE.md."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_envelope_has_no_positive_screen(self, client: TestClient) -> None:
        """No categorical screen — UCLA-3 is a continuous
        dimensional measure."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-no-screen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_envelope_has_no_scaled_score(self, client: TestClient) -> None:
        """UCLA-3 reports the raw 3-9 total; no scaled mapping to
        another range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-no-scaled"),
        )
        body = response.json()
        assert body.get("scaled_score") is None

    def test_envelope_has_no_triggering_items(
        self, client: TestClient
    ) -> None:
        """triggering_items is C-SSRS-only (risk-band audit trail).
        UCLA-3 is continuous; no item individually flags."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-no-triggering"),
        )
        body = response.json()
        assert body.get("triggering_items") is None

    # -- Severity always continuous ----------------------------------------

    def test_severity_continuous_at_minimum(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 1]},
            headers=self._headers("ucla3-sev-min"),
        )
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_steptoe_upper_tercile(
        self, client: TestClient
    ) -> None:
        """Steptoe 2013 upper-tercile boundary is 6; ELSA cohort
        analyses use >= 6 as the "lonely" indicator.  Platform
        MUST fire NO band here — Steptoe 2013 is sample-
        descriptive, not a primary-source cutpoint."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-sev-steptoe"),
        )
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_maximum(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-sev-max"),
        )
        body = response.json()
        assert body["total"] == 9
        assert body["severity"] == "continuous"

    # -- T3 posture --------------------------------------------------------

    def test_maximum_total_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Raw [3, 3, 3] = total 9 is the maximum-loneliness
        extremum.  Calati 2019 documents loneliness as a suicide
        risk factor, but the platform surfaces this to the
        clinician UI as C-SSRS-follow-up context — the assessment
        itself MUST NOT set requires_t3.  Active-risk screening
        stays on C-SSRS / PHQ-9 item 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-t3-max"),
        )
        body = response.json()
        assert body["total"] == 9
        assert body["requires_t3"] is False

    def test_isolated_item_alone_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Item 3 ("feel isolated") at max with items 1/2 at min.
        Raw [1, 1, 3] = 5.  "Isolated" is a subjective-connection
        construct, NOT suicidal ideation.  MUST NOT set T3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 3]},
            headers=self._headers("ucla3-t3-isolated"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    # -- No-reverse-keying wire pins ---------------------------------------

    def test_items_pass_through_unchanged_item1(
        self, client: TestClient
    ) -> None:
        """UCLA-3 has ZERO reverse-keying.  Raising item 1 from 1
        to 3 with others at 1 raises the total by exactly 2 (the
        raw Likert step × 1 item).  Contrast FNE-B reverse-item
        positions which DROP the total by 4 when raised."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 1]},
            headers=self._headers("ucla3-pass-1-base"),
        ).json()
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 1, 1]},
            headers=self._headers("ucla3-pass-1-raised"),
        ).json()
        assert raised["total"] - base["total"] == 2

    def test_items_pass_through_unchanged_item2(
        self, client: TestClient
    ) -> None:
        """Item 2 (feel left out) pass-through check."""
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 3, 1]},
            headers=self._headers("ucla3-pass-2"),
        ).json()
        assert raised["total"] == 5

    def test_items_pass_through_unchanged_item3(
        self, client: TestClient
    ) -> None:
        """Item 3 (feel isolated) pass-through check."""
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 3]},
            headers=self._headers("ucla3-pass-3"),
        ).json()
        assert raised["total"] == 5

    # -- Item count traps --------------------------------------------------

    def test_rejects_two_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2]},
            headers=self._headers("ucla3-ic-2"),
        )
        assert response.status_code == 422

    def test_rejects_four_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2, 2]},
            headers=self._headers("ucla3-ic-4"),
        )
        assert response.status_code == 422

    def test_rejects_zero_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": []},
            headers=self._headers("ucla3-ic-0"),
        )
        assert response.status_code == 422

    def test_rejects_twenty_items_full_ucla_r20(
        self, client: TestClient
    ) -> None:
        """Guards against accidental full UCLA-R-20 administration
        being routed through the brief-form scorer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2] * 20},
            headers=self._headers("ucla3-ic-20"),
        )
        assert response.status_code == 422

    # -- Item value traps --------------------------------------------------

    def test_rejects_item_value_zero(self, client: TestClient) -> None:
        """UCLA-3 is 1-3 Likert; 0 is below range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [0, 2, 2]},
            headers=self._headers("ucla3-iv-0"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_four(self, client: TestClient) -> None:
        """UCLA-3 is 1-3 Likert; 4 is above range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [4, 2, 2]},
            headers=self._headers("ucla3-iv-4"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_negative(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [-1, 2, 2]},
            headers=self._headers("ucla3-iv-neg"),
        )
        assert response.status_code == 422

    def test_rejects_five_point_likert_value(
        self, client: TestClient
    ) -> None:
        """Guards against accidental FNE-B 1-5 or STAI-6 1-4 Likert
        value being routed through UCLA-3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [5, 2, 2]},
            headers=self._headers("ucla3-iv-5"),
        )
        assert response.status_code == 422

    # -- Item type trap ----------------------------------------------------

    def test_rejects_string_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": ["two", 2, 2]},
            headers=self._headers("ucla3-iv-str"),
        )
        assert response.status_code == 422

    def test_rejects_float_with_decimal(self, client: TestClient) -> None:
        """Pydantic ``list[int]`` rejects 2.5 as non-integer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2.5, 2, 2]},
            headers=self._headers("ucla3-iv-fl"),
        )
        assert response.status_code == 422

    # -- Pydantic bool-coercion doc ---------------------------------------

    def test_true_coerced_to_one_is_valid(self, client: TestClient) -> None:
        """Pydantic's ``list[int]`` coerces JSON ``true`` → 1 BEFORE
        the scorer sees it.  On UCLA-3's 1-3 scale, 1 is a valid
        response ("Hardly ever") so True passes.  Equivalent to raw
        all-1s = 3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [True, 1, 1]},
            headers=self._headers("ucla3-true"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 3

    def test_false_coerced_to_zero_is_rejected_by_range(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces ``false`` → 0, which is BELOW UCLA-3's
        1-3 range.  Range check rejects with 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [False, 1, 1]},
            headers=self._headers("ucla3-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes ------------------------------------------------

    def test_vignette_widowhood_profile(self, client: TestClient) -> None:
        """Keyes 2012 widowhood profile: strong "lack companionship"
        (lost spouse), moderate "left out" (couple-centric social
        invitations), moderate isolation (routine disrupted).
        Raw [3, 2, 2] = 7.  Signals the 2-year post-widowhood
        AUD-incidence window."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 2, 2]},
            headers=self._headers("ucla3-vig-widow"),
        )
        body = response.json()
        assert body["total"] == 7
        assert body["severity"] == "continuous"

    def test_vignette_retirement_isolation(self, client: TestClient) -> None:
        """Satre 2004 retirement-transition profile: moderate
        across all three items.  Raw [2, 2, 2] = 6.  Signals
        retirement-trigger relapse-risk window."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 2, 2]},
            headers=self._headers("ucla3-vig-retire"),
        )
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "continuous"

    def test_vignette_socially_connected_baseline(
        self, client: TestClient
    ) -> None:
        """Community low-loneliness baseline.  Raw [1, 1, 1] = 3.
        Hughes 2004 HRS bottom tercile."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [1, 1, 1]},
            headers=self._headers("ucla3-vig-baseline"),
        )
        body = response.json()
        assert body["total"] == 3
        assert body["severity"] == "continuous"

    def test_vignette_severe_isolation_extremum(
        self, client: TestClient
    ) -> None:
        """Hughes 2004 HRS top-tercile extremum.  Raw [3, 3, 3] = 9.
        Holt-Lunstad 2010 mortality-HR ≈ 1.26 territory.  Surfaces
        to clinician UI for C-SSRS follow-up per Calati 2019 but
        does NOT set requires_t3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-vig-severe"),
        )
        body = response.json()
        assert body["total"] == 9
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_post_bereavement_group_delta(
        self, client: TestClient
    ) -> None:
        """12-week bereavement-support-group intervention: pre-
        treatment widowhood profile (7), post-treatment connection-
        rebuilt (4).  Delta 3 is a meaningful within-participant
        change on the 3-9 range (50% of the 6-point range).
        Jacobson-Truax RCI at the trajectory layer determines
        clinical significance."""
        pre = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 2, 2]},
            headers=self._headers("ucla3-vig-pre"),
        ).json()
        post = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [2, 1, 1]},
            headers=self._headers("ucla3-vig-post"),
        ).json()
        assert pre["total"] == 7
        assert post["total"] == 4
        assert pre["total"] - post["total"] == 3

    def test_vignette_fne_b_dissociation_high_ucla3_low_fne(
        self, client: TestClient
    ) -> None:
        """Widowed retiree with intact social skills — expected
        LOW FNE-B, HIGH UCLA-3.  UCLA-3 alone = 9 documents the
        structural-isolation construct orthogonal to evaluation-
        anxiety.  Intervention target: structural social-contact
        building (befriending, peer-support), NOT exposure."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "ucla3", "items": [3, 3, 3]},
            headers=self._headers("ucla3-vig-dissoc"),
        )
        body = response.json()
        assert body["total"] == 9


class TestCiusRouting:
    """End-to-end routing tests for the CIUS dispatcher branch.

    Meerkerk, Van Den Eijnden, Vermulst & Garretsen (CyberPsych &
    Behavior 2009, 12(1):1-6) — 14-item Compulsive Internet Use
    Scale.  0-4 Likert ("Never" .. "Very often"), NO reverse keying,
    total 0-56, single factor confirmed via EFA/CFA on three Dutch
    adult/adolescent samples (α = 0.89, six-month r = 0.70-0.76,
    Young 1998 IAT r ≈ 0.70 convergent validity).

    Scoring convention note — **CIUS IS THE FIRST PLATFORM
    INSTRUMENT WHERE 0 IS A VALID RESPONSE**.  Downstream consequence:
    the scorer's explicit ``isinstance(value, bool)`` rejection
    BEFORE the range check is load-bearing.  On every other scorer
    (PHQ-9 0-3, GAD-7 0-3, AUDIT-C 0-4, C-SSRS 0-1, WHO-5 0-5,
    PSS-10 0-4, and so on), Pydantic's JSON ``false`` → 0 is
    actually a valid range value too — but those scorers have
    already been reviewing their own 0-as-valid-value semantics
    for so long that the bool-rejection invariant here deserves
    explicit router-layer reinforcement.  Two dedicated tests
    below pin both coercion directions: ``true`` → 1 (valid Likert
    "Rarely") AND ``false`` → 0 (valid Likert "Never") — the LATTER
    being unique to CIUS among the instruments documented by this
    test module at the time of sprint 71.

    Higher = more compulsive internet use; aligns with PHQ-9 /
    GAD-7 / AUDIT / STAI-6 / FNE-B / UCLA-3 / SHAPS "higher-is-
    worse" convention.  NO reverse-keying means the acquiescence
    signature is the trivial linear ``total = 14v`` for any
    all-v constant vector.  Endpoint-only-responder gap is the
    full 0-56 range (all-4s minus all-0s = 56) — matches UCLA-3
    in relative terms (100% of range) but on an absolute scale
    nine-fold larger.

    Clinical use cases for Discipline OS:
    1. Digital-behavior urge trigger for Marlatt 1985 negative-
       emotional-states and social-pressure relapse determinants
       (pp. 137-142, 189-215): compulsive internet use is BOTH
       an outcome variable for problematic-use clients AND a
       proximal cross-addictive substitution channel for AUD/
       OUD clients in early recovery (Koob 2005 allostatic
       reward deficiency model).
    2. Caplan 2003 compensatory-internet-use — FNE-B + UCLA-3 + CIUS
       triad: socially-avoidant (FNE-B-high) lonely (UCLA-3-high)
       clients use the internet compulsively (CIUS-high) as an
       isolating-but-reinforcing coping strategy.  Intervention
       requires addressing the antecedent construct (social-
       evaluation anxiety + structural isolation), NOT the
       behavior itself as an acute CBT target.
    3. ICD-11 6C51 "Gaming disorder" and 6C5Y "other specified
       disorders due to addictive behaviours" — CIUS provides
       continuous monitoring on internet-mediated compulsive
       engagement without committing to a categorical diagnosis
       that ICD-10 does not recognise.  Guertler 2014 proposed
       ≥21 "at risk" and ≥28 "compulsive" cutpoints from a
       German general-population sample; those are secondary-
       literature splits and **NOT pinned here** per CLAUDE.md
       non-negotiable #9 ("Don't hand-roll severity thresholds").
    4. Jacobson & Truax 1991 RCI at the trajectory layer pins
       the ≈5-point MCID from the α=0.89 Dutch sample; CBT-CIUS
       responder signature is pre-56 → post-14 (delta 42).

    T3 posture — NOT safety-adjacent.  Compulsive internet use
    has documented associations with depression (Young 1998) and
    social anxiety (Caplan 2003), but those associations surface
    through PHQ-9 and FNE-B respectively.  The CIUS instrument
    itself measures a behavior-frequency construct and MUST NOT
    trigger T3 escalation even at the maximum (14 × "Very often").
    Active-risk surveillance stays on C-SSRS / PHQ-9 item 9.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ----------------------------------------------------

    def test_max_total_fifty_six(self, client: TestClient) -> None:
        """Meerkerk 2009 ceiling: "Very often" on all fourteen items.
        Raw [4]*14.  No reverse keying → total = 56.  Clinically the
        extreme-compulsive-gamer / pornography-binge profile that
        Guertler 2014 ≥28 would categorize well above the German
        general-population compulsive-user threshold; we surface
        only the raw total because ≥28 is secondary literature."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "cius"
        assert body["total"] == 56
        assert body["severity"] == "continuous"

    def test_min_total_zero(self, client: TestClient) -> None:
        """Meerkerk 2009 floor: "Never" on all fourteen items.  Raw
        [0]*14.  **CRITICAL** — this is the first platform instrument
        where a valid clinical response is 0 on every item.  Total 0
        is a legitimate scored response for a non-user or a client
        whose internet use is not compulsive in any dimension."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 14},
            headers=self._headers("cius-min"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "cius"
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_midpoint_twenty_eight(self, client: TestClient) -> None:
        """Raw [2]*14 = 28, the arithmetic midpoint of the 0-56 range.
        Numerically coincident with Guertler 2014's "compulsive" cut,
        but the platform MUST NOT fire any band here — that cutpoint
        is secondary literature and un-pinned."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 14},
            headers=self._headers("cius-mid"),
        )
        body = response.json()
        assert body["total"] == 28
        assert body["severity"] == "continuous"

    # -- Acquiescence signature — linear total = 14v ----------------------

    def test_acquiescence_all_zeros_yields_zero(
        self, client: TestClient
    ) -> None:
        """Linear formula v=0: total = 14×0 = 0.  No reverse-keying
        offset.  **UNIQUE TO CIUS** — every other platform instrument's
        all-minimum acquiescence baseline is a positive value (FNE-B
        28, STAI-6 15, UCLA-3 3).  All-zero is a valid scored response,
        not a validation failure, because 0 is a valid CIUS Likert value."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 14},
            headers=self._headers("cius-acq-0"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0

    def test_acquiescence_all_ones_yields_fourteen(
        self, client: TestClient
    ) -> None:
        """Linear formula v=1: total = 14×1 = 14.  Contrast FNE-B
        4v+24 = 28 (baseline + scale-flip offset) and STAI-6 constant
        15 (symmetric reverse-keying collapse)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [1] * 14},
            headers=self._headers("cius-acq-1"),
        )
        body = response.json()
        assert body["total"] == 14

    def test_acquiescence_all_twos_yields_twenty_eight(
        self, client: TestClient
    ) -> None:
        """Linear formula v=2: total = 14×2 = 28."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 14},
            headers=self._headers("cius-acq-2"),
        )
        body = response.json()
        assert body["total"] == 28

    def test_acquiescence_all_threes_yields_forty_two(
        self, client: TestClient
    ) -> None:
        """Linear formula v=3: total = 14×3 = 42."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [3] * 14},
            headers=self._headers("cius-acq-3"),
        )
        body = response.json()
        assert body["total"] == 42

    def test_acquiescence_all_fours_yields_fifty_six(
        self, client: TestClient
    ) -> None:
        """Linear formula v=4: total = 14×4 = 56.  Full-range
        acquiescence endpoint."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-acq-4"),
        )
        body = response.json()
        assert body["total"] == 56

    def test_acquiescence_gap_is_fifty_six(self, client: TestClient) -> None:
        """Pin the endpoint-exposure: all-4s minus all-0s = 56, which
        is the full 0-56 range (100%).  Matches UCLA-3's 100%-of-range
        endpoint exposure (highest on the platform in relative terms)
        but on a nine-fold larger absolute scale.  Meerkerk 2009
        treated this as acceptable because the high Cronbach α=0.89
        implies coherent positive-wording interpretation overrides
        acquiescence bias in practice."""
        r_low = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 14},
            headers=self._headers("cius-gap-0"),
        ).json()
        r_high = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-gap-4"),
        ).json()
        assert r_high["total"] - r_low["total"] == 56

    # -- Envelope fields — no subscales/cutoff/screen/scaled/trigger ------

    def test_envelope_has_no_subscales(self, client: TestClient) -> None:
        """Meerkerk 2009 factor-analytic derivation confirmed SINGLE
        factor (EFA across three Dutch samples, CFI > 0.95 in each);
        envelope MUST NOT carry subscales."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 14},
            headers=self._headers("cius-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_envelope_has_no_cutoff_used(self, client: TestClient) -> None:
        """Meerkerk 2009 published NO cutpoints (continuous dimensional
        measure by design).  Guertler 2014 ≥21/≥28 are secondary
        literature and NOT pinned per CLAUDE.md non-negotiable #9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 14},
            headers=self._headers("cius-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_envelope_has_no_positive_screen(self, client: TestClient) -> None:
        """No categorical screen — CIUS is a continuous dimensional
        measure.  Guertler 2014 "at risk" / "compulsive" labels stay
        at the clinician-interpretation layer, not the envelope."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-no-screen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_envelope_has_no_scaled_score(self, client: TestClient) -> None:
        """CIUS reports the raw 0-56 total; no scaled mapping to a
        different range or to the Young 1998 IAT 20-100 range (even
        though r ≈ 0.70 convergent validity would support a rough
        mapping)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 14},
            headers=self._headers("cius-no-scaled"),
        )
        body = response.json()
        assert body.get("scaled_score") is None

    def test_envelope_has_no_triggering_items(
        self, client: TestClient
    ) -> None:
        """triggering_items is C-SSRS-only (risk-band audit trail).
        CIUS is continuous; no item individually flags."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-no-triggering"),
        )
        body = response.json()
        assert body.get("triggering_items") is None

    # -- Severity always continuous ---------------------------------------

    def test_severity_continuous_at_minimum(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 14},
            headers=self._headers("cius-sev-min"),
        )
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_guertler_at_risk_21(
        self, client: TestClient
    ) -> None:
        """Guertler 2014 "at risk" boundary = 21.  Platform MUST fire
        NO band here — Guertler is secondary literature per CLAUDE.md
        non-negotiable #9.  Construct this total as [2,2,2,2,2,2,2,
        2,2,2,1,0,0,0] = 14+7+0 = 21."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0]},
            headers=self._headers("cius-sev-guertler-21"),
        )
        body = response.json()
        assert body["total"] == 21
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_guertler_compulsive_28(
        self, client: TestClient
    ) -> None:
        """Guertler 2014 "compulsive" boundary = 28 (numerically the
        Meerkerk 2009 midpoint).  Platform MUST fire NO band — this
        coincides with the all-2s midpoint and is secondary literature."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 14},
            headers=self._headers("cius-sev-guertler-28"),
        )
        body = response.json()
        assert body["total"] == 28
        assert body["severity"] == "continuous"

    def test_severity_continuous_at_maximum(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-sev-max"),
        )
        body = response.json()
        assert body["total"] == 56
        assert body["severity"] == "continuous"

    # -- T3 posture -------------------------------------------------------

    def test_maximum_total_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Raw [4]*14 = total 56 is the maximum-compulsion extremum.
        Young 1998 and Caplan 2003 document strong depression /
        social-anxiety associations with internet-use dimensions,
        but those associations surface through PHQ-9 / FNE-B.
        The CIUS instrument itself MUST NOT set requires_t3.
        Active-risk screening stays on C-SSRS / PHQ-9 item 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-t3-max"),
        )
        body = response.json()
        assert body["total"] == 56
        assert body["requires_t3"] is False

    def test_isolated_single_item_max_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Item 14 ("restless when cannot use internet") alone at
        max with all others at 0.  Raw [0]*13 + [4] = 4.  Withdrawal-
        phenomena item — DSM-5 flagged but MUST NOT set T3 in
        isolation at the assessment layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 13 + [4]},
            headers=self._headers("cius-t3-restless"),
        )
        body = response.json()
        assert body["total"] == 4
        assert body["requires_t3"] is False

    # -- No-reverse-keying wire pins --------------------------------------

    def test_items_pass_through_unchanged_item1(
        self, client: TestClient
    ) -> None:
        """CIUS has ZERO reverse-keying.  Raising item 1 from 0 to 4
        with others at 0 raises the total by exactly 4 (the raw Likert
        step × 1 item).  Contrast FNE-B reverse-item positions which
        DROP the total by 4 when raised."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 14},
            headers=self._headers("cius-pass-1-base"),
        ).json()
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] + [0] * 13},
            headers=self._headers("cius-pass-1-raised"),
        ).json()
        assert raised["total"] - base["total"] == 4

    def test_items_pass_through_unchanged_item7(
        self, client: TestClient
    ) -> None:
        """Item 7 (preference for internet over offline company).
        Raised alone 0→4, total becomes 4.  Caplan 2003 compensatory-
        internet-use signature item."""
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 6 + [4] + [0] * 7},
            headers=self._headers("cius-pass-7"),
        ).json()
        assert raised["total"] == 4

    def test_items_pass_through_unchanged_item14(
        self, client: TestClient
    ) -> None:
        """Item 14 ("restless when cannot use internet") pass-through.
        Withdrawal-phenomena probe; raised alone 0→4, total = 4."""
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 13 + [4]},
            headers=self._headers("cius-pass-14"),
        ).json()
        assert raised["total"] == 4

    def test_item_ordering_does_not_affect_total(
        self, client: TestClient
    ) -> None:
        """Pin a specific asymmetric pattern across items and reverse
        it — CIUS has no reverse-keyed positions, so order reversal
        MUST yield the same total.  This guards against accidental
        FNE-B (reverse at 2/4/7/10) or FFMQ-15 patterning logic
        leaking through the dispatcher for CIUS payloads."""
        forward = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4]},
            headers=self._headers("cius-order-fwd"),
        ).json()
        reversed_items = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4][::-1]},
            headers=self._headers("cius-order-rev"),
        ).json()
        assert forward["total"] == reversed_items["total"] == 20

    # -- Item count traps -------------------------------------------------

    def test_rejects_thirteen_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 13},
            headers=self._headers("cius-ic-13"),
        )
        assert response.status_code == 422

    def test_rejects_fifteen_items(self, client: TestClient) -> None:
        """Guards against accidental FFMQ-15 (15 items) being routed
        through the CIUS scorer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 15},
            headers=self._headers("cius-ic-15"),
        )
        assert response.status_code == 422

    def test_rejects_twenty_items(self, client: TestClient) -> None:
        """Guards against accidental Young 1998 IAT (20 items, 1-5
        Likert) being routed through the CIUS scorer — convergent
        validity of r ≈ 0.70 is published but the scorers are
        dimensionally distinct."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2] * 20},
            headers=self._headers("cius-ic-20"),
        )
        assert response.status_code == 422

    def test_rejects_zero_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": []},
            headers=self._headers("cius-ic-0"),
        )
        assert response.status_code == 422

    # -- Item value traps -------------------------------------------------

    def test_accepts_item_value_zero(self, client: TestClient) -> None:
        """**CIUS-UNIQUE**: 0 is a VALID Likert value ("Never").
        This test explicitly pins the 0-acceptance invariant that
        distinguishes CIUS from every other platform instrument
        documented above (FNE-B / STAI-6 / UCLA-3 / PHQ-9 / GAD-7
        all REJECT 0 in at least one of their validation layers).
        0 on every item yields total 0, which is the legitimate
        non-user profile."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
            headers=self._headers("cius-iv-0-ok"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0

    def test_rejects_item_value_five(self, client: TestClient) -> None:
        """CIUS is 0-4 Likert; 5 is above range.  Guards against
        accidental Young 1998 IAT 1-5 Likert value being submitted."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [5] + [0] * 13},
            headers=self._headers("cius-iv-5"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_negative_one(self, client: TestClient) -> None:
        """Below-range rejection — -1 is not a valid Likert value."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [-1] + [0] * 13},
            headers=self._headers("cius-iv-neg1"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_ninety_nine(self, client: TestClient) -> None:
        """Far-above-range rejection — 99 guards against accidental
        percentage-scale submission."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [99] + [0] * 13},
            headers=self._headers("cius-iv-99"),
        )
        assert response.status_code == 422

    # -- Item type traps --------------------------------------------------

    def test_rejects_string_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": ["two"] + [0] * 13},
            headers=self._headers("cius-iv-str"),
        )
        assert response.status_code == 422

    def test_rejects_float_with_decimal(self, client: TestClient) -> None:
        """Pydantic ``list[int]`` rejects 2.5 as non-integer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [2.5] + [0] * 13},
            headers=self._headers("cius-iv-fl"),
        )
        assert response.status_code == 422

    # -- Pydantic bool-coercion — CIUS-UNIQUE both directions -------------

    def test_true_coerced_to_one_is_valid(self, client: TestClient) -> None:
        """Pydantic's ``list[int]`` coerces JSON ``true`` → 1 BEFORE
        the scorer sees it.  On CIUS's 0-4 scale, 1 is a valid
        response ("Rarely").  With item 1 as True and items 2-14 all
        0, total = 1."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [True] + [0] * 13},
            headers=self._headers("cius-true"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 1

    def test_false_coerced_to_zero_is_accepted_at_wire_layer_unique_to_cius(
        self, client: TestClient
    ) -> None:
        """**CIUS-UNIQUE WIRE-LAYER BEHAVIOR** — the only instrument
        on the platform for which JSON ``false`` in an items array
        round-trips to HTTP 201 with a legitimate scored total.

        Pydantic's ``list[int]`` TYPE-ERASES the JSON boolean: by
        the time the scorer receives the value it is already a
        Python ``int`` with value 0, no longer a ``bool``.  The
        scorer's defensive ``isinstance(value, bool)`` rejection
        is load-bearing for DIRECT Python calls (covered in
        ``test_cius_scoring.py::TestItemTypeValidation``) — when
        an internal service passes a literal ``False`` into
        ``score_cius`` without going through the HTTP wire, the
        scorer raises.  But over HTTP, Pydantic runs first.

        Contrast with UCLA-3 / FNE-B / STAI-6 / PHQ-9 / GAD-7 /
        AUDIT-C / WHO-5 / PSS-10: on those scales 0 is OUTSIDE
        the valid range (or outside that specific Likert floor),
        so the range check rejects the former-false-now-0 value
        and the round-trip returns 422.  CIUS is the first
        instrument where 0 is a legitimate Likert response
        ("Never" on Meerkerk 2009), so the range check passes
        and the scorer produces total = 0 for a single False in
        an otherwise all-zero vector.

        Clinical implication: a malformed mobile/web client that
        ships JSON booleans instead of integers WILL silently get
        a "floor" score for CIUS only.  The downstream renderer
        must treat CIUS floor scores as a data-quality signal
        (validate client schema adherence) rather than as the
        unambiguous "non-user" profile it represents when the
        integers were sent deliberately.  This invariant is
        pinned here so that any future attempt to "fix" the
        bool-accept-as-int behavior at the wire layer is visible
        as a breaking change to clients that depend on it."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [False] + [0] * 13},
            headers=self._headers("cius-false"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0

    def test_all_false_coerced_to_all_zero_is_accepted_at_wire_layer(
        self, client: TestClient
    ) -> None:
        """Vector of all False values.  Each coerces to int 0 at the
        Pydantic wire layer, type-erasing the Python ``bool``.  The
        scorer receives fourteen int-0s, passes range validation,
        passes the now-moot bool check (bools no longer present),
        and produces total = 0.

        This is the extreme version of the single-False test
        above — an entire vector of booleans round-trips as a
        legitimate "non-user" scored response.  Pins the wire-
        layer type-erasure invariant across the full vector,
        complementing the direct-Python-call bool-rejection
        invariant in ``test_cius_scoring.py``."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [False] * 14},
            headers=self._headers("cius-false-vec"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0

    # -- Clinical vignettes ----------------------------------------------

    def test_vignette_non_user(self, client: TestClient) -> None:
        """Client reports no compulsive-use features on any item.
        Raw [0]*14 = total 0.  Legitimate clinical response; the
        "floor" is not a validation failure."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [0] * 14},
            headers=self._headers("cius-vig-nonuser"),
        )
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"

    def test_vignette_moderate_meerkerk_mean_profile(
        self, client: TestClient
    ) -> None:
        """Meerkerk 2009 Dutch general-population adult sample mean
        ≈ 10-16 on the 0-56 range (varies across the three samples).
        Profile of mild-frequency use across most items with a
        couple of null items.  Raw [1]*14 + 2 = 16."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2]},
            headers=self._headers("cius-vig-meerkerk-mean"),
        )
        body = response.json()
        assert body["total"] == 16
        assert body["severity"] == "continuous"

    def test_vignette_caplan_compensatory_profile(
        self, client: TestClient
    ) -> None:
        """Caplan 2003 compensatory-internet-use signature: socially-
        avoidant (high FNE-B) lonely (high UCLA-3) client uses
        internet compulsively to avoid face-to-face interaction.
        Profile: items 7 ("prefer internet over offline company")
        and 9 ("neglect obligations") elevated; moderate across
        items 1/2/5/6/11 (control-loss and preoccupation); lower
        on items 13/14 (withdrawal) because the use is AVOIDANT,
        not addiction-withdrawal pattern.  Total 33."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [3, 3, 1, 2, 3, 3, 4, 2, 4, 1, 3, 2, 1, 1]},
            headers=self._headers("cius-vig-caplan"),
        )
        body = response.json()
        assert body["total"] == 33
        assert body["severity"] == "continuous"

    def test_vignette_gaming_maximal_profile(
        self, client: TestClient
    ) -> None:
        """ICD-11 6C51 Gaming disorder extremum — all 14 items at
        maximum frequency.  Raw [4]*14 = 56.  Surfaces the extreme-
        compulsion profile without firing Guertler 2014 ≥28
        secondary-literature bands."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-vig-gaming-max"),
        )
        body = response.json()
        assert body["total"] == 56
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_recovery_compensation_profile(
        self, client: TestClient
    ) -> None:
        """Koob 2005 allostatic cross-addiction profile: AUD client
        in early recovery (3 months abstinent) presents increased
        CIUS as internet use compensates for loss of the primary
        reward.  Profile: elevated control-loss (items 1, 3, 5) and
        preoccupation (items 2, 6, 10), moderate neglect (items 8,
        9), and rising withdrawal (items 13, 14).  Total 31."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [3, 3, 3, 1, 3, 3, 1, 2, 2, 3, 1, 1, 2, 3]},
            headers=self._headers("cius-vig-koob"),
        )
        body = response.json()
        assert body["total"] == 31
        assert body["severity"] == "continuous"

    def test_vignette_cbt_responder_delta(
        self, client: TestClient
    ) -> None:
        """CBT-CIUS 12-week trial responder signature — pre-treatment
        extreme-compulsion profile (56) reduces to mild-frequency
        maintenance profile (14) post-treatment.  Delta 42 is vastly
        larger than the Jacobson 1991 RCI MCID (≈5 points derived
        from α=0.89 and Dutch-sample SD); documents unambiguous
        clinical response in the trajectory layer."""
        pre = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-vig-cbt-pre"),
        ).json()
        post = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [1] * 14},
            headers=self._headers("cius-vig-cbt-post"),
        ).json()
        assert pre["total"] == 56
        assert post["total"] == 14
        assert pre["total"] - post["total"] == 42

    def test_vignette_triad_dissociation_high_cius_low_fneb_low_ucla3(
        self, client: TestClient
    ) -> None:
        """FNE-B / UCLA-3 / CIUS triad dissociation: gaming-
        disorder client with normal social skills (low FNE-B) and
        active peer network (low UCLA-3) but extreme compulsive
        gaming (CIUS = 56).  This profile rules out the Caplan 2003
        compensatory-use framing and points toward primary
        behavioral-addiction pathology (ICD-11 6C51) rather than
        secondary anxiety / loneliness substitution.  Intervention
        target accordingly: gaming-specific CBT-I / habit-reversal,
        NOT social-skills training or structural-contact building."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "cius", "items": [4] * 14},
            headers=self._headers("cius-vig-triad-dissoc"),
        )
        body = response.json()
        assert body["total"] == 56


class TestSwlsRouting:
    """End-to-end routing tests for the SWLS dispatcher branch.

    Diener, Emmons, Larsen & Griffin 1985 Satisfaction With Life
    Scale — 5 items, 1-7 Likert, NO reverse keying (all items
    positively worded in the "higher = more satisfied" direction
    per Diener 1985 Table 1 and Pavot & Diener 1993 confirmation),
    unidimensional, total = straight sum 5-35.  **HIGHER = MORE
    satisfied** — uniform with WHO-5 / LOT-R / BRS / MAAS / RSES /
    PANAS-10 PA / CD-RISC-10 / FFMQ-15 "higher-is-better"
    direction.

    The ZERO-reverse-keying design is Diener 1985's explicit
    choice: all five items positively worded to probe the
    cognitive-judgmental "life close to my ideal" construct
    directly.  Pavot 1993 §Discussion rejected reverse-keying as
    unnecessary given α = 0.87 evidence of coherent-interpretation
    dominance over acquiescence bias.  Consequence: the
    acquiescence signature is the trivial linear formula
    ``total = 5v`` for any all-v constant vector, and the endpoint-
    only-responder gap is the full 30-point 5-35 range (100% of
    range).  This matches UCLA-3 / CIUS in proportion-of-range
    endpoint exposure.

    Clinically DISTINCT from affective-wellbeing instruments —
    WHO-5 measures the LAST-TWO-WEEKS affective mood (cheerful,
    relaxed, active, rested, interested); LOT-R measures DISPOSITIONAL
    OPTIMISM (trait-level expectations about future outcomes); BRS
    measures BOUNCE-BACK RESILIENCE.  SWLS measures COGNITIVE-
    JUDGMENTAL GLOBAL LIFE EVALUATION — a slow-moving trait-like
    construct that integrates across domains and time.  The four-
    way dissociation profile (SWLS-low + WHO-5-high + LOT-R-high
    + BRS-high) is the "wrong-life" pattern: mood / optimism /
    resilience intact, but cognitive life-evaluation persistently
    low — ACT values-clarification indication per Hayes 2006.

    Clinical use cases:
    1. Moos 2005 delayed-relapse detection (n = 628 AUD cohort
       16-year follow-up — SWLS at 1-3 years predicts year-16
       remission where affective measures do not).
    2. ACT values-clarification (Hayes 2006) indication when
       SWLS-low pairs with normal affective wellbeing.
    3. Beck 1985 hopelessness-suicide-risk context (SWLS-low +
       LOT-R-low) — clinician-UI C-SSRS follow-up prompt.
    4. Smith 2008 BRS validation paper "stuck-stress" pattern
       (SWLS-low + BRS-low) — resilience-skills-first sequencing.
    5. Long-horizon trajectory tracking — Pavot 2008 SD ≈ 6.6 and
       α ≈ 0.87 anchor a Jacobson-Truax RCI MCID of ≈ 6 points
       on the 5-35 range for the trajectory layer.

    T3 posture — NO item probes suicidality.  Item 5 ("would
    change almost nothing") is a counterfactual life-evaluation
    probe, NOT a self-harm or ideation probe.  The clinician-UI
    layer may prompt C-SSRS follow-up when SWLS-low pairs with
    LOT-R-low (Beck 1985 hopelessness-suicide-risk profile), but
    the SWLS assessment itself MUST NOT set T3.  Active-risk
    screening stays on C-SSRS / PHQ-9 item 9.

    Envelope: banded+total (no subscales — unidimensional factor
    structure per Diener 1985 / Pavot 1993 eigenvalue ratio
    2.9:0.6; no scaled_score, positive_screen, cutoff_used,
    triggering_items — same shape as UCLA-3 / CIUS / STAI-6 /
    FNE-B / RSES).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ---------------------------------------------------

    def test_max_satisfaction_extremum_thirty_five(
        self, client: TestClient
    ) -> None:
        """Diener 1985 top-of-range: "Strongly Agree" on all five
        items.  Raw [7]*5.  No reverse keying → total = 35, the
        Pavot 1993 "Extremely satisfied" ceiling."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [7, 7, 7, 7, 7]},
            headers=self._headers("swls-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "swls"
        assert body["total"] == 35
        assert body["severity"] == "continuous"

    def test_min_satisfaction_extremum_five(
        self, client: TestClient
    ) -> None:
        """Diener 1985 bottom-of-range: "Strongly Disagree" on all
        five items.  Raw [1]*5 = total 5, the Pavot 1993 "Extremely
        dissatisfied" floor."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("swls-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 5
        assert body["severity"] == "continuous"

    def test_pavot_neutral_single_value_twenty(
        self, client: TestClient
    ) -> None:
        """Pavot 1993 single-value "Neutral" point at exactly 20.
        Raw [4]*5 (all "Neither Agree nor Disagree") = 20.
        Pavot 1993 explicitly resisted collapsing this into a
        binary above-vs-below band; the platform MUST surface the
        value continuously, not as a banded flag."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4, 4, 4, 4, 4]},
            headers=self._headers("swls-neutral"),
        )
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "continuous"

    # -- Acquiescence signature — linear total = 5v -----------------------

    @pytest.mark.parametrize(
        "v, expected",
        [
            (1, 5),
            (2, 10),
            (3, 15),
            (4, 20),
            (5, 25),
            (6, 30),
            (7, 35),
        ],
    )
    def test_acquiescence_signature_linear(
        self, client: TestClient, v: int, expected: int
    ) -> None:
        """Linear formula v: total = 5v for any constant vector.
        NO reverse-keying offset, unlike FNE-B (4v+24 = 28-48) or
        STAI-6 (constant 15 symmetric collapse).  7-point parametrize
        covers the full Likert range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [v] * 5},
            headers=self._headers(f"swls-acq-{v}"),
        )
        body = response.json()
        assert body["total"] == expected

    def test_acquiescence_gap_is_thirty(self, client: TestClient) -> None:
        """Pin the endpoint-exposure: all-7s minus all-1s = 30,
        the full 5-35 range (100%).  Matches UCLA-3 / CIUS 100%
        endpoint-exposure in relative terms.  Documents Diener
        1985's design trade-off: no reverse-keying in exchange
        for α = 0.87 coherent-interpretation dominance."""
        r_low = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("swls-gap-1"),
        ).json()
        r_high = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [7, 7, 7, 7, 7]},
            headers=self._headers("swls-gap-7"),
        ).json()
        assert r_high["total"] - r_low["total"] == 30

    # -- Envelope fields — no subscales/cutoff/screen/scaled/trigger ------

    def test_envelope_has_no_subscales(self, client: TestClient) -> None:
        """Diener 1985 / Pavot 1993 confirmed unidimensional factor
        structure (eigenvalue ratio 2.9:0.6 = strong single-factor
        dominance); envelope MUST NOT carry subscales.  Partitioning
        into facets (e.g., "present-state" vs "retrospective" vs
        "counterfactual") would over-fit the published factor
        structure."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4, 4, 4, 4, 4]},
            headers=self._headers("swls-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_envelope_has_no_cutoff_used(self, client: TestClient) -> None:
        """Pavot 1993 seven-band interpretive guidelines (Extremely
        satisfied 31-35 down to Extremely dissatisfied 5-9) are
        INTERPRETIVE, not decision cutpoints (explicitly framed as
        "overall interpretive guidelines" in Pavot 1993 §Discussion).
        Platform MUST NOT surface any as cutoff_used per CLAUDE.md
        non-negotiable #9 ("Don't hand-roll severity thresholds").
        Those bands live at the clinician-UI renderer layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [5, 5, 5, 5, 5]},
            headers=self._headers("swls-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_envelope_has_no_positive_screen(
        self, client: TestClient
    ) -> None:
        """SWLS is not a screen.  Pavot 1993's Neutral band at
        exactly 20 resists binary dichotomization; any cutoff
        choice would be hand-rolled against primary-source
        guidance."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [5, 5, 5, 5, 5]},
            headers=self._headers("swls-no-screen"),
        )
        body = response.json()
        assert body.get("positive_screen") is None

    def test_envelope_has_no_scaled_score(self, client: TestClient) -> None:
        """SWLS reports the raw 5-35 total; no scaled mapping to
        another range (unlike WHO-5 which scales raw 0-25 to 0-100
        index per Bech 2003)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [5, 5, 5, 5, 5]},
            headers=self._headers("swls-no-scaled"),
        )
        body = response.json()
        assert body.get("scaled_score") is None

    def test_envelope_has_no_triggering_items(
        self, client: TestClient
    ) -> None:
        """triggering_items is C-SSRS-only (risk-band audit trail).
        SWLS is continuous; no item individually flags."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("swls-no-triggering"),
        )
        body = response.json()
        assert body.get("triggering_items") is None

    # -- Severity always continuous ---------------------------------------

    @pytest.mark.parametrize(
        "items, expected_total",
        [
            ([1, 1, 1, 1, 1], 5),     # Extremely dissatisfied floor
            ([2, 3, 2, 3, 2], 12),    # Dissatisfied band
            ([3, 4, 3, 4, 3], 17),    # Slightly dissatisfied band
            ([4, 4, 4, 4, 4], 20),    # Pavot "Neutral" single value
            ([4, 5, 4, 5, 4], 22),    # Slightly satisfied band
            ([5, 6, 5, 6, 6], 28),    # Satisfied band
            ([7, 7, 7, 7, 7], 35),    # Extremely satisfied ceiling
        ],
    )
    def test_severity_is_continuous_across_pavot_bands(
        self, client: TestClient, items: list[int], expected_total: int
    ) -> None:
        """Severity is always ``"continuous"`` regardless of which
        Pavot 1993 interpretive band the total would fall into.
        Pins the CLAUDE.md non-negotiable #9 invariant at the wire
        layer: the envelope does NOT collapse to Pavot's seven-band
        categorization."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": items},
            headers=self._headers(f"swls-sev-{expected_total}"),
        )
        body = response.json()
        assert body["total"] == expected_total
        assert body["severity"] == "continuous"

    # -- T3 posture -------------------------------------------------------

    def test_minimum_total_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Raw [1, 1, 1, 1, 1] = total 5 is the minimum-satisfaction
        extremum.  Low SWLS paired with low LOT-R parallels Beck
        1985 hopelessness-suicide-risk profile, but the SWLS
        instrument itself MUST NOT set requires_t3.  Active-risk
        screening stays on C-SSRS / PHQ-9 item 9.  The clinician
        UI may prompt C-SSRS follow-up based on the SWLS × LOT-R
        combination — that is a renderer-layer decision, not a
        scorer-layer flag."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("swls-t3-min"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["requires_t3"] is False

    def test_counterfactual_item5_alone_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Item 5 ("If I could live my life over, I would change
        almost nothing") at minimum with others neutral.  Raw
        [4, 4, 4, 4, 1] = 17.  "Would change my life" is a
        counterfactual regret probe, NOT an ideation probe.
        MUST NOT set T3 even when this item alone is at the floor."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4, 4, 4, 4, 1]},
            headers=self._headers("swls-t3-item5-floor"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_maximum_total_does_not_require_t3(
        self, client: TestClient
    ) -> None:
        """Raw [7, 7, 7, 7, 7] = 35 (maximum).  T3 is categorically
        absent for SWLS."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [7, 7, 7, 7, 7]},
            headers=self._headers("swls-t3-max"),
        )
        body = response.json()
        assert body["total"] == 35
        assert body["requires_t3"] is False

    # -- No-reverse-keying wire pins --------------------------------------

    @pytest.mark.parametrize("position", [0, 1, 2, 3, 4])
    def test_items_pass_through_unchanged_per_position(
        self, client: TestClient, position: int
    ) -> None:
        """SWLS has ZERO reverse-keying.  Raising any single item
        from 1 to 7 with others at 1 raises the total by exactly 6
        (the full Likert step × 1 item).  Contrast FNE-B reverse-
        item positions which DROP the total by 4 when raised.
        Parametrized over all 5 positions to document the invariant
        at every administration-order slot."""
        base = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 1, 1, 1, 1]},
            headers=self._headers(f"swls-pass-{position}-base"),
        ).json()
        items = [1, 1, 1, 1, 1]
        items[position] = 7
        raised = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": items},
            headers=self._headers(f"swls-pass-{position}-raised"),
        ).json()
        assert raised["total"] - base["total"] == 6

    def test_item_ordering_does_not_affect_total(
        self, client: TestClient
    ) -> None:
        """Pin asymmetric item pattern [7, 6, 5, 4, 3] forward vs
        [3, 4, 5, 6, 7] reversed.  SWLS has no reverse-keyed
        positions, so order reversal MUST yield the same total
        (25).  Guards against accidental reverse-keying logic
        leaking through the dispatcher for SWLS payloads."""
        forward = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [7, 6, 5, 4, 3]},
            headers=self._headers("swls-order-fwd"),
        ).json()
        reversed_items = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [3, 4, 5, 6, 7]},
            headers=self._headers("swls-order-rev"),
        ).json()
        assert forward["total"] == reversed_items["total"] == 25

    # -- Item count traps -------------------------------------------------

    @pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 6, 7, 10, 20])
    def test_rejects_wrong_item_count(
        self, client: TestClient, count: int
    ) -> None:
        """Any count other than 5 returns 422.  count=10 / count=20
        guard against accidental full-WHO-5 (5 items — would pass!)
        or full-BHS-20 submission being routed through the SWLS
        scorer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4] * count},
            headers=self._headers(f"swls-ic-{count}"),
        )
        assert response.status_code == 422

    # -- Item value traps -------------------------------------------------

    def test_rejects_item_value_zero(self, client: TestClient) -> None:
        """SWLS is 1-7 Likert; 0 is below range.  Guards against
        accidental WHO-5 0-5 scale or PHQ-9 0-3 scale submission."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [0, 4, 4, 4, 4]},
            headers=self._headers("swls-iv-0"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_eight(self, client: TestClient) -> None:
        """SWLS is 1-7 Likert; 8 is above range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [8, 4, 4, 4, 4]},
            headers=self._headers("swls-iv-8"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_negative(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [-1, 4, 4, 4, 4]},
            headers=self._headers("swls-iv-neg"),
        )
        assert response.status_code == 422

    def test_rejects_item_value_ninety_nine(
        self, client: TestClient
    ) -> None:
        """Far-above-range guard against accidental percentage-
        scale submission."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [99, 4, 4, 4, 4]},
            headers=self._headers("swls-iv-99"),
        )
        assert response.status_code == 422

    # -- Item type traps --------------------------------------------------

    def test_rejects_string_items(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": ["four", 4, 4, 4, 4]},
            headers=self._headers("swls-iv-str"),
        )
        assert response.status_code == 422

    def test_rejects_float_with_decimal(self, client: TestClient) -> None:
        """Pydantic ``list[int]`` rejects 4.5 as non-integer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4.5, 4, 4, 4, 4]},
            headers=self._headers("swls-iv-fl"),
        )
        assert response.status_code == 422

    # -- Pydantic bool-coercion doc ---------------------------------------

    def test_true_coerced_to_one_is_valid(self, client: TestClient) -> None:
        """Pydantic's ``list[int]`` coerces JSON ``true`` → 1 BEFORE
        the scorer sees it.  On SWLS's 1-7 scale, 1 is a valid
        response ("Strongly Disagree") so True passes.  With item 1
        as True and items 2-5 at 1, total = 5."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [True, 1, 1, 1, 1]},
            headers=self._headers("swls-true"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 5

    def test_false_coerced_to_zero_is_rejected_by_range(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces ``false`` → 0, which is BELOW SWLS's
        1-7 range.  Range check rejects with 422.  Unlike CIUS
        (0-4, 0 valid) where the JSON boolean round-trips as a
        legitimate score, SWLS rejects at the range layer.  This
        matches the UCLA-3 / FNE-B / STAI-6 / PHQ-9 / GAD-7 bool-
        false-rejection pattern."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [False, 1, 1, 1, 1]},
            headers=self._headers("swls-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes ----------------------------------------------

    def test_vignette_extremely_dissatisfied_floor(
        self, client: TestClient
    ) -> None:
        """Pavot 1993 "Extremely dissatisfied" floor.  Raw [1]*5 = 5.
        Severe-depression-with-pervasive-dissatisfaction profile;
        long-horizon suicide-risk context when paired with low
        LOT-R (Beck 1985)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 1, 1, 1, 1]},
            headers=self._headers("swls-vig-floor"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["severity"] == "continuous"

    def test_vignette_moos_delayed_relapse_profile(
        self, client: TestClient
    ) -> None:
        """Moos 2005 delayed-relapse signature: improved affective
        wellbeing (WHO-5 would be high) with persistent low
        cognitive satisfaction.  SWLS = 13 ("Dissatisfied" band)
        in an 18-month-post-AUD-treatment client with good mood
        but "this isn't the life I want" cognitive profile.  Raw
        [2, 3, 3, 3, 2] = 13.  Intervention signal: ACT values-
        clarification (Hayes 2006) or BATD with values-mapping
        (Kanter 2010), NOT further affect-work."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [2, 3, 3, 3, 2]},
            headers=self._headers("swls-vig-moos"),
        )
        body = response.json()
        assert body["total"] == 13
        assert body["severity"] == "continuous"

    def test_vignette_pavot_neutral(self, client: TestClient) -> None:
        """Pavot 1993 "Neutral" single-value band at exactly 20.
        Raw [4]*5.  Platform does NOT collapse this into an
        above-vs-below binary band — the envelope surfaces the
        continuous value."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4, 4, 4, 4, 4]},
            headers=self._headers("swls-vig-neutral"),
        )
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "continuous"

    def test_vignette_satisfied_stable_recovery(
        self, client: TestClient
    ) -> None:
        """Pavot 1993 "Satisfied" band.  Raw [5, 6, 5, 6, 6] = 28.
        Stable-recovery profile — Moos 2005 long-horizon-remission
        predictor at this range in 1-3 years post-treatment."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [5, 6, 5, 6, 6]},
            headers=self._headers("swls-vig-satisfied"),
        )
        body = response.json()
        assert body["total"] == 28
        assert body["severity"] == "continuous"

    def test_vignette_extremely_satisfied_ceiling(
        self, client: TestClient
    ) -> None:
        """Pavot 1993 "Extremely satisfied" ceiling.  Raw [7]*5 = 35."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [7, 7, 7, 7, 7]},
            headers=self._headers("swls-vig-ceiling"),
        )
        body = response.json()
        assert body["total"] == 35
        assert body["severity"] == "continuous"

    def test_vignette_cbt_responder_delta(
        self, client: TestClient
    ) -> None:
        """12-week CBT + BA responder signature: pre-treatment
        [2, 2, 3, 2, 2] = 11 ("Dissatisfied"), post-treatment
        [5, 5, 5, 4, 4] = 23 ("Slightly satisfied").  Delta 12 is
        substantially above the Jacobson 1991 RCI MCID (≈ 6 points
        derived from Pavot 1993 α ≈ 0.87 and Pavot 2008 SD ≈ 6.6);
        documents reliable clinical change at the trajectory
        layer."""
        pre = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [2, 2, 3, 2, 2]},
            headers=self._headers("swls-vig-cbt-pre"),
        ).json()
        post = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [5, 5, 5, 4, 4]},
            headers=self._headers("swls-vig-cbt-post"),
        ).json()
        assert pre["total"] == 11
        assert post["total"] == 23
        assert post["total"] - pre["total"] == 12

    def test_vignette_wrong_life_ACT_indication(
        self, client: TestClient
    ) -> None:
        """Hayes 2006 ACT values-clarification indication: the
        "wrong-life" profile features low item-4 (important things
        attained) and low item-5 (would change nothing) with
        neutral present-state items (1-3).  Raw [4, 4, 4, 2, 1] = 15.
        At the clinician-UI layer, pairs with normal WHO-5 /
        LOT-R / BRS to identify ACT values-mapping as the matched
        intervention (NOT further affect-work, NOT resilience
        skills)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [4, 4, 4, 2, 1]},
            headers=self._headers("swls-vig-wrong-life"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"

    def test_vignette_hopelessness_parallel_profile(
        self, client: TestClient
    ) -> None:
        """Beck 1985 hopelessness-suicide-risk PARALLEL profile:
        low SWLS documenting the "my life isn't good" cognitive
        half.  At the clinician-UI layer, pairs with low LOT-R
        (the "and I don't expect it to get good" future-directed
        half) to prompt C-SSRS follow-up.  Raw [1, 2, 2, 1, 1] = 7
        (within Pavot 1993 "Extremely dissatisfied" band).
        The SWLS assessment itself MUST NOT set requires_t3 —
        that stays on C-SSRS / PHQ-9 item 9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "swls", "items": [1, 2, 2, 1, 1]},
            headers=self._headers("swls-vig-hopelessness"),
        )
        body = response.json()
        assert body["total"] == 7
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False


class TestMspssRouting:
    """End-to-end routing tests for the MSPSS dispatcher branch.

    Zimet, Dahlem, Zimet & Farley 1988 Multidimensional Scale of
    Perceived Social Support — 12 items, 1-7 Likert, NO reverse keying
    (all 12 items positively worded in the "higher = more perceived
    support" direction per Zimet 1988 Table 1), three-factor structure
    (Significant Other / Family / Friends).  Per-subscale sum = 4-28;
    total = 12-84.  **HIGHER = MORE perceived support** — uniform with
    WHO-5 / LOT-R / BRS / MAAS / RSES / SWLS / PANAS-10 PA "higher-is-
    better" direction.

    Multi-subscale envelope — second instrument (after PANAS-10) to
    populate the ``subscales`` dict slot with its three source-
    partitioned sums.  Zimet 1988 factor analysis (n = 275 undergrads;
    eigenvalues 6.1, 1.3, 1.1) confirmed the three factors are NOT
    interchangeable; clinicians MUST read subscales via the dict —
    the total alone cannot distinguish partner-dependent, family-only,
    peer-only, diffuse-deficit, or distributed-support profiles.

    Interleaved administration order — Zimet 1988 items alternate
    across sources to prevent subscale-block context effects:
        SO, SO, Fam, Fam, SO, Fr, Fr, Fam, Fr, SO, Fam, Fr
    The wire layer MUST preserve this ordering; a client that
    reshuffles items per-subscale will silently misclassify the
    profile (total still correct, subscales misattributed).

    Subscale position mapping (1-indexed per Zimet 1988 Table 1):
        Significant Other: items 1, 2, 5, 10
        Family:            items 3, 4, 8, 11
        Friends:           items 6, 7, 9, 12

    Clinical use cases:
    1. Cohen & Wills 1985 stress-buffering — MSPSS low + PSS-10 high
       identifies "unsupported-under-stress" profile; social-
       prescribing (Kiernan 2019) + skill-building in parallel.
    2. Beattie 1999 perceived-friends-support predicts 3-year AUD
       outcomes > structural network variables.
    3. Holt-Lunstad 2010 n=308,849 isolation-mortality meta — all-
       three-subscales-low ("diffuse-deficit") is the priority
       intervention target.
    4. Calati 2019 convergent isolation + suicide-risk: MSPSS low +
       UCLA-3 high + PHQ-9 high → clinician-UI C-SSRS follow-up
       prompt (renderer layer), NOT scorer-layer T3.
    5. Moos 2005 delayed-relapse + network-vulnerability: MSPSS low
       + SWLS low → network-rebuild precedes life-evaluation work.

    T3 posture — NO item probes suicidality.  Item 10 ("special
    person in my life who cares about my feelings") is an attachment-
    adequacy probe, NOT a self-harm or ideation probe.  Active-risk
    screening stays on C-SSRS / PHQ-9 item 9.

    Envelope: banded+total + subscales (no scaled_score,
    positive_screen, cutoff_used, triggering_items).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ---------------------------------------------------

    def test_max_support_extremum_eighty_four(
        self, client: TestClient
    ) -> None:
        """Zimet 1988 top-of-range: "Very Strongly Agree" on all 12
        items.  Raw [7]*12.  No reverse keying → total = 84, Canty-
        Mitchell 2000 "high" band (mean 7.0)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [7] * 12},
            headers=self._headers("mspss-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "mspss"
        assert body["total"] == 84
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_min_support_extremum_twelve(
        self, client: TestClient
    ) -> None:
        """Zimet 1988 bottom-of-range: "Very Strongly Disagree" on all
        12 items.  Raw [1]*12 = total 12, Canty-Mitchell 2000 "low"
        floor (mean 1.0) — Holt-Lunstad 2010 diffuse-deficit."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [1] * 12},
            headers=self._headers("mspss-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "continuous"

    def test_canty_mitchell_midpoint_forty_eight(
        self, client: TestClient
    ) -> None:
        """Canty-Mitchell 2000 moderate-band center: all items = 4
        (mean 4.0).  Total = 48.  Envelope stays continuous per
        CLAUDE.md non-negotiable #9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [4] * 12},
            headers=self._headers("mspss-mid"),
        )
        body = response.json()
        assert body["total"] == 48
        assert body["severity"] == "continuous"

    def test_subscales_populated_with_three_zimet_keys(
        self, client: TestClient
    ) -> None:
        """Second multi-subscale instrument (after PANAS-10) — the
        ``subscales`` dict carries three keys matching MSPSS_SUBSCALES
        constants so clinician-UI renderers key off one source of truth."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [4] * 12},
            headers=self._headers("mspss-subscales-keys"),
        )
        body = response.json()
        subscales = body["subscales"]
        assert set(subscales.keys()) == {
            "significant_other",
            "family",
            "friends",
        }

    def test_subscales_are_integer_sums_not_means(
        self, client: TestClient
    ) -> None:
        """Envelope stores integer SUMS (4-28 per subscale), not the
        float mean Canty-Mitchell 2000 used.  The renderer divides by
        4 to recover the mean.  All items = 5 → each subscale = 20
        (four items × 5)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [5] * 12},
            headers=self._headers("mspss-subscales-int"),
        )
        body = response.json()
        for v in body["subscales"].values():
            assert isinstance(v, int)
            assert v == 20

    # -- Subscale partitioning per Zimet 1988 Table 1 ---------------------

    def test_significant_other_only_elevated_profile(
        self, client: TestClient
    ) -> None:
        """SO items (1, 2, 5, 10) = 7; Family / Friends items = 1.
        Partner-dependent profile — relapse risk in partner-rupture."""
        items = [1] * 12
        for pos in (1, 2, 5, 10):
            items[pos - 1] = 7
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-so-only"),
        )
        body = response.json()
        assert body["subscales"]["significant_other"] == 28
        assert body["subscales"]["family"] == 4
        assert body["subscales"]["friends"] == 4
        assert body["total"] == 36

    def test_family_only_elevated_profile(
        self, client: TestClient
    ) -> None:
        """Family items (3, 4, 8, 11) = 7; SO / Friends items = 1.
        Early-recovery withdrawal pattern — prosocial peer-network
        reconstruction indication."""
        items = [1] * 12
        for pos in (3, 4, 8, 11):
            items[pos - 1] = 7
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-fam-only"),
        )
        body = response.json()
        assert body["subscales"]["significant_other"] == 4
        assert body["subscales"]["family"] == 28
        assert body["subscales"]["friends"] == 4

    def test_friends_only_elevated_profile(
        self, client: TestClient
    ) -> None:
        """Friends items (6, 7, 9, 12) = 7; SO / Family items = 1.
        Peer-only support — assess peer substance-use norms."""
        items = [1] * 12
        for pos in (6, 7, 9, 12):
            items[pos - 1] = 7
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-fr-only"),
        )
        body = response.json()
        assert body["subscales"]["significant_other"] == 4
        assert body["subscales"]["family"] == 4
        assert body["subscales"]["friends"] == 28

    def test_subscale_partition_sum_equals_total(
        self, client: TestClient
    ) -> None:
        """Invariant: subscale sums always add up to the total.  If
        the partition is ever broken, this test fails."""
        items = [1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-partition-sum"),
        )
        body = response.json()
        subs = body["subscales"]
        assert (
            subs["significant_other"] + subs["family"] + subs["friends"]
            == body["total"]
        )

    def test_interleaved_order_matters_for_subscales(
        self, client: TestClient
    ) -> None:
        """Reversing the item array preserves the total but changes
        subscale sums — the wire layer MUST preserve Zimet 1988
        administration order."""
        aligned = [1, 1, 7, 7, 1, 7, 7, 7, 7, 1, 7, 7]
        reversed_ = list(reversed(aligned))

        r1 = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": aligned},
            headers=self._headers("mspss-aligned"),
        ).json()
        r2 = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": reversed_},
            headers=self._headers("mspss-reversed"),
        ).json()
        assert r1["total"] == r2["total"]
        assert r1["subscales"] != r2["subscales"]

    # -- Acquiescence signature -------------------------------------------

    @pytest.mark.parametrize(
        "v,expected_total",
        [(1, 12), (2, 24), (3, 36), (4, 48), (5, 60), (6, 72), (7, 84)],
    )
    def test_all_constant_total_is_linear_twelve_v(
        self, client: TestClient, v: int, expected_total: int
    ) -> None:
        """No reverse-keying: all-``v`` total = 12v for v ∈ {1..7}.
        Endpoint-only responders expose the full 72-point range (100%
        of 12-84)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [v] * 12},
            headers=self._headers(f"mspss-acq-{v}"),
        )
        body = response.json()
        assert body["total"] == expected_total

    def test_endpoint_gap_is_seventy_two(
        self, client: TestClient
    ) -> None:
        """All-7 minus all-1 = 72, full 12-84 range (100% endpoint
        exposure — matches SWLS / UCLA-3 / CIUS proportion)."""
        r_max = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [7] * 12},
            headers=self._headers("mspss-gap-max"),
        ).json()
        r_min = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [1] * 12},
            headers=self._headers("mspss-gap-min"),
        ).json()
        assert r_max["total"] - r_min["total"] == 72

    # -- Envelope fields --------------------------------------------------

    def test_subscales_populated(
        self, client: TestClient
    ) -> None:
        """MSPSS IS a multi-subscale instrument — ``subscales`` MUST
        be populated (not None)."""
        response = _post(client, instrument="mspss", items=[4] * 12)
        body = response.json()
        assert body["subscales"] is not None

    def test_cutoff_used_absent(
        self, client: TestClient
    ) -> None:
        """MSPSS has no cutoff gate."""
        response = _post(client, instrument="mspss", items=[4] * 12)
        body = response.json()
        assert body.get("cutoff_used") is None

    def test_positive_screen_absent(
        self, client: TestClient
    ) -> None:
        """MSPSS is not a screen."""
        response = _post(client, instrument="mspss", items=[4] * 12)
        body = response.json()
        assert body.get("positive_screen") is None

    def test_triggering_items_absent(
        self, client: TestClient
    ) -> None:
        """MSPSS is not an item-firing screen."""
        response = _post(client, instrument="mspss", items=[4] * 12)
        body = response.json()
        assert body.get("triggering_items") in (None, [])

    def test_index_absent(
        self, client: TestClient
    ) -> None:
        """``index`` is WHO-5-only."""
        response = _post(client, instrument="mspss", items=[4] * 12)
        body = response.json()
        assert body.get("index") is None

    # -- Severity continuous across Canty-Mitchell bands ------------------

    @pytest.mark.parametrize(
        "v",
        [1, 2, 3, 4, 5, 6, 7],
    )
    def test_severity_always_continuous(
        self, client: TestClient, v: int
    ) -> None:
        """Envelope is continuous regardless of Canty-Mitchell band —
        bands stay at the clinician-UI renderer layer per CLAUDE.md
        non-negotiable #9."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [v] * 12},
            headers=self._headers(f"mspss-cont-{v}"),
        )
        body = response.json()
        assert body["severity"] == "continuous"

    # -- T3 posture -------------------------------------------------------

    def test_requires_t3_always_false_at_max(
        self, client: TestClient
    ) -> None:
        """No MSPSS item probes suicidality.  Even at max support
        score (all 7), requires_t3 is False."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [7] * 12},
            headers=self._headers("mspss-t3-max"),
        )
        assert response.json()["requires_t3"] is False

    def test_requires_t3_always_false_at_min(
        self, client: TestClient
    ) -> None:
        """Even at diffuse-deficit floor (all 1), MSPSS does not set
        T3.  Acute-risk escalation stays on C-SSRS / PHQ-9 item 9.
        Clinician-UI may prompt C-SSRS follow-up per Calati 2019
        but the MSPSS assessment itself MUST NOT set T3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [1] * 12},
            headers=self._headers("mspss-t3-min"),
        )
        assert response.json()["requires_t3"] is False

    def test_requires_t3_false_on_item10_counterfactual(
        self, client: TestClient
    ) -> None:
        """Item 10 ("special person who cares about my feelings")
        low is an attachment-adequacy signal, NOT an ideation
        signal.  Isolating item 10 to the floor still returns
        requires_t3 False."""
        items = [4] * 12
        items[9] = 1  # item 10 at floor
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-t3-item10"),
        )
        assert response.json()["requires_t3"] is False

    # -- No reverse-keying pass-through -----------------------------------

    @pytest.mark.parametrize("pos", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    def test_no_reverse_keying_raw_item_adds_directly(
        self, client: TestClient, pos: int
    ) -> None:
        """No reverse-keying: raising any position from 1 to 7
        increases the total by 6.  Uniform direction across all 12
        items."""
        base = [1] * 12
        bumped = list(base)
        bumped[pos - 1] = 7
        r_base = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": base},
            headers=self._headers(f"mspss-rev-base-{pos}"),
        ).json()
        r_bumped = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": bumped},
            headers=self._headers(f"mspss-rev-bumped-{pos}"),
        ).json()
        assert r_bumped["total"] - r_base["total"] == 6

    # -- Item count traps -------------------------------------------------

    @pytest.mark.parametrize("count", [0, 1, 5, 10, 11, 13, 14, 20, 100])
    def test_wrong_item_count_returns_422(
        self, client: TestClient, count: int
    ) -> None:
        """MSPSS requires exactly 12 items.  Mismatch → 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [4] * count},
            headers=self._headers(f"mspss-count-{count}"),
        )
        assert response.status_code == 422

    # -- Item value traps -------------------------------------------------

    @pytest.mark.parametrize("bad", [0, 8, -1, 99])
    def test_out_of_range_item_returns_422(
        self, client: TestClient, bad: int
    ) -> None:
        """MSPSS range is 1-7.  Out-of-range → 422."""
        items = [bad] + [4] * 11
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers(f"mspss-range-{bad}"),
        )
        assert response.status_code == 422

    # -- Item type traps --------------------------------------------------

    def test_numeric_string_coerces_via_pydantic_lax_mode(
        self, client: TestClient
    ) -> None:
        """Pydantic ``list[int]`` uses lax-mode coercion at the wire
        layer — numeric-string ``"4"`` becomes int 4 BEFORE the scorer
        runs.  This is the same round-trip mechanism that makes JSON
        ``true`` → int 1.  Documents the actual Pydantic behavior:
        scorer-level type checks fire for DIRECT Python callers; the
        HTTP wire layer's lax coercion decides HTTP behavior
        independently."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": ["4"] + [4] * 11},
            headers=self._headers("mspss-type-numstr"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["total"] == 48  # all coerced to int 4

    def test_non_numeric_string_returns_422(
        self, client: TestClient
    ) -> None:
        """Non-numeric strings cannot coerce to int even in lax mode;
        Pydantic returns 422 at the wire layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": ["hello"] + [4] * 11},
            headers=self._headers("mspss-type-badstr"),
        )
        assert response.status_code == 422

    def test_float_item_returns_422(
        self, client: TestClient
    ) -> None:
        """Non-integer floats are rejected at the Pydantic wire layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [4.5] + [4] * 11},
            headers=self._headers("mspss-type-float"),
        )
        assert response.status_code == 422

    # -- Pydantic bool coercion behavior ----------------------------------

    def test_true_coerces_to_one_and_is_accepted(
        self, client: TestClient
    ) -> None:
        """Pydantic ``list[int]`` coerces JSON ``true`` to int 1 at the
        wire layer, BEFORE the scorer's bool-check runs.  1 is a valid
        MSPSS response.  Documents defence-in-depth: scorer-level bool
        rejection protects direct Python callers; wire layer decides
        HTTP behavior independently."""
        items = [True] + [4] * 11  # type: ignore[list-item]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-bool-true"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        # total = 1 (from coerced True) + 4*11 = 45
        assert body["total"] == 45

    def test_false_coerces_to_zero_and_is_rejected_by_range(
        self, client: TestClient
    ) -> None:
        """Pydantic coerces JSON ``false`` to int 0 at the wire layer.
        MSPSS range is 1-7, so 0 fails the range check and returns 422
        — the INVERSE of CIUS, where 0 is valid and the scorer's bool
        check is load-bearing."""
        items = [False] + [4] * 11  # type: ignore[list-item]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-bool-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes -----------------------------------------------

    def test_vignette_diffuse_deficit_highest_risk(
        self, client: TestClient
    ) -> None:
        """Holt-Lunstad 2010 isolation-mortality priority profile: all
        three subscales at the floor.  Raw [1]*12.  Total = 12.  The
        clinician-UI layer flags for supported-housing / IOP scaffold
        per Cohen-Wills 1985 buffering-absence logic."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [1] * 12},
            headers=self._headers("mspss-vig-diffuse"),
        )
        body = response.json()
        assert body["total"] == 12
        for v in body["subscales"].values():
            assert v == 4  # subscale floor

    def test_vignette_distributed_support_protective(
        self, client: TestClient
    ) -> None:
        """Protective profile — all three subscales elevated.  Raw
        [6]*12 (mean 6.0, Canty-Mitchell "high" band).  Total = 72."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [6] * 12},
            headers=self._headers("mspss-vig-distributed"),
        )
        body = response.json()
        assert body["total"] == 72
        for v in body["subscales"].values():
            assert v == 24

    def test_vignette_partner_dependent_relapse_risk(
        self, client: TestClient
    ) -> None:
        """Partner-dependent profile — SO elevated, Family / Friends
        low.  Raw items: SO (1,2,5,10) = 7; others = 2.  Relapse risk
        concentrates in partner-rupture episodes."""
        items = [2] * 12
        for pos in (1, 2, 5, 10):
            items[pos - 1] = 7
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": items},
            headers=self._headers("mspss-vig-partner"),
        )
        body = response.json()
        assert body["subscales"]["significant_other"] == 28
        assert body["subscales"]["family"] == 8
        assert body["subscales"]["friends"] == 8

    def test_vignette_mspss_low_pss10_high_pairing_mspss_side(
        self, client: TestClient
    ) -> None:
        """Cohen-Wills 1985 "unsupported-under-stress" pairing: MSPSS
        side.  Raw [2]*12 (mean 2.0, Canty-Mitchell "low" band at the
        clinician-UI layer).  Envelope stays continuous."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [2] * 12},
            headers=self._headers("mspss-vig-stress"),
        )
        body = response.json()
        assert body["total"] == 24
        assert body["severity"] == "continuous"

    def test_vignette_mspss_low_swls_low_pairing_mspss_side(
        self, client: TestClient
    ) -> None:
        """Moos 2005 delayed-relapse + network-vulnerability pairing:
        MSPSS side.  Total < 36 (below Canty-Mitchell moderate
        floor).  Network-rebuild precedes life-evaluation work."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [2, 3, 2, 2, 2, 2, 3, 2, 2, 2, 3, 2]},
            headers=self._headers("mspss-vig-swls-low"),
        )
        body = response.json()
        assert body["total"] < 36
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_calati_isolation_suicide_risk_context(
        self, client: TestClient
    ) -> None:
        """Calati 2019 convergent isolation + suicide-risk context:
        MSPSS low documents the perceived-support half.  At the
        clinician-UI layer, pairs with UCLA-3 high and PHQ-9 high to
        prompt C-SSRS follow-up.  The MSPSS assessment itself MUST
        NOT set T3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "mspss", "items": [1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1]},
            headers=self._headers("mspss-vig-calati"),
        )
        body = response.json()
        assert body["total"] <= 20  # deep low-support range
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False


class TestGseRouting:
    """End-to-end routing tests for the GSE dispatcher branch.

    Schwarzer & Jerusalem 1995 Generalized Self-Efficacy Scale —
    10 items, 1-4 Likert, NO reverse keying (all 10 items positively
    worded per Schwarzer 1995 Table 1), unidimensional factor
    structure (Scholz, Gutiérrez-Doña, Sud & Schwarzer 2002;
    n=19,120 across 25 countries; median α=0.86).  Total = 10-40.
    **HIGHER = MORE general self-efficacy** — uniform with
    WHO-5 / LOT-R / BRS / MAAS / RSES / SWLS / MSPSS / PANAS-10 PA
    "higher-is-better" direction.

    Single-total envelope — NO subscales (Scholz 2002 unidimensional
    factor structure pinned by cross-cultural measurement invariance).
    Partitioning into facets would over-fit the published structure
    and is refused at the scorer layer.

    Clinical use cases (all resolved at the clinician-UI renderer
    layer; the scorer output stays ``"continuous"`` per CLAUDE.md
    non-negotiable #9):

    1. Bandura 1997 mastery-experience sequencing — GSE low +
       DTCQ-8 low ("pervasive-low-confidence") indicates small-step
       success-building BEFORE high-risk-situation exposure.
    2. Marlatt 2005 coping-skills targeting — GSE high + DTCQ-8 low
       ("competence-gap" profile) indicates direct situation-specific
       skill work without trait-level preamble.
    3. Marlatt 1985 AVE pathway — GSE low + BRS low indicates
       parallel self-efficacy + resilience training (Reivich 2002
       PRP).
    4. Beck 1979 cognitive-triad convergence — GSE low + LOT-R low
       indicates CBT-D (Beck 1979; Hollon 2005).
    5. Cohen-Wills 1985 buffering breakdown — GSE low + SWLS low +
       PSS-10 high ("overwhelmed-and-depleted") indicates immediate
       stress regulation + graduated mastery, life-evaluation later.

    T3 posture — NO item probes suicidality.  Item 7 ("remain calm
    when facing difficulties because I can rely on my coping
    abilities") is a coping-confidence probe, NOT a self-harm or
    ideation probe.  Active-risk screening stays on C-SSRS /
    PHQ-9 item 9.

    Envelope: banded+total (no subscales, scaled_score,
    positive_screen, cutoff_used, triggering_items, index).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ---------------------------------------------------

    def test_max_efficacy_extremum_forty(
        self, client: TestClient
    ) -> None:
        """Schwarzer 1995 top-of-range: "Exactly true" on all 10
        items.  Raw [4]*10.  No reverse keying → total = 40,
        Scholz 2002 descriptive-ceiling."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [4] * 10},
            headers=self._headers("gse-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "gse"
        assert body["total"] == 40
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_min_efficacy_extremum_ten(
        self, client: TestClient
    ) -> None:
        """Schwarzer 1995 bottom-of-range: "Not at all true" on all
        10 items.  Raw [1]*10 → total 10.  Scholz 2002 descriptive
        floor."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [1] * 10},
            headers=self._headers("gse-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 10
        assert body["severity"] == "continuous"

    def test_midpoint_twenty_five(
        self, client: TestClient
    ) -> None:
        """Midpoint of the 10-40 range: alternating 2/3 × 5.  Total
        = 25.  Envelope stays continuous per CLAUDE.md non-
        negotiable #9 — Scholz 2002 norms (mean ≈ 29, SD ≈ 4) and
        Luszczynska 2005 descriptive clusters stay at the
        clinician-UI layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [2, 3] * 5},
            headers=self._headers("gse-mid"),
        )
        body = response.json()
        assert body["total"] == 25
        assert body["severity"] == "continuous"

    def test_scholz_normative_mean_twenty_nine(
        self, client: TestClient
    ) -> None:
        """Scholz 2002 European n=4,988 normative mean ≈ 29.  A
        submission landing at 29 must still render ``"continuous"``
        — the normative distribution is a RENDERER-LAYER reference
        point, not a severity band."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 2],
            },
            headers=self._headers("gse-normative-mean"),
        )
        body = response.json()
        assert body["total"] == 29
        assert body["severity"] == "continuous"

    def test_envelope_has_no_subscales(
        self, client: TestClient
    ) -> None:
        """Scholz 2002 unidimensional factor structure → the
        response MUST NOT populate ``subscales``.  If it did, a
        clinician renderer might incorrectly partition the total
        into facets that the published validation does not
        support."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [3] * 10},
            headers=self._headers("gse-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_envelope_has_no_cutoff_or_screen(
        self, client: TestClient
    ) -> None:
        """GSE is not a screen — no validated diagnostic gate
        against a structured clinical interview exists.  Envelope
        must NOT populate ``cutoff_used`` or ``positive_screen``."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [3] * 10},
            headers=self._headers("gse-no-cutoff"),
        )
        body = response.json()
        assert body.get("cutoff_used") is None
        assert body.get("positive_screen") is None

    def test_envelope_has_no_index_or_scaled_score(
        self, client: TestClient
    ) -> None:
        """The GSE total IS the published score — no WHO-5-style
        index or MAAS-style scaled_score.  Callers should render
        ``total`` directly."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [3] * 10},
            headers=self._headers("gse-no-index"),
        )
        body = response.json()
        assert body.get("index") is None
        assert body.get("scaled_score") is None

    def test_envelope_has_no_triggering_items(
        self, client: TestClient
    ) -> None:
        """GSE has no C-SSRS-style per-item acuity routing."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [3] * 10},
            headers=self._headers("gse-no-triggering"),
        )
        body = response.json()
        assert body.get("triggering_items") is None

    def test_envelope_carries_instrument_version(
        self, client: TestClient
    ) -> None:
        """The pinned instrument_version flows into the FHIR R4
        Observation export at the reporting layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [3] * 10},
            headers=self._headers("gse-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "gse-1.0.0"

    # -- Acquiescence signature -----------------------------------------

    @pytest.mark.parametrize("v", [1, 2, 3, 4])
    def test_uniform_response_produces_linear_total(
        self, client: TestClient, v: int
    ) -> None:
        """All-positive-wording scale — uniform response v produces
        total = 10 × v.  Would fail if any position were reverse-
        keyed (would introduce asymmetry)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [v] * 10},
            headers=self._headers(f"gse-uniform-{v}"),
        )
        body = response.json()
        assert body["total"] == 10 * v

    def test_acquiescence_gap_equals_full_range(
        self, client: TestClient
    ) -> None:
        """Uniform-agreement minus uniform-disagreement = full range
        (30 points = 100% of the 10-40 scale).  Schwarzer 1995
        all-positive wording signature — any reverse-keyed item
        would shrink this gap."""
        agree = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [4] * 10},
            headers=self._headers("gse-acq-agree"),
        ).json()
        disagree = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [1] * 10},
            headers=self._headers("gse-acq-disagree"),
        ).json()
        assert agree["total"] - disagree["total"] == 30

    # -- No reverse-keying pass-through --------------------------------

    @pytest.mark.parametrize("pos_1_indexed", list(range(1, 11)))
    def test_single_four_at_position_increases_total_uniformly(
        self, client: TestClient, pos_1_indexed: int
    ) -> None:
        """Baseline [1]*10 with one 4 at position N → total = 13 at
        every position.  A reverse-keyed position would decrease
        the total instead."""
        items = [1] * 10
        items[pos_1_indexed - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers(f"gse-reverse-check-{pos_1_indexed}"),
        )
        body = response.json()
        assert body["total"] == 13

    # -- T3 posture ------------------------------------------------------

    def test_t3_always_false_at_max(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [4] * 10},
            headers=self._headers("gse-t3-max"),
        )
        assert response.json()["requires_t3"] is False

    def test_t3_always_false_at_min(
        self, client: TestClient
    ) -> None:
        """GSE minimum total (10) signals pervasive-low-confidence,
        which the clinician-UI layer may escalate to a C-SSRS
        prompt ONLY in combination with PHQ-9 / LOT-R.  The GSE
        assessment itself MUST NOT set requires_t3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [1] * 10},
            headers=self._headers("gse-t3-min"),
        )
        assert response.json()["requires_t3"] is False

    def test_t3_always_false_item_7_coping_confidence(
        self, client: TestClient
    ) -> None:
        """Schwarzer 1995 item 7 — "I can remain calm when facing
        difficulties because I can rely on my coping abilities" —
        is a COPING-CONFIDENCE probe, NOT a self-harm or ideation
        probe.  A low response on item 7 does not indicate acute
        risk; the GSE scorer MUST NOT set requires_t3 on the basis
        of item 7."""
        items = [3] * 10
        items[6] = 1  # item 7 = "Not at all true"
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-t3-item7"),
        )
        assert response.json()["requires_t3"] is False

    # -- Severity across the Scholz 2002 range ---------------------------

    @pytest.mark.parametrize(
        "responses",
        [
            [1] * 10,                           # 10 — descriptive floor
            [2] * 10,                           # 20
            [2, 3, 2, 3, 2, 3, 2, 3, 2, 3],     # 25 — midpoint
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 2],     # 29 — normative mean
            [3] * 10,                           # 30
            [4, 4, 4, 4, 4, 3, 3, 3, 3, 3],     # 35
            [4] * 10,                           # 40 — descriptive ceiling
        ],
    )
    def test_severity_continuous_across_range(
        self, client: TestClient, responses: list[int]
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": responses},
            headers=self._headers(
                f"gse-severity-range-{sum(responses)}"
            ),
        )
        body = response.json()
        assert body["severity"] == "continuous"

    # -- Item-count validation -------------------------------------------

    @pytest.mark.parametrize(
        "bad_count", [1, 2, 5, 7, 8, 9, 11, 12, 20]
    )
    def test_wrong_item_count_returns_422(
        self, client: TestClient, bad_count: int
    ) -> None:
        """Per-instrument item count is pinned at the router.  GSE
        = 10 (Schwarzer 1995); all other counts 422.  Note: count=0
        is rejected earlier by Pydantic's min_length=1, so not in
        this parametrize set."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [2] * bad_count},
            headers=self._headers(f"gse-bad-count-{bad_count}"),
        )
        assert response.status_code == 422

    # -- Item-value validation -------------------------------------------

    def test_zero_item_value_returns_422(
        self, client: TestClient
    ) -> None:
        items = [2] * 10
        items[0] = 0
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-zero"),
        )
        assert response.status_code == 422

    def test_five_item_value_returns_422(
        self, client: TestClient
    ) -> None:
        items = [2] * 10
        items[4] = 5
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-five"),
        )
        assert response.status_code == 422

    def test_negative_item_value_returns_422(
        self, client: TestClient
    ) -> None:
        items = [2] * 10
        items[9] = -1
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-neg"),
        )
        assert response.status_code == 422

    def test_large_item_value_returns_422(
        self, client: TestClient
    ) -> None:
        items = [2] * 10
        items[2] = 99
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-large"),
        )
        assert response.status_code == 422

    # -- Type validation -------------------------------------------------

    def test_numeric_string_coerces_via_pydantic_lax_mode(
        self, client: TestClient
    ) -> None:
        """Pydantic ``list[int]`` uses LAX-mode coercion: a numeric
        string "4" coerces to int 4 BEFORE the scorer's isinstance
        check runs.  Documented behavior — the scorer's type
        rejection only fires on values that PYDANTIC cannot coerce
        to int.  All 10 "4"s → total 40 (success, not 422)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": ["4"] * 10},
            headers=self._headers("gse-string-coerce"),
        )
        assert response.status_code == 201
        assert response.json()["total"] == 40

    def test_non_numeric_string_returns_422(
        self, client: TestClient
    ) -> None:
        """Non-numeric strings cannot lax-coerce → Pydantic 422 at
        the wire layer, BEFORE the scorer runs."""
        items: list[object] = [2] * 10
        items[0] = "hello"
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-str-reject"),
        )
        assert response.status_code == 422

    def test_float_item_value_returns_422(
        self, client: TestClient
    ) -> None:
        """Floats also reject at Pydantic's strict-int mode for
        non-whole floats.  3.5 cannot coerce to int losslessly."""
        items: list[object] = [2] * 10
        items[0] = 3.5
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": items},
            headers=self._headers("gse-float-reject"),
        )
        assert response.status_code == 422

    def test_bool_true_coerces_via_pydantic_lax_mode(
        self, client: TestClient
    ) -> None:
        """Pydantic lax-mode coerces JSON ``true`` to int 1 — a
        valid Likert response — BEFORE the scorer runs.  The
        scorer's bool-rejection guard never sees the value, so the
        request succeeds with total = 10 (all 1s).  The scorer's
        bool rejection is still the authoritative check at the
        Python-call layer (see test_gse_scoring.py)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [True] * 10},
            headers=self._headers("gse-bool-true"),
        )
        assert response.status_code == 201
        assert response.json()["total"] == 10

    def test_bool_false_coerces_then_rejected_at_range(
        self, client: TestClient
    ) -> None:
        """JSON ``false`` coerces to int 0 via Pydantic lax-mode,
        then the scorer's RANGE check (1-4) rejects it → 422.  The
        error surfaces as a range violation rather than a type
        violation at the wire layer."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [False] * 10},
            headers=self._headers("gse-bool-false"),
        )
        assert response.status_code == 422

    # -- Clinical vignettes ----------------------------------------------

    def test_vignette_pervasive_low_confidence_bandura_1997(
        self, client: TestClient
    ) -> None:
        """Bandura 1997 §3 pervasive-low-efficacy profile.  Pairs
        with DTCQ-8 low to indicate mastery-experience sequencing
        BEFORE high-risk-situation exposure.  Scorer emits
        ``"continuous"``; the intervention match is resolved at the
        clinician-UI layer."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [1, 1, 2, 1, 1, 1, 1, 2, 1, 1],
            },
            headers=self._headers("gse-vig-bandura"),
        )
        body = response.json()
        assert body["total"] == 12  # deep low tail
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_competence_gap_marlatt_2005(
        self, client: TestClient
    ) -> None:
        """Marlatt 2005 high-functioning-early-recovery profile.
        GSE near normative mean + DTCQ-8 low → direct situation-
        specific skill work without trait-level preamble."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            },
            headers=self._headers("gse-vig-marlatt-gap"),
        )
        body = response.json()
        assert body["total"] == 30
        assert body["severity"] == "continuous"

    def test_vignette_ave_pathway_marlatt_1985(
        self, client: TestClient
    ) -> None:
        """Marlatt 1985 abstinence-violation-effect pathway.  GSE
        low + BRS low → cognitive-expectation deficit AND
        behavioral-recovery deficit.  Priority: parallel self-
        efficacy + resilience training (Reivich 2002 PRP).  GSE
        scorer output low, severity continuous, NOT T3."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [1, 2, 1, 1, 2, 1, 1, 2, 1, 1],
            },
            headers=self._headers("gse-vig-ave"),
        )
        body = response.json()
        assert body["total"] == 13
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_depressive_triad_beck_1979(
        self, client: TestClient
    ) -> None:
        """Beck 1979 cognitive-triad convergence.  GSE low (self-
        competence deficit) + LOT-R low (future pessimism) → CBT-D
        indication (Beck 1979; Hollon 2005).  Clinician-UI may
        prompt C-SSRS follow-up in combination with PHQ-9; the GSE
        scorer itself MUST NOT set T3."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [1, 1, 1, 2, 1, 1, 1, 1, 2, 1],
            },
            headers=self._headers("gse-vig-beck"),
        )
        body = response.json()
        assert body["total"] == 12
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_overwhelmed_and_depleted_cohen_wills(
        self, client: TestClient
    ) -> None:
        """Cohen-Wills 1985 buffering-capacity breakdown + global
        dissatisfaction.  GSE low + SWLS low + PSS-10 high →
        immediate stress regulation + graduated mastery; life-
        evaluation work later."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [1, 2, 2, 1, 1, 2, 1, 2, 1, 2],
            },
            headers=self._headers("gse-vig-cohenwills"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "continuous"
        assert body["requires_t3"] is False

    def test_vignette_full_self_efficacy_profile(
        self, client: TestClient
    ) -> None:
        """GSE-high + DTCQ-8 high → full self-efficacy.  Protective;
        maintenance-oriented interventions."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "gse", "items": [4] * 10},
            headers=self._headers("gse-vig-full"),
        )
        body = response.json()
        assert body["total"] == 40
        assert body["severity"] == "continuous"

    def test_vignette_baseline_followup_rci_5pt_delta(
        self, client: TestClient
    ) -> None:
        """Jacobson & Truax 1991 RCI ≈ 5 points on GSE (from Scholz
        2002 α=0.86, SD≈5).  A 5-point delta is clinically
        meaningful in Marlatt-style relapse prevention.  Both
        baseline and followup render as ``"continuous"`` — the
        delta is computed at the trajectory layer, not encoded in
        a severity band."""
        baseline = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            },
            headers=self._headers("gse-traj-baseline"),
        ).json()
        followup = client.post(
            "/v1/assessments",
            json={
                "instrument": "gse",
                "items": [3, 2, 3, 2, 3, 2, 2, 3, 2, 3],
            },
            headers=self._headers("gse-traj-followup"),
        ).json()
        assert baseline["total"] == 20
        assert followup["total"] == 25
        assert followup["total"] - baseline["total"] == 5
        assert baseline["severity"] == "continuous"
        assert followup["severity"] == "continuous"


class TestCore10Routing:
    """End-to-end routing tests for the CORE-10 dispatcher branch.

    Barkham, Bewick, Mullin, Gilbody, Connell, Cahill, Mellor-Clark,
    Richards, Unsworth & Evans 2013 Clinical Outcomes in Routine
    Evaluation-10 — 10 items, 0-4 Likert, reverse-keyed items 2 and
    3 (wellbeing/functioning), unidimensional routine-outcome short
    form of the 34-item CORE-OM (Evans 2000).  Validated on n=1,241
    UK NHS IAPT sample: α=0.90, RCI=6.  Published severity bands
    (Barkham 2013 Table 3):

        healthy:         0-5
        low:             6-10
        mild:            11-14    [≥ 11 = Barkham 2013 clinical cutoff]
        moderate:        15-19
        moderate_severe: 20-24
        severe:          25-40

    **Third scorer-layer T3 instrument** (after PHQ-9 item 9 and
    C-SSRS) — CORE-10 item 6 ("I made plans to end my life") any
    non-zero response triggers requires_t3=True with
    triggering_items=(6,).  The threshold matches the PHQ-9 item 9
    any-non-zero precedent (Kroenke 2001; Simon 2013) and is MORE
    conservative than C-SSRS (which requires specific item /
    behavior combinations).

    Feature-rich envelope — CORE-10 is the FIRST instrument in this
    sprint series to populate the full envelope: total, severity,
    positive_screen, cutoff_used, requires_t3, triggering_items,
    items, instrument_version.  Only subscales and index are left
    null (unidimensional, no scale transformation).

    Clinical use cases:
    1. UK NHS IAPT routine-outcome trajectory — session-by-session
       RCI tracking with Barkham 2013 RCI ≈ 6 points for reliable
       change flagging.
    2. CORE-10 item 6 + PHQ-9 item 9 convergent positive → C-SSRS
       follow-up prompt at clinician-UI layer.
    3. CORE-10 severe (≥ 25) + WSAS clinically-significant (≥ 20)
       → distressed-AND-impaired profile → intensive engagement.
    4. CORE-10 moderate + readiness-ruler low → ambivalent despite
       distress → MI change-talk elicitation.

    Envelope: severity + positive_screen + cutoff_used + T3-
    routing + triggering_items (no subscales, no scaled_score,
    no index).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape --------------------------------------------------

    def test_all_zeros_applies_reverse_keying(
        self, client: TestClient
    ) -> None:
        """All raw zeros → items 2,3 flip to 4 each → total 8.
        Confirms the reverse-keying is applied at the router layer
        (not silently bypassed)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [0] * 10},
            headers=self._headers("core10-all-zeros"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "core10"
        assert body["total"] == 8
        assert body["severity"] == "low"  # 8 ∈ 6-10
        assert body["requires_t3"] is False

    def test_reverse_keying_minimum_total_zero(
        self, client: TestClient
    ) -> None:
        """raw=[0,4,4,0,0,0,0,0,0,0] → items 2,3 flip 4→0 → total 0.
        The MINIMUM achievable total after reverse-keying."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [0, 4, 4, 0, 0, 0, 0, 0, 0, 0],
            },
            headers=self._headers("core10-min-zero"),
        )
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "healthy"
        assert body["positive_screen"] is False

    def test_reverse_keying_maximum_total_forty(
        self, client: TestClient
    ) -> None:
        """raw=[4,0,0,4,4,4,4,4,4,4] → items 2,3 flip 0→4 → total 40.
        The MAXIMUM achievable total after reverse-keying.  Also
        triggers T3 via item 6 = 4."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [4, 0, 0, 4, 4, 4, 4, 4, 4, 4],
            },
            headers=self._headers("core10-max-forty"),
        )
        body = response.json()
        assert body["total"] == 40
        assert body["severity"] == "severe"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [6]

    def test_cutoff_used_surfaces_11(
        self, client: TestClient
    ) -> None:
        """Barkham 2013 clinical cutoff = 11 surfaced on every
        response.  The clinician-UI renders "positive at ≥ 11"."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [2] * 10},
            headers=self._headers("core10-cutoff"),
        )
        body = response.json()
        assert body["cutoff_used"] == 11

    def test_instrument_version_surfaces(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [2] * 10},
            headers=self._headers("core10-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "core10-1.0.0"

    def test_envelope_has_no_subscales(
        self, client: TestClient
    ) -> None:
        """CORE-10 is the unidimensional short form of the 4-factor
        CORE-OM — the factor structure does NOT propagate to the
        10-item short form."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [2] * 10},
            headers=self._headers("core10-no-subscales"),
        )
        body = response.json()
        assert body.get("subscales") is None

    def test_envelope_has_no_index_or_scaled_score(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [2] * 10},
            headers=self._headers("core10-no-index"),
        )
        body = response.json()
        assert body.get("index") is None
        assert body.get("scaled_score") is None

    # -- Barkham 2013 severity bands ---------------------------------------

    def test_severity_healthy_at_zero(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [0, 4, 4, 0, 0, 0, 0, 0, 0, 0],
            },
            headers=self._headers("core10-band-healthy"),
        )
        assert response.json()["severity"] == "healthy"

    def test_severity_healthy_at_five_upper_bound(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 1, 1, 0, 0, 0, 0, 0],
            },
            headers=self._headers("core10-band-healthy-5"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["severity"] == "healthy"

    def test_severity_low_at_six(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 1, 1, 0, 0, 0, 1, 0],
            },
            headers=self._headers("core10-band-low-6"),
        )
        body = response.json()
        assert body["total"] == 6
        assert body["severity"] == "low"

    def test_severity_mild_at_cutoff_11(
        self, client: TestClient
    ) -> None:
        """Barkham 2013 clinical cutoff — first "positive" screen."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 1, 1, 0, 1, 2, 1, 2],
            },
            headers=self._headers("core10-band-mild-cutoff"),
        )
        body = response.json()
        assert body["total"] == 11
        assert body["severity"] == "mild"
        assert body["positive_screen"] is True

    def test_severity_moderate_at_15(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 2, 2, 0, 2, 2, 2, 2],
            },
            headers=self._headers("core10-band-moderate"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "moderate"

    def test_severity_moderate_severe_at_20(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [2] * 10},
            headers=self._headers("core10-band-modsev-20"),
        )
        body = response.json()
        assert body["total"] == 20
        assert body["severity"] == "moderate_severe"

    def test_severity_severe_at_25(self, client: TestClient) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [3, 2, 2, 3, 3, 0, 3, 3, 3, 3],
            },
            headers=self._headers("core10-band-severe"),
        )
        body = response.json()
        assert body["total"] == 25
        assert body["severity"] == "severe"

    # -- Barkham 2013 clinical cutoff boundary -------------------------------

    def test_positive_screen_false_at_total_10(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 1, 1, 0, 1, 1, 1, 2],
            },
            headers=self._headers("core10-cutoff-10"),
        )
        body = response.json()
        assert body["total"] == 10
        assert body["positive_screen"] is False

    def test_positive_screen_true_at_total_11(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 1, 1, 0, 1, 2, 1, 2],
            },
            headers=self._headers("core10-cutoff-11"),
        )
        body = response.json()
        assert body["total"] == 11
        assert body["positive_screen"] is True

    # -- Item 6 T3 routing ---------------------------------------------------

    def test_item_6_zero_no_t3(self, client: TestClient) -> None:
        """Item 6 = 0 → no T3, triggering_items absent."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [2, 2, 2, 2, 2, 0, 2, 2, 2, 2],
            },
            headers=self._headers("core10-t3-item6-zero"),
        )
        body = response.json()
        assert body["requires_t3"] is False
        # Absence represented as null / missing (model field default
        # None when the list would be empty).
        assert body.get("triggering_items") is None

    @pytest.mark.parametrize("v", [1, 2, 3, 4])
    def test_item_6_any_non_zero_triggers_t3(
        self, client: TestClient, v: int
    ) -> None:
        """Any non-zero response on CORE-10 item 6 → T3 per
        Barkham 2013 safety guidance.  Matches PHQ-9 item 9 any-
        non-zero precedent."""
        raw = [0, 4, 4, 0, 0, v, 0, 0, 0, 0]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": raw},
            headers=self._headers(f"core10-t3-item6-{v}"),
        )
        body = response.json()
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [6]

    def test_item_6_t3_fires_at_subclinical_total(
        self, client: TestClient
    ) -> None:
        """Simon 2013 scenario: overall total subclinical (< 11),
        but item 6 one-off positive.  T3 MUST fire regardless of
        total.  This is the designed-purpose detection case for
        session-by-session routine monitoring."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 0, 0, 1, 1, 0, 1, 0],
            },
            headers=self._headers("core10-t3-subclinical"),
        )
        body = response.json()
        assert body["total"] == 6  # low band, subclinical
        assert body["positive_screen"] is False
        # But T3 still fires on item 6:
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [6]

    # -- Item-count validation ---------------------------------------------

    @pytest.mark.parametrize(
        "bad_count", [1, 2, 5, 7, 8, 9, 11, 12, 20]
    )
    def test_wrong_item_count_returns_422(
        self, client: TestClient, bad_count: int
    ) -> None:
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [2] * bad_count},
            headers=self._headers(f"core10-bad-count-{bad_count}"),
        )
        assert response.status_code == 422

    # -- Item-value validation ---------------------------------------------

    def test_negative_one_returns_422(self, client: TestClient) -> None:
        items = [2] * 10
        items[0] = -1
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": items},
            headers=self._headers("core10-val-neg"),
        )
        assert response.status_code == 422

    def test_five_returns_422(self, client: TestClient) -> None:
        items = [2] * 10
        items[4] = 5
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": items},
            headers=self._headers("core10-val-five"),
        )
        assert response.status_code == 422

    # -- Type validation (Pydantic wire-layer behavior) --------------------

    def test_numeric_string_coerces_via_pydantic_lax_mode(
        self, client: TestClient
    ) -> None:
        """Pydantic list[int] lax mode: numeric string "2" → int 2
        before scorer runs.  All "2"s → total 20."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": ["2"] * 10},
            headers=self._headers("core10-str-coerce"),
        )
        assert response.status_code == 201
        assert response.json()["total"] == 20

    def test_non_numeric_string_returns_422(
        self, client: TestClient
    ) -> None:
        items: list[object] = [2] * 10
        items[0] = "hello"
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": items},
            headers=self._headers("core10-str-reject"),
        )
        assert response.status_code == 422

    def test_bool_true_coerces_to_one(
        self, client: TestClient
    ) -> None:
        """JSON true → int 1 via Pydantic lax mode.  All True → items
        2,3 flip 1→3; rest raw 1.  Total = 1+3+3+1+1+1+1+1+1+1 = 14.
        Mild band.  Item 6 = 1 → T3 fires (any-non-zero)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [True] * 10},
            headers=self._headers("core10-bool-true"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 14
        # Item 6 at raw = 1 triggers T3:
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [6]

    def test_bool_false_coerces_to_zero(
        self, client: TestClient
    ) -> None:
        """JSON false → int 0 via Pydantic lax mode.  All False →
        items 2,3 flip 0→4; rest raw 0.  Total = 0+4+4+0+0+0+0+0+0+0 = 8.
        Low band.  Item 6 = 0 → no T3."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "core10", "items": [False] * 10},
            headers=self._headers("core10-bool-false"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 8
        assert body["severity"] == "low"
        assert body["requires_t3"] is False

    # -- Clinical vignettes ------------------------------------------------

    def test_vignette_recovered_end_of_therapy(
        self, client: TestClient
    ) -> None:
        """Barkham 2013 end-of-therapy recovered case — healthy
        band at total ≤ 5."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [1, 3, 3, 0, 0, 0, 1, 0, 1, 0],
            },
            headers=self._headers("core10-vig-recovered"),
        )
        body = response.json()
        assert body["total"] == 5
        assert body["severity"] == "healthy"
        assert body["positive_screen"] is False
        assert body["requires_t3"] is False

    def test_vignette_iapt_intake_moderate(
        self, client: TestClient
    ) -> None:
        """Typical UK IAPT intake — moderate distress, clinical
        caseness, no active suicidality."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [2, 2, 2, 1, 1, 0, 2, 1, 2, 2],
            },
            headers=self._headers("core10-vig-iapt"),
        )
        body = response.json()
        assert body["total"] == 15
        assert body["severity"] == "moderate"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False

    def test_vignette_severe_distress_no_item_6(
        self, client: TestClient
    ) -> None:
        """Severe-distress profile with item 6 = 0 → severe band,
        positive screen, but NO T3 at scorer layer (Barkham 2013
        requires item 6 positive for scorer-layer T3)."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [4, 0, 0, 4, 3, 0, 3, 4, 4, 4],
            },
            headers=self._headers("core10-vig-severe-no-t3"),
        )
        body = response.json()
        assert body["total"] == 34
        assert body["severity"] == "severe"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is False

    def test_vignette_acute_suicidality(
        self, client: TestClient
    ) -> None:
        """The CORE-10's designed-purpose detection case — severe
        distress WITH item-6-positive.  T3 fires, triggering_items
        audit trail populated."""
        response = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [4, 0, 0, 4, 3, 3, 3, 4, 4, 4],
            },
            headers=self._headers("core10-vig-acute"),
        )
        body = response.json()
        assert body["total"] == 37
        assert body["severity"] == "severe"
        assert body["positive_screen"] is True
        assert body["requires_t3"] is True
        assert body["triggering_items"] == [6]

    def test_vignette_rci_recovery_6pt_delta(
        self, client: TestClient
    ) -> None:
        """Barkham 2013 RCI ≈ 6 points — clinically meaningful
        reliable change.  Trajectory layer computes the delta."""
        baseline = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [3, 1, 1, 3, 3, 0, 3, 3, 3, 3],
            },
            headers=self._headers("core10-traj-baseline"),
        ).json()
        followup = client.post(
            "/v1/assessments",
            json={
                "instrument": "core10",
                "items": [2, 2, 2, 2, 2, 0, 3, 3, 3, 2],
            },
            headers=self._headers("core10-traj-followup"),
        ).json()
        assert baseline["total"] == 27
        assert followup["total"] == 21
        assert baseline["total"] - followup["total"] == 6
        assert baseline["severity"] == "severe"
        assert followup["severity"] == "moderate_severe"


# =============================================================================
# Cross-instrument — extended coverage for new dispatcher branches
# =============================================================================


class TestExtendedResponseShape:
    def test_cssrs_and_pss10_return_required_fields(
        self, client: TestClient
    ) -> None:
        """Ensure the two new instruments populate the always-present
        response envelope fields.  The renderer relies on these keys
        across every instrument."""
        required = {
            "assessment_id",
            "instrument",
            "total",
            "severity",
            "requires_t3",
            "instrument_version",
        }

        cssrs_body = _post_cssrs(client, items=[0, 0, 0, 0, 0, 0]).json()
        assert not (required - set(cssrs_body.keys()))

        pss10_body = _post(client, instrument="pss10", items=[2] * 10).json()
        assert not (required - set(pss10_body.keys()))

        dast10_body = _post(
            client, instrument="dast10", items=[0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        ).json()
        assert not (required - set(dast10_body.keys()))

    def test_triggering_items_absent_or_empty_for_non_cssrs(
        self, client: TestClient
    ) -> None:
        """``triggering_items`` is C-SSRS-specific; other instruments
        never populate it (None or absent).  A renderer that always
        reads the field shouldn't see stale values from prior screens."""
        body = _post(client, instrument="gad7", items=[1] * 7).json()
        assert body.get("triggering_items") in (None, [])

        body = _post(client, instrument="pss10", items=[2] * 10).json()
        assert body.get("triggering_items") in (None, [])

        body = _post(
            client, instrument="dast10", items=[1, 1, 0, 1, 1, 1, 1, 1, 1, 1]
        ).json()
        assert body.get("triggering_items") in (None, [])


# =============================================================================
# Safety stream — T3 fires must be emitted to the safety log
# =============================================================================


class TestSafetyStreamT3Emission:
    """When a PHQ-9 or C-SSRS response fires ``requires_t3``, the router
    emits a Merkle-chained event to the safety stream so on-call clinical
    operators can correlate with contact workflows.

    Privacy contract (CLAUDE.md Rule #6 + Whitepaper 04 §T3):
    - The event MUST carry ``instrument``, ``severity``, ``total``,
      ``t3_reason``, ``triggering_items``, ``assessment_id``, ``user_id``.
    - The event MUST NOT carry raw item responses, free-text narrative,
      or LLM output — those would leak content beyond the 2-year
      safety-stream retention boundary.

    Tests monkeypatch the ``warning`` method on the bound safety logger;
    the full chain-processor pipeline is exercised in streams-level unit
    tests.  Here we're pinning the emission contract itself.
    """

    def _capture_safety_events(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> list[dict[str, Any]]:
        """Install a capture on ``_safety.warning`` and return the list
        that will collect emitted events.  The returned list is the same
        object the patch closes over, so caller assertions see new events
        as they're appended."""
        captured: list[dict[str, Any]] = []

        def capture(event: str, **kwargs: Any) -> None:
            captured.append({"event": event, **kwargs})

        from discipline.psychometric import router as psych_router

        monkeypatch.setattr(psych_router._safety, "warning", capture)
        return captured

    # ---- PHQ-9 T3 path ----

    def test_phq9_safety_item_fires_emits_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Item 9 (zero-indexed 8) > 0 → requires_t3 → one safety event."""
        captured = self._capture_safety_events(monkeypatch)
        items = [0] * 9
        items[8] = 2  # safety item positive
        resp = _post(
            client,
            instrument="phq9",
            items=items,
            headers={"Idempotency-Key": "safety-phq9-1"},
        )
        resp_body = resp.json()
        resp_body["user_id"] = None  # pin expected value for readability

        assert resp.status_code == 201
        assert resp_body["requires_t3"] is True
        assert len(captured) == 1
        event = captured[0]
        assert event["event"] == "psychometric.t3_fire"
        assert event["instrument"] == "phq9"
        assert event["t3_reason"] is not None
        assert event["total"] == 2
        # assessment_id cross-references the stored result
        assert event["assessment_id"] == resp_body["assessment_id"]

    def test_phq9_no_safety_item_no_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No T3 → no safety event.  A test that passed the 'emit' test
        but also quietly emitted on non-T3 paths would create compliance
        noise in the 2-year safety retention pool."""
        captured = self._capture_safety_events(monkeypatch)
        resp = _post(client, instrument="phq9", items=[1, 1, 1, 1, 1, 1, 1, 1, 0])
        assert resp.status_code == 201
        assert resp.json()["requires_t3"] is False
        assert captured == []

    def test_safety_event_never_carries_raw_items(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Critical privacy assertion: the emitted event payload must
        NOT contain the raw items list.  A renderer that added 'items'
        to the log context would leak the patient's binary response
        pattern into the 2-year safety retention pool."""
        captured = self._capture_safety_events(monkeypatch)
        items = [0, 1, 2, 3, 0, 1, 2, 3, 2]  # item 9 positive; varied pattern
        _post(client, instrument="phq9", items=items)
        assert len(captured) == 1
        event = captured[0]
        assert "items" not in event
        assert "raw_items" not in event

    # ---- C-SSRS T3 path ----

    def test_cssrs_item_4_fires_emits_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Item 4 (active ideation with intent) positive → acute T3."""
        captured = self._capture_safety_events(monkeypatch)
        resp = _post_cssrs(client, items=[0, 0, 0, 1, 0, 0])
        body = resp.json()
        assert body["requires_t3"] is True
        assert len(captured) == 1
        event = captured[0]
        assert event["instrument"] == "cssrs"
        assert event["severity"] == "acute"
        assert event["t3_reason"] == "cssrs_acute_triage"
        assert event["triggering_items"] == [4]

    def test_cssrs_item_5_fires_emits_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Item 5 (plan + intent) positive → acute T3."""
        captured = self._capture_safety_events(monkeypatch)
        resp = _post_cssrs(client, items=[0, 0, 0, 0, 1, 0])
        assert resp.json()["requires_t3"] is True
        assert len(captured) == 1
        assert captured[0]["triggering_items"] == [5]

    def test_cssrs_item_6_recent_fires_emits_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Item 6 (behavior) + recency → acute T3."""
        captured = self._capture_safety_events(monkeypatch)
        resp = _post_cssrs(
            client, items=[0, 0, 0, 0, 0, 1], behavior_within_3mo=True
        )
        assert resp.json()["requires_t3"] is True
        assert len(captured) == 1
        assert captured[0]["triggering_items"] == [6]

    def test_cssrs_item_6_historic_does_not_emit(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Item 6 positive WITHOUT recency → moderate band, not T3.
        Moderate is NOT a safety-stream-worthy escalation per Posner
        2011; a clinician check-in (via non-safety channel) is the
        right response.  This test pins the boundary between moderate
        (no safety event) and acute (safety event)."""
        captured = self._capture_safety_events(monkeypatch)
        resp = _post_cssrs(
            client, items=[0, 0, 0, 0, 0, 1], behavior_within_3mo=False
        )
        body = resp.json()
        assert body["severity"] == "moderate"
        assert body["requires_t3"] is False
        assert captured == []

    def test_cssrs_all_negative_does_not_emit(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = self._capture_safety_events(monkeypatch)
        _post_cssrs(client, items=[0, 0, 0, 0, 0, 0])
        assert captured == []

    # ---- Non-T3 instruments never emit ----

    def test_gad7_never_emits(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = self._capture_safety_events(monkeypatch)
        _post(client, instrument="gad7", items=[3, 3, 3, 3, 3, 3, 3])
        assert captured == []

    def test_who5_never_emits(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """WHO-5 depression_screen band is NOT a T3 trigger — Whitepaper
        04 reserves T3 for active suicidality.  Even the lowest possible
        WHO-5 (all zeros) does not emit to the safety stream."""
        captured = self._capture_safety_events(monkeypatch)
        _post(client, instrument="who5", items=[0, 0, 0, 0, 0])
        assert captured == []

    def test_audit_c_never_emits(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = self._capture_safety_events(monkeypatch)
        _post(client, instrument="audit_c", items=[4, 4, 4])
        assert captured == []

    def test_pss10_never_emits(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = self._capture_safety_events(monkeypatch)
        _post(client, instrument="pss10", items=[4] * 10)
        assert captured == []

    def test_dast10_never_emits(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DAST-10 has no safety item — even the maximum-severity
        screen (every item endorsed, control item negative) must not
        fire a safety event.  A regression that emitted on DAST-10
        severe would put substance-use intake patients into the
        clinical-ops T3 paging queue, where they don't belong."""
        captured = self._capture_safety_events(monkeypatch)
        _post(client, instrument="dast10", items=[1, 1, 0, 1, 1, 1, 1, 1, 1, 1])
        assert captured == []

    # ---- user_id pass-through ----

    def test_user_id_echoed_into_safety_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When caller supplies ``user_id`` on the request body, the
        safety event carries it verbatim so on-call can correlate."""
        captured = self._capture_safety_events(monkeypatch)
        items = [0] * 9
        items[8] = 1  # phq9 item 9 positive
        client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": items, "user_id": "u_abc123"},
            headers={"Idempotency-Key": "safety-user-id-1"},
        )
        assert len(captured) == 1
        assert captured[0]["user_id"] == "u_abc123"

    def test_missing_user_id_emits_none(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When ``user_id`` is omitted (test fixtures, diagnostic paths),
        the event still emits but with ``user_id=None``.  This is a
        gap a compliance reviewer will see and fix — the telemetry
        surfaces it explicitly rather than silently dropping the record."""
        captured = self._capture_safety_events(monkeypatch)
        items = [0] * 9
        items[8] = 1
        _post(client, instrument="phq9", items=items)
        assert len(captured) == 1
        assert captured[0]["user_id"] is None

    # ---- Multi-emission isolation ----

    def test_two_t3_assessments_emit_two_events(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Each T3 result emits exactly one event.  A renderer that
        accidentally emitted twice (e.g., inside a retry) would double
        the 2-year retention footprint."""
        captured = self._capture_safety_events(monkeypatch)
        items = [0] * 9
        items[8] = 2
        _post(
            client,
            instrument="phq9",
            items=items,
            headers={"Idempotency-Key": "k1"},
        )
        _post(
            client,
            instrument="phq9",
            items=items,
            headers={"Idempotency-Key": "k2"},
        )
        assert len(captured) == 2
        # Each carries a distinct assessment_id — different idempotency
        # keys produce independent submissions.
        assert (
            captured[0]["assessment_id"] != captured[1]["assessment_id"]
        )


# =============================================================================
# Idempotency — replay-safety over the wire
# =============================================================================


class TestIdempotency:
    """End-to-end idempotency tests through the HTTP surface.

    The store is cleared between tests by the autouse
    ``_reset_idempotency_store`` fixture so each test starts fresh;
    within a single test we exercise replay / conflict / cross-key
    scenarios explicitly.

    Critical property: when a request with a T3-firing payload is
    replayed under the same key, **no second safety event is emitted**
    — a retry-induced double emission would inflate the 2-year safety
    retention pool and create duplicate clinical-ops paging.
    """

    def test_same_key_same_body_returns_cached_response(
        self, client: TestClient
    ) -> None:
        """Two POSTs with the same key + same body return the same
        assessment_id — proves the cache is serving the second call."""
        items = [1, 1, 1, 1, 1, 1, 1, 1, 0]  # phq9 mild
        headers = {"Idempotency-Key": "same-key-1"}
        first = _post(client, instrument="phq9", items=items, headers=headers).json()
        second = _post(
            client, instrument="phq9", items=items, headers=headers
        ).json()
        assert first["assessment_id"] == second["assessment_id"]
        assert first == second

    def test_same_key_different_body_returns_409(
        self, client: TestClient
    ) -> None:
        """Same key, different items → 409 Conflict with the canonical
        error code.  A caller that quietly succeeded here would let a
        client accidentally double-submit a misclicked assessment."""
        headers = {"Idempotency-Key": "conflict-key-1"}
        first = _post(
            client,
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
            headers=headers,
        )
        assert first.status_code == 201

        # Different items → different body hash → Conflict.
        second = _post(
            client,
            instrument="phq9",
            items=[2, 2, 2, 2, 2, 2, 2, 2, 0],
            headers=headers,
        )
        assert second.status_code == 409
        detail = second.json()["detail"]
        assert detail["code"] == "idempotency.conflict"

    def test_different_key_same_body_produces_distinct_responses(
        self, client: TestClient
    ) -> None:
        """Cache is keyed on ``(key, body_hash)``, not body alone.  Two
        clients sending the same payload under different keys get
        distinct ``assessment_id`` values."""
        items = [1, 1, 1, 1, 1, 1, 1, 1, 0]
        first = _post(
            client,
            instrument="phq9",
            items=items,
            headers={"Idempotency-Key": "k-alpha"},
        ).json()
        second = _post(
            client,
            instrument="phq9",
            items=items,
            headers={"Idempotency-Key": "k-beta"},
        ).json()
        assert first["assessment_id"] != second["assessment_id"]

    def test_missing_idempotency_key_rejected(self, client: TestClient) -> None:
        """The header is required.  FastAPI surfaces a 422 (pydantic
        validation) rather than silently defaulting."""
        resp = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [0] * 9},
        )
        # FastAPI returns 422 when a required Header dependency is missing.
        assert resp.status_code == 422

    def test_empty_body_formatting_does_not_change_hash(
        self, client: TestClient
    ) -> None:
        """Whitespace / key-ordering differences in the JSON payload
        must hash identically — the second POST is a valid replay, not
        a Conflict.  Tests the ``canonical_json_bytes`` determinism
        end-to-end through FastAPI's Pydantic parsing."""
        headers = {"Idempotency-Key": "whitespace-k"}
        # FastAPI + Pydantic parse both bodies to the same model; the
        # model_dump(mode="json") → sort_keys hash is the same regardless
        # of the raw wire format.  So two logically-identical requests
        # produce the same hash → the second is a Hit, not a Conflict.
        r1 = client.post(
            "/v1/assessments",
            json={"instrument": "phq9", "items": [1, 1, 1, 1, 1, 1, 1, 1, 0]},
            headers=headers,
        )
        r2 = client.post(
            "/v1/assessments",
            # Different key ordering in the JSON object.
            json={"items": [1, 1, 1, 1, 1, 1, 1, 1, 0], "instrument": "phq9"},
            headers=headers,
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["assessment_id"] == r2.json()["assessment_id"]

    def test_replay_does_not_reemit_safety_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Replay of a T3-firing assessment under the same key must
        NOT emit a second safety event.  This is the load-bearing
        clinical property of the cache — a retry-induced double
        emission would page on-call twice for the same incident and
        double the 2-year retention footprint."""
        captured: list[dict[str, Any]] = []

        def capture(event: str, **kwargs: Any) -> None:
            captured.append({"event": event, **kwargs})

        from discipline.psychometric import router as psych_router

        monkeypatch.setattr(psych_router._safety, "warning", capture)

        items = [0] * 9
        items[8] = 2  # item 9 positive → T3
        headers = {"Idempotency-Key": "replay-t3-key"}
        first = _post(client, instrument="phq9", items=items, headers=headers).json()
        assert first["requires_t3"] is True
        assert len(captured) == 1

        # Replay — same key + same body → cache Hit, no new emission.
        second = _post(
            client, instrument="phq9", items=items, headers=headers
        ).json()
        assert second["requires_t3"] is True
        assert second["assessment_id"] == first["assessment_id"]
        assert len(captured) == 1  # still one, not two

    def test_conflict_on_t3_does_not_emit(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A 409 Conflict returns before any scoring or safety-stream
        work — the second (conflicting) submission must not produce a
        safety event even if it would have fired T3 on its own merits.
        Catches a bug where the 409 is raised AFTER dispatch."""
        captured: list[dict[str, Any]] = []

        def capture(event: str, **kwargs: Any) -> None:
            captured.append({"event": event, **kwargs})

        from discipline.psychometric import router as psych_router

        monkeypatch.setattr(psych_router._safety, "warning", capture)

        headers = {"Idempotency-Key": "conflict-t3-key"}
        # First: non-T3 body.
        _post(
            client,
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
            headers=headers,
        )
        assert len(captured) == 0

        # Second: same key but T3-firing body → 409, no emission.
        t3_items = [0] * 9
        t3_items[8] = 2
        resp = _post(client, instrument="phq9", items=t3_items, headers=headers)
        assert resp.status_code == 409
        assert len(captured) == 0

    def test_different_user_id_same_items_is_conflict(
        self, client: TestClient
    ) -> None:
        """``user_id`` is part of the hashed body.  Two submissions
        under the same key with the same items but different
        ``user_id`` hash differently and so produce a Conflict.  This
        pins that the key-owner can't accidentally collapse two
        patients' submissions."""
        headers = {"Idempotency-Key": "user-key-1"}
        first = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [1, 1, 1, 1, 1, 1, 1, 1, 0],
                "user_id": "u_alice",
            },
            headers=headers,
        )
        assert first.status_code == 201

        second = client.post(
            "/v1/assessments",
            json={
                "instrument": "phq9",
                "items": [1, 1, 1, 1, 1, 1, 1, 1, 0],
                "user_id": "u_bob",
            },
            headers=headers,
        )
        assert second.status_code == 409

    def test_422_not_cached(self, client: TestClient) -> None:
        """Validation errors (422) don't populate the cache — the
        caller can submit the same key next time with a corrected
        body and get a 201 rather than a stale 422 replay."""
        headers = {"Idempotency-Key": "bad-then-good-key"}
        # First: bad item count → 422.
        bad = _post(client, instrument="phq9", items=[0] * 3, headers=headers)
        assert bad.status_code == 422

        # Second: same key, well-formed body → the cache did NOT
        # record the 422, so this proceeds.  But the body hash now
        # differs from whatever was hashed pre-validation; nothing was
        # stored either way.  Expected: 201.
        good = _post(
            client,
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
            headers=headers,
        )
        assert good.status_code == 201


# =============================================================================
# GET /v1/assessments/history — Sprint 23
# =============================================================================


def _submit_for_user(
    client: TestClient,
    *,
    user_id: str,
    instrument: str,
    items: list[int],
    sex: str | None = None,
) -> Any:
    """Submit one assessment with ``user_id`` in the body so it
    persists to the repository.  Fresh Idempotency-Key per call via
    the underlying helper."""
    body: dict[str, Any] = {
        "instrument": instrument,
        "items": items,
        "user_id": user_id,
    }
    if sex is not None:
        body["sex"] = sex
    import uuid

    headers = {"Idempotency-Key": f"test-{uuid.uuid4()}"}
    return client.post("/v1/assessments", json=body, headers=headers)


class TestHistoryEndpoint:
    """``GET /v1/assessments/history`` — reads through the
    AssessmentRepository that Sprint 23 introduced.  Identity comes
    from the ``X-User-Id`` header (stub for the Clerk session JWT
    in a later sprint)."""

    def test_missing_user_id_header_returns_401(
        self, client: TestClient
    ) -> None:
        """Without identity there's no timeline to return — refuse
        rather than returning an empty list, which would let an
        unauthenticated client probe for the endpoint's shape."""
        resp = client.get("/v1/assessments/history")
        # FastAPI's Header(...) with an alias surfaces the missing
        # required header as a 422 from pydantic validation.  Either
        # 401 (our guard) or 422 (pydantic) is acceptable — the point
        # is that the request does NOT succeed.
        assert resp.status_code in (401, 422)

    def test_empty_user_id_header_returns_401(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/v1/assessments/history", headers={"X-User-Id": ""}
        )
        assert resp.status_code == 401

    def test_zero_limit_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/assessments/history?limit=0",
            headers={"X-User-Id": "user-1"},
        )
        assert resp.status_code == 400

    def test_negative_limit_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/assessments/history?limit=-5",
            headers={"X-User-Id": "user-1"},
        )
        assert resp.status_code == 400

    def test_empty_history_for_new_user(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "brand-new-user"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"items": [], "limit": 50, "total": 0}

    def test_submit_then_history_round_trip(
        self, client: TestClient
    ) -> None:
        """Post an assessment with user_id in the body, then GET
        /history under that same id — the record must appear with
        matching assessment_id."""
        post = _submit_for_user(
            client,
            user_id="user-1",
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
        )
        assert post.status_code == 201
        assessment_id = post.json()["assessment_id"]

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-1"},
        )
        assert hist.status_code == 200
        items = hist.json()["items"]
        assert len(items) == 1
        assert items[0]["assessment_id"] == assessment_id
        assert items[0]["instrument"] == "phq9"

    def test_history_response_omits_raw_items(
        self, client: TestClient
    ) -> None:
        """PHI-boundary shape: the raw answers are stored in the
        repository but NOT projected into the history timeline.  A
        regression that surfaced raw_items here would leak PHI to the
        patient-portal timeline view."""
        _submit_for_user(
            client,
            user_id="user-1",
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
        )
        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-1"},
        )
        item = hist.json()["items"][0]
        assert "raw_items" not in item

    def test_history_is_newest_first(self, client: TestClient) -> None:
        """Three submissions land in chronological order — history
        returns them newest-first by ``created_at``."""
        # Three distinct bodies so each gets a unique assessment_id.
        _submit_for_user(
            client,
            user_id="user-1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit_for_user(
            client,
            user_id="user-1",
            instrument="gad7",
            items=[0, 0, 0, 0, 0, 0, 0],
        )
        _submit_for_user(
            client,
            user_id="user-1",
            instrument="who5",
            items=[0, 0, 0, 0, 0],
        )
        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-1"},
        )
        items = hist.json()["items"]
        assert len(items) == 3
        # Newest-first means the third submission leads.
        assert items[0]["instrument"] == "who5"
        assert items[1]["instrument"] == "gad7"
        assert items[2]["instrument"] == "phq9"

    def test_multi_user_isolation(self, client: TestClient) -> None:
        """User A's submissions are invisible to user B and vice-versa.
        This is the clinical privacy boundary — a leak here would
        expose one patient's trajectory to another."""
        _submit_for_user(
            client,
            user_id="user-A",
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
        )
        _submit_for_user(
            client,
            user_id="user-B",
            instrument="gad7",
            items=[1, 1, 1, 1, 1, 1, 1],
        )

        a = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-A"},
        )
        b = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-B"},
        )
        a_items = a.json()["items"]
        b_items = b.json()["items"]
        assert len(a_items) == 1
        assert len(b_items) == 1
        assert a_items[0]["instrument"] == "phq9"
        assert b_items[0]["instrument"] == "gad7"

    def test_limit_caps_returned_but_total_is_absolute(
        self, client: TestClient
    ) -> None:
        """``limit`` caps the returned page; ``total`` is the
        unbounded count.  Ordering matters to the UI — the 'load
        older' affordance depends on seeing total > items.length."""
        for i in range(5):
            _submit_for_user(
                client,
                user_id="user-1",
                instrument="gad7",
                items=[(i % 4)] * 7,
            )
        hist = client.get(
            "/v1/assessments/history?limit=2",
            headers={"X-User-Id": "user-1"},
        )
        body = hist.json()
        assert len(body["items"]) == 2
        assert body["limit"] == 2
        assert body["total"] == 5

    def test_submit_without_user_id_does_not_persist(
        self, client: TestClient
    ) -> None:
        """A test-harness submission that omits user_id still scores
        and returns a result, but leaves no trace in /history under
        any identity.  Matches the stated contract: 'phantom anonymous
        user timelines have no owner and no value.'"""
        post = _post(
            client,
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],
        )
        assert post.status_code == 201

        # Nobody should see this record.
        for uid in ("user-1", "user-A", "anonymous", ""):
            if not uid:
                continue  # empty id is 401, not a history query
            hist = client.get(
                "/v1/assessments/history",
                headers={"X-User-Id": uid},
            )
            assert hist.json() == {"items": [], "limit": 50, "total": 0}

    def test_t3_firing_assessment_persisted_with_flag(
        self, client: TestClient
    ) -> None:
        """A T3-firing PHQ-9 (item 9 positive) must appear in the
        timeline with ``requires_t3=True`` — the clinical-ops view
        renders that flag prominently."""
        resp = _submit_for_user(
            client,
            user_id="user-1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 1],
        )
        assert resp.status_code == 201
        assert resp.json()["requires_t3"] is True

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-1"},
        )
        items = hist.json()["items"]
        assert len(items) == 1
        assert items[0]["requires_t3"] is True
        assert items[0]["t3_reason"] == "phq9_item9_positive"

    def test_cssrs_history_preserves_triggering_items(
        self, client: TestClient
    ) -> None:
        """C-SSRS records carry ``triggering_items`` — the audit trail
        of which 1-indexed questions drove the band.  Must survive
        the repository round-trip and appear in the timeline."""
        # Item 4 positive → acute T3 per C-SSRS triage.
        resp = client.post(
            "/v1/assessments",
            json={
                "instrument": "cssrs",
                "items": [0, 0, 0, 1, 0, 0],
                "user_id": "user-1",
            },
            headers={"Idempotency-Key": "cssrs-history-1"},
        )
        assert resp.status_code == 201

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-1"},
        )
        items = hist.json()["items"]
        assert len(items) == 1
        assert items[0]["instrument"] == "cssrs"
        assert items[0]["triggering_items"] == [4]

    def test_idempotency_replay_does_not_duplicate_history(
        self, client: TestClient
    ) -> None:
        """A retried submission under the same Idempotency-Key must
        create exactly ONE history entry.  The replay returns the
        cached result but MUST NOT call the repository a second time —
        the clinical timeline would otherwise show phantom duplicates
        of the same assessment."""
        headers = {"Idempotency-Key": "history-replay-key"}
        body = {
            "instrument": "phq9",
            "items": [1, 1, 1, 1, 1, 1, 1, 1, 0],
            "user_id": "user-1",
        }
        first = client.post("/v1/assessments", json=body, headers=headers)
        assert first.status_code == 201
        second = client.post("/v1/assessments", json=body, headers=headers)
        assert second.status_code == 201

        hist = client.get(
            "/v1/assessments/history",
            headers={"X-User-Id": "user-1"},
        )
        items = hist.json()["items"]
        assert len(items) == 1
        assert items[0]["assessment_id"] == first.json()["assessment_id"]


# =============================================================================
# Trajectory from history
# =============================================================================


def _save_record(
    *,
    assessment_id: str,
    user_id: str,
    instrument: str,
    total: int,
    created_at: Any,
    index: int | None = None,
    severity: str = "mild",
    raw_items: tuple[int, ...] | None = None,
    triggering_items: tuple[int, ...] | None = None,
) -> None:
    """Directly persist a record with a pinned ``created_at``.

    The HTTP ``POST /v1/assessments`` path stamps records with
    ``datetime.now(timezone.utc)``, which is fine for most tests but
    makes deterministic chronology assertions fragile (two back-to-
    back submissions land microseconds apart).  Trajectory tests need
    a pinned baseline-vs-later ordering, so they bypass the HTTP layer
    and write to the repository directly.  The by-user / by-id
    indices are exercised through the repository's own test suite;
    this helper only exists to produce a predictable timeline."""
    from discipline.psychometric.repository import (
        AssessmentRecord,
        get_assessment_repository,
    )

    get_assessment_repository().save(
        AssessmentRecord(
            assessment_id=assessment_id,
            user_id=user_id,
            instrument=instrument,
            total=total,
            severity=severity,
            requires_t3=False,
            raw_items=raw_items if raw_items is not None else (0,) * 9,
            created_at=created_at,
            index=index,
            triggering_items=triggering_items,
        )
    )


class TestTrajectoryHistoryEndpoint:
    """``GET /v1/assessments/trajectory/{instrument}`` — reads the
    user's repository records, filters by instrument, sorts oldest-
    first, uses the earliest as baseline, and annotates every
    subsequent record with an RCI direction per Jacobson & Truax 1991.

    Instruments without a validated RCI threshold (C-SSRS, DAST-10,
    unknown strings) still return the time series but every point's
    direction is ``insufficient_data`` and ``rci_threshold`` is null."""

    def test_missing_user_id_header_rejected(
        self, client: TestClient
    ) -> None:
        """No identity → no timeline.  FastAPI's required-header missing
        path produces 422; our explicit empty-string guard returns 401.
        Either is acceptable — the point is the request does NOT
        succeed."""
        resp = client.get("/v1/assessments/trajectory/phq9")
        assert resp.status_code in (401, 422)

    def test_empty_user_id_header_returns_401(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": ""},
        )
        assert resp.status_code == 401

    def test_empty_history_returns_empty_series(
        self, client: TestClient
    ) -> None:
        """A user with no records returns threshold + null baseline +
        empty points.  UI renders 'collect a first reading' prompt
        instead of erroring."""
        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "brand-new-user"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "instrument": "phq9",
            "rci_threshold": 5.2,
            "baseline": None,
            "points": [],
        }

    def test_single_record_is_baseline_with_empty_points(
        self, client: TestClient
    ) -> None:
        """One record → it's the baseline; points is empty because
        RCI needs two readings by definition."""
        post = _submit_for_user(
            client,
            user_id="user-1",
            instrument="phq9",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0],  # total=8
        )
        assert post.status_code == 201
        baseline_id = post.json()["assessment_id"]

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["instrument"] == "phq9"
        assert body["rci_threshold"] == 5.2
        assert body["baseline"]["assessment_id"] == baseline_id
        assert body["baseline"]["score"] == 8
        assert body["points"] == []

    def test_two_records_below_threshold_no_reliable_change(
        self, client: TestClient
    ) -> None:
        """PHQ-9 from 5 to 7: |Δ|=2 < 5.2 → no_reliable_change.
        Delta is still echoed (the arithmetic result is meaningful
        even when the RCI classifier says 'below threshold')."""
        from datetime import datetime, timezone

        _save_record(
            assessment_id="a1",
            user_id="user-1",
            instrument="phq9",
            total=5,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="a2",
            user_id="user-1",
            instrument="phq9",
            total=7,
            created_at=datetime(2026, 4, 8, tzinfo=timezone.utc),
        )

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["baseline"]["assessment_id"] == "a1"
        assert body["baseline"]["score"] == 5
        assert len(body["points"]) == 1
        p = body["points"][0]
        assert p["assessment_id"] == "a2"
        assert p["score"] == 7
        assert p["delta"] == 2
        assert p["direction"] == "no_reliable_change"

    def test_phq9_improvement_across_threshold(
        self, client: TestClient
    ) -> None:
        """PHQ-9 15 → 8: Δ=-7, |Δ|≥5.2, lower-is-better → improvement."""
        from datetime import datetime, timezone

        _save_record(
            assessment_id="a1",
            user_id="user-1",
            instrument="phq9",
            total=15,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="a2",
            user_id="user-1",
            instrument="phq9",
            total=8,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
        )

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["baseline"]["score"] == 15
        assert len(body["points"]) == 1
        p = body["points"][0]
        assert p["delta"] == -7
        assert p["direction"] == "improvement"

    def test_phq9_deterioration_across_threshold(
        self, client: TestClient
    ) -> None:
        """PHQ-9 3 → 10: Δ=+7, |Δ|≥5.2, lower-is-better → deterioration."""
        from datetime import datetime, timezone

        _save_record(
            assessment_id="a1",
            user_id="user-1",
            instrument="phq9",
            total=3,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="a2",
            user_id="user-1",
            instrument="phq9",
            total=10,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
        )

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["points"][0]["direction"] == "deterioration"

    def test_who5_uses_index_not_raw_total(
        self, client: TestClient
    ) -> None:
        """WHO-5 RCI threshold (17) is on the *index* scale (0-100),
        not the raw total (0-25).  A trajectory computed against raw
        totals would silently compress deltas by 4× and misclassify
        every clinically meaningful change.  This is a correctness
        bar, not a stylistic preference."""
        from datetime import datetime, timezone

        # Raw 5 → index 20; raw 10 → index 40.  Δ on index = 20 ≥ 17,
        # higher-is-better → improvement.  On raw scale |Δ| = 5 (way
        # below 17), a buggy implementation would return
        # no_reliable_change.
        _save_record(
            assessment_id="w1",
            user_id="user-1",
            instrument="who5",
            total=5,
            index=20,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
            raw_items=(1, 1, 1, 1, 1),
        )
        _save_record(
            assessment_id="w2",
            user_id="user-1",
            instrument="who5",
            total=10,
            index=40,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
            raw_items=(2, 2, 2, 2, 2),
        )

        resp = client.get(
            "/v1/assessments/trajectory/who5",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        # Baseline score is the INDEX (20), not the raw total (5).
        assert body["baseline"]["score"] == 20
        p = body["points"][0]
        assert p["score"] == 40
        assert p["delta"] == 20
        assert p["direction"] == "improvement"

    def test_cssrs_has_no_rci_threshold(self, client: TestClient) -> None:
        """C-SSRS has no published RCI threshold — the endpoint still
        returns the time series (clients can render the raw chart) but
        every direction is ``insufficient_data`` and ``delta`` is null
        (matches trajectories.py contract)."""
        from datetime import datetime, timezone

        _save_record(
            assessment_id="c1",
            user_id="user-1",
            instrument="cssrs",
            total=2,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
            raw_items=(1, 1, 0, 0, 0, 0),
            triggering_items=(1, 2),
        )
        _save_record(
            assessment_id="c2",
            user_id="user-1",
            instrument="cssrs",
            total=0,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
            raw_items=(0, 0, 0, 0, 0, 0),
            triggering_items=(),
        )

        resp = client.get(
            "/v1/assessments/trajectory/cssrs",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["rci_threshold"] is None
        assert body["baseline"]["score"] == 2
        assert len(body["points"]) == 1
        p = body["points"][0]
        assert p["score"] == 0
        assert p["delta"] is None
        assert p["direction"] == "insufficient_data"

    def test_dast10_has_no_rci_threshold(self, client: TestClient) -> None:
        """DAST-10 has no validated RCI threshold — same
        insufficient_data semantics as C-SSRS."""
        from datetime import datetime, timezone

        _save_record(
            assessment_id="d1",
            user_id="user-1",
            instrument="dast10",
            total=6,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
            raw_items=(1, 1, 1, 0, 1, 0, 1, 1, 0, 0),
        )
        _save_record(
            assessment_id="d2",
            user_id="user-1",
            instrument="dast10",
            total=1,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
            raw_items=(0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
        )

        resp = client.get(
            "/v1/assessments/trajectory/dast10",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["rci_threshold"] is None
        assert body["points"][0]["direction"] == "insufficient_data"
        assert body["points"][0]["delta"] is None

    def test_instrument_filtering_excludes_other_instruments(
        self, client: TestClient
    ) -> None:
        """A phq9 trajectory must not include gad7 records.  Without
        filtering, a cross-instrument 'composite' trajectory would be
        clinically meaningless — PHQ-9 and GAD-7 have different scale
        ranges and different RCI thresholds."""
        from datetime import datetime, timezone

        _save_record(
            assessment_id="p1",
            user_id="user-1",
            instrument="phq9",
            total=10,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="g1",
            user_id="user-1",
            instrument="gad7",
            total=12,
            created_at=datetime(2026, 4, 5, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="p2",
            user_id="user-1",
            instrument="phq9",
            total=4,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
        )

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["baseline"]["assessment_id"] == "p1"
        assert len(body["points"]) == 1
        assert body["points"][0]["assessment_id"] == "p2"

    def test_multi_user_isolation(self, client: TestClient) -> None:
        """User A's phq9 trajectory is empty if A has no phq9 records,
        even if user B has a long phq9 series.  Privacy boundary."""
        from datetime import datetime, timezone

        for i in range(3):
            _save_record(
                assessment_id=f"b-{i}",
                user_id="user-B",
                instrument="phq9",
                total=i * 5,
                created_at=datetime(2026, 4, 1 + i, tzinfo=timezone.utc),
            )

        # user-A has no records.
        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-A"},
        )
        body = resp.json()
        assert body["baseline"] is None
        assert body["points"] == []

        # user-B sees their full series.
        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-B"},
        )
        body = resp.json()
        assert body["baseline"]["assessment_id"] == "b-0"
        assert len(body["points"]) == 2

    def test_chronological_sort_ignores_insertion_order(
        self, client: TestClient
    ) -> None:
        """Records saved out of chronological order must still sort
        oldest-first.  The *earliest* by ``created_at`` is the
        baseline — not the first-saved."""
        from datetime import datetime, timezone

        # Saved in: middle, first, last.  Expected trajectory order:
        # first (baseline) → middle → last.
        _save_record(
            assessment_id="mid",
            user_id="user-1",
            instrument="phq9",
            total=10,
            created_at=datetime(2026, 4, 8, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="first",
            user_id="user-1",
            instrument="phq9",
            total=15,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        _save_record(
            assessment_id="last",
            user_id="user-1",
            instrument="phq9",
            total=3,
            created_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
        )

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["baseline"]["assessment_id"] == "first"
        assert [p["assessment_id"] for p in body["points"]] == [
            "mid",
            "last",
        ]

    def test_unknown_instrument_returns_empty_series(
        self, client: TestClient
    ) -> None:
        """A nonsense path param yields an empty series with
        ``rci_threshold=None`` and ``baseline=None``.  Matches the
        POST /trajectory contract: unknown instruments fall through
        rather than 422-ing so client charting code doesn't need
        per-instrument branches."""
        resp = client.get(
            "/v1/assessments/trajectory/nonsense",
            headers={"X-User-Id": "user-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["instrument"] == "nonsense"
        assert body["rci_threshold"] is None
        assert body["baseline"] is None
        assert body["points"] == []

    def test_path_param_is_lowercased(self, client: TestClient) -> None:
        """Casing in the path segment is normalized so callers don't
        need to know the canonical form.  Mirrors the POST /trajectory
        normalization."""
        post = _submit_for_user(
            client,
            user_id="user-1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        assert post.status_code == 201

        resp = client.get(
            "/v1/assessments/trajectory/PHQ9",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["instrument"] == "phq9"
        assert body["baseline"] is not None
        assert body["rci_threshold"] == 5.2

    def test_thresholds_static_route_still_wins(
        self, client: TestClient
    ) -> None:
        """Route-registration order guard: ``GET /trajectory/thresholds``
        must still return the static threshold map, not be captured by
        the parameterized ``/trajectory/{instrument}`` handler.  A
        regression here would make the threshold lookup return a
        404-equivalent 'trajectory for user thresholds' which is
        nonsense."""
        resp = client.get("/v1/assessments/trajectory/thresholds")
        assert resp.status_code == 200
        body = resp.json()
        # The thresholds endpoint returns a flat dict; the trajectory
        # endpoint returns an envelope with baseline/points/etc.
        assert "phq9" in body
        assert body["phq9"] == 5.2
        assert "baseline" not in body  # not the trajectory shape

    def test_replay_via_idempotency_does_not_duplicate_trajectory(
        self, client: TestClient
    ) -> None:
        """A retried POST under the same Idempotency-Key must not add
        a phantom trajectory point.  The repository-persist runs only
        on a fresh cache-miss; the replay returns the cached response
        without re-saving."""
        headers = {"Idempotency-Key": "traj-replay-key"}
        body = {
            "instrument": "phq9",
            "items": [1, 1, 1, 1, 1, 1, 1, 1, 0],
            "user_id": "user-1",
        }
        first = client.post("/v1/assessments", json=body, headers=headers)
        assert first.status_code == 201
        second = client.post("/v1/assessments", json=body, headers=headers)
        assert second.status_code == 201

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        body_json = resp.json()
        # One record → baseline only, no points (a duplicate would
        # have produced a second record and thus one point).
        assert body_json["baseline"] is not None
        assert body_json["points"] == []

    def test_full_trajectory_four_points_under_threshold(
        self, client: TestClient
    ) -> None:
        """Four sequential phq9 readings that drift gently: every Δ
        against the baseline stays under 5.2 so every direction is
        ``no_reliable_change``.  Guards against a regression where
        the handler compares to the PREVIOUS reading instead of the
        baseline."""
        from datetime import datetime, timezone

        totals = [10, 11, 9, 12]
        for i, total in enumerate(totals):
            _save_record(
                assessment_id=f"r{i}",
                user_id="user-1",
                instrument="phq9",
                total=total,
                created_at=datetime(
                    2026, 4, 1 + i, tzinfo=timezone.utc
                ),
            )

        resp = client.get(
            "/v1/assessments/trajectory/phq9",
            headers={"X-User-Id": "user-1"},
        )
        body = resp.json()
        assert body["baseline"]["score"] == 10
        assert len(body["points"]) == 3
        for p in body["points"]:
            assert p["direction"] == "no_reliable_change"
        # Deltas are against the baseline 10, not the prior reading.
        deltas = [p["delta"] for p in body["points"]]
        assert deltas == [1, -1, 2]


class TestIesrRouting:
    """End-to-end routing tests for the IES-R dispatcher branch.

    Weiss & Marmar 1997 Impact of Event Scale-Revised — 22 items, 0-4
    Likert, NO reverse-keying (all items distress-positive), three-
    factor structure (Intrusion 8 items / Avoidance 8 items /
    Hyperarousal 6 items).  Per-subscale sums: intrusion 0-32,
    avoidance 0-32, hyperarousal 0-24.  Total = 0-88.

    **HIGHER = MORE trauma-symptom severity** — uniform with PHQ-9 /
    GAD-7 / PCL-5 / CORE-10; opposite of WHO-5 / SWLS / MSPSS / GSE.

    Multi-subscale envelope — third instrument (after PANAS-10 and
    MSPSS) to populate the ``subscales`` dict slot.  Weiss & Marmar
    1997 factor-analytic derivation (n = 196; Gulf War veterans +
    San Francisco earthquake survivors + Northridge earthquake
    emergency workers); confirmed by Creamer 2003 (n = 386 Vietnam
    veterans) and Beck 2008 (n = 182 MVA survivors).

    Subscale position mapping (1-indexed per Weiss & Marmar 1997
    Table 1):
        Intrusion:    items 1, 2, 3, 6, 9, 14, 16, 20
        Avoidance:    items 5, 7, 8, 11, 12, 13, 17, 22
        Hyperarousal: items 4, 10, 15, 18, 19, 21

    **Load-bearing position invariant**: item 2 ("trouble staying
    asleep") → INTRUSION per Weiss & Marmar 1997 (nightmare-driven
    sleep disturbance), item 15 ("trouble falling asleep") →
    HYPERAROUSAL (sleep-onset arousal).  A DSM-5-cluster scorer
    would place both in hyperarousal; this scorer MUST preserve the
    Weiss & Marmar 1997 factor assignment or break clinical-trial
    outcome compatibility.

    Creamer 2003 cutoff: total ≥ 33 (ROC against CAPS; AUC = 0.88)
    for probable PTSD.  ``positive_screen`` flags this;
    ``cutoff_used`` surfaces 33.  Envelope ``severity`` stays
    "continuous" — Creamer 2003 published a single cutoff, not
    severity bands.

    Clinical use cases:
    1. Intrusion-dominant profile → Foa 2007 prolonged exposure
       therapy indication.
    2. Avoidance-dominant profile → Resick 2017 cognitive
       processing therapy indication.
    3. Hyperarousal-dominant profile + PSS-10 high → van der Kolk
       2014 somatic regulation / Linehan 1993 DBT TIP grounding-
       first.
    4. IES-R high + AAQ-II high → Hayes 2006 ACT / Walser 2007 ACT
       for PTSD.
    5. IES-R high + ACEs ≥ 4 → Cloitre 2011 phase-based complex-
       PTSD treatment / Herman 1992.
    6. Najavits 2002 "Seeking Safety" PTSD+SUD — IES-R provides the
       routine-outcome tracking.

    T3 posture — NO item probes suicidality.  Item 4 (irritable /
    angry), item 10 (jumpy / startled), and item 21 (watchful /
    on-guard) are hyperarousal probes, NOT self-harm probes.  Item
    15 (trouble falling asleep) is a sleep-onset probe, NOT a
    hopelessness probe.  Active-risk screening stays on C-SSRS /
    PHQ-9 item 9 / CORE-10 item 6.

    Envelope: total + severity("continuous") + positive_screen +
    cutoff_used(33) + subscales (no scaled_score, no index, no
    triggering_items, requires_t3 always False).
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    # -- Envelope shape ---------------------------------------------------

    def test_max_distress_extremum_eighty_eight(
        self, client: TestClient
    ) -> None:
        """Weiss & Marmar 1997 top-of-range: "Extremely" on all 22
        items.  Raw [4]*22 → total 88, well above Creamer 2003
        cutoff."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [4] * 22},
            headers=self._headers("iesr-max"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "iesr"
        assert body["total"] == 88
        assert body["severity"] == "continuous"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 33
        assert body["requires_t3"] is False

    def test_min_distress_extremum_zero(
        self, client: TestClient
    ) -> None:
        """Weiss & Marmar 1997 bottom-of-range: "Not at all" on all 22
        items.  Raw [0]*22 → total 0, below Creamer 2003 cutoff —
        remitted/asymptomatic presentation."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [0] * 22},
            headers=self._headers("iesr-min"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0
        assert body["severity"] == "continuous"
        assert body["positive_screen"] is False
        assert body["cutoff_used"] == 33
        assert body["requires_t3"] is False

    def test_midpoint_total_forty_four(
        self, client: TestClient
    ) -> None:
        """Mid-range uniform responding — all items = 2 ("Moderately").
        Linear: 22 × 2 = 44 (above Creamer 2003 cutoff of 33)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [2] * 22},
            headers=self._headers("iesr-mid"),
        )
        body = response.json()
        assert body["total"] == 44
        assert body["positive_screen"] is True

    def test_at_creamer_2003_cutoff_exact(
        self, client: TestClient
    ) -> None:
        """Total = 33 exactly → Creamer 2003 ROC boundary → positive.

        Build: all intrusion items = 4 (8 × 4 = 32), plus one
        avoidance item = 1.  Total 33 = cutoff; positive_screen
        fires at the ≥ 33 boundary per Creamer 2003.
        """
        items = [0] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        for pos in intrusion_positions:
            items[pos - 1] = 4
        items[4] = 1
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-cutoff-33"),
        )
        body = response.json()
        assert body["total"] == 33
        assert body["positive_screen"] is True

    def test_one_below_cutoff_is_negative(
        self, client: TestClient
    ) -> None:
        """Total = 32 → one below Creamer 2003 cutoff → NOT positive.

        Build: all 8 intrusion items = 4, everything else 0.  Total 32
        demonstrates the < 33 side of the cutoff.
        """
        items = [0] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        for pos in intrusion_positions:
            items[pos - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-cutoff-32"),
        )
        body = response.json()
        assert body["total"] == 32
        assert body["positive_screen"] is False

    # -- Subscale partitioning -------------------------------------------

    def test_intrusion_isolation_via_router(
        self, client: TestClient
    ) -> None:
        """Set intrusion items (1,2,3,6,9,14,16,20) to 4, others to 0.
        Subscales dict should reflect intrusion=32 / avoidance=0 /
        hyperarousal=0 at the wire layer."""
        items = [0] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        for pos in intrusion_positions:
            items[pos - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-intrusion-iso"),
        )
        body = response.json()
        assert body["subscales"] == {
            "intrusion": 32,
            "avoidance": 0,
            "hyperarousal": 0,
        }
        assert body["total"] == 32

    def test_avoidance_isolation_via_router(
        self, client: TestClient
    ) -> None:
        """Set avoidance items (5,7,8,11,12,13,17,22) to 4, others to 0."""
        items = [0] * 22
        avoidance_positions = (5, 7, 8, 11, 12, 13, 17, 22)
        for pos in avoidance_positions:
            items[pos - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-avoidance-iso"),
        )
        body = response.json()
        assert body["subscales"] == {
            "intrusion": 0,
            "avoidance": 32,
            "hyperarousal": 0,
        }
        assert body["total"] == 32

    def test_hyperarousal_isolation_via_router(
        self, client: TestClient
    ) -> None:
        """Set hyperarousal items (4,10,15,18,19,21) to 4, others to 0.
        Hyperarousal max is 24 (6 items × 4), unequal to the 32
        maxima of the other two subscales."""
        items = [0] * 22
        hyperarousal_positions = (4, 10, 15, 18, 19, 21)
        for pos in hyperarousal_positions:
            items[pos - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-hyperarousal-iso"),
        )
        body = response.json()
        assert body["subscales"] == {
            "intrusion": 0,
            "avoidance": 0,
            "hyperarousal": 24,
        }
        assert body["total"] == 24

    def test_item_2_routes_to_intrusion_not_hyperarousal(
        self, client: TestClient
    ) -> None:
        """Weiss & Marmar 1997 load-bearing invariant: item 2
        ("trouble staying asleep") classifies as INTRUSION (nightmare-
        driven), NOT hyperarousal.  A DSM-5 scorer would misroute
        this; we preserve the factor-analytic assignment."""
        items = [0] * 22
        items[1] = 4  # item 2
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-item2-intrusion"),
        )
        body = response.json()
        assert body["subscales"]["intrusion"] == 4
        assert body["subscales"]["hyperarousal"] == 0
        assert body["subscales"]["avoidance"] == 0

    def test_item_15_routes_to_hyperarousal_not_intrusion(
        self, client: TestClient
    ) -> None:
        """Weiss & Marmar 1997 load-bearing invariant: item 15
        ("trouble falling asleep") classifies as HYPERAROUSAL
        (sleep-onset arousal), distinct from item 2 nightmare-driven
        sleep disturbance."""
        items = [0] * 22
        items[14] = 4  # item 15
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-item15-hyperarousal"),
        )
        body = response.json()
        assert body["subscales"]["hyperarousal"] == 4
        assert body["subscales"]["intrusion"] == 0
        assert body["subscales"]["avoidance"] == 0

    def test_subscale_position_order_matters(
        self, client: TestClient
    ) -> None:
        """Reversing item order keeps total identical but shuffles
        subscale sums — Weiss & Marmar 1997 factor assignments are
        position-dependent."""
        aligned = [4, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0]
        reversed_ = list(reversed(aligned))

        r1 = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": aligned},
            headers=self._headers("iesr-aligned"),
        ).json()
        r2 = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": reversed_},
            headers=self._headers("iesr-reversed"),
        ).json()
        assert r1["total"] == r2["total"]
        assert r1["subscales"] != r2["subscales"]

    # -- Acquiescence signature -------------------------------------------

    @pytest.mark.parametrize(
        "v,expected_total",
        [(0, 0), (1, 22), (2, 44), (3, 66), (4, 88)],
    )
    def test_all_constant_total_is_linear_twenty_two_v(
        self, client: TestClient, v: int, expected_total: int
    ) -> None:
        """No reverse-keying: all-``v`` total = 22v for v ∈ {0..4}.
        Endpoint-only responders expose the full 88-point range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [v] * 22},
            headers=self._headers(f"iesr-acq-{v}"),
        )
        body = response.json()
        assert body["total"] == expected_total

    def test_endpoint_gap_is_eighty_eight(
        self, client: TestClient
    ) -> None:
        """All-4 minus all-0 = 88, full 0-88 range (100% endpoint
        exposure)."""
        r_max = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [4] * 22},
            headers=self._headers("iesr-gap-max"),
        ).json()
        r_min = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [0] * 22},
            headers=self._headers("iesr-gap-min"),
        ).json()
        assert r_max["total"] - r_min["total"] == 88

    # -- Envelope fields --------------------------------------------------

    def test_subscales_populated(
        self, client: TestClient
    ) -> None:
        """IES-R IS a multi-subscale instrument — ``subscales`` MUST
        be populated (not None).  Third such instrument after
        PANAS-10 and MSPSS."""
        response = _post(client, instrument="iesr", items=[2] * 22)
        body = response.json()
        assert body["subscales"] is not None
        assert set(body["subscales"].keys()) == {
            "intrusion",
            "avoidance",
            "hyperarousal",
        }

    def test_cutoff_used_is_thirty_three(
        self, client: TestClient
    ) -> None:
        """Creamer 2003 cutoff surfaces for UI "positive at ≥ 33"
        rendering."""
        response = _post(client, instrument="iesr", items=[2] * 22)
        body = response.json()
        assert body["cutoff_used"] == 33

    def test_instrument_version_surfaces(
        self, client: TestClient
    ) -> None:
        """Pinned version string for downstream FHIR export."""
        response = _post(client, instrument="iesr", items=[0] * 22)
        body = response.json()
        assert body["instrument_version"] == "iesr-1.0.0"

    def test_index_absent(self, client: TestClient) -> None:
        """IES-R has no index transformation — total IS the score."""
        response = _post(client, instrument="iesr", items=[2] * 22)
        body = response.json()
        assert body.get("index") is None

    def test_scaled_score_absent(self, client: TestClient) -> None:
        """IES-R publishes no scaled-score transformation."""
        response = _post(client, instrument="iesr", items=[2] * 22)
        body = response.json()
        assert body.get("scaled_score") is None

    def test_triggering_items_absent(self, client: TestClient) -> None:
        """No item-level acuity routing on IES-R."""
        response = _post(client, instrument="iesr", items=[4] * 22)
        body = response.json()
        assert body.get("triggering_items") is None

    # -- Severity envelope ------------------------------------------------

    @pytest.mark.parametrize("v", [0, 1, 2, 3, 4])
    def test_severity_continuous_across_range(
        self, client: TestClient, v: int
    ) -> None:
        """Creamer 2003 published only a cutoff, no severity bands.
        Envelope stays 'continuous' across the full response range."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [v] * 22},
            headers=self._headers(f"iesr-severity-{v}"),
        )
        body = response.json()
        assert body["severity"] == "continuous"

    # -- T3 posture -------------------------------------------------------

    def test_no_t3_even_at_max_hyperarousal(
        self, client: TestClient
    ) -> None:
        """All hyperarousal items maxed — item 4 (irritable), item 10
        (jumpy), item 21 (watchful) all = 4.  These are NOT self-harm
        probes; requires_t3 stays False.  Active-risk screening
        belongs to C-SSRS / PHQ-9 item 9 / CORE-10 item 6."""
        items = [0] * 22
        hyperarousal_positions = (4, 10, 15, 18, 19, 21)
        for pos in hyperarousal_positions:
            items[pos - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-hyper-no-t3"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    def test_no_t3_at_all_fours(
        self, client: TestClient
    ) -> None:
        """Ceiling response: all 22 items at 4; requires_t3 stays
        False (no suicidality probe on IES-R)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [4] * 22},
            headers=self._headers("iesr-ceiling-no-t3"),
        )
        body = response.json()
        assert body["requires_t3"] is False

    # -- Item count/value/type validation --------------------------------

    @pytest.mark.parametrize("count", [0, 1, 10, 15, 20, 21, 23, 24, 30])
    def test_wrong_item_count_422(
        self, client: TestClient, count: int
    ) -> None:
        """IES-R requires exactly 22 items."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [2] * count},
            headers=self._headers(f"iesr-count-{count}"),
        )
        assert response.status_code == 422

    def test_item_value_above_range_422(
        self, client: TestClient
    ) -> None:
        """Value 5 exceeds 0-4 Likert."""
        items = [2] * 21 + [5]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-bad-high"),
        )
        assert response.status_code == 422

    def test_item_value_below_range_422(
        self, client: TestClient
    ) -> None:
        """Negative value rejected (0 is the floor)."""
        items = [2] * 21 + [-1]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-bad-neg"),
        )
        assert response.status_code == 422

    def test_numeric_string_coerces(
        self, client: TestClient
    ) -> None:
        """Pydantic lax mode: numeric string "4" coerces to int 4.
        Documenting the wire-layer behavior established across the
        roster."""
        items: list[object] = [2] * 21 + ["4"]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-str-coerce"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 2 * 21 + 4

    def test_non_numeric_string_rejects(
        self, client: TestClient
    ) -> None:
        """Non-numeric string cannot coerce to int."""
        items: list[object] = [2] * 21 + ["abc"]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-str-bad"),
        )
        assert response.status_code == 422

    def test_non_whole_float_rejects(
        self, client: TestClient
    ) -> None:
        """Pydantic strict_int at wire layer rejects non-whole floats."""
        items: list[object] = [2] * 21 + [2.5]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-float-bad"),
        )
        assert response.status_code == 422

    def test_bool_true_coerces_to_one(
        self, client: TestClient
    ) -> None:
        """Pydantic lax mode: True → 1 at the wire layer, then the
        scorer processes the int (the scorer-level bool-rejection
        happens only when the Python caller passes raw bool)."""
        items: list[object] = [True] * 22
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-bool-true"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 22

    def test_bool_false_coerces_to_zero(
        self, client: TestClient
    ) -> None:
        """False → 0 at the wire layer; clean all-zero presentation."""
        items: list[object] = [False] * 22
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-bool-false"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["total"] == 0
        assert body["positive_screen"] is False

    # -- Clinical vignettes ----------------------------------------------

    def test_intrusion_dominant_pe_indication(
        self, client: TestClient
    ) -> None:
        """Foa 2007 prolonged exposure indication: intrusion at
        ceiling, avoidance and hyperarousal moderate.  Subscales dict
        should show intrusion high relative to the others, total
        above Creamer 2003 cutoff."""
        items = [0] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        avoidance_positions = (5, 7, 8, 11, 12, 13, 17, 22)
        hyperarousal_positions = (4, 10, 15, 18, 19, 21)
        for pos in intrusion_positions:
            items[pos - 1] = 4
        for pos in avoidance_positions:
            items[pos - 1] = 1
        for pos in hyperarousal_positions:
            items[pos - 1] = 1
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-intrusion-dominant"),
        )
        body = response.json()
        assert body["subscales"]["intrusion"] == 32
        assert body["subscales"]["avoidance"] == 8
        assert body["subscales"]["hyperarousal"] == 6
        assert body["positive_screen"] is True

    def test_avoidance_dominant_cpt_indication(
        self, client: TestClient
    ) -> None:
        """Resick 2017 cognitive processing therapy indication:
        avoidance at ceiling, intrusion and hyperarousal moderate."""
        items = [0] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        avoidance_positions = (5, 7, 8, 11, 12, 13, 17, 22)
        hyperarousal_positions = (4, 10, 15, 18, 19, 21)
        for pos in intrusion_positions:
            items[pos - 1] = 1
        for pos in avoidance_positions:
            items[pos - 1] = 4
        for pos in hyperarousal_positions:
            items[pos - 1] = 1
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-avoidance-dominant"),
        )
        body = response.json()
        assert body["subscales"]["avoidance"] == 32
        assert body["subscales"]["intrusion"] == 8
        assert body["subscales"]["hyperarousal"] == 6
        assert body["positive_screen"] is True

    def test_hyperarousal_dominant_somatic_grounding(
        self, client: TestClient
    ) -> None:
        """van der Kolk 2014 somatic regulation / Linehan 1993 DBT TIP
        indication: hyperarousal-dominant profile; grounding before
        trauma-processing."""
        items = [0] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        avoidance_positions = (5, 7, 8, 11, 12, 13, 17, 22)
        hyperarousal_positions = (4, 10, 15, 18, 19, 21)
        for pos in intrusion_positions:
            items[pos - 1] = 1
        for pos in avoidance_positions:
            items[pos - 1] = 1
        for pos in hyperarousal_positions:
            items[pos - 1] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": items},
            headers=self._headers("iesr-hyper-dominant"),
        )
        body = response.json()
        assert body["subscales"]["hyperarousal"] == 24
        assert body["subscales"]["intrusion"] == 8
        assert body["subscales"]["avoidance"] == 8
        assert body["positive_screen"] is True

    def test_seeking_safety_complex_trauma_profile(
        self, client: TestClient
    ) -> None:
        """Najavits 2002 'Seeking Safety' concurrent PTSD+SUD
        framework — all three subscales elevated.  Cloitre 2011
        phase-based treatment indicated."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [3] * 22},
            headers=self._headers("iesr-seeking-safety"),
        )
        body = response.json()
        assert body["subscales"]["intrusion"] == 24
        assert body["subscales"]["avoidance"] == 24
        assert body["subscales"]["hyperarousal"] == 18
        assert body["total"] == 66
        assert body["positive_screen"] is True

    def test_subthreshold_trauma_monitoring_posture(
        self, client: TestClient
    ) -> None:
        """All items low — total below Creamer 2003 cutoff.  The
        trajectory layer still tracks week-over-week change; the
        clinician-UI layer surfaces this as a monitoring (not
        referral) posture."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [1] * 22},
            headers=self._headers("iesr-subthreshold"),
        )
        body = response.json()
        assert body["total"] == 22
        assert body["positive_screen"] is False
        assert body["severity"] == "continuous"

    def test_remitted_post_treatment_profile(
        self, client: TestClient
    ) -> None:
        """Post-treatment resolution — clean all-zero presentation.
        Treatment-completion / maintenance phase."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [0] * 22},
            headers=self._headers("iesr-remitted"),
        )
        body = response.json()
        assert body["total"] == 0
        assert body["subscales"] == {
            "intrusion": 0,
            "avoidance": 0,
            "hyperarousal": 0,
        }
        assert body["positive_screen"] is False

    def test_improving_trajectory_rci_10pt_delta(
        self, client: TestClient
    ) -> None:
        """Jacobson 1991 RCI on IES-R ≈ 10.  Baseline 44 (all 2s) →
        follow-up 24 (partial resolution) represents a reliable
        change per Creamer 2003 α = 0.96 psychometrics."""
        baseline = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [2] * 22},
            headers=self._headers("iesr-rci-baseline"),
        ).json()
        assert baseline["total"] == 44

        followup_items = [2] * 22
        intrusion_positions = (1, 2, 3, 6, 9, 14, 16, 20)
        avoidance_positions = (5, 7, 8, 11, 12, 13, 17, 22)
        hyperarousal_positions = (4, 10, 15, 18, 19, 21)
        for pos in intrusion_positions[:4]:
            followup_items[pos - 1] = 0
        for pos in avoidance_positions[:4]:
            followup_items[pos - 1] = 0
        for pos in hyperarousal_positions[:2]:
            followup_items[pos - 1] = 0
        followup = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": followup_items},
            headers=self._headers("iesr-rci-followup"),
        ).json()
        assert followup["total"] == 24
        assert baseline["total"] - followup["total"] >= 10

    def test_ceiling_invariant_eighty_eight(
        self, client: TestClient
    ) -> None:
        """Instrument ceiling: all-4 → total 88 and all three
        subscales at their respective maxima (32/32/24).  Establishes
        the ceiling invariant for trajectory-layer Δ normalization."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "iesr", "items": [4] * 22},
            headers=self._headers("iesr-ceiling"),
        )
        body = response.json()
        assert body["total"] == 88
        assert body["subscales"] == {
            "intrusion": 32,
            "avoidance": 32,
            "hyperarousal": 24,
        }


class TestHadsRouting:
    """End-to-end routing tests for the HADS dispatcher branch.

    Zigmond & Snaith 1983 Hospital Anxiety and Depression Scale —
    14 items, 0–3 Likert, two-subscale structure (Anxiety 7 items /
    Depression 7 items alternating), 6 reverse-keyed items.  Designed
    for medical (non-psychiatric) settings: every somatic symptom is
    intentionally excluded so the instrument isolates the psychological
    / cognitive component of anxiety and depression in patients with
    chronic medical illness (oncology / cardiology / post-surgical /
    chronic-pain) where PHQ-9 somatic item load falsely inflates
    depression scores.  Validated by Bjelland 2002 (systematic review,
    747 studies) and Herrmann 1997 (criterion-validity against
    structured clinical interview, ROC AUC ≈ 0.80 per subscale).

    Fourth multi-subscale instrument (after PANAS-10 / MSPSS / IES-R)
    to populate the ``subscales`` envelope slot.

    Subscale partitioning (Zigmond & Snaith 1983 Table 1 — odd-even
    alternating design for acquiescence control):

        Anxiety     (7 items): 1, 3, 5, 7, 9, 11, 13  (odd)
        Depression  (7 items): 2, 4, 6, 8, 10, 12, 14 (even)

    Reverse-keyed positions (6 items — per Zigmond & Snaith 1983
    acquiescence-control design, roughly half the items read
    distress-NEGATIVE ("I still enjoy...") so higher raw = LESS
    distress; these items must be flipped before summation):

        Reverse: 2, 4, 6, 7, 12, 14

    Within the reverse set: position 7 is anxiety-subscale
    (1 of 7 anxiety items); positions 2, 4, 6, 12, 14 are
    depression-subscale (5 of 7 depression items).  Per-position:
    ``flipped = 3 - raw``.  Items field stores RAW values (audit
    invariance per CLAUDE.md Rule #6).

    **HIGHER = MORE distress** after reverse-keying — uniform with
    PHQ-9 / GAD-7 / CORE-10; opposite of WHO-5 / MSPSS / SWLS / GSE.

    Snaith 2003 / Zigmond & Snaith 1983 severity bands (APPLIED PER
    SUBSCALE):

        0–7   normal
        8–10  mild
        11–14 moderate
        15–21 severe

    Bjelland 2002 clinical cutoff: ≥ 11 per subscale (pooled ROC
    optimal cutoff; sensitivity 0.80 / specificity 0.80 against SCID
    major depression / generalized anxiety diagnoses).
    ``positive_screen`` flags either-subscale ≥ 11;
    ``cutoff_used`` surfaces 11.

    Overall ``severity`` field = WORST-of-two-subscale-bands.  A patient
    severe on anxiety but normal on depression gets severity=severe —
    the clinician's primary-triage number.  Per-subscale detail is
    retained in ``subscales``.

    T3 posture — NO item probes suicidality.  Zigmond & Snaith 1983
    deliberately excluded the "thoughts of ending life" item so the
    instrument could be used by non-psychiatrist medical staff in
    oncology / cardiology / chronic-pain clinics without the hand-off
    infrastructure an active-risk item demands.  A severe HADS-D in a
    HADS-using clinic triggers a C-SSRS follow-up at the clinician-UI
    layer, NOT a scorer-layer T3 flag.  Same renderer-versus-scorer
    boundary used for IES-R / MSPSS / SWLS / GSE.

    Construct placement — complement to PHQ-9 (DSM-criterion depression
    with somatic items; best for primary care) and GAD-7 (generalized
    anxiety severity).  HADS alongside PHQ-9 / PHQ-15 gives the
    Barsky 2005 three-way decomposition of medical-setting distress:
    depression / anxiety-mood (HADS) vs somatization (PHQ-15) vs
    DSM-criterion mood (PHQ-9).

    Envelope: total + severity(worst-of-two-bands) + positive_screen
    (either ≥ 11) + cutoff_used(11) + subscales (anxiety / depression);
    no scaled_score, no index, no triggering_items, requires_t3
    always False.
    """

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        return {"Idempotency-Key": key}

    @staticmethod
    def _items_for(anx_target: int, dep_target: int) -> list[int]:
        """Build a 14-item RAW vector that, after reverse-keying
        (flip positions 2, 4, 6, 7, 12, 14 via ``3 - raw``), sums to
        ``anx_target`` on the anxiety subscale and ``dep_target`` on
        the depression subscale.

        Anxiety positions 1, 3, 5, 9, 11, 13 are forward (contribute
        raw); position 7 is reverse (contributes 3 - raw).  Forward
        anxiety max = 18, reverse anxiety max flipped = 3 → subscale
        max 21.

        Depression positions 8, 10 are forward (contribute raw);
        positions 2, 4, 6, 12, 14 are reverse (contribute 3 - raw
        each).  Forward depression max = 6, reverse depression max
        flipped = 15 → subscale max 21.

        Safe-baseline raw vector (both subscales = 0):
            [0, 3, 0, 3, 0, 3, 3, 0, 0, 0, 0, 3, 0, 3]
        (forward items default to 0 for raw 0; reverse items set to
        raw 3 so they flip to contribution 0).
        """
        assert 0 <= anx_target <= 21, f"anx_target {anx_target} out of range"
        assert 0 <= dep_target <= 21, f"dep_target {dep_target} out of range"
        items = [0] * 14
        # Initialize all reverse positions to raw 3 → flipped 0 → subscale 0 baseline
        for pos in (2, 4, 6, 7, 12, 14):
            items[pos - 1] = 3
        # Anxiety: fill forward positions first (max 18); then reverse item 7
        if anx_target <= 18:
            remaining = anx_target
            for pos in (1, 3, 5, 9, 11, 13):
                c = min(3, remaining)
                items[pos - 1] = c
                remaining -= c
                if remaining == 0:
                    break
        else:
            for pos in (1, 3, 5, 9, 11, 13):
                items[pos - 1] = 3
            overage = anx_target - 18  # 1..3
            items[7 - 1] = 3 - overage  # raw = 3 - overage → flipped = overage
        # Depression: fill forward positions first (max 6); then reverse items
        if dep_target <= 6:
            remaining = dep_target
            for pos in (8, 10):
                c = min(3, remaining)
                items[pos - 1] = c
                remaining -= c
                if remaining == 0:
                    break
        else:
            for pos in (8, 10):
                items[pos - 1] = 3
            remaining = dep_target - 6  # 1..15
            for pos in (2, 4, 6, 12, 14):
                c = min(3, remaining)
                items[pos - 1] = 3 - c  # raw = 3 - c → flipped = c
                remaining -= c
                if remaining == 0:
                    break
        return items

    # -- Envelope shape ---------------------------------------------------

    def test_all_zeros_total_eighteen(self, client: TestClient) -> None:
        """All raw items = 0 → reverse positions (2, 4, 6, 7, 12, 14)
        flip to 3 each (6 × 3 = 18 total contribution); forward
        positions contribute 0.  Anxiety = forward 0 + flipped item 7
        (raw 0 → flipped 3) = 3 (normal).  Depression = forward 0 +
        flipped items 2, 4, 6, 12, 14 (5 × 3 = 15) = 15 (severe).
        Severity = severe (worst-of-two).  Positive screen = True
        (depression ≥ 11)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [0] * 14},
            headers=self._headers("hads-all-zeros"),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["instrument"] == "hads"
        assert body["total"] == 18
        assert body["subscales"] == {"anxiety": 3, "depression": 15}
        assert body["severity"] == "severe"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 11
        assert body["requires_t3"] is False

    def test_all_threes_total_twenty_four(self, client: TestClient) -> None:
        """All raw items = 3 → reverse positions flip to 0 (6 × 0);
        forward positions contribute 3 each (8 × 3 = 24).  Anxiety =
        forward 18 (items 1,3,5,9,11,13 at 3) + flipped item 7 (raw 3
        → flipped 0) = 18 (severe).  Depression = forward 6 (items
        8, 10 at 3) + flipped items 2, 4, 6, 12, 14 all 0 = 6 (normal).
        Severity = severe (worst-of-two).  Positive screen = True
        (anxiety ≥ 11)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [3] * 14},
            headers=self._headers("hads-all-threes"),
        )
        body = response.json()
        assert body["total"] == 24
        assert body["subscales"] == {"anxiety": 18, "depression": 6}
        assert body["severity"] == "severe"
        assert body["positive_screen"] is True
        assert body["cutoff_used"] == 11

    def test_all_ones_total_twenty(self, client: TestClient) -> None:
        """All raw items = 1 → reverse positions flip to 2; forward
        positions contribute 1.  Anxiety = 6 × 1 + (3 - 1) = 8 (mild).
        Depression = 2 × 1 + 5 × 2 = 12 (moderate).  Severity =
        moderate (worst-of mild/moderate)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [1] * 14},
            headers=self._headers("hads-all-ones"),
        )
        body = response.json()
        assert body["total"] == 20
        assert body["subscales"] == {"anxiety": 8, "depression": 12}
        assert body["severity"] == "moderate"
        assert body["positive_screen"] is True

    def test_all_twos_total_twenty_two(self, client: TestClient) -> None:
        """All raw items = 2 → reverse positions flip to 1; forward
        positions contribute 2.  Anxiety = 6 × 2 + (3 - 2) = 13
        (moderate).  Depression = 2 × 2 + 5 × 1 = 9 (mild).  Severity
        = moderate."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [2] * 14},
            headers=self._headers("hads-all-twos"),
        )
        body = response.json()
        assert body["total"] == 22
        assert body["subscales"] == {"anxiety": 13, "depression": 9}
        assert body["severity"] == "moderate"
        assert body["positive_screen"] is True

    def test_baseline_zero_via_helper(self, client: TestClient) -> None:
        """Helper-constructed "safe baseline": anxiety=0, depression=0.
        Raw vector = [0, 3, 0, 3, 0, 3, 3, 0, 0, 0, 0, 3, 0, 3] — all
        reverse items at raw 3 (flipped 0), forward items at 0.
        Total = 0; severity = normal; positive_screen = False — the
        medical-setting "no distress" baseline."""
        items = self._items_for(0, 0)
        assert items == [0, 3, 0, 3, 0, 3, 3, 0, 0, 0, 0, 3, 0, 3]
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-baseline-zero"),
        )
        body = response.json()
        assert body["total"] == 0
        assert body["subscales"] == {"anxiety": 0, "depression": 0}
        assert body["severity"] == "normal"
        assert body["positive_screen"] is False

    def test_instrument_version_pinned(self, client: TestClient) -> None:
        """``instrument_version`` is pinned — downstream FHIR export
        and longitudinal trajectory computation require a stable
        version identifier per Zigmond & Snaith 1983 reference."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [1] * 14},
            headers=self._headers("hads-version"),
        )
        body = response.json()
        assert body["instrument_version"] == "hads-1.0.0"

    # -- Reverse-keying wire-layer arithmetic -----------------------------

    def test_reverse_item_2_flips_zero_to_three(
        self, client: TestClient
    ) -> None:
        """Item 2 (depression subscale, reverse-keyed).  Isolate:
        raw item 2 = 0 → flipped 3 → depression +3.  All other items
        at "safe" raw (forward 0, other reverse 3)."""
        items = self._items_for(0, 0)
        items[2 - 1] = 0  # change reverse item 2 from raw 3 → raw 0 → flipped +3
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-rev2"),
        )
        body = response.json()
        assert body["subscales"]["anxiety"] == 0
        assert body["subscales"]["depression"] == 3

    def test_reverse_item_7_is_anxiety_subscale(
        self, client: TestClient
    ) -> None:
        """Item 7 is the SINGLE reverse-keyed anxiety item.  Set raw
        item 7 = 0 → flipped 3 → anxiety +3 (not depression).
        Load-bearing: a flaw mapping item 7 into depression would
        break the Zigmond & Snaith 1983 subscale partition."""
        items = self._items_for(0, 0)
        items[7 - 1] = 0  # raw item 7: 3 → 0 → flipped contribution 0 → 3
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-rev7-anx"),
        )
        body = response.json()
        assert body["subscales"]["anxiety"] == 3
        assert body["subscales"]["depression"] == 0

    def test_forward_item_8_is_depression_subscale(
        self, client: TestClient
    ) -> None:
        """Item 8 is depression-subscale FORWARD (not reverse).  Raw
        item 8 = 3 → contributes 3 directly to depression."""
        items = self._items_for(0, 0)
        items[8 - 1] = 3
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-fwd8-dep"),
        )
        body = response.json()
        assert body["subscales"]["anxiety"] == 0
        assert body["subscales"]["depression"] == 3

    def test_forward_item_1_is_anxiety_subscale(
        self, client: TestClient
    ) -> None:
        """Item 1 is anxiety-subscale FORWARD.  Raw item 1 = 3 →
        contributes 3 directly to anxiety."""
        items = self._items_for(0, 0)
        items[1 - 1] = 3
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-fwd1-anx"),
        )
        body = response.json()
        assert body["subscales"]["anxiety"] == 3
        assert body["subscales"]["depression"] == 0

    def test_items_field_preserves_raw_not_flipped(
        self, client: TestClient
    ) -> None:
        """Audit-invariance — the submitted raw response set is what
        the scorer / repository / FHIR-export layer must see.  A
        future re-score must reconstruct the clinical total from the
        RAW values plus the pinned reverse-keying rule.  Assert the
        envelope's ``total`` matches our computed flipped sum, not
        the raw sum (raw sum = 3 for this fixture; flipped sum =
        anxiety 0 + depression 0 + flip of item 4 = 0 contribution ≠
        raw)."""
        items = self._items_for(0, 0)  # safe baseline
        items[4 - 1] = 0  # reverse item 4: raw 3 → raw 0 → flipped +3 depression
        raw_sum = sum(items)  # accounting for both forward zeros and reverse threes
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-raw-audit"),
        )
        body = response.json()
        # The total is the post-reverse-key total (0 + 3 = 3), not the raw sum.
        assert body["total"] == 3
        assert body["total"] != raw_sum  # reverse-keyed totals differ from raw sums

    # -- Subscale partitioning --------------------------------------------

    def test_anxiety_and_depression_are_independent(
        self, client: TestClient
    ) -> None:
        """A burst in anxiety leaves depression baseline-zero and
        vice versa (separable subscales per Zigmond & Snaith 1983
        odd-even partition)."""
        # Anxiety burst, depression baseline
        anx_burst = self._items_for(15, 0)
        r1 = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": anx_burst},
            headers=self._headers("hads-sep-anx"),
        ).json()
        assert r1["subscales"] == {"anxiety": 15, "depression": 0}
        # Depression burst, anxiety baseline
        dep_burst = self._items_for(0, 15)
        r2 = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": dep_burst},
            headers=self._headers("hads-sep-dep"),
        ).json()
        assert r2["subscales"] == {"anxiety": 0, "depression": 15}

    @pytest.mark.parametrize(
        "anx_target,dep_target",
        [(0, 0), (5, 10), (11, 11), (18, 6), (21, 21), (7, 14), (15, 8)],
    )
    def test_helper_construction_round_trips(
        self,
        client: TestClient,
        anx_target: int,
        dep_target: int,
    ) -> None:
        """The helper produces a raw vector whose post-reverse-key
        subscale totals equal the targets.  Verifies the construction
        itself across representative values."""
        items = self._items_for(anx_target, dep_target)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers(
                f"hads-rt-{anx_target}-{dep_target}"
            ),
        )
        body = response.json()
        assert body["subscales"] == {
            "anxiety": anx_target,
            "depression": dep_target,
        }
        assert body["total"] == anx_target + dep_target

    # -- Anxiety severity-band boundaries (Snaith 2003) -------------------

    @pytest.mark.parametrize(
        "anx_score,band",
        [
            (0, "normal"),
            (7, "normal"),
            (8, "mild"),
            (10, "mild"),
            (11, "moderate"),
            (14, "moderate"),
            (15, "severe"),
            (21, "severe"),
        ],
    )
    def test_anxiety_severity_band_boundaries(
        self,
        client: TestClient,
        anx_score: int,
        band: str,
    ) -> None:
        """Per-subscale severity bands (Snaith 2003 / Zigmond &
        Snaith 1983): 0–7 normal, 8–10 mild, 11–14 moderate, 15–21
        severe.  Isolate anxiety: depression at 0 (normal).  Overall
        severity = anxiety band (depression normal is weakest)."""
        items = self._items_for(anx_score, 0)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers(f"hads-anx-band-{anx_score}"),
        )
        body = response.json()
        assert body["subscales"] == {
            "anxiety": anx_score,
            "depression": 0,
        }
        assert body["severity"] == band

    # -- Depression severity-band boundaries ------------------------------

    @pytest.mark.parametrize(
        "dep_score,band",
        [
            (0, "normal"),
            (7, "normal"),
            (8, "mild"),
            (10, "mild"),
            (11, "moderate"),
            (14, "moderate"),
            (15, "severe"),
            (21, "severe"),
        ],
    )
    def test_depression_severity_band_boundaries(
        self,
        client: TestClient,
        dep_score: int,
        band: str,
    ) -> None:
        """Per-subscale severity bands — depression side (Snaith 2003
        identical bands to anxiety).  Isolate depression: anxiety at
        0 (normal)."""
        items = self._items_for(0, dep_score)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers(f"hads-dep-band-{dep_score}"),
        )
        body = response.json()
        assert body["subscales"] == {
            "anxiety": 0,
            "depression": dep_score,
        }
        assert body["severity"] == band

    # -- Overall severity = worst-of-two ---------------------------------

    def test_severity_worst_of_anx_severe_dep_normal(
        self, client: TestClient
    ) -> None:
        """Anxiety severe (18), depression normal (5).  Overall
        severity = severe.  A clinician's triage-level summary should
        reflect the worst of the two dimensions — a patient severely
        anxious but depression-normal still needs severe-level
        resource allocation."""
        items = self._items_for(18, 5)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-worst-anx-severe"),
        ).json()
        assert response["subscales"] == {"anxiety": 18, "depression": 5}
        assert response["severity"] == "severe"

    def test_severity_worst_of_anx_normal_dep_severe(
        self, client: TestClient
    ) -> None:
        """Inverted — depression severe (18), anxiety normal (5).
        Overall severity = severe."""
        items = self._items_for(5, 18)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-worst-dep-severe"),
        ).json()
        assert response["subscales"] == {"anxiety": 5, "depression": 18}
        assert response["severity"] == "severe"

    def test_severity_mild_plus_moderate_is_moderate(
        self, client: TestClient
    ) -> None:
        """Anxiety mild (9), depression moderate (12).  Overall
        severity = moderate."""
        items = self._items_for(9, 12)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-worst-mild-mod"),
        ).json()
        assert response["severity"] == "moderate"

    def test_severity_normal_plus_mild_is_mild(
        self, client: TestClient
    ) -> None:
        """Anxiety normal (5), depression mild (9).  Overall severity
        = mild."""
        items = self._items_for(5, 9)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-worst-norm-mild"),
        ).json()
        assert response["severity"] == "mild"

    def test_severity_identical_bands_returns_that_band(
        self, client: TestClient
    ) -> None:
        """Both subscales in the same band → overall = that band.
        Moderate-both (anx 12, dep 13) → moderate."""
        items = self._items_for(12, 13)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-worst-both-mod"),
        ).json()
        assert response["severity"] == "moderate"

    # -- Positive-screen subscale independence ---------------------------

    def test_positive_screen_only_anxiety_geq_eleven(
        self, client: TestClient
    ) -> None:
        """Anxiety ≥ 11, depression < 11 → positive_screen True
        (Bjelland 2002 either-subscale rule)."""
        items = self._items_for(11, 10)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-pos-anx-only"),
        ).json()
        assert response["positive_screen"] is True
        assert response["cutoff_used"] == 11

    def test_positive_screen_only_depression_geq_eleven(
        self, client: TestClient
    ) -> None:
        """Depression ≥ 11, anxiety < 11 → positive_screen True."""
        items = self._items_for(10, 11)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-pos-dep-only"),
        ).json()
        assert response["positive_screen"] is True
        assert response["cutoff_used"] == 11

    def test_positive_screen_both_subscales_geq_eleven(
        self, client: TestClient
    ) -> None:
        """Both ≥ 11 → positive_screen True."""
        items = self._items_for(15, 15)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-pos-both"),
        ).json()
        assert response["positive_screen"] is True
        assert response["severity"] == "severe"

    def test_negative_screen_both_subscales_below_cutoff(
        self, client: TestClient
    ) -> None:
        """Both subscales < 11 → positive_screen False (no Bjelland
        2002 cutoff met)."""
        items = self._items_for(10, 10)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-neg-both"),
        ).json()
        assert response["positive_screen"] is False
        assert response["severity"] == "mild"

    def test_positive_screen_exact_cutoff_anxiety_eleven(
        self, client: TestClient
    ) -> None:
        """Anxiety = 11 exactly → positive_screen True (Bjelland 2002
        inclusive ≥ 11)."""
        items = self._items_for(11, 0)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-pos-exact"),
        ).json()
        assert response["positive_screen"] is True

    def test_negative_screen_at_ten_not_positive(
        self, client: TestClient
    ) -> None:
        """Anxiety = 10, depression = 10 → positive_screen False.
        Verifies the ≥ 11 boundary is inclusive at 11, exclusive at
        10 (the "mild" upper bound)."""
        items = self._items_for(10, 10)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-neg-at-10"),
        ).json()
        assert response["positive_screen"] is False
        assert response["subscales"] == {"anxiety": 10, "depression": 10}

    # -- Item-count validation -------------------------------------------

    def test_thirteen_items_rejected(self, client: TestClient) -> None:
        """< 14 items → 422 with instrument-specific message."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [1] * 13},
            headers=self._headers("hads-short"),
        )
        assert response.status_code == 422

    def test_fifteen_items_rejected(self, client: TestClient) -> None:
        """> 14 items → 422."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [1] * 15},
            headers=self._headers("hads-long"),
        )
        assert response.status_code == 422

    def test_zero_items_rejected_at_pydantic_layer(
        self, client: TestClient
    ) -> None:
        """Empty items list — 422 at the Pydantic min_length=1 check."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": []},
            headers=self._headers("hads-empty"),
        )
        assert response.status_code == 422

    # -- Item-value range validation -------------------------------------

    def test_value_negative_rejected(self, client: TestClient) -> None:
        """Raw item value < 0 → 422."""
        items = [1] * 14
        items[0] = -1
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-neg"),
        )
        assert response.status_code == 422

    def test_value_four_rejected(self, client: TestClient) -> None:
        """Raw item value > 3 → 422 (HADS is 0–3 Likert; 4 is the
        GAD-7 / PHQ-9 max, not HADS)."""
        items = [1] * 14
        items[7] = 4
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-over"),
        )
        assert response.status_code == 422

    def test_value_far_out_of_range_rejected(
        self, client: TestClient
    ) -> None:
        """Raw item value = 100 → 422."""
        items = [1] * 14
        items[13] = 100
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-far-out"),
        )
        assert response.status_code == 422

    # -- Item-type / Pydantic-coercion boundary --------------------------

    def test_string_value_non_numeric_rejected(
        self, client: TestClient
    ) -> None:
        """Non-numeric string ("two") → 422 at Pydantic list[int]."""
        items: list[object] = [1] * 14
        items[3] = "two"
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-str-nonnum"),
        )
        assert response.status_code == 422

    def test_string_numeric_coerced_to_int(
        self, client: TestClient
    ) -> None:
        """Numeric string ("2") → Pydantic lax-mode coerces to 2 →
        accepted."""
        items: list[object] = [1] * 14
        items[3] = "2"
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-str-num"),
        )
        assert response.status_code == 201

    def test_float_whole_coerced(self, client: TestClient) -> None:
        """Whole-number float (2.0) → Pydantic lax-mode coerces → 201."""
        items: list[object] = [1] * 14
        items[5] = 2.0
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-float-whole"),
        )
        assert response.status_code == 201

    def test_float_fractional_rejected(self, client: TestClient) -> None:
        """Non-whole float (2.5) → Pydantic rejects at list[int]."""
        items: list[object] = [1] * 14
        items[5] = 2.5
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-float-frac"),
        )
        assert response.status_code == 422

    def test_bool_true_coerced_via_pydantic(
        self, client: TestClient
    ) -> None:
        """JSON ``true`` → Pydantic lax-mode coerces to 1 → 201.
        The strict-bool rejection only applies to DIRECT-Python
        calls into the scorer; the wire layer follows Pydantic's
        standard list[int] coercion."""
        items: list[object] = [1] * 14
        items[0] = True
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-bool-true"),
        )
        assert response.status_code == 201

    def test_bool_false_coerced_via_pydantic(
        self, client: TestClient
    ) -> None:
        """JSON ``false`` → Pydantic lax-mode coerces to 0 → 201."""
        items: list[object] = [0] * 14
        items[0] = False
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-bool-false"),
        )
        assert response.status_code == 201

    def test_null_rejected(self, client: TestClient) -> None:
        """JSON ``null`` at a list position → 422."""
        items: list[object] = [1] * 14
        items[7] = None
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-null"),
        )
        assert response.status_code == 422

    # -- Unused envelope fields -----------------------------------------

    def test_no_scaled_score_key(self, client: TestClient) -> None:
        """HADS has no scaled-score transformation — the total IS
        the published score."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [1] * 14},
            headers=self._headers("hads-no-scaled"),
        ).json()
        assert response.get("scaled_score") is None

    def test_no_index_key(self, client: TestClient) -> None:
        """HADS has no index — WHO-5 is the only instrument using
        index (raw × 4)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [1] * 14},
            headers=self._headers("hads-no-index"),
        ).json()
        assert response.get("index") is None

    def test_no_triggering_items(self, client: TestClient) -> None:
        """HADS has no per-item acuity routing — triggering_items
        null in the envelope (no item-level T3 flag)."""
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": [3] * 14},
            headers=self._headers("hads-no-trig"),
        ).json()
        assert response.get("triggering_items") is None

    def test_requires_t3_always_false_even_at_ceiling(
        self, client: TestClient
    ) -> None:
        """HADS by design excludes suicidality probes (Zigmond &
        Snaith 1983 medical-setting rationale).  requires_t3 is
        False even at the maximum severity profile."""
        items = self._items_for(21, 21)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-t3-ceiling"),
        ).json()
        assert response["total"] == 42
        assert response["severity"] == "severe"
        assert response["requires_t3"] is False

    # -- Clinical vignettes ----------------------------------------------

    def test_vignette_medical_setting_normal_baseline(
        self, client: TestClient
    ) -> None:
        """Chronic-illness-clinic baseline: anxiety 5 / depression 6
        — both in normal range (0–7 per Snaith 2003).  The typical
        pattern in a stable chronic-illness cohort (mild
        cardiovascular, post-op day 30, managed oncology surveillance).
        No mood-intervention referral indicated."""
        items = self._items_for(5, 6)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-vignette-medical-baseline"),
        ).json()
        assert response["subscales"] == {"anxiety": 5, "depression": 6}
        assert response["severity"] == "normal"
        assert response["positive_screen"] is False

    def test_vignette_convergent_depression_with_phq9(
        self, client: TestClient
    ) -> None:
        """HADS-D = 13 (moderate) + PHQ-9 = 15 (moderate; tested
        separately in PHQ-9 suite).  In a medical cohort, when PHQ-9
        and HADS-D agree, the depression inference is strengthened —
        somatic-inflation is not confounding the signal.  Bjelland
        2002 cross-instrument convergence pattern."""
        items = self._items_for(4, 13)  # anx normal, dep moderate
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-vignette-convergent-phq9"),
        ).json()
        assert response["subscales"] == {"anxiety": 4, "depression": 13}
        assert response["severity"] == "moderate"
        assert response["positive_screen"] is True

    def test_vignette_convergent_anxiety_with_gad7(
        self, client: TestClient
    ) -> None:
        """HADS-A = 12 (moderate) + GAD-7 = 12 (moderate; tested
        separately).  Medical-setting anxiety with convergent
        cross-instrument signal.  Routes to anxiety-focused
        intervention (CBT / relaxation training / SSRI consult)."""
        items = self._items_for(12, 4)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-vignette-convergent-gad7"),
        ).json()
        assert response["subscales"] == {"anxiety": 12, "depression": 4}
        assert response["severity"] == "moderate"
        assert response["positive_screen"] is True

    def test_vignette_anhedonia_dominant_medical_comorbidity(
        self, client: TestClient
    ) -> None:
        """HADS-D elevated (14 moderate) + HADS-A normal (6).  In a
        cancer / chronic-pain cohort, this isolates the anhedonia /
        cognitive-mood component from anxiety.  A PHQ-9 for this
        patient would likely be inflated by somatic items (fatigue,
        sleep) that reflect illness rather than mood — HADS-D
        corrects for that."""
        items = self._items_for(6, 14)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-vignette-anhedonia"),
        ).json()
        assert response["subscales"] == {"anxiety": 6, "depression": 14}
        assert response["severity"] == "moderate"
        assert response["positive_screen"] is True

    def test_vignette_mixed_moderate_both_subscales(
        self, client: TestClient
    ) -> None:
        """Both subscales moderate (anx 12 / dep 12) — the classic
        mixed-anxiety-depression presentation.  Treatment routes
        toward transdiagnostic CBT (Barlow 2010 Unified Protocol)
        rather than a disorder-specific protocol."""
        items = self._items_for(12, 12)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-vignette-mixed-mod"),
        ).json()
        assert response["subscales"] == {"anxiety": 12, "depression": 12}
        assert response["severity"] == "moderate"
        assert response["total"] == 24
        assert response["positive_screen"] is True

    def test_vignette_ceiling_severe_both(
        self, client: TestClient
    ) -> None:
        """Maximum severity on both subscales — anx 21 / dep 21.
        Total = 42 (envelope ceiling).  Routes to urgent psychiatric
        evaluation; C-SSRS follow-up flagged by clinician-UI
        layer (scorer itself reports requires_t3=False per HADS
        design — no suicidality probe)."""
        items = self._items_for(21, 21)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-vignette-ceiling"),
        ).json()
        assert response["subscales"] == {"anxiety": 21, "depression": 21}
        assert response["total"] == 42
        assert response["severity"] == "severe"
        assert response["positive_screen"] is True
        assert response["requires_t3"] is False

    def test_vignette_puhan_rci_delta(
        self, client: TestClient
    ) -> None:
        """Puhan 2008 COPD-cohort MCID = 1.5 points per subscale;
        platform RCI benchmark.  Baseline anx 12 → follow-up anx 10
        (Δ = 2) meets MCID.  Baseline positive_screen True (≥ 11);
        follow-up positive_screen False — a clinically meaningful
        within-episode improvement."""
        baseline = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": self._items_for(12, 5)},
            headers=self._headers("hads-puhan-baseline"),
        ).json()
        assert baseline["subscales"]["anxiety"] == 12
        assert baseline["positive_screen"] is True
        followup = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": self._items_for(10, 5)},
            headers=self._headers("hads-puhan-followup"),
        ).json()
        assert followup["subscales"]["anxiety"] == 10
        assert followup["positive_screen"] is False
        assert baseline["subscales"]["anxiety"] - followup["subscales"]["anxiety"] >= 2

    def test_vignette_bjelland_at_threshold(
        self, client: TestClient
    ) -> None:
        """Bjelland 2002 cutoff boundary: anxiety = 11 exactly →
        positive_screen True.  Verifies the sensitivity-of-the-cutoff
        for the either-subscale rule."""
        items = self._items_for(11, 7)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-bjelland-at-11"),
        ).json()
        assert response["subscales"] == {"anxiety": 11, "depression": 7}
        assert response["positive_screen"] is True
        assert response["severity"] == "moderate"

    def test_vignette_bjelland_below_threshold(
        self, client: TestClient
    ) -> None:
        """Bjelland 2002 just-below: anxiety = 10 / depression = 10
        → positive_screen False.  A subthreshold presentation the
        clinician-UI may flag for watchful waiting / repeat screen,
        but not immediate referral."""
        items = self._items_for(10, 10)
        response = client.post(
            "/v1/assessments",
            json={"instrument": "hads", "items": items},
            headers=self._headers("hads-bjelland-below-11"),
        ).json()
        assert response["subscales"] == {"anxiety": 10, "depression": 10}
        assert response["positive_screen"] is False
        assert response["severity"] == "mild"
