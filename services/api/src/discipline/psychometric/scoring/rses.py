"""RSES — Rosenberg Self-Esteem Scale (Rosenberg 1965).

The Rosenberg Self-Esteem Scale is a 10-item self-report measure
of global self-esteem and is the single most widely-used
psychological instrument in the behavioral-science literature
(>100,000 citations per Google Scholar).  Morris Rosenberg
introduced it in *Society and the Adolescent Self-Image*
(Princeton University Press 1965) and it has been cross-
culturally validated in >50 languages (Schmitt & Allik 2005
n = 16,998 across 53 nations, factorial invariance confirmed).
The RSES's longevity, brevity, and robustness to cultural
context make it the standard anchor for any platform that needs
to track self-concept.

Clinical relevance to the Discipline OS platform:

RSES fills the platform's **self-concept dimension gap**.
Every prior instrument targets a specific syndrome (depression
/ anxiety / PTSD / OCD / eating disorder / etc), a craving-or-
impulse construct (PACS / VAS / BIS-11), an affect dimension
(PANAS-10), a regulatory construct (DERS-16 / AAQ-II / MAAS /
TAS-20), or a resilience / recovery construct (CD-RISC-10 /
BRS / LOT-R).  None measure GLOBAL SELF-ESTEEM — the
evaluative attitude one holds toward oneself.

Self-concept is clinically load-bearing for relapse prevention
specifically via the **abstinence-violation effect** (AVE;
Marlatt 1985 Relapse Prevention pp. 37-44; Marlatt 2005
Relapse Prevention 2nd ed ch 1):

1. **AVE mechanism.**  A single lapse triggers a cognitive-
   attributional cascade: internal ("I am the kind of person
   who fails"), stable ("I will always fail"), global ("This
   affects everything, not just this one incident").  Low self-
   esteem is both the substrate for this attributional style
   (Rosenberg & Pearlin 1978) and the outcome it produces.
   The AVE cycle is self-reinforcing.
2. **Intervention matching.**  Patients with low RSES respond
   to self-compassion-based interventions (Neff 2003; Gilbert
   2010 Compassion-Focused Therapy) and self-efficacy-
   strengthening work (Bandura 1977; Witkiewitz 2007 CBT for
   substance use).  Patients with high RSES in the context of
   persistent substance use suggest a different clinical
   picture — possibly narcissistic / externalizing profile
   requiring DBT-adapted framing (Linehan 2015).
3. **Trajectory monitoring.**  Self-esteem is state-sensitive
   (Kernis 2005 Handbook of Self and Identity) and responds
   to intervention within weeks.  RSES paired with Jacobson-
   Truax RCI (Jacobson & Truax 1991) gives an early-signal
   measure of whether intervention is landing or the AVE cycle
   is dominant.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Rosenberg 1965.**  No paraphrase.
   No machine translation.  Schmitt & Allik 2005 §2 validated
   translated versions using forward-backward protocols across
   53 languages; machine translation invalidates the cross-
   cultural measurement invariance (CLAUDE.md rule 8).
2. **Latin digits for the RSES total** at render time
   (CLAUDE.md rule 9).
3. **No T3 triggering.**  RSES measures self-esteem, not
   suicidality.  Item 9 "All in all, I am inclined to feel
   that I am a failure" is a SELF-CONCEPT item, NOT a
   worthlessness-suicidal-intent item.  The wording probes
   global self-evaluation, not active ideation.  Item 6 "I
   certainly feel useless at times" is similarly a self-
   concept item per Rosenberg 1965 derivation.  Acute-risk
   screening stays on C-SSRS / PHQ-9 item 9.  A clinician
   reviewing a low RSES should pair it with a safety screen,
   but the RSES itself does not carry an acute-risk signal.

Scoring semantics:

- 10 items in Rosenberg 1965 published order.
- Each item is 0-3 Likert ("strongly disagree" / "disagree" /
  "agree" / "strongly agree"; standard modern 0-3 anchoring
  per Gray-Little 1997 meta-analysis §1).
- Items 1, 3, 4, 7, 10 are POSITIVELY-KEYED (worded positively;
  "strongly agree" = high self-esteem).
- Items 2, 5, 6, 8, 9 are REVERSE-KEYED (worded negatively;
  "strongly agree" = LOW self-esteem).  Reverse-keyed items
  are re-scored via (ITEM_MIN + ITEM_MAX) - raw = 3 - raw at
  scoring time.
- Total = sum of post-flip values, 0-30.
- HIGHER = MORE self-esteem.  Uniform higher-is-better
  direction (WHO-5 / BRS / PANAS-10 total / LOT-R / MAAS /
  CD-RISC-10 / Ruler / DTCQ-8).

Direction note:

RSES inherits the PGSI / BRS / TAS-20 / PSWQ / LOT-R reverse-
keying idiom used throughout the platform.  The ``items``
field stores RAW pre-flip responses (audit invariance — a
FHIR re-export or clinician review needs to see the exact
ordinal response the patient gave, not the post-processed
value).  Post-flip values are used only for total computation.

Severity:

- NO published clinical cutpoints.  Rosenberg 1965 did not
  propose severity bands.  Gray-Little 1997 meta-analysis
  §3 confirmed the unidimensional structure but also did
  NOT publish bands.  Schmitt & Allik 2005 reported n = 16,998
  cross-national means (grand M = 21.3 SD = 5.5 on 0-30
  scale) as a descriptive distribution, NOT a clinical
  cutoff.  The severity sentinel is "continuous"; the
  trajectory layer applies Jacobson-Truax RCI on total
  directly.  Hand-rolling severity bands violates CLAUDE.md
  (no unvalidated thresholds).

Citations:

- Rosenberg M (1965).  *Society and the Adolescent Self-
  Image.*  Princeton University Press, Princeton NJ.  (Canonical
  derivation; n = 5,024 high-school students in New York
  State; unidimensional self-esteem construct.)
- Rosenberg M (1979).  *Conceiving the Self.*  Basic Books,
  New York.  (Expanded theoretical framework; construct
  validity across adult samples.)
- Gray-Little B, Williams VSL, Hancock TD (1997).  *An item
  response theory analysis of the Rosenberg Self-Esteem Scale.*
  Personality and Social Psychology Bulletin 23(5):443-451.
  (IRT meta-analysis confirming unidimensional structure;
  reference for modern 0-3 anchoring convention.)
- Robins RW, Hendin HM, Trzesniewski KH (2001).  *Measuring
  global self-esteem: Construct validation of a single-item
  measure and the Rosenberg Self-Esteem Scale.*  Personality
  and Social Psychology Bulletin 27(2):151-161.  (n = 503
  convergent validity with single-item SISE r = 0.74-0.80.)
- Schmitt DP, Allik J (2005).  *Simultaneous administration
  of the Rosenberg Self-Esteem Scale in 53 nations: Exploring
  the universal and culture-specific features of global self-
  esteem.*  Journal of Personality and Social Psychology
  89(4):623-642.  (Cross-national n = 16,998; factorial
  invariance across cultures; basis for the platform's
  cross-cultural deployment claim.)
- Rosenberg M, Pearlin LI (1978).  *Social class and self-
  esteem among children and adults.*  American Journal of
  Sociology 84(1):53-77.  (Social-context moderators of
  self-esteem; relevant to the platform's population-
  stratification analytics.)
- Marlatt GA, Gordon JR (1985).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive
  Behaviors.*  Guilford Press, New York.  (The canonical
  abstinence-violation effect framework; self-esteem as
  mediator.  Pp. 37-44 explicitly describe the AVE
  attributional cascade.)
- Marlatt GA, Donovan DM, eds (2005).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive
  Behaviors, 2nd edition.*  Guilford Press, New York.
  (Updated AVE framework; Ch 1 Witkiewitz & Marlatt
  contemporary formulation.)
- Witkiewitz K, Marlatt GA (2007).  *Modeling the complexity
  of post-treatment drinking: It's a rocky road to relapse.*
  Clinical Psychology Review 27(6):724-738.  (AVE mediator
  analysis; self-efficacy pathway.)
- Neff KD (2003).  *Self-compassion: An alternative
  conceptualization of a healthy attitude toward oneself.*
  Self and Identity 2(2):85-101.  (Self-compassion vs self-
  esteem — for the intervention-matching discussion.)
- Kernis MH (2005).  *Measuring self-esteem in context: The
  importance of stability of self-esteem in psychological
  functioning.*  Journal of Personality 73(6):1569-1605.
  (State vs trait self-esteem; basis for RCI-compatible
  trajectory claim.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and
  Clinical Psychology 59(1):12-19.  (Reliable Change Index
  framework; applied to RSES total in the trajectory layer.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "rses-1.0.0"
ITEM_COUNT = 10
ITEM_MIN, ITEM_MAX = 0, 3


# Rosenberg 1965 reverse-keyed items (1-indexed).  These are the
# five items with NEGATIVE wording ("At times I think I am no
# good at all", "I feel I do not have much to be proud of", "I
# certainly feel useless at times", "I wish I could have more
# respect for myself", "All in all, I am inclined to feel that I
# am a failure") — for these, a "strongly agree" response
# indicates LOW self-esteem, so the raw response is reflected
# via (ITEM_MIN + ITEM_MAX) - raw = 3 - raw before summing.
# Changing this tuple invalidates Rosenberg 1965 / Gray-Little
# 1997 factor-analytic derivation.
RSES_REVERSE_ITEMS: tuple[int, ...] = (2, 5, 6, 8, 9)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class RsesResult:
    """Typed RSES output.

    Fields:
    - ``total``: 0-30 sum of post-flip item values.  HIGHER =
      MORE self-esteem (higher-is-better direction, uniform
      with WHO-5 / BRS / PANAS-10 total / LOT-R / MAAS / CD-
      RISC-10 / Ruler / DTCQ-8).
    - ``severity``: literal ``"continuous"`` sentinel.  Rosenberg
      1965 did not publish clinical cutpoints; Gray-Little 1997
      meta-analysis did not publish bands either.  The trajectory
      layer applies Jacobson-Truax RCI on the total directly.
    - ``items``: verbatim 10-tuple of RAW pre-flip 0-3
      responses in Rosenberg 1965 administration order.
      Preserved raw (not post-flip) for audit invariance — a
      FHIR re-export or clinician review must see the exact
      ordinal response, not the post-processed value.

    Deliberately-absent fields:
    - No ``subscales`` — Gray-Little 1997 IRT confirmed
      unidimensional factor structure.  Proposals for a two-
      factor (positive / negative) structure (e.g. Tomas 1999)
      are method-artifact rather than substantive; Marsh 1996
      argued the apparent two factors reflect positive-
      negative wording bias, not substantive self-esteem
      dimensions.  Platform treats RSES as unidimensional.
    - No ``positive_screen`` / ``cutoff_used`` — RSES is not a
      screen.
    - No ``requires_t3`` — no item probes suicidality per
      Rosenberg 1965 derivation.  Item 9 ("inclined to feel
      that I am a failure") is a self-concept item, NOT an
      ideation item.  Acute-risk stays on C-SSRS / PHQ-9
      item 9.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"RSES item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"RSES item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _apply_reverse(index_1: int, value: int) -> int:
    """Apply reverse-keying to positions in ``RSES_REVERSE_ITEMS``.

    The Rosenberg 1965 reverse-keyed items have NEGATIVE wording
    — "strongly agree" = LOW self-esteem.  The transform
    (ITEM_MIN + ITEM_MAX) - raw = 3 - raw inverts the scale so
    that higher post-flip values consistently mean MORE self-
    esteem across all 10 items.
    """
    if index_1 in RSES_REVERSE_ITEMS:
        return (ITEM_MIN + ITEM_MAX) - value
    return value


def score_rses(raw_items: Sequence[int]) -> RsesResult:
    """Score an RSES response set.

    Inputs:
    - ``raw_items``: 10 items, each 0-3 Likert (0 = "strongly
      disagree", 3 = "strongly agree"), in Rosenberg 1965
      published administration order:
        1.  On the whole, I am satisfied with myself.          [+]
        2.  At times I think I am no good at all.              [R]
        3.  I feel that I have a number of good qualities.     [+]
        4.  I am able to do things as well as most other
            people.                                            [+]
        5.  I feel I do not have much to be proud of.          [R]
        6.  I certainly feel useless at times.                 [R]
        7.  I feel that I'm a person of worth, at least on
            an equal plane with others.                        [+]
        8.  I wish I could have more respect for myself.       [R]
        9.  All in all, I am inclined to feel that I am a
            failure.                                           [R]
        10. I take a positive attitude toward myself.          [+]
      [+] = positively-keyed, [R] = reverse-keyed.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - For reverse-keyed items (2, 5, 6, 8, 9): post-flip =
      3 - raw.  For positively-keyed items (1, 3, 4, 7, 10):
      post-flip = raw.
    - ``total``: sum of post-flip values, 0-30.

    The ``items`` field in the result preserves RAW pre-flip
    responses in administration order for audit and FHIR-export
    reproducibility.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"RSES requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(
        _apply_reverse(index_1=i + 1, value=v)
        for i, v in enumerate(items)
    )

    return RsesResult(
        total=total,
        severity="continuous",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "RSES_REVERSE_ITEMS",
    "InvalidResponseError",
    "RsesResult",
    "Severity",
    "score_rses",
]
