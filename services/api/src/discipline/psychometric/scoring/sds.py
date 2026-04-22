"""SDS — Severity of Dependence Scale (Gossop, Darke, Griffiths, Hando,
Powis, Hall, Strang 1995).

The Severity of Dependence Scale is a 5-item screen for *psychological*
dependence on a specified substance — the subjective compulsive-use
construct (loss of control, worry about use, desire to stop, perceived
difficulty of abstaining), deliberately *distinct* from the amount-and-
frequency-of-use dimension measured by AUDIT / AUDIT-C (alcohol) and
DAST-10 (drug use severity).  A patient can score low on DAST-10
(infrequent, low-volume use) yet high on SDS (the little use they have
feels out of control), or high on DAST-10 yet low on SDS (heavy but
ego-syntonic use).  Gossop 1995 validated this construct as the signal
that discriminates dependent from non-dependent users and predicts
treatment outcome better than consumption volume alone.

Clinical relevance to the Discipline OS platform:
SDS fills a distinct slot from the alcohol / drug-use pillar — it
catches the psychological-dependence signal that determines *how hard
it will be to stop*, which is the actionable question for relapse
prevention.  Per Docs/Technicals/12_Psychometric_System.md Tier B
roadmap, SDS is scheduled for v1.5 addition to the catalog
("Dependence" construct, 5 items).

Instrument structure (Gossop 1995, "In the past month..."):

**5 items, each on a 0-3 Likert scale**:

 1. Did you think your use of [substance] was out of control?
    0 = Never / almost never
    1 = Sometimes
    2 = Often
    3 = Always / nearly always

 2. Did the prospect of missing a fix (or dose) make you anxious or
    worried?
    0 = Never / almost never
    1 = Sometimes
    2 = Often
    3 = Always / nearly always

 3. Did you worry about your use of [substance]?
    0 = Not at all
    1 = A little
    2 = Quite a lot
    3 = A great deal

 4. Did you wish you could stop?
    0 = Never / almost never
    1 = Sometimes
    2 = Often
    3 = Always / nearly always

 5. How difficult did you find it to stop, or go without,
    [substance]?
    0 = Not difficult
    1 = Quite difficult
    2 = Very difficult
    3 = Impossible

Range: 0-15 total.

**Substance-adaptive positive-screen cutoffs** (the load-bearing
design choice for this instrument):

| Substance   | Cutoff | Source                           |
| ----------- | ------ | -------------------------------- |
| heroin      | ≥ 5    | Gossop 1995                      |
| cannabis    | ≥ 3    | Martin 2006 / Swift 1998         |
| cocaine     | ≥ 3    | Kaye & Darke 2002/2004           |
| amphetamine | ≥ 4    | Topp & Mattick 1997              |
| unspecified | ≥ 3    | conservative default (this scorer) |

Unlike PHQ-9 / GAD-7 (one severity band set, fixed) or AUDIT-C (two
cutoffs keyed on sex), SDS has a *substance-keyed* cutoff with
published thresholds for at least a dozen substances in the
downstream literature.  This scorer ships the four most-cited
substance cutoffs plus a conservative unspecified default; extending
to additional substances (MDMA ≥ 4 per Topp 1999, benzodiazepines ≥ 7
per de las Cuevas 2000, alcohol ≥ 3 per Lawrinson 2007, etc.) is a
clinical-sign-off change to ``SDS_CUTOFFS``, not a code-shape change.

Safety posture:
Default to the **lower** cutoff when substance is unspecified — same
conservative posture as AUDIT-C sex="unspecified".  It is better to
over-flag a possible dependence signal and let a clinician adjudicate
than to under-flag and miss a relapse-risk patient.  The default
``SDS_CUTOFF_UNSPECIFIED = 3`` matches the cannabis / cocaine cutoff,
which is the lowest published substance cutoff at the time of this
writing.

Complement to AUDIT / AUDIT-C / DAST-10:
- AUDIT-C / AUDIT: alcohol use frequency and consequences.
- DAST-10: drug use severity and consequences (multi-substance).
- SDS: subjective psychological dependence on a *named* substance.
Running AUDIT + SDS(substance="alcohol") on the same patient gives
two orthogonal reads: how much they drink, and how captive they feel
to the drinking.  A clinician treats a low-AUDIT-high-SDS patient
very differently from a high-AUDIT-low-SDS patient.

Subscale note:
Gossop 1995 reported a dominant single factor and validated SDS as
unidimensional.  No subscales are wire-exposed; splitting items
into "cognitive" (items 1/3/4) vs. "behavioral" (items 2/5) factors
has been explored but not clinically validated and is not used here.

Safety routing:
SDS has **no direct safety item**.  None of the five items probes
suicidal thoughts, plans, or intent.  ``requires_t3`` is never set
by this scorer — acute suicidality screening is the job of PHQ-9
item 9 / C-SSRS, not SDS.  A patient with a high SDS (strongly
positive psychological dependence) may benefit from a co-administered
C-SSRS; that is a separate instrument submission per the Safety
Framework.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py for the shared
rationale.

References:
- Gossop M, Darke S, Griffiths P, Hando J, Powis B, Hall W, Strang J
  (1995).  *The Severity of Dependence Scale (SDS): psychometric
  properties of the SDS in English and Australian samples of heroin,
  cocaine and amphetamine users.*  Addiction 90(5):607-614.
- Martin G, Copeland J, Gates P, Gilmour S (2006).  *The Severity of
  Dependence Scale (SDS) in an adolescent population of cannabis
  users: reliability, validity and diagnostic cut-off.*  Drug and
  Alcohol Dependence 83(1):90-93.
- Swift W, Copeland J, Hall W (1998).  *Choosing a diagnostic
  cut-off for cannabis dependence.*  Addiction 93(11):1681-1692.
- Kaye S, Darke S (2002).  *Determining a diagnostic cut-off on the
  Severity of Dependence Scale (SDS) for cocaine dependence.*
  Addiction 97(6):727-731.
- Topp L, Mattick RP (1997).  *Choosing a cut-off on the Severity
  of Dependence Scale (SDS) for amphetamine users.*  Addiction
  92(7):839-845.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "sds-1.0.0"
ITEM_COUNT = 5
ITEM_MIN = 0
ITEM_MAX = 3

# Substance-adaptive cutoffs.  Each entry is the *minimum* total at
# which a positive screen is asserted — ``total >= cutoff``.  Pinned
# as a module constant so any change forces a clinical sign-off
# rather than slipping through as a tweak.  Sources for each cutoff
# are cited in the module docstring.
SDS_CUTOFF_HEROIN = 5
SDS_CUTOFF_CANNABIS = 3
SDS_CUTOFF_COCAINE = 3
SDS_CUTOFF_AMPHETAMINE = 4
# Conservative default for callers that cannot or will not name the
# substance.  Matches the lowest published cutoff (cannabis/cocaine)
# — same safety posture as AUDIT-C's sex="unspecified" falling back
# to the female (lower) cutoff.
SDS_CUTOFF_UNSPECIFIED = 3

SDS_CUTOFFS: dict[str, int] = {
    "heroin": SDS_CUTOFF_HEROIN,
    "cannabis": SDS_CUTOFF_CANNABIS,
    "cocaine": SDS_CUTOFF_COCAINE,
    "amphetamine": SDS_CUTOFF_AMPHETAMINE,
    "unspecified": SDS_CUTOFF_UNSPECIFIED,
}

Substance = Literal[
    "heroin",
    "cannabis",
    "cocaine",
    "amphetamine",
    "unspecified",
]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class SdsResult:
    """Typed SDS output.

    Fields:
    - ``total``: 0-15, the straight sum of the 5 Likert items.
    - ``cutoff_used``: the integer cutoff that was applied for the
      supplied substance, surfaced so downstream renderers can show
      "positive at ≥ N" without re-implementing the substance → cutoff
      mapping.  This is the AUDIT-C precedent applied to the
      substance axis.
    - ``positive_screen``: ``total >= cutoff_used``.  The actionable
      flag — true means route to follow-up / psychological-dependence
      work-up.
    - ``substance``: the substance key used to select the cutoff.
      Echoed for audit traceability — a renderer or log consumer can
      reconstruct which cutoff table row was applied without having
      to look up SDS_CUTOFFS.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  SDS has no safety item.  See module docstring.
    """

    total: int
    cutoff_used: int
    positive_screen: bool
    substance: Substance
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-5) so error messages
    name the item a clinician would recognize from the SDS document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SDS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"SDS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _cutoff_for(substance: Substance) -> int:
    """Map substance to the published positive-screen cutoff.

    ``unspecified`` falls back to the lowest published cutoff
    (cannabis / cocaine = 3) — safety-conservatism in screening.
    A KeyError here would indicate a Literal type drift, so we
    fall through to unspecified as a defensive default."""
    return SDS_CUTOFFS.get(substance, SDS_CUTOFF_UNSPECIFIED)


def score_sds(
    raw_items: Sequence[int],
    *,
    substance: Substance = "unspecified",
) -> SdsResult:
    """Score an SDS response set with a substance-aware cutoff.

    Inputs:
    - ``raw_items``: 5 items, each 0-3 Likert.
    - ``substance``: the substance name the screen was administered
      against.  Defaults to ``"unspecified"`` so callers that don't
      have or don't want to send a substance value get the
      safety-conservative behavior automatically (cutoff ≥ 3).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - Total score (0-15).
    - Cutoff-keyed positive screen per Gossop 1995 and the substance-
      specific follow-up validation literature (see SDS_CUTOFFS).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SDS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    cutoff = _cutoff_for(substance)
    return SdsResult(
        total=total,
        cutoff_used=cutoff,
        positive_screen=total >= cutoff,
        substance=substance,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SDS_CUTOFFS",
    "SDS_CUTOFF_AMPHETAMINE",
    "SDS_CUTOFF_CANNABIS",
    "SDS_CUTOFF_COCAINE",
    "SDS_CUTOFF_HEROIN",
    "SDS_CUTOFF_UNSPECIFIED",
    "InvalidResponseError",
    "SdsResult",
    "Substance",
    "score_sds",
]
