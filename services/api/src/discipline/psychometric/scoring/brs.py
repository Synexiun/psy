"""BRS — Brief Resilience Scale (Smith et al. 2008).

The Brief Resilience Scale is a 6-item, 1-5 Likert self-report
instrument developed by Bruce Smith and colleagues at the University
of New Mexico specifically to address a conceptual gap in the
resilience-measurement literature: existing instruments conflated
resilience (the process of bouncing back from adversity) with the
*resources* that support it (optimism, social support, hardiness,
self-efficacy).  BRS was designed to measure the outcome itself —
the capacity to recover and adapt — independent of the resources
that produce it.  Smith 2008 §1-2 explicitly named this the
"original and most basic meaning of resilience" in the stress-
recovery literature (Lazarus 1993; Smith 1989).

The 6-item structure was derived via exploratory factor analysis on
candidate-item pools across four samples (n = 128 undergraduates,
n = 64 undergraduates, n = 112 cardiac-rehabilitation patients,
n = 50 women with chronic pain / fibromyalgia — Smith 2008 §2.1,
§3.1).  Three items are positively worded ("I tend to bounce back
quickly after hard times") and three are negatively worded ("It is
hard for me to snap back when something bad happens").  The three-
positive / three-negative symmetry is deliberate: it controls for
response-set acquiescence bias and produces a single-factor solution
with α = 0.80-0.91 across all four samples (Smith 2008 Table 1).

Clinical relevance to the Discipline OS platform:

BRS complements — but does NOT duplicate — the CD-RISC-10 instrument
already shipped.  The two instruments measure orthogonal dimensions
of the resilience construct and Smith 2008 §3 explicitly
differentiates them:

- **CD-RISC (Connor & Davidson 2003):** measures **agentic
  resilience** — the personal capacities that produce recovery
  (optimism, self-efficacy, emotion regulation, spiritual beliefs,
  goal orientation, adaptability).  A high CD-RISC score means
  "I have the resources to weather adversity."
- **BRS (Smith 2008):** measures **ecological / outcome
  resilience** — the actual recovery itself.  A high BRS score
  means "I do, in fact, bounce back from adversity."

The clinical value of shipping both is the discrepancy case:
patients with high CD-RISC and low BRS have resilience-supporting
resources on paper but are not actually recovering from stressors.
Smith 2008 §4 discussion frames this as a "resource-outcome
decoupling" profile — often seen in patients with depression
comorbidity where the cognitive triad (Beck 1967) interferes with
the deployment of existing resources.  Intervention framing
differs: CD-RISC-focused work builds resources; BRS-focused work
addresses the deployment gap (behavioral activation per Martell
2010; values-based committed action per ACT, Hayes 2012).

BRS also ships as the platform's **primary within-subject
recovery-trajectory instrument**.  The BRS single-factor structure
(Smith 2008 §3.2; Windle 2011 psychometric review) and high test-
retest reliability (r = 0.69 at 3 months; Smith 2008 §3.2) make it
well-suited to repeat administration — unlike CD-RISC which is
more state-sensitive.  A three-month recovery follow-up in the
platform uses BRS as the outcome anchor for RCI computation.

Platform non-negotiables enforced by this module:

1. **Latin digits for all BRS totals, means, and band labels** at
   render time.  The total is a clinical number — Kroenke-style
   uniformity across locales (CLAUDE.md rule 9).
2. **Verbatim item text from Smith 2008.**  No paraphrase.  No
   machine translation.  Translations ship with native-reviewer
   validation or fall back to ``en`` at render time (CLAUDE.md
   rule 8; Smith 2010 multi-language validation framework).
3. **Reverse-keying is applied at scoring time, not at survey
   administration time.**  The patient sees items 2, 4, 6 in the
   original negatively-worded phrasing; the scorer flips them
   internally.  The ``items`` field of the result preserves the
   PATIENT'S raw pre-flip responses — audit-trail invariant,
   matching the TAS-20 / PSWQ / LOT-R pattern.
4. **No T3/T4 triggering.**  BRS probes resilience outcomes —
   none of the 6 items reference suicidality, self-harm, or
   acute-risk behavior.  Acute-risk screening stays on C-SSRS /
   PHQ-9 item 9.

Scoring semantics:

The published convention in Smith 2008 is to report the BRS as a
**mean score** on the 1.00-5.00 scale (sum of 6 post-flip items
divided by 6).  The platform stores the **sum** (6-30) internally
and exposes it as ``total`` to remain uniform with every other
banded instrument (PHQ-9 / GAD-7 / AUDIT / PSS-10 / ISI / PGSI).
The three Smith 2008 bands (low mean 1.00-2.99, normal 3.00-4.30,
high 4.31-5.00) map cleanly onto integer sums because the item
Likert is 1-5:

- Low resilience:     sum 6-17   (mean 1.00-2.99)
- Normal resilience:  sum 18-25  (mean 3.00-4.30)
- High resilience:    sum 26-30  (mean 4.31-5.00)

Direction: **HIGHER = MORE RESILIENT** (opposite of PHQ-9 /
GAD-7 / AUDIT / PGSI where higher = worse).  This matches the
WHO-5 / MAAS / CD-RISC-10 higher-is-better convention already
shipped.

Deliberate design choices (do not remove without clinical review):

- **Store raw pre-flip items.**  ``BrsResult.items`` holds the
  patient's actual 1-5 responses in presentation order.  This is
  the TAS-20 / PSWQ / LOT-R contract — downstream FHIR export
  and clinician review needs the raw audit trail, not the
  post-flip internal representation.
- **Sum-based storage instead of mean-based.**  A single
  ``total: int`` field is uniform across the scorer API.  A
  mean can be computed downstream (``total / ITEM_COUNT``)
  but storing it as the primary field would fragment the
  envelope contract.  The routing layer converts to a band
  label, which is the clinically-consumable output.
- **No subscales.**  BRS is explicitly single-factor by
  construction (Smith 2008 §3.2 EFA eigenvalue 2.68, second
  eigenvalue 0.64 — no second factor).  Surfacing the
  positive-item vs negative-item sums as "subscales" would
  contradict the factor derivation and double-count response-
  set bias (which the reverse-keying design exists to control).
- **No positive_screen field.**  BRS is banded (3 bands), not
  a binary screen.  Clinically-meaningful information is the
  3-way category, not a binary above/below cutoff.  Uniform
  with PHQ-9 / GAD-7 / AUDIT / PSS-10 / ISI / PGSI banded
  pattern, NOT AUDIT-C / PC-PTSD-5 / SHAPS / ACEs screen
  pattern.

Citations:

- Smith BW, Dalen J, Wiggins K, Tooley E, Christopher P, Bernard J
  (2008).  *The brief resilience scale: Assessing the ability to
  bounce back.*  International Journal of Behavioral Medicine
  15(3):194-200.  (Canonical derivation; α = 0.80-0.91 across
  four samples; test-retest r = 0.69 at 3 months; construct
  validity with Connor-Davidson, ego-resiliency, optimism,
  social support, active coping, and — inverse — anxiety,
  depression, perceived stress, negative affect.)
- Smith BW, Epstein EM, Ortiz JA, Christopher PJ, Tooley EM (2013).
  *The foundations of resilience: What are the critical resources
  for bouncing back from stress?*  In: Prince-Embury S, Saklofske
  DH (eds), Resilience in Children, Adolescents, and Adults.
  Springer, New York.  (BRS / CD-RISC construct differentiation;
  resource-vs-outcome framing.)
- Windle G, Bennett KM, Noyes J (2011).  *A methodological review
  of resilience measurement scales.*  Health and Quality of Life
  Outcomes 9:8.  (Systematic psychometric review of 15 resilience
  scales — BRS rated highest on content / construct validity
  among brief instruments; CD-RISC rated highest among
  comprehensive instruments.  Recommendation: pair both for
  complete-coverage resilience assessment.)
- Connor KM, Davidson JRT (2003).  *Development of a new
  resilience scale: The Connor-Davidson Resilience Scale (CD-
  RISC).*  Depression and Anxiety 18(2):76-82.  (CD-RISC origin;
  agentic-resilience framing — the instrument BRS deliberately
  contrasts with.)
- Campbell-Sills L, Stein MB (2007).  *Psychometric analysis and
  refinement of the Connor-Davidson Resilience Scale (CD-RISC):
  Validation of a 10-item measure of resilience.*  Journal of
  Traumatic Stress 20(6):1019-1028.  (CD-RISC-10 derivation
  the platform ships; necessary for the BRS-vs-CD-RISC-10
  pairing rationale.)
- Lazarus RS (1993).  *From psychological stress to the emotions:
  A history of changing outlooks.*  Annual Review of Psychology
  44:1-21.  (Stress-recovery framing; ecological-resilience
  construct precedes Smith 2008 instrumentation.)
- Hayes SC, Strosahl KD, Wilson KG (2012).  *Acceptance and
  Commitment Therapy: The process and practice of mindful
  change* (2nd ed.).  Guilford Press, New York.  (Values-based
  committed action as the deployment-gap intervention for the
  high-CD-RISC / low-BRS discrepancy profile.)
- Martell CR, Dimidjian S, Herman-Dunn R (2010).  *Behavioral
  Activation for Depression: A Clinician's Guide.*  Guilford
  Press, New York.  (Behavioral-activation framing for the
  resource-outcome decoupling case.)
- Beck AT (1967).  *Depression: Clinical, Experimental, and
  Theoretical Aspects.*  Harper & Row, New York.  (Cognitive
  triad as the mechanism interfering with deployment of
  existing resilience resources.)
- Chmitorz A, Kunzler A, Helmreich I, Tüscher O, Kalisch R,
  Kubiak T, Wessa M, Lieb K (2018).  *Intervention studies to
  foster resilience — A systematic review and proposal for a
  resilience framework in future intervention studies.*
  Clinical Psychology Review 59:78-100.  (Intervention-outcome
  evidence for BRS-measured resilience gains; framing for
  within-subject recovery-trajectory use.)
- Kunzler AM, Chmitorz A, Bagusat C, Kaluza AJ, Hoffmann I,
  Schäfer M, Quiring O, Rigotti T, Kalisch R, Tüscher O,
  Franke AG, van Dick R, Lieb K (2018).  *Construct validity
  and population-based norms of the German Brief Resilience
  Scale (BRS).*  European Journal of Health Psychology 25(3):
  107-117.  (Multi-locale norm data; framework for non-EN
  locale validation — supports the platform's no-MT rule for
  clinical instruments.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.  (RCI framework used with BRS
  test-retest SD for longitudinal change detection.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "brs-1.0.0"
ITEM_COUNT = 6
ITEM_MIN, ITEM_MAX = 1, 5


# Per Smith 2008 §2.1 Table 1: items 2, 4, 6 are the negatively-
# worded items ("It is hard for me to snap back..." / "It is hard
# for me to bounce back..." / "I tend to take a long time...").
# These three items express the ABSENCE of resilience; they are
# flipped before summing so each post-flip value contributes in
# the resilience-presence direction.  Changing this set is a
# clinical decision — Smith 2008 derived the three-positive /
# three-negative structure via EFA precisely to control response-
# set acquiescence bias.
BRS_REVERSE_ITEMS: tuple[int, ...] = (2, 4, 6)


# Published severity (resilience) bands per Smith 2008 §3.3
# conceptual-mean framework, mapped to the integer-sum envelope
# the platform uses uniformly across banded instruments.  The
# published bands are mean-based on 1.00-5.00 (low 1.00-2.99,
# normal 3.00-4.30, high 4.31-5.00); mapped onto sum 6-30 these
# translate to:
#
#   Low        mean  1.00-2.99  ->  sum  6-17
#   Normal     mean  3.00-4.30  ->  sum 18-25
#   High       mean  4.31-5.00  ->  sum 26-30
#
# DIRECTION: HIGHER SUM = MORE RESILIENT.  This is the OPPOSITE
# of PHQ-9 / GAD-7 / PGSI / AUDIT where higher = worse.  Matches
# WHO-5 / MAAS / CD-RISC-10 higher-is-better convention.
#
# Tuple pairs are (upper-inclusive bound, band label) — classify
# picks the FIRST label whose bound >= total.  Changing these
# values is a clinical decision.
BRS_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (17, "low"),
    (25, "normal"),
    (30, "high"),
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["low", "normal", "high"]


@dataclass(frozen=True)
class BrsResult:
    """Typed BRS output.

    Fields:
    - ``total``: 6-30 integer sum of the 6 POST-FLIP items (items
      2, 4, 6 reverse-keyed before summing).  HIGHER = MORE
      RESILIENT.  Flows into the FHIR Observation's
      ``valueInteger``.
    - ``severity``: one of three Smith 2008 bands ("low" /
      "normal" / "high").  Despite the ``severity`` field name
      (retained for API uniformity across instruments), this is
      a resilience level — "high" is the clinically-positive
      outcome.
    - ``items``: verbatim 6-tuple of RAW PRE-FLIP Likert responses
      in presentation order, pinned for auditability and FHIR
      export.  NOT post-flip values — audit invariance per the
      TAS-20 / PSWQ / LOT-R contract.

    Deliberately-absent fields:
    - No ``positive_screen`` / ``cutoff_used`` — BRS is banded
      (3 bands), not a binary screen.
    - No ``subscales`` — BRS is single-factor by construction
      (Smith 2008 §3.2 EFA).  Surfacing positive-item /
      negative-item sums would contradict the factor derivation.
    - No ``requires_t3`` field — no item probes suicidality,
      self-harm, or acute-risk behavior.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    """Map a 6-30 post-flip total to a Smith 2008 resilience band."""
    for upper, label in BRS_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    # Unreachable — classified list ends at 30.
    raise InvalidResponseError(f"total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item.

    ``index_1`` is the 1-indexed item number (1-6) so error messages
    name the item a clinician would recognize from the Smith 2008
    administration order.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values are
    rejected before the int check because Python's ``bool is int``
    coercion would silently accept ``True`` / ``False`` as item
    responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"BRS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"BRS item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _flip_if_reverse(index_1: int, value: int) -> int:
    """Return the post-flip value for item ``index_1``.

    Reuses the arithmetic-reflection idiom from TAS-20 / PSWQ /
    LOT-R:  ``flipped = ITEM_MIN + ITEM_MAX - raw`` = ``6 - raw``
    on the 1-5 envelope.  Non-reverse items pass through unchanged.

    For BRS items 2, 4, 6 (negatively-worded "hard to bounce
    back..." items) a raw 5 ("strongly agree: it is hard") becomes
    a post-flip 1 (low resilience contribution), and a raw 1
    ("strongly disagree: it is hard") becomes a post-flip 5 (high
    resilience contribution).  This makes every post-flip item
    contribute in the resilience-PRESENCE direction.
    """
    if index_1 in BRS_REVERSE_ITEMS:
        return (ITEM_MIN + ITEM_MAX) - value
    return value


def score_brs(raw_items: Sequence[int]) -> BrsResult:
    """Score a BRS response set.

    Inputs:
    - ``raw_items``: 6 items, each 1-5 Likert (1 = "strongly
      disagree", 5 = "strongly agree").  Reverse-keying on items
      2, 4, 6 is applied internally before summing — callers
      should NOT pre-flip the raw values.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 6).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Post-flip total (6-30).  HIGHER = MORE RESILIENT.
    - Smith 2008 band (low / normal / high) via integer-sum
      thresholds mapped from the published mean-based bands.

    The ``items`` field of the result preserves the PATIENT'S raw
    pre-flip responses — audit-trail invariant, matching the
    TAS-20 / PSWQ / LOT-R contract.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"BRS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    validated_raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    post_flip = tuple(
        _flip_if_reverse(index_1=i + 1, value=v)
        for i, v in enumerate(validated_raw)
    )
    total = sum(post_flip)
    severity = _classify(total)

    return BrsResult(
        total=total,
        severity=severity,
        items=validated_raw,
    )


__all__ = [
    "BRS_REVERSE_ITEMS",
    "BRS_SEVERITY_THRESHOLDS",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "BrsResult",
    "InvalidResponseError",
    "Severity",
    "score_brs",
]
