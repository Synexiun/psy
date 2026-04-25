"""Tests for discipline.shared.tracing.

configure_tracing is an OTel bootstrap function. The tests exercise the
no-op guard paths (disabled SDK, inactive endpoint) without requiring a live
collector. The production SDK path is not tested here because it would require
opentelemetry-exporter-otlp-proto-http to be installed and a collector
endpoint to be reachable — both are integration concerns.

What we verify:
- No-op path: OTEL_SDK_DISABLED=true → function returns without error
- No-op path: empty endpoint → function returns without error
- No-op path: endpoint="none" (case-insensitive) → returns without error
- No-op path: endpoint="NONE" (uppercase) → returns without error
- tracer() returns an OpenTelemetry Tracer object
- tracer() with a named module string works
"""

from __future__ import annotations

import os
from unittest.mock import patch


class TestConfigureTracingNoOp:
    def test_sdk_disabled_env_returns_cleanly(self) -> None:
        from discipline.shared.tracing import configure_tracing

        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}):
            configure_tracing("discipline-api", "http://localhost:4318")
        # No exception raised

    def test_empty_endpoint_returns_cleanly(self) -> None:
        from discipline.shared.tracing import configure_tracing

        configure_tracing("discipline-api", "")

    def test_endpoint_none_lowercase_returns_cleanly(self) -> None:
        from discipline.shared.tracing import configure_tracing

        configure_tracing("discipline-api", "none")

    def test_endpoint_none_uppercase_returns_cleanly(self) -> None:
        from discipline.shared.tracing import configure_tracing

        configure_tracing("discipline-api", "NONE")

    def test_endpoint_none_mixed_case_returns_cleanly(self) -> None:
        from discipline.shared.tracing import configure_tracing

        configure_tracing("discipline-api", "None")

    def test_sdk_disabled_false_with_none_endpoint_returns_cleanly(self) -> None:
        from discipline.shared.tracing import configure_tracing

        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "false"}):
            configure_tracing("service", "none")

    def test_returns_none(self) -> None:
        from discipline.shared.tracing import configure_tracing

        result = configure_tracing("discipline-api", "")
        assert result is None


class TestTracer:
    def test_returns_tracer_object(self) -> None:
        from opentelemetry import trace

        from discipline.shared.tracing import tracer

        t = tracer("test.module")
        assert isinstance(t, trace.Tracer)

    def test_module_name_accepted(self) -> None:
        from discipline.shared.tracing import tracer

        t = tracer("discipline.psychometric.scoring.phq9")
        assert t is not None

    def test_empty_string_accepted(self) -> None:
        from discipline.shared.tracing import tracer

        t = tracer("")
        assert t is not None

    def test_two_tracers_from_same_name(self) -> None:
        from discipline.shared.tracing import tracer

        t1 = tracer("my.module")
        t2 = tracer("my.module")
        # Both should be valid tracer objects
        assert t1 is not None
        assert t2 is not None
