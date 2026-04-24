"""
Soak test — Discipline OS API.

Purpose: detect memory leaks, connection pool exhaustion, and gradual latency
creep under a sustained moderate load over 30 minutes.

Load shape:
  0–60 s     ramp from 0 to 20 virtual users
  60–1860 s  hold at 20 VU (29 minutes steady state)
  ≥ 1860 s   test ends

20 VU is below the "normal load" tier (50 VU from the SLO spec) but held for
long enough to surface resource leaks that only appear after thousands of
requests.  Signals to watch:

  - Median (p50) latency trend over time: a steadily rising p50 with no
    corresponding RPS increase is a leak signal.
  - 95th/99th percentile latency should remain flat from t=5min onward.
  - Error rate must stay < 0.1% throughout (08_Infrastructure_DevOps §11).
  - Database connection pool: if asyncpg raises "too many clients", that
    appears as 503 responses; count them separately in Grafana.

Run:
    locust -f tests/load/scenarios/soak_test.py --host=http://localhost:8000 \\
           --headless --run-time 31m --csv=soak-results

Monitor in parallel:
    # Memory growth on the API Fargate task
    watch -n 30 "aws cloudwatch get-metric-statistics \\
        --namespace AWS/ECS --metric-name MemoryUtilization \\
        --dimensions Name=ServiceName,Value=discipline-api \\
        --start-time $(date -u -d '35 minutes ago' +%FT%TZ) \\
        --end-time $(date -u +%FT%TZ) \\
        --period 60 --statistics Average"
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime

from locust import HttpUser, LoadTestShape, between, task

_TRIGGER_TAGS = [
    "stress",
    "work_deadline",
    "social_pressure",
    "evening_alone",
    "boredom",
    "fatigue",
]

_LOCATION_CONTEXTS = ["work", "home", "transit", "social", "unknown"]


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _idempotency_key() -> str:
    return str(uuid.uuid4())


def _fake_auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer load-test-synthetic-jwt"}


# ---------------------------------------------------------------------------
# Load shape
# ---------------------------------------------------------------------------


class SoakShape(LoadTestShape):
    """
    Ramp from 0 to 20 users over 60 s, then hold for the remainder of the
    configured run time.  The shape hands off to Locust's built-in run-time
    limit (--run-time) to stop the test.
    """

    _RAMP_DURATION_S = 60
    _PEAK_USERS = 20
    _SPAWN_RATE = 1  # slow ramp to avoid masking early leaks

    def tick(self) -> tuple[int, float] | None:
        run_time = self.get_run_time()
        if run_time < self._RAMP_DURATION_S:
            # Linear ramp
            current = max(
                1,
                int(self._PEAK_USERS * run_time / self._RAMP_DURATION_S),
            )
            return current, self._SPAWN_RATE
        return self._PEAK_USERS, self._SPAWN_RATE


# ---------------------------------------------------------------------------
# User behaviour
# ---------------------------------------------------------------------------


class SoakUser(HttpUser):
    """
    Broad, representative user behaviour sustained over 30 minutes.

    The task mix intentionally covers all major backend subsystems so that any
    subsystem-specific resource leak (e.g. unclosed Redis connections in the
    pattern module, uncollected SQLAlchemy sessions in the analytics module)
    manifests within the soak window.
    """

    wait_time = between(3, 10)
    headers: dict[str, str]

    def on_start(self) -> None:
        self.headers = _fake_auth_headers()

    # ---- reads (lower cost, higher frequency) ----

    @task(4)
    def get_today(self) -> None:
        with self.client.get(
            "/v1/today",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/today [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_streak(self) -> None:
        with self.client.get(
            "/v1/streak",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/streak [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_patterns(self) -> None:
        with self.client.get(
            "/v1/patterns?active=true",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/patterns [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def get_insights_resilience(self) -> None:
        with self.client.get(
            "/v1/insights/resilience",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/insights/resilience [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def get_me(self) -> None:
        with self.client.get(
            "/v1/me",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/me [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def get_signals_state(self) -> None:
        """Signal state read — exercises the TimescaleDB hypertable path."""
        with self.client.get(
            "/v1/signals/state",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/signals/state [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    # ---- writes (higher cost, lower frequency) ----

    @task(3)
    def post_urge(self) -> None:
        """Write path — exercises DB pool + bandit policy lookup."""
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
            name="POST /v1/urges [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def post_signal_window(self) -> None:
        """
        Signal batch upload — exercises the TimescaleDB write path and the
        PgBouncer transaction-mode connection pool.  A single-window payload
        is sufficient; realistic clients send 5-minute batches.
        """
        payload = {
            "windows": [
                {
                    "ts": _now_iso(),
                    "window_seconds": 60,
                    "hrv_rmssd_ms": round(random.uniform(20.0, 60.0), 1),
                    "hr_bpm": random.randint(55, 100),
                    "step_count": random.randint(0, 80),
                    "phone_unlock_count": random.randint(0, 5),
                    "scroll_velocity_ema": round(random.uniform(0.0, 4.0), 2),
                    "geofence_risk": 0,
                    "signal_source": "apple_watch",
                    "device_confidence": round(random.uniform(0.7, 1.0), 2),
                }
            ]
        }
        with self.client.post(
            "/v1/signals/windows",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/signals/windows [soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during soak: {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def post_sos(self) -> None:
        """
        T3 path — included in soak to verify the crisis path holds its
        200ms p99 budget even after 30 minutes of sustained load.
        5xx on this path is always a critical finding.
        """
        payload = {"started_at": _now_iso()}
        with self.client.post(
            "/v1/sos",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/sos [T3-CRISIS soak]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(
                    f"5xx on T3 crisis path during soak — critical: {resp.status_code}"
                )
            else:
                resp.success()
