# Psychometric System — Discipline OS

## 1. Purpose

The psychometric system administers, scores, stores, and longitudinally tracks **validated clinical assessments**. It exists for three reasons:

1. **Clinical rigor** — use instruments that clinicians and regulators recognize, with published psychometric properties (reliability, validity, normative data).
2. **Longitudinal signal** — a user's score trajectory on PHQ-9, GAD-7, AUDIT, etc., is a stronger evidence base for efficacy than engagement metrics.
3. **Safety surveillance** — scales include items (PHQ-9 item 9, SAD-PERSONS) that flag acute risk and feed the T4 human-handoff pipeline.

This is not a "mood quiz" layer. These are licensed, validated instruments treated with the same respect a clinic would give them — with proper licensing, scoring fidelity, interpretation guardrails, and change-tracking.

---

## 2. Design Principles

1. **Every instrument is versioned + citation-linked.** The exact item wording, scoring rubric, and source publication must be immutable.
2. **Administration is ethical, not gamified.** No streak rewards for completing PHQ-9. Frequency is clinically-grounded, not engagement-driven.
3. **Scoring is always explicit and auditable.** No LLM interpretation. Scoring uses deterministic rule sets validated against the source publication.
4. **Interpretation is bounded.** We surface severity bands + change over time. We never "diagnose."
5. **Safety items escalate immediately.** Any endorsement of suicidal ideation or acute risk item triggers the T4 pathway in real time — not at batch-processing time.
6. **Licensing is respected.** Some instruments (BDI-II, MINI, C-SSRS licensed variants) are not free. We pay, license, and cite.
7. **Clinician-facing outputs match clinical conventions.** PDF summaries use the format clinicians already recognize in their EHRs.
8. **Consent-first for research.** Population-level psychometric datasets exposed to research partners only under explicit opt-in consent + IRB oversight.

---

## 3. Instrument Catalog

### 3.1 Tier A — Required at launch (v1.0)

| # | Instrument | Construct | Items | Scoring | Licensing | Cadence |
|---|-----------|-----------|-------|---------|-----------|---------|
| 1 | **PHQ-9** | Depression severity | 9 | 0–27, bands (0–4 none/1–4 minimal, 5–9 mild, 10–14 moderate, 15–19 moderately severe, 20–27 severe) | Free (Pfizer) | Every 2 weeks (configurable) |
| 2 | **GAD-7** | Generalized anxiety severity | 7 | 0–21, bands | Free (Pfizer) | Every 2 weeks |
| 3 | **AUDIT-C** | Hazardous drinking screen | 3 | 0–12, gender-adjusted cutoffs | Free (WHO) | Monthly for alcohol vertical |
| 4 | **AUDIT** (full) | Alcohol use disorder | 10 | 0–40, bands | Free (WHO) | Quarterly (alcohol vertical) |
| 5 | **DAST-10** | Drug use severity | 10 | 0–10, bands | Free (academic) | Monthly (cannabis + other substance verticals) |
| 6 | **PSS-10** | Perceived stress | 10 | 0–40, reverse-coded 4,5,7,8 | Free (academic) | Monthly |
| 7 | **WHO-5** | Wellbeing | 5 | 0–100 (raw ×4) | Free | Bi-weekly |
| 8 | **Craving VAS** | Momentary craving intensity | 1 | 0–100 | Public domain | EMA (ad-hoc + pre/post intervention) |
| 9 | **Self-Efficacy (DTCQ-8)** | Drug-taking confidence | 8 | 0–100 per-situation | Free (Annis) | Monthly |
| 10 | **URICA short** | Stages of change | 16 | 4 subscale scores | Free | Quarterly |
| 11 | **Readiness Ruler** | Motivation | 1 | 0–10 | Public domain | Weekly |

### 3.2 Tier B — Implemented (v1.5+)

All instruments listed below have scorer modules in `services/api/src/discipline/psychometric/scoring/`,
full scorer unit tests, and HTTP routing tests under `POST /v1/assessments`.

**Mood / Depression**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **PHQ-2** | Depression 2-item screen | 2 | 0–6 | Kroenke 2003 |
| **PHQ-15** | Somatic symptom severity | 15 | 0–30 | Kroenke 2002 |
| **CES-D** | Depressive symptomatology | 20 | 0–60 | Radloff 1977 |
| **DASS-21** | Depression, Anxiety, Stress | 21 | 0–126 | Lovibond 1995 |
| **SHAPS** | Anhedonia | 14 | 0–14 | Snaith 1995 |
| **HADS** | Anxiety + depression (medical) | 14 | 0–42 | Zigmond 1983 |

**Anxiety / Worry / Social**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **GAD-2** | Anxiety 2-item screen | 2 | 0–6 | Kroenke 2001 |
| **OASIS** | Anxiety severity | 5 | 0–20 | Norman 2006 |
| **PSWQ** | Trait worry | 16 | 16–80 | Meyer 1990 |
| **SPIN** | Social phobia | 17 | 0–68 | Connor 2000 |
| **STAI-6** | State anxiety | 6 | 6–24 | Marteau 1992 |
| **FNE-B** | Fear of negative evaluation | 12 | 12–60 | Leary 1983 |

**PTSD / Trauma**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **PCL-5** | PTSD symptom severity | 20 | 0–80 | Weathers 2013 |
| **PC-PTSD-5** | PTSD screen | 5 | 0–5 | Prins 2016 |
| **IES-R** | Trauma symptom distress | 22 | 0–88 | Weiss 1997 |

**Substance use / Behavioral addiction**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **SDS** | Severity of dependence | 5 | 0–15 | Gossop 1995 |
| **CUDIT-R** | Cannabis use disorder | 8 | 0–32 | Adamson 2010 |
| **FTND** | Nicotine dependence | 6 | 0–10 | Heatherton 1991 |
| **CIUS** | Compulsive internet use | 14 | 14–70 | Meerkerk 2009 |
| **IGDS9-SF** | Internet gaming disorder | 9 | 9–45 | Pontes 2015 |
| **SAS-SV** | Smartphone addiction | 10 | 10–60 | Kwon 2013 |
| **PGSI** | Problem gambling | 9 | 0–27 | Ferris 2001 |
| **PACS** | Alcohol craving | 5 | 0–30 | Flannery 1999 |

**Safety / Safety-adjacent**

| Instrument | Construct | Items | Notes | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **C-SSRS** | Suicide ideation + behavior | 6 | T3/T4 trigger | Posner 2011 |
| **SCOFF** | Eating disorder screen | 5 | Binary; ≥2 → referral | Morgan 1999 |
| **ASRS-6** | ADHD screen | 6 | Binary; triage only | Kessler 2005 |
| **MDQ** | Bipolar-spectrum screen | 13 | 3-gate screen | Hirschfeld 2000 |

**Distress / General wellbeing**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **K-10** | Psychological distress | 10 | 10–50 | Kessler 2002 |
| **K-6** | Psychological distress (short) | 6 | 6–30 | Kessler 2003 |
| **CORE-10** | Global clinical distress | 10 | 0–40 | Barkham 2013 |
| **WEMWBS** | Mental wellbeing | 14 | 14–70 | Tennant 2007 |
| **SWLS** | Life satisfaction | 5 | 5–35 | Diener 1985 |

**Resilience / Coping / Self-efficacy**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **CD-RISC-10** | Trait resilience | 10 | 0–40 | Campbell-Sills 2007 |
| **BRS** | Bounce-back resilience | 6 | 6–30 | Smith 2008 |
| **Brief COPE** | Coping strategies | 28 | 28–112 | Carver 1997 |
| **AAQ-II** | Psychological flexibility | 7 | 7–49 | Bond 2011 |
| **GSE** | General self-efficacy | 10 | 10–40 | Schwarzer 1995 |
| **RSES** | Self-esteem | 10 | 10–40 | Rosenberg 1965 |

**Emotion regulation / Mindfulness**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **DERS-16** | Emotion dysregulation | 16 | 16–80 | Bjureberg 2016 |
| **ERQ** | Regulation strategy (reappraisal vs. suppression) | 10 | 10–50 | Gross 2003 |
| **TAS-20** | Alexithymia | 20 | 20–100 | Bagby 1994 |
| **MAAS** | Trait mindful attention | 15 | 15–90 | Brown 2003 |
| **FFMQ-15** | Trait mindfulness (5 facets) | 15 | 15–75 | Gu 2016 |
| **RRS-10** | Ruminative responses | 10 | 10–40 | Treynor 2003 |
| **SCS-SF** | Self-compassion | 12 | 12–60 | Raes 2011 |

**Social / Context**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **MSPSS** | Perceived social support | 12 | 12–84 | Zimet 1988 |
| **UCLA-3** | Loneliness | 3 | 3–9 | Hughes 2004 |
| **ACES** | Adverse childhood experiences | 10 | 0–10 | Felitti 1998 |
| **BIS-11** | Trait impulsivity | 30 | 30–120 | Patton 1995 |
| **PANAS-10** | Positive and negative affect | 10 | 10–50 | Thompson 2007 |

**Functional / Sleep**

| Instrument | Construct | Items | Range | Key Reference |
|-----------|-----------|-------|-------|---------------|
| **WSAS** | Work and social adjustment | 5 | 0–40 | Mundt 2002 |
| **ESS** | Daytime sleepiness | 8 | 0–24 | Johns 1991 |
| **ISI** | Insomnia severity | 7 | 0–28 | Morin 1993 |
| **PCS** | Pain catastrophizing | 13 | 0–52 | Sullivan 1995 |
| **LOT-R** | Dispositional optimism | 10 | 0–24 | Scheier 1994 |

**Planned (not yet implemented)**

| Instrument | Construct | Notes |
|-----------|-----------|-------|
| **ASSIST** | Multi-substance screen | Broader vertical support |
| **PSQI** | Sleep quality | Integrates with wearable sleep data |
| **WHOQOL-BREF** | Quality of life | 26 items |

### 3.3 Tier C — Clinical SKU / trial use (v2+)

| Instrument | Use |
|-----------|-----|
| **MINI** (Mini-International Neuropsychiatric Interview) | Structured diagnostic — clinician-administered only |
| **BDI-II** | Depression — licensed, used in trials where payers require it |
| **HDRS** | Clinician-rated depression — trial contexts |
| **SCID-5** | Structured diagnostic — trial contexts |

### 3.4 Instruments we intentionally do not use

- Proprietary personality tests marketed without validation (e.g., most "engagement science" scales).
- Instruments normed on narrow demographics where we can't justify applicability.
- Instruments that pathologize normal variation without published psychometric validation (validated digital-use scales — CIUS, IGDS9-SF, SAS-SV — are implemented in Tier B above with explicit citation rationale).

---

## 4. Administration Logic

### 4.1 Cadence calculation

A central `PsychometricScheduler` computes, per user per day, which instruments are due. Inputs:

- User's target behaviors (alcohol → AUDIT family; multi-substance → DAST; etc.)
- Instrument cadence config (Tier A table above)
- Last administration timestamp + score
- User preference (throttle or opt out of non-required assessments)
- Clinical escalation (PHQ-9 every 2 weeks becomes every 1 week if user is in "elevated concern" clinical state)

Output: a `DueAssessments[]` list with priority.

### 4.2 Presentation policy

- Never present a psychometric **during a detected urge window or elevated state**. Those are the worst times to ask clinical questions.
- Never present more than **one full instrument per session**. Fatigue biases responses.
- Never require response — users can skip, defer, or opt out.
- **Opt-out is remembered** per instrument, not globally. Users can opt out of PHQ-9 while still using AUDIT.

### 4.3 EMA-mode (1–2 item variants)

For daily micro-assessment:
- PHQ-2 (2 items, <20 seconds) — depression
- GAD-2 (2 items) — anxiety
- Craving VAS (1 item) — momentary craving
- Readiness Ruler (1 item) — weekly motivation

EMA instruments presented via morning/evening check-in; full instruments presented on a separate tap-through path.

### 4.4 Real-world flow examples

**New user, alcohol target, post-onboarding day 1:**
1. Short welcome message.
2. Baseline: AUDIT-C + PHQ-9 + GAD-7 + PSS-10. Split across 2 sessions over first 48h (avoid fatigue).

**Existing user, day 14 elevated state detected, PHQ-9 due:**
- Scheduler skips PHQ-9 today (elevated state). Re-evaluates tomorrow.

**Existing user, AUDIT due (quarterly), current state = calm, morning check-in:**
- AUDIT presented in check-in flow with gentle framing: "Quarterly review — takes about 3 minutes."

---

## 5. Scoring Engine

### 5.1 Deterministic scoring

Each instrument has a pinned **scoring function** in `src/discipline/psychometric/instruments/<name>.py`:

```python
def score_phq9(responses: list[int]) -> PHQ9Result:
    assert len(responses) == 9
    for r in responses:
        assert 0 <= r <= 3
    total = sum(responses)
    severity = classify_phq9_severity(total)
    risk_item = responses[8]   # Item 9 — suicidal ideation
    return PHQ9Result(
        total_score=total,
        severity_band=severity,
        suicide_risk_item_score=risk_item,
        suicide_risk_flag=risk_item >= 1,
    )
```

Every scoring function is:
- Pure (no I/O).
- Unit-tested with the instrument's published scoring examples.
- Version-pinned; changing the function requires clinical advisor sign-off.

### 5.2 Interpretation

Severity bands are returned alongside raw scores. Band boundaries come from the source publication; we never invent bands.

User-facing copy for each band:
- Approved by Clinical QA.
- Does not say "You are X." → says "A score of 14 is in the *moderate* band on PHQ-9. One score isn't a diagnosis. If this feels right, a clinician can help."
- Links to hotline + find-a-provider resources at elevated + severe bands.

### 5.3 Change detection

- Each user has a per-instrument time series.
- Change flagged when:
  - Reliable Change Index (RCI) exceeds instrument-specific threshold.
  - Score crosses a clinically-meaningful band boundary (e.g., PHQ-9 enters "moderately severe").
  - 3 consecutive administrations trend same direction ≥ RCI/2.
- Flags sent to: user (gentle notification), clinician (if linked), pattern engine.

---

## 6. Safety Items (Real-Time T4 Path)

**Critical:** the following items, when endorsed, trigger **immediate** safety routing — not batch processing.

| Instrument | Item | Trigger condition | Action |
|-----------|------|-------------------|--------|
| PHQ-9 | Item 9 (thoughts of self-harm) | Score ≥ 1 | T4 path: show safety message, offer hotline, notify on-call clinical operator if user has linked clinical oversight |
| C-SSRS screening | Items 3–5 | Any endorsement | Immediate T4 + safety plan offer |
| SAD-PERSONS | Cumulative ≥5 | Real-time after submission | T4 |

### 6.1 T4 routing pipeline

```
Response submitted → scoring engine → safety classifier (in-process) → 
if flagged:
  1. Show in-app safety message (compassionate, non-alarming, template-based).
  2. Offer hotline (988, Crisis Text Line, local).
  3. Offer "share with clinician" button if linked.
  4. Emit event to on-call clinical operator queue (30-min outreach SLA if user has consented).
  5. Log audit entry (severity, consent state, actions offered).
  6. Throttle further assessments for 48h; replaced with resource-and-support screen.
```

### 6.2 Safety items never feature-flagged

Same rule as T3 — no experiment or flag can disable or modify the safety routing path.

---

## 7. Clinical Summary Outputs

### 7.1 PDF clinical summary

For linked clinicians, a per-patient PDF report generated on demand:

- Header: patient identifier (pseudonymized), reporting period, generating clinician, generation timestamp.
- Section 1 — Instrument trajectories: line charts for PHQ-9, GAD-7, AUDIT, etc., over time.
- Section 2 — Key events: baseline, notable band crossings, safety flags.
- Section 3 — Engagement + behavioral summary: urges handled, relapses, resilience streak.
- Section 4 — Safety flag log (redacted user content, action log only).
- Footer: methodology reference, instrument citations, disclaimer.

Generated by `reports.ClinicalSummaryBuilder` — deterministic, templated. Goes through the same LLM-free path as any clinical output.

### 7.2 Export formats

- PDF (default)
- CSV bundle (one CSV per instrument + one for events)
- FHIR Observation resources (R4) for EHR-integrable output (v2 SKU)
- HL7 v2 ORU messages (where payer demands it; v2 SKU)

---

## 8. Data Model Additions

New tables (see `02_Data_Model.md` for integration):

### 8.1 `psychometric_instruments`

Static reference table. One row per instrument version.

```sql
CREATE TABLE psychometric_instruments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                  TEXT NOT NULL,        -- 'phq9', 'gad7', 'audit_c', ...
  version               TEXT NOT NULL,        -- 'v1.0' from source
  locale                TEXT NOT NULL,        -- 'en-US', 'es-MX', ...
  item_count            SMALLINT NOT NULL,
  scoring_function      TEXT NOT NULL,        -- ref to scoring impl
  citation              TEXT NOT NULL,
  licensing             TEXT NOT NULL,
  is_active             BOOLEAN NOT NULL DEFAULT true,
  clinical_signoff_at   TIMESTAMPTZ NOT NULL,
  clinical_signoff_by   UUID,
  UNIQUE (code, version, locale)
);
```

### 8.2 `psychometric_assessments`

One row per administration.

```sql
CREATE TABLE psychometric_assessments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  instrument_id         UUID NOT NULL REFERENCES psychometric_instruments(id),
  administered_at       TIMESTAMPTZ NOT NULL,
  completed_at          TIMESTAMPTZ,
  responses             SMALLINT[] NOT NULL,   -- raw item responses
  total_score           REAL,
  subscale_scores_json  JSONB,
  severity_band         TEXT,
  safety_flags_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
  completion_state      TEXT NOT NULL,         -- completed | skipped | partial
  context_state         TEXT,                  -- calm | elevated | ...
  administration_mode   TEXT NOT NULL,         -- full | ema | clinician_administered
  session_id            UUID,                  -- ties EMA pairs
  tz_offset_minutes     SMALLINT
);

CREATE INDEX idx_pa_user_time ON psychometric_assessments(user_id, administered_at DESC);
CREATE INDEX idx_pa_instrument ON psychometric_assessments(instrument_id);
```

### 8.3 `psychometric_change_events`

Emitted by change detection; consumed by pattern engine, clinician alerts, user insights.

```sql
CREATE TABLE psychometric_change_events (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  instrument_id         UUID NOT NULL REFERENCES psychometric_instruments(id),
  detected_at           TIMESTAMPTZ NOT NULL,
  change_kind           TEXT NOT NULL,        -- rci_threshold | band_crossing | trend
  from_score            REAL,
  to_score              REAL,
  from_band             TEXT,
  to_band               TEXT,
  supporting_assessment_ids UUID[] NOT NULL
);
```

### 8.4 `psychometric_preferences`

Per-user opt-outs and cadence overrides.

```sql
CREATE TABLE psychometric_preferences (
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  instrument_code       TEXT NOT NULL,
  opt_out               BOOLEAN NOT NULL DEFAULT false,
  cadence_override      TEXT,                 -- 'weekly', 'monthly', 'never', ...
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, instrument_code)
);
```

### 8.5 Retention

- `psychometric_assessments`: indefinite (user-owned clinical evidence).
- `psychometric_change_events`: indefinite.
- `psychometric_preferences`: indefinite.
- All tables covered by user soft-delete + hard-delete pipeline (30-day recovery → purge).

---

## 9. API Surface

New endpoints (see `03_API_Specification.md` for full specs):

```
GET    /v1/psychometric/due                       List instruments due for user
GET    /v1/psychometric/instruments/{code}        Item list + meta for administration
POST   /v1/psychometric/assessments               Submit responses, receive score
GET    /v1/psychometric/assessments               Paginated history
GET    /v1/psychometric/assessments/{id}          Single assessment
GET    /v1/psychometric/trajectories              Score timeseries per instrument
GET    /v1/psychometric/preferences               User opt-outs
PATCH  /v1/psychometric/preferences/{code}        Update cadence / opt-out
POST   /v1/psychometric/assessments/{id}/safety-ack  User acknowledges safety resources shown

# Clinician-scope
GET    /v1/clinician/patients/{id}/psychometric/trajectories
GET    /v1/clinician/patients/{id}/psychometric/summary-pdf
```

---

## 10. Backend Module: `discipline.psychometric`

Add to the module map (`05_Backend_Services.md` §2):

```
src/discipline/psychometric/
├── router.py                   HTTP surface (POST /v1/assessments)
├── repository.py               In-memory assessment store
├── scheduler.py                Due-instrument calculator (decide())
├── safety_items.py             T3/T4 safety-item evaluation (PHQ-9 item 9, C-SSRS)
├── scoring/                    68 deterministic scorer modules (one per instrument)
│   ├── phq9.py, gad7.py, who5.py, audit.py, audit_c.py   # Tier A core
│   ├── dast10.py, pss10.py, dtcq8.py, urica.py            # Tier A substance/motivation
│   ├── craving_vas.py, readiness_ruler.py                  # Tier A EMA
│   ├── phq2.py, gad2.py, phq15.py, cesd.py, dass21.py    # Mood/depression
│   ├── shaps.py, hads.py, panas10.py                       # Affect
│   ├── oasis.py, pswq.py, spin.py, stai6.py, fneb.py      # Anxiety/social
│   ├── pcl5.py, pcptsd5.py, iesr.py                        # PTSD/trauma
│   ├── cssrs.py, scoff.py, asrs6.py, mdq.py               # Safety/screening
│   ├── sds.py, cuditr.py, ftnd.py, cius.py                # Substance
│   ├── igds9sf.py, sassv.py, pgsi.py, pacs.py             # Behavioral addiction
│   ├── k10.py, k6.py, core10.py, wemwbs.py, swls.py      # Distress/wellbeing
│   ├── cdrisc10.py, brs.py, brief_cope.py, aaq2.py        # Resilience/coping
│   ├── gse.py, rses.py                                     # Self-efficacy/esteem
│   ├── ders16.py, erq.py, tas20.py, maas.py               # Regulation
│   ├── ffmq15.py, rrs10.py, scssf.py                      # Mindfulness/rumination
│   ├── mspss.py, ucla3.py, aces.py, bis11.py              # Social/context
│   ├── wsas.py, ess.py, isi.py, pcs.py, lotr.py          # Functional/sleep
│   └── ... (68 total — see scoring/ directory)
└── tests/                      Scorer unit tests + HTTP routing tests
```

Service interface (excerpt):

```python
class PsychometricService:
    async def due_for_user(self, user_id: UUID, now: datetime) -> list[DueAssessment]: ...
    async def submit(self, user_id: UUID, submission: AssessmentSubmission) -> AssessmentResult: ...
    async def history(self, user_id: UUID, instrument_code: str, range: DateRange) -> list[Assessment]: ...
    async def trajectory(self, user_id: UUID, instrument_code: str) -> Trajectory: ...
```

---

## 11. Mobile UX

### 11.1 Administration screens

- **AssessmentIntroScreen:** instrument name, expected duration, why we ask, skip option.
- **AssessmentItemScreen:** one item per screen (reduce carryover bias), progress bar, back button.
- **AssessmentResultScreen:** score, band, contextualizing copy, linked resources, never diagnostic language.

### 11.2 EMA mini-presentation

- 1–2 items inline in morning/evening check-in card.
- Submitted as an EMA-mode assessment.
- User can tap "take the full version" to escalate to full instrument.

### 11.3 Trajectory visualization

- Line chart per instrument across selectable windows (4w, 12w, 6m, 1y).
- Band thresholds visually overlaid.
- Safety-flag markers visible to user with on-tap context.

### 11.4 Never

- Never show "scores" as a leaderboard or social comparison.
- Never show streak of assessments completed — it's not a game.
- Never announce a band change as "you got worse." Change is surfaced with curiosity framing.

---

## 12. Localization

- Each instrument in each supported locale is **independently validated** — we don't use Google-translated clinical items.
- Source: WHO + publisher-approved translations where available.
- Required locales at v1.0: en-US. Added by v1.5: en-GB, es-US, es-MX. By v2: pt-BR, fr-CA, de-DE.
- An instrument without a validated translation **is not shown in that locale** — not auto-translated.

---

## 13. Research & Publication

### 13.1 Opt-in cohort consent

Users can opt in to "contribute anonymized psychometric data to methodology research." Only opted-in users' data enters the research corpus.

### 13.2 De-identification

- User IDs mapped to research pseudonyms in a one-way table with access restricted to DPO.
- Dates jittered ±3 days (research-common technique).
- Rare-event data (severity X + vertical Y + geo Z) suppressed if cohort < 30.

### 13.3 Methodology papers

- Open-source the scoring code.
- Publish trajectories (aggregated) in peer-reviewed work.
- Never publish individual-level data.

### 13.4 IRB oversight

- Research use requires IRB approval (vendor IRB first, then partner academic IRB for major studies).
- Informed consent doc distinct from product ToS.
- Withdrawal means data is removed from future research corpora; already-published aggregate statistics remain.

---

## 14. Clinician Review Workflow

For organizations with clinician oversight (v2 SKU):

1. Patient completes assessment.
2. Change event emitted.
3. If crosses clinical threshold → clinician inbox alert.
4. Clinician can annotate (notes never visible to patient unless shared).
5. Follow-up scheduled in-app.
6. Summary appears in next clinical summary PDF.

---

## 15. Quality & Validation

### 15.1 Scoring fidelity test suite

- Every instrument has a "golden" test using scoring examples from the source publication.
- CI fails if any scoring function produces a different result from the published value.

### 15.2 Translation fidelity

- On adding a locale, back-translation check by a second translator.
- Cognitive interview pilot (n=15) before locale go-live.

### 15.3 Change-detection validation

- RCI thresholds validated against published test-retest reliability.
- Trend detection false-positive rate monitored; target < 5%.

### 15.4 Safety-item coverage

- Unit + integration + E2E tests exercise the PHQ-9 item 9 path.
- Quarterly drill: simulated endorsement triggers full T4 pipeline in staging.

---

## 16. What's Out of Scope

- **Diagnostic claims.** We never tell a user they have a disorder. The MINI + SCID require a clinician.
- **Billing codes / CPT.** Clinical SKU only; consumer product never bills for assessments.
- **Algorithmic triage toward specific medications.** Out of category.
- **Replacing clinician judgment.** Trajectories are inputs to a clinical conversation, not substitutes for one.
