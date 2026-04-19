"""Psychometric HTTP surface — PHQ-9, GAD-7, WHO-5, AUDIT, AUDIT-C,
C-SSRS, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI, PCL-5, OCI-R, PHQ-15,
PACS, BIS-11, Craving VAS, Readiness Ruler, DTCQ-8, URICA, PHQ-2,
GAD-2, OASIS, K10, SDS, K6, DUDIT, ASRS-6, AAQ-II, WSAS, DERS-16,
CD-RISC-10, PSWQ, LOT-R, TAS-20.

Single ``POST /v1/assessments`` endpoint dispatches by ``instrument``
key.  Each instrument has its own validated item count and item-value
range; the dispatch layer picks the right scorer and renders a unified
response shape.

Response shape additions over the original phq9/gad7-only design:
- ``index``: the WHO-5 Index value (raw_total × 4).  Optional because
  no other instrument uses an index conversion.  Clients reading WHO-5
  scores MUST display ``index``, not ``total`` — the published cutoffs
  are on the index scale.
- ``cutoff_used`` + ``positive_screen``: AUDIT-C-only fields surfacing
  the sex-aware cutoff that was applied.  Clients render the cutoff
  in the result UI ("positive at ≥ N").  ``positive_screen`` is also
  reused by MDQ (the three-gate Hirschfeld 2000 screen), but MDQ does
  not surface a ``cutoff_used`` — its gate is categorical (≥ 7 items +
  concurrent + moderate/serious impairment), not an ordinal cutoff.
- ``triggering_items``: C-SSRS-only — the 1-indexed item numbers that
  drove the risk band.  Clinician-facing UI renders these as the
  "these answers escalated this screen" audit trail.
- ``instrument_version``: pinned version string for downstream storage
  and FHIR Observation export.

Idempotency:
- The ``Idempotency-Key`` header is required.  Re-sending the same key
  with the same body yields the same response (the route is currently
  stateless — repository wiring to enforce this lands when the
  AssessmentRepository ships).

Safety routing:
- PHQ-9 runs through the item-9 classifier (single item positive →
  T3 check per Kroenke 2001).
- C-SSRS runs through its own triage rules: items 4/5 positive OR
  item 6 positive with ``behavior_within_3mo=True`` → T3.
- GAD-7, WHO-5, AUDIT, AUDIT-C, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI,
  PCL-5, OCI-R, PHQ-15, PACS, BIS-11, Craving VAS, Readiness Ruler,
  DTCQ-8, URICA, PHQ-2, GAD-2, OASIS, K10, SDS, K6, DUDIT, ASRS-6, AAQ-II, WSAS, DERS-16, CD-RISC-10, PSWQ, LOT-R, TAS-20 have no safety items —
  ``requires_t3`` is always False for these instruments.  WHO-5 ``depression_screen``
  band is *not* a T3 trigger; T3 is reserved for active suicidality
  per Docs/Whitepapers/04_Safety_Framework.md §T3.  A positive MDQ
  screen is a referral signal for a bipolar-spectrum structured
  interview, not a crisis signal — see ``scoring/mdq.py`` module
  docstring.  A positive PC-PTSD-5 is a referral signal for trauma-
  informed care (CAPS-5 / PCL-5 structured interview, EMDR / TF-CBT
  intake), not a crisis signal — see ``scoring/pcptsd5.py``.  A
  severe ISI result is a referral signal for CBT-I / sleep medicine,
  not a crisis signal — see ``scoring/isi.py``.  A positive PCL-5
  screen is the structured follow-up to PC-PTSD-5 — referral for
  trauma-focused therapy (PE / CPT / EMDR), not a crisis signal —
  see ``scoring/pcl5.py``.  A positive OCI-R screen routes to
  subtype-appropriate OCD therapy (ERP / CBT-H / thought-action-
  fusion work) — not a crisis signal — see ``scoring/ocir.py``.
  A high PHQ-15 score is a somatization signal routing to
  interoceptive-exposure / somatic-awareness interventions —
  item 6 (chest pain) and item 8 (fainting) are medical-urgency
  markers surfaced by the clinician-UI layer separately and are not
  T3 triggers — see ``scoring/phq15.py``.  PACS (Flannery 1999)
  is a continuous craving measure — the trajectory layer extracts
  its signal via week-over-week Δ rather than classifying a status.
  It is *the* platform-core instrument since craving is the
  60-180s urge-to-action construct the product intervenes on, but
  it carries no crisis item and no validated severity bands.
  See ``scoring/pacs.py``.  BIS-11 (Patton 1995) is the trait-
  level impulsivity measure — the dispositional substrate that
  PACS's state-level craving rides on.  BIS-11 has no safety
  item; high impulsivity routes to DBT distress-tolerance /
  mindfulness attention training / implementation-intention work
  at the intervention-selection layer, not to T3.  See
  ``scoring/bis11.py``.  Craving VAS (Sayette 2000) is the
  single-item 0-100 EMA partner to PACS — it measures
  momentary-point craving at urge-onset and post-intervention so
  the contextual bandit can train on within-episode Δ.  No
  safety item; a VAS of 100 is "strongest craving ever felt",
  not active suicidality.  See ``scoring/craving_vas.py``.  The
  Readiness Ruler (Rollnick 1999 / Heather 2008) is the single-
  item 0-10 motivation-to-change companion — the motivation
  signal the intervention layer pairs with the craving signal to
  pick a tool variant (MI-scripted elicitation vs effortful-
  resistance vs maintenance).  Higher-is-better direction
  (opposite of VAS / PHQ-9 / GAD-7); the trajectory layer
  applies the same direction-inversion logic it uses for WHO-5.
  No safety item; a Ruler of 0 ("not ready at all") is a
  motivation signal, not a crisis signal.  See
  ``scoring/readiness_ruler.py``.  DTCQ-8 (Sklar & Turner 1999)
  is the 8-item Drug-Taking Confidence Questionnaire short form
  — coping self-efficacy across Marlatt 1985's 8 high-risk
  relapse situations on a 0-100 confidence scale.  The instrument
  is the **coping-profile partner** to PACS / VAS: where craving
  measures urge intensity and Ruler measures motivation, DTCQ-8
  measures the per-situation confidence to resist.  The
  intervention layer reads the 8-tuple profile (not just the
  aggregate mean) to pick skill-building tool variants matched
  to the weakest Marlatt category.  Higher-is-better direction
  (same as WHO-5 / Ruler) — the trajectory layer's RCI logic
  must register DTCQ-8 in the higher-is-better partition when
  Sprint-X adds DTCQ-8 trajectory coverage.  No safety item;
  a DTCQ-8 of 0 ("no confidence at all") is a skill-building
  signal, not a crisis signal.  See ``scoring/dtcq8.py``.  URICA
  (McConnaughy 1983 / DiClemente & Hughes 1990) is the 16-item
  short-form University of Rhode Island Change Assessment — the
  multi-stage profile partner to Readiness Ruler (where Ruler is
  the single-item snapshot, URICA carries the full four-stage
  distribution across precontemplation / contemplation / action /
  maintenance).  **First multi-subscale wire-exposed instrument**
  in the package — the dispatch surfaces the four subscale sums
  on the response envelope's ``subscales`` map so the intervention
  layer reads the stage profile (not just the Readiness aggregate)
  to pick stage-matched scripts.  **First signed-total instrument**
  — URICA Readiness = ``C + A + M − PC`` is a signed integer
  (range -8 to +56) where a negative value is clinically meaningful
  (precontemplation-dominant profile).  Higher-is-better direction
  (same as WHO-5 / Ruler / DTCQ-8).  No safety item; a negative
  Readiness is a motivation signal, not a crisis signal.  See
  ``scoring/urica.py``.  PHQ-2 (Kroenke 2003) is the 2-item ultra-
  short depression pre-screener composed of PHQ-9 items 1
  (anhedonia) and 2 (depressed mood) — the **daily-EMA partner**
  to the weekly PHQ-9 full form.  Deliberately excludes PHQ-9
  item 9 (suicidality) so the daily-EMA surface does not carry
  an in-line safety-routing interrupt; acute ideation remains
  gated by the weekly PHQ-9 and by C-SSRS on-demand.  **No
  validated severity bands** — Kroenke 2003 and the 20+ years of
  downstream literature treat PHQ-2 as a binary decision gate
  ("promote to PHQ-9 this week? yes/no"), not a severity measure.
  Hand-rolling bands (e.g. back-calculated from PHQ-9 thresholds)
  would violate CLAUDE.md's "Don't hand-roll severity thresholds"
  rule; the scorer exposes ``total`` + ``positive_screen`` only,
  and the router maps onto the cutoff-only wire envelope
  (severity = "positive_screen" / "negative_screen") uniform with
  PC-PTSD-5 / MDQ / AUDIT-C.  No safety routing — a patient who
  needs daily depression check-ins AND is at acute risk should be
  on PHQ-9 or C-SSRS (instrument choice is itself clinical), not
  on PHQ-2 with an added safety hack.  See ``scoring/phq2.py``.
  GAD-2 (Kroenke 2007) is the 2-item ultra-short anxiety pre-
  screener composed of GAD-7 items 1 (nervousness / on-edge) and
  2 (uncontrolled worry) — the **companion to PHQ-2** on the
  daily-EMA affective check-in surface.  Shipping PHQ-2 without
  GAD-2 would strand the daily-EMA tier with only half the
  affective signal (depression, not anxiety).  **No validated
  severity bands** — Kroenke 2007 and downstream literature treat
  GAD-2 as a binary decision gate ("promote to GAD-7 this week?
  yes/no"), not a severity measure.  The router maps onto the
  cutoff-only wire envelope (severity = "positive_screen" /
  "negative_screen") uniform with PHQ-2 / PC-PTSD-5 / MDQ /
  AUDIT-C.  No safety routing: GAD-2 has no suicidality item —
  neither does the full GAD-7 — so anxiety screens never fire T3.
  Acute ideation stays gated by PHQ-9 item 9 / C-SSRS per the
  uniform safety-posture convention.  See ``scoring/gad2.py``.
  OASIS (Norman 2006 / Campbell-Sills 2009) is the 5-item Overall
  Anxiety Severity And Impairment Scale — the first anxiety measure
  in the package that explicitly indexes functional impairment
  (avoidance + work/school + social) alongside symptom severity
  (frequency + intensity).  Complementary to GAD-7 (which indexes
  symptom severity only): a patient may screen GAD-7-negative but
  OASIS-positive if their anxiety is "functional" (low-intensity,
  high-cost), and vice versa — the two instruments deliberately
  catch different presentations.  **No validated severity bands** —
  Norman 2006 validates only the total score, and downstream
  literature is uniform in reporting only the ``>= 8`` cutoff
  (Campbell-Sills 2009).  **No subscale exposure** — Norman 2006's
  factor analysis supports a single-factor structure; attempting to
  split items 1-2 / 3 / 4-5 into symptom / avoidance / impairment
  subscales yields unvalidated scores and is not supported.  The
  router maps onto the cutoff-only wire envelope
  (severity = "positive_screen" / "negative_screen") uniform with
  PHQ-2 / GAD-2 / PC-PTSD-5 / MDQ / AUDIT-C, with ``subscales=None``.
  No safety routing: OASIS has no item probing suicidality (none of
  the 5 items probes acute-harm intent); anxiety-impairment screens
  never fire T3.  See ``scoring/oasis.py``.
  K10 (Kessler 2002 / Andrews & Slade 2001) is the 10-item Kessler
  Psychological Distress Scale — a cross-cutting general-distress
  measure, neither depression- nor anxiety-specific.  The
  instrument's items span depressive (hopeless / sad / worthless),
  anxiety (nervous / restless), and arousal (tired / effort)
  dimensions and Kessler 2002 validates a *unidimensional* total
  score.  Bands per Andrews & Slade 2001 (10-19 low / 20-24 moderate
  / 25-29 high / 30-50 very_high) are the canonical population-
  survey reference and are echoed on the wire via the banded
  envelope (uniform with PHQ-9 / GAD-7 / PSS-10 / etc.).  **First
  instrument with ``ITEM_MIN = 1``** — Kessler's original coding is
  1-5 (where 1 = "None of the time"), and the Andrews & Slade bands
  are calibrated against this coding; a client that submits 0-indexed
  items shifts every total by 10 and drops a band.  The router
  enforces the 1-5 range at the validator.  No subscale exposure:
  Kessler 2002's factor analysis supports the unidimensional total;
  splitting items into depression / anxiety subscales is
  unvalidated.  No safety routing: K10's hopelessness items
  (4 / 9 / 10) are affect probes, not intent probes — T3 remains
  reserved for PHQ-9 item 9 / C-SSRS.  See ``scoring/k10.py``.
  SDS (Gossop 1995) is the 5-item Severity of Dependence Scale — a
  *psychological-dependence* screen for a specified substance,
  deliberately orthogonal to use-volume-and-frequency (AUDIT / AUDIT-C /
  DAST-10).  The instrument captures the subjective compulsive-use
  construct (loss of control, worry about use, desire to stop, perceived
  difficulty of abstaining) — a patient can be DAST-low / SDS-high
  (infrequent but ego-dystonic use) or DAST-high / SDS-low (heavy but
  ego-syntonic use), and those two patterns have very different
  treatment paths.  **First instrument with substance-adaptive
  cutoffs** — extends the AUDIT-C per-population-cutoff precedent (sex)
  to a second demographic axis (substance).  Cutoffs per Gossop 1995
  and the substance-specific follow-up literature: heroin ≥ 5,
  cannabis ≥ 3 (Martin 2006 / Swift 1998), cocaine ≥ 3 (Kaye & Darke
  2002), amphetamine ≥ 4 (Topp & Mattick 1997); substance unspecified
  falls back to the lowest (≥ 3) as a safety-conservative default —
  same posture as AUDIT-C sex = "unspecified".  The router maps onto
  the cutoff-only wire envelope (severity = "positive_screen" /
  "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 /
  MDQ / AUDIT-C.  ``cutoff_used`` echoes the substance-keyed cutoff so
  a clinician-UI renders "positive at ≥ N" with no re-derivation.
  **No subscale exposure**: Gossop 1995 validates unidimensionality;
  splitting items into cognitive / behavioral factors is unvalidated.
  No safety routing: SDS has no suicidality item — a high SDS is a
  psychological-dependence work-up signal, not a crisis signal.  See
  ``scoring/sds.py``.
  K6 (Kessler 2003) is the 6-item short form of K10 — same 1-5
  Likert coding as K10 (ITEM_MIN = 1 is load-bearing), total 6-30,
  cutoff ≥ 13 for probable serious mental illness (SMI) per Kessler
  2003 (validated against the 12-month DSM-IV SMI criterion, AUC
  0.87).  The **daily-EMA partner to K10** — same unidimensional
  psychological-distress construct, six items ≈ 30s on a phone
  instead of ten items ≈ 50s.  Mirrors the PHQ-9 → PHQ-2 and
  GAD-7 → GAD-2 companion-pairing pattern.  The router maps K6 onto
  the cutoff-only wire envelope (severity = "positive_screen" /
  "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5
  / AUDIT-C / SDS — *not* the K10 banded envelope.  Kessler 2003
  published only the ≥ 13 SMI cutoff; back-calculating K10-style
  bands onto K6 totals is unvalidated and explicitly not done here.
  If banded-severity tracking is the clinical need, the answer is
  K10, not K6 with invented bands.  No subscale exposure: K6 items
  were selected for their loading on the K10 dominant factor, so
  the scale is unidimensional by design.  No safety routing: K6's
  hopelessness / depressed / worthless items (2 / 4 / 6) are affect
  probes, not intent probes — same posture as K10.  See
  ``scoring/k6.py``.
  DUDIT (Berman 2003, 2005) is the 11-item Drug Use Disorders
  Identification Test — the parallel to AUDIT for non-alcohol
  substances.  Together with AUDIT-C (alcohol) and the Gossop 1995
  SDS (specific-substance dependence), DUDIT completes the substance-
  use screening trio at the assessment layer.  **First instrument
  with a non-uniform per-index item validator** — items 1-9 take
  the 0-4 Likert envelope, items 10-11 take the {0, 2, 4} trinary
  envelope (no / yes-but-not-in-last-year / yes-in-last-year).  A
  response of 1 or 3 on items 10-11 is rejected at the scorer even
  though it sits within the numerical range 0-4; the router forwards
  the scorer's ``InvalidResponseError`` as 422 with a message naming
  the legal values (0/2/4).  Total 0-44.  Sex-keyed cutoffs
  (Berman 2005): men ≥ 6 / women ≥ 2 / unspecified ≥ 2 (safety-
  conservative default, matches female cutoff — same posture as
  AUDIT-C sex = "unspecified").  The sex asymmetry is larger than
  AUDIT-C's (3× vs ≈1.3×) because women show drug-related harm at
  substantially lower use frequencies per Berman 2005 §4.  The
  ``sex`` field on the request is now read by both AUDIT-C and DUDIT
  — a single demographic axis serves both sex-keyed cutoff
  instruments.  The router maps onto the cutoff-only wire envelope
  (severity = "positive_screen" / "negative_screen") uniform with
  PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / AUDIT-C / SDS / K6.  ``cutoff_used``
  echoes the sex-keyed cutoff so a clinician-UI renders "positive
  at ≥ N".  **No subscale exposure**: Berman 2003 validates DUDIT
  at the unidimensional screening-score level; factor-analysis sub-
  structure is not clinically scored.  No safety routing: DUDIT's
  loss-of-control items (4 / 5 / 6) are substance-use probes, not
  suicidality probes, and item 10 ("have you or anyone else been
  hurt") spans physical / mental / social / legal consequences
  (not intent) — acute ideation screening remains PHQ-9 item 9 /
  C-SSRS.  See ``scoring/dudit.py``.
  ASRS-6 (Kessler 2005) is the 6-item WHO Adult ADHD Self-Report Scale
  short screener — the brief derivative of the full 18-item ASRS-v1.1
  Symptom Checklist, selected for peak discriminative value vs DSM-IV
  adult-ADHD diagnosis.  Closes the ADHD-screening gap in the platform:
  adult ADHD co-occurs with depression / anxiety / impulsivity /
  substance use at rates well above base (Kessler 2006, Wilens 2013),
  and a patient with undetected adult ADHD presenting with co-occurring
  distress is a common missed-diagnosis pattern that the existing
  PHQ-9 / GAD-7 / BIS-11 / AUDIT-C / DUDIT coverage doesn't surface
  on its own.  **First instrument with weighted-threshold scoring**
  — where PHQ-9 / GAD-7 / K10 / etc. sum raw Likert responses against
  a total cutoff, ASRS-6 applies a per-item firing threshold
  (inattentive items 1-3 fire at Likert ≥ 2; hyperactive items 4-6
  fire at Likert ≥ 3 per Kessler 2005 Figure 1) and counts the number
  of fired items against a count cutoff (≥ 4 of 6).  The scorer
  surfaces both ``total`` (for trajectory tracking) and
  ``positive_count`` (for the screen decision) — a caller using
  ``total`` to interpret the screen would under-detect in exactly the
  symptom pattern the weighted-threshold rule was designed to catch
  (sum=12 is possible with only one fired item).  The router maps onto
  the cutoff-only wire envelope (severity = "positive_screen" /
  "negative_screen") uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 /
  AUDIT-C / SDS / K6 / DUDIT.  ``cutoff_used`` echoes the count cutoff
  (= 4) so a clinician-UI renders "positive at ≥ 4 of 6 items".
  ``triggering_items`` reuses the existing C-SSRS wire slot — 1-indexed
  item numbers that met their per-item firing threshold — so a
  clinician-UI can render "these symptoms drove the screen" as an
  audit trail of the decision, not just the aggregate count.  **No
  subscale exposure**: the inattentive (items 1-3) / hyperactive-
  impulsive (items 4-6) factor split is implicit in the asymmetric
  thresholds but Kessler 2005 validates the screener at the
  unidimensional count-of-fires level, not at the subscale level.
  Clinicians needing the factor split should administer the full
  18-item ASRS Symptom Checklist, not back-calculate from the 6-item
  screener.  **No banded severity**: Kessler 2005 published only the
  binary decision gate; secondary sources presenting ordinal bands are
  not calibrated against a published clinical criterion and the
  package refuses to ship them per CLAUDE.md's "don't hand-roll
  severity thresholds" rule.  No safety routing: ASRS-6 has no
  suicidality item — items 5 (fidget) and 6 (driven by a motor)
  probe hyperactivity, not intent — acute ideation screening remains
  PHQ-9 item 9 / C-SSRS.  See ``scoring/asrs6.py``.
  AAQ-II (Bond 2011) is the 7-item Acceptance and Action
  Questionnaire-II — the definitive transdiagnostic measure of
  **psychological inflexibility**, the ACT (Acceptance and Commitment
  Therapy) target construct.  Where CBT-aligned instruments (PHQ-9 /
  GAD-7 / PCL-5) measure symptom severity, AAQ-II measures the
  *relationship* to symptoms (experiential avoidance / cognitive
  fusion) — two patients with identical PHQ-9 totals can differ
  sharply on AAQ-II, and the AAQ-II difference predicts treatment
  course and intervention fit independently of symptom severity
  (Bond 2011, Hayes 2006).  Closes the ACT-alignment intervention-
  selection gap at the platform assessment layer: the contextual
  bandit needs the psychological-inflexibility signal to route a
  craving episode to an ACT-variant tool (defusion / values-
  clarification / willingness exercises) when experiential avoidance
  is the active process, rather than defaulting to CBT cognitive
  restructuring which can backfire in high-inflexibility patients
  (Hayes 2006 §"When not to do CBT").  **First instrument with a
  1-7 Likert envelope in the package** — prior instruments use 0-3
  (C-SSRS), 0-4 (PHQ-9 / GAD-7 / DUDIT items 1-9 / ASRS-6 / etc.),
  0-5 (WHO-5 / PCL-5 / OCI-R), or 1-5 (K10 / K6).  Bond 2011's
  7-point scale reduces ceiling / floor compression observed in
  earlier AAQ versions; the widened per-item resolution is load-
  bearing at the sensitivity layer.  ``ITEM_MIN = 1`` is shared with
  K10 / K6 but ``ITEM_MAX = 7`` is novel — a response of 0 is
  rejected (even though 0-indexed instruments in the package accept
  it) and responses of 6 / 7 are accepted (even though K10 / K6
  would reject them).  Total 7-49.  Cutoff ≥ 24 per Bond 2011 (ROC-
  derived vs SCID-II, sensitivity 0.75 / specificity 0.80).  The
  router maps onto the cutoff-only wire envelope (severity =
  "positive_screen" / "negative_screen") uniform with PHQ-2 / GAD-2 /
  OASIS / PC-PTSD-5 / AUDIT-C / SDS / K6 / DUDIT / ASRS-6.
  ``cutoff_used`` echoes the Bond 2011 cutoff (= 24, constant across
  all inputs — unlike AUDIT-C / SDS / DUDIT where the cutoff varies
  by demographic axis).  **No subscale exposure**: Bond 2011's
  confirmatory factor analysis supports a unidimensional structure
  for AAQ-II; earlier AAQ-I / 9-item sub-factor proposals did not
  survive psychometric refinement into AAQ-II.  **No banded
  severity**: Bond 2011 published only the ≥ 24 clinical cutoff;
  secondary sources with ordinal bands are not calibrated against a
  published clinical criterion and the package refuses to ship them
  per CLAUDE.md's "don't hand-roll severity thresholds" rule.  No
  safety routing: AAQ-II has no suicidality item — item 1 / 4
  ("painful experiences and memories") and item 2 ("afraid of my
  feelings") are process-of-avoidance probes, not intent probes —
  acute ideation screening remains PHQ-9 item 9 / C-SSRS.  See
  ``scoring/aaq2.py``.
  WSAS (Mundt 2002) is the 5-item Work and Social Adjustment Scale —
  the canonical functional-impairment outcome measure in the UK
  IAPT / stepped-care pathway, administered alongside PHQ-9 and
  GAD-7 at every session to track the *functional* arc
  independently of symptom change (Clark 2011).  Closes the
  functional-impairment construct gap at the platform assessment
  layer: where PHQ-9 / GAD-7 / K10 / PCL-5 measure symptom
  severity and AAQ-II measures the relationship to internal
  experience, WSAS measures the observable behavioral cost — can
  the patient work, manage home, sustain relationships?  Two
  patients with identical PHQ-9 totals can differ sharply on WSAS
  (PHQ-9=8 with WSAS=28 is a much more urgent clinical picture
  than PHQ-9=8 with WSAS=4), and the bandit / reporting layer
  needs the WSAS signal to distinguish these cases and route
  behavioral-activation / committed-action tool variants when
  functional restoration is lagging symptom reduction.
  **First 0-8 Likert instrument in the package** — widest per-item
  envelope yet (prior widest was AAQ-II's 1-7; predominant
  envelopes are 0-3 / 0-4 / 0-5 / 1-5).  Mundt 2002 argued the
  9-point scale reduces ceiling / floor compression and gives
  sufficient resolution for RCI-grade change detection.
  ``ITEM_MIN = 0`` is shared with every 0-indexed instrument; the
  ceiling of 8 is novel and the scorer rejects 9 at the validator.
  Total 0-40.  **Banded severity** per Mundt 2002 —
  [0, 10) subclinical, [10, 20) significant, [20, 40] severe.
  Cut-points at 10 and 20 derived against SCID-diagnosed
  depressive-episode patients.  Per CLAUDE.md's "don't hand-roll
  severity thresholds" rule, the scorer ships exactly these three
  Mundt 2002 bands — splitting "severe" into moderate-severe
  (20-29) and severe (30-40) is unpublished and is refused.  The
  router maps onto the banded wire envelope uniform with PHQ-9 /
  GAD-7 / ISI / DAST-10 / PCL-5 / OCI-R / BIS-11 / PHQ-15 / K10 /
  DUDIT.  ``cutoff_used`` / ``positive_screen`` are NOT set
  (banded instruments do not surface a single cutoff).  No
  subscale exposure: Mundt 2002's confirmatory factor analysis
  supports a unidimensional structure (a "productive" vs "social"
  subfactor split was explicitly rejected).  No T3: WSAS has no
  suicidality item — the five items probe work / home / social /
  private / relationships, none of which references suicidality,
  self-harm, or crisis behavior.  A "severe" WSAS is a strong
  signal for intensive behavioral-activation / committed-action
  work but is not itself a crisis gate — acute ideation screening
  remains PHQ-9 item 9 / C-SSRS.  See ``scoring/wsas.py``.
  DERS-16 (Bjureberg 2016) is the 16-item short form of the
  Difficulties in Emotion Regulation Scale (Gratz & Roemer 2004) —
  the validated measure of **emotion dysregulation**, the
  Dialectical Behavior Therapy (DBT) target construct.  Closes the
  DBT-alignment gap at the assessment layer: where AAQ-II measures
  the ACT target (psychological inflexibility) and PHQ-9 / GAD-7
  measure CBT-aligned symptom severity, DERS-16 measures the
  regulatory-process dimension that DBT interventions
  (distress-tolerance, emotion regulation skills, wise-mind,
  radical acceptance) directly address.  Together with AAQ-II and
  PHQ-9 / GAD-7, DERS-16 completes the **three-way process-target
  triangle** so the contextual bandit can route process-level
  decisions to the therapeutic frame whose target construct the
  patient's profile loads most heavily on — rather than defaulting
  to CBT because CBT is the instrument default.  16 items each on
  a 1-5 Likert ("Almost never" to "Almost always"), all worded in
  the dysregulation direction (Bjureberg 2016 pruned the six
  awareness-subscale items from DERS-36 that required reverse-
  keying).  Total 16-80.  Five CFA-validated subscales per
  Bjureberg 2016 Table 2 — ``nonacceptance`` (items 9, 10, 13;
  range 3-15), ``goals`` (items 3, 7, 15; range 3-15), ``impulse``
  (items 4, 8, 11; range 3-15), ``strategies`` (items 5, 6, 12,
  14, 16; range 5-25, the widest subscale), and ``clarity`` (items
  1, 2; range 2-10, the narrowest).  **First 5-subscale
  instrument** — prior multi-subscale ceiling was OCI-R's 6 and
  PCL-5's 4.  Subscale dict is surfaced on the envelope's
  ``subscales`` field because the intervention layer reads the
  5-tuple profile (not just the aggregate) to pick DBT skill
  modules: impulse-dominant → distress-tolerance (TIP / STOP /
  self-soothe), strategies-dominant → cope-ahead / opposite-
  action, clarity-dominant → observe / describe mindfulness,
  nonacceptance-dominant → self-compassion / non-judgmental
  stance, goals-dominant → wise-mind / mindfulness-of-current-
  activity.  **Severity bands deliberately absent.**  Bjureberg
  2016 did NOT publish banded thresholds; downstream literature
  (Fowler 2014 PTSD samples, Hallion 2018 mixed-anxiety samples)
  proposes cutoffs that are not cross-calibrated against a shared
  clinical criterion and vary by sample.  Per CLAUDE.md's "don't
  hand-roll severity thresholds" rule, DERS-16 ships as a
  **continuous dimensional measure** uniform with Craving VAS /
  PACS — the envelope carries ``severity="continuous"`` as the
  sentinel and the trajectory layer extracts the clinical signal
  via RCI-style change detection (Jacobson & Truax 1991) rather
  than banded classification.  ``cutoff_used`` / ``positive_screen``
  are NOT set (continuous instrument, no cutoff shape).  No T3:
  DERS-16 has no direct suicidality item — items 4 and 8 ("out of
  control") probe impulse-control loss but not acute intent; item
  14 ("feel very bad about myself") probes self-critical affect
  but not suicidality.  A high DERS-16 total / impulse subscale
  is a strong signal for DBT-variant intervention tools but is
  not itself a crisis gate — acute ideation screening remains
  PHQ-9 item 9 / C-SSRS.  See ``scoring/ders16.py``.
  CD-RISC-10 (Campbell-Sills & Stein 2007) is the 10-item
  unidimensional short form of the original 25-item Connor-Davidson
  Resilience Scale (Connor & Davidson 2003) — the validated measure
  of trait resilience, the product's **core construct**.  The
  platform ships a monotonically-increasing resilience streak
  (CLAUDE.md Rule #3), a recovery-pathway framing, and compassion-
  first messaging that all presuppose a measurable resilience
  dimension; CD-RISC-10 closes that gap at the assessment layer.
  Gives the trajectory layer a construct-aligned score so the
  bandit can answer "is the cumulative intervention arc moving
  this patient's resilience?", "is resilience decoupling from
  symptom severity (PHQ-9 flat while CD-RISC-10 rising — the
  expected recovery signature)?", and "below-population resilience
  at intake → heavier scaffold?".  10 items on a 0-4 Likert ("not
  true at all" → "true nearly all the time"), all positively
  worded (Campbell-Sills & Stein 2007 pruned the 15 cross-loading
  items from CD-RISC-25); total 0-40.  **Higher-is-better
  directionality** — uniform with WHO-5 / DTCQ-8 / Readiness
  Ruler, opposite from PHQ-9 / GAD-7 / DERS-16 / PCL-5 / OCI-R /
  K10 / WSAS.  A falling CD-RISC-10 score is a DETERIORATION, not
  an improvement; clinician-UI layers that reuse higher-is-worse
  visual language from symptom measures would misread this
  instrument.  **Severity bands deliberately absent.**
  Campbell-Sills & Stein 2007 reported general-population mean
  31.8 ± 5.4 (N=764) but NO banded thresholds; Connor 2003
  cutpoints apply to the 25-item scale and do not translate
  linearly to the 10-item form.  Per CLAUDE.md "don't hand-roll
  severity thresholds", CD-RISC-10 ships as a continuous
  dimensional measure uniform with Craving VAS / PACS / DERS-16 /
  DTCQ-8 — the envelope carries ``severity="continuous"`` as the
  sentinel.  The clinician-UI layer may surface a "below general-
  population mean" flag (score < 31) as contextual information —
  that flag is NOT a classification and NOT a gate.  No subscales
  (Campbell-Sills & Stein 2007 CFA — unidimensional; CD-RISC-25's
  five-factor split was explicitly rejected for the 10-item form).
  ``cutoff_used`` / ``positive_screen`` NOT set.  No T3 —
  CD-RISC-10 items probe adaptability, coping, humor, post-stress
  growth, bounce-back, goal persistence, focus, failure-tolerance,
  self-strength, distress-tolerance; none reference suicidality.
  Item 10 ("can handle unpleasant or painful feelings") probes
  distress-tolerance capacity (the INVERSE of what a crisis item
  probes) — a floor on item 10 is a DBT-distress-tolerance
  scaffolding signal, not a crisis gate.  Acute ideation screening
  remains PHQ-9 item 9 / C-SSRS.  See ``scoring/cdrisc10.py``.
- PSWQ (Meyer 1990) is the 16-item Penn State Worry Questionnaire —
  the gold-standard measure of trait-level worry, the CBT-for-GAD
  process-target instrument.  GAD-7 measures anxiety symptoms over
  a 2-week window (state severity); PSWQ measures the dispositional
  worry *process* that cognitive therapy for GAD explicitly targets,
  so the two instruments answer orthogonal clinical questions (a
  patient can have controlled symptoms but persistent worry trait,
  or vice versa).  **First reverse-keying pattern in the package** —
  items 1, 3, 8, 10, 11 are worded in the worry-ABSENT direction
  (e.g., "I do not tend to worry about things.") so a high raw
  Likert reflects LOW worry; the scorer applies arithmetic
  reflection (``flipped = 6 - raw``) to those items before summing
  so every post-flip item contributes in the same direction.  Mixed-
  direction design is deliberate: Meyer 1990 included reverse-keyed
  items to suppress acquiescent-response bias (all-5s gives 60, not
  80; all-1s gives 36, not 16).  ``items`` audit field preserves
  the RAW pre-flip patient response for auditability — clinicians
  reviewing the record see what the patient ticked, not the
  scorer's internal representation.  16 items 1-5 Likert (uniform
  with DERS-16); total 16-80.  Higher is worse (same as PHQ-9 /
  GAD-7 / DERS-16 / PCL-5, opposite of WHO-5 / DTCQ-8 / Readiness
  Ruler / CD-RISC-10).  **No severity bands** — Meyer 1990
  published GAD/general-pop means (~67 / ~48) but no cross-
  calibrated cutpoints; downstream cuts (Behar 2003: 45/62 tertiles
  in students; Startup & Erickson 2006: 56+ GAD-diagnostic in
  treatment-seekers; Fresco 2003: mid-50s GAD-threshold) are
  sample-specific and not cross-calibrated against a shared
  clinical criterion.  Per CLAUDE.md's "don't hand-roll severity
  thresholds", PSWQ ships as a continuous dimensional measure
  uniform with DERS-16 / CD-RISC-10 / PACS; envelope carries
  ``severity="continuous"``.  The clinician-UI layer may surface a
  "above GAD-sample mean" context flag (score ≥ 60) — that flag is
  NOT a classification and NOT a gate.  Unidimensional per Meyer
  1990 / Brown 1992 CFA — no subscales dict.  ``cutoff_used`` /
  ``positive_screen`` NOT set.  No T3 — the 16 items probe the
  worry-process construct only (intensity, persistence,
  uncontrollability, chronicity); item 2 ("My worries overwhelm
  me.") and item 14 ("Once I start worrying, I cannot stop.") at
  ceiling endorse GAD-DSM-5-criterion uncontrollability, NOT
  suicidality.  Acute ideation screening remains PHQ-9 item 9 /
  C-SSRS.  See ``scoring/pswq.py``.
- LOT-R (Scheier, Carver & Bridges 1994): 10-item payload on the
  wire (6 scored + 4 filler); the filler items are present on the
  patient-facing form to obscure the optimism construct from demand
  characteristics and are NOT summed into the total.  0-4 Likert,
  post-flip range 0-24, **higher is better** (more dispositional
  optimism) — uniform direction with CD-RISC-10 / WHO-5 / DTCQ-8 /
  Readiness Ruler, opposite of PHQ-9 / GAD-7 / DERS-16 / PCL-5 /
  OCI-R / K10 / WSAS / PSWQ.  Reuses the reverse-keying pattern
  established by PSWQ: items 3, 7, 9 are pessimism-worded and
  flipped (``flipped = 4 - raw``) before summing.  **First filler-
  item pattern in the package** — earlier instruments scored every
  validated-input item; LOT-R is the first with within-form
  camouflage.  The audit-trail invariant is preserved: the stored
  ``items`` tuple echoes all 10 raw responses (including the 4
  filler values) so a clinician reviewing the record sees exactly
  what the patient ticked on the form.  Per CLAUDE.md "don't hand-
  roll severity thresholds", LOT-R ships as a continuous
  dimensional measure uniform with PACS / Craving VAS / DERS-16 /
  CD-RISC-10 / PSWQ; envelope carries ``severity="continuous"``.
  Scheier 1994 reported general-population means (~14-15) but
  published no cross-calibrated clinical cutpoints.  Unidimensional
  per Scheier 1994 CFA — no subscales dict (Chang 1997's
  optimism/pessimism two-factor split is sample-specific and
  deliberately rejected).  ``cutoff_used`` / ``positive_screen``
  NOT set.  **No T3** — all 10 items probe the optimism-pessimism
  construct and general-affect fillers; none probe suicidality,
  self-harm, or crisis behavior.  LOT-R pairs directly with
  CD-RISC-10 as the two-axis trait-positive-psychology layer
  (capacity + expectancy).  See ``scoring/lotr.py``.
- TAS-20 (Bagby, Parker & Taylor 1994): 20 items, 1-5 Likert.
  Measures **alexithymia** — trait-level difficulty identifying
  feelings (DIF), describing feelings (DDF), and an externally-
  oriented cognitive style (EOT).  Reverse-keying on items 4, 5,
  10, 18, 19 (reuses the PSWQ / LOT-R arithmetic-reflection
  idiom; ``flipped = 6 - raw``).  Three-subscale structure per
  Bagby 1994 CFA — surfaced via the ``subscales`` map with keys
  ``dif`` / ``ddf`` / ``eot`` (uniform with DERS-16's subscale
  dispatch shape).  Higher-is-worse (more alexithymia); uniform
  direction with PHQ-9 / GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 /
  WSAS / PSWQ.  **Re-introduces banded classification** after
  five consecutive continuous-sentinel sprints (WSAS, DERS-16,
  CD-RISC-10, PSWQ, LOT-R) — Bagby 1994 published cross-
  calibrated cutoffs (≤51 non_alexithymic, 52-60
  possible_alexithymia, ≥61 alexithymic) replicated across
  Taylor 1997 / Ogrodniczuk 2011 / Cleland 2005 validation work.
  Clinical framing: upstream emotion-identification measure that
  GATES downstream emotion-regulation training — a patient who
  cannot identify "I am angry right now" cannot plausibly deploy
  an anger-regulation strategy, so the intervention-selection
  layer routes high-DIF patients to affect-labeling work BEFORE
  DBT-style regulation skills.  No ``cutoff_used`` /
  ``positive_screen`` — TAS-20 uses three bands, not a single
  binary cutoff.  No T3 — the 20 items probe emotion-
  identification / description / externally-oriented cognition;
  none probe suicidality.  See ``scoring/tas20.py``.

C-SSRS transport note:
- Clients send item responses as 0/1 ints (consistent with every other
  instrument).  The scorer coerces to bool internally; the response
  echoes the raw caller input in the stored record.
"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.shared.idempotency import (
    Conflict,
    Hit,
    get_idempotency_store,
    hash_pydantic,
)
from discipline.shared.logging import LogStream, get_stream_logger

from .repository import AssessmentRecord, get_assessment_repository
from .safety_items import evaluate_phq9
from .scoring.aaq2 import (
    InvalidResponseError as Aaq2Invalid,
    score_aaq2,
)
from .scoring.asrs6 import (
    ASRS6_POSITIVE_CUTOFF,
    InvalidResponseError as Asrs6Invalid,
    score_asrs6,
)
from .scoring.audit import (
    InvalidResponseError as AuditInvalid,
    score_audit,
)
from .scoring.cdrisc10 import (
    InvalidResponseError as Cdrisc10Invalid,
    score_cdrisc10,
)
from .scoring.bis11 import (
    InvalidResponseError as Bis11Invalid,
    score_bis11,
)
from .scoring.audit_c import (
    InvalidResponseError as AuditCInvalid,
    Sex,
    score_audit_c,
)
from .scoring.craving_vas import (
    InvalidResponseError as CravingVasInvalid,
    score_craving_vas,
)
from .scoring.cssrs import (
    InvalidResponseError as CssrsInvalid,
    score_cssrs_screen,
)
from .scoring.dast10 import InvalidResponseError as Dast10Invalid, score_dast10
from .scoring.ders16 import (
    InvalidResponseError as Ders16Invalid,
    score_ders16,
)
from .scoring.dtcq8 import (
    InvalidResponseError as Dtcq8Invalid,
    score_dtcq8,
)
from .scoring.dudit import (
    InvalidResponseError as DuditInvalid,
    score_dudit,
)
from .scoring.gad2 import (
    InvalidResponseError as Gad2Invalid,
    score_gad2,
)
from .scoring.gad7 import InvalidResponseError as Gad7Invalid, score_gad7
from .scoring.isi import InvalidResponseError as IsiInvalid, score_isi
from .scoring.k10 import (
    InvalidResponseError as K10Invalid,
    score_k10,
)
from .scoring.k6 import (
    InvalidResponseError as K6Invalid,
    score_k6,
)
from .scoring.lotr import (
    InvalidResponseError as LotrInvalid,
    score_lotr,
)
from .scoring.mdq import (
    ImpairmentLevel,
    InvalidResponseError as MdqInvalid,
    score_mdq,
)
from .scoring.oasis import (
    InvalidResponseError as OasisInvalid,
    score_oasis,
)
from .scoring.ocir import (
    InvalidResponseError as OcirInvalid,
    score_ocir,
)
from .scoring.pacs import (
    InvalidResponseError as PacsInvalid,
    score_pacs,
)
from .scoring.pcl5 import (
    InvalidResponseError as Pcl5Invalid,
    score_pcl5,
)
from .scoring.pcptsd5 import (
    InvalidResponseError as PcPtsd5Invalid,
    score_pcptsd5,
)
from .scoring.phq2 import (
    InvalidResponseError as Phq2Invalid,
    score_phq2,
)
from .scoring.phq9 import InvalidResponseError as Phq9Invalid, score_phq9
from .scoring.phq15 import (
    InvalidResponseError as Phq15Invalid,
    score_phq15,
)
from .scoring.pss10 import InvalidResponseError as Pss10Invalid, score_pss10
from .scoring.pswq import (
    InvalidResponseError as PswqInvalid,
    score_pswq,
)
from .scoring.readiness_ruler import (
    InvalidResponseError as ReadinessRulerInvalid,
    score_readiness_ruler,
)
from .scoring.sds import (
    InvalidResponseError as SdsInvalid,
    Substance as SdsSubstance,
    score_sds,
)
from .scoring.tas20 import (
    InvalidResponseError as Tas20Invalid,
    score_tas20,
)
from .scoring.urica import (
    InvalidResponseError as UricaInvalid,
    score_urica,
)
from .scoring.who5 import InvalidResponseError as Who5Invalid, score_who5
from .scoring.wsas import (
    InvalidResponseError as WsasInvalid,
    score_wsas,
)
from .trajectories import RCI_THRESHOLDS, compute_point

router = APIRouter(prefix="/assessments", tags=["psychometric"])

# Safety stream — 2-year retention, HMAC-Merkle chained, clinical-ops reader.
# Per CLAUDE.md Rule #6 the audit/safety writers are gated by import boundary.
# This module (``psychometric``) is on the allow-list because PHQ-9 item 9 and
# C-SSRS items 4/5/6 are themselves safety-routing inputs.
_safety = get_stream_logger(LogStream.SAFETY)


Instrument = Literal[
    "phq9",
    "gad7",
    "who5",
    "audit",
    "audit_c",
    "cssrs",
    "pss10",
    "dast10",
    "mdq",
    "pcptsd5",
    "isi",
    "pcl5",
    "ocir",
    "phq15",
    "pacs",
    "bis11",
    "craving_vas",
    "readiness_ruler",
    "dtcq8",
    "urica",
    "phq2",
    "gad2",
    "oasis",
    "k10",
    "sds",
    "k6",
    "dudit",
    "asrs6",
    "aaq2",
    "wsas",
    "ders16",
    "cdrisc10",
    "pswq",
    "lotr",
    "tas20",
]


# Item-count contracts per instrument.  Pinned so a request with the
# wrong number of items fails at the router with a 422 listing the
# expected count, rather than passing a malformed list to the scorer.
_INSTRUMENT_ITEM_COUNTS: dict[Instrument, int] = {
    "phq9": 9,
    "gad7": 7,
    "who5": 5,
    "audit": 10,
    "audit_c": 3,
    "cssrs": 6,
    "pss10": 10,
    "dast10": 10,
    "mdq": 13,
    "pcptsd5": 5,
    "isi": 7,
    "pcl5": 20,
    "ocir": 18,
    "phq15": 15,
    "pacs": 5,
    "bis11": 30,
    "craving_vas": 1,
    "readiness_ruler": 1,
    "dtcq8": 8,
    "urica": 16,
    "phq2": 2,
    "gad2": 2,
    "oasis": 5,
    "k10": 10,
    "sds": 5,
    "k6": 6,
    "dudit": 11,
    "asrs6": 6,
    "aaq2": 7,
    "wsas": 5,
    "ders16": 16,
    "cdrisc10": 10,
    "pswq": 16,
    "lotr": 10,
    "tas20": 20,
}


class AssessmentRequest(BaseModel):
    """Wire-format assessment submission.

    Per-instrument item-count is validated at the route layer (after
    Pydantic) so the error message can be specific to the instrument
    ("PHQ-9 requires exactly 9 items, got N").  The Pydantic
    ``min_length=1, max_length=30`` bound is the broadest envelope
    covering every supported instrument (Craving VAS=1, DTCQ-8=8
    through BIS-11=30); a tighter check needs to know the instrument value,
    which Pydantic field validators can't see in a clean way.  Craving
    VAS (Sprint 36) dropped the floor from 3 to 1 so the single-item
    EMA instrument could flow through the same wire shape; BIS-11
    (Sprint 35) had raised the ceiling from 20 to 30.  Callers on
    multi-item instruments see no change since the per-instrument count
    check at ``_validate_item_count`` is the tight constraint.

    ``sex`` is read by both AUDIT-C (Bush 1998 sex-keyed cutoff) and
    DUDIT (Berman 2005 sex-keyed cutoff); ignored by other instruments.
    Defaulting to ``None`` (rather than ``"unspecified"``) lets the
    router echo 'caller did not supply' vs 'caller supplied
    unspecified' if that distinction ever matters for telemetry.  Both
    instruments map ``None`` to the conservative (lower, more
    sensitive) cutoff — AUDIT-C ≥ 3 / DUDIT ≥ 2 — as the safety posture
    for unknown sex.

    ``behavior_within_3mo`` is C-SSRS-only; it modulates whether a
    positive item 6 (past suicidal behavior) escalates to acute T3.
    Default ``None`` means 'not supplied' — the scorer treats that
    as False (historic), producing a moderate band rather than acute.

    ``concurrent_symptoms`` and ``functional_impairment`` are MDQ-only
    — Parts 2 and 3 of the Hirschfeld 2000 instrument.  Both are
    *required* to score MDQ; the dispatch layer raises 422 if either
    is missing when ``instrument == "mdq"``.  A partial MDQ submission
    would silently produce ``negative_screen`` regardless of Part 1,
    so surfacing the gap explicitly at the wire boundary is the right
    clinical posture.

    ``substance`` is SDS-only; it selects the Gossop 1995 / follow-up-
    literature cutoff used to derive ``positive_screen``.  Default
    ``None`` means 'not supplied' — the scorer applies the
    safety-conservative ``unspecified`` cutoff (≥ 3).  Ignored by
    other instruments.
    """

    instrument: Instrument
    items: list[int] = Field(min_length=1, max_length=30)
    sex: Sex | None = Field(
        default=None,
        description=(
            "Read by AUDIT-C (Bush 1998) and DUDIT (Berman 2005); "
            "ignored by other instruments.  ``None`` maps to the "
            "conservative cutoff — AUDIT-C ≥ 3 / DUDIT ≥ 2."
        ),
    )
    behavior_within_3mo: bool | None = Field(
        default=None,
        description=(
            "C-SSRS only; whether item 6 (past behavior) was within the "
            "past 3 months.  Drives T3 escalation for item 6 positives."
        ),
    )
    concurrent_symptoms: bool | None = Field(
        default=None,
        description=(
            "MDQ only; Part 2 — whether several Part 1 items co-occurred "
            "in the same period.  Required when instrument == 'mdq'."
        ),
    )
    functional_impairment: ImpairmentLevel | None = Field(
        default=None,
        description=(
            "MDQ only; Part 3 — one of 'none'/'minor'/'moderate'/'serious'. "
            "Required when instrument == 'mdq'.  Only 'moderate' or "
            "'serious' satisfies the Hirschfeld 2000 positive-screen gate."
        ),
    )
    substance: SdsSubstance | None = Field(
        default=None,
        description=(
            "SDS only; one of 'heroin'/'cannabis'/'cocaine'/'amphetamine'/"
            "'unspecified'.  Selects the published positive-screen cutoff "
            "(heroin ≥ 5, cannabis/cocaine ≥ 3, amphetamine ≥ 4).  Omit or "
            "send None to fall back to the conservative 'unspecified' "
            "cutoff (≥ 3) — same posture as AUDIT-C sex='unspecified'."
        ),
    )
    user_id: str | None = Field(
        default=None,
        description=(
            "Pseudonymous subject identifier — recorded in the safety "
            "stream when a T3 fires so on-call clinicians can route "
            "contact.  In production this is derived from the session "
            "JWT, not the request body; the body field is here so "
            "test fixtures and unauthenticated diagnostic harnesses "
            "can supply one explicitly.  May be None when no T3 fires "
            "(no safety event is emitted for non-T3 results)."
        ),
    )


class AssessmentResult(BaseModel):
    """Unified result envelope across all instruments.

    Always-present fields: ``assessment_id``, ``instrument``, ``total``,
    ``severity``, ``requires_t3``, ``instrument_version``.

    Instrument-specific optional fields:
    - ``index`` — WHO-5 only; the WHO-5 Index (0–100).
    - ``cutoff_used`` — AUDIT-C / SDS / DUDIT / ASRS-6 / AAQ-II; the cutoff
      that was applied (AUDIT-C 3 or 4, SDS 3-5 by substance, DUDIT 2 or 6
      by sex, ASRS-6 4 of 6 fired items, AAQ-II 24 per Bond 2011).
    - ``positive_screen`` — AUDIT-C / SDS / DUDIT / K6 / PHQ-2 / GAD-2 /
      OASIS / PC-PTSD-5 / MDQ / ASRS-6 / AAQ-II; whether the cutoff gate is met.
    - ``t3_reason`` — PHQ-9 / C-SSRS when ``requires_t3`` is True;
      a short machine-readable reason code for logging/display.
    - ``triggering_items`` — C-SSRS / ASRS-6; 1-indexed item numbers that
      drove the screen decision.  For C-SSRS these are the positive
      items that forced the risk band; for ASRS-6 these are the items
      whose Likert response met their per-item firing threshold
      (inattentive ≥ 2, hyperactive ≥ 3 per Kessler 2005 Figure 1).
      Empty tuple when no items fired.
    - ``subscales`` — multi-subscale instruments; a map of
      subscale-name → subscale-total.  Populated for URICA (four
      stages of change: precontemplation / contemplation / action /
      maintenance), PCL-5 (four DSM-5 clusters: intrusion / avoidance
      / negative_mood / hyperarousal), OCI-R (six OCD subtypes:
      hoarding / checking / ordering / neutralizing / washing /
      obsessing), BIS-11 (three Patton 1995 second-order factors:
      attentional / motor / non_planning), and DERS-16 (five
      Bjureberg 2016 emotion-dysregulation subscales: nonacceptance
      / goals / impulse / strategies / clarity).  Each subscale is a
      non-negative integer total on the scorer's native subscale
      scale (note asymmetric ranges: DERS-16 strategies 5-25,
      clarity 2-10, others 3-15).  Keys match the scorer-module
      constants (``SUBSCALE_LABELS`` / ``PCL5_CLUSTERS`` /
      ``OCIR_SUBSCALES`` / ``BIS11_SUBSCALES`` /
      ``DERS16_SUBSCALES``) so clinician-UI renderers key off one
      source of truth across the whole package.  Instruments without
      subscales (PHQ-9 / PHQ-2 / GAD-7 / GAD-2 / OASIS / K10 / K6 /
      SDS / DUDIT / ASRS-6 / AAQ-II / WSAS / WHO-5 / AUDIT / AUDIT-C / C-SSRS / PSS-10 / DAST-10 /
      MDQ / PC-PTSD-5 / ISI / PHQ-15 / PACS / Craving VAS /
      Readiness Ruler / DTCQ-8 / CD-RISC-10 / PSWQ / LOT-R) emit ``subscales=None``.

    For C-SSRS, ``total`` is ``positive_count`` (the number of yes
    answers, 0-6) and ``severity`` is the risk band string.  There is
    no clinically meaningful single-number "total" for C-SSRS, but
    positive_count is the closest analogue and clients can use it for
    trajectory tracking independently of band changes.

    For PACS (Flannery 1999), Craving VAS (Sayette 2000), Readiness
    Ruler (Rollnick 1999 / Heather 2008), DTCQ-8 (Sklar & Turner
    1999), DERS-16 (Bjureberg 2016), CD-RISC-10 (Campbell-Sills &
    Stein 2007), PSWQ (Meyer 1990), and LOT-R (Scheier 1994),
    ``severity`` is the literal sentinel ``"continuous"``.  None of these instruments publishes
    severity bands; the trajectory layer extracts the clinical
    signal from ``total`` directly — week-over-week Δ for PACS,
    within-episode Δ + EMA trajectory for VAS, week-over-week Δ for
    the Ruler, week-over-week Δ on the coping-self-efficacy mean
    for DTCQ-8, RCI-style change detection (Jacobson & Truax 1991)
    on total+subscales for DERS-16, RCI-style change on the total
    for CD-RISC-10 with the "below general-population mean (< 31)"
    flag surfaced as contextual UI only (not a classification, not
    a gate), RCI-style change on the total for PSWQ with the
    "above GAD-sample mean (≥ 60)" flag surfaced as contextual UI
    only, and RCI-style change on the total for LOT-R with the
    "below general-population mean (< 14)" flag surfaced as
    contextual UI only.  Direction semantics differ: VAS / PACS /
    DERS-16 / PSWQ are higher-is-worse; the Ruler / DTCQ-8 /
    CD-RISC-10 / LOT-R are higher-is-better (same direction as WHO-5).  Clients rendering these results must not attempt to
    classify status from ``severity`` — show ``total`` and the
    trajectory chart instead.  Direction semantics differ:
    VAS and PACS are higher-is-worse (craving rising = deterioration);
    the Ruler and DTCQ-8 are higher-is-better (motivation / coping-
    confidence rising = improvement, same direction as WHO-5).
    Clients rendering these results must not attempt to classify
    status from ``severity`` — show ``total`` and the trajectory chart
    instead.  DTCQ-8 additionally carries irreducible per-situation
    profile signal in the stored record's ``raw_items`` tuple; the
    response envelope exposes the aggregate ``total`` only, and
    clinician-UI surfaces reading the coping profile fetch the raw
    items through the PHI-boundary-gated repository path.
    """

    assessment_id: str
    instrument: Instrument
    total: int
    severity: str
    requires_t3: bool
    t3_reason: str | None = None
    index: int | None = None
    cutoff_used: int | None = None
    positive_screen: bool | None = None
    triggering_items: list[int] | None = None
    subscales: dict[str, int] | None = None
    instrument_version: str | None = None


def _validate_item_count(payload: AssessmentRequest) -> None:
    """Enforce per-instrument item count at the router boundary.

    Raises 422 with a specific message rather than letting the scorer
    raise ``InvalidResponseError`` later — same end behavior, but the
    error surface is one layer earlier and more diagnostic."""
    expected = _INSTRUMENT_ITEM_COUNTS[payload.instrument]
    if len(payload.items) != expected:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.item_count",
                "message": (
                    f"{payload.instrument} requires exactly {expected} items, "
                    f"got {len(payload.items)}"
                ),
            },
        )


def _dispatch(payload: AssessmentRequest) -> AssessmentResult:
    """Per-instrument dispatch — pure function over the payload.

    Extracted from ``submit_assessment`` so safety-event emission can
    happen in one place after a result is built (rather than threaded
    through every per-instrument branch).  Scorer exceptions propagate
    to the caller; the HTTP layer translates them to 422.
    """
    if payload.instrument == "phq9":
        result = score_phq9(payload.items)
        safety = evaluate_phq9(result)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="phq9",
            total=result.total,
            severity=result.severity,
            requires_t3=bool(safety and safety.requires_t3),
            t3_reason=safety.reason if safety else None,
            instrument_version=result.instrument_version,
        )
    if payload.instrument == "gad7":
        g = score_gad7(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="gad7",
            total=g.total,
            severity=g.severity,
            requires_t3=False,
            instrument_version=g.instrument_version,
        )
    if payload.instrument == "who5":
        w = score_who5(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="who5",
            total=w.raw_total,
            index=w.index,
            severity=w.band,
            requires_t3=False,
            instrument_version=w.instrument_version,
        )
    if payload.instrument == "audit":
        au = score_audit(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="audit",
            total=au.total,
            severity=au.band,
            requires_t3=False,
            instrument_version=au.instrument_version,
        )
    if payload.instrument == "audit_c":
        a = score_audit_c(payload.items, sex=payload.sex or "unspecified")
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="audit_c",
            total=a.total,
            severity="positive_screen" if a.positive_screen else "negative_screen",
            requires_t3=False,
            cutoff_used=a.cutoff_used,
            positive_screen=a.positive_screen,
            instrument_version=a.instrument_version,
        )
    if payload.instrument == "cssrs":
        # Bool coercion happens inside the scorer; passing int list
        # is fine.  ``behavior_within_3mo`` defaults to False at the
        # scorer when ``None`` is supplied — the safer default.
        c = score_cssrs_screen(
            payload.items,
            behavior_within_3mo=bool(payload.behavior_within_3mo),
        )
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="cssrs",
            total=c.positive_count,
            severity=c.risk,
            requires_t3=c.requires_t3,
            t3_reason="cssrs_acute_triage" if c.requires_t3 else None,
            triggering_items=list(c.triggering_items),
            instrument_version=c.instrument_version,
        )
    if payload.instrument == "pss10":
        p = score_pss10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pss10",
            total=p.total,
            severity=p.band,
            requires_t3=False,
            instrument_version=p.instrument_version,
        )
    if payload.instrument == "dast10":
        d = score_dast10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="dast10",
            total=d.total,
            severity=d.band,
            requires_t3=False,
            instrument_version=d.instrument_version,
        )
    if payload.instrument == "pcptsd5":
        # Prins 2016 — 5-item PTSD screen, positive at >= 3.  Total
        # carries the positive_count (0-5); severity echoes
        # positive/negative_screen uniform with AUDIT-C and MDQ so
        # a chart-view client rendering screen-style instruments
        # uses one projection layer across all three.
        pt = score_pcptsd5(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pcptsd5",
            total=pt.positive_count,
            severity=(
                "positive_screen" if pt.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=pt.positive_screen,
            instrument_version=pt.instrument_version,
        )
    if payload.instrument == "isi":
        # Bastien 2001 — 7-item 0-4 Likert, total 0-28.  severity is
        # the four-band Bastien label (none/subthreshold/moderate/
        # severe) so the wire shape matches PHQ-9 / GAD-7 severity-
        # band instruments.  No safety routing — ISI is a CBT-I /
        # sleep-medicine referral signal, not a crisis signal.
        i = score_isi(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="isi",
            total=i.total,
            severity=i.severity,
            requires_t3=False,
            instrument_version=i.instrument_version,
        )
    if payload.instrument == "pcl5":
        # Weathers 2013 / Blevins 2015 — 20-item 0-4 Likert, total
        # 0-80, positive at >= 33.  Wire envelope follows PC-PTSD-5 /
        # MDQ / AUDIT-C's positive/negative_screen semantic since
        # PCL-5 is a cutoff-driven screen (not a banded severity
        # instrument like PHQ-9).  DSM-5 cluster B/C/D/E subscales
        # (intrusion / avoidance / negative_mood / hyperarousal) are
        # surfaced on the ``subscales`` envelope map so the clinician-
        # UI timeline can render cluster-level trajectory lines
        # without a per-row repository re-read.  The mapping keys
        # match ``scoring.pcl5.PCL5_CLUSTERS`` — clinician-UI
        # renderers that key off the scorer-module constant pick up
        # the same names in the response payload.  The cluster
        # profile drives trauma-focused therapy selection (PE for
        # intrusion-dominant vs CPT for negative-mood-dominant vs EMDR
        # for mixed) at the intervention-selection layer.
        pcl = score_pcl5(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pcl5",
            total=pcl.total,
            severity=(
                "positive_screen" if pcl.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=pcl.positive_screen,
            subscales={
                "intrusion": pcl.cluster_intrusion,
                "avoidance": pcl.cluster_avoidance,
                "negative_mood": pcl.cluster_negative_mood,
                "hyperarousal": pcl.cluster_hyperarousal,
            },
            instrument_version=pcl.instrument_version,
        )
    if payload.instrument == "ocir":
        # Foa 2002 — 18-item 0-4 Likert, total 0-72, positive at
        # >= 21.  Wire envelope matches PCL-5's screen semantic.
        # Six 3-item subscales (hoarding / checking / ordering /
        # neutralizing / washing / obsessing) are surfaced on the
        # ``subscales`` envelope map so the clinician-UI surface
        # picks the right subtype-appropriate ERP protocol
        # (ERP-for-contamination on washing-dominant vs ERP-with-
        # response-prevention on checking-dominant vs CBT-H for
        # hoarding-dominant).  Unlike PCL-5's contiguous DSM-5
        # cluster ranges, OCI-R items are deliberately distributed
        # across the instrument (item 1 = hoarding, item 2 =
        # checking, item 3 = ordering, etc.) per Foa 2002 §2.2, so
        # the scorer's per-subscale summation is load-bearing — a
        # flat contiguous-slice reading would silently miscategorize
        # every subscale.  The wire keys match ``scoring.ocir.
        # OCIR_SUBSCALES`` dict keys so clinician-UI renderers key
        # off one source of truth.
        ocir = score_ocir(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="ocir",
            total=ocir.total,
            severity=(
                "positive_screen" if ocir.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=ocir.positive_screen,
            subscales={
                "hoarding": ocir.subscale_hoarding,
                "checking": ocir.subscale_checking,
                "ordering": ocir.subscale_ordering,
                "neutralizing": ocir.subscale_neutralizing,
                "washing": ocir.subscale_washing,
                "obsessing": ocir.subscale_obsessing,
            },
            instrument_version=ocir.instrument_version,
        )
    if payload.instrument == "phq15":
        # Kroenke 2002 — 15-item 0-2 Likert somatic symptom scale,
        # total 0-30.  Severity band (minimal/low/medium/high) uniform
        # with PHQ-9 / GAD-7 / ISI — banded-severity envelope, NOT the
        # positive/negative_screen envelope used by PCL-5 / PC-PTSD-5 /
        # OCI-R / MDQ.  No safety routing: PHQ-15 has no suicidality
        # item, and item 6 (chest pain) + item 8 (fainting) are
        # medical-urgency signals surfaced by the clinician-UI layer
        # separately rather than T3 triggers.  Sex-aware item 4
        # (menstrual problems) is handled upstream — the scorer takes
        # 15 pre-coded items; men code item 4 as 0 per Kroenke 2002.
        phq15 = score_phq15(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="phq15",
            total=phq15.total,
            severity=phq15.severity,
            requires_t3=False,
            instrument_version=phq15.instrument_version,
        )
    if payload.instrument == "bis11":
        # Patton 1995 — 30-item 1-4 Likert Barratt Impulsiveness Scale,
        # total 30-120.  Banded-severity envelope (low/normal/high) per
        # Stanford 2009 norms.  **First non-zero-based Likert in the
        # dispatch table** — the 1-4 range is pinned at the scorer and
        # enforced via InvalidResponseError → 422.  11 reverse-coded
        # items (positively-worded: "I plan tasks carefully") are
        # handled inside the scorer; callers submit raw 1-4 responses
        # and the stored record's ``total`` reflects the post-reversal
        # sum, not the raw-response sum.  No safety routing: BIS-11 is
        # a trait inventory with no suicidality / acute-harm item.
        # Three Patton 1995 second-order subscales (attentional /
        # motor / non_planning) are surfaced on the ``subscales``
        # envelope map so the intervention layer picks the profile-
        # appropriate variant: attentional-dominant → mindfulness-
        # based attention training, motor-dominant → response-delay
        # / impulse-interruption drills, non_planning-dominant →
        # implementation-intention scripting.  Distributed-item
        # composition (same as OCI-R — items are interleaved across
        # subscales, not contiguous) means the scorer's per-subscale
        # summation is load-bearing; a contiguous-slice read would
        # corrupt the aggregate.  Wire keys match
        # ``scoring.bis11.BIS11_SUBSCALES``.
        bis = score_bis11(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="bis11",
            total=bis.total,
            severity=bis.severity,
            requires_t3=False,
            subscales={
                "attentional": bis.subscale_attentional,
                "motor": bis.subscale_motor,
                "non_planning": bis.subscale_non_planning,
            },
            instrument_version=bis.instrument_version,
        )
    if payload.instrument == "pacs":
        # Flannery 1999 — 5-item 0-6 Likert Penn Alcohol Craving Scale,
        # total 0-30.  **Continuous-severity envelope** (new in Sprint 34)
        # — Flannery 1999 publishes no severity bands and the clinical
        # literature treats PACS as a week-over-week trajectory measure,
        # not a categorical screen.  The router emits
        # ``severity="continuous"`` as a sentinel so every instrument in
        # the dispatch table has a severity field (banded / screen /
        # continuous), without hand-rolling bands that would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds" rule.  No
        # safety routing: craving is the *pre-behavior* signal the
        # platform intervenes on within the 60-180 second urge-to-action
        # window, not a T3 crisis marker.  A positive PACS + acute
        # suicidality still needs co-administered PHQ-9 / C-SSRS to fire
        # T3, consistent with the PHQ-15 / OCI-R / ISI safety posture.
        pacs = score_pacs(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pacs",
            total=pacs.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=pacs.instrument_version,
        )
    if payload.instrument == "craving_vas":
        # Sayette 2000 synthesis — single-item 0-100 Visual Analog Scale
        # of momentary craving.  **Continuous-severity envelope** (same
        # sentinel as PACS) — the VAS publishes no bands and the
        # literature treats it as a per-user / per-episode relative
        # signal, not a categorical severity measure.  The clinical
        # value lives in three places, none of which are absolute
        # cutoffs: (a) within-user trajectory across EMA sessions,
        # (b) within-episode Δ (pre-intervention VAS minus post-
        # intervention VAS) — the efficacy signal the bandit trains
        # on, and (c) baseline-relative deviation against the user's
        # running EMA mean.  This is the EMA partner to PACS (weekly
        # aggregated) — PACS answers 'has this week been harder?',
        # VAS answers 'is the intervention working right now?'  No
        # safety routing: a VAS of 100 is 'peak subjective craving',
        # not active suicidality; acute ideation is gated by PHQ-9
        # item 9 / C-SSRS, consistent with the PACS / PHQ-15 / OCI-R /
        # ISI safety-posture convention.  The substance context
        # (alcohol / cannabis / nicotine / opioid / gambling /
        # porn-use) is surfaced at the UI layer and stored alongside
        # the assessment at the repository layer — the scorer is
        # substance-agnostic so one validated instrument serves every
        # vertical without per-vertical branching.  See
        # ``scoring/craving_vas.py``.
        vas = score_craving_vas(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="craving_vas",
            total=vas.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=vas.instrument_version,
        )
    if payload.instrument == "readiness_ruler":
        # Rollnick 1999 / Heather 2008 — single-item 0-10 motivation-
        # to-change ruler.  **Continuous-severity envelope** (same
        # sentinel as PACS / VAS) — Heather 2008 publishes no bands,
        # and the MI stages-of-change anchors (pre-contemplation /
        # contemplation / action) are pedagogical descriptions, NOT
        # clinically-validated cutoffs with consensus uptake.
        # Fabricating bands from pedagogical anchors would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds" rule.
        # **Direction semantics: higher is better** — unlike Craving
        # VAS (higher = worse craving) or PHQ-9 / GAD-7 / PSS-10
        # (higher = worse symptom).  The trajectory layer must apply
        # the same direction-inversion logic it uses for WHO-5 when
        # Ruler trajectories are added; until then, wire-layer
        # behavior is identical to PACS / VAS (emit raw total + the
        # ``"continuous"`` sentinel).  The Ruler is URICA's single-
        # item equivalent — the full 16-item 4-subscale stages-of-
        # change instrument is a separate future sprint per
        # Docs/Technicals/12_Psychometric_System.md §3.1 row #10.
        # No safety routing: a Ruler score of 0 ("not ready at all")
        # is a motivation signal routing to MI-scripted interventions
        # (decisional-balance elicitation, change-talk amplification),
        # not a crisis signal.  Acute ideation is gated by PHQ-9 item
        # 9 / C-SSRS per the PACS / PHQ-15 / OCI-R / ISI / VAS
        # safety-posture convention.  See
        # ``scoring/readiness_ruler.py``.
        rr = score_readiness_ruler(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="readiness_ruler",
            total=rr.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=rr.instrument_version,
        )
    if payload.instrument == "dtcq8":
        # Sklar & Turner 1999 — 8-item Drug-Taking Confidence
        # Questionnaire short form.  Each item is a 0-100 integer
        # confidence-percentage score; the aggregate is the **mean**
        # across the 8 Marlatt 1985 situation categories, not the
        # sum.  The scorer exposes ``total`` as the mean rounded to
        # int (for AssessmentResult envelope compatibility) AND
        # ``mean`` as the exact float (for FHIR valueDecimal /
        # clinician-PDF precision).  The router emits ``total`` here;
        # the ``mean`` field flows through the repository record so
        # downstream consumers (trajectory layer, FHIR export) can
        # read the precise aggregate.  **Continuous-severity
        # envelope** (same sentinel as PACS / VAS / Ruler) — Sklar
        # 1999 publishes no bands and the "50% = moderate confidence"
        # clinician-training heuristic is pedagogical shorthand, not
        # a validated cutoff with consensus uptake.  Fabricating
        # bands would violate CLAUDE.md's "Don't hand-roll severity
        # thresholds" rule.  **Direction semantics: higher is
        # better** — the third higher-is-better instrument in the
        # package after WHO-5 and Readiness Ruler.  The trajectory
        # layer must apply the same direction-inversion logic when
        # DTCQ-8 trajectory coverage is added.  **Per-situation
        # profile signal** is load-bearing here (unique to DTCQ-8
        # among shipped instruments): the intervention layer reads
        # the 8-tuple via ``SITUATION_LABELS`` positional mapping to
        # pick skill-building tool variants matched to the weakest
        # Marlatt category (e.g. social-pressure weakness routes to
        # refusal-skills, unpleasant-emotions weakness routes to
        # distress-tolerance).  The wire response envelope surfaces
        # only the aggregate ``total``; clinician-UI surfaces
        # reading the full profile go through the
        # PHI-boundary-gated repository path.  No safety routing:
        # low coping self-efficacy is a skill-building signal, not
        # a crisis signal; acute ideation is gated by PHQ-9 item 9
        # / C-SSRS per the uniform safety-posture convention.  See
        # ``scoring/dtcq8.py``.
        d = score_dtcq8(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="dtcq8",
            total=d.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=d.instrument_version,
        )
    if payload.instrument == "urica":
        # McConnaughy 1983 / DiClemente & Hughes 1990 — 16-item
        # stages-of-change profile.  **First multi-subscale wire-
        # exposed instrument** in the package — the dispatch surfaces
        # the four subscale sums (precontemplation / contemplation /
        # action / maintenance) on the response envelope's ``subscales``
        # map so the intervention layer reads the stage profile
        # alongside the Readiness aggregate without a second round-trip.
        # The field shape is generic (``dict[str, int]``) so PCL-5
        # cluster surfacing, OCI-R subtypes, and BIS-11 subscales can
        # ride the same envelope in later sprints without wire-schema
        # churn.  **First signed total** — Readiness = ``C + A + M −
        # PC`` is a signed int (range −8 to +56); a negative value is
        # clinically meaningful (precontemplation-dominant profile).
        # **Continuous-severity envelope** (same sentinel as PACS /
        # VAS / Ruler / DTCQ-8) — DiClemente & Hughes 1990 publishes
        # no bands and the canonical analytic approach is
        # cluster-analysis of the profile, not cutoff thresholding.
        # Hand-rolling Readiness bands would violate CLAUDE.md's
        # "Don't hand-roll severity thresholds" rule.  **Direction
        # semantics: higher is better** — the fourth higher-is-better
        # instrument after WHO-5 / Ruler / DTCQ-8.  The trajectory
        # layer must apply the same direction-inversion logic when
        # URICA trajectory coverage is added.  No safety routing:
        # a precontemplation-dominant profile is a motivation signal
        # routing to MI-scripted interventions, not a crisis signal.
        # Acute ideation is gated by PHQ-9 item 9 / C-SSRS per the
        # uniform safety-posture convention.  See ``scoring/urica.py``.
        u = score_urica(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="urica",
            total=u.total,
            severity="continuous",
            requires_t3=False,
            subscales={
                "precontemplation": u.precontemplation,
                "contemplation": u.contemplation,
                "action": u.action,
                "maintenance": u.maintenance,
            },
            instrument_version=u.instrument_version,
        )
    if payload.instrument == "phq2":
        # Kroenke 2003 — 2-item 0-3 Likert ultra-short depression
        # pre-screener composed of PHQ-9 items 1 (anhedonia) and 2
        # (depressed mood).  Total 0-6, positive at >= 3.  **Daily-EMA
        # partner** to the weekly PHQ-9 full form: when PHQ-2 crosses
        # the positive cutoff, the clinician workflow recommends
        # promotion to a full PHQ-9 for severity banding and item-9
        # safety evaluation.  Wire envelope uses the cutoff-only
        # semantic (severity = positive_screen / negative_screen)
        # uniform with PC-PTSD-5 / MDQ / AUDIT-C — NOT the banded
        # severity envelope used by PHQ-9 itself.  Kroenke 2003
        # publishes no PHQ-2 severity bands and the downstream
        # literature is uniform in not endorsing any — back-calculating
        # bands from PHQ-9 thresholds would violate CLAUDE.md's
        # "Don't hand-roll severity thresholds" rule.  No safety
        # routing: PHQ-2 deliberately excludes PHQ-9 item 9
        # (suicidality), so the daily-EMA surface does not carry an
        # in-line safety-routing interrupt.  Acute ideation stays
        # gated by the weekly PHQ-9 / C-SSRS on-demand — a patient
        # needing daily depression check-ins AND at acute risk should
        # be on PHQ-9 or C-SSRS, not on PHQ-2 with a safety hack.
        # See ``scoring/phq2.py``.
        p2 = score_phq2(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="phq2",
            total=p2.total,
            severity=(
                "positive_screen" if p2.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=p2.positive_screen,
            instrument_version=p2.instrument_version,
        )
    if payload.instrument == "gad2":
        # Kroenke 2007 — 2-item 0-3 Likert ultra-short anxiety pre-
        # screener composed of GAD-7 items 1 (nervousness / on-edge)
        # and 2 (uncontrolled worry).  Total 0-6, positive at >= 3.
        # **Companion to PHQ-2** on the daily-EMA affective check-in
        # surface: PHQ-2 covers depression, GAD-2 covers anxiety, and
        # together they form the 4-item daily screener that captures
        # ~80% of primary-care mental-health screening volume in ~30
        # seconds.  When GAD-2 crosses the positive cutoff across
        # consecutive daily checks, the clinician workflow recommends
        # promotion to a full GAD-7 for severity banding.  Wire
        # envelope uses the cutoff-only semantic (severity =
        # positive_screen / negative_screen) uniform with PHQ-2 /
        # PC-PTSD-5 / MDQ / AUDIT-C — NOT the banded envelope used
        # by GAD-7 itself.  Kroenke 2007 publishes no GAD-2 severity
        # bands; back-calculating from GAD-7 thresholds would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds" rule.
        # No safety routing: GAD-2 has no suicidality item (neither
        # does GAD-7 full form), so anxiety screens never fire T3.
        # Acute ideation stays gated by PHQ-9 item 9 / C-SSRS on
        # demand per the uniform safety-posture convention.  See
        # ``scoring/gad2.py``.
        g2 = score_gad2(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="gad2",
            total=g2.total,
            severity=(
                "positive_screen" if g2.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=g2.positive_screen,
            instrument_version=g2.instrument_version,
        )
    if payload.instrument == "oasis":
        # Norman 2006 / Campbell-Sills 2009 — 5-item 0-4 Likert anxiety
        # severity AND impairment measure.  Items are: frequency (1),
        # intensity (2), avoidance (3), work/school/home impairment (4),
        # social impairment (5).  Total 0-20, positive at >= 8.
        # **Anxiety-impairment complement** to GAD-7 (symptom severity
        # only) — the two instruments deliberately catch different
        # presentations: GAD-7-positive / OASIS-negative = intense
        # symptoms, not yet functionally costly; GAD-7-negative /
        # OASIS-positive = low-intensity "functional" anxiety whose
        # cost is in avoidance + impairment.  Wire envelope uses the
        # cutoff-only semantic (severity = positive_screen /
        # negative_screen) uniform with PHQ-2 / GAD-2 / PC-PTSD-5 /
        # MDQ / AUDIT-C.  No severity bands (Norman 2006 validates
        # only the total; hand-rolling bands would violate CLAUDE.md's
        # "Don't hand-roll severity thresholds" rule).  No subscales
        # wire-exposed (Norman 2006's factor analysis supports a
        # single-factor structure; splitting symptom / avoidance /
        # impairment subscales is unvalidated).  No safety routing:
        # OASIS has no suicidality item — none of the 5 items probes
        # acute-harm intent — so anxiety-impairment screens never
        # fire T3.  See ``scoring/oasis.py``.
        oa = score_oasis(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="oasis",
            total=oa.total,
            severity=(
                "positive_screen" if oa.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=oa.positive_screen,
            instrument_version=oa.instrument_version,
        )
    if payload.instrument == "k10":
        # Kessler 2002 / Andrews & Slade 2001 — 10-item 1-5 Likert
        # cross-cutting psychological-distress screener.  Total 10-50.
        # Banded envelope per Andrews & Slade 2001:
        #   10-19 low / 20-24 moderate / 25-29 high / 30-50 very_high.
        # Wire uses the banded severity envelope uniform with PHQ-9 /
        # GAD-7 / PSS-10 — severity is the band string, not a screen
        # sentinel.  **First banded instrument with ITEM_MIN=1** — the
        # scorer enforces the 1-5 range; clients that mistakenly send
        # 0-indexed items hit the out-of-range validator.  No subscale
        # exposure (Kessler 2002 validates the unidimensional total;
        # splitting depression / anxiety subscales is unvalidated).
        # No safety routing: K10's hopelessness items (4 = hopeless,
        # 9 = so sad, 10 = worthless) are *affect* probes, not *intent*
        # probes — a "very high" K10 is a strong signal to work up the
        # patient with safety-gated instruments (PHQ-9 item 9 / C-SSRS),
        # not an excuse to skip them.  See ``scoring/k10.py``.
        k = score_k10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="k10",
            total=k.total,
            severity=k.severity,
            requires_t3=False,
            instrument_version=k.instrument_version,
        )
    if payload.instrument == "sds":
        # Gossop 1995 Severity of Dependence Scale — 5-item 0-3 Likert
        # psychological-dependence screen, total 0-15.  Cutoff envelope
        # (uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / AUDIT-C):
        # severity is "positive_screen" / "negative_screen"; the
        # substance-keyed cutoff is echoed via ``cutoff_used`` so the
        # clinician-UI renders "positive at ≥ N".  ``substance=None``
        # falls back to the conservative unspecified cutoff (≥ 3) —
        # same safety posture as AUDIT-C sex=None.  **First instrument
        # with substance-adaptive cutoffs** — extends the AUDIT-C
        # per-population-cutoff pattern (sex) to a second demographic
        # axis (substance).  No subscales (Gossop 1995 validated
        # unidimensionality), no T3 (no suicidality item — a high SDS
        # is a psychological-dependence work-up signal, not a crisis
        # signal).  See ``scoring/sds.py``.
        s = score_sds(
            payload.items,
            substance=payload.substance or "unspecified",
        )
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="sds",
            total=s.total,
            severity=(
                "positive_screen" if s.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            cutoff_used=s.cutoff_used,
            positive_screen=s.positive_screen,
            instrument_version=s.instrument_version,
        )
    if payload.instrument == "k6":
        # Kessler 2003 K6 short form — 6-item 1-5 Likert
        # psychological-distress screen, total 6-30, cutoff ≥ 13 for
        # probable serious mental illness (SMI).  Cutoff envelope
        # (severity = "positive_screen" / "negative_screen") uniform
        # with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / AUDIT-C / SDS —
        # NOT the K10 banded envelope, because Kessler 2003 published
        # only the binary SMI gate.  Hand-rolling K10-style bands onto
        # K6 totals would violate CLAUDE.md's "Don't hand-roll severity
        # thresholds" rule.  ITEM_MIN = 1 (same as K10) — a 0-indexed
        # client would shift totals by 6 and potentially collapse a
        # positive SMI screen.  No subscales: K6 items were selected
        # for their loading on the K10 dominant factor; the scale is
        # unidimensional by design.  No T3: K6's hopelessness /
        # depressed / worthless items (2 / 4 / 6) are affect probes,
        # not intent probes — same posture as K10.  See
        # ``scoring/k6.py``.
        k6 = score_k6(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="k6",
            total=k6.total,
            severity=(
                "positive_screen" if k6.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=k6.positive_screen,
            instrument_version=k6.instrument_version,
        )
    if payload.instrument == "dudit":
        # Berman 2005 Drug Use Disorders Identification Test — 11-item
        # non-alcohol substance-use screen.  Novel per-index validator:
        # items 1-9 take the 0-4 Likert envelope, items 10-11 take the
        # {0, 2, 4} trinary envelope; a response of 1 or 3 on items
        # 10-11 is rejected at the scorer even though it sits within
        # the numerical range 0-4.  Sex-keyed cutoff extends the
        # AUDIT-C precedent (men ≥ 6 / women ≥ 2 / unspecified ≥ 2).
        # Cutoff envelope uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 /
        # MDQ / AUDIT-C / SDS / K6.  ``cutoff_used`` echoes the sex-
        # keyed cutoff.  No subscales (Berman 2003 validated at the
        # unidimensional screening-score level), no T3 (loss-of-
        # control / consequence items are not suicidality probes).
        # See ``scoring/dudit.py``.
        du = score_dudit(payload.items, sex=payload.sex or "unspecified")
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="dudit",
            total=du.total,
            severity=(
                "positive_screen" if du.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            cutoff_used=du.cutoff_used,
            positive_screen=du.positive_screen,
            instrument_version=du.instrument_version,
        )
    if payload.instrument == "asrs6":
        # Kessler 2005 6-item WHO Adult ADHD Self-Report Scale screener.
        # NOVEL weighted-threshold wire shape: items 1-3 (inattentive)
        # fire at Likert ≥ 2, items 4-6 (hyperactive/impulsive) fire at
        # Likert ≥ 3, and the screen decision is the count of fired
        # items (≥ 4 of 6 is positive).  The scorer's raw-Likert-sum
        # ``total`` (0-24) is surfaced for trajectory tracking but MUST
        # NOT be used as the screen input — a ``total`` of 12 can occur
        # with only one fired item.  ``cutoff_used`` echoes the count
        # cutoff (= 4, a constant) so the clinician-UI renders
        # "positive at ≥ 4 of 6 items"; callers rendering the cutoff
        # don't need to import ASRS6_POSITIVE_CUTOFF.
        # ``triggering_items`` reuses the existing C-SSRS wire slot —
        # 1-indexed item numbers that met their per-item firing
        # threshold — so the clinician-UI can render "these symptoms
        # met their threshold" as an audit trail of the decision.
        # Cutoff envelope uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 /
        # MDQ / AUDIT-C / SDS / K6 / DUDIT.  No subscales (Kessler 2005
        # validates unidimensionally at count-of-fires; the inattentive
        # / hyperactive split is implicit in the thresholds, not a
        # surfaced subscale — full 18-item ASRS Symptom Checklist is
        # the factor-level instrument).  No T3 (ASRS-6 has no safety
        # item — items 5 and 6 probe hyperactivity, not suicidality).
        # See ``scoring/asrs6.py``.
        ar = score_asrs6(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="asrs6",
            total=ar.total,
            severity=(
                "positive_screen" if ar.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            cutoff_used=ASRS6_POSITIVE_CUTOFF,
            positive_screen=ar.positive_screen,
            triggering_items=list(ar.triggering_items),
            instrument_version=ar.instrument_version,
        )
    if payload.instrument == "aaq2":
        # Bond 2011 Acceptance and Action Questionnaire-II — 7-item
        # transdiagnostic measure of psychological inflexibility, the
        # ACT (Acceptance and Commitment Therapy) target construct.
        # **First 1-7 Likert instrument in the package** — the widened
        # per-item resolution (7 points vs 5) reduces ceiling / floor
        # compression observed in earlier AAQ versions and is load-
        # bearing at the sensitivity layer (Bond 2011).
        # ``ITEM_MIN = 1`` is shared with K10 / K6 but the 7-point
        # ceiling is novel; the scorer rejects 0 (even though 0-indexed
        # instruments accept it) and accepts 6 / 7 (even though K10 /
        # K6 would reject them).  Cutoff ≥ 24 per Bond 2011 (ROC-
        # derived vs SCID-II, sensitivity 0.75 / specificity 0.80) —
        # constant across all inputs, unlike AUDIT-C / SDS / DUDIT
        # where the cutoff varies by demographic axis.  Cutoff envelope
        # uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / AUDIT-C /
        # SDS / K6 / DUDIT / ASRS-6.  No subscales (Bond 2011 CFA
        # supports unidimensional structure).  No banded severity
        # (Bond 2011 published only the ≥ 24 cutoff).  No T3 (AAQ-II
        # has no suicidality item — "painful experiences" / "afraid of
        # feelings" items are process-of-avoidance probes, not intent
        # probes).  Clinically: positive screen routes a craving
        # episode to ACT-variant intervention tools (defusion / values-
        # clarification / willingness exercises) at the bandit layer
        # when experiential avoidance is the active process.  See
        # ``scoring/aaq2.py``.
        aq = score_aaq2(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="aaq2",
            total=aq.total,
            severity=(
                "positive_screen" if aq.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            cutoff_used=aq.cutoff_used,
            positive_screen=aq.positive_screen,
            instrument_version=aq.instrument_version,
        )
    if payload.instrument == "wsas":
        # Mundt 2002 Work and Social Adjustment Scale — 5-item
        # functional-impairment measure; the canonical IAPT /
        # stepped-care functional outcome, administered alongside
        # PHQ-9 and GAD-7 at every session to track the functional
        # arc independently of symptom change (Clark 2011).
        # **First 0-8 Likert instrument in the package** — widest
        # per-item envelope yet; prior widest was AAQ-II's 1-7.
        # Mundt 2002's 9-point scale gives sufficient resolution
        # for RCI-grade change detection.  ``ITEM_MIN = 0`` is
        # shared with every 0-indexed instrument; the ceiling of
        # 8 is novel and the scorer rejects 9 at the validator.
        # Total 0-40.  Banded severity per Mundt 2002 — subclinical
        # [0, 10), significant [10, 20), severe [20, 40].
        # Cut-points at 10 and 20 derived against SCID-diagnosed
        # depressive-episode patients.  Per CLAUDE.md "don't hand-
        # roll severity thresholds", the scorer ships exactly these
        # three bands — a moderate-severe/severe split is refused.
        # Banded wire envelope uniform with PHQ-9 / GAD-7 / ISI /
        # DAST-10 / PCL-5 / OCI-R / BIS-11 / PHQ-15 / K10 / DUDIT.
        # No ``cutoff_used`` / ``positive_screen`` (banded, not
        # cutoff).  No subscales (Mundt 2002 CFA — unidimensional;
        # productive-vs-social split was explicitly rejected).
        # No T3 — WSAS items probe work / home / social / private /
        # relationships, none referencing suicidality.  A severe
        # WSAS routes behavioral-activation / committed-action tool
        # variants at the bandit layer, not to the crisis path.
        # See ``scoring/wsas.py``.
        ws = score_wsas(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="wsas",
            total=ws.total,
            severity=ws.severity,
            requires_t3=False,
            instrument_version=ws.instrument_version,
        )
    if payload.instrument == "ders16":
        # Bjureberg 2016 Difficulties in Emotion Regulation Scale —
        # 16-item short form of DERS-36 (Gratz & Roemer 2004); the
        # validated measure of emotion dysregulation, the DBT target
        # construct.  Closes the DBT-alignment gap at the platform
        # assessment layer: AAQ-II measures the ACT target, PHQ-9 /
        # GAD-7 measure CBT-aligned symptom severity, and DERS-16
        # measures the regulatory-process dimension that DBT
        # interventions (distress-tolerance, emotion regulation,
        # wise-mind, radical acceptance) directly address.  Together
        # with AAQ-II and PHQ-9 / GAD-7, DERS-16 completes the
        # three-way process-target triangle so the contextual bandit
        # can route process-level decisions to the therapeutic frame
        # whose target the patient's profile loads most heavily on.
        # 16 items, 1-5 Likert (Almost never → Almost always); total
        # 16-80.  All items worded in the dysregulation direction
        # (Bjureberg 2016 pruned DERS-36's awareness-subscale
        # reverse-keyed items), so no reverse-coding logic needed.
        # **First 5-subscale instrument** — Bjureberg 2016 Table 2:
        # nonacceptance (items 9, 10, 13; 3-15), goals (items 3, 7,
        # 15; 3-15), impulse (items 4, 8, 11; 3-15), strategies
        # (items 5, 6, 12, 14, 16; 5-25 — widest), clarity (items 1,
        # 2; 2-10 — narrowest).  Subscale dict surfaced on the
        # envelope's ``subscales`` field because the intervention
        # layer reads the 5-tuple profile to pick DBT skill modules:
        # impulse-dominant → distress-tolerance (TIP/STOP/self-
        # soothe), strategies-dominant → cope-ahead / opposite-
        # action, clarity-dominant → observe/describe mindfulness,
        # nonacceptance-dominant → self-compassion, goals-dominant
        # → wise-mind / mindfulness-of-current-activity.
        # **No severity bands** — Bjureberg 2016 did NOT publish
        # banded thresholds, and downstream sample-specific cutoffs
        # are not cross-calibrated.  Per CLAUDE.md "don't hand-roll
        # severity thresholds", DERS-16 ships as a continuous
        # dimensional measure uniform with Craving VAS / PACS — the
        # envelope carries ``severity="continuous"`` as the sentinel;
        # trajectory layer extracts the clinical signal via RCI-style
        # change detection (Jacobson & Truax 1991) on both the total
        # and each subscale rather than banded classification.
        # ``cutoff_used`` / ``positive_screen`` NOT set (continuous,
        # not cutoff).  No T3 — items 4/8 ("out of control") probe
        # impulse-control loss but not acute intent; item 14 ("feel
        # very bad about myself") probes self-critical affect but
        # not suicidality.  Acute ideation screening stays on PHQ-9
        # item 9 / C-SSRS.  See ``scoring/ders16.py``.
        dr = score_ders16(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="ders16",
            total=dr.total,
            severity="continuous",
            requires_t3=False,
            subscales={
                "nonacceptance": dr.subscale_nonacceptance,
                "goals": dr.subscale_goals,
                "impulse": dr.subscale_impulse,
                "strategies": dr.subscale_strategies,
                "clarity": dr.subscale_clarity,
            },
            instrument_version=dr.instrument_version,
        )
    if payload.instrument == "cdrisc10":
        # Campbell-Sills & Stein 2007 Connor-Davidson Resilience Scale
        # 10-item short form — the validated unidimensional refinement
        # of Connor & Davidson 2003's 25-item CD-RISC.  Measures trait
        # resilience: the capacity to adapt, recover, and maintain
        # function under stress, adversity, illness, and trauma.
        # **Closes the platform-core resilience construct gap** —
        # every product-layer affordance (resilience streak per
        # CLAUDE.md Rule #3, recovery-pathway framing, relapse-as-
        # data framing, compassion-first messaging) presupposes a
        # measurable resilience dimension.  Until CD-RISC-10 the
        # assessment layer had no validated resilience measure; with
        # it, the trajectory layer can answer "is the platform's
        # intervention arc moving this patient's resilience?", detect
        # the resilience-decoupling signal (CD-RISC-10 rises while
        # PHQ-9 stays flat — the early-recovery leading indicator
        # Connor & Davidson 2003 documented), and surface patients
        # with below-population resilience at intake for heavier
        # scaffolding.  Completes the cross-construct trajectory
        # stack: process measures (AAQ-II / DERS-16) fall, symptom
        # measures (PHQ-9 / GAD-7 / PCL-5 / K10) fall, functional
        # measures (WSAS) recover, and resilience measures (CD-RISC-
        # 10) RISE — the full recovery signature.
        # 10 items, 0-4 Likert (not true at all → true nearly all
        # the time); total 0-40.  All items worded in the RESILIENCE
        # direction — **higher is better**, same directionality as
        # WHO-5 / DTCQ-8 / Readiness Ruler, **opposite** of PHQ-9 /
        # GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 / WSAS.  Clients
        # rendering the total must NOT reuse higher-is-worse visual
        # language — a falling CD-RISC-10 is a DETERIORATION.
        # **No severity bands** — Campbell-Sills & Stein 2007
        # published general-population norms (mean 31.8 ± 5.4 in
        # U.S. adult sample N=764) but NOT banded clinical
        # thresholds.  Connor & Davidson 2003's 25-item cutpoints
        # do not translate linearly; downstream 10-item tertiles
        # are sample-specific and not cross-calibrated.  Per
        # CLAUDE.md "don't hand-roll severity thresholds", CD-RISC-
        # 10 ships as a continuous dimensional measure uniform with
        # Craving VAS / PACS / DERS-16; envelope carries
        # ``severity="continuous"``.  The clinician-UI layer may
        # surface a "below general-population mean" flag (score
        # < 31) as context — that flag is NOT a classification and
        # NOT a gate.  Unidimensional per Campbell-Sills & Stein
        # 2007 CFA (CFI .95, RMSEA .06) — the 25-item's five-factor
        # structure was explicitly rejected for the 10-item form,
        # so ``subscales`` is NOT emitted (distinct from DERS-16's
        # 5-subscale surface).  No T3 — the 10 items probe
        # resilience-capacity constructs (adaptability, coping,
        # humor, bounce-back, goal persistence, focus under
        # pressure, failure-tolerance, self-strength, distress-
        # tolerance); none probe suicidality, self-harm, or crisis
        # behavior.  Acute ideation screening stays on PHQ-9 item 9
        # / C-SSRS.  ``cutoff_used`` / ``positive_screen`` NOT set
        # (continuous, not cutoff).  See ``scoring/cdrisc10.py``.
        cd = score_cdrisc10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="cdrisc10",
            total=cd.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=cd.instrument_version,
        )
    if payload.instrument == "pswq":
        # Meyer 1990 Penn State Worry Questionnaire — the gold-standard
        # 16-item measure of trait-level worry, the CBT-for-GAD
        # process-target instrument.  GAD-7 measures anxiety symptoms
        # over a 2-week window (state severity); PSWQ measures the
        # dispositional worry process that cognitive therapy for GAD
        # explicitly targets.  A patient can have controlled symptoms
        # (low GAD-7) but persistent worry trait (high PSWQ), or vice
        # versa — the two are orthogonal clinical axes.  PSWQ
        # complements AAQ-II (ACT target: inflexibility), DERS-16 (DBT
        # target: dysregulation), PCL-5 (trauma-driven hyperarousal),
        # OCI-R (compulsive subtype), and the symptom-severity cluster
        # so the intervention-selection layer can route worry-driven
        # compulsive cycles (hypervigilant checking, pre-emptive
        # reassurance-seeking, catastrophization-driven avoidance) to
        # CBT-for-GAD tool variants: worry-postponement,
        # decatastrophizing, uncertainty-acceptance exposures.
        # 16 items, 1-5 Likert (1 = "not at all typical of me", 5 =
        # "very typical of me"); total 16-80.  **First reverse-keying
        # pattern in the package** — items 1, 3, 8, 10, 11 are worded
        # in the worry-ABSENT direction (e.g., "I do not tend to worry
        # about things.") so a high raw Likert on those items reflects
        # LOW trait-worry.  The scorer applies the arithmetic-
        # reflection flip (``flipped = 6 - raw``) to those items
        # before summing so every post-flip item contributes in the
        # higher-is-more-worry direction uniformly.  Mixed-direction
        # design is deliberate: Meyer 1990 included reverse-keyed
        # items to suppress acquiescent-response bias (an all-5s
        # responder scores 60, not 80; an all-1s responder scores 36,
        # not 16 — the design self-catches response-set artifacts).
        # Audit-trail invariant: the scorer's ``items`` field
        # preserves the PATIENT'S raw pre-flip responses, not the
        # internal post-flip values — so a clinician reviewing the
        # stored record sees what the patient actually ticked, not
        # the scorer's internal representation.
        # Higher-is-worse direction (same as PHQ-9 / GAD-7 / DERS-16 /
        # PCL-5 / OCI-R / K10 / WSAS; opposite of WHO-5 / DTCQ-8 /
        # Readiness Ruler / CD-RISC-10).
        # **No severity bands** — Meyer 1990 published GAD and
        # general-pop means (~67 / ~48) but no cross-calibrated
        # cutpoints.  Downstream cuts (Behar 2003: 45/62 tertiles in
        # students; Startup & Erickson 2006: 56+ GAD-diagnostic in
        # treatment-seekers; Fresco 2003: mid-50s GAD-threshold) are
        # sample-specific and not cross-calibrated against a shared
        # clinical criterion.  Per CLAUDE.md "don't hand-roll severity
        # thresholds", PSWQ ships as a continuous dimensional measure
        # uniform with DERS-16 / CD-RISC-10 / Craving VAS / PACS;
        # envelope carries ``severity="continuous"``.  Clinician-UI
        # layer may surface an "above GAD-sample mean" context flag
        # (score ≥ 60) — NOT a classification, NOT a gate.
        # Unidimensional per Meyer 1990 / Brown 1992 CFA — no
        # subscales dict (distinct from DERS-16's 5-subscale surface).
        # ``cutoff_used`` / ``positive_screen`` NOT set (continuous,
        # not cutoff).  No T3 — all 16 items probe the worry-process
        # construct (intensity, persistence, uncontrollability,
        # chronicity); item 2 ("My worries overwhelm me.") and item
        # 14 ("Once I start worrying, I cannot stop.") at ceiling
        # endorse GAD-DSM-5-criterion uncontrollability, NOT
        # suicidality.  Acute ideation screening stays on PHQ-9 item
        # 9 / C-SSRS.  See ``scoring/pswq.py``.
        pw = score_pswq(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pswq",
            total=pw.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=pw.instrument_version,
        )
    if payload.instrument == "lotr":
        # Scheier, Carver & Bridges 1994 Life Orientation Test Revised —
        # the validated 10-item (6 scored + 4 filler) revision of the
        # original 1985 LOT.  Measures **dispositional optimism** — the
        # generalized outcome expectancy that good things (rather than
        # bad) will happen to a person across life domains.  Pairs
        # DIRECTLY with CD-RISC-10 as the two-axis trait-positive-
        # psychology layer:  CD-RISC-10 answers "CAN I bounce back?"
        # (resilience capacity); LOT-R answers "DO I EXPECT good things
        # to happen?" (outcome expectancy).  Together they predict
        # treatment adherence (Carver 2010 meta-analysis: optimists stay
        # in treatment longer), effort allocation to implementation-
        # intention scaffolding (low-optimism patients route to short-
        # horizon small-wins scaffolding; high-optimism patients tolerate
        # longer arcs without disengagement), and recovery-slope
        # steepness (optimism predicts post-intervention recovery
        # velocity above baseline-severity covariates).
        # 10 items on the wire, 0-4 Likert (0 = "strongly disagree", 4 =
        # "strongly agree"); **6 items scored + 4 filler**.  Scored
        # positions (1-indexed): 1, 3, 4, 7, 9, 10.  Filler positions:
        # 2, 5, 6, 8 — included on the form to obscure the optimism
        # construct against demand characteristics (optimism is a
        # socially-desirable trait) but NOT summed.  **First filler-
        # item pattern in the package** — earlier instruments scored
        # every validated item.  The router accepts a 10-item payload
        # because the patient sees 10 items; the scorer drops the 4
        # filler positions during summation.  Audit-trail invariant:
        # the stored record preserves all 10 raw responses — what the
        # patient ticked — not just the 6 scored values.
        # Reuses the reverse-keying pattern from PSWQ.  Items 3, 7, 9
        # are pessimism-worded; the scorer applies the arithmetic-
        # reflection flip ``flipped = 4 - raw`` to those items before
        # summing so every post-flip scored item contributes in the
        # optimism direction uniformly.  Post-flip range 0-24.
        # **Higher is better** — uniform direction with CD-RISC-10 /
        # WHO-5 / DTCQ-8 / Readiness Ruler; opposite of PHQ-9 / GAD-7 /
        # DERS-16 / PCL-5 / OCI-R / K10 / WSAS / PSWQ.  Clients
        # rendering LOT-R scores must not reuse the higher-is-worse
        # visual language — a falling LOT-R is a DETERIORATION.
        # **No severity bands** — Scheier 1994 reported general-
        # population means (~14-15 U.S. adults) but published no
        # cross-calibrated clinical cutpoints; Carver 2010's 400-study
        # review did not yield a cross-calibrated threshold either.
        # Per CLAUDE.md "don't hand-roll severity thresholds", LOT-R
        # ships as a continuous dimensional measure uniform with PACS /
        # Craving VAS / DERS-16 / CD-RISC-10 / PSWQ; envelope carries
        # ``severity="continuous"``.  Clinician-UI layer may surface a
        # "below general-population mean" (< 14) context flag — NOT a
        # classification, NOT a gate.  Unidimensional per Scheier 1994
        # CFA — no subscales dict (Chang 1997's optimism/pessimism
        # two-factor split is sample-specific and deliberately
        # rejected).  ``cutoff_used`` / ``positive_screen`` NOT set
        # (continuous, not cutoff).  **No T3** — all 10 items probe
        # the optimism-pessimism construct and general-affect fillers;
        # none probe suicidality, self-harm, or crisis behavior.
        # Acute ideation screening stays on PHQ-9 item 9 / C-SSRS.
        # See ``scoring/lotr.py``.
        lr = score_lotr(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="lotr",
            total=lr.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=lr.instrument_version,
        )
    if payload.instrument == "tas20":
        # Bagby, Parker & Taylor 1994 Toronto Alexithymia Scale — the
        # validated 20-item measure of alexithymia (trait-level
        # difficulty identifying / describing feelings and
        # externally-oriented cognitive style).  Clinically: the
        # UPSTREAM emotion-identification construct that GATES
        # downstream emotion-regulation training — a patient who
        # cannot identify "I am angry right now" cannot plausibly
        # deploy an anger-regulation strategy.  The intervention-
        # selection layer reads high-DIF (Difficulty Identifying
        # Feelings) subscale scores as an affect-labeling
        # prerequisite check; high-alexithymia patients route FIRST
        # to emotion-identification work (Taylor & Bagby 2004
        # Emotion Regulation Therapy; DBT "Observe"/"Describe"
        # mindfulness skills before regulation skills; CBT
        # emotion-awareness logs before cognitive restructuring)
        # before DBT / CBT-style regulation tools return benefit.
        # Alexithymia additionally predicts poorer standard-CBT
        # response across depression / anxiety / addiction
        # populations (Ogrodniczuk 2011 meta-analysis), elevates
        # somatization risk (Taylor 1997; pairs with PHQ-15 for the
        # somatization cluster), and predicts SUD relapse (Cleland
        # 2005, Thorberg 2009 — alexithymic patients cannot preempt
        # emotional triggers to the craving-to-use pathway).
        # 20 items, 1-5 Likert.  Reverse-keying on items 4, 5, 10,
        # 18, 19 — reuses the PSWQ / LOT-R arithmetic-reflection
        # idiom (``flipped = 6 - raw``) before summing.  Three
        # subscales per Bagby 1994 CFA: DIF (7 items: 1, 3, 6, 7,
        # 9, 13, 14), DDF (5 items: 2, 4, 11, 12, 17), EOT (8
        # items: 5, 8, 10, 15, 16, 18, 19, 20).  Subscale sums
        # reconstruct to the 20-item total.  Surfaced via the
        # ``subscales`` map with keys ``dif`` / ``ddf`` / ``eot``
        # uniformly with DERS-16 dispatch shape (Bjureberg 2016
        # surfaces ``nonacceptance`` / ``goals`` / ``impulse`` /
        # ``strategies`` / ``clarity``).
        # **Higher-is-worse direction** — uniform with PHQ-9 /
        # GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 / WSAS / PSWQ;
        # opposite of WHO-5 / DTCQ-8 / Readiness Ruler /
        # CD-RISC-10 / LOT-R.
        # **Re-introduces banded classification** after five
        # consecutive continuous-sentinel sprints (WSAS, DERS-16,
        # CD-RISC-10, PSWQ, LOT-R).  Bagby 1994 published cross-
        # calibrated cutoffs replicated across Taylor 1997 /
        # Ogrodniczuk 2011 / Cleland 2005:
        #     ≤51    → non_alexithymic
        #     52-60  → possible_alexithymia
        #     ≥61    → alexithymic (clinical threshold)
        # These are validated thresholds (NOT hand-rolled per
        # CLAUDE.md "don't hand-roll severity thresholds") — pinned
        # as TAS20_NON_ALEXITHYMIC_UPPER / TAS20_POSSIBLE_UPPER in
        # the scorer module.  Notable clinical property: raw
        # all-3s midline → total 60 → possible_alexithymia (upper
        # edge of middle band), NOT non_alexithymic.  This is a
        # deliberate property of Bagby's threshold placement —
        # "neither agree nor disagree" on alexithymia-identifying
        # statements is itself evidence of poor emotional self-
        # knowledge; do NOT 'fix' the midline classification.
        # ``cutoff_used`` / ``positive_screen`` NOT set — TAS-20
        # uses three bands, not a single binary cutoff.  No T3 —
        # all 20 items probe emotion-identification / description
        # / externally-oriented cognition; none probe suicidality.
        # Acute ideation screening stays on PHQ-9 item 9 / C-SSRS.
        # See ``scoring/tas20.py``.
        ta = score_tas20(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="tas20",
            total=ta.total,
            severity=ta.band,
            requires_t3=False,
            subscales={
                "dif": ta.subscale_dif,
                "ddf": ta.subscale_ddf,
                "eot": ta.subscale_eot,
            },
            instrument_version=ta.instrument_version,
        )
    # mdq — Hirschfeld 2000 three-gate positive screen.  Both Part 2
    # (concurrent_symptoms) and Part 3 (functional_impairment) are
    # required.  Raise MdqInvalid here (translated to 422 at the HTTP
    # layer) rather than forwarding partial input to the scorer — the
    # scorer's own strict-bool / strict-str checks would reject with a
    # less diagnostic message, and silently defaulting to False / "none"
    # would produce a misleading negative_screen.
    if payload.concurrent_symptoms is None:
        raise MdqInvalid(
            "MDQ requires concurrent_symptoms (Part 2 yes/no) — "
            "omit instrument=mdq or supply the field"
        )
    if payload.functional_impairment is None:
        raise MdqInvalid(
            "MDQ requires functional_impairment (Part 3: one of "
            "'none'/'minor'/'moderate'/'serious')"
        )
    m = score_mdq(
        payload.items,
        concurrent_symptoms=payload.concurrent_symptoms,
        functional_impairment=payload.functional_impairment,
    )
    # ``total`` carries the positive-item count (0-13) — the closest
    # single-number analogue, and the value the FHIR Observation
    # emits as ``valueInteger``.  ``severity`` is the three-gate
    # outcome so the response shape is uniform with AUDIT-C's
    # positive/negative screen semantic.
    return AssessmentResult(
        assessment_id=str(uuid4()),
        instrument="mdq",
        total=m.positive_count,
        severity="positive_screen" if m.positive_screen else "negative_screen",
        requires_t3=False,
        positive_screen=m.positive_screen,
        instrument_version=m.instrument_version,
    )


def _emit_t3_safety_event(
    result: AssessmentResult, *, user_id: str | None
) -> None:
    """Record a T3 fire to the safety stream.

    Privacy contract (CLAUDE.md Rule #6 + Whitepaper 04 §T3):
    - Includes: ``assessment_id``, ``user_id``, ``instrument``,
      ``severity``, ``total``, ``t3_reason``, ``triggering_items``.
    - Excludes: raw item responses, free-text patient narrative, any
      LLM output.  The 1-indexed ``triggering_items`` numbers are
      diagnostic ("items 4 and 5 fired") and not item *values* (binary
      responses), so they're safe to include.

    The 2-year retention + clinical-ops-only IAM on the safety stream
    is what makes including ``user_id`` defensible — it's the same data
    boundary as a clinical chart note.
    """
    _safety.warning(
        "psychometric.t3_fire",
        assessment_id=result.assessment_id,
        user_id=user_id,
        instrument=result.instrument,
        severity=result.severity,
        total=result.total,
        t3_reason=result.t3_reason,
        triggering_items=result.triggering_items,
    )


@router.post("", response_model=AssessmentResult, status_code=201)
async def submit_assessment(
    payload: AssessmentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> AssessmentResult:
    """Score an assessment and return a deterministic typed result.

    Safety routing happens BEFORE the response is returned; PHQ-9
    callers rely on ``requires_t3`` to switch to the crisis path UI.
    See Docs/Whitepapers/04_Safety_Framework.md §T4.

    When ``requires_t3`` is True (PHQ-9 item 9 OR C-SSRS items 4/5/6
    +recency), a Merkle-chained event is emitted to the safety stream
    so on-call clinical operators can correlate with downstream contact
    workflows.  GAD-7 / WHO-5 / AUDIT-C / PSS-10 / DAST-10 never fire
    T3, so they never emit a safety event.

    Idempotency (RFC 7238-style):
    - Same ``Idempotency-Key`` + same body → return the cached
      response and skip side-effects (re-scoring, safety emission).
    - Same key + different body → 409 Conflict.
    - Entries expire after 24 h (see
      :mod:`discipline.shared.idempotency`).
    """
    _validate_item_count(payload)

    store = get_idempotency_store()
    body_hash = hash_pydantic(payload)
    cached = store.lookup(idempotency_key, body_hash)
    if isinstance(cached, Conflict):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "idempotency.conflict",
                "message": (
                    "Idempotency-Key was previously seen with a different "
                    "request body.  Pick a new key or resubmit the original "
                    "body."
                ),
            },
        )
    if isinstance(cached, Hit):
        # Replay: return stored response and skip the safety emission.
        # Storing an AssessmentResult in the cache means we re-serve the
        # same assessment_id + identical severity/total fields, which is
        # what a retrying client expects on a network retry.
        return cached.response

    try:
        result = _dispatch(payload)
    except (
        Phq9Invalid,
        Gad7Invalid,
        Who5Invalid,
        AuditInvalid,
        AuditCInvalid,
        CssrsInvalid,
        Pss10Invalid,
        Dast10Invalid,
        MdqInvalid,
        PcPtsd5Invalid,
        IsiInvalid,
        Pcl5Invalid,
        OcirInvalid,
        Phq15Invalid,
        PacsInvalid,
        Bis11Invalid,
        CravingVasInvalid,
        ReadinessRulerInvalid,
        Dtcq8Invalid,
        UricaInvalid,
        Phq2Invalid,
        Gad2Invalid,
        OasisInvalid,
        K10Invalid,
        SdsInvalid,
        K6Invalid,
        DuditInvalid,
        Asrs6Invalid,
        Aaq2Invalid,
        WsasInvalid,
        Ders16Invalid,
        Cdrisc10Invalid,
        PswqInvalid,
        LotrInvalid,
        Tas20Invalid,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation.invalid_payload", "message": str(exc)},
        ) from exc

    if result.requires_t3:
        _emit_t3_safety_event(result, user_id=payload.user_id)

    # Persist the record when a user_id is supplied.  Unauthenticated
    # diagnostic harnesses omit user_id; those submissions still score
    # and still emit safety events, but leave no history trail — which
    # matches the clinical posture that a phantom 'anonymous user'
    # timeline has no owner and no value.
    if payload.user_id:
        _persist_record(payload, result)

    # Only cache successful results.  A 422 re-raises on replay by
    # rerunning validation — the invalid payload is deterministic, so
    # caching the exception would save a few microseconds at the cost
    # of a much more complex cache invalidation story.
    store.store(idempotency_key, body_hash, result)
    return result


def _persist_record(
    payload: AssessmentRequest, result: AssessmentResult
) -> None:
    """Save the submitted event to the assessment repository.

    The record captures the full request context (raw items plus the
    per-instrument options ``sex`` / ``behavior_within_3mo``) so a
    later FHIR Observation re-render (Sprint 24 and beyond) does not
    need to re-fetch from a second source.  ``/history`` only surfaces
    the summary projection; the stored shape carries the full event.
    """
    repo = get_assessment_repository()
    # Convert list → tuple so the frozen dataclass stays hashable and
    # immutable.  A shared list reference would otherwise let a caller
    # mutate the stored record from the outside.
    raw_items = tuple(payload.items)
    triggering = (
        tuple(result.triggering_items)
        if result.triggering_items is not None
        else None
    )
    # Copy the subscale dict so a future caller that mutates their
    # reference (e.g. a test harness reusing a submission builder)
    # doesn't retroactively alter the stored record.  ``None`` stays
    # ``None`` — the repository record carries the "no subscales
    # applicable" signal verbatim for instruments that don't surface
    # subscales on the wire.
    subscales = (
        dict(result.subscales) if result.subscales is not None else None
    )
    record = AssessmentRecord(
        assessment_id=result.assessment_id,
        user_id=payload.user_id or "",
        instrument=result.instrument,
        total=result.total,
        severity=result.severity,
        requires_t3=result.requires_t3,
        raw_items=raw_items,
        created_at=repo.now(),
        t3_reason=result.t3_reason,
        index=result.index,
        cutoff_used=result.cutoff_used,
        positive_screen=result.positive_screen,
        triggering_items=triggering,
        subscales=subscales,
        instrument_version=result.instrument_version,
        sex=payload.sex,
        behavior_within_3mo=payload.behavior_within_3mo,
        concurrent_symptoms=payload.concurrent_symptoms,
        functional_impairment=payload.functional_impairment,
        substance=payload.substance,
    )
    repo.save(record)


# =============================================================================
# Trajectory — RCI (Reliable Change Index) per Jacobson & Truax 1991
# =============================================================================


# Direction literal mirrors the trajectories module so the response
# schema is type-safe across the boundary.  Keeping it in sync is
# checked at import time — a regression where the trajectories module
# adds/removes a direction would surface as a Pydantic validation
# error on the response, not a silent shape drift.
TrajectoryDirection = Literal[
    "improvement", "deterioration", "no_reliable_change", "insufficient_data"
]


class TrajectoryRequest(BaseModel):
    """Single-instrument trajectory query.

    ``instrument`` accepts any string — unknown values gracefully fall
    through to ``insufficient_data`` rather than 422-ing.  This matches
    the trajectories module's own contract: the endpoint mirrors the
    library's tolerance so a renderer that asks about a not-yet-validated
    instrument receives a typed answer ("we have no RCI threshold")
    rather than an HTTP error.

    ``baseline`` is optional; ``None`` produces ``insufficient_data``
    with the threshold still echoed so the UI can show 'no comparison
    available — collect a second reading'.
    """

    instrument: str
    current: float
    baseline: float | None = None


class TrajectoryResponse(BaseModel):
    """Typed trajectory point.

    All fields except ``direction`` are echoed verbatim from the input
    or computed deterministically:
    - ``delta`` is ``current - baseline`` when both are present, else
      ``None``.  Sign convention matches the underlying scale (e.g.
      negative on PHQ-9 means symptoms decreased).
    - ``rci_threshold`` is the per-instrument |Δ| that counts as
      reliable change; pinned in
      ``Docs/Whitepapers/02_Clinical_Evidence_Base.md``.
    - ``direction`` is the clinical interpretation: lower-is-better
      instruments invert the sign so improvement is always positive
      semantically, regardless of the underlying scale.
    """

    instrument: str
    current: float
    baseline: float | None
    delta: float | None
    rci_threshold: float | None
    direction: TrajectoryDirection


@router.post(
    "/trajectory",
    response_model=TrajectoryResponse,
    status_code=200,
    tags=["psychometric"],
)
async def compute_trajectory(payload: TrajectoryRequest) -> TrajectoryResponse:
    """Compute the reliable-change-index trajectory for one instrument.

    Pure computation — no idempotency key required, no DB writes.
    The endpoint is safe to call repeatedly; identical inputs always
    yield identical outputs.

    Direction interpretation by instrument:
    - PHQ-9 / GAD-7 / PSS-10 / AUDIT-C / DAST-10: lower is better;
      ``delta < 0`` with |delta| ≥ threshold → improvement.
    - WHO-5: higher is better; ``delta > 0`` with |delta| ≥ threshold
      → improvement.

    Unknown instruments and missing baselines both produce
    ``direction='insufficient_data'`` with HTTP 200 — this is a
    successful query, just one with no comparable trajectory.
    """
    # Normalize instrument to lowercase so callers don't need to know
    # the canonical casing.  The thresholds dict keys are lowercase by
    # convention.
    instrument = payload.instrument.strip().lower()
    point = compute_point(
        instrument=instrument,
        current=payload.current,
        baseline=payload.baseline,
    )
    return TrajectoryResponse(
        instrument=instrument,
        current=point.current,
        baseline=point.baseline,
        delta=point.delta,
        rci_threshold=point.rci_threshold,
        direction=point.direction,
    )


@router.get("/trajectory/thresholds", tags=["psychometric"])
async def trajectory_thresholds() -> dict[str, float]:
    """Return the per-instrument RCI threshold table.

    Useful for UI surfaces that want to render '|Δ| ≥ N counts as
    reliable change' tooltips alongside the trajectory chart, without
    hard-coding the table on the client side.  The values come from
    the same source-of-truth dict as the trajectory computation —
    one source, no drift."""
    return dict(RCI_THRESHOLDS)


class AssessmentHistoryItem(BaseModel):
    """Summary row for a single historical assessment.

    Deliberately omits ``raw_items`` — the user's literal answers on a
    validated clinical instrument are PHI that the history timeline
    does not need.  A clinician viewing a single Observation (Sprint 24
    GET ``/reports/fhir/observations/{id}``) reads the raw items
    through that PHI-boundary-gated endpoint instead; the history
    surface is the patient's own timeline view.

    Field shape matches :class:`AssessmentResult` for the fields that
    overlap, so a client rendering either response uses the same
    projection layer.
    """

    assessment_id: str
    instrument: str
    total: int
    severity: str
    requires_t3: bool
    created_at: str  # ISO-8601 UTC — consumed by chart-plot code as-is
    t3_reason: str | None = None
    index: int | None = None
    cutoff_used: int | None = None
    positive_screen: bool | None = None
    triggering_items: list[int] | None = None
    subscales: dict[str, int] | None = None
    instrument_version: str | None = None


class AssessmentHistoryResponse(BaseModel):
    """Envelope for the history endpoint.

    ``items`` is newest-first, capped at ``limit``.  ``limit`` is
    echoed so a client rendering pagination can display "showing 50 of
    N" without a second call; ``total`` is the absolute count for
    this user (not the returned page size) so the UI can decide
    whether to surface a "load older" control.
    """

    items: list[AssessmentHistoryItem]
    limit: int
    total: int


@router.get(
    "/history",
    response_model=AssessmentHistoryResponse,
    tags=["psychometric"],
)
async def history(
    x_user_id: str = Header(..., alias="X-User-Id"),
    limit: int = 50,
) -> AssessmentHistoryResponse:
    """Return the authenticated user's assessment timeline.

    Authentication (temporary shape):
    - ``X-User-Id`` header carries the pseudonymous subject id.  In
      production this is derived from the Clerk session JWT inside an
      auth middleware and injected here; the header form is a
      scaffolding stub so the Sprint 23 endpoint is testable before
      the Clerk v6 integration lands.  Callers must NOT supply an
      ``X-User-Id`` from a client-controlled source in a production
      deploy — the server-side middleware overwrite is what makes the
      identity trustable.
    - A missing or empty ``X-User-Id`` yields a 401.  ``limit`` must
      be a positive integer; 0 and negatives are 400.

    Response projection:
    - Items are newest-first by ``created_at``.
    - ``raw_items`` is deliberately omitted (see
      :class:`AssessmentHistoryItem`).  Clinician-portal views that
      need raw items go through Sprint 24's FHIR Observation GET.

    This endpoint does NOT touch the idempotency cache — GET is
    idempotent by HTTP semantics so there's nothing to deduplicate.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "auth.missing_user_id",
                "message": "X-User-Id header required.",
            },
        )
    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "validation.limit",
                "message": f"limit must be positive, got {limit}",
            },
        )

    repo = get_assessment_repository()
    records = repo.history_for(x_user_id, limit=limit)
    total = repo.count_for(x_user_id)

    items = [
        AssessmentHistoryItem(
            assessment_id=r.assessment_id,
            instrument=r.instrument,
            total=r.total,
            severity=r.severity,
            requires_t3=r.requires_t3,
            created_at=r.created_at.isoformat(),
            t3_reason=r.t3_reason,
            index=r.index,
            cutoff_used=r.cutoff_used,
            positive_screen=r.positive_screen,
            triggering_items=(
                list(r.triggering_items)
                if r.triggering_items is not None
                else None
            ),
            subscales=(
                dict(r.subscales) if r.subscales is not None else None
            ),
            instrument_version=r.instrument_version,
        )
        for r in records
    ]
    return AssessmentHistoryResponse(items=items, limit=limit, total=total)


# =============================================================================
# Trajectory from history — reads the repository, builds an RCI-annotated series
# =============================================================================


class TrajectoryHistoryBaseline(BaseModel):
    """The earliest recorded reading for this instrument — the baseline
    against which every later reading is compared.

    Surfaced as a distinct shape (rather than the first entry in
    ``points``) so the chart renderer can visually distinguish the
    baseline (flat horizontal reference line) from subsequent readings
    (trajectory points).  A ``null`` baseline means the user has no
    records for this instrument yet — the client renders a 'collect a
    first reading' prompt, not an error state.
    """

    assessment_id: str
    score: float
    created_at: str


class TrajectoryHistoryPoint(BaseModel):
    """One reading strictly after the baseline, annotated with its
    reliable-change interpretation.

    ``delta`` is ``None`` when the instrument has no validated RCI
    threshold (C-SSRS, DAST-10, unknown instruments) — matching the
    :mod:`discipline.psychometric.trajectories` contract that a missing
    threshold suppresses the arithmetic delta as well.  A future UI
    sprint that wants raw deltas for non-RCI instruments can add them
    as a separate field without breaking this contract.
    """

    assessment_id: str
    score: float
    created_at: str
    delta: float | None
    direction: TrajectoryDirection


class TrajectoryHistoryResponse(BaseModel):
    """Time series for one instrument across the user's timeline.

    ``rci_threshold`` is the per-instrument |Δ| that counts as reliable
    change.  ``null`` for instruments without a validated threshold
    (C-SSRS, DAST-10) — in which case every point's ``direction`` is
    ``insufficient_data``.  The series is still returned with real
    scores and timestamps so a non-annotated chart can still render.

    Zero-record and one-record cases intentionally return HTTP 200
    rather than 404: 'this user has no readings yet' is a successful
    state the UI needs to render, not a not-found error.
    """

    instrument: str
    rci_threshold: float | None
    baseline: TrajectoryHistoryBaseline | None
    points: list[TrajectoryHistoryPoint]


_WHO5_INSTRUMENT = "who5"


def _rci_score_for(record: AssessmentRecord) -> float:
    """Pick the value that aligns with the RCI threshold scale.

    The published WHO-5 reliable-change threshold (17 points) is on the
    *index* scale (0-100), not the raw total (0-25).  Every other
    instrument is scored on the same scale as its RCI threshold (PHQ-9
    total matches the 5.2 threshold, etc.).  Rendering a WHO-5
    trajectory against raw totals would silently compress deltas by 4×
    and misclassify every clinically meaningful change as
    ``no_reliable_change``.
    """
    if record.instrument == _WHO5_INSTRUMENT and record.index is not None:
        return float(record.index)
    return float(record.total)


@router.get(
    "/trajectory/{instrument}",
    response_model=TrajectoryHistoryResponse,
    status_code=200,
    tags=["psychometric"],
)
async def trajectory_from_history(
    instrument: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
) -> TrajectoryHistoryResponse:
    """Build the user's RCI-annotated trajectory for one instrument.

    Reads the authenticated user's records via the in-memory assessment
    repository, filters to this instrument, sorts oldest-first, treats
    the earliest record as the baseline per Jacobson & Truax 1991, and
    computes a reliable-change annotation for every subsequent record.

    Baseline shape (clinical contract):
    - Zero records for this instrument → ``baseline=None``, empty
      ``points``.
    - One record → baseline populated, empty ``points``.  RCI needs
      two readings by definition.
    - Two or more records → baseline + one point per subsequent record.

    Instruments without a validated RCI threshold (C-SSRS, DAST-10,
    unknown strings) return ``rci_threshold=None`` and every point's
    ``direction`` is ``insufficient_data``.  This mirrors
    :func:`discipline.psychometric.trajectories.compute_point` so the
    GET endpoint is a drop-in for the POST /trajectory path when both
    baseline and current scores are known.

    Authentication mirrors ``/history`` — missing or empty
    ``X-User-Id`` is 401.  The path parameter is stripped + lowercased
    so callers don't need to know the canonical casing.

    Route registration: this route is declared AFTER
    ``GET /trajectory/thresholds`` so the static-literal route wins —
    a request to ``/trajectory/thresholds`` returns the threshold table,
    not a trajectory for a user named 'thresholds'.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "auth.missing_user_id",
                "message": "X-User-Id header required.",
            },
        )

    instrument = instrument.strip().lower()
    repo = get_assessment_repository()
    # History is normally paginated at 50, but trajectory is an analytics
    # view across the full timeline.  10 000 covers ~200 years of weekly
    # check-ins per instrument — safely past any real retention window.
    all_records = repo.history_for(x_user_id, limit=10000)
    for_instrument = [r for r in all_records if r.instrument == instrument]
    # Repository returns newest-first; trajectories need oldest-first so
    # the earliest reading is the baseline.
    for_instrument.sort(key=lambda r: r.created_at)

    threshold = RCI_THRESHOLDS.get(instrument)

    if not for_instrument:
        return TrajectoryHistoryResponse(
            instrument=instrument,
            rci_threshold=threshold,
            baseline=None,
            points=[],
        )

    baseline_record = for_instrument[0]
    baseline_score = _rci_score_for(baseline_record)
    baseline = TrajectoryHistoryBaseline(
        assessment_id=baseline_record.assessment_id,
        score=baseline_score,
        created_at=baseline_record.created_at.isoformat(),
    )

    points: list[TrajectoryHistoryPoint] = []
    for record in for_instrument[1:]:
        score = _rci_score_for(record)
        point = compute_point(
            instrument=instrument,
            current=score,
            baseline=baseline_score,
        )
        points.append(
            TrajectoryHistoryPoint(
                assessment_id=record.assessment_id,
                score=score,
                created_at=record.created_at.isoformat(),
                delta=point.delta,
                direction=point.direction,
            )
        )

    return TrajectoryHistoryResponse(
        instrument=instrument,
        rci_threshold=threshold,
        baseline=baseline,
        points=points,
    )
