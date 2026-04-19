"""FNE-B — Brief Fear of Negative Evaluation Scale (Leary 1983).

The Brief Fear of Negative Evaluation Scale (often abbreviated
BFNE or FNE-B) is Mark R. Leary's 1983 12-item short-form
derivation of Watson & Friend's (1969) 30-item true/false Fear
of Negative Evaluation Scale.  The derivation is published in
Leary MR (1983) "A brief version of the Fear of Negative
Evaluation Scale", Personality and Social Psychology Bulletin
9(3):371-375.  Leary's derivation used factor analysis to
retain the 12 items with the highest loadings on the FNE
single factor, converted from the original true/false format
to a 5-point Likert scale (1 = "Not at all characteristic of
me" to 5 = "Extremely characteristic of me") to increase
score variance, and demonstrated r = 0.96 with the full
Watson & Friend 1969 FNE.  The FNE-B has since been validated
across clinical social-anxiety samples (Collins, Westra,
Dozois & Stewart 2005), student samples (Weeks 2005), and
was further refined into the BFNE-II by Carleton, Collimore
& Asmundson 2007 (dropping the 4 reverse-keyed items whose
reliability was questioned).  This module implements the
ORIGINAL Leary 1983 12-item BFNE, which remains the most
widely-cited version in clinical research.

Clinical relevance to the Discipline OS platform:

FNE-B fills the platform's **social-evaluation anxiety gap**.
Existing anxiety coverage captures general and state
anxiety:

- GAD-7 (Spitzer 2006): generalized anxiety disorder,
  14-day window, trait-ish.
- GAD-2 (Kroenke 2007): GAD-7 brief screen.
- OASIS (Norman 2006): overall anxiety severity, 7-day
  window.
- STAI-6 (Marteau 1992): momentary state anxiety.
- AAQ-II (Bond 2011): experiential-avoidance trait.
- PSWQ (Meyer 1990): pathological worry.

None isolate **socially-evaluative anxiety** — the specific
fear-of-judgment cognitive-affective pattern that Leary's
1983 scale measures.  Social-evaluation anxiety is
mechanistically distinct from generalized anxiety:

1. **Alcohol-as-social-lubrication relapse.**  Marlatt 1985
   Table 4.1 documented interpersonal conflict and social
   pressure as the second-largest proximal relapse category
   (after negative emotional states).  Patients who drink
   to manage social-evaluation anxiety have a specific
   cue-reactivity profile — the cue is a social-evaluative
   situation (meeting new people, public speaking, dating
   interactions), and the avoidance response is alcohol
   consumption.  FNE-B at baseline lets the intervention
   engine predict which AUDIT-positive patients will
   benefit most from social-anxiety-focused relapse-
   prevention (assertiveness training, social-skills
   exposure, Heimberg 1995 CBGT) versus general craving-
   management tools.
2. **Digital-avoidance behavioral substitution.**  Within
   the platform's digital-behavior scope, social-evaluation
   anxiety drives specific patterns: social-media
   lurking without posting, delayed messaging responses,
   video-call avoidance, gaming as parasocial substitute.
   FNE-B scores at clinical range (Leary 1983 mean ~38 in
   student samples; Collins 2005 reported >= 49 in social-
   phobic samples) predict these substitution patterns,
   informing the bandit's intervention selection toward
   social-exposure rather than general-craving-management
   scripts.
3. **Differential relapse trajectory.**  Per Hofmann 2007
   meta-analysis, social-anxiety disorder has a
   characteristic treatment-response profile (cognitive
   restructuring + exposure) distinct from generalized
   anxiety (behavioral activation + acceptance) or panic
   (interoceptive exposure).  FNE-B score discriminates
   these treatment-response targets at the intake-
   classification layer, where no generalized-anxiety
   instrument can.

Scoring:

- 12 items, 5-point Likert (1 = "Not at all characteristic
  of me", 5 = "Extremely characteristic of me").
- Items (Leary 1983 Appendix with REVERSE-keyed positions):
    1. I worry about what other people will think of me
       even when I know it doesn't make any difference.
    2. I am unconcerned even if I know people are forming
       an unfavorable impression of me.  (REVERSE)
    3. I am frequently afraid of other people noticing my
       shortcomings.
    4. I rarely worry about what kind of impression I am
       making on someone.  (REVERSE)
    5. I am afraid that others will not approve of me.
    6. I am afraid that people will find fault with me.
    7. Other people's opinions of me do not bother me.
       (REVERSE)
    8. When I am talking to someone, I worry about what
       they may be thinking about me.
    9. I am usually worried about what kind of impression
       I make.
   10. If I know someone is judging me, it has little
       effect on me.  (REVERSE)
   11. Sometimes I think I am too concerned with what
       other people think of me.
   12. I often worry that I will say or do the wrong
       things.
- Post-flip = (ITEM_MIN + ITEM_MAX) - raw = 6 - raw at
  positions 2, 4, 7, 10.  Non-reverse positions pass
  through raw.
- Total: sum of post-flip items, range 12-60.  HIGHER =
  MORE fear of negative evaluation (lower-is-better
  direction — uniform with PHQ-9 / GAD-7 / AUDIT / PSS-10
  / PGSI / SHAPS / STAI-6; OPPOSITE of WHO-5 / BRS / RSES
  / FFMQ-15 / MAAS / LOT-R).

Acquiescence-bias signature:

Leary 1983's 8-straight / 4-reverse ASYMMETRIC split (not
the symmetric 5/5 of RSES or 3/3 of STAI-6) means uniform
response vectors do NOT land at the midpoint:

- Raw all-1s: 8 straight items contribute 1 each (8); 4
  reverse items flip 1->5 each (20); total = 28.
- Raw all-5s: 8 straight items contribute 5 each (40); 4
  reverse items flip 5->1 each (4); total = 44.
- Separation: |44 - 28| = 16.

This is the Leary 1983 wire-level signature (stronger
acquiescence-sensitivity than STAI-6 or RSES; weaker than
a fully-straight BFNE-II).  Changing ``FNEB_REVERSE_ITEMS``
invalidates this signature and the 0.96 correlation with
Watson & Friend 1969 FNE.

No severity bands:

Leary 1983 did NOT publish clinical cutpoints.  Various
secondary-literature cutoffs exist (e.g., Collins 2005
used >= 49 as "high social anxiety" in a clinical
comparison; Carleton 2007 suggested ~45 for the BFNE-II),
but no derivation-source anchor pins a specific threshold.
Per CLAUDE.md "no hand-rolled severity thresholds" rule,
the platform emits ``severity="continuous"`` and defers
clinical-significance to Jacobson-Truax RCI at the
trajectory layer.  Same contract as OASIS / K10 / RSES /
PANAS-10 / FFMQ-15 / STAI-6.

No T3 gating:

FNE-B has NO ideation item.  The 12 items probe social-
evaluative concern (opinions, impressions, judgment,
approval) — affective concerns about other people's views
of self, NOT lethality or self-harm intent.  Item 12 "I
often worry that I will say or do the wrong things" is
conversational-performance concern, NOT suicidal ideation.
Acute-risk screening stays on C-SSRS / PHQ-9 item 9.

References:
- Leary MR (1983).  *A brief version of the Fear of
  Negative Evaluation Scale.*  Personality and Social
  Psychology Bulletin 9(3):371-375.  (Canonical 12-item
  derivation from Watson & Friend 1969 FNE; r = 0.96
  with the original 30-item scale.  Reverse positions
  2, 4, 7, 10 pinned in Table 1.)
- Watson D, Friend R (1969).  *Measurement of social-
  evaluative anxiety.*  Journal of Consulting and
  Clinical Psychology 33(4):448-457.  (Original 30-item
  true/false FNE — source scale from which Leary 1983
  derived the 12-item Likert short form.)
- Collins KA, Westra HA, Dozois DJA, Stewart SH (2005).
  *The validity of the brief version of the Fear of
  Negative Evaluation Scale.*  Journal of Anxiety
  Disorders 19(3):345-359.  (Clinical-sample validation;
  reported >= 49 as a clinical-range indicator in a
  social-phobic sample — secondary-literature cutoff,
  not pinned per CLAUDE.md.)
- Weeks JW, Heimberg RG, Fresco DM, Hart TA, Turk CL,
  Schneier FR, Liebowitz MR (2005).  *Empirical
  validation and psychometric evaluation of the Brief
  Fear of Negative Evaluation Scale in patients with
  social anxiety disorder.*  Psychological Assessment
  17(2):179-190.  (Student-sample and social-anxiety-
  disorder-patient validation; informed the BFNE-II
  straight-items-only refinement.)
- Carleton RN, Collimore KC, Asmundson GJG (2007).
  *Social anxiety and fear of negative evaluation:
  Construct validity of the BFNE-II.*  Journal of
  Anxiety Disorders 21(1):131-141.  (BFNE-II 8-item
  straight-worded revision dropping the 4 reverse-
  keyed items per reliability concerns; this module
  implements the ORIGINAL Leary 1983 12-item version,
  not BFNE-II.)
- Heimberg RG, Becker RE (1995).  *Cognitive-behavioral
  group therapy for social phobia: Basic mechanisms and
  clinical strategies.*  Guilford Press.  (CBGT
  protocol; FNE-B is a canonical outcome measure for
  CBGT efficacy trials, and the intervention-selection
  signal referenced in §1 above.)
- Hofmann SG, Smits JAJ (2008).  *Cognitive-behavioral
  therapy for adult anxiety disorders: A meta-analysis
  of randomized placebo-controlled trials.*  Journal of
  Clinical Psychiatry 69(4):621-632.  (Meta-analytic
  evidence for differential treatment response across
  anxiety subtypes — informs the §3 differential-
  intervention-matching argument.)
- Marlatt GA, Gordon JR (1985).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive
  Behaviors.*  Guilford Press.  (Interpersonal conflict
  / social pressure as second-largest proximal relapse
  category — Table 4.1, pp. 98-102.  Direct rationale
  for the §1 social-lubrication-relapse use case.)
- Jacobson NS, Truax P (1991).  *Clinical significance:
  A statistical approach to defining meaningful change
  in psychotherapy research.*  Journal of Consulting
  and Clinical Psychology 59(1):12-19.  (RCI applied to
  FNE-B raw total in the trajectory layer.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "fneb-1.0.0"
ITEM_COUNT = 12
ITEM_MIN, ITEM_MAX = 1, 5


# Leary 1983 reverse-keyed items (1-indexed).  These are the four
# positively-worded items asserting LACK of social-evaluation
# concern: position 2 ("I am unconcerned..."), position 4 ("I
# rarely worry..."), position 7 ("opinions of me do not bother
# me"), position 10 ("If I know someone is judging me, it has
# little effect on me").  Remaining 8 items (1, 3, 5, 6, 8, 9,
# 11, 12) are negatively worded and pass through raw.  Post-flip
# = (ITEM_MIN + ITEM_MAX) - raw = 6 - raw.  Changing this tuple
# invalidates Leary 1983's factor structure and breaks the
# r = 0.96 equivalence with the Watson & Friend 1969 FNE.
FNEB_REVERSE_ITEMS: tuple[int, ...] = (2, 4, 7, 10)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class FnebResult:
    """Typed FNE-B output.

    Fields:
    - ``total``: 12-60 sum of post-flip item values.  HIGHER =
      MORE fear of negative evaluation (lower-is-better
      direction — uniform with PHQ-9 / GAD-7 / AUDIT / PSS-10 /
      PGSI / SHAPS / STAI-6).
    - ``severity``: literal ``"continuous"`` sentinel.  Leary
      1983 did not publish clinical cutpoints; Collins 2005
      >= 49 cutoff is secondary literature and not pinned here
      per CLAUDE.md.
    - ``items``: verbatim 12-tuple of RAW pre-flip 1-5
      responses in Leary 1983 administration order.  Raw
      preserved for audit invariance.

    Deliberately-absent fields:
    - No ``subscales`` — FNE-B is a single-factor instrument
      per Leary 1983 factor-analytic derivation, confirmed by
      Rodebaugh 2004 CFA and Weeks 2005.
    - No ``positive_screen`` / ``cutoff_used`` — FNE-B is not
      a screen.
    - No ``requires_t3`` — no item probes suicidality.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"FNE-B item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"FNE-B item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _apply_reverse_keying(
    raw_items: tuple[int, ...], reverse_positions_1: tuple[int, ...]
) -> tuple[int, ...]:
    """Return a new tuple with reverse-keyed positions flipped via
    ``(ITEM_MIN + ITEM_MAX) - raw``.  Non-reverse positions copy
    unchanged."""
    reverse_set = frozenset(reverse_positions_1)
    flipped: list[int] = []
    for i, raw in enumerate(raw_items):
        position_1 = i + 1
        if position_1 in reverse_set:
            flipped.append((ITEM_MIN + ITEM_MAX) - raw)
        else:
            flipped.append(raw)
    return tuple(flipped)


def score_fneb(raw_items: Sequence[int]) -> FnebResult:
    """Score an FNE-B response set.

    Inputs:
    - ``raw_items``: 12 items, each 1-5 Likert (1 = "Not at all
      characteristic of me", 5 = "Extremely characteristic of
      me"), in Leary 1983 administration order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 12).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Post-flip sum, range 12-60.  ``items`` preserves RAW pre-
      flip for audit and FHIR R4 export.

    Changing ``FNEB_REVERSE_ITEMS`` invalidates Leary 1983
    factor structure and breaks the r = 0.96 equivalence with
    the Watson & Friend 1969 FNE.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"FNE-B requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    post_flip = _apply_reverse_keying(raw, FNEB_REVERSE_ITEMS)
    total = sum(post_flip)

    return FnebResult(
        total=total,
        severity="continuous",
        items=raw,
    )


__all__ = [
    "FNEB_REVERSE_ITEMS",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "FnebResult",
    "Severity",
    "score_fneb",
]
