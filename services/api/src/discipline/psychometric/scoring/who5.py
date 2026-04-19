"""WHO-5 Well-Being Index scoring — Topp et al. (2015) review.

Five positively-worded items (original WHO 1998 formulation):

1. I have felt cheerful and in good spirits.
2. I have felt calm and relaxed.
3. I have felt active and vigorous.
4. I woke up feeling fresh and rested.
5. My daily life has been filled with things that interest me.

Each item is scored 0 ("At no time") to 5 ("All of the time") across
the **past two weeks**.  The raw total ranges 0–25.

The **reported score** is the WHO-5 Index, which is ``raw_total × 4``
and ranges 0–100.  The ``× 4`` conversion is non-negotiable — it puts
the score on the same percentage axis as other wellbeing measures and
is the score referenced in every published cutoff.  A deploy that
reports the raw total would mis-trigger every clinical cutoff.

Cutoffs (Topp 2015 §3.2):

- ``< 50`` — Poor wellbeing; consider further assessment.  This is the
  primary screening cutoff referenced by WHO and used in most clinical
  trials.
- ``< 28`` — Positive screen for depression (higher specificity,
  narrower use).  When both bands fire, depression-screen-positive
  takes precedence in UX — it's the stronger signal.

Reverse-scoring: **none**.  All 5 items are positively worded so no
item inversion is required.  This differs from PSS-10 (which reverses
items 4/5/7/8) and is why WHO-5 is one of the simplest-to-score
validated instruments.

References:
- Topp CW, Østergaard SD, Søndergaard S, Bech P (2015).
  *The WHO-5 Well-Being Index: a systematic review of the literature.*
  Psychother Psychosom 84(3):167-176.
- Original: WHO Regional Office for Europe (1998), *Wellbeing measures
  in primary health care/The DEPCARE Project.*
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "who5-1.0.0"
ITEM_COUNT = 5
ITEM_MIN, ITEM_MAX = 0, 5

# The raw-total → WHO-5 Index conversion factor.  Pinned as a constant
# so callers that need the denominator (e.g., renormalization in the
# dashboard) import from one source.
RAW_TO_INDEX_MULTIPLIER = 4

# Cutoffs are expressed on the WHO-5 Index (0–100), not the raw total,
# because that's the scale every published paper uses.
WHO5_POOR_WELLBEING_CUTOFF = 50
WHO5_DEPRESSION_SCREEN_CUTOFF = 28


class InvalidResponseError(ValueError):
    """Raised when raw items fail validation.  Never caught — partial
    scoring on WHO-5 is a bug; better to fail than report a misleading
    wellbeing index."""


# Clinical band label on the WHO-5 Index (0–100 scale).
# ``depression_screen`` is the narrower, stronger signal; ``poor``
# covers the broader "please consider a check-in" band.
Band = Literal["depression_screen", "poor", "adequate"]


@dataclass(frozen=True)
class Who5Result:
    """Typed output of a WHO-5 scoring run.

    Fields:
    - ``raw_total``: sum of the five items, 0–25.  Preserved for
      integration with downstream systems that want to re-verify the
      ``× 4`` conversion.
    - ``index``: WHO-5 Index, ``raw_total * 4``, 0–100.  The reported
      score.
    - ``band``: clinical band on the index scale.  ``depression_screen``
      takes precedence over ``poor`` when both would apply — the
      narrower positive signal is the more actionable one.
    - ``poor_wellbeing_flag``: True iff ``index < 50``.  Exposed as a
      boolean alongside ``band`` so UI code can check one flag without
      matching on the band string.
    - ``items``: verbatim item echo (tuple).
    """

    raw_total: int
    index: int
    band: Band
    poor_wellbeing_flag: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(index: int) -> Band:
    """Map a WHO-5 Index value to its clinical band.

    Precedence is intentional: depression-screen takes precedence over
    poor-wellbeing when both fire (index < 28 is necessarily also
    < 50).  Without this ordering, a UI that matches only on the first
    truthy flag would flag depression screens as ``poor`` and lose the
    stronger signal."""
    if index < WHO5_DEPRESSION_SCREEN_CUTOFF:
        return "depression_screen"
    if index < WHO5_POOR_WELLBEING_CUTOFF:
        return "poor"
    return "adequate"


def score_who5(raw_items: Sequence[int]) -> Who5Result:
    """Score a WHO-5 response set.

    Raises :class:`InvalidResponseError` on item-count or item-range
    violations; callers are expected to let it propagate (partial
    scoring is never acceptable for a clinical instrument).

    The ``× 4`` conversion from raw to index is applied here, not at
    the render boundary, so every consumer sees the same canonical
    index value and can't accidentally forget the conversion.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"WHO-5 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(int(v) for v in raw_items)
    for idx, v in enumerate(items):
        if v < ITEM_MIN or v > ITEM_MAX:
            raise InvalidResponseError(
                f"WHO-5 item {idx + 1} out of range [{ITEM_MIN}, {ITEM_MAX}]: {v}"
            )
    raw_total = sum(items)
    index = raw_total * RAW_TO_INDEX_MULTIPLIER
    band = _classify(index)
    return Who5Result(
        raw_total=raw_total,
        index=index,
        band=band,
        poor_wellbeing_flag=index < WHO5_POOR_WELLBEING_CUTOFF,
        items=items,
    )


__all__ = [
    "Band",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "RAW_TO_INDEX_MULTIPLIER",
    "WHO5_DEPRESSION_SCREEN_CUTOFF",
    "WHO5_POOR_WELLBEING_CUTOFF",
    "Who5Result",
    "score_who5",
]
