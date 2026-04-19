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
