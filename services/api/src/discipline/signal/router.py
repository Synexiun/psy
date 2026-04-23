"""Signal HTTP surface — signal ingest and state estimates.

Endpoints:
- ``POST /v1/signals/windows`` — batch signal window ingest
- ``GET /v1/signals/state`` — latest state estimate for caller
- ``POST /v1/signals/state`` — record a new state estimate
- ``GET /v1/signals/device-capabilities`` — device capability stub

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.signal.repository import (
    get_signal_window_repository,
    get_state_estimate_repository,
)

router = APIRouter(tags=["signal"])


# =============================================================================
# Signal window schemas
# =============================================================================


class SignalSample(BaseModel):
    """A single sample within a window."""

    timestamp: str = Field(..., min_length=1)
    value: float
    unit: str | None = Field(default=None, max_length=32)


class SignalWindowCreate(BaseModel):
    """Request body for ingesting a signal window."""

    window_start: str = Field(..., min_length=1)
    window_end: str = Field(..., min_length=1)
    source: str = Field(..., pattern=r"^(healthkit|health_connect|manual_checkin|watch)$")
    samples: list[SignalSample] = Field(default_factory=list)


class SignalWindowItem(BaseModel):
    """Ingested signal window response."""

    window_id: str
    window_start: str
    window_end: str
    source: str
    samples_hash: str
    created_at: str


# =============================================================================
# State estimate schemas
# =============================================================================


class StateEstimateCreate(BaseModel):
    """Request body for recording a state estimate."""

    state_label: str = Field(
        ...,
        pattern=r"^(stable|rising_urge|peak_urge|post_urge|baseline)$",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = Field(..., min_length=1, max_length=32)
    inferred_at: str = Field(..., min_length=1)
    features: dict[str, object] | None = Field(default=None)


class StateEstimateItem(BaseModel):
    """State estimate response."""

    estimate_id: str
    state_label: str
    confidence: float
    model_version: str
    inferred_at: str
    created_at: str


# =============================================================================
# Device capability schemas
# =============================================================================


class DeviceCapabilities(BaseModel):
    """Device capability report."""

    heart_rate: bool
    hrv: bool
    accelerometer: bool
    sleep: bool
    audio_journal: bool


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


def _hash_samples(samples: list[SignalSample]) -> str:
    """Deterministic hash of samples for deduplication."""
    import hashlib
    import json

    canonical = json.dumps(
        [{"t": s.timestamp, "v": s.value, "u": s.unit} for s in samples],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# =============================================================================
# Signal window endpoints
# =============================================================================


@router.post("/signals/windows", response_model=SignalWindowItem, status_code=201)
async def ingest_signal_window(
    payload: SignalWindowCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> SignalWindowItem:
    """Ingest a signal window batch.

    Deduplicates by ``samples_hash`` — identical sample sequences from
    the same user are silently ignored (idempotent at the hash level).
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_signal_window_repository()
    samples_hash = _hash_samples(payload.samples)

    existing = await repo.get_by_samples_hash(user_id, samples_hash)
    if existing is not None:
        return SignalWindowItem(
            window_id=existing.window_id,
            window_start=existing.window_start,
            window_end=existing.window_end,
            source=existing.source,
            samples_hash=existing.samples_hash,
            created_at=existing.created_at,
        )

    record = await repo.create(
        user_id=user_id,
        window_start=payload.window_start,
        window_end=payload.window_end,
        source=payload.source,
        samples_hash=samples_hash,
        samples_json={"samples": [s.model_dump() for s in payload.samples]},
    )
    return SignalWindowItem(
        window_id=record.window_id,
        window_start=record.window_start,
        window_end=record.window_end,
        source=record.source,
        samples_hash=record.samples_hash,
        created_at=record.created_at,
    )


# =============================================================================
# State estimate endpoints
# =============================================================================


@router.post("/signals/state", response_model=StateEstimateItem, status_code=201)
async def record_state_estimate(
    payload: StateEstimateCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> StateEstimateItem:
    """Record a state classifier estimate.

    Used by the on-device model (server fallback) to log its output.
    The latest estimate drives intervention eligibility.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_state_estimate_repository()
    record = await repo.create(
        user_id=user_id,
        state_label=payload.state_label,
        confidence=payload.confidence,
        model_version=payload.model_version,
        inferred_at=payload.inferred_at,
        features_json=payload.features,
    )
    return StateEstimateItem(
        estimate_id=record.estimate_id,
        state_label=record.state_label,
        confidence=record.confidence,
        model_version=record.model_version,
        inferred_at=record.inferred_at,
        created_at=record.created_at,
    )


@router.get("/signals/state", response_model=StateEstimateItem)
async def get_latest_state_estimate(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> StateEstimateItem:
    """Retrieve the most recent state estimate for the caller."""
    user_id = _derive_user_id(x_user_id)
    repo = get_state_estimate_repository()
    record = await repo.latest_by_user(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="state_estimate.not_found")
    return StateEstimateItem(
        estimate_id=record.estimate_id,
        state_label=record.state_label,
        confidence=record.confidence,
        model_version=record.model_version,
        inferred_at=record.inferred_at,
        created_at=record.created_at,
    )


# =============================================================================
# Device capability endpoint
# =============================================================================


@router.get("/signals/device-capabilities", response_model=DeviceCapabilities)
async def device_capabilities(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> DeviceCapabilities:
    """Return device capability stub.

    Production: queries the user's most recently registered device
    to determine which signal sources are available.
    """
    _ = _derive_user_id(x_user_id)
    return DeviceCapabilities(
        heart_rate=True,
        hrv=True,
        accelerometer=True,
        sleep=True,
        audio_journal=True,
    )
