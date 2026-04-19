"""Analytics HTTP surface — user-facing insights.

All responses respect the P1–P6 framing rules in :mod:`.framing`.  The
business logic lives in the pure composition service
(:mod:`.weekly_reflection`) and the primitives (:mod:`.framing`); this router
is a thin adapter.

Endpoint styles:

- ``POST /insights/weekly/compose`` — accepts a full :class:`WeeklyReflectionInputModel`
  and returns the framed reflection.  This is the service's preview surface:
  callers provide the snapshot data the DB would have supplied.  A future GET
  variant will pull the same data from repositories once they exist.

- ``GET /insights/trajectory`` — query-param single-instrument trajectory
  framing.  Useful for quick UI previews and per-instrument deep-links.

- ``GET /insights/resilience`` — query-param resilience co-presentation.

- ``GET /insights/weekly`` and ``GET /insights/patterns`` remain stubs
  pending repository implementation.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from discipline.psychometric.trajectories import compute_point

from .framing import (
    FramedResilience,
    FramedScore,
    FramedTrend,
    frame_resilience,
    frame_trend,
)
from .weekly_reflection import (
    WeeklyReflection,
    WeeklyReflectionInput,
    compose,
)

router = APIRouter(prefix="/insights", tags=["analytics"])


# ---- Response models --------------------------------------------------------


class FramedScoreResponse(BaseModel):
    instrument: str
    display: str
    tone: Literal["calm", "neutral", "alert"]
    suppressed_reason: str | None = None

    @classmethod
    def from_dataclass(cls, fs: FramedScore) -> "FramedScoreResponse":
        return cls(
            instrument=fs.instrument,
            display=fs.display,
            tone=fs.tone,
            suppressed_reason=fs.suppressed_reason,
        )


class FramedTrendResponse(BaseModel):
    instrument: str
    direction_label: Literal["softer", "steadier", "heavier"] | None
    narrative: str
    tone: Literal["calm", "neutral", "alert"]
    suppressed_reason: Literal["insufficient_data"] | None = None

    @classmethod
    def from_dataclass(cls, ft: FramedTrend) -> "FramedTrendResponse":
        return cls(
            instrument=ft.instrument,
            direction_label=ft.direction_label,
            narrative=ft.narrative,
            tone=ft.tone,
            suppressed_reason=ft.suppressed_reason,
        )


class FramedResilienceResponse(BaseModel):
    resilience_days: int
    days_clean: int
    display: str
    tone: Literal["calm", "neutral", "alert"]

    @classmethod
    def from_dataclass(cls, fr: FramedResilience) -> "FramedResilienceResponse":
        return cls(
            resilience_days=fr.resilience_days,
            days_clean=fr.days_clean,
            display=fr.display,
            tone=fr.tone,
        )


class WeeklyReflectionResponse(BaseModel):
    user_id: str
    week_ending: date
    safety_routed: bool
    severity_phq9: FramedScoreResponse | None
    severity_gad7: FramedScoreResponse | None
    trend_phq9: FramedTrendResponse | None
    trend_gad7: FramedTrendResponse | None
    trend_who5: FramedTrendResponse | None
    trend_pss10: FramedTrendResponse | None
    resilience: FramedResilienceResponse | None

    @classmethod
    def from_dataclass(cls, r: WeeklyReflection) -> "WeeklyReflectionResponse":
        return cls(
            user_id=r.user_id,
            week_ending=r.week_ending,
            safety_routed=r.safety_routed,
            severity_phq9=(
                FramedScoreResponse.from_dataclass(r.severity_phq9)
                if r.severity_phq9 is not None
                else None
            ),
            severity_gad7=(
                FramedScoreResponse.from_dataclass(r.severity_gad7)
                if r.severity_gad7 is not None
                else None
            ),
            trend_phq9=(
                FramedTrendResponse.from_dataclass(r.trend_phq9)
                if r.trend_phq9 is not None
                else None
            ),
            trend_gad7=(
                FramedTrendResponse.from_dataclass(r.trend_gad7)
                if r.trend_gad7 is not None
                else None
            ),
            trend_who5=(
                FramedTrendResponse.from_dataclass(r.trend_who5)
                if r.trend_who5 is not None
                else None
            ),
            trend_pss10=(
                FramedTrendResponse.from_dataclass(r.trend_pss10)
                if r.trend_pss10 is not None
                else None
            ),
            resilience=(
                FramedResilienceResponse.from_dataclass(r.resilience)
                if r.resilience is not None
                else None
            ),
        )


# ---- Request models ---------------------------------------------------------


class WeeklyReflectionInputModel(BaseModel):
    """Wire-format mirror of :class:`WeeklyReflectionInput`."""

    user_id: str
    week_ending: date
    phq9_current: int | None = Field(default=None, ge=0, le=27)
    phq9_baseline: int | None = Field(default=None, ge=0, le=27)
    gad7_current: int | None = Field(default=None, ge=0, le=21)
    gad7_baseline: int | None = Field(default=None, ge=0, le=21)
    who5_current: float | None = Field(default=None, ge=0, le=100)
    who5_baseline: float | None = Field(default=None, ge=0, le=100)
    pss10_current: float | None = Field(default=None, ge=0, le=40)
    pss10_baseline: float | None = Field(default=None, ge=0, le=40)
    resilience_days: int = Field(default=0, ge=0)
    days_clean: int = Field(default=0, ge=0)
    n_checkins_7d: int = Field(default=0, ge=0)
    safety_positive_this_week: bool = False

    def to_dataclass(self) -> WeeklyReflectionInput:
        return WeeklyReflectionInput(
            user_id=self.user_id,
            week_ending=self.week_ending,
            phq9_current=self.phq9_current,
            phq9_baseline=self.phq9_baseline,
            gad7_current=self.gad7_current,
            gad7_baseline=self.gad7_baseline,
            who5_current=self.who5_current,
            who5_baseline=self.who5_baseline,
            pss10_current=self.pss10_current,
            pss10_baseline=self.pss10_baseline,
            resilience_days=self.resilience_days,
            days_clean=self.days_clean,
            n_checkins_7d=self.n_checkins_7d,
            safety_positive_this_week=self.safety_positive_this_week,
        )


# ---- Endpoints --------------------------------------------------------------


_SUPPORTED_TREND_INSTRUMENTS: frozenset[str] = frozenset(
    {"phq9", "gad7", "who5", "pss10", "audit_c"}
)


@router.post("/weekly/compose", response_model=WeeklyReflectionResponse, status_code=200)
async def compose_weekly_reflection(
    payload: WeeklyReflectionInputModel,
) -> WeeklyReflectionResponse:
    """Compose a P1–P6-compliant weekly reflection from provided snapshot data.

    This is the service's preview surface; in production the GET variant will
    assemble the same input from repositories behind the identity middleware.
    A ``safety_positive_this_week=true`` payload returns HTTP 200 with
    ``safety_routed=true`` — the client inspects the flag and renders the T3
    handoff UI.  We return 200 (not 4xx) because the request is well-formed;
    the safety state is a domain signal, not a validation error.
    """
    reflection = compose(payload.to_dataclass())
    return WeeklyReflectionResponse.from_dataclass(reflection)


@router.get("/trajectory", response_model=FramedTrendResponse)
async def get_trajectory(
    instrument: str = Query(..., description="Instrument key (phq9, gad7, who5, pss10, audit_c)"),
    current: float = Query(..., ge=0),
    baseline: float | None = Query(None, ge=0),
    n_checkins_7d: int | None = Query(None, ge=0),
) -> FramedTrendResponse:
    """Single-instrument trajectory framing.

    P6 enforcement lives upstream in :func:`frame_trend`, which raises
    :class:`SafetyPositiveBypassError` when ``has_safety_positive=True``.
    This endpoint does not accept that flag — safety-positive assessments
    MUST route through the weekly reflection composition so the UI can
    short-circuit to T3.  Attempting to expose a trend for a known
    safety-positive signal is a structural bug; we simply do not allow it
    at the HTTP surface.
    """
    if instrument not in _SUPPORTED_TREND_INSTRUMENTS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.unknown_instrument",
                "message": f"trajectory framing not supported for {instrument!r}",
            },
        )
    point = compute_point(instrument, current=current, baseline=baseline)
    framed = frame_trend(point, n_checkins_7d=n_checkins_7d)
    return FramedTrendResponse.from_dataclass(framed)


@router.get("/resilience", response_model=FramedResilienceResponse)
async def get_resilience(
    resilience_days: int = Query(..., ge=0),
    days_clean: int = Query(..., ge=0),
) -> FramedResilienceResponse:
    """Resilience co-presentation (P2).  Both fields are required — the
    service rejects any attempt to surface resilience in isolation."""
    framed = frame_resilience(
        resilience_days=resilience_days, days_clean=days_clean
    )
    return FramedResilienceResponse.from_dataclass(framed)


@router.get("/weekly")
async def weekly_reflection() -> dict[str, str]:
    """Stub — GET variant pending repository integration.

    Use POST ``/insights/weekly/compose`` for the preview surface today.
    """
    return {"status": "not_implemented"}


@router.get("/patterns")
async def patterns() -> dict[str, str]:
    """Stub — reads from pattern.PatternRepository."""
    return {"status": "not_implemented"}
