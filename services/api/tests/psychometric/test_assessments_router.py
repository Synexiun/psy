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
