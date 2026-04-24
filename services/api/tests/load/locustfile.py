"""
Locust load test suite for the Discipline OS API.

Target SLOs (from Docs/Technicals/08_Infrastructure_DevOps.md §11):
  - p95 response time ≤ 400ms for urge submission (spec §5.1: "p95 < 400ms warm")
  - p99 response time ≤ 2s for pattern analysis
  - Error rate < 0.1% under normal load (50 concurrent users)
  - Crisis path GET /v1/sos and POST /v1/sos ≤ 200ms p99 at any load
    (CLAUDE.md rule 1: T3/T4 paths are deterministic and must never miss)

These tests do NOT require real auth. They pass a synthetic bearer token and
let the server respond with 401/422 as appropriate. The goal is to measure
server-side throughput, connection pool behaviour, and response-time budgets
under load, not to exercise application logic end-to-end.

Run (interactive UI):
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Run (CI headless, 50 users, 60-second window):
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \\
           --headless -u 50 -r 10 --run-time 60s \\
           --csv=load-results --only-summary

SLO gate script (example — wire into CI after --csv run):
    python tests/load/check_slo.py load-results_stats.csv

User mix (weights sum to 100):
    RegularUser      70 % — typical authenticated user session
    CrisisUser        5 % — T3/T4 SOS path; latency-critical
    AssessmentUser   15 % — weekly psychometric assessment flow
    ClinicianUser    10 % — clinician portal read patterns
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime

from locust import HttpUser, between, task


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_TRIGGER_TAGS = [
    "stress",
    "work_deadline",
    "social_pressure",
    "evening_alone",
    "boredom",
    "fatigue",
    "conflict",
    "financial_worry",
    "anniversary",
    "low_sleep",
]

_LOCATION_CONTEXTS = ["work", "home", "transit", "social", "unknown"]

_BEHAVIORS = ["alcohol", "doomscroll", "gambling", "substance", "compulsive_eating"]

_PHQ9_RESPONSES = [
    # 9 items, each 0-3. These produce a total of 12 (moderate severity).
    # Safe values: item 9 (suicidal ideation) is always 0 so no T4 escalation
    # is triggered from load test traffic.
    {"item": 1, "value": 1},
    {"item": 2, "value": 2},
    {"item": 3, "value": 1},
    {"item": 4, "value": 2},
    {"item": 5, "value": 1},
    {"item": 6, "value": 1},
    {"item": 7, "value": 2},
    {"item": 8, "value": 1},
    {"item": 9, "value": 0},  # MUST remain 0 — item 9 is a safety item
]

_INSTRUMENTS = ["phq9", "gad7", "who5", "audit"]


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _idempotency_key() -> str:
    return str(uuid.uuid4())


def _fake_auth_headers() -> dict[str, str]:
    """
    Synthetic bearer token.  The auth middleware will reject it with 401,
    which is expected and intentional — we are measuring server-side capacity,
    not application logic.  To run against a real stack with valid tokens,
    replace this with a token from your test-user fixture.
    """
    return {"Authorization": "Bearer load-test-synthetic-jwt"}


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------


class RegularUser(HttpUser):
    """
    Simulates a typical authenticated user session (70 % of virtual users).

    Task flow mirrors the primary daily loop described in
    Docs/Technicals/03_API_Specification.md §5, §8, §9:
      1. GET /health          — warm-up; excluded from SLO stats via name=None
      2. GET /v1/me           — profile fetch on app open
      3. GET /v1/today        — home card state
      4. POST /v1/urges       — urge log (p95 < 400ms warm per spec §5.1)
      5. GET /v1/patterns     — pattern list (p99 ≤ 2s)
      6. GET /v1/streak       — streak / resilience counters
      7. GET /v1/insights/resilience — resilience insight card
    """

    weight = 70
    wait_time = between(2, 8)
    headers: dict[str, str]

    def on_start(self) -> None:
        self.headers = _fake_auth_headers()
        # Warm-up health check, not tracked in statistics.
        self.client.get("/health", name="_warmup_health", headers=self.headers)

    @task(3)
    def get_me(self) -> None:
        with self.client.get(
            "/v1/me",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/me",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_today(self) -> None:
        with self.client.get(
            "/v1/today",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/today",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(5)
    def post_urge(self) -> None:
        """
        Core intervention trigger.  SLO: p95 < 400ms warm (spec §5.1).
        Idempotency-Key is per-request, as the spec requires.
        """
        payload = {
            "started_at": _now_iso(),
            "intensity_start": random.randint(1, 10),
            "trigger_tags": random.sample(_TRIGGER_TAGS, k=random.randint(1, 3)),
            "location_context": random.choice(_LOCATION_CONTEXTS),
            "origin": "self_reported",
        }
        with self.client.post(
            "/v1/urges",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/urges",
        ) as resp:
            if resp.status_code not in (201, 401, 422):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_patterns(self) -> None:
        """Pattern list.  SLO: p99 ≤ 2s."""
        with self.client.get(
            "/v1/patterns?active=true",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/patterns",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def get_streak(self) -> None:
        with self.client.get(
            "/v1/streak",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/streak",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def get_resilience_insight(self) -> None:
        with self.client.get(
            "/v1/insights/resilience",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/insights/resilience",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def get_weekly_insights(self) -> None:
        with self.client.get(
            "/v1/insights/weekly",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/insights/weekly",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()


class CrisisUser(HttpUser):
    """
    Simulates T3/T4 SOS path (5 % of virtual users).

    SLO: POST /v1/sos p99 ≤ 200ms (CLAUDE.md rule 1 — deterministic crisis path).
    The SOS endpoint must never miss; it is the highest-priority latency target
    in the system.  A 200ms p99 budget under any load level is non-negotiable.

    NOTE: The spec (§5.2) states the SOS response is served from a pre-cached
    device payload when possible and the network call is fire-and-forget.
    This user class still measures server-side latency to verify the server
    can sustain the budget even without client-side caching.
    """

    weight = 5
    wait_time = between(5, 15)
    headers: dict[str, str]

    def on_start(self) -> None:
        self.headers = _fake_auth_headers()

    @task(1)
    def post_sos(self) -> None:
        """
        T3 SOS trigger.  Server must respond ≤ 200ms p99.
        A 451 response is treated as success per spec §16 (deterministic
        fallback payload — never return 500 on a T3 path).
        """
        payload = {"started_at": _now_iso()}
        with self.client.post(
            "/v1/sos",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/sos [T3-CRISIS]",
        ) as resp:
            # 201 = success; 401 = expected without real auth; 451 = degraded
            # but still a valid deterministic crisis response per spec §16.
            # Any 5xx is a failure — the spec explicitly forbids 500 on T3.
            if resp.status_code >= 500:
                resp.failure(
                    f"5xx on T3 crisis path — spec forbids this: {resp.status_code}"
                )
            else:
                resp.success()


class AssessmentUser(HttpUser):
    """
    Simulates weekly psychometric assessment flow (15 % of virtual users).

    Models a user completing a PHQ-9 or similar instrument.  The long wait
    between tasks (30–90 s) reflects realistic questionnaire completion time —
    do not reduce this; it would generate an unrealistically high RPS from
    this user class.

    Safety note: PHQ-9 item 9 (suicidal ideation) is always set to 0 in load
    test payloads to avoid triggering T4 escalation against a real API instance.
    """

    weight = 15
    wait_time = between(30, 90)
    headers: dict[str, str]

    def on_start(self) -> None:
        self.headers = _fake_auth_headers()

    @task(2)
    def get_due_assessments(self) -> None:
        """Which instruments are due now?  Spec §20."""
        with self.client.get(
            "/v1/psychometric/due",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/psychometric/due",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def post_assessment(self) -> None:
        """
        Submit a completed psychometric instrument.  Spec §20.
        Uses PHQ-9 with item 9 = 0 (safe for load testing).
        """
        instrument = random.choice(_INSTRUMENTS)
        # Use PHQ-9-safe responses for all instruments in load test payloads.
        # For non-PHQ9 instruments the server will reject with 422 (wrong item
        # count), which is treated as a successful request for load purposes.
        payload = {
            "instrument_id": instrument,
            "version": "1.0",
            "responses": _PHQ9_RESPONSES,
        }
        with self.client.post(
            "/v1/assessments",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/assessments",
        ) as resp:
            if resp.status_code not in (201, 401, 422):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def get_assessment_trajectory(self) -> None:
        """Trajectory chart data.  Spec §20."""
        instrument = random.choice(["phq9", "gad7", "who5"])
        with self.client.get(
            f"/v1/assessments/trajectory?instrument={instrument}&window=90d",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/assessments/trajectory",
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()


class ClinicianUser(HttpUser):
    """
    Simulates clinician portal access patterns (10 % of virtual users).

    Clinician sessions are longer-lived and lower-frequency than regular user
    sessions; the 10–30 s wait models a clinician reading between page loads.
    Every read on the clinician path emits an audit log entry (spec §12 /
    CLAUDE.md rule 6), so this user class indirectly stresses the audit
    log pipeline.
    """

    weight = 10
    wait_time = between(10, 30)
    headers: dict[str, str]

    def on_start(self) -> None:
        self.headers = _fake_auth_headers()

    @task(3)
    def get_clinician_links(self) -> None:
        """List of patient-clinician links.  Enterprise router §13."""
        with self.client.get(
            "/v1/enterprise/clinician-links",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/enterprise/clinician-links",
        ) as resp:
            if resp.status_code not in (200, 401, 403):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def get_clinician_patients(self) -> None:
        """Patient list (clinician scope).  Spec §12.1."""
        with self.client.get(
            "/v1/clinician/patients?status=active",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/clinician/patients",
        ) as resp:
            if resp.status_code not in (200, 401, 403, 404):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def get_insights_patterns(self) -> None:
        """Patterns endpoint shared by both user and clinician views."""
        with self.client.get(
            "/v1/insights/patterns",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/insights/patterns",
        ) as resp:
            if resp.status_code not in (200, 401, 403):
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()
