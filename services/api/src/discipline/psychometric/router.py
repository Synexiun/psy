"""Psychometric HTTP surface — PHQ-9, GAD-7, WHO-5, AUDIT, AUDIT-C,
C-SSRS, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI, PCL-5, OCI-R, PHQ-15,
PACS, BIS-11, Craving VAS, Readiness Ruler, DTCQ-8, URICA, PHQ-2,
GAD-2, OASIS, K10, SDS, K6, DUDIT, ASRS-6, AAQ-II, WSAS, DERS-16,
CD-RISC-10, PSWQ, LOT-R, TAS-20, ERQ, SCS-SF, RRS-10, MAAS, SHAPS,
ACEs, PGSI, BRS, SCOFF, PANAS-10, RSES, FFMQ-15, STAI-6, FNE-B,
UCLA-3, CIUS,
SWLS.

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
  DTCQ-8, URICA, PHQ-2, GAD-2, OASIS, K10, SDS, K6, DUDIT, ASRS-6, AAQ-II, WSAS, DERS-16, CD-RISC-10, PSWQ, LOT-R, TAS-20, ERQ, SCS-SF, RRS-10, MAAS, SHAPS, ACEs, PGSI, BRS, SCOFF, PANAS-10, RSES, FFMQ-15, STAI-6, FNE-B, UCLA-3, CIUS, SWLS have no safety items —
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
- ERQ (Gross & John 2003): 10 items, 1-7 Likert.  Measures
  **emotion-regulation strategy choice** — cognitive reappraisal
  (antecedent-focused, applied early in the emotion-generative
  cycle) vs expressive suppression (response-focused, applied
  after the emotion is active).  Two-subscale structure per
  Gross & John 2003 Study 1 CFA: reappraisal (6 items: 1, 3, 5,
  7, 8, 10) and suppression (4 items: 2, 4, 6, 9) — surfaced via
  the ``subscales`` map with keys ``reappraisal`` / ``suppression``
  (uniform with DERS-16 / TAS-20 subscale dispatch shape).  **No
  reverse-keyed items** — all 10 items are endorsement-direction
  for their subscale, so subscale sums operate on raw values
  directly (distinguishing ERQ from TAS-20 / LOT-R / PSWQ which
  require arithmetic-reflection flips).  **Novel Likert envelope**
  — 1-7 points (vs 1-5 for TAS-20 / DERS-16 / PSWQ, 0-3 for PHQ-9
  / GAD-7, 0-5 for WHO-5, 0-4 for LOT-R).  **Continuous-sentinel
  band** — Gross & John 2003 published no severity cutoffs; ERQ
  is a dispositional continuous measure, interpreted by the
  subscale PROFILE (the ``reappraisal, suppression`` 2-tuple) not
  by an aggregate classification.  Router emits the continuous-
  sentinel ``severity="continuous"`` literal (uniform with DERS-16 /
  BRS / PSWQ / SDS / K6 / CD-RISC-10 / LOT-R / PACS / BIS-11).
  Clinical framing: the **strategy-choice layer** completing the
  three-layer emotion-processing architecture (TAS-20 upstream =
  can the patient IDENTIFY the emotion; ERQ midstream = WHICH
  strategy does the patient REACH FOR; DERS-16 downstream = can
  the patient EXECUTE the chosen regulation).  The intervention-
  selection layer reads all three to route process-level work:
  high TAS-20 DIF → affect-labeling first; TAS-20 OK + ERQ
  suppression-dominant → cognitive-reappraisal training before
  skill-building; TAS-20 OK + ERQ reappraisal already high +
  DERS-16 high → distress-tolerance capacity work.  Clinical
  asymmetry (Aldao 2010 meta-analysis of 114 studies): higher
  reappraisal predicts BETTER outcomes, higher suppression
  predicts WORSE outcomes — but the router emits both subscale
  sums without imposing a directional frame, because the
  clinically relevant signal is the PROFILE (both values), not
  a pooled "good vs bad regulation" score.  Pairs with PHQ-9 /
  GAD-7 (suppression-elevated patients respond slower to standard
  CBT), AAQ-II (suppression correlates with but is not identical
  to experiential avoidance), and relapse-prevention signals
  (Bonn-Miller 2011 — suppression predicts substance-use relapse
  more strongly than reappraisal protects).  ``cutoff_used`` /
  ``positive_screen`` NOT set — ERQ has no binary cutoff.  No T3
  — the 10 items probe self-rated strategy use; none probe
  suicidality.  See ``scoring/erq.py``.
- SCS-SF (Raes 2011): 12 items, 1-5 Likert.  Measures **self-
  compassion** — the 3-component construct pair (self-kindness
  vs self-judgment, common humanity vs isolation, mindfulness
  vs over-identification) that is the empirically documented
  antagonist of shame.  Clinically load-bearing for the
  platform: shame-avoidance drives the abstinence-violation
  effect (Marlatt 1985) — relapse → shame → disengagement →
  next relapse — and low SCS-SF is the measurement signal
  identifying patients at relapse-risk-via-shame.  The product
  CLAUDE.md enshrines "compassion-first relapse copy" as a
  non-negotiable rule; SCS-SF is the measurement lever the
  intervention-selection layer reads to route low-compassion
  patients to Compassion Focused Therapy (CFT; Gilbert 2014)
  tool variants BEFORE the next urge episode.  Six subscales per
  Raes 2011 factor structure — Self-Kindness (items 2, 6),
  Self-Judgment (11, 12), Common Humanity (5, 10), Isolation
  (4, 8), Mindfulness (3, 7), Over-Identification (1, 9).
  **Novel 6-subscale wire** — largest subscale count in the
  package (DERS-16 had 5, URICA had 4, TAS-20 had 3, ERQ /
  LOT-R had 2).  Surfaced via the ``subscales`` map with keys
  ``self_kindness`` / ``self_judgment`` / ``common_humanity`` /
  ``isolation`` / ``mindfulness`` / ``over_identification``.
  **Novel scoring asymmetry** — the TOTAL is computed POST-flip
  (6 reverse items arithmetically reflected → aggregate reads
  in the self-compassion direction, range 12-60), while
  SUBSCALES are computed on RAW values (native construct
  direction — ``subscale_self_judgment`` reads as "how much
  self-judgment does the patient endorse", NOT the post-flip
  inversion).  This asymmetry is DELIBERATE per Raes 2011 /
  Neff 2016 scoring methodology; it preserves the positive/
  negative construct dyad structure so a clinician reading the
  subscale card sees the native dyad imbalance (e.g. "high SK
  and high SJ" = CFT-target dyad) rather than the aggregate-
  direction collapse.  Subscales are 2-10 (2 items × 1-5
  Likert).  **Built-in acquiescence catch**: all-1s and all-5s
  both yield total=36 (midpoint) because the balanced positive
  and negative items cancel — a feature of Neff 2003 / Raes
  2011 instrument design, not a bug.  The clinician-UI layer
  flags this pattern for bias review.  Higher-is-better
  direction (more self-compassion = higher total); uniform
  with WHO-5 / CD-RISC-10 / LOT-R / DTCQ-8 / BRS.  **Continuous-
  sentinel severity** — Raes 2011 published no validated bands;
  hand-rolling a cutoff from the descriptive "< 30 low, > 45
  high" literature ranges would violate CLAUDE.md's "Don't
  hand-roll severity thresholds" rule.  Router emits
  ``severity="continuous"``.  ``cutoff_used`` /
  ``positive_screen`` NOT set.  No T3 — the 12 items probe
  dispositional self-related responding; none probe suicidality.
  See ``scoring/scssf.py``.
- RRS-10 (Treynor 2003): 10 items, 1-4 Likert.  Measures
  **rumination** — the attentional/cognitive loop that sustains
  affect past its natural decay.  The psychometrically-clean
  10-item subset of Nolen-Hoeksema's RRS-22 with the depressive-
  symptom-confounded items removed; Treynor 2003 PCA extracted
  two factors: **Brooding** (maladaptive — passive evaluative
  comparison; items 1, 3, 6, 7, 8) and **Reflection** (adaptive —
  active analytic problem-solving; items 2, 4, 5, 9, 10).  This
  two-factor split is the clinical point of RRS-10 over RRS-22 —
  treatment routing depends on WHICH kind of rumination dominates,
  not total rumination.  Clinically load-bearing for the
  60-180 s urge-intervention window the platform targets:
  brooding is the attentional engine that keeps a craving alive
  past its natural decay, and Caselli 2010 demonstrated it
  prospectively predicts time-to-relapse in alcohol-use-disorder
  samples independent of concurrent depression.  Reflection does
  not carry the same prospective risk.  Surfaced via the
  ``subscales`` map with keys ``brooding`` / ``reflection``;
  each subscale sums to 5-20.  Total 10-40.  No reverse items
  (Treynor 2003 wording is direction-aligned, same as ERQ).
  **Continuous-sentinel severity** — Treynor 2003 published no
  validated bands; hand-rolling thresholds would violate
  CLAUDE.md's "Don't hand-roll severity thresholds" rule.  The
  clinical read is the (brooding, reflection) 2-tuple, not a
  categorical classification; router emits
  ``severity="continuous"``.  ``cutoff_used`` /
  ``positive_screen`` NOT set.  No T3 — the 10 items probe
  attentional style during low mood; none probe suicidality.
  Note that the parent RRS-22 contains suicidality-adjacent
  content, but the Treynor 2003 10-item subset does not — this
  is one of the reasons the 10-item version was extracted.
  See ``scoring/rrs10.py``.
- MAAS (Brown & Ryan 2003): 15 items, 1-6 Likert.  Measures
  **trait mindful attention** — the dispositional frequency of
  present-moment awareness versus automatic-pilot cognitive
  absorption.  The most widely validated single-facet measure of
  mindfulness; Brown & Ryan 2003 deliberately restricted the
  construct to the attentional / awareness component (no
  acceptance / non-judgment / compassion overlays) for
  psychometric cleanness.  Single-factor unidimensional — Brown
  & Ryan 2003 EFA, Carlson & Brown 2005 CFA, MacKillop & Anderson
  2007 IRT all confirm.  Novel envelope shape on the platform:
  **continuous + NO subscales** at 15 items (prior unidimensional-
  continuous instruments shipped with ≤ 16 items include PSWQ 16,
  CD-RISC-10, K6 6, BRS 6, DTCQ-8 — MAAS joins this group).
  Clinically load-bearing: mindful attention is the exact
  capacity that every in-app grounding / urge-surfing / 3-minute-
  breathing-space tool is training.  Baseline MAAS stratifies
  users into mindfulness-first vs cognitive-first intervention
  sequences; repeat MAAS is the outcome measure for whether the
  mindfulness-based tool variants are producing dispositional
  change (Bowen 2014 MBRP RCT used MAAS as its primary trait-
  mindfulness outcome).  The 15 items are all worded in the
  MINDLESSNESS direction (e.g. "I find myself doing things
  without paying attention") and the Likert anchors run 1 =
  almost always [mindless] to 6 = almost never [mindless] — so
  the native total is already higher = more mindful, requiring
  NO flip arithmetic at the scorer layer.  Total 15-90.  Brown
  & Ryan 2003 report the MEAN (1.0-6.0); the platform stores
  the SUM for integer auditability, and renderers divide by
  15 to recover the published-literature comparison metric.
  **Continuous-sentinel severity** — Brown & Ryan 2003
  published no validated bands.  Descriptive ranges exist in
  the literature (Carmody 2008 MBSR pre ≈ 3.8, post ≈ 4.3 on
  the mean metric) but are sample-dependent, not cutoffs.
  Hand-rolling thresholds would violate CLAUDE.md's "Don't
  hand-roll severity thresholds" rule.  Router emits
  ``severity="continuous"`` (uniform with DERS-16 / ERQ / BRS /
  PSWQ / SDS / K6 / SCS-SF / RRS-10 / CD-RISC-10 / LOT-R).
  ``cutoff_used`` / ``positive_screen`` / ``subscales`` NOT set.
  Higher-is-better direction (uniform with WHO-5 / CD-RISC-10 /
  LOT-R / DTCQ-8 / BRS / SCS-SF total).  No T3 — the 15 items
  probe attentional default patterns; none probe suicidality.
  See ``scoring/maas.py``.
- SHAPS (Snaith 1995): 14 items, 1-4 Likert (Strongly Disagree
  to Strongly Agree).  Measures **anhedonia** — the capacity
  to experience pleasure from normally-rewarding activities.
  Unidimensional per Franken 2007 PCA / Leventhal 2006 CFA /
  Nakonezny 2010 IRT.  The platform's primary hedonic-reactivity
  signal — anhedonia is a prospective SUD-relapse predictor
  independent of depressed mood (Garfield 2014 systematic
  review; Koob 2008 opponent-process / stress-surfeit theory)
  and the indication for behavioral-activation-augmented
  intervention (Daughters 2008 LETS ACT; Magidson 2011) rather
  than MBRP / CBT alone.  **Novel wire shape on this platform**:
  first scorer whose stored ``total`` is NOT a linear function
  of the raw per-item input.  Snaith 1995 dichotomizes raw 1-4
  BEFORE summation — raw 1/2 → 0 (hedonic response), raw 3/4 →
  1 (anhedonic response); ``total`` is a count of anhedonic
  items, 0-14.  The raw 1-4 input is preserved verbatim in the
  scorer's ``items`` tuple so FHIR export and Franken 2007
  continuous-alternative consumers can recover the original
  response without re-acquiring data.  **Cutoff envelope** —
  ``total >= 3`` per Snaith 1995 §Results (sensitivity 0.77 /
  specificity 0.82 against MINI depression per Franken 2007).
  Wire shape matches OCI-R / MDQ / PC-PTSD-5 / AUDIT-C:
  severity carries the positive/negative_screen string,
  positive_screen field carries the bool, cutoff_used field
  carries the integer 3.  Higher-is-worse direction (same as
  PHQ-9 / GAD-7 / PSS-10 / K6).  No T3 — the 14 items probe
  hedonic capacity; phenomenological closeness to severe-
  depression suicidality (Fawcett 1990) is handled at the
  PROFILE level (SHAPS + PHQ-9 + C-SSRS), not via per-item
  SHAPS content triggering T3.  See ``scoring/shaps.py``.
- ACEs (Felitti 1998): 10 items, BINARY (0 = No / 1 = Yes).
  The **etiological-stratification** instrument.  Measures
  **cumulative adversity exposure before age 18** across 10
  categories (emotional / physical / sexual abuse, emotional /
  physical neglect, witnessing maternal violence, household
  substance abuse, household mental illness, parental
  separation, incarcerated household member).  Total is a
  straight sum, 0-10.  Felitti 1998 §Results established the
  dose-response relationship between ACE count and essentially
  every major adult health outcome — ACE >= 4 = 4.7× alcoholism
  risk, 10.3× injection drug use risk, 2.5× adult suicide-
  attempt risk vs ACE = 0.  Hughes 2017 international meta-
  analysis (n = 253,719, 37 studies) replicated: ACE >= 4 =
  7.4× problem drinking / 10.2× problem drug use.  The platform
  uses ACE score at enrollment to stratify treatment sequencing:
  ACE >= 4 routes to **trauma-informed-care (TIC) sequencing**
  BEFORE standard CBT-based relapse-prevention (van der Kolk
  2014; Briere 2012; Herman 1992 three-stage model).  **Novel
  wire shape on this platform — TWO firsts**: (1) first BINARY-
  item instrument (every prior scorer accepts a Likert range:
  0-3 PHQ-9, 0-4 OCI-R, 1-4 SHAPS, 1-6 MAAS, 1-7 ERQ); the
  validator rejects integers that are "in range" (2-10) but not
  strictly 0/1.  (2) first RETROSPECTIVE instrument (every
  prior scorer measures current state); ACEs measures lifetime
  exposure before age 18 — a one-time-enrollment measurement
  rather than a trajectory-tracking repeated measure (Felitti
  1998 1.5-year test-retest r = 0.66 — re-administration is not
  clinically meaningful).  Upstream trajectory logic handles the
  one-time-only semantics; the scorer itself is stateless.
  **Cutoff envelope** — ``total >= 4`` per Felitti 1998.  Wire
  shape matches SHAPS / OCI-R / MDQ / PC-PTSD-5 / AUDIT-C:
  severity carries the positive/negative_screen string,
  positive_screen field carries the bool, cutoff_used field
  carries ``ACES_POSITIVE_CUTOFF = 4``.  **No subscales** —
  Dong 2004 factor-analyzed the 10 items and confirmed single-
  factor structure at the total-score level, rejecting three-
  subscale (abuse / neglect / household-dysfunction) models as
  producing unstable per-domain cutoffs.  Surfacing a subscales
  map on the wire would create the false impression of
  validated per-domain cutoffs where only the total-score
  cutoff is validated.  Higher-is-worse direction (same as
  PHQ-9 / GAD-7 / SHAPS / PSS-10 / K6 — the trajectory RCI
  direction logic must register ACEs alongside these, NOT
  with WHO-5 / MAAS / CD-RISC-10).  No T3 — ACEs probes
  retrospective childhood exposure, not current ideation.  A
  patient with ACE = 10 carries elevated dispositional risk
  across the lifespan but that is not time-limited current-
  state crisis; acute-ideation screening stays on C-SSRS /
  PHQ-9 item 9.  **Content-sensitivity**: items 1-3 (abuse)
  and item 6 (maternal violence) require administration-UI
  content warning, opt-out, and post-administration resources
  — a UI-layer concern, NOT a scorer-layer concern.  See
  ``scoring/aces.py``.
- PGSI (Ferris & Wynne 2001): 9 items, 0-3 Likert.  The platform's
  FIRST BEHAVIORAL-ADDICTION instrument — every prior scorer
  targets substance use (AUDIT / DAST-10 / DUDIT / SDS / PACS /
  DTCQ-8 / URICA / Craving VAS) or an internalizing / regulatory
  dimension (PHQ-9 / GAD-7 / PSS-10 / OCI-R / PCL-5 / SHAPS /
  MAAS / DERS-16 / ACEs).  PGSI expands the scope to
  **compulsive-behavior cycles that are not substance-mediated**
  — the exact 60-180 s urge-to-action window the product
  intervenes on, applied to a non-substance reinforcer.
  Clinically load-bearing: gambling co-occurs with SUD at 10-20%
  population (Lorains 2011 meta-analysis) and 35-60% clinical
  (Petry 2005 NESARC).  Gambling disorder was reclassified from
  DSM-IV "Impulse Control Disorders NEC" to DSM-5 "Substance-
  Related and Addictive Disorders" (APA 2013; Petry 2013) because
  the behavioral-addiction mechanics (intermittent variable-ratio
  reinforcement; ventral-striatum reward-cue sensitization Potenza
  2003 fMRI; tolerance; chasing-losses analogue to Marlatt 1985
  abstinence-violation effect) are indistinguishable from SUD
  mechanics.  Total = sum of 9 items, 0-27.  **Four-band
  severity** per Ferris & Wynne 2001 §5 Table 5.1: 0
  ``non_problem``, 1-2 ``low_risk``, 3-7 ``moderate_risk``,
  8-27 ``problem_gambler``.  Operating point at >= 8 has kappa
  = 0.83 against DSM-IV pathological-gambling diagnosis (Ferris
  2001 n = 3,120 Canadian community sample; Currie 2013
  confirmed at n = 12,229 across 4 Canadian population surveys;
  Williams & Volberg 2014 recommended no revision).  Wire
  envelope matches AUDIT / PHQ-9 / GAD-7 / PSS-10 / ISI banded-
  severity shape — severity carries the band label;
  ``cutoff_used`` / ``positive_screen`` / ``subscales`` NOT set.
  Ferris 2001 retained unidimensional structure by design (9
  items extracted from a 31-item pool via factor analysis
  precisely to preserve single-factor severity).  Higher-is-
  worse direction (uniform with PHQ-9 / GAD-7 / SHAPS / ACEs).
  No T3 — items 5 ("might have a problem") and 9 ("felt guilty")
  are problem-awareness / affect items, NOT suicide-ideation /
  self-harm items; the well-established problem-gambler suicide-
  risk elevation (Moghaddam 2015: 3.4x attempt risk) is handled
  at the PROFILE level (PGSI + PHQ-9 + C-SSRS), not via per-
  PGSI-item T3 triggering.  See ``scoring/pgsi.py``.
- BRS (Smith 2008): 6 items, 1-5 Likert.  Measures **ecological /
  outcome resilience** — the capacity to BOUNCE BACK from stress
  — and is deliberately shipped ALONGSIDE CD-RISC-10 which measures
  **agentic resilience** (the resources that produce recovery).
  Smith 2008 §3 framed the distinction as resource-vs-outcome:
  CD-RISC ≈ "I have the resources to weather adversity"; BRS ≈
  "I do, in fact, bounce back from adversity".  The clinical
  value of shipping both is the DISCREPANCY profile — high
  CD-RISC + low BRS = resilience-supporting resources present
  but not deployed (Beck 1967 cognitive-triad interference with
  resource deployment); intervention framing shifts to behavioral
  activation (Martell 2010) or values-based committed action (ACT
  per Hayes 2012), not resource-building.  Three items are
  positively worded (1, 3, 5: "I tend to bounce back...") and
  three are negatively worded (2, 4, 6: "It is hard for me to
  snap back..." — reverse-scored at the scorer; ``6 - raw``
  idiom shared with TAS-20 / PSWQ / LOT-R).  The three-positive /
  three-negative symmetry is the Smith 2008 acquiescence-bias
  control design — by construction both uniform-response
  extremes (all-1s and all-5s) produce post-flip sum 18, which
  lands at the LOW-NORMAL boundary and ensures response-set bias
  cannot push a patient into either extreme band.  Total = sum
  of 6 POST-FLIP items, 6-30.  HIGHER = MORE RESILIENT (opposite
  of PHQ-9 / GAD-7 / AUDIT / PGSI; uniform with WHO-5 / MAAS /
  CD-RISC-10 higher-is-better convention).  **Three-band
  resilience** per Smith 2008 §3.3 conceptual-mean framework,
  mapped to integer sum: 6-17 ``low``, 18-25 ``normal``, 26-30
  ``high`` (original mean-based bands: 1.00-2.99 / 3.00-4.30 /
  4.31-5.00 — the integer-sum envelope preserves the clinical
  band assignment exactly).  Wire envelope matches
  PHQ-9 / GAD-7 / AUDIT / PSS-10 / ISI / PGSI banded-severity
  shape — severity carries the band label; ``cutoff_used`` /
  ``positive_screen`` / ``subscales`` NOT set.  Smith 2008 §3.2
  EFA: single factor by construction (eigenvalue 2.68, second
  0.64) — surfacing positive-item / negative-item sums as
  "subscales" would contradict the factor derivation and
  double-count response-set bias.  No T3 — no item probes
  suicidality, self-harm, or acute-risk behavior; BRS measures
  resilience outcomes only.  Acute-risk screening stays on
  C-SSRS / PHQ-9 item 9.  The ``items`` field stores the RAW
  PRE-FLIP patient responses (audit-trail invariance, shared
  with TAS-20 / PSWQ / LOT-R).  Use-case: BRS is the platform's
  primary within-subject **recovery-trajectory** anchor (test-
  retest r = 0.69 at 3 months, Smith 2008 §3.2) — paired with
  Jacobson & Truax 1991 RCI for clinically-significant-change
  computation at the 3-month follow-up.  See ``scoring/brs.py``.
- SCOFF (Morgan, Reid & Lacey 1999 BMJ): 5 items, binary yes/no.
  Rapid primary-care screen for anorexia nervosa / bulimia
  nervosa.  Acronym is a mnemonic for the 5 question cues —
  **S**ick (self-induced vomiting), **C**ontrol (loss of
  control over eating), **O**ne (>= 1 stone / 6.35 kg loss in
  3 months), **F**at (perceive self as fat when others say
  thin), **F**ood (food dominates life).  Fills a clearly-
  missed clinical domain — every prior instrument covers
  substance use, internalizing / regulatory dimensions,
  trauma, a behavioral addiction (PGSI), or resilience (CD-
  RISC-10 / BRS).  Eating disorders co-occur with SUD at
  25-50% in clinical samples (Hudson 2007 NCS-R 23.7%
  lifetime; Krug 2008 European multi-site n = 879 at 45%
  lifetime SUD in AN/BN) and share substantial behavioral-
  addiction mechanics (restraint-binge cycle in BN parallels
  abstinence-violation effect; reward-prediction-error
  dysfunction in AN parallels SUD anhedonia profiles — Kaye
  2013).  Cutoff >= 2 positive items per Morgan 1999 §3
  Table 2 (sens 100% / spec 87.5% vs DSM-III-R AN/BN); Cotton
  2003 primary-care replication n = 233 (sens 100% / spec
  89.6%); Solmi 2015 meta-analysis 25 studies n = 26,488
  (pooled AUC 0.89).  Morgan 1999 specifically REJECTED the
  >= 1 threshold (spec 69% — unacceptable false-positive
  burden for primary care).  Wire envelope matches AUDIT-C /
  PC-PTSD-5 / SHAPS / ACEs binary-screen shape — total
  carries the positive-item count, severity carries
  "positive_screen" / "negative_screen", cutoff_used = 2.
  No subscales (5 clinical-consensus cues, not factor-
  partitioned).  No bands (SCOFF is a screen, not severity
  — a count of 5 is not "more severe" than 2 in a banded
  sense; both are above-threshold positive screens
  requiring specialist assessment).  No T3 — item 1 "make
  yourself Sick" explicitly means PURGING BEHAVIOR (self-
  induced vomiting per Morgan 1999 Background §1), NOT self-
  harm.  Acute-risk screening stays on C-SSRS / PHQ-9 item 9.
  Item 3 ("lost more than one stone in 3 months") is a
  medical-risk indicator but NOT an acute-safety indicator
  at the scorer level — severe positive SCOFF triggers the
  downstream ED-assessment pathway (EDE-Q 2.0 per Fairburn
  1994; EDE interview per Cooper & Fairburn 1987), not the
  T3 suicide-response protocol.  LOCALE-SENSITIVE item 3:
  Morgan 1999 uses imperial stones (UK publication); non-UK
  locales must present a validated-translation version with
  culturally-appropriate mass unit (6.35 kg for EU/SI
  locales, 14 lb for US locale — Kutz 2020 validated
  non-English adaptations and the kg substitution).  Scorer
  is locale-agnostic (only sees the yes/no response); the
  administration-UI must present the culturally-appropriate
  translation.  See ``scoring/scoff.py``.
- PANAS-10 (Thompson 2007 I-PANAS-SF): 10 items, 1-5 Likert.
  The International Positive and Negative Affect Schedule Short
  Form — cross-cultural derivation of the 20-item PANAS
  (Watson, Clark & Tellegen 1988).  Thompson 2007 JCCP 38(2):
  227-242 established configural + metric + scalar measurement
  invariance across 8 cultural groups (n = 1,789), making the
  I-PANAS-SF the PANAS variant of record for the Discipline OS
  four-locale launch.  Fills the **positive/negative affect
  dimension gap** — every prior instrument targets a specific
  syndrome or construct; none measure the orthogonal PA / NA
  affect dimensions that Watson & Clark's tripartite model
  (Clark & Watson 1991 JAP) identifies as the core discriminator
  between anxiety and depression.  PA deficit is depression-
  specific (anhedonia); NA elevation is the shared general-
  distress dimension.  Clinically load-bearing for: (1)
  intervention matching (low PA + high NA → behavioral
  activation per Martell 2010 / Dimidjian 2006; normal PA +
  high NA → unified protocol per Barlow 2011 or ACT per Hayes
  2012; low PA + normal NA → positive-affect treatment per
  Craske 2019); (2) differential diagnosis (PHQ-9+ without
  PANAS PA deficit suggests somatic-driven positivity rather
  than core anhedonic depression); (3) trajectory monitoring
  (Watson 1988 §3: PA is more state-sensitive than NA — PA
  responds to intervention faster, forming the earlier treatment-
  response marker).  **Novel wire envelope** — PANAS-10 is the
  platform's FIRST bidirectional-subscales instrument with no
  canonical aggregate total.  Watson 1988 and Tellegen 1999
  established PA and NA as ORTHOGONAL affect-circumplex
  dimensions; summing them is a category error.  The platform
  resolves this via: ``total`` = PA subscale sum (5-25, not a
  composite) chosen as the primary because PA is the more
  clinically discriminating dimension per tripartite-model
  priority (Clark & Watson 1991; Craske 2019); ``subscales``
  dict carries both ``"positive_affect"`` and ``"negative_affect"``
  sums (5-25 each).  CLINICIANS MUST READ BOTH SUBSCALES — the
  total alone is insufficient to distinguish depression-,
  anxiety-, anhedonia-, or flourishing-dominant profiles.
  ``severity`` = literal sentinel ``"continuous"`` — Thompson
  2007 did not publish banded severity cutpoints; Crawford &
  Henry 2004 UK norms (PA 32.1 ±6.8, NA 14.8 ±5.3 on 10-50
  scale; 16.05 ±3.4 and 7.40 ±2.65 on 5-25 scale equivalents)
  are descriptive distributions, not clinical bands.  Hand-
  rolling bands violates CLAUDE.md.  No reverse-keying (items
  within each subscale are valence-aligned per Watson 1988 §2).
  No T3 — item 1 "upset" is general NA, NOT suicidal ideation.
  Acute-risk screening stays on C-SSRS / PHQ-9 item 9.  See
  ``scoring/panas10.py``.
- RSES (Rosenberg 1965): 10 items, 0-3 Likert, 5 reverse-keyed
  (items 2, 5, 6, 8, 9).  Rosenberg Self-Esteem Scale — the
  most widely-used psychological instrument (>100k citations).
  Morris Rosenberg's *Society and the Adolescent Self-Image*
  (Princeton University Press 1965) established the
  unidimensional global self-esteem construct; Gray-Little 1997
  IRT meta-analysis confirmed unidimensional factor structure;
  Schmitt & Allik 2005 cross-national n = 16,998 confirmed
  factorial invariance across 53 nations (grand M = 21.3 SD =
  5.5 on 0-30 scale).  Fills the platform's **self-concept
  dimension gap** — every prior instrument targets a specific
  syndrome, a craving / impulse construct, an affect dimension,
  a regulatory construct, or a resilience / recovery construct.
  None measure GLOBAL SELF-ESTEEM, the evaluative attitude one
  holds toward oneself.  Self-concept is clinically load-
  bearing for relapse prevention specifically via the
  **abstinence-violation effect** (Marlatt 1985 Relapse
  Prevention pp. 37-44; Marlatt 2005 Relapse Prevention 2nd
  ed): a single lapse triggers an internal / stable / global
  attributional cascade with low self-esteem as both substrate
  and outcome — a self-reinforcing cycle that RSES measures.
  Intervention matching: low RSES routes to self-compassion-
  based work (Neff 2003; Gilbert 2010 CFT) or self-efficacy-
  strengthening (Bandura 1977; Witkiewitz 2007).  Reverse-
  keyed items (2, 5, 6, 8, 9) are the negatively-worded items
  ("At times I think I am no good at all", "I feel I do not
  have much to be proud of", "I certainly feel useless at
  times", "I wish I could have more respect for myself", "All
  in all, I am inclined to feel that I am a failure"); post-
  flip = (ITEM_MIN + ITEM_MAX) - raw = 3 - raw.  Inherits the
  PGSI / BRS / TAS-20 / PSWQ / LOT-R reverse-keying idiom.
  Total = sum of post-flip, 0-30.  HIGHER = more self-esteem
  (higher-is-better direction, uniform with WHO-5 / BRS /
  PANAS-10 total / LOT-R / MAAS / CD-RISC-10 / Ruler /
  DTCQ-8).  NO bands — Rosenberg 1965 did not publish clinical
  cutpoints; Gray-Little 1997 meta-analysis confirmed no
  banded thresholds; Schmitt & Allik 2005 cross-national means
  are descriptive, not clinical.  Hand-rolling bands violates
  CLAUDE.md.  severity = "continuous" sentinel; trajectory
  layer applies Jacobson-Truax RCI (Jacobson & Truax 1991) on
  total directly.  NO subscales — Gray-Little 1997 IRT
  confirmed unidimensional; Tomas 1999 / Marsh 1996 two-factor
  proposals are method-artifact (positive-negative wording
  bias), not substantive.  NO T3 — RSES measures self-esteem,
  not suicidality.  Item 9 "inclined to feel that I am a
  failure" is a SELF-CONCEPT item per Rosenberg 1965
  derivation, NOT ideation.  Item 6 "I certainly feel useless
  at times" is similarly a self-concept item.  Acute-risk
  screening stays on C-SSRS / PHQ-9 item 9.  ``items`` field
  preserves RAW pre-flip for audit invariance.  See
  ``scoring/rses.py``.
- FFMQ-15 (Baer 2006 / Gu 2016): 15 items, 1-5 Likert, 7
  reverse-keyed (positions 6, 7, 8, 9, 10, 11, 12).  Five-Facet
  Mindfulness Questionnaire short form — the Baer, Smith,
  Hopkins, Krietemeyer & Toney 2006 Assessment 13(1):27-45
  five-factor integration of prior mindfulness scales (MAAS,
  KIMS, FMI, CAMS-R, SMQ), with the 15-item short form derived
  by Gu, Strauss, Crane, Barnhofer, Karl, Cavanagh & Kuyken
  2016 Psychological Assessment 28(7):791-802 (n = 2,876 IRT
  analysis across 5 samples).  Five facets at 3 items each:
  **observing** (1-3), **describing** (4-6), **acting with
  awareness** (7-9), **non-judging of inner experience**
  (10-12), **non-reactivity to inner experience** (13-15).
  Extends platform's MAAS single-factor mindfulness measure
  with facet-level decomposition — the FIRST PENTA-SUBSCALE
  instrument on the platform.  Clinical load-bearing for
  intervention matching: each facet maps to a distinct
  intervention modality.  Low observing -> body-scan / sensory-
  grounding (Kabat-Zinn 1990).  Low describing -> emotion-
  labeling / affect-literacy (Kircanski 2012).  Low acting-
  with-awareness -> Mindfulness-Based Relapse Prevention urge-
  surfing (Bowen 2014) — the facet MOST DIRECTLY implicated in
  cue-reactivity and automatic-pilot relapse, making FFMQ-15
  Acting-with-Awareness a primary signal for the Discipline OS
  intervention engine.  Low non-judging -> self-compassion
  (Neff 2011; Gilbert 2010 CFT) — same lever as low RSES, the
  non-judging deficit is the Marlatt 1985 AVE-cascade
  precursor.  Low non-reactivity -> acceptance / defusion
  (Hayes 2012 ACT; Segal 2013 MBCT).  Reverse-keyed items
  reflect the Baer 2006 factor structure: describing has ONE
  reverse item at position 6 ("It's hard for me to find the
  words to describe what I'm thinking"); acting-with-awareness
  is ENTIRELY reverse-keyed (items phrased as automatic-pilot
  failures — "I rush through activities without being really
  attentive to them"); non-judging is ENTIRELY reverse-keyed
  (items phrased as judgmental thoughts — "I criticize myself
  for having irrational or inappropriate emotions"); observing
  and non-reactivity are entirely positively worded.  Post-flip
  = (1 + 5) - raw = 6 - raw.  Total = sum of all 15 post-flip
  items (15-75); subscales dict holds per-facet post-flip sums
  (each 3-15).  HIGHER = more mindfulness (higher-is-better
  direction, uniform with WHO-5 / BRS / PANAS-10 PA / LOT-R /
  MAAS / CD-RISC-10 / RSES).  NO bands — Baer 2006 and Gu 2016
  did not publish clinical cutpoints at either total or facet
  level; severity = "continuous" sentinel; trajectory layer
  applies Jacobson-Truax RCI per facet.  Hand-rolling facet
  bands violates CLAUDE.md.  Acquiescence-bias asymmetric:
  unlike RSES (symmetric 5+5 so all-0s = all-3s = 15), FFMQ-15
  has 8 positive + 7 reverse items so all-raw-1 yields total
  43 and all-raw-5 yields total 47 (separation of 4, bounding
  acquiescence bias < 6% of the 15-75 range).  NO T3 — no
  item probes suicidality; non-judging items mention "my
  emotions are bad" but are self-evaluative NOT ideation
  (content flows to RSES-linked AVE-substrate handling, not
  acute-risk).  ``items`` field preserves RAW pre-flip for
  audit invariance.  See ``scoring/ffmq15.py``.
- STAI-6 (Marteau & Bekker 1992): 6 items, 1-4 Likert, 3
  reverse-keyed (positions 1, 4, 5).  The brief 6-item
  derivation of the state-anxiety subscale of the full 20-
  item Spielberger State-Trait Anxiety Inventory (Spielberger
  1983 Form Y), developed by Marteau & Bekker (British
  Journal of Clinical Psychology 1992, 31:301-306; n = 200
  pre-surgical patients; r = 0.94 with full STAI-S).  Fills
  the platform's **state-vs-trait anxiety distinction gap** —
  existing anxiety coverage is trait-anchored (GAD-7's 14-
  day window, GAD-2 same, OASIS's 7-day window, AAQ-II and
  PSWQ dispositional).  STAI-6 measures **momentary state
  anxiety** anchored to the present ("how you feel right
  now, at this moment") per Spielberger's (1966, 1983)
  seminal state / trait distinction.  Clinical load-
  bearing: (1) pre/post intervention-session within-session
  effect measurement (the canonical efficacy metric GAD-7
  cannot resolve — its 14-day window averages across a
  single session); (2) trigger-vs-baseline cue reactivity
  detection (Craske 2014 exposure targets vs Dugas 2010
  trait-anxiety targets); (3) real-time relapse-risk gating
  per Marlatt 1985 pp. 137-142 (negative emotional states
  as the most common proximal relapse precipitant —
  elevated state anxiety in the hour before a craving
  episode is a bandit-policy predictive signal).  Items
  (Marteau 1992 Table 1): 1. calm (reverse), 2. tense,
  3. upset, 4. relaxed (reverse), 5. content (reverse),
  6. worried.  Post-flip = 5 - raw at reverse positions;
  total = sum of post-flip items, range 6-24.  HIGHER =
  more state-anxious (lower-is-better direction, uniform
  with PHQ-9 / GAD-7 / AUDIT / PSS-10 / PGSI / SHAPS).  NO
  scaled score (Marteau 1992 recommended (total × 20) / 6
  mapping to the full STAI-S 20-80 range; platform does not
  emit — non-integer for most inputs, adds no clinical info
  over raw total at the trajectory layer, and Kvaal 2005
  ≥ 40 scaled cutoff is secondary literature not pinnable
  per CLAUDE.md).  NO bands — severity = "continuous"
  sentinel; trajectory layer applies Jacobson-Truax RCI on
  the raw 6-24 total for clinical-significance.  NO T3 — no
  item probes suicidality; "upset" (item 3) is general
  distress, NOT ideation.  ``items`` field preserves RAW
  pre-flip for audit invariance.  See ``scoring/stai6.py``.
- FNE-B (Leary 1983): 12 items, 1-5 Likert, 4 reverse-keyed
  (positions 2, 4, 7, 10).  The original Brief Fear of Negative
  Evaluation scale — Leary (Personality and Social Psychology
  Bulletin 1983, 9(3):371-375) derived the 12-item abbreviation
  from Watson & Friend's (1969) original 30-item FNE with
  r = 0.96 on n = 164 undergraduates.  Fills the platform's
  **social-evaluative anxiety gap** — existing anxiety coverage
  targets generalized worry (GAD-7, PSWQ), state anxiety (STAI-6,
  OASIS), experiential avoidance (AAQ-II), but none measure the
  fear-of-judgement construct that drives social-situation
  avoidance, public-speaking paralysis, and social-anxiety-
  disorder phenomenology (Heimberg 1995, Hofmann 2008).
  Clinical load-bearing: (1) social-phobia case-identification
  and CBGT / CT treatment-targeting (Heimberg 1995 Cognitive-
  Behavioral Group Therapy for Social Phobia protocol uses
  FNE as a primary pre/post outcome); (2) addiction-relevant
  **socially-cued relapse detection** — Marlatt 1985 Table 4.1
  identifies social-pressure / interpersonal-conflict as a top
  proximal relapse determinant; FNE-B discriminates the
  "alcohol-as-social-lubrication" user profile from the
  "negative-affect-self-medication" profile (distinct
  intervention strategies: exposure + social-skills training
  vs affect-regulation + DBT distress-tolerance); (3)
  digital-avoidance substitution detection — high FNE-B
  + high CIUS / gaming disorder = social-anxiety-driven
  escape into online worlds rather than face-to-face
  engagement (Caplan 2003 compensatory-internet-use model).
  Items (Leary 1983 Table 1): 1. worry what people think,
  2. unconcerned opinions (reverse), 3. afraid other won't
  approve, 4. rarely worry seeming foolish (reverse), 5.
  afraid make unfavorable impression, 6. afraid others won't
  approve, 7. unconcerned if disapproved (reverse), 8.
  frequently afraid of mistakes, 9. others' opinions don't
  bother me, 10. not worried what say (reverse), 11. worry
  disapproval, 12. worry say wrong thing.  Post-flip =
  6 - raw at reverse positions; total = sum of post-flip
  items, range 12-60.  HIGHER = more fear of negative
  evaluation (lower-is-better direction, uniform with
  PHQ-9 / GAD-7 / PSS-10 / STAI-6).  NO bands — severity
  = "continuous" sentinel; no pinnable Leary 1983
  cutpoints (Collins 2005 n = 234 college sample mean
  35.7 SD 8.1 with ≥ 49 = "clinical range" is secondary-
  literature post-hoc and not pinnable per CLAUDE.md);
  trajectory layer applies Jacobson-Truax RCI on the
  raw 12-60 total for clinical-significance.  NO T3 —
  no item probes suicidality; "afraid of making mistakes"
  (item 8) is evaluative-apprehension, NOT ideation.
  Acquiescence-bias asymmetric: 8 straight + 4 reverse
  items give total = 4v + 24 for any all-v constant
  vector — all-raw-1 yields 28 and all-raw-5 yields 44
  (separation of 16, the largest on the platform; a
  random endpoint-only responder shifts the score 33%
  of full range, bounded and pinnable).  ``items`` field
  preserves RAW pre-flip for audit invariance.  See
  ``scoring/fneb.py``.
- UCLA-3 (Hughes 2004): 3 items, 1-3 Likert, ZERO reverse-keyed
  items.  Brief form of the UCLA Loneliness Scale derived by
  Hughes, Waite, Hawkley & Cacioppo (Research on Aging 2004,
  26(6):655-672) from Russell's 1980 full 20-item UCLA-R.
  Validated in the Health and Retirement Study (HRS) cohort
  (n = 2,101) with r = 0.82 against the full UCLA-R-20.
  Fills the platform's **loneliness / perceived-isolation
  gap** — clinically distinct from FNE-B (social-evaluative
  anxiety = fear of judgement) because UCLA-3 measures the
  orthogonal construct (actual perceived isolation).  A user
  can be high UCLA-3 with low FNE-B (widowed retiree, intact
  social skills but absent network) or vice versa (social-
  anxiety patient with many acquaintances but high
  evaluative apprehension).  The pair differentiates CAUSE
  of social under-engagement: high FNE-B low UCLA-3 →
  exposure + social-skills (Heimberg 1995), low FNE-B high
  UCLA-3 → structural social-contact building / befriending
  / peer-support, both elevated → combined protocol.
  Clinical load-bearing: (1) widowhood / bereavement relapse
  risk per Keyes 2012 (2.4× AUD-incidence elevation in the
  2-year post-widowhood window, mediated by loneliness);
  (2) retirement-trigger relapse detection per Satre 2004
  (structural social loss at retirement as proximal trigger,
  orthogonal to craving intensity); (3) Marlatt 1985 pp.
  137-142 negative-emotional-states proximal relapse
  precipitant (loneliness sub-type alongside depression and
  anhedonia); (4) Holt-Lunstad 2010 meta-analytic mortality-
  risk stratification (loneliness HR ≈ 1.26, effect-size
  comparable to smoking or obesity).  Items (Hughes 2004
  Table 1, verbatim): 1. lack companionship, 2. feel left
  out, 3. feel isolated from others.  All three are
  NEGATIVELY worded — Hughes 2004 deliberately omits Marsh
  1996 balanced-wording acquiescence control to preserve
  r = 0.82 equivalence with the full UCLA-R-20.  Total =
  raw sum (no flipping), range 3-9.  HIGHER = more lonely
  (lower-is-better direction).  NO bands — Hughes 2004
  published no cutpoints; Steptoe 2013 HRS-cohort tercile
  splits (3 / 4-5 / 6-9) are sample-descriptive and NOT
  pinned per CLAUDE.md.  NO T3 — no item probes
  suicidality; "feel isolated" (item 3) is a subjective-
  connection construct, NOT ideation.  Clinician-UI
  surfaces high UCLA-3 as C-SSRS-follow-up context per
  Calati 2019 (k=40 meta-analysis) but assessment itself
  does not set ``requires_t3``.  Acquiescence gap = 6 (the
  full 3-9 range × endpoint exposure), the highest
  endpoint-exposure on the platform — trade-off Hughes 2004
  made for brevity.  Linear signature: total = 3v for every
  all-v constant vector.  ``items`` field = raw input
  (identity under no-reverse-keying).  See ``scoring/ucla3.py``.
- CIUS (Meerkerk 2009): 14 items, 0-4 Likert, ZERO reverse-
  keyed items.  The Compulsive Internet Use Scale developed
  by Meerkerk, Van Den Eijnden, Vermulst & Garretsen
  (CyberPsychology & Behavior 2009, 12(1):1-6) on a Dutch
  adolescent / adult sample (n = 447 derivation + n = 16,925
  cross-validation).  Cronbach α = 0.89; single-factor CFA
  confirmed by Guertler 2014 on n = 2,512 German sample.
  Fills the platform's **behavioral-addiction substrate /
  digital compensation gap** — directly follows the Caplan
  2003 compensatory-internet-use thread opened by FNE-B
  (social-anxiety-driven digital escape) and UCLA-3
  (loneliness-driven digital substitution).  Three
  addiction-relevant clinical use cases drive the
  measurement: (1) Caplan 2003 compensatory-internet-use
  detection — the FNE-B / UCLA-3 / CIUS triad differentiates
  socially-avoidant digital compensation (high FNE-B + low
  UCLA-3 + high CIUS → exposure + use limits) from
  isolation-compensating digital substitution (low FNE-B +
  high UCLA-3 + high CIUS → structural social-contact
  building + use limits); (2) cross-addiction relapse-risk
  detection per Koob 2005 allostatic-reward-deficiency
  theory — rising CIUS trajectory in a recovering user is an
  early-warning signal that the brain is finding alternative
  allostatic load rather than resolving it; (3) ICD-11 6C51
  Gaming Disorder / DSM-5 Section III IGD overlap for
  clinical-completeness surfacing alongside AUDIT / DAST-10
  in the substance-use panel.  Items (Meerkerk 2009 Table 1,
  abbreviated): 1. difficult-to-stop, 2. continue-despite-
  intention, 3. others-say-use-less, 4. prefer-Internet-over-
  others, 5. short-of-sleep, 6. think-when-offline, 7. look-
  forward-to-next-session, 8. should-use-less, 9.
  unsuccessfully-tried-cut-down, 10. rush-homework-to-use,
  11. neglect-obligations, 12. go-online-when-down, 13.
  escape-negative-feelings-via-Internet, 14. restless-when-
  cannot-use.  Response scale 0 ("Never"), 1 ("Seldom"),
  2 ("Sometimes"), 3 ("Often"), 4 ("Very often").  Total =
  raw sum (no flipping), range 0-56.  HIGHER = more
  compulsive use (lower-is-better direction).  NO bands —
  Meerkerk 2009 published no cutpoints; Guertler 2014's
  >= 21 / >= 28 thresholds are secondary literature excluded
  per CLAUDE.md.  NO T3 — no item probes suicidality;
  withdrawal-like restlessness (item 14) is behavioral-
  addiction criterion, NOT active-risk ideation.  Special
  validation property: CIUS is the FIRST platform instrument
  with a valid 0-response.  Pydantic coerces JSON
  ``false -> 0`` which is now in range; the scorer's bool
  rejection (run BEFORE range check) protects against
  serialization bugs that would silently score ``False`` as
  "never" (zero compulsivity).  Acquiescence signature:
  total = 14v linear, endpoint-gap = 56 (full range — the
  widest on the platform, uniform with UCLA-3's proportion-
  of-range).  ``items`` field = raw input (identity under
  zero-reverse-keying).  See ``scoring/cius.py``.
- SWLS — 5 items, 1-7 Likert, NO reverse keying, unidimensional,
  Diener, Emmons, Larsen & Griffin 1985 (Journal of Personality
  Assessment 49(1):71-75).  Total = straight sum, range 5-35.
  HIGHER = more satisfied (uniform with WHO-5 / LOT-R / BRS /
  MAAS / RSES / CD-RISC-10 / FFMQ-15 / PANAS-10 PA higher-is-
  better direction).  Severity = ``"continuous"`` — Pavot &
  Diener 1993 seven-band interpretive guidelines (Extremely
  satisfied 31-35, Satisfied 26-30, Slightly satisfied 21-25,
  Neutral 20, Slightly dissatisfied 15-19, Dissatisfied 10-14,
  Extremely dissatisfied 5-9) stay at the clinician-UI renderer
  layer, NOT in the envelope band — consistent with UCLA-3 /
  CIUS "continuous measure with published interpretive
  guidelines" platform posture and CLAUDE.md non-negotiable #9.
  NO T3 — no item probes suicidality; item 5 ("would change
  almost nothing") is a counterfactual life-evaluation probe,
  not ideation.  Low SWLS paired with low LOT-R surfaces the
  Beck 1985 hopelessness-suicide-risk profile at the clinician-
  UI layer as a C-SSRS follow-up prompt, NOT as a scorer-layer
  T3 flag.  Acquiescence signature: total = 5v linear, endpoint-
  gap = 30 (full 5-35 range, 100% of range — matches UCLA-3 /
  CIUS relative endpoint-exposure profile).  ``items`` field =
  raw input (identity under zero-reverse-keying).  Fills a
  cognitive-vs-affective gap: WHO-5 measures affective
  wellbeing, LOT-R measures dispositional optimism, BRS measures
  bounce-back resilience; SWLS measures cognitive-judgmental
  global life evaluation ("does my life match my ideal?")
  which has independent predictive validity for delayed relapse
  (Moos 2005 AUD n=628 16-year follow-up — SWLS at 1-3 years
  predicts year-16 remission where affective measures do not).
  See ``scoring/swls.py``.

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
from .scoring.aces import (
    ACES_POSITIVE_CUTOFF,
    InvalidResponseError as AcesInvalid,
    score_aces,
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
from .scoring.brs import (
    InvalidResponseError as BrsInvalid,
    score_brs,
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
from .scoring.erq import (
    InvalidResponseError as ErqInvalid,
    score_erq,
)
from .scoring.ffmq15 import (
    FFMQ15_SUBSCALES,
    InvalidResponseError as Ffmq15Invalid,
    score_ffmq15,
)
from .scoring.fneb import (
    InvalidResponseError as FnebInvalid,
    score_fneb,
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
from .scoring.maas import (
    InvalidResponseError as MaasInvalid,
    score_maas,
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
from .scoring.panas10 import (
    InvalidResponseError as Panas10Invalid,
    PANAS10_SUBSCALES,
    score_panas10,
)
from .scoring.pcl5 import (
    InvalidResponseError as Pcl5Invalid,
    score_pcl5,
)
from .scoring.pgsi import (
    InvalidResponseError as PgsiInvalid,
    score_pgsi,
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
from .scoring.rrs10 import (
    InvalidResponseError as Rrs10Invalid,
    score_rrs10,
)
from .scoring.rses import (
    InvalidResponseError as RsesInvalid,
    score_rses,
)
from .scoring.scoff import (
    InvalidResponseError as ScoffInvalid,
    SCOFF_POSITIVE_CUTOFF,
    score_scoff,
)
from .scoring.scssf import (
    InvalidResponseError as ScsSfInvalid,
    score_scssf,
)
from .scoring.shaps import (
    InvalidResponseError as ShapsInvalid,
    score_shaps,
)
from .scoring.sds import (
    InvalidResponseError as SdsInvalid,
    Substance as SdsSubstance,
    score_sds,
)
from .scoring.stai6 import (
    InvalidResponseError as Stai6Invalid,
    score_stai6,
)
from .scoring.ucla3 import (
    InvalidResponseError as Ucla3Invalid,
    score_ucla3,
)
from .scoring.cius import (
    InvalidResponseError as CiusInvalid,
    score_cius,
)
from .scoring.swls import (
    InvalidResponseError as SwlsInvalid,
    score_swls,
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
    "erq",
    "scssf",
    "rrs10",
    "maas",
    "shaps",
    "aces",
    "pgsi",
    "brs",
    "scoff",
    "panas10",
    "rses",
    "ffmq15",
    "stai6",
    "fneb",
    "ucla3",
    "cius",
    "swls",
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
    "erq": 10,
    "scssf": 12,
    "rrs10": 10,
    "maas": 15,
    "shaps": 14,
    "aces": 10,
    "pgsi": 9,
    "brs": 6,
    "scoff": 5,
    "panas10": 10,
    "rses": 10,
    "ffmq15": 15,
    "stai6": 6,
    "fneb": 12,
    "ucla3": 3,
    "cius": 14,
    "swls": 5,
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
    if payload.instrument == "erq":
        # Gross & John 2003 Emotion Regulation Questionnaire — the
        # validated 10-item measure of strategy choice: cognitive
        # reappraisal (antecedent-focused, applied early in the
        # emotion-generative cycle) vs expressive suppression
        # (response-focused, applied after the emotion is active).
        # Clinically: the STRATEGY-CHOICE layer completing the three-
        # layer emotion-processing architecture that TAS-20 (upstream
        # IDENTIFY) and DERS-16 (downstream EXECUTE) frame.  The
        # intervention-selection layer reads the 3-instrument profile:
        #   (a) high TAS-20 DIF → affect-labeling FIRST (strategy
        #       choice is moot if the emotion can't be named);
        #   (b) TAS-20 OK + ERQ suppression-dominant → cognitive-
        #       reappraisal training BEFORE skill-building (patient
        #       is regulating but via a strategy that paradoxically
        #       amplifies the state — Gross 1998, Butler 2003);
        #   (c) TAS-20 OK + ERQ reappraisal already high + DERS-16
        #       high → distress-tolerance capacity work (patient
        #       knows the right strategy but emotional load has
        #       overwhelmed execution capacity).
        # Aldao 2010 meta-analysis (114 studies): higher reappraisal
        # predicts BETTER outcomes on every indicator studied (mood,
        # life satisfaction, interpersonal functioning, health);
        # higher suppression predicts WORSE outcomes on the same
        # indicators.  Bonn-Miller 2011 / Hofmann 2012: suppression
        # predicts substance-use / compulsive-behavior relapse more
        # strongly than reappraisal protects — the platform reads
        # elevated suppression as a preemptive relapse-risk signal.
        # 10 items, 1-7 Likert (1 = strongly disagree, 7 = strongly
        # agree).  **NO reverse-keyed items** — all 10 items are
        # endorsement-direction for their subscale, distinguishing
        # ERQ from TAS-20 / LOT-R / PSWQ (arithmetic-reflection flips
        # required for those).  Two subscales per Gross & John 2003
        # Study 1 CFA: reappraisal (6 items: 1, 3, 5, 7, 8, 10),
        # suppression (4 items: 2, 4, 6, 9).  Surfaced via the
        # ``subscales`` map with keys ``reappraisal`` / ``suppression``
        # (uniform with DERS-16 / TAS-20 subscale dispatch shape).
        # **Novel Likert envelope** (1-7) vs prior instruments (1-5
        # for TAS-20 / DERS-16 / PSWQ; 0-3 for PHQ-9 / GAD-7; 0-5
        # for WHO-5; 0-4 for LOT-R).
        # **Continuous-sentinel band** — Gross & John 2003 published
        # no severity cutoffs; ERQ is a dispositional continuous
        # measure interpreted by the subscale PROFILE (the
        # ``reappraisal, suppression`` 2-tuple), not by an aggregate
        # classification.  Hand-rolling bands (e.g. median-split the
        # normative sample) would violate CLAUDE.md's "Don't hand-roll
        # severity thresholds" rule and collapse the clinically
        # critical 2-tuple signal into a single ordinal.  Router
        # emits the continuous-sentinel ``severity="continuous"``
        # literal (uniform with DERS-16 / BRS / PSWQ / SDS / K6 /
        # CD-RISC-10 / LOT-R / PACS / BIS-11).
        # Direction note: the two subscales go OPPOSITE clinical
        # directions at the aggregate level — higher reappraisal is
        # protective, higher suppression is risk-elevating — but the
        # router emits both subscale sums without imposing a
        # directional frame, because the relevant signal is the
        # PROFILE (both values), not a pooled direction.  Downstream
        # trajectory coverage (when added) will register reappraisal
        # in the higher-is-better partition and suppression in the
        # higher-is-worse partition.
        # ``cutoff_used`` / ``positive_screen`` NOT set — ERQ has no
        # binary cutoff.  No T3 — the 10 items probe self-rated
        # strategy use; none probe suicidality.  Acute ideation
        # screening stays on PHQ-9 item 9 / C-SSRS.  See
        # ``scoring/erq.py``.
        er = score_erq(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="erq",
            total=er.total,
            severity="continuous",
            requires_t3=False,
            subscales={
                "reappraisal": er.subscale_reappraisal,
                "suppression": er.subscale_suppression,
            },
            instrument_version=er.instrument_version,
        )
    if payload.instrument == "scssf":
        # Raes, Pommier, Neff & Van Gucht 2011 Self-Compassion Scale
        # Short Form — the validated 12-item short form of Neff 2003's
        # 26-item SCS.  Measures self-compassion: the 3-component
        # construct pair (self-kindness vs self-judgment, common
        # humanity vs isolation, mindfulness vs over-identification)
        # that is the empirically documented antagonist of shame
        # (MacBeth & Gumley 2012 meta-analysis).  Clinically load-
        # bearing for the platform's "compassion-first relapse copy"
        # non-negotiable (CLAUDE.md): shame-avoidance drives the
        # abstinence-violation effect (Marlatt 1985), and low SCS-SF
        # is the measurement signal identifying relapse-risk-via-
        # shame patients.  The intervention-selection layer routes
        # low-compassion / high-uncompassionate-self-responding
        # profiles to CFT (Gilbert 2014) tool variants BEFORE the
        # next urge episode, and proactively re-engages those
        # patients post-relapse with compassion-framed copy (never
        # "streak reset", never "you failed").
        # 12 items, 1-5 Likert.  Reverse-keying on the 6 uncompassion-
        # ate items (1, 4, 8, 9, 11, 12) via the PSWQ / LOT-R /
        # TAS-20 arithmetic-reflection idiom (``flipped = 6 - raw``).
        # Six 2-item subscales per Raes 2011 / Neff 2003 factor
        # structure — largest subscale count in the package (DERS-16
        # had 5, URICA had 4, TAS-20 had 3, ERQ / LOT-R had 2).
        # Surfaced via ``subscales`` map with keys ``self_kindness``
        # / ``self_judgment`` / ``common_humanity`` / ``isolation`` /
        # ``mindfulness`` / ``over_identification``.
        # **Novel scoring asymmetry** — TOTAL is POST-flip (aggregate
        # reads in self-compassion direction, range 12-60), but
        # SUBSCALES are RAW (native construct direction — SJ reads as
        # "how much self-judgment does the patient endorse", NOT the
        # post-flip inversion).  This is DELIBERATE per Raes 2011 /
        # Neff 2016 methodology: subscales preserve the positive /
        # negative construct dyad structure so a clinician can read
        # the dyad imbalance directly (e.g. "high SK + high SJ" =
        # CFT-target dyad) rather than the collapsed post-flip view.
        # Note this differs from TAS-20 where subscales ARE post-
        # flipped — because TAS-20's 3 subscales all measure the
        # same pathology direction, while SCS-SF's 6 subscales are
        # intentional positive/negative pairs.
        # **Built-in acquiescence catch**: all-1s and all-5s both
        # yield total=36 (midpoint) because the balanced positive
        # and negative items cancel.  This is a FEATURE of the
        # Neff 2003 / Raes 2011 instrument design — the clinician-
        # UI layer flags this pattern (all subscales simultaneously
        # at 10) for bias review.
        # **Higher-is-better** direction (uniform with WHO-5 /
        # CD-RISC-10 / LOT-R / DTCQ-8 / BRS).
        # **Continuous-sentinel** — Raes 2011 published no validated
        # bands.  Hand-rolling a cutoff from descriptive ranges
        # (< 30 low, > 45 high in the literature) would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds" rule.
        # Router emits ``severity="continuous"`` (uniform with
        # DERS-16 / ERQ / BRS / PSWQ / SDS / K6 / CD-RISC-10 /
        # LOT-R / PACS / BIS-11).
        # ``cutoff_used`` / ``positive_screen`` NOT set.  No T3 —
        # the 12 items probe dispositional self-related responding;
        # none probe suicidality.  Acute ideation screening stays
        # on PHQ-9 item 9 / C-SSRS.  See ``scoring/scssf.py``.
        sc = score_scssf(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="scssf",
            total=sc.total,
            severity="continuous",
            requires_t3=False,
            subscales={
                "self_kindness": sc.subscale_self_kindness,
                "self_judgment": sc.subscale_self_judgment,
                "common_humanity": sc.subscale_common_humanity,
                "isolation": sc.subscale_isolation,
                "mindfulness": sc.subscale_mindfulness,
                "over_identification": sc.subscale_over_identification,
            },
            instrument_version=sc.instrument_version,
        )
    if payload.instrument == "rrs10":
        # Treynor, Gonzalez & Nolen-Hoeksema 2003 Ruminative Responses
        # Scale, 10-item refined subset of Nolen-Hoeksema's RRS-22.
        # Measures rumination — the attentional/cognitive loop that
        # sustains affect past its natural decay.  Treynor 2003 PCA
        # extracted two factors from the 10 non-symptom-confounded
        # items of the RRS-22: Brooding (maladaptive passive
        # evaluative comparison — items 1, 3, 6, 7, 8) and Reflection
        # (adaptive active analytic problem-solving — items 2, 4, 5,
        # 9, 10).  This two-factor split is the whole clinical point
        # of RRS-10 over RRS-22: treatment routing depends on WHICH
        # rumination style dominates, not total rumination.
        # Clinically load-bearing for the platform's 60-180 s urge-
        # intervention window: brooding is the attentional engine
        # that keeps a craving alive past natural decay.  Caselli
        # 2010 demonstrated that brooding prospectively predicts
        # time-to-relapse in alcohol-use-disorder samples independent
        # of concurrent depression; reflection does not carry the
        # same prospective risk.  Downstream intervention routing
        # reads the (brooding, reflection) 2-tuple:
        #   high brood / low reflect → mindfulness / attention-
        #       deployment tools BEFORE any cognitive intervention
        #       (cognitive work on a brood-dominant mind amplifies
        #       the loop; Watkins 2008 abstract-thinking account).
        #   high brood / high reflect → brief attention-deployment
        #       bridge, then analytical reframing.
        #   low brood / high reflect → adaptive; minimal scaffolding.
        #   low brood / low reflect → evaluate for emotion avoidance
        #       (cross-read with TAS-20 DIF, ERQ suppression,
        #       AAQ-II experiential avoidance).
        # 10 items, 1-4 Likert.  No reverse items (Treynor 2003
        # wording is direction-aligned throughout, like ERQ).
        # Two 5-item subscales; each sums to 5-20.  Total 10-40.
        # **Continuous-sentinel** — Treynor 2003 published no
        # validated bands; population norms vary across samples
        # (Schoofs 2010 Belgian, Whitmer 2011 US) and hand-rolling a
        # cutoff would violate CLAUDE.md's "Don't hand-roll severity
        # thresholds" rule.  Router emits ``severity="continuous"``
        # (uniform with DERS-16 / ERQ / BRS / PSWQ / SDS / K6 /
        # SCS-SF).
        # ``cutoff_used`` / ``positive_screen`` NOT set.  No T3 —
        # the 10 items probe attentional style during low mood;
        # none probe suicidality.  Note: the parent RRS-22 contains
        # suicidality-adjacent content, but the Treynor 2003 subset
        # specifically does NOT — one of the reasons the 10-item
        # version was extracted for non-symptom-confounded process
        # measurement.  Acute ideation screening stays on PHQ-9
        # item 9 / C-SSRS.  See ``scoring/rrs10.py``.
        rr = score_rrs10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="rrs10",
            total=rr.total,
            severity="continuous",
            requires_t3=False,
            subscales={
                "brooding": rr.subscale_brooding,
                "reflection": rr.subscale_reflection,
            },
            instrument_version=rr.instrument_version,
        )
    if payload.instrument == "maas":
        # Brown & Ryan 2003 Mindful Attention Awareness Scale — 15-item
        # dispositional trait-mindfulness measure.  Single-factor
        # (Brown & Ryan 2003 EFA, Carlson & Brown 2005 CFA, MacKillop
        # & Anderson 2007 IRT).  The platform's primary outcome
        # measure for mindfulness-based tool variants (grounding,
        # urge-surfing, 3-minute breathing space, body scan, 5-4-3-2-1
        # sensory) — Bowen 2014 MBRP RCT used MAAS as its primary
        # trait-mindfulness outcome, and the same logic carries
        # here: MAAS is the dispositional signal for whether the
        # mindfulness-based interventions are changing the patient's
        # default attentional mode, not just their in-session state.
        # Baseline MAAS also gates treatment sequence: low MAAS at
        # enrollment routes to attention-training BEFORE cognitive
        # or exposure work, because those tools assume a patient
        # who can notice their own internal state.
        # All 15 items are worded in the MINDLESSNESS direction; the
        # 1-6 Likert anchors (1 = almost always [mindless], 6 = almost
        # never [mindless]) mean the native total already reads
        # higher = more mindful — no flip arithmetic at the scorer.
        # **Novel wire shape on this platform**: continuous + NO
        # subscales at 15 items.  Other unidimensional-continuous
        # instruments shipped: PSWQ 16, CD-RISC-10 10, K6 6, BRS 6,
        # DTCQ-8 8.  MAAS fits the family but is the second-largest
        # (after PSWQ).  Total 15-90; the downstream renderer divides
        # by 15 to produce the Brown & Ryan 2003 published mean
        # metric (1.0-6.0) for descriptive comparison against the
        # community (≈ 4.1) / MBSR-post (≈ 4.3; Carmody 2008) /
        # SUD-sample (≈ 3.2-3.5; Bowen 2014 baseline) ranges.
        # **Continuous-sentinel** — no validated bands; Brown & Ryan
        # 2003 and every subsequent major validation (Carlson 2005,
        # MacKillop 2007, Christopher 2009, Park 2013 systematic
        # review) treat MAAS as dispositional continuous.  Router
        # emits ``severity="continuous"`` (uniform with DERS-16 /
        # ERQ / BRS / PSWQ / SDS / K6 / SCS-SF / RRS-10 / CD-RISC-
        # 10 / LOT-R).
        # Higher-is-better direction (uniform with WHO-5 / CD-RISC-
        # 10 / LOT-R / DTCQ-8 / BRS / SCS-SF total).
        # ``cutoff_used`` / ``positive_screen`` / ``subscales`` NOT
        # set.  No T3 — the 15 items probe attentional default
        # patterns; none probe suicidality.  Acute ideation
        # screening stays on PHQ-9 item 9 / C-SSRS.  See
        # ``scoring/maas.py``.
        ma = score_maas(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="maas",
            total=ma.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=ma.instrument_version,
        )
    if payload.instrument == "shaps":
        # Snaith 1995 Snaith-Hamilton Pleasure Scale — 14-item 1-4
        # Likert anhedonia measure.  Unidimensional (Franken 2007
        # PCA, Leventhal 2006 CFA, Nakonezny 2010 IRT).  The platform's
        # primary hedonic-reactivity signal — anhedonia is a
        # prospective SUD-relapse predictor independent of depressed
        # mood (Garfield 2014 systematic review; Koob 2008 opponent-
        # process theory) and the indication for behavioral-
        # activation-augmented intervention (Daughters 2008 LETS ACT,
        # Magidson 2011) vs standard MBRP / CBT.  Paired with MAAS:
        # low MAAS + positive SHAPS is the post-acute-withdrawal
        # signature (attention impaired AND reward response blunted)
        # and routes to BA + attention-training in combination, not
        # mindfulness-only.
        # **Novel wire shape on this platform**: the first scorer
        # whose stored ``total`` is NOT a linear function of the raw
        # per-item input.  Raw 1-4 Likert is DICHOTOMIZED per
        # Snaith 1995 (raw 1/2 → 0 hedonic, raw 3/4 → 1 anhedonic)
        # BEFORE summation — total 0-14 is a count of anhedonic
        # items, not the raw Likert sum.  The raw 1-4 response is
        # preserved verbatim in the scorer's ``items`` tuple so
        # FHIR export surfaces the original response and downstream
        # consumers can recover the Franken 2007 continuous
        # alternative (sum of raw - 14, range 0-42) without
        # re-acquiring the data.
        # **Cutoff-based wire envelope** — ``total >= 3`` is the
        # Snaith 1995 §Results operating point (sensitivity 0.77 /
        # specificity 0.82 against MINI depression per Franken 2007).
        # Envelope matches OCI-R / MDQ / PC-PTSD-5 / AUDIT-C: severity
        # carries the positive/negative_screen string, positive_screen
        # field carries the bool, cutoff_used field carries the
        # integer 3 so the clinician UI renders the same threshold
        # the trajectory RCI layer uses.
        # Higher-is-worse direction (same as PHQ-9 / GAD-7 / PSS-10 /
        # K6) — rising total = worsening anhedonia; the trajectory
        # layer's RCI direction logic must register SHAPS in the
        # higher-is-worse partition, NOT with WHO-5 / MAAS / CD-RISC-
        # 10.  A silent direction flip would register treatment
        # gains as anhedonia worsening and vice-versa.
        # No T3 — SHAPS has no safety item.  The 14 items probe
        # hedonic capacity only; phenomenological closeness to
        # suicidal ideation in severe depression (Fawcett 1990) is
        # handled at the PROFILE level (SHAPS + PHQ-9 + C-SSRS), not
        # via per-item SHAPS content triggering T3.  Acute ideation
        # screening stays on C-SSRS / PHQ-9 item 9.  See
        # ``scoring/shaps.py``.
        sh = score_shaps(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="shaps",
            total=sh.total,
            severity=(
                "positive_screen" if sh.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=sh.positive_screen,
            cutoff_used=3,
            instrument_version=sh.instrument_version,
        )
    if payload.instrument == "aces":
        # Felitti 1998 Adverse Childhood Experiences Questionnaire —
        # 10-item binary lifetime-exposure count.  THE etiological-
        # stratification instrument: every other instrument the
        # platform ships measures a current state (past 2 weeks for
        # PHQ-9, past week for SHAPS, dispositional-current for MAAS);
        # ACEs measures lifetime exposure before age 18.  ACE >= 4 =
        # 4.7x alcoholism risk / 10.3x IDU risk (Felitti 1998) and
        # 7.4x problem drinking / 10.2x problem drug use in the
        # Hughes 2017 meta-analysis (n = 253,719).  Used at enrollment
        # to stratify treatment sequencing — ACE >= 4 routes to
        # trauma-informed-care (TIC) sequencing BEFORE standard CBT-
        # based relapse-prevention intervention (van der Kolk 2014;
        # Briere 2012; Herman 1992 three-stage model).  Profile
        # pairings with instruments already shipped:
        #   - high ACE + positive SHAPS = developmental-anhedonia
        #     profile (Anda 2006 reward-circuit hypofunction) → BA
        #     + TIC, NOT mindfulness-only;
        #   - high ACE + low MAAS = dissociative-attention profile
        #     → grounding / sensory tools BEFORE open-awareness
        #     meditation;
        #   - high ACE + high DERS nonacceptance = chronic-
        #     dysregulation profile → DBT skills-first (Linehan);
        #   - high ACE + positive PCL-5 = chronic PTSD profile →
        #     stabilization-phase before trauma-processing;
        #   - high ACE + positive AUDIT-C/DUDIT = self-medication
        #     profile (Khantzian 1997) → integrated trauma/SUD
        #     treatment (Najavits 2002 Seeking Safety).
        # **Novel wire shape on this platform**: first BINARY-item
        # instrument — each item is 0 (No) or 1 (Yes); values in a
        # plausible range (2-10) but not strictly binary are rejected
        # at the scorer.  First RETROSPECTIVE instrument — lifetime
        # exposure rather than current state; trajectory-layer treats
        # ACEs specially as a one-time-enrollment measurement rather
        # than a repeated trajectory measure (Felitti 1998 test-
        # retest r = 0.66 at 1.5 years — re-administration is not
        # clinically meaningful).  That upstream handling is not a
        # scorer concern — the scorer is stateless.
        # **Cutoff envelope** — ``total >= 4`` is the Felitti 1998
        # §Results operating point.  Envelope matches SHAPS / OCI-R /
        # MDQ / PC-PTSD-5 / AUDIT-C: severity carries the positive_
        # screen / negative_screen string, positive_screen field
        # carries the bool, cutoff_used field carries the integer 4
        # so the clinician UI renders the same threshold the
        # trajectory RCI layer uses.  No subscale surfacing — Dong
        # 2004 rejected the three-subscale (abuse / neglect /
        # dysfunction) model as producing unstable per-domain
        # cutoffs; only total-score cutoff is validated.
        # Higher-is-worse direction (same as PHQ-9 / GAD-7 / SHAPS /
        # PSS-10 / K6) — rising total = more cumulative adversity;
        # the trajectory RCI direction logic must register ACEs in
        # the higher-is-worse partition, NOT with WHO-5 / MAAS / CD-
        # RISC-10 (higher-is-better).
        # No T3 — ACEs probes retrospective childhood exposure, not
        # current ideation.  A patient with ACE = 10 carries elevated
        # dispositional risk across the lifespan but that is not
        # time-limited current-state crisis.  Acute ideation
        # screening stays on C-SSRS / PHQ-9 item 9.  Content-
        # sensitivity of items 1-3 (abuse) and item 6 (maternal
        # violence) is handled by the administration UI (content
        # warning, opt-out, post-administration resources), not the
        # scorer.  See ``scoring/aces.py``.
        ac = score_aces(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="aces",
            total=ac.total,
            severity=(
                "positive_screen" if ac.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=ac.positive_screen,
            cutoff_used=ACES_POSITIVE_CUTOFF,
            instrument_version=ac.instrument_version,
        )
    if payload.instrument == "pgsi":
        # Ferris & Wynne 2001 Problem Gambling Severity Index — 9-item
        # 0-3 Likert, banded severity per Canadian Problem Gambling
        # Index.  The platform's FIRST behavioral-addiction instrument:
        # every prior scorer targets substance-use (AUDIT / DAST / DUDIT
        # / SDS / PACS / DTCQ / URICA / Craving VAS) or an internalizing
        # / regulatory dimension (PHQ-9 / GAD-7 / PSS-10 / OCI-R / PCL-5
        # / SHAPS / MAAS / DERS-16 / ACEs).  PGSI expands the scope to
        # compulsive-behavior cycles that are not substance-mediated —
        # the exact 60-180 s urge-to-action window the product
        # intervenes on, applied to a non-substance reinforcer.
        # Gambling co-occurs with SUD at 10-20% population (Lorains
        # 2011) and 35-60% clinical (Petry 2005 NESARC).  Gambling
        # disorder was reclassified from DSM-IV "Impulse Control
        # Disorders NEC" to DSM-5 "Substance-Related and Addictive
        # Disorders" (APA 2013; Petry 2013) because the behavioral-
        # addiction mechanics (intermittent variable-ratio reinforcement
        # Skinner 1957; ventral-striatum reward-cue sensitization
        # Potenza 2003 fMRI; tolerance; chasing-losses analogue to
        # Marlatt 1985 abstinence-violation effect) are indistinguishable
        # from SUD mechanics.
        # Profile pairings with instruments already shipped:
        #   - AUDIT-C/DUDIT + PGSI → dual-addiction profile (Petry
        #     2005) → integrated concurrent treatment, not sequential;
        #   - ACEs + PGSI → trauma-driven behavioral-addiction profile
        #     (Felitti 2003 includes gambling in ACE dose-response;
        #     Hodgins 2010) → TIC sequencing applies identically;
        #   - BIS-11 + PGSI → impulsivity-driven gambling profile
        #     (Steel 1998; Alessi 2003) → DBT distress-tolerance /
        #     implementation-intention over exposure-centric;
        #   - SHAPS + PGSI → anhedonic-compulsive-gambler profile
        #     (Blaszczynski 2002 Pathway 2 emotionally-vulnerable
        #     subtype) → BA + gambling-specific CBT;
        #   - PHQ-9 + PGSI → depressed-gambler profile (Kessler 2008
        #     38% MDD comorbidity) → concurrent mood + gambling
        #     treatment.
        # **Novel wire shape on this platform**: first BEHAVIORAL-
        # ADDICTION severity-banded instrument.  AUDIT is also 4-
        # banded (Saunders 1993 low-risk / increasing / high / possible-
        # dependence) but targets substance use; PGSI is the first
        # non-substance banded instrument.  Wire envelope matches the
        # AUDIT / PHQ-9 / GAD-7 / PSS-10 / ISI banded-severity shape —
        # severity carries one of "non_problem" / "low_risk" /
        # "moderate_risk" / "problem_gambler" (Ferris 2001 Table 5.1
        # population-derived operating points with kappa = 0.83 vs
        # DSM-IV pathological-gambling diagnosis at the >=8 cutoff;
        # Currie 2013 confirmed the cut-points across n = 12,229).
        # cutoff_used / positive_screen NOT set — banded, not screen.
        # subscales NOT set — Ferris 2001 retained unidimensional
        # structure by design (9 items extracted from 31-item pool
        # via factor analysis to preserve single-factor severity).
        # Higher-is-worse direction (same as PHQ-9 / GAD-7 / SHAPS /
        # ACEs) — rising total = worsening gambling-problem severity;
        # trajectory RCI direction logic must register PGSI in the
        # higher-is-worse partition, NOT with WHO-5 / MAAS / CD-RISC-
        # 10 / LOT-R / BRS / DTCQ-8.
        # No T3 — PGSI has no safety item.  Items 5 ("might have a
        # problem") and 9 ("felt guilty") are problem-awareness /
        # affect items, NOT suicide-ideation / self-harm items.
        # The well-established problem-gambler suicide-risk
        # elevation (Moghaddam 2015 meta-analysis: 3.4x attempt
        # risk) is handled at the PROFILE level (PGSI + PHQ-9 +
        # C-SSRS), not via per-PGSI-item T3 triggering.  See
        # ``scoring/pgsi.py``.
        pg = score_pgsi(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pgsi",
            total=pg.total,
            severity=pg.severity,
            requires_t3=False,
            instrument_version=pg.instrument_version,
        )
    if payload.instrument == "brs":
        # Smith 2008 Brief Resilience Scale — 6-item 1-5 Likert.
        # Measures ECOLOGICAL / OUTCOME resilience (the capacity to
        # bounce back from adversity) — shipped deliberately
        # ALONGSIDE the previously-shipped CD-RISC-10 which measures
        # AGENTIC resilience (the personal resources that produce
        # recovery: optimism, self-efficacy, emotion regulation,
        # spiritual beliefs, adaptability).  Smith 2008 §3 framed
        # the distinction: CD-RISC ≈ "I have the resources"; BRS ≈
        # "I do, in fact, bounce back".  Windle 2011 systematic
        # review recommended PAIRING both for complete-coverage
        # resilience assessment — BRS rated highest on content /
        # construct validity among brief instruments; CD-RISC
        # highest among comprehensive instruments.
        # Clinical value of shipping both = the DISCREPANCY
        # profile: high CD-RISC + low BRS = resources present on
        # paper but not deployed.  Typical mechanism: Beck 1967
        # cognitive-triad interference with resource deployment in
        # depression comorbidity.  Intervention framing shifts to
        # behavioral activation (Martell 2010) or values-based
        # committed action (ACT per Hayes 2012) rather than
        # resource-building.  The inverse (low CD-RISC + high BRS)
        # is rare — when present, it indicates externally-scaffolded
        # recovery (social support, environmental stability) that
        # should be reinforced rather than supplemented with
        # resource-building work.
        # Reverse-keying: items 2, 4, 6 are negatively worded ("It
        # is hard for me to snap back..." / "It is hard for me to
        # bounce back..." / "I tend to take a long time...").  The
        # scorer applies ``6 - raw`` internally (shared idiom with
        # TAS-20 / PSWQ / LOT-R).  The PATIENT sees the items in
        # the original phrasing; the scorer flips them before
        # summing.  The BrsResult.items field preserves the RAW
        # PRE-FLIP responses — audit-trail invariance per the
        # TAS-20 / PSWQ / LOT-R contract.
        # Acquiescence-bias control: the three-positive /
        # three-negative symmetry is Smith 2008's EFA-derived
        # response-set control.  By construction both uniform-
        # response extremes (all-1s and all-5s) produce post-flip
        # sum 18, landing at the LOW-NORMAL boundary.  This is a
        # feature, not a bug — response-set bias cannot push a
        # patient into either extreme band.
        # **Novel wire shape on this platform**: first HIGHER-IS-
        # BETTER banded-severity instrument.  WHO-5 / MAAS /
        # CD-RISC-10 / LOT-R are higher-is-better but use either
        # index conversion (WHO-5) or continuous-band semantics.
        # BRS uses discrete banded severity (low/normal/high)
        # with higher-is-better direction — the trajectory RCI
        # direction logic must register BRS in the higher-is-
        # better partition (with WHO-5 / MAAS / CD-RISC-10 /
        # LOT-R / DTCQ-8), NOT with PHQ-9 / GAD-7 / AUDIT / PGSI.
        # Wire envelope matches PHQ-9 / GAD-7 / AUDIT / PSS-10 /
        # ISI / PGSI banded-severity shape — severity carries one
        # of "low" / "normal" / "high" (Smith 2008 §3.3 conceptual-
        # mean framework mapped to integer-sum 6-17 / 18-25 /
        # 26-30).  cutoff_used / positive_screen NOT set — banded,
        # not screen.  subscales NOT set — Smith 2008 §3.2 EFA
        # single-factor solution (eigenvalue 2.68, second 0.64);
        # surfacing positive-item / negative-item sums would
        # contradict the factor derivation and double-count the
        # response-set bias the reverse-keying design exists to
        # control.
        # No T3 — no BRS item probes suicidality, self-harm, or
        # acute-risk behavior; the instrument measures resilience
        # outcomes only.  Acute-risk screening stays on C-SSRS /
        # PHQ-9 item 9.
        # Recovery-trajectory use: BRS is the platform's primary
        # within-subject recovery-trajectory anchor (test-retest
        # r = 0.69 at 3 months, Smith 2008 §3.2) — paired with
        # Jacobson & Truax 1991 RCI for clinically-significant-
        # change detection at the 3-month follow-up.  CD-RISC-10
        # is more state-sensitive and less suited to repeat
        # administration; BRS is the anchor.  See ``scoring/brs.py``.
        br = score_brs(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="brs",
            total=br.total,
            severity=br.severity,
            requires_t3=False,
            instrument_version=br.instrument_version,
        )
    if payload.instrument == "scoff":
        # Morgan, Reid & Lacey 1999 SCOFF — 5-item binary yes/no
        # eating-disorder screen.  Fills a clearly-missed clinical
        # domain: every prior instrument covers substance use
        # (AUDIT / AUDIT-C / DAST / DUDIT / SDS / PACS / DTCQ /
        # URICA / Craving VAS), an internalizing / regulatory
        # dimension (PHQ-9 / GAD-7 / PSS-10 / OCI-R / PCL-5 /
        # SHAPS / MAAS / DERS-16), trauma (ACEs / PC-PTSD-5), a
        # behavioral addiction (PGSI), or resilience (CD-RISC-10
        # / BRS).  None cover disordered eating.
        # Clinical load: eating disorders co-occur with SUD at
        # 25-50% in clinical samples (Hudson 2007 NCS-R: 23.7%
        # lifetime AN/BN comorbidity among SUD; Krug 2008
        # European multi-site n = 879: 45% lifetime SUD among
        # AN/BN).  The behavioral-addiction mechanics overlap
        # substantially (restraint-binge cycle in BN parallels
        # abstinence-violation effect in SUD; reward-prediction-
        # error dysfunction in AN parallels SUD anhedonia
        # profiles; compulsive cue-driven behavior patterns
        # converge — Kaye 2013 neurobiological review).  The
        # platform's 60-180 s urge-to-action intervention window
        # applies identically to binge-eating urges as to
        # substance-use urges (Jansen 2016 binge-cue reactivity
        # review).
        # Profile pairings with instruments already shipped:
        #   - SCOFF+ alone → primary ED pathway (CBT-E per
        #     Fairburn 2008 for BN/BED; specialist AN care per
        #     APA 2006);
        #   - SCOFF+ AND AUDIT+/DUDIT+ → co-occurring ED/SUD
        #     profile (Krug 2008 45% comorbidity) → concurrent
        #     integrated treatment per Harrop & Marlatt 2010,
        #     NOT substance-first-then-ED sequencing;
        #   - SCOFF+ AND PHQ-9 item-3 positive (appetite
        #     change) → resolves the ED-vs-MDD ambiguity in
        #     the bidirectional PHQ-9 appetite item;
        #   - SCOFF+ AND ACEs >= 4 → trauma-driven ED profile
        #     (Brewerton 2007 meta-analysis: childhood abuse is
        #     a consistent ED risk factor) → trauma-informed
        #     sequencing per van der Kolk 2014;
        #   - SCOFF+ AND BIS-11 high → impulsive binge-purge
        #     profile (Claes 2005) → DBT-adapted-for-ED per
        #     Safer 2009;
        #   - SCOFF+ AND OCI-R high → obsessive-compulsive-type
        #     restriction profile (Godier 2014 AN-OCD overlap)
        #     → intervention framing differs from impulsive
        #     binge profile.
        # Wire envelope matches AUDIT-C / PC-PTSD-5 / SHAPS /
        # ACEs binary-screen shape — total carries the positive-
        # item count (0-5), severity carries "positive_screen" /
        # "negative_screen", cutoff_used = SCOFF_POSITIVE_CUTOFF
        # (= 2 per Morgan 1999).  NO bands — SCOFF is a screen,
        # not a severity instrument (a count of 5 is not "more
        # severe" than 2 in a banded sense; both are above-
        # threshold positive screens requiring specialist
        # assessment).  Clinical follow-up (EDE-Q 2.0 per
        # Fairburn 1994; EDE interview per Cooper & Fairburn
        # 1987) is the severity instrument.  NO subscales — 5
        # clinical-consensus cues, not factor-partitioned.
        # No T3 — item 1 "make yourself Sick" explicitly means
        # PURGING BEHAVIOR (self-induced vomiting per Morgan
        # 1999 Background §1), NOT self-harm.  Acute-risk
        # screening stays on C-SSRS / PHQ-9 item 9.  Item 3
        # ("lost more than one stone in 3 months") is a medical-
        # risk indicator but NOT an acute-safety indicator at
        # the scorer level — a severe positive SCOFF triggers
        # the downstream ED-assessment pathway, not the T3
        # suicide-response protocol.
        # LOCALE-SENSITIVE NOTE: Morgan 1999 item 3 uses imperial
        # stones (UK publication).  Non-UK locales present a
        # validated-translation version with culturally-
        # appropriate mass unit (6.35 kg for EU/SI locales, 14 lb
        # for US locale — Kutz 2020 multi-language meta-
        # analysis validated the kg substitution).  The scorer
        # is locale-agnostic (only sees the yes/no response);
        # the administration-UI must present the culturally-
        # appropriate translation.  See ``scoring/scoff.py``.
        sc = score_scoff(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="scoff",
            total=sc.total,
            severity=(
                "positive_screen" if sc.positive_screen
                else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=sc.positive_screen,
            cutoff_used=SCOFF_POSITIVE_CUTOFF,
            instrument_version=sc.instrument_version,
        )
    if payload.instrument == "panas10":
        # Thompson 2007 I-PANAS-SF — 10-item cross-cultural PANAS
        # short form.  Fills the platform's **positive / negative
        # affect dimension gap** — every prior instrument targets
        # a specific syndrome or construct; none measure the
        # orthogonal PA / NA affect dimensions that the tripartite
        # model (Clark & Watson 1991 JAP; Watson, Clark & Carey
        # 1988 JAP) identifies as the core discriminator between
        # anxiety and depression.  PA deficit is depression-
        # specific (anhedonia, diminished engagement); NA
        # elevation is the shared general-distress dimension.
        # Clinical load-bearing use of the PA/NA split:
        #   - Intervention matching:
        #       low PA + high NA (classic depression) →
        #         behavioral activation (Martell 2010; Dimidjian
        #         2006) targeting the PA deficit via scheduled
        #         positive-reinforcement contact;
        #       normal PA + high NA (anxiety-dominant) →
        #         unified protocol (Barlow 2011) / ACT (Hayes
        #         2012) targeting NA regulation without PA
        #         manipulation;
        #       low PA + normal NA (anhedonia-dominant without
        #         anxious distress) →
        #         positive-affect treatment (Craske 2019 reward-
        #         sensitivity training).
        #   - Differential diagnosis: PHQ-9 positive WITHOUT PANAS
        #     PA deficit suggests PHQ-9 positivity is being
        #     driven by somatic items (sleep / appetite / fatigue)
        #     rather than core anhedonic depression — worth
        #     investigating medical contributors (Pressman &
        #     Cohen 2005).
        #   - Trajectory monitoring: Watson 1988 §3 reported PA
        #     is more state-sensitive than NA — PA responds to
        #     intervention faster; PA change-signal is the
        #     earlier detector of treatment response.
        # **Novel wire envelope** — PANAS-10 is the platform's
        # FIRST bidirectional-subscales instrument with no
        # canonical aggregate total.  Watson 1988 and Tellegen
        # 1999 established PA and NA as ORTHOGONAL affect-
        # circumplex dimensions; summing them would collapse
        # two independent clinical signals into one (a category
        # error that contradicts the factor structure the
        # instrument was engineered to provide).  The platform
        # resolves this via:
        #   - total = pa_sum (5-25).  Not a composite.  PA is
        #     chosen as the primary per tripartite-model
        #     intervention-matching priority — PA deficit is
        #     depression-specific; NA elevation is non-specific
        #     distress (Clark & Watson 1991; Craske 2019).
        #   - subscales = {"positive_affect": pa_sum,
        #                  "negative_affect": na_sum} preserves
        #     both orthogonal dimensions.  Clinicians MUST read
        #     both subscales via the subscales dict — the total
        #     alone is insufficient to distinguish depression-,
        #     anxiety-, anhedonia-, or flourishing-dominant
        #     profiles (see scoring/panas10.py module docstring
        #     for worked examples).
        #   - severity = "continuous" sentinel — Thompson 2007
        #     did not publish banded severity cutpoints;
        #     Crawford & Henry 2004 UK norms (PA 32.1 ±6.8, NA
        #     14.8 ±5.3 on 10-50 scale; 16.05 ±3.4 and 7.40
        #     ±2.65 on 5-25 scale) are descriptive distributions,
        #     not clinical bands.  Hand-rolling bands violates
        #     CLAUDE.md.  Clinicians compare against the
        #     normative distribution via RCI / percentile
        #     machinery downstream.
        # No T3 — PANAS-10 probes affect dimensions, not
        # suicidality.  Item 1 "upset" is general negative
        # affect per Watson 1988 item derivation, NOT suicidal
        # ideation.  Acute-risk screening stays on C-SSRS /
        # PHQ-9 item 9.  See ``scoring/panas10.py``.
        p = score_panas10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="panas10",
            total=p.pa_sum,
            severity="continuous",
            requires_t3=False,
            subscales={
                PANAS10_SUBSCALES[0]: p.pa_sum,
                PANAS10_SUBSCALES[1]: p.na_sum,
            },
            instrument_version=p.instrument_version,
        )
    if payload.instrument == "rses":
        # Rosenberg 1965 Self-Esteem Scale — 10-item 0-3 Likert
        # global self-esteem instrument.  The most widely-used
        # psychological instrument (>100k citations per Google
        # Scholar).  Morris Rosenberg's *Society and the
        # Adolescent Self-Image* (Princeton University Press
        # 1965) established the unidimensional self-esteem
        # construct; Gray-Little 1997 IRT meta-analysis
        # confirmed unidimensional factor structure; Schmitt &
        # Allik 2005 cross-national n = 16,998 confirmed
        # factorial invariance across 53 nations.
        # Fills the platform's **self-concept dimension gap** —
        # every prior instrument targets a syndrome, a craving /
        # impulse construct, an affect dimension, a regulatory
        # construct, or a resilience / recovery construct.  None
        # measure GLOBAL SELF-ESTEEM, the evaluative attitude
        # one holds toward oneself.
        # Clinical load-bearing for relapse prevention via the
        # **abstinence-violation effect** (AVE; Marlatt 1985
        # Relapse Prevention pp. 37-44).  A single lapse triggers
        # an internal / stable / global attributional cascade
        # with low self-esteem as both substrate and outcome —
        # a self-reinforcing cycle that RSES measures directly.
        # Intervention matching:
        #   - low RSES -> self-compassion-based work (Neff
        #     2003; Gilbert 2010 CFT) or self-efficacy-
        #     strengthening (Bandura 1977; Witkiewitz 2007);
        #   - high RSES with persistent SUD -> possibly
        #     narcissistic / externalizing profile suggesting
        #     DBT-adapted framing (Linehan 2015).
        # Trajectory monitoring: self-esteem is state-sensitive
        # (Kernis 2005) and responds to intervention within
        # weeks.  RSES + Jacobson-Truax RCI gives an early-
        # signal measure of whether intervention is landing or
        # AVE is dominant.
        # Reverse-keying: items 2, 5, 6, 8, 9 are negatively
        # worded; post-flip = 3 - raw.  Inherits the PGSI / BRS
        # / TAS-20 / PSWQ / LOT-R reverse-keying idiom.  Total =
        # sum of post-flip, 0-30.  Higher-is-better direction.
        # No bands — Rosenberg 1965 did not publish clinical
        # cutpoints; Gray-Little 1997 and Schmitt & Allik 2005
        # cross-national means are descriptive, not clinical.
        # severity = "continuous"; trajectory layer applies RCI
        # on total directly.
        # No subscales — Gray-Little 1997 IRT confirmed
        # unidimensional.  Tomas 1999 / Marsh 1996 two-factor
        # proposals are method-artifact (positive-negative
        # wording bias), not substantive subscales.
        # No T3 — RSES measures self-esteem, not suicidality.
        # Item 9 "All in all, I am inclined to feel that I am a
        # failure" is a self-concept item per Rosenberg 1965
        # derivation, NOT ideation.  Item 6 "I certainly feel
        # useless at times" is similarly a self-concept item.
        # Acute-risk screening stays on C-SSRS / PHQ-9 item 9.
        # A clinician reviewing a low RSES should pair it with
        # a safety screen, but the RSES itself does not carry
        # an acute-risk signal.  See ``scoring/rses.py``.
        r = score_rses(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="rses",
            total=r.total,
            severity=r.severity,
            requires_t3=False,
            instrument_version=r.instrument_version,
        )
    if payload.instrument == "ffmq15":
        # Five-Facet Mindfulness Questionnaire short form —
        # 15-item 1-5 Likert instrument derived by Gu, Strauss,
        # Crane, Barnhofer, Karl, Cavanagh & Kuyken (2016
        # Psychological Assessment 28(7):791-802) via IRT
        # analysis (n = 2,876) from the 39-item FFMQ (Baer,
        # Smith, Hopkins, Krietemeyer & Toney 2006 Assessment
        # 13(1):27-45).  The canonical five-factor mindfulness
        # measure — observing, describing, acting with
        # awareness, non-judging of inner experience, non-
        # reactivity to inner experience (3 items each).
        # Extends platform's MAAS (Brown & Ryan 2003) single-
        # factor mindfulness measure with facet-level
        # decomposition — MAAS gives ONE mindfulness total
        # (present-moment awareness), FFMQ-15 gives five
        # independently-interpretable sub-dimensions.
        # Clinical load-bearing for the Discipline OS
        # intervention-matching engine — each facet maps to
        # a distinct intervention modality:
        #   - low observing -> body-scan / sensory grounding
        #     (Kabat-Zinn 1990 §2 MBSR);
        #   - low describing -> emotion-labeling / affect
        #     literacy (Kircanski 2012 linguistically-
        #     scaffolded exposure); describing deficit
        #     correlates with TAS-20 alexithymia (r = -0.59
        #     per Baer 2006);
        #   - low acting-with-awareness -> Mindfulness-Based
        #     Relapse Prevention urge-surfing (Bowen 2014
        #     §3.2) — the facet MOST DIRECTLY implicated in
        #     cue-reactivity and automatic-pilot relapse;
        #   - low non-judging -> self-compassion (Neff 2011;
        #     Gilbert 2010 CFT) — same lever as low RSES,
        #     non-judging deficit is Marlatt 1985 AVE-cascade
        #     precursor;
        #   - low non-reactivity -> acceptance / defusion
        #     (Hayes 2012 ACT; Segal 2013 MBCT).
        # This means FFMQ-15 is the FIRST PLATFORM
        # INSTRUMENT whose subscales directly map to five
        # independent intervention tools.  PANAS-10 (Sprint
        # 65) introduced the bidirectional-subscales envelope
        # (PA + NA).  FFMQ-15 extends to **penta-subscales**
        # — the first five-subscale instrument on the
        # platform.
        # Reverse-keying: 7 positions (6 describing-reverse,
        # 7-9 acting all-reverse, 10-12 non-judging all-
        # reverse).  Observing (1-3) and non-reactivity
        # (13-15) entirely positive.  Post-flip = 6 - raw.
        # Total = sum of post-flip, 15-75.  Higher-is-better
        # direction.  No bands — Baer 2006 / Gu 2016 did not
        # publish cutpoints; severity = "continuous";
        # trajectory layer applies Jacobson-Truax RCI per
        # facet.
        # No T3 — no item probes suicidality.  Non-judging
        # items mention "my emotions are bad" but are self-
        # evaluative NOT ideation (AVE-substrate content, not
        # acute risk).  See ``scoring/ffmq15.py``.
        f = score_ffmq15(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="ffmq15",
            total=f.total,
            severity=f.severity,
            requires_t3=False,
            subscales={
                FFMQ15_SUBSCALES[0]: f.observing_sum,
                FFMQ15_SUBSCALES[1]: f.describing_sum,
                FFMQ15_SUBSCALES[2]: f.acting_sum,
                FFMQ15_SUBSCALES[3]: f.nonjudging_sum,
                FFMQ15_SUBSCALES[4]: f.nonreactivity_sum,
            },
            instrument_version=f.instrument_version,
        )
    if payload.instrument == "stai6":
        # STAI-6 — 6-item brief state-anxiety scale derived by
        # Marteau & Bekker (British Journal of Clinical
        # Psychology 1992, 31:301-306) from the full 20-item
        # State-Trait Anxiety Inventory (Spielberger 1983 Form
        # Y).  n = 200 pre-surgical patients; r = 0.94 with the
        # full STAI-S established the equivalence.  Items 1
        # (calm), 4 (relaxed), 5 (content) are positively
        # worded and reverse-keyed at scoring time; items 2
        # (tense), 3 (upset), 6 (worried) are negatively
        # worded and pass through raw.  Post-flip = 5 - raw
        # at reverse positions; total is the 6-24 sum of
        # post-flip values with HIGHER = more state-anxious
        # (lower-is-better direction, uniform with PHQ-9 /
        # GAD-7 / AUDIT / PSS-10 / PGSI / SHAPS; OPPOSITE of
        # WHO-5 / BRS / RSES / FFMQ-15 / MAAS / LOT-R).  The
        # instrument fills the platform's **state-vs-trait
        # anxiety distinction gap** — every prior anxiety
        # instrument on the platform (GAD-7's 14-day window,
        # GAD-2 same, OASIS's 7-day window, AAQ-II and PSWQ
        # dispositional) measures trait-ish anxiety, whereas
        # STAI-6 measures MOMENTARY state anxiety anchored to
        # the present ("how you feel right now, at this
        # moment") per Spielberger's (1966, 1983) seminal
        # state / trait theoretical distinction.  Three
        # clinical use cases drive the measurement:
        #   - Pre/post intervention-session within-session
        #     effect measurement.  A behavioral-activation /
        #     exposure session is expected to REDUCE state
        #     anxiety immediately post-session; GAD-7 cannot
        #     resolve this signal (its 14-day window averages
        #     across the session).  STAI-6 pre/post delta is
        #     the canonical within-session efficacy metric
        #     for the Discipline OS intervention engine.
        #   - Trigger-vs-baseline cue reactivity.  Baseline
        #     STAI-6 vs post-trigger STAI-6 discriminates
        #     reactive-profile patients (exposure-therapy
        #     targets per Craske 2014) from chronically-
        #     anxious patients (trait-anxiety protocol
        #     targets per Dugas 2010).
        #   - Real-time relapse-risk gating.  Marlatt 1985
        #     pp. 137-142 identified negative emotional
        #     states including elevated state anxiety as the
        #     MOST COMMON proximal relapse determinant (137-
        #     relapse sample).  A STAI-6 spike in the hour
        #     before a reported craving episode feeds the
        #     intervention-bandit policy as a predictive
        #     signal.
        # No scaled score — Marteau 1992 recommended (total ×
        # 20) / 6 to map to the full STAI-S 20-80 range;
        # platform does not emit because: (1) non-integer for
        # most inputs, clashes with CLAUDE.md Latin-digits
        # rendering; (2) RCI at the trajectory layer works
        # on the raw total directly; (3) Kvaal 2005 ≥ 40
        # scaled cutoff is secondary-literature derivation
        # (validated against HADS), not a primary-source
        # anchor.  Per CLAUDE.md "no hand-rolled severity
        # thresholds" rule, severity = "continuous" and
        # clinical-significance lives at the trajectory
        # layer via Jacobson-Truax RCI.  No T3 gating — no
        # item probes suicidality; "upset" (item 3) is
        # general distress, NOT ideation; acute-risk
        # screening stays on C-SSRS / PHQ-9 item 9.  The
        # envelope is banded+total (no subscales, no
        # scaled_score, no positive_screen) — same shape as
        # OASIS / K10 / RSES / PANAS-10-total.  The 3-
        # positive / 3-negative symmetric reverse-keying is
        # Marsh 1996's canonical acquiescence-bias control
        # design; every constant vector lands at the midpoint
        # total of 15 (stronger than FFMQ-15's 8/7 asymmetric
        # differ-by-4 property).  See ``scoring/stai6.py``.
        s = score_stai6(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="stai6",
            total=s.total,
            severity=s.severity,
            requires_t3=False,
            instrument_version=s.instrument_version,
        )
    if payload.instrument == "fneb":
        # FNE-B — 12-item Brief Fear of Negative Evaluation scale
        # (Leary, Personality and Social Psychology Bulletin 1983,
        # 9(3):371-375).  Derived from Watson & Friend's (1969)
        # original 30-item FNE; Leary's 12-item brief form yielded
        # r = 0.96 with the full FNE on n = 164 undergraduates and
        # carries through the same psychometric properties at
        # one-third the response burden.  Items 2 ("unconcerned
        # about others' opinions"), 4 ("rarely worry about seeming
        # foolish"), 7 ("unconcerned even if I know I'm disapproved"),
        # 10 ("not worried about what others say") are positively
        # worded and reverse-keyed at scoring time; the remaining
        # 8 items are negatively worded and pass through raw.
        # Post-flip = 6 - raw at reverse positions; total is the
        # 12-60 sum of post-flip values with HIGHER = more fear of
        # negative evaluation (lower-is-better direction, uniform
        # with PHQ-9 / GAD-7 / PSS-10 / STAI-6; OPPOSITE of
        # WHO-5 / BRS / RSES / FFMQ-15 / MAAS / LOT-R).
        #
        # The instrument fills the platform's **social-evaluative
        # anxiety gap**: prior anxiety coverage targets generalized
        # worry (GAD-7, PSWQ), acute state-anxiety (STAI-6, OASIS),
        # or experiential avoidance (AAQ-II), but none capture the
        # fear-of-judgement construct that drives social-situation
        # avoidance, public-speaking paralysis, and the core
        # phenomenology of social anxiety disorder (Heimberg 1995
        # Cognitive-Behavioral Group Therapy for Social Phobia
        # uses FNE as a primary pre/post outcome; Hofmann 2008
        # meta-analysis identifies FNE reduction as the
        # mechanism of change in SAD CBT).
        #
        # Three addiction-relevant clinical use cases drive the
        # measurement on this platform:
        #   - Socially-cued relapse detection.  Marlatt 1985
        #     Table 4.1 identifies social-pressure / inter-
        #     personal-conflict as a top proximal relapse
        #     determinant (second to negative emotional
        #     states covered by STAI-6).  A user with high
        #     FNE-B entering a social drinking context is at
        #     elevated relapse risk on a mechanism orthogonal
        #     to craving intensity itself (PACS) — the bandit
        #     policy surfaces avoidance-coaching or escape-
        #     planning tool variants rather than craving-
        #     tolerance variants.
        #   - User-profile differentiation for treatment
        #     targeting.  High FNE-B + elevated AUDIT /
        #     DUDIT identifies the "alcohol-as-social-
        #     lubrication" user, for whom exposure-based
        #     social-skills-training is indicated; low FNE-B
        #     + elevated PSS-10 / STAI-6 identifies the
        #     "negative-affect-self-medication" user, for
        #     whom DBT distress-tolerance / affect-regulation
        #     is indicated.  These are DISTINCT intervention
        #     pathways confused by craving-intensity alone.
        #   - Digital-avoidance substitution detection.  High
        #     FNE-B co-occurring with problematic internet /
        #     gaming use is the Caplan 2003 compensatory-
        #     internet-use signature — social-anxiety-driven
        #     escape into online worlds rather than face-to-
        #     face engagement.  Intervention targeting
        #     substitutes in-vivo exposure hierarchies for
        #     online-only coping.
        #
        # No bands — Leary 1983 did not publish severity cut-
        # points; Collins 2005 n = 234 college sample reports
        # mean 35.7 SD 8.1 with ≥ 49 noted as "clinical range"
        # but this is a secondary-literature post-hoc
        # derivation and not pinnable per CLAUDE.md "no hand-
        # rolled severity thresholds" rule.  severity =
        # "continuous" sentinel; clinical-significance lives at
        # the trajectory layer via Jacobson-Truax RCI on the
        # raw 12-60 total.  No T3 gating — no item probes
        # suicidality; "afraid of making mistakes" (item 8) is
        # evaluative-apprehension, NOT ideation; acute-risk
        # screening stays on C-SSRS / PHQ-9 item 9.  The
        # envelope is banded+total (no subscales, no
        # scaled_score, no positive_screen) — same shape as
        # RSES / PANAS-10-total / STAI-6.  Acquiescence-bias
        # signature: 8 straight + 4 reverse is ASYMMETRIC, so
        # any all-v constant vector yields total = 4v + 24 —
        # all-raw-1 yields 28 and all-raw-5 yields 44
        # (separation of 16, the largest on the platform; a
        # random endpoint-only responder shifts the score 33%
        # of the 12-60 range).  The linear formula 4v + 24 is
        # pinned in the test suite so regression is immediate
        # if reverse-keying positions drift.  See
        # ``scoring/fneb.py``.
        f = score_fneb(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="fneb",
            total=f.total,
            severity=f.severity,
            requires_t3=False,
            instrument_version=f.instrument_version,
        )
    if payload.instrument == "ucla3":
        # UCLA-3 — 3-item brief loneliness scale derived by
        # Hughes, Waite, Hawkley & Cacioppo (Research on Aging
        # 2004, 26(6):655-672) from Russell's 1980 full 20-item
        # UCLA Loneliness Scale (Revised).  Validated in the
        # Health and Retirement Study cohort (n = 2,101) with
        # r = 0.82 against the full UCLA-R-20 — preserves the
        # core social-isolation construct at one-seventh the
        # response burden.  Items 1 (lack companionship), 2
        # (feel left out), 3 (feel isolated from others) are
        # ALL negatively worded; ZERO reverse-keyed positions,
        # so raw sum = scored total.  This is the only
        # multi-item platform instrument with no reverse-keying
        # at all — Hughes 2004 deliberately omits Marsh 1996
        # balanced-wording acquiescence-bias control because
        # adding it would invalidate the r = 0.82 UCLA-R-20
        # equivalence.  The trade-off is documented: UCLA-3
        # carries the highest acquiescence-bias exposure on
        # the platform (constant-v vectors yield total = 3v,
        # so endpoint-only responders shift the score the full
        # 75% of the 3-9 range).
        #
        # The instrument fills the platform's **loneliness /
        # perceived-isolation gap**, which is clinically
        # DISTINCT from the fear-of-judgement construct FNE-B
        # measures.  A user can be HIGH UCLA-3 with LOW FNE-B
        # (a recently-widowed retiree has intact social skills
        # and no evaluation anxiety — the network simply does
        # not exist) or LOW UCLA-3 with HIGH FNE-B (a socially-
        # anxious adolescent may have abundant peer contact
        # while reporting severe fear-of-judgement).  The pair
        # differentiates CAUSE of social under-engagement and
        # therefore differentiates intervention targeting:
        #   - High FNE-B, low UCLA-3 → exposure + social-skills
        #     training (Heimberg 1995 CBGT protocol).
        #   - Low FNE-B, high UCLA-3 → structural social-contact
        #     building (befriending, peer-support groups).
        #   - Both elevated → combined protocol, network
        #     absent AND avoidance of rebuilding it.
        #
        # Four addiction-relevant clinical use cases drive the
        # measurement on this platform:
        #   - Widowhood / bereavement relapse risk.  Keyes 2012
        #     documented a 2.4× elevation in alcohol-use-
        #     disorder incidence in the 2-year post-widowhood
        #     window, mediated by loneliness.  High UCLA-3 in
        #     a user with an alcohol-use history flags a
        #     contextual relapse risk that craving-intensity
        #     measures (PACS, Craving VAS) do not surface.
        #   - Retirement-trigger relapse detection.  Satre
        #     2004 identified structural social loss at
        #     retirement as a proximal trigger; UCLA-3
        #     captures the onset of the structural change
        #     while STAI-6 / GAD-7 may not elevate if the
        #     user does not subjectively interpret the
        #     change as threatening.
        #   - Marlatt 1985 negative-emotional-states proximal
        #     relapse precipitant (pp. 137-142; 35% of the
        #     137-relapse sample).  Loneliness is a sub-type
        #     within this category alongside depression
        #     (PHQ-9) and anhedonia (SHAPS); UCLA-3 captures
        #     the socially-driven sub-type specifically.
        #   - Longitudinal mortality-risk stratification.
        #     Holt-Lunstad 2010 meta-analysis (k = 148, n ≈
        #     308,849) showed loneliness independently predicts
        #     mortality with HR ≈ 1.26 — effect size comparable
        #     to smoking or obesity.  Improving UCLA-3 over
        #     6-month telemetry windows is a clinically-
        #     meaningful outcome independent of relapse-event
        #     count.
        #
        # No bands — Hughes 2004 published no primary-source
        # cutpoints; Steptoe 2013 tercile splits (3 / 4-5 /
        # 6-9) are HRS-sample descriptive derivations and
        # excluded per CLAUDE.md "no hand-rolled severity
        # thresholds" rule.  severity = "continuous"; Jacobson-
        # Truax RCI at the trajectory layer supplies clinical-
        # significance judgement on the raw 3-9 total.
        #
        # No T3 gating — no item probes suicidality; "feel
        # isolated from others" (item 3) is a subjective-
        # connection construct, NOT ideation.  Clinical note:
        # loneliness IS an established suicide risk factor
        # (Calati 2019 meta-analysis, k = 40) — the platform
        # surfaces high UCLA-3 to the clinician UI as C-SSRS-
        # follow-up context, but the assessment itself does
        # not set requires_t3.  Active-risk screening stays on
        # C-SSRS / PHQ-9 item 9.
        #
        # Envelope: banded+total (no subscales, scaled_score,
        # positive_screen, cutoff_used, triggering_items) —
        # same shape as RSES / STAI-6 / FNE-B / PANAS-10-total.
        # See ``scoring/ucla3.py``.
        u = score_ucla3(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="ucla3",
            total=u.total,
            severity=u.severity,
            requires_t3=False,
            instrument_version=u.instrument_version,
        )
    if payload.instrument == "cius":
        # CIUS — 14-item Compulsive Internet Use Scale (Meerkerk,
        # Van Den Eijnden, Vermulst & Garretsen, CyberPsychology
        # & Behavior 2009, 12(1):1-6).  Dutch adolescent / adult
        # derivation sample (n = 447 derivation + n = 16,925
        # cross-validation); Cronbach α = 0.89; single-factor CFA
        # confirmed by Guertler 2014 on a German n = 2,512 sample.
        # All 14 items are negatively worded (compulsive-use
        # symptom descriptions) — ZERO reverse-keyed positions,
        # so raw sum = scored total.  Total range 0-56.
        #
        # Response scale is Meerkerk 2009's ORIGINAL 0-based 5-
        # point Likert: 0 ("Never"), 1 ("Seldom"), 2 ("Sometimes"),
        # 3 ("Often"), 4 ("Very often").  This is deliberate —
        # Meerkerk 2009 scored "Never" as semantically ZERO
        # compulsivity (not just "low"), and the r = 0.70+
        # convergent validity with Young 1998 IAT is anchored on
        # the 0-4 scale.  CIUS is the first platform instrument
        # with a valid 0-response, which creates a specific
        # bool-coercion concern (see §validation below).
        #
        # The instrument fills the platform's **behavioral-
        # addiction substrate / digital compensation gap**.
        # Three addiction-relevant use cases drive the measurement:
        #   - Caplan 2003 compensatory-internet-use detection.
        #     Caplan's preference-for-online-social-interaction
        #     model predicts that high FNE-B (social-evaluation
        #     anxiety) or high UCLA-3 (loneliness) drives
        #     problematic internet use as an affect-regulation
        #     substitute.  The triad FNE-B + UCLA-3 + CIUS lets
        #     the platform differentiate:
        #       - High FNE-B + low UCLA-3 + high CIUS →
        #         socially-avoidant digital compensation
        #         (treatment: in-vivo exposure + use limits,
        #         NOT more online socialization).
        #       - Low FNE-B + high UCLA-3 + high CIUS →
        #         isolation-compensating digital substitution
        #         (treatment: structural social-contact
        #         building + use limits).
        #       - High FNE-B + high UCLA-3 + high CIUS →
        #         combined protocol; digital compensation is
        #         doing both jobs.
        #   - Cross-addiction relapse-risk detection.  Koob
        #     2005 allostatic-reward-deficiency theory predicts
        #     that abstinence from a primary addictive substrate
        #     often produces compensatory engagement with a
        #     secondary behavioral substrate.  For a recovering
        #     alcohol-use-disorder user, a rising CIUS
        #     trajectory over 3-6 months is a canonical early-
        #     warning signal of relapse pressure on the primary
        #     substrate — the brain is finding alternative
        #     allostatic load rather than resolving it.
        #   - ICD-11 / DSM-5 behavioral-addiction overlap.
        #     ICD-11 codes Gaming Disorder (6C51) under
        #     "Disorders Due to Addictive Behaviours"; DSM-5
        #     Section III lists Internet Gaming Disorder for
        #     further study.  CIUS captures the broader
        #     internet-as-substrate construct (not gaming-
        #     specific) for clinical-completeness surfacing
        #     alongside AUDIT / DAST-10 / DUDIT / PGSI in the
        #     substance-use panel.
        #
        # §validation: CIUS is the FIRST platform instrument
        # where ``0`` is a valid response value.  Pydantic
        # ``list[int]`` coerces JSON ``false → 0`` which is now
        # in range, so the scorer's bool rejection is LOAD-
        # BEARING: without it, a serialization bug would silently
        # score ``False`` responses as "never" (semantic "zero
        # compulsivity") rather than raising.  The scorer runs
        # the ``isinstance(value, bool)`` check BEFORE the range
        # check precisely for this reason, and tests pin the
        # distinction explicitly.
        #
        # No bands — Meerkerk 2009 derivation paper did not
        # publish primary-source cutpoints; Guertler 2014
        # proposed >= 21 as "at risk" and >= 28 as "high risk"
        # but these are later-literature secondary derivations,
        # NOT primary-source anchors.  Per CLAUDE.md "no hand-
        # rolled severity thresholds" rule, severity =
        # "continuous" and clinical-significance lives at the
        # trajectory layer via Jacobson-Truax RCI on the raw
        # 0-56 total.  No T3 gating — no item probes
        # suicidality; "feel restless, frustrated, or irritated
        # when cannot use the Internet" (item 14) is a
        # Griffiths 1998 withdrawal-symptom construct, NOT
        # ideation; active-risk screening stays on C-SSRS /
        # PHQ-9 item 9.  Envelope: banded+total (no subscales,
        # scaled_score, positive_screen, cutoff_used,
        # triggering_items) — same shape as RSES / STAI-6 /
        # FNE-B / UCLA-3.  See ``scoring/cius.py``.
        c = score_cius(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="cius",
            total=c.total,
            severity=c.severity,
            requires_t3=False,
            instrument_version=c.instrument_version,
        )
    if payload.instrument == "swls":
        # SWLS — 5-item Satisfaction With Life Scale (Diener,
        # Emmons, Larsen & Griffin, Journal of Personality
        # Assessment 1985, 49(1):71-75).  Most widely-used self-
        # report instrument for the **cognitive-judgmental
        # component of subjective wellbeing**.  Deliberately
        # constructed by Diener 1985 to be orthogonal to
        # affective-wellbeing measures — asks the respondent to
        # evaluate their life against their own IDEAL, a global
        # judgment integrating across domains (work, relationships,
        # leisure, health) and across time rather than capturing
        # transient positive or negative mood.  Pavot & Diener 1993
        # (Psychological Assessment 5(2):164-172) published the
        # canonical review with interpretive bands; Pavot & Diener
        # 2008 (Journal of Positive Psychology 3(2):137-152) is the
        # 25-year retrospective confirming α range 0.79-0.89,
        # test-retest r = 0.54 (4 years) / 0.82 (2 months), and
        # the normative SD ≈ 6.6 that anchors the Jacobson-Truax
        # RCI at the trajectory layer.
        #
        # Fills a cognitive-vs-affective gap in the platform's
        # wellbeing-measurement roster:
        # - WHO-5 measures AFFECTIVE wellbeing (last-two-weeks
        #   mood: cheerful / relaxed / active / rested / interested).
        # - LOT-R measures DISPOSITIONAL OPTIMISM (trait-level
        #   expectations about future outcomes).
        # - BRS measures BOUNCE-BACK RESILIENCE (recovery capacity
        #   after setbacks).
        # - SWLS measures COGNITIVE-JUDGMENTAL GLOBAL LIFE
        #   EVALUATION ("does my life, overall, match my ideal?").
        #   Diener 1985 §1 explicitly framed this as the cognitive
        #   counterpart to affective wellbeing: "A respondent can
        #   have a high level of positive affect and yet be
        #   dissatisfied with life as a whole because of specific
        #   unfulfilled areas."
        #
        # For relapse-prevention, low SWLS in early recovery is a
        # documented DELAYED-RELAPSE signal.  Moos & Moos 2005
        # (Addiction 100(8):1121-1130) found n = 628 AUD-cohort
        # 16-year follow-up that life-satisfaction at 1-3 years
        # post-treatment predicted sustained remission at year 16
        # more strongly than affective measures.  The mechanism:
        # clients with improved affective wellbeing but persistent
        # cognitive dissatisfaction ("things are better, but this
        # isn't the life I want") have an ambient motivational
        # gradient toward resuming the substance / behavior that
        # provided the closest proxy to their ideal, even after
        # post-acute-withdrawal resolves.
        #
        # Profile pairings:
        # - SWLS-low + WHO-5-high ("wrong-life" profile) — ACT
        #   values-clarification indication (Hayes 2006).
        # - SWLS-high + WHO-5-low ("right life but poor mood") —
        #   acute-affective regulation indication.
        # - SWLS-low + LOT-R-low (hopelessness-suicide-risk
        #   parallel, Beck 1985) — clinician-UI prompts C-SSRS
        #   follow-up but the SWLS assessment itself MUST NOT set
        #   T3.
        # - SWLS-low + BRS-low ("stuck-stress" pattern, Smith
        #   2008) — resilience-skills training (Reivich 2002 Penn
        #   Resiliency Program) precedes life-evaluation work.
        #
        # Scoring: 5 items, 1-7 Likert (1 = Strongly Disagree,
        # 7 = Strongly Agree), NO reverse keying (all five items
        # positively worded in the "higher = more satisfied"
        # direction — Diener 1985 Table 1 confirmed and Pavot 1993
        # retained through subsequent validations).  Total =
        # straight sum, range 5-35.  HIGHER = more satisfied.
        # Uniform with WHO-5 / LOT-R / BRS / MAAS / RSES / PANAS-10
        # PA / CD-RISC-10 / FFMQ-15 "higher-is-better" direction.
        #
        # Severity = "continuous".  Pavot & Diener 1993 seven-band
        # interpretive guidelines (Extremely satisfied 31-35,
        # Satisfied 26-30, Slightly satisfied 21-25, Neutral 20,
        # Slightly dissatisfied 15-19, Dissatisfied 10-14,
        # Extremely dissatisfied 5-9) stay at the CLINICIAN-UI
        # RENDERER LAYER, not in the envelope band — consistent
        # with UCLA-3 / CIUS "continuous measure with published
        # interpretive guidelines" platform posture and CLAUDE.md
        # non-negotiable #9 ("Don't hand-roll severity thresholds").
        # Pavot 1993 explicitly called these "overall interpretive
        # guidelines" rather than diagnostic thresholds, so
        # collapsing them into envelope bands would over-commit
        # the clinical-decision scaffolding.  The "Neutral" band
        # at exactly 20 is especially resistant to envelope
        # dichotomization — any cutoff choice (≤20 vs <20 vs ≤19
        # vs <21) would be hand-rolled against the primary-source
        # guidance.
        #
        # Acquiescence signature: linear total = 5v for any all-v
        # constant vector, endpoint-gap = 30 (full 5-35 range,
        # 100% of range — matches UCLA-3 / CIUS relative endpoint-
        # exposure).  Diener 1985 / Pavot 1993 treated the all-
        # positive-wording as acceptable because α ≈ 0.87 indicated
        # coherent-interpretation dominance over acquiescence bias
        # in practice (same rationale as CIUS, SHAPS).
        #
        # T3 posture — NO item probes suicidality.  Item 5 ("would
        # change almost nothing") is a counterfactual life-
        # evaluation probe, NOT a self-harm or ideation probe.
        # Acute-risk screening stays on C-SSRS / PHQ-9 item 9.
        # Low SWLS paired with low LOT-R (Beck 1985 hopelessness-
        # suicide-risk profile) surfaces at the clinician-UI layer
        # as a C-SSRS follow-up prompt, NOT as a scorer-layer T3
        # flag — same posture as UCLA-3 with Calati 2019 loneliness
        # / suicide-risk association.
        #
        # Envelope: banded+total (no subscales — unidimensional
        # factor structure per Diener 1985 / Pavot 1993 eigenvalue
        # ratio 2.9:0.6; no scaled_score, positive_screen,
        # cutoff_used, triggering_items — same shape as UCLA-3 /
        # CIUS / STAI-6 / FNE-B).  ``items`` field = raw input
        # (identity under zero-reverse-keying).  See
        # ``scoring/swls.py``.
        s = score_swls(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="swls",
            total=s.total,
            severity=s.severity,
            requires_t3=False,
            instrument_version=s.instrument_version,
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
        ErqInvalid,
        ScsSfInvalid,
        Rrs10Invalid,
        MaasInvalid,
        ShapsInvalid,
        AcesInvalid,
        PgsiInvalid,
        BrsInvalid,
        ScoffInvalid,
        Panas10Invalid,
        RsesInvalid,
        Ffmq15Invalid,
        Stai6Invalid,
        FnebInvalid,
        Ucla3Invalid,
        CiusInvalid,
        SwlsInvalid,
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
