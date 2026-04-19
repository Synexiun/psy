# Technical Roadmap — Discipline OS

> **Surfaces at launch:** iOS · Android · Web (marketing, app, clinician alpha, enterprise pilot, crisis).
> **Locales at launch (v1.0):** `en`, `fr`, `ar`, `fa` (Arabic and Persian are RTL).
> **Framing:** production-target from day one. This is not an MVP-then-harden plan — clinical defensibility, SOC 2, HIPAA, and four-locale parity are built into the phase gates. See `../bUSINESS/07_Roadmap.md` for the aligned business view.

---

## 1. Roadmap Structure

We organize the technical roadmap in **5 phases** aligned to the business roadmap. Each phase is 3-6 months, with explicit entry and exit gates. **Nothing ships because a calendar says it should — gates are always measured against reality.**

| Phase | Duration | Codename | Goal |
|-------|----------|----------|------|
| 0 | Months 0–3 | Bedrock | Validate clinical hypothesis with a human-in-the-loop closed system |
| 1 | Months 4–9 | Closed Loop | Full closed-beta with on-device ML, en-only, iOS + Android + web-app internal |
| 2 | Months 9–14 | Launch Ready | v1.0 public launch — iOS + Android + web (marketing, app, crisis), four locales (en/fr/ar/fa), clinician portal alpha, enterprise pilot |
| 3 | Months 15–24 | Expand | Clinician portal GA, enterprise GA (self-serve SSO/SCIM), second vertical, additional locales |
| 4 | Months 24–36 | Clinical | FDA SaMD pathway, prescription SKU, reimbursement |
| 5 | Months 36–60 | Platform | Multi-vertical, multi-region, researcher API, cross-product moat |

This roadmap maps onto **16 Technicals specs** (`00_Architecture_Overview.md` through `16_Web_Application.md`). Every deliverable below is traceable to a spec section — no off-spec work.

---

## 2. Phase 0 — Bedrock (Months 0–3)

### Goal
Prove the clinical hypothesis that **the closed-loop intervention model reduces urge-to-action within a cohort of real users** — before committing to production engineering.

### Technical deliverables

| # | Deliverable | Spec ref | Owner |
|---|-------------|----------|-------|
| 1 | Landing page + waitlist + research screener (en only) | 16 | Founder / contract |
| 2 | Staff-only iOS app (local-only, no backend) | 04 | iOS lead |
| 3 | Human-in-the-loop intervention: clinicians hand-send nudges to 15 volunteers based on check-ins | 05 §Intervention | CEO + Head of Clinical |
| 4 | Minimal backend: Clerk stub + 1 FastAPI service + Postgres, enough for check-in + response | 05, 14 | Backend lead |
| 5 | Instrumented anonymous telemetry for research sign-off | 13 | Backend lead |

### Technical bar

- 15 users for 6 weeks; measurable increase in "handled" outcomes vs. baseline check-in-only control.
- Staff iOS app functional with HealthKit + check-in + basic tool library (10 scripted tools, en only).
- Data pipeline sufficient for weekly clinical review.
- No MFA/SSO/web surfaces yet — this is an internal validation phase.

### Gate to Phase 1
- **Clinical signal:** measurable handled-outcome lift vs baseline (advisor-adjudicated).
- **Product signal:** 10 of 15 users request continued access; qualitative interviews show mechanism clarity.
- **Capital:** seed round closed (~$5.5M target).
- **Team:** CTO + 3 engineers + Head of Clinical + Clinical Content Lead hired.
- **Regulatory posture defined:** wellness-now / SaMD-later path explicitly documented.

---

## 3. Phase 1 — Closed Loop (Months 4–9)

### Goal
Ship v0.5 to closed beta (300 users, en-only, iOS + Android primary; web-app available in internal QA). Full closed-loop architecture operating with on-device ML and first-class auth/logging from day one.

### Engineering workstreams

#### W1 — Mobile foundation (2 engineers)
- React Native **0.76+** skeleton with New Architecture (Fabric, TurboModules, Hermes). Spec: `04_Mobile_Architecture.md §2`.
- iOS + Android shared UI foundation; shared design system primitives (`packages/design-system/`).
- Native signal-ingest modules (HealthKit, Health Connect).
- Journal write + voice session UX.
- App-lock, alt-icon, quick-erase. Offline mutation queue + SQLite.
- **i18n harness** even though we ship en-only: ICU MessageFormat in place, `forceRTL` tested on an RTL debug locale so Phase 2 does not surprise us. Spec: `15_Internationalization.md`.

#### W2 — Backend foundation (2 engineers)
- Modular monolith scaffolded with all modules per `05_Backend_Services.md §2`: `identity`, `signal`, `intervention`, `clinical`, `memory`, `compliance`, `psychometric`, `analytics`, `reports`, `content`, `shared.logging`, `shared.i18n`.
- TimescaleDB + pgvector; ClickHouse stood up (even if analytics surface is thin).
- Envelope encryption pipeline; per-user DEK + AWS KMS CMK.
- Clerk → EdDSA JWT exchange via KMS (`14_Authentication_Logging.md §2–3`); 15-min access + 30-day rolling refresh with family rotation + reuse detection. **MFA mandatory** from day one — staff + beta users both.
- Four-stream logging with IAM-isolated writer roles (`14 §9`): `app.log`, `audit.log` (S3 Object Lock compliance mode), `safety.log`, `security.log`.
- Audit log + retention workers.

#### W3 — Infrastructure (1 engineer / part-time CTO)
- Terraform 1.8+ for prod + staging. ECS Fargate.
- Per-origin CloudFront + WAF for web apps (even if only `www` and `app` are live in Phase 1). Spec: `08_Infrastructure_DevOps.md §4`.
- S3 Object Lock buckets provisioned for `audit.log` (7y) and `safety.log` (10y). Writer role cannot DeleteObject.
- Observability stack (Loki, Prometheus, Grafana, Tempo, Sentry self-hosted with project per surface).
- CI/CD pipeline with per-locale catalog lint gates (no-op yet, but wired).

#### W4 — ML foundation (1 ML engineer)
- State classifier v0.1 on CoreML / LiteRT, seeded from Phase 0 data.
- Contextual bandit stub with seeded priors.
- Voice pipeline: Whisper-small on-device iOS; server-side fallback Android.
- Safety classifier v0.x on validation set ≥ 96% recall (target for Phase 1; v1.0 bar is ≥98%).
- Model registry + OTA + model card discipline from model #1.

#### W5 — Clinical content & psychometric (Clinical Content Lead + advisors)
- Scripted versions of 12 coping tools (en).
- Deterministic T3 crisis flow templates (en, for all 6 surfaces — mobile iOS, mobile Android, web-marketing, web-app, web-crisis static, internal).
- Compassion relapse-response templates.
- LLM prompt library v0.1 with advisor sign-off. **LLM never on safety path.**
- Psychometric instruments (en) live with validated scoring: PHQ-9, GAD-7, AUDIT-C, PSS-10, WHO-5, DTCQ-8, URICA, Readiness Ruler, C-SSRS. Scoring-correctness test suite references published reference tables (`09_Testing_QA.md §18`). **SLI: `assessment.scoring.correctness` = 100%** — non-negotiable.

#### W6 — Web foundation (0.5 engineer — shared with mobile)
- `apps/web-app` Next.js 15 skeleton with App Router, React 19, Tailwind v4, next-intl, Clerk integration stubs, shared `packages/api-client/` talking to the same backend. Used for internal QA + admin views this phase; not user-facing beta surface yet.

### Phase 1 gate → Phase 2

- 300 beta users active ≥ 60 days.
- WUH metric computable per user + cohort.
- **Zero safety incident** (missed or delayed crisis signal).
- T3 mobile latency SLO met at p95 (`<200ms warm`, `<800ms cold`).
- Safety classifier recall ≥ 96% on validation set; advisor sign-off on false-negative review.
- 99.5%+ uptime for 30 days.
- Weekly clinical review process operational with signed meeting notes.
- Psychometric scoring correctness at 100% (property-tested against published reference tables, all 9 instruments in en).
- Audit log Merkle chain verification test green.
- Auth refresh-family reuse-detection test green.
- Four-stream log IAM isolation verified (no role can write outside its stream).

---

## 4. Phase 2 — Launch Ready (Months 9–14)

### Goal
Ship **v1.0** to the public: iOS + Android on their respective stores, web (marketing, app, crisis) on four hostnames, clinician portal in invite-only alpha, enterprise in hand-rolled pilots. **Four locales (en, fr, ar, fa) at parity** — RTL fully supported, psychometric instruments with validated translations, safety content translated+reviewed, hotline directories per country.

### Major engineering initiatives

#### I1 — Surface expansion (iOS + Android + Web)

**Mobile (iOS + Android):**
- Full coping toolkit (25 tool variants).
- Widget + watch complication.
- Family tier (multi-seat).
- Subscription infra via IAP (iOS/Android) + Stripe (web).
- Relapse review workflow.
- Weekly + monthly insight reports per `13_Analytics_Reporting.md`.
- RTL layout verified across every screen; Arabic 6-plural categories, Persian digit handling.

**Web (5 Next.js apps — spec `16_Web_Application.md`):**
- `apps/web-marketing` at `www.disciplineos.com` — SEO-tuned marketing site; LCP ≤ 2.0s, INP ≤ 150ms, CLS ≤ 0.05.
- `apps/web-app` at `app.disciplineos.com` — full user dashboard: check-ins, insights, journal, tool library, crisis access.
- `apps/web-clinician` at `clinicians.disciplineos.com` — **invite-only alpha** (GA in Phase 3). Scope-gated rendering via `clinician_links.scopes`.
- `apps/web-enterprise` at `enterprise.disciplineos.com` — **pilot only** (GA in Phase 3). SSO-mandatory. Served to named pilot customers with manual provisioning.
- `apps/web-crisis` at `crisis.disciplineos.com` — static, zero network dependency after first paint, own 99.99% SLO, bundled deterministic T3 catalog mirroring mobile.

**Shared packages:**
- `packages/design-system/` with per-platform primitives.
- `packages/i18n-catalog/` — single source of truth for en/fr/ar/fa across mobile + web.
- `packages/safety-directory/` — per-country hotline directory, loaded on both surfaces.

#### I2 — Scale readiness
- Load testing to 10× projected first-month user volume, per-surface.
- Auto-scaling tested on ECS Fargate + CloudFront cache behavior validated.
- DR runbooks + semi-annual DR drill executed at least once.
- Postgres read replicas live. ClickHouse cluster sized for internal analytics.
- Backup + restore tested end-to-end (quarterly).

#### I3 — Safety & compliance
- **SOC 2 Type I audit window opens**; readiness assessment completed.
- HIPAA readiness complete — BAAs signed with **all** processors: AWS, Clerk (Enterprise BAA), Sentry (self-hosted so no BAA needed), PostHog (Enterprise BAA), ClickHouse Cloud if used, Lokalise (Enterprise BAA), any hotline-directory data provider.
- Third-party pen test conducted, findings remediated or accepted-with-mitigation.
- Safety classifier v1.0 validated: **recall ≥ 98%** on held-out set; false-negative review by clinical advisors every month.
- Audit log immutability proven (S3 Object Lock compliance mode in place, writer role has no DeleteObject).

#### I4 — Product polish & launch locales

**Four-locale launch** — strict gates per locale per `15_Internationalization.md §10`:

| Locale | BCP 47 | Script | Launch gate |
|--------|--------|--------|-------------|
| English | `en` | Latin | Default; reference translation source |
| French | `fr` | Latin | All 5 locale gates met |
| Arabic | `ar` | Arabic (RTL) | All 5 locale gates met + MSA review + Vazirmatn/IBM Plex Sans Arabic stack validated |
| Persian | `fa` | Persian (RTL) | All 5 locale gates met + Iranian Persian review + Vazirmatn (not Arabic-first) + Shamsi calendar option |

**Per-locale launch gate (5 criteria):**
1. All safety content (T3 catalog, hotline directory, compassion scripts) translated + clinical-reviewer signoff.
2. All psychometric instruments used by the product have validated translations attached (published citation recorded in `psychometric_instruments` table). Gaps (e.g. DTCQ-8 AR/FA) trigger instrument substitution plan, not launch delay.
3. Hotline directory covers every country where the locale is served, verified within the last 90 days.
4. Typography stack loads + renders on golden-path devices (low-end Android, iPhone SE, desktop Safari/Chrome/Firefox).
5. Native-speaker QA pass on onboarding + crisis flow + first-week content.

- Accessibility audit pass across golden flows (WCAG 2.2 AA baseline, AAA contrast on clinician portal).
- Performance tuning: **T3 < 200ms warm, < 800ms cold — hard gate** on mobile and on `web-crisis`.

#### I5 — Observability maturity
- SLO dashboards live with review cadence.
- Error budget policy enforced (violation blocks releases automatically).
- Clinical safety dashboard for ops (separate from product analytics).
- Four-stream log exports to SIEM (security.log) and compliance archive (audit.log, safety.log).

### Launch readiness checklist (excerpted)

- [ ] T3 latency SLO met 30 consecutive days, both mobile and `web-crisis`.
- [ ] Crash-free sessions > 99.8% (30 days), per platform.
- [ ] Safety classifier recall ≥ 98%; clinical sign-off recorded.
- [ ] Pen test remediation complete; residual risks accepted by CTO + Head of Clinical.
- [ ] SOC 2 Type I audit initiated.
- [ ] All legal review items closed (ToS, Privacy, BAA, per-country addendum for fr/ar/fa markets).
- [ ] App-store compliance (medical claims, rating, metadata) reviewed per locale.
- [ ] 24/7 on-call rotation staffed; runbooks tested for all P0/P1 scenarios.
- [ ] Status page live (per surface + aggregate).
- [ ] Per-locale launch gate green (5/5) for all four launch locales.
- [ ] Audit log Merkle chain verification automated.
- [ ] Log-stream IAM isolation test green in CI.
- [ ] Web CSP contract test green; per-request nonce verified.
- [ ] Web PWA + `web-crisis` offline-capable per Playwright network-interception test.
- [ ] axe-core WCAG 2.2 AA (AAA on clinician) green across all 4 locales.
- [ ] PR + marketing ready in all 4 launch locales.

### Phase 2 gate → Phase 3

- Launched publicly on all 6 target origins; onboarded ≥ 10k users across mobile + web within 60 days of launch.
- Retention D30 > 30%; D90 > 18% (measured per-surface and per-locale; no locale below 80% of en baseline).
- WUH stable across cohort.
- Paid conversion > 4.5% at 30 days.
- Zero P0 incidents in first 45 days.
- Web SLOs met: LCP ≤ 2.0s, INP ≤ 150ms, CLS ≤ 0.05 on marketing; 99.95% on `web-app`; 99.99% on `web-crisis`.
- Clinician alpha: ≥ 10 clinicians onboarded, ≥ 50 patient links established, zero unauthorized-scope incidents.
- Enterprise pilot: ≥ 2 paying pilots in production.

---

## 5. Phase 3 — Expand (Months 15–24)

### Goal
Bring clinician and enterprise surfaces from alpha/pilot to **GA with self-serve SSO/SCIM**; add a second behavioral vertical; expand locales; mature ML.

### Major initiatives

#### E1 — Enterprise GA
- Self-serve SAML 2.0 + OIDC SSO via Clerk Enterprise (`14 §8`).
- SCIM 2.0 provisioning for automated lifecycle (create, update, deactivate).
- Reference integrations: Okta, Entra ID (Azure AD), Google Workspace, Ping, OneLogin.
- Enterprise analytics portal with k-anonymity ≥ 5 + differential privacy noise at the SQL view layer (`13 §7`).
- Billing: PMPM via invoice + Stripe.
- Quarterly re-identification red-team exercise; findings remediated before ship.

#### E2 — Clinician portal GA
- Public onboarding + billing (clinician-self-pay tier).
- Patient linking + consent workflow at scale.
- FHIR R4 Observation exports + HL7 v2 ORU bundles (`03 §21`).
- HIPAA-compliant audit trail for clinician views (every PHI read logged to `audit.log`, 7-year retention).
- Messaging (clinician ↔ patient) with safety classifier inline.

#### E3 — Second vertical
- Cannabis (leveraging alcohol content + methodology; adaptation by Clinical Content Lead).
- New tool variants, content adaptation, clinician advisor review.
- Cross-vertical transfer learning validated (bandit priors and urge-predictor adaptation).

#### E4 — Additional locales & regional expansion
- **eu-central-1 infrastructure** with data residency controls (EU users never cross Atlantic).
- DPO appointed; DPIAs for EU data refreshed.
- Additional locales: `de` (German), `es` (Spanish; es-US + es-MX variants), `pt-BR` (Brazilian Portuguese).
- GDPR DSR tooling hardened; Right-to-be-Forgotten flow end-to-end tested across mobile + web + analytics warehouse.

#### E5 — ML maturity
- Federated learning opt-in pilot.
- Bandit retrained with 12 months of production data.
- Urge predictor accuracy + calibration improvements; calibration reviewed per locale (psychometric baseline differs across cultures).
- Personalization adapter pattern in production (one model, per-user adapter).

### Phase 3 gate → Phase 4
- 400k+ paid users across locales.
- Enterprise ARR > $3M.
- 5+ named clinical advisors + peer-reviewed methodology paper submitted.
- Revenue run-rate supports clinical SKU investment.
- **SOC 2 Type II report achieved.**
- No locale falling below 80% retention of en baseline after 6 months in market.

---

## 6. Phase 4 — Clinical (Months 24–36)

### Goal
Pursue FDA clearance for a prescription-only version of the product (De Novo or 510(k) pathway).

### Major initiatives

#### C1 — Clinical trial infrastructure
- IRB-approved RCT protocol.
- Trial recruitment + screening platform (web-app extension).
- Endpoint tracking + adjudication.
- Trial management platform integration (Medable / Protego).

#### C2 — Quality management system
- **ISO 13485** adoption.
- Design history file for clinical product.
- Risk management file (**ISO 14971**).
- Clinical evaluation plan + report.
- **IEC 62304** software lifecycle processes.

#### C3 — Software of Medical Device (SaMD)
- Segregated "clinical product" build pipeline.
- Version-locked intervention policy + models; frozen per submission.
- Change-controlled documentation.
- Regulatory-grade release procedures with full trace from user story → code → test → deployment.

#### C4 — Reimbursement infrastructure
- Payer integration (PBM + medical benefits).
- CPT code alignment.
- Patient-access support tooling.

### Phase 4 gate → Phase 5
- FDA submission accepted.
- Trial endpoints met (primary + secondary).
- PMPM or reimbursed revenue live.
- Cross-product learning model meaningful (20%+ cold-start lift for new vertical).

---

## 7. Phase 5 — Platform (Months 36–60)

### Goal
Become the default behavioral OS layer across multiple verticals + geographies.

### Major directions
- Additional verticals: porn, binge eating, compulsive shopping, doomscroll.
- Additional regions: UK, AU, CA, JP, IN (new locales via the same per-locale launch gate framework).
- Cross-product moat: single platform serves multiple behavior categories with shared signal + intervention primitives.
- Employer / health-system strategic accounts.
- Researcher API (BAA-scope) — academic collaboration with differential-privacy-protected queries.
- Multi-vertical federated learning in production.

No detailed milestone breakdown at this range — roadmap at a 24-month horizon is better planned from within Phase 4.

---

## 8. Cross-cutting Themes

### 8.1 Reliability

Each phase has an explicit **reliability bar**:

| Phase | Overall | Crisis path (T3) | Notes |
|-------|---------|------------------|-------|
| Phase 0 | 99% | — | Internal only |
| Phase 1 | 99.5% | 99.9% | Closed beta; T3 still measured even though surface is small |
| Phase 2 (launch) | 99.9% | **99.99%** | 99.99% from v1.0 on mobile + `web-crisis` — not deferred |
| Phase 3+ | 99.95% | 99.99% | Mature operations |

The safety path (T3) has always been held to the highest bar. From v1.0 onward, **99.99% on the crisis surface is a hard launch gate** — historical roadmaps that deferred this to later phases are superseded.

### 8.2 Technical debt

- 15% of each sprint reserved for tech-debt repair.
- Quarterly "debt budget review" — discrete initiatives sized.
- Debt ledger maintained publicly inside eng.
- Dependency count homeostasis: no new major dependency without justifying removal of an existing one.

### 8.3 Clinical parity

- Every feature that touches user experience ships with clinical review sign-off.
- Clinical advisory quarterly review synced to major feature gates.
- Clinical QA role not optional from Phase 2+.
- **Translation clinical QA** — every locale change to safety/psychometric content requires clinical translator + back-translator + reviewer sign-off (not optional at any phase that supports that locale).

### 8.4 Privacy

- Privacy posture tightens over time, never loosens.
- New integration reviews recorded in privacy ledger.
- Annual privacy audit scope expands each year.
- Analytics (`13_Analytics_Reporting.md`) enforces k-anonymity ≥ 5 and differential privacy on enterprise reports at the **SQL view layer**, not the application layer — application bugs cannot leak.

### 8.5 Model governance

- Each model card updated on any change.
- Cross-phase model registry preserved — historical models available for audit.
- No silent model rollout; all promotions audited + announced internally.
- Safety classifier regressions automatically revert.

### 8.6 Internationalization

- **No machine-translation** on shipped clinical content — ever. Linter enforces.
- New locale = new launch-gate cycle (5 criteria from §4 I4).
- Psychometric instrument translations must be published/validated; gaps trigger instrument substitution, not "ship anyway."

---

## 9. Dependency Graph

Critical cross-team dependencies that can bottleneck the roadmap:

```
Signal module ─┐
               ├─► Intervention bandit ─► Outcome feedback loop
ML state model ┘       ▲
                       │
                Clinical content ─── Clinical QA ─── Translation QA (per locale)
                       │                  │                    │
                LLM prompt lib            Safety classifier    │
                       │                  │                    │
                       ▼                  ▼                    ▼
                  User features ─────► Release gate ◄──── Locale launch gate (×4)

Auth (Clerk + KMS EdDSA) ──► Session ──► Every endpoint (transitive block)
Logging streams (4 streams, IAM-isolated) ──► Every write site
Observability ──► SLO gate ──► Release

Design system ──► Mobile + 5 Web apps (shared primitives)
i18n catalog    ──► Mobile + 5 Web apps (single source of truth)
Safety directory ──► Mobile + `web-crisis` (deterministic T3)
```

**Known serial bottlenecks:**
1. Clinical content authoring — staggered across Phase 1/2 so engineers aren't blocked.
2. Clinical translation — gated by validated psychometric translations; Phase 2 locale launch requires them to be in hand by month 11 to leave time for in-product QA.
3. SOC 2 audit windows — started in Phase 2, achieved in Phase 3; cannot be compressed below the auditor's observation window.

---

## 10. Hiring ↔ Capability

A map of which engineering capabilities unlock which phase:

| Capability | Unlocked by | Timing |
|-----------|-------------|--------|
| RN + iOS native | Senior iOS + Android | Phase 1 start |
| Modular monolith | Senior Backend | Phase 1 start |
| On-device ML | Senior ML | Phase 1 Month 4 |
| Observability + infra | Part-time CTO → Dedicated Infra hire | Phase 1 Month 8 |
| **Web (Next.js, 5 apps)** | Senior web lead + 1 mid | Phase 1 Month 6 |
| **i18n + RTL engineering** | Senior i18n/accessibility engineer | Phase 1 Month 6 |
| **Clinical translation program** | Clinical Translation Lead + external translator network | Phase 1 Month 7 |
| Clinician portal (GA) | +1 backend + senior designer | Phase 3 |
| Enterprise SSO/SCIM (self-serve) | +1 backend | Phase 3 |
| Federated learning | Dedicated ML infra hire | Phase 3 |
| Clinical trial infra | +1 clinical operations | Phase 4 |
| FDA submission | Regulatory lead (+ external QMS consultancy) | Phase 4 |

---

## 11. Risk Register (technical)

Top 15 technical risks with mitigations:

1. **T3 SLO regression** → Continuous synthetic monitoring on all 3 surfaces (iOS, Android, `web-crisis`) + release gate hard block.
2. **Safety classifier false negatives** → Dual-signal (classifier + keyword), monthly advisor review, per-locale validation because failure modes differ across languages.
3. **On-device ML battery drain** → Battery budget enforced in CI synthetic day.
4. **HealthKit / Health Connect API deprecations** → Track beta releases; maintain abstraction layer.
5. **Cross-surface parity bugs** (mobile vs web) → Shared E2E matrix; feature parity gate in release checklist.
6. **LLM cost explosion** → Quotas + degraded mode + prompt caching. LLM never on safety path so outage ≠ safety outage.
7. **Federated learning privacy bug** → Shadow mode pre-launch; formal protocol review.
8. **Subpoena over-compliance** → Data minimization; legal counsel on response playbook.
9. **Clerk outage impact** → Cached sessions + server-side session fallback; migration plan drafted.
10. **AWS region outage** → DR runbook + quarterly drills + active/active Y3 evaluation.
11. **Validated psychometric translation gap** (e.g. DTCQ-8 AR/FA) → Pre-launch audit of every locale × instrument; substitute (PHQ-9/GAD-7/WHO-5 have solid translations) rather than ship an unvalidated score.
12. **RTL regression** → Per-locale Playwright + per-locale mobile snapshot tests in CI; `forceRTL` debug menu for manual QA.
13. **Audit log tampering** → S3 Object Lock compliance mode + Merkle chain + writer-role-has-no-DeleteObject + quarterly tamper test.
14. **Refresh token family leak / reuse** → Reuse detection kills entire family + forces re-auth + logs to `security.log`; property test ≥ 200 combinations of reuse scenarios (`09 §20`).
15. **Enterprise report re-identification** → k-anon + DP enforced at SQL view layer; quarterly red-team on enterprise reports with findings remediated before ship.

---

## 12. Quarter-by-Quarter (Phases 0–3)

| Quarter | Months | Milestones |
|---------|--------|------------|
| Q1 | M1–3 | Phase 0: human-in-the-loop validation, staff iOS app, waitlist, seed close |
| Q2 | M4–6 | RN scaffolding; modular monolith foundation; HealthKit ingest; first ML state model; i18n + logging harness in place (en only); web-app internal skeleton |
| Q3 | M7–9 | Closed beta (300 users, en); bandit v0.5; voice pipeline; SOC 2 readiness underway; clinical translation program kickoff (fr/ar/fa); `web-crisis` static origin live in staging |
| Q4 | M10–12 | Locale content translation + clinical QA (fr/ar/fa); RTL engineering; clinician alpha begins; pen test; SOC 2 Type I audit opens |
| Q5 | M13–14 | v1.0 launch prep; per-locale launch gates green; app-store submissions per locale; PR ramp; public launch |
| Q6 | M15–18 | Post-launch stabilization; enterprise pilot → GA prep; clinician alpha → GA prep; additional locale scoping; SOC 2 Type II observation window runs |
| Q7–Q8 | M19–24 | Clinician GA + Enterprise GA; second vertical scoping; eu-central-1 infrastructure; SOC 2 Type II report; additional locales (de, es) |

---

## 13. Exit Criteria Summary

Every phase has these discrete exit criteria (phase-specific values in each section):

- **Reliability:** meets tier-specific SLOs, including T3 99.99% from v1.0.
- **Safety:** classifier recall bar met + clean incident history + per-locale validation where the locale is live.
- **User:** retention + WUH targets met (per-surface and per-locale).
- **Business:** revenue / user / partnership targets met.
- **Team:** hiring backfill to required capability level.
- **Locale parity (from Phase 2+):** every shipped locale passes its 5-criterion launch gate continuously — not just at launch.
- **Compliance:** audit posture required for the phase is in flight or achieved (SOC 2 Type I at launch; Type II by end of Phase 3).

No phase advances without all of these. We've seen too many organizations "hit the date" and leave gaps that explode later. Gates exist to prevent that.
