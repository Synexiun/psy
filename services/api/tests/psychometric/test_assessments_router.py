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

from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


# ---- Fixtures --------------------------------------------------------------


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
    body: dict[str, Any] = {"instrument": instrument, "items": items}
    if sex is not None:
        body["sex"] = sex
    h = {"Idempotency-Key": "test-key-abc"}
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
        # Each carries a distinct assessment_id — the idempotency key
        # isn't yet repository-backed, so unique assessment_ids are the
        # correlation anchor.
        assert (
            captured[0]["assessment_id"] != captured[1]["assessment_id"]
        )
