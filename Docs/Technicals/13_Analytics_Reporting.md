# 13 — Analytics & Reporting System

**Document:** Analytics, Data Analysis, and Reporting subsystem specification
**Status:** Authoritative, production target
**Audience:** Backend engineers, data engineers, clinical research leads, product, privacy counsel
**Upstream dependencies:** 02_Data_Model, 05_Backend_Services, 06_ML_AI_Architecture, 07_Security_Privacy, 12_Psychometric_System

---

## 1. Purpose

The analytics and reporting subsystem exists to serve **four non-interchangeable audiences**, each with incompatible demands on the same underlying data:

| Audience | What they need | What is protective / required |
|---|---|---|
| **User (self-insight)** | Longitudinal trajectories, pattern discovery, week/month summaries | No shame framing, no false precision, no raw scores exposed without context, no "dashboards of decline" |
| **Clinician (linked)** | Psychometric trajectories with RCI, instrument-level scores, safety events, session attendance | Scientific rigor; full fidelity to instrument scoring; cited interpretation ranges |
| **Enterprise / program owner** | De-identified, aggregate, cohort-level outcomes for contracted cohorts only | k-anonymity ≥ 5; no re-identifiable drill-down; differential-privacy noise on public-facing stats |
| **Internal product & research** | Funnel analytics, retention, intervention efficacy experiments, model telemetry | PHI-free event layer; product events must never carry free-text journal content or instrument responses |

These four audiences **cannot share a single pipeline**. A protective filter that is ethical for a user (smoothing a PHQ-9 bump so it does not feel catastrophic) is scientific malpractice for a clinician. A drill-down that is routine for a clinician is a re-identification attack for an enterprise. The architecture below enforces these boundaries.

---

## 2. Design principles

1. **PHI never crosses into product analytics.** Product event pipeline (PostHog self-hosted) receives event names and coarse non-sensitive properties only. No journal text, no psychometric responses, no urge descriptors, no free-text crisis inputs, no biometric samples, ever.
2. **Aggregation-first for enterprise reporting.** Enterprise customers never see individual user data. All their reports are server-side-aggregated, k-anonymized, and differentially-noised.
3. **Deterministic scoring only.** Every score shown in any report is produced by a pure, version-pinned scoring function (see 12_Psychometric_System §5). Reports never contain LLM-generated numbers.
4. **Provenance is non-negotiable.** Every score, trajectory point, and aggregate in every report carries a provenance tuple: `(instrument_id, version, scoring_function_version, administration_id, administration_timestamp, source="user"|"clinician"|"ema")`.
5. **Time zones are sticky.** A user's day boundaries use their recorded local time zone at the moment of each event. Retrospective time-zone changes do not silently rewrite history.
6. **Reports are idempotent and reproducible.** Any report can be regenerated from raw source data and yield byte-identical output (ignoring render timestamp). This is a compliance requirement, not an aspiration.
7. **Protective framing is a first-class feature, not a UX decoration.** The user-insight surface applies a documented set of framing rules (below) that are versioned and reviewed by clinical advisors. This is not about hiding bad news — it is about presenting bad news in a way that does not itself cause harm.

---

## 3. Data architecture

### 3.1 Source of truth vs. analytical stores

```
┌────────────────────────────────────────────────────────────────┐
│  Operational (source of truth) — Postgres 16 + TimescaleDB      │
│  • users, urge_events, interventions, outcomes, relapse_events  │
│  • psychometric_assessments, psychometric_change_events          │
│  • journals (pgvector for embeddings, not for analytics)         │
└────────────────────────────────────────────────────────────────┘
            │
            ├──→ daily_user_rollups (materialized, timezone-aware)
            ├──→ psychometric_trajectories (computed on assessment write)
            └──→ event export to analytics sinks (per pipeline)
                 │
     ┌───────────┼──────────────────┬───────────────────────────┐
     ▼           ▼                  ▼                           ▼
  PostHog    ClickHouse*        Research warehouse        Enterprise
  (product   (server-side       (de-identified,           reports
  events,    analytics          IRB-gated, opt-in         (k-anon,
  PHI-free)  of operational     only, pseudonymous)       DP-noised)
             facts)
```

*ClickHouse is used for internal product/clinical analytics that need columnar performance over operational facts. It is on the same compliance perimeter as Postgres (HIPAA BAA, in-VPC, KMS-encrypted).

### 3.2 Rollup tables

The daily rollup (`daily_user_rollups`, defined in 02_Data_Model) is the backbone of user-facing trajectories. It is rebuilt nightly in the user's recorded time zone and covers:

- Urges: `urges_total`, `urges_handled`, `urges_escalated_to_t3`, `urges_followed_by_relapse_within_24h`
- Relapses: `relapses_count` (never resets resilience streak — see §6)
- Interventions: `interventions_delivered_t1`, `_t2`, `_t3`, `_t4`; `interventions_accepted_t1`, `_t2`; `effectiveness_mean_t1`, `_t2` (Laplace-smoothed)
- Psychometrics: `phq9_latest`, `gad7_latest`, `pss10_latest`, `audit_c_latest`, `who5_latest` (NULL if not administered within rolling window)
- Biometrics (derived, on-device): `sleep_hours_mean`, `resting_hr_mean`, `hrv_rmssd_mean` (windowed)
- Engagement: `app_opens`, `check_ins_completed`, `journals_entered`
- Safety: `crisis_path_entries`, `hotline_link_taps`, `safety_plan_activations`

Rollups are immutable once the day is closed (3am local + 6h grace). Late-arriving events within grace are backfilled; events arriving after close trigger an append-only correction row, never an in-place edit.

### 3.3 Psychometric trajectory store

`psychometric_trajectories` is a compact derived table optimized for chart rendering:

```sql
CREATE TABLE psychometric_trajectories (
  user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  instrument_id      TEXT NOT NULL,
  version            TEXT NOT NULL,
  administered_at    TIMESTAMPTZ NOT NULL,
  total_score        INTEGER NOT NULL,
  subscale_scores    JSONB NOT NULL DEFAULT '{}'::jsonb,
  severity_band      TEXT NOT NULL,
  rci_vs_baseline    NUMERIC(6,3),
  rci_vs_previous    NUMERIC(6,3),
  clinically_significant_change BOOLEAN NOT NULL DEFAULT FALSE,
  scoring_fn_version TEXT NOT NULL,
  source             TEXT NOT NULL CHECK (source IN ('user','clinician','ema')),
  PRIMARY KEY (user_id, instrument_id, version, administered_at)
);
CREATE INDEX ix_pt_user_instrument_time
  ON psychometric_trajectories (user_id, instrument_id, administered_at DESC);
```

RCI is computed using published reliability coefficients per instrument (see 12_Psychometric_System §5.4 and the research citations in `Docs/Whitepapers/02_Clinical_Evidence_Base.md`).

---

## 4. User-facing insights (self-insight surface)

### 4.1 Surfaces

| Surface | Cadence | Shown in | Latency SLO |
|---|---|---|---|
| **Today** | On every app open | Home screen card | < 150 ms from cache |
| **Weekly Reflection** | Sunday 18:00 local | Dedicated screen + optional push | Pre-rendered by 16:00 local |
| **Monthly Story** | 1st of month | Dedicated screen | Pre-rendered by day 1, 08:00 local |
| **Pattern Insights** | Event-driven | Home screen inline + Patterns tab | ≤ 5 min after pattern confirmed |
| **Instrument Trajectory** | On assessment completion + Psychometrics tab | Psychometrics detail screen | Live |

### 4.2 Protective framing rules (v1.0)

Every user-facing metric passes through a framing layer before render. These rules are versioned. Changes require clinical advisor sign-off.

**Rule P1 — No unframed decline.** A trajectory that shows worsening must be accompanied by: (a) context ("many people go through weeks like this"), (b) actionability ("here are two small things you used successfully last month"), and (c) absence of superlatives ("worst ever", "lowest", "bottom"). Never rank against personal historical extremes in a way that implies rock-bottom.

**Rule P2 — No spurious precision.** PHQ-9 delta of 1 point is not reported as "+1 worse". It is reported as "roughly the same — normal week-to-week variation." The threshold for a reported change is RCI ≥ 1.96 (95% confidence) — anything below that is explicitly flagged as within-noise.

**Rule P3 — Resilience streak is always primary.** The resilience-days counter (never resets) is the headline number on every summary. The continuous days number is secondary and explicitly described as "just one way to measure."

**Rule P4 — Relapse language.** The word "relapse" appears nowhere in user-facing copy. The event is called "a setback" in summaries and "a slip" in logs. The event date is recorded; the count is not emphasized.

**Rule P5 — Crisis events are invisible in analytics.** T3 crisis-path entries do not appear in any user-facing trend. They are in the clinical record (for the clinician surface and the user's own export on demand), but a user browsing their weekly summary does not see "crisis entries: 3" as a statistic.

**Rule P6 — Framing is localized.** All framing copy is per-locale, reviewed by a clinical native speaker. No auto-translation of framing text.

### 4.3 Weekly Reflection structure

```
Week of Mar 17–23

Resilience: 287 days strong
Continuous: 42 days (your current streak)

This week
  • 14 urges noticed and handled
  • 3 urges reached crisis mode and passed
  • 2 small wins you named: "walked instead of scrolled", "called Sam"

What you told your journal
  [User highlights from journals, extracted by a local pattern-matcher
   and surfaced only with consent. Never LLM-synthesized claims about
   the user's life.]

Your check-ins this week
  Mood (1–10):   6.2 avg  (within your usual range)
  Sleep:         6h 42m avg  (below your usual — worth noticing)
  PHQ-9 last:    7 — mild range, roughly the same as two weeks ago

One small thing for next week
  [A suggestion drawn from what worked for this user historically,
   not a generic tip. Produced by the pattern engine, not the LLM.]
```

The copy is produced by a template engine with slot-filling from pre-computed facts. The LLM is **not** in this path.

### 4.4 Monthly Story

The Monthly Story is a longer-form version of the Weekly Reflection, additionally surfacing:
- Instrument trajectories (PHQ-9, GAD-7, WHO-5, AUDIT-C, PSS-10) with RCI-gated change annotations
- Patterns confirmed during the month (from the pattern module — see 05_Backend_Services)
- Intervention efficacy summary ("urge surfing helped 68% of the time this month; box breathing 54%")
- A "things you did" section (no count of failures)

---

## 5. Clinician surface

### 5.1 What the clinician sees

When a user links a clinician via `/v1/clinician/*` and grants read access, the clinician gets, **only for scopes the user explicitly granted**:

- Instrument-level scores with full provenance, in a table view and trajectory view
- Severity bands with citation footnotes to the validation literature
- RCI annotations at clinical standard (1.96 SE_diff)
- Safety items flagged (PHQ-9 item 9, C-SSRS items) — always surfaced if present, never smoothed
- Adherence: completion rates of scheduled assessments, engagement cadence (aggregate)
- The user's exported journal excerpts **only if the user granted journal-share scope**

The clinician surface has a **different framing layer from the user surface**. No protective smoothing. No Rule P1/P2/P4. It reads like a medical record summary, not a weekly reflection.

### 5.2 Clinical summary PDF

The clinical summary PDF is the primary handoff artifact. See 12_Psychometric_System §7 for PDF layout. Additional analytical elements the PDF carries:

- Adherence timeline (what was assessed, what was skipped, reasons if recorded)
- Pattern engine outputs flagged "clinically reviewable" (not every pattern; patterns pass a configurable confidence gate)
- Intervention/tool utilization breakdown
- Engagement cadence (weekly active days)

Every number in the PDF links back to a source administration record. The PDF is signed (digital signature) and carries a document hash so tampering is detectable.

### 5.3 Clinician-facing API

See 12_Psychometric_System §9 and 03_API_Specification §X for the `/v1/clinician/patients/{user_id}/...` endpoints. Analytics-specific additions:

- `GET /v1/clinician/patients/{user_id}/trajectories?instrument=phq9&window=90d` — structured trajectory JSON
- `GET /v1/clinician/patients/{user_id}/summary?format=pdf` — clinical summary PDF
- `GET /v1/clinician/patients/{user_id}/summary?format=fhir` — FHIR R4 Observation bundle
- `GET /v1/clinician/patients/{user_id}/summary?format=hl7v2` — HL7 v2.5.1 ORU^R01 message

All clinician access is logged to `audit_logs` with the clinician's identity, the patient's identity, the scope accessed, and the timestamp. These logs are themselves immutable and available to the user on request (HIPAA Right of Access).

---

## 6. Enterprise & program reporting

### 6.1 Contract scope

An enterprise contract (employer EAP, university counseling center, health plan partner) is represented as an `enterprise_contracts` row (02_Data_Model). Each contract defines a **cohort membership rule** (e.g., "users who signed up via this SSO realm"). Membership is dynamic — a user who leaves the program is retroactively excluded from reports covering dates after their departure.

Enterprise customers never receive any individual user data. They receive only:

### 6.2 Aggregate metrics produced

| Metric | Definition | Protection |
|---|---|---|
| **Cohort size** | Users currently enrolled | Only shown if ≥ 25 |
| **Active users (7d, 30d)** | Opened app within window | k-anonymity ≥ 5; counts < 5 reported as "< 5" |
| **Crisis-path engagement rate** | Proportion of active users who entered crisis mode ≥ once | Rates computed only when numerator ≥ 5 AND denominator ≥ 25 |
| **Baseline-to-current delta (PHQ-9, GAD-7, WHO-5)** | Mean change from first assessment to most recent, per user, averaged over cohort | Reported with 95% CI via bootstrap; DP-noise (ε=1.0) on published numbers |
| **Intervention acceptance rate** | T1/T2 acceptance aggregated | k-anonymity ≥ 5 |
| **Hotline link engagement** | Aggregate only; no timestamps, no frequency |
| **Average resilience days** | Mean across active users | DP-noised |

### 6.3 What enterprise reports *never* contain

- Any user identifier (not even pseudonymous)
- Timestamps finer than week
- Any journal text, any psychometric response, any individual score
- Any ability to filter or drill down below the cohort aggregate
- Any export format that would permit re-identification

### 6.4 Delivery

Enterprise reports are generated monthly as signed PDFs and CSVs with aggregates only. Delivery is via authenticated portal (no email attachments of PHI-adjacent artifacts). Reports are generated by a dedicated worker that has read-only access to a **restricted view** of operational data — this view enforces the k-anonymity and DP-noise rules at the SQL layer, not at the application layer, so bugs in application code cannot accidentally leak raw figures.

---

## 7. Internal product & research analytics

### 7.1 Product event layer (PostHog)

The product event layer answers questions like "what % of new users complete onboarding", "which intervention variant has higher 7-day retention", "does the crisis-button's new copy increase engagement".

**PostHog is PHI-free by construction.** The client SDK is wrapped in a thin allow-list that rejects any event property not on the schema. The schema is code-reviewed and cannot be bypassed. Example allowed events:

- `app_opened` (no properties except `cold_start: bool`)
- `onboarding_step_completed` (property: `step: "consent"|"profile"|"permissions"|"first_check_in"`)
- `intervention_delivered` (properties: `tier: "t1"|"t2"`, `variant_id: string`) — never the intervention content
- `crisis_path_entered` (no properties) — no count context, no triggering signal
- `assessment_started` (property: `instrument_id: string`) — never the responses or score
- `feature_used` (property: `feature: string`) — feature names from a fixed enum

Properties that are **strictly forbidden**: `user_text`, `journal_excerpt`, `score`, `response`, `severity`, `crisis_reason`, any free-form string.

### 7.2 Server-side analytics (ClickHouse)

Product questions that require joining operational facts (e.g., "does intervention acceptance predict 30-day PHQ-9 improvement") need real data, not PHI-free events. ClickHouse is used here, inside the HIPAA perimeter, with:

- Role-based access (only named analysts / researchers)
- All queries logged to audit_logs
- Cell-level access policies: an analyst can see aggregate queries but not SELECT-* from source tables
- Dashboards reviewed by privacy counsel before publication

### 7.3 Experimentation

A/B tests on non-clinical surfaces (onboarding copy, notification timing, icon choices) use feature flags (Unleash self-hosted, in-VPC). Experiments on clinical surfaces (intervention content, T1/T2 wording, crisis-path variations) are **not product experiments** — they are clinical experiments and require IRB review before launch (see §8 and `Docs/Whitepapers/04_Safety_Framework.md`).

### 7.4 Model telemetry

Model telemetry (bandit rewards, classifier confusion, urge-predictor calibration) lives in ClickHouse and is covered in 06_ML_AI_Architecture §7. Model telemetry does not contain PHI; the unit of analysis is the model prediction, not the user content.

---

## 8. Research warehouse (de-identified, opt-in, IRB-gated)

For formal research collaborations, published studies, and algorithmic improvements that cannot be validated on internal data alone, a separate de-identified research warehouse exists.

- **Enrollment:** Users explicitly opt in via a consent flow with IRB-approved copy. Consent is revocable; revocation removes future exports but cannot un-do prior exports (users are informed of this before opting in).
- **De-identification:** HIPAA Safe Harbor de-identification is applied: all 18 identifiers removed, dates shifted per user by a random offset ∈ [-365, +365] days, ages ≥ 90 banded, ZIP3 only. A statistician-approved re-identification risk assessment is run before any export goes out.
- **Access:** Researchers request specific data slices via a data-use agreement (DUA). Access is time-boxed, scope-limited, and revoked automatically on DUA expiry.
- **Warehouse location:** A physically separate AWS account with its own KMS CMK; no production credentials reach it.

The specific research program plan, IRB status, and current DUAs are tracked in `Docs/Research/` (created as research partnerships are formed).

---

## 9. API surface (analytics & reporting)

See 03_API_Specification for full request/response shapes. Summary:

### User-facing
- `GET /v1/insights/today` — Home card payload
- `GET /v1/insights/week?week_of=YYYY-MM-DD` — Weekly Reflection
- `GET /v1/insights/month?month=YYYY-MM` — Monthly Story
- `GET /v1/insights/patterns` — Currently surfaced patterns with explanations
- `GET /v1/insights/trajectory?instrument=phq9&window=180d` — Instrument trajectory, user-framed

### Export (HIPAA Right of Access — always available, machine-readable)
- `GET /v1/me/export` — Bundle of all user data in JSON + PDF + FHIR bundle; delivered as a signed URL
- `POST /v1/me/export/scopes` — User-controlled scope selection (e.g., "exclude journals")
- `GET /v1/me/export/{export_id}/status` — Progress
- `POST /v1/me/quick-erase` — Hard delete with 24h soft-delete window; documented explicitly

### Clinician-facing
- `GET /v1/clinician/patients/{user_id}/summary?format=pdf|fhir|hl7v2`
- `GET /v1/clinician/patients/{user_id}/trajectories?instrument=...&window=...`
- `GET /v1/clinician/patients/{user_id}/adherence`

### Enterprise (admin portal, not mobile)
- `GET /v1/enterprise/{contract_id}/report?period=YYYY-MM` — Aggregate report (JSON + PDF)
- `GET /v1/enterprise/{contract_id}/report/preview` — Live estimate with current-month data

---

## 10. Backend module structure

```
services/api/src/discipline/
├── analytics/
│   ├── __init__.py
│   ├── router.py                # /v1/insights/* endpoints
│   ├── rollups.py               # daily_user_rollups builder
│   ├── trajectories.py          # psychometric_trajectories builder
│   ├── framing.py               # Protective framing rules (P1–P6)
│   ├── patterns_surface.py      # User-facing pattern presentation
│   ├── weekly_reflection.py     # Weekly template renderer (no LLM)
│   ├── monthly_story.py         # Monthly template renderer
│   └── tests/
├── reports/
│   ├── __init__.py
│   ├── router.py                # /v1/me/export, /v1/clinician/.../summary
│   ├── clinical_pdf.py          # Clinical summary PDF generator
│   ├── fhir_observation.py      # FHIR R4 Observation bundle builder
│   ├── hl7v2_oru.py             # HL7 v2.5.1 ORU^R01 builder
│   ├── user_export.py           # Full HIPAA-RoA export bundler
│   ├── enterprise.py            # k-anon + DP aggregation
│   └── tests/
```

`analytics` and `reports` are separate because they have different concurrency profiles (analytics = read-heavy on-request; reports = async worker, hours-long tolerance, heavy PDF rendering) and different blast radii (analytics bug = wrong chart; reports bug = wrong clinical handoff — much higher stakes).

---

## 11. Privacy controls in the analytics pipeline

The analytics and reporting subsystem is the single biggest privacy exposure surface in the product. The following controls are enforced:

| Control | Where enforced |
|---|---|
| No PHI in product event pipeline | Client SDK allow-list + server ingest reject + PostHog schema lock |
| No individual identifiers in enterprise reports | SQL-level view with k-anon; DP-noise layer; test suite that attempts to extract individual data from reports and asserts failure |
| Clinician access scoped to granted permissions | `/v1/clinician` middleware checks `clinician_links.scopes` on every request |
| Research warehouse de-identification | Pre-export statistician review + automated Safe Harbor check |
| Export audit trail | Every report generation writes to `audit_logs`; users can query their own audit trail |
| Report reproducibility | Every report carries a `data_as_of` timestamp and source version hashes; same inputs → same output |
| PHI never reaches LLMs | Covered at the LLM middleware layer (06_ML_AI_Architecture §6) — reports never pass through the LLM path |

---

## 12. Quality & validation

- **Scoring fidelity tests (inherited from 12_Psychometric_System):** every instrument scored against the published reference tables; zero tolerance for drift.
- **Framing rule tests:** each of Rules P1–P6 has a dedicated test that asserts the UI/API response complies given a curated input (e.g., a worsening trajectory does not produce a "worst ever" string).
- **k-anonymity tests:** enterprise report generator is tested against synthetic cohorts of size 3, 5, 10, 25, 100; assertions that reports for n<25 refuse to render and reports for n=25 correctly suppress any field with <5 in a cell.
- **Differential privacy tests:** repeated generation on a fixed cohort produces varied published values with the expected noise envelope.
- **Reproducibility test:** generate a PDF for a fixed user and a fixed date range; SHA-256 of the content (minus the render timestamp) must be stable across runs and across deploys (pinned fonts, pinned layout).
- **Red-team test:** a recurring exercise where a privacy engineer attempts to re-identify individuals from an enterprise report; findings are tracked and remediated before the report is signed off for the quarter.

---

## 13. Out of scope for this document

- The mobile UI of the Weekly Reflection / Monthly Story / Trajectories — owned by 04_Mobile_Architecture and the design system.
- The specific layout and typography of the clinical PDF — owned by `Docs/Design/Clinical_PDF_Layout.md` (to be created alongside the first PDF implementation).
- Model training and evaluation pipelines — owned by 06_ML_AI_Architecture.
- Data retention schedules — owned by 07_Security_Privacy §X.

---

## 14. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-18 | Initial authoritative specification |
