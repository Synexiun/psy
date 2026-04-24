"""OpenTelemetry bootstrap for Discipline OS API.

Reads OTEL_EXPORTER_OTLP_ENDPOINT from Settings (default: ``http://localhost:4318``).
Service name comes from Settings.otel_service_name (default: ``discipline-api``).
Service version comes from the APP_VERSION env var or the package __version__.

Propagators: W3C TraceContext + Baggage (IETF standard; ensures distributed
trace context flows correctly from mobile clients and CloudFront edges).

No-op behaviour
---------------
- ``OTEL_SDK_DISABLED=true`` — skip all instrumentation.
- ``OTEL_EXPORTER_OTLP_ENDPOINT`` is the literal string ``"none"`` or empty —
  skip export (useful in unit tests / local dev without a collector).

FastAPI auto-instrumentation is applied when the SDK is active so every
request generates a root span without manual decorator boilerplate.

Called once from ``app.py`` lifespan::

    configure_tracing(settings.otel_service_name, settings.otel_endpoint)
"""

from __future__ import annotations

import os

from opentelemetry import trace


def configure_tracing(service_name: str, endpoint: str) -> None:
    """Bootstrap the OTel SDK.

    Parameters
    ----------
    service_name:
        Value of ``Settings.otel_service_name`` — controls the ``service.name``
        resource attribute visible in Tempo / Grafana.
    endpoint:
        Value of ``Settings.otel_endpoint`` (i.e. ``OTEL_EXPORTER_OTLP_ENDPOINT``).
        Pass an empty string or ``"none"`` to skip export and run the SDK in
        no-op mode (safe for local dev and unit tests).
    """
    # --- no-op guard ---------------------------------------------------------
    sdk_disabled = os.getenv("OTEL_SDK_DISABLED", "").lower() == "true"
    endpoint_inactive = not endpoint or endpoint.lower() == "none"
    if sdk_disabled or endpoint_inactive:
        return

    # --- SDK setup -----------------------------------------------------------
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from discipline import __version__ as _pkg_version

    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: os.getenv("APP_VERSION", _pkg_version),
        }
    )
    provider = TracerProvider(resource=resource)

    # --- OTLP exporter -------------------------------------------------------
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except ImportError:
        # opentelemetry-exporter-otlp-proto-http not installed — acceptable
        # in stripped-down dev envs; SDK still active for in-process spans.
        pass

    trace.set_tracer_provider(provider)

    # --- W3C propagators (TraceContext + Baggage) ----------------------------
    try:
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.b3 import B3MultiFormat  # noqa: F401 — optional
    except ImportError:
        pass

    try:
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.composite import CompositePropagator
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        from opentelemetry.baggage.propagation import W3CBaggagePropagator

        set_global_textmap(
            CompositePropagator(
                [TraceContextTextMapPropagator(), W3CBaggagePropagator()]
            )
        )
    except ImportError:
        # Propagator packages missing — fall back to SDK default.
        pass

    # --- FastAPI auto-instrumentation ----------------------------------------
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument()
    except ImportError:
        # opentelemetry-instrumentation-fastapi not installed — acceptable.
        pass


def tracer(name: str) -> trace.Tracer:
    """Return a named tracer from the global provider.

    Usage::

        _tracer = tracer(__name__)

        async def my_handler() -> None:
            with _tracer.start_as_current_span("my_handler"):
                ...
    """
    return trace.get_tracer(name)
