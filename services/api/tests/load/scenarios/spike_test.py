"""
Spike test — Discipline OS API.

Tests auto-scaling behaviour (ECS Fargate desired count 12 → up to 60 on RPS,
per Docs/Technicals/08_Infrastructure_DevOps.md §5.1).

Load shape:
  0 →  30 s  ramp from 0 to 200 virtual users  (spawn rate: ~6-7 users/s)
 30 → 90 s   hold at 200 users
 90 → 120 s  ramp down to 0

The spike deliberately exceeds the "normal load" tier (50 VU) to probe the
auto-scaling signal and measure p99 degradation under burst.  The expected
outcome is that p99 stays below 2× the normal-load p99 (≤ 4s for pattern
analysis) — a regression here indicates the scaling policy is too slow.

Run:
    locust -f tests/load/scenarios/spike_test.py --host=http://localhost:8000 \\
           --headless --run-time 120s --csv=spike-results --only-summary

The spawn rate is controlled by --users / --spawn-rate when using the custom
shape.  When using LoadTestShape the UI does not accept --users / --spawn-rate;
let the shape class drive them.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from locust import HttpUser, LoadTestShape, between, task


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _idempotency_key() -> str:
    return str(uuid.uuid4())


def _fake_auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer load-test-synthetic-jwt"}


class SpikeShape(LoadTestShape):
    """
    Three-phase shape:
      Phase 1 (0–30 s):  ramp 0 → 200 VU at 7 users/s
      Phase 2 (30–90 s): hold at 200 VU
      Phase 3 (90–120 s): ramp down to 0 (Locust stops when tick() returns None)
    """

    stages = [
        {"duration": 30, "users": 200, "spawn_rate": 7},
        {"duration": 90, "users": 200, "spawn_rate": 7},
        {"duration": 120, "users": 0, "spawn_rate": 7},
    ]

    def tick(self) -> tuple[int, float] | None:
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


class SpikeUser(HttpUser):
    """
    Focused user that hits the most latency-sensitive endpoints during the spike.
    Deliberately mixes read-heavy and write-heavy paths to stress both the DB
    connection pool and the auth middleware.
    """

    wait_time = between(1, 3)
    headers: dict[str, str]

    def on_start(self) -> None:
        self.headers = _fake_auth_headers()

    @task(4)
    def post_urge(self) -> None:
        """High-frequency write — most likely to saturate DB pool first."""
        payload = {
            "started_at": _now_iso(),
            "intensity_start": 7,
            "trigger_tags": ["stress", "work_deadline"],
            "location_context": "work",
            "origin": "self_reported",
        }
        with self.client.post(
            "/v1/urges",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/urges [spike]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during spike: {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_patterns(self) -> None:
        """Pattern list — p99 budget 2s; first to degrade under spike."""
        with self.client.get(
            "/v1/patterns?active=true",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/patterns [spike]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during spike: {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def post_sos(self) -> None:
        """
        SOS path must remain ≤ 200ms p99 even during a traffic spike.
        A 5xx here is a critical finding — report immediately.
        """
        payload = {"started_at": _now_iso()}
        with self.client.post(
            "/v1/sos",
            json=payload,
            headers={**self.headers, "Idempotency-Key": _idempotency_key()},
            catch_response=True,
            name="POST /v1/sos [T3-CRISIS spike]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(
                    f"5xx on T3 crisis path during spike — critical: {resp.status_code}"
                )
            else:
                resp.success()

    @task(1)
    def get_streak(self) -> None:
        with self.client.get(
            "/v1/streak",
            headers=self.headers,
            catch_response=True,
            name="GET /v1/streak [spike]",
        ) as resp:
            if resp.status_code >= 500:
                resp.failure(f"5xx during spike: {resp.status_code}")
            else:
                resp.success()
