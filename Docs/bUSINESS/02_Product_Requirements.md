# Product Requirements Document (PRD) — Discipline OS v1.0

**Status:** v1.0 production requirements (not a draft scoping document)
**Audience:** Product, Engineering, Design, Clinical, Compliance, Localization
**Surfaces at launch:** iOS · Android · Web (5 sub-surfaces — marketing, app, clinician alpha, enterprise pilot, crisis-static)
**Locales at launch:** `en`, `fr`, `ar`, `fa` (Arabic + Persian are RTL; strict per-locale launch gate — see F-16)
**Vertical at launch:** alcohol (second vertical — cannabis — in Phase 3 per `../Technicals/11_Technical_Roadmap.md`)
**Specs referenced:** `../Technicals/13_Analytics_Reporting.md`, `../Technicals/14_Authentication_Logging.md`, `../Technicals/15_Internationalization.md`, `../Technicals/16_Web_Application.md`

---

## 1. User Personas

### Persona 1 — "The High-Functioning Controller" (primary at launch)
- 28–45, urban/suburban US
- Mid-to-senior professional, income $80k–250k
- Values performance, agency, evidence
- Primary struggle: impulse that contradicts stated goals (alcohol, work-delay, anger)
- Tried: therapy (inconsistent), apps (bounced after 30 days), books
- Uses: Apple Watch / Fitbit / Oura, Apple Health, calendar
- Willing to pay: $10–25/month for *real* results
- Acquisition channel: Podcast ads, long-form YouTube, founder-thesis content

### Persona 2 — "The Recovery Graduate"
- 30–60, has done formal treatment or AA/SMART
- Seeks post-program support without losing community ties
- Primary need: moment-of-decision help between meetings
- Does not want: to replace their existing program
- Pain: existing apps feel juvenile or shame-adjacent

### Persona 3 — "The Quiet Struggler"
- 22–40, high privacy sensitivity
- Struggles with urges they haven't told anyone about (porn, self-harm adjacent, binge eating)
- Needs: strong privacy, stigma-free UI, no community
- Critical feature: app-lock, generic icon, no push preview on lock screen

### Persona 4 — "The Clinician-Prescribed" (Year 2+)
- Patient of an integrated care team
- Uses app between therapy sessions
- Therapist has limited, consented dashboard access
- Payment: reimbursed or employer-sponsored

### Persona 5 — "The Enterprise Employee" (Year 2+)
- Covered by employer EAP
- Privacy-first flow (employer sees aggregate only, never individual data)
- Onboarded through company benefits portal

---

## 2. Core Use Cases (v1.0 Launch Scope)

### UC-01: First-Time Onboarding (Consumer)
**Goal:** Get user to baseline + first intervention within 10 minutes.
**Steps:**
1. Install, open app → privacy-first welcome (3 slides max)
2. Behavior selection (v1.0: alcohol, with "more coming" preview)
3. Goal setting (reduce / abstain / maintain)
4. Signal permissions (HealthKit, notifications, optional location geofence)
5. Baseline assessment (5-minute: history, triggers, existing support)
6. First if-then plan creation (Gollwitzer implementation intention)
7. First coping tool walkthrough (Box Breathing — lowest friction)
8. Set check-in cadence (morning intention / evening review)
9. Show dashboard with initial state

**Success criteria:**
- ≥80% of installers complete onboarding
- ≥50% complete first coping tool
- ≥70% grant notification permission
- ≥40% grant HealthKit permission

### UC-02: Active Urge — User-Initiated SOS
**Goal:** Deliver intervention in <2 seconds from tap.
**Steps:**
1. User taps SOS (widget, watch complication, or main app)
2. App launches directly into Tier 3 UI (skip menu)
3. Single-button starting workflow (default: Urge Surfing or last-used)
4. Deterministic flow, no choice screens
5. Post-workflow: 2-tap "did this help?" + optional voice note
6. Logged, added to pattern analytics, bandit updated

**Critical SLO:** <800ms cold launch on SOS path.

### UC-03: Active Urge — System-Initiated
**Goal:** Predict urge and arrive before user opens app.
**Trigger:** State estimator confidence ≥ threshold + nudge budget available.
**Steps:**
1. Push notification: "Noticed your energy's low and it's a Friday 6pm — quick 60s check-in?"
2. Notification action: swipe to open 60s tool OR dismiss
3. If dismissed 2× in a row for this context, suppress for 7 days
4. If opened, same flow as UC-02

### UC-04: Daily Check-In
**Goal:** 60-second ritual, morning + evening.
**Morning (voluntary):** intention set ("My target for today is…"), optional if-then plan review.
**Evening (voluntary):** urge dial, emotion picker, one reflection prompt (adaptive from today's events).

### UC-05: Relapse Event
**Goal:** Turn the hardest moment into the best engagement moment.
**Trigger:** User taps "I lapsed" OR state estimator + user confirmation.
**Steps:**
1. Immediate compassion screen (single screen, no judgment copy): "That's hard. You're here — that matters."
2. 24-hour reduced-friction mode: smaller targets, more supportive tone
3. Functional-analysis workflow (CBT-structured, 3–5 min): what preceded, what cue, what thought, what behavior, what outcome, what alternative
4. Continuous streak: honestly reset (shown on dashboard, de-emphasized)
5. Resilience streak: **not reset** (urges handled remains intact)
6. Updated trigger map with new context cluster
7. Optional: offer accountability contact / crisis line
8. 72-hour elevated support: extra check-ins, supportive push, pre-written reflection prompts

### UC-06: Pattern Surfacing
**Goal:** Deliver insight only when actionable.
**Trigger:** Weekly, gated on confidence threshold.
**Steps:**
1. In-app insight card (never forced notification): e.g., "Your urge intensity drops 40% after 7+ hours of sleep"
2. Actionable recommendation attached
3. User can dismiss or commit (converts to new if-then plan)

### UC-07: Voice Journal
**Goal:** Reduce journaling friction at peak stress.
**Steps:**
1. Tap voice-journal action
2. Record (client-side)
3. On-device transcription (Whisper-small)
4. On-device summarization into CBT-structured fields (situation / thought / feeling / behavior / outcome)
5. User edits, saves (E2E encrypted)
6. Optional structured insight extraction

### UC-08: Accountability Contact Flow
**Goal:** Friction-reduced outreach at peak vulnerability.
**Steps:**
1. User pre-configures 1–3 contacts during onboarding or later
2. Pre-written message templates (editable)
3. In urge moment: tap contact → confirm → send SMS via native share
4. Logged without content (privacy)
5. Optional "they replied" ack

### UC-09: Clinician Dashboard (launch alpha; GA in Phase 3)
**Goal:** Bridge the 6-days-between-sessions gap. Surface: `clinicians.disciplineos.com`, invite-only at v1.0.
**Steps:**
1. Patient invites clinician by code (scope-gated: `full` / `summary` / `outcomes-only`)
2. Clinician signs in via passkey or SSO (step-up auth required to view patient summary — 5-minute freshness, see `14_Authentication_Logging.md §7`)
3. Clinician sees: weekly urge count, intervention efficacy, relapse events (count, not content), patterns, psychometric trajectories (with confidence + reliable-change markers, `13_Analytics_Reporting.md §6`)
4. Patient content under envelope encryption; voice transcripts never visible unless patient explicitly shares a specific session
5. Revocable at any moment by patient; clinician receives revocation notice
6. Every PHI view logged to `audit.log` (7-year retention, S3 Object Lock compliance mode)
7. PDF, FHIR R4 Observation, and HL7 v2 ORU export formats available

### UC-10: Enterprise Admin (launch pilot; GA in Phase 3)
**Goal:** Organization rolls out to employees; admin sees aggregates only. Surface: `enterprise.disciplineos.com`, hand-rolled onboarding for named pilots at v1.0; self-serve SSO/SCIM in Phase 3.
**Steps:**
1. SSO via SAML 2.0 or OIDC (Clerk Enterprise IdP); SCIM 2.0 provisioning in Phase 3
2. Admin dashboard: enrollment count, aggregate engagement, aggregate outcomes (k-anonymity ≥ 5, differential-privacy noise at the SQL view layer — enforcement lives in the database, not the app; see `13_Analytics_Reporting.md §7`)
3. Never individual data, never identifiable, never relapse event content
4. Minimum cohort size per slice: 5 members; below threshold = "not enough data to report"
5. Quarterly re-identification red-team exercise with findings remediated before next reporting cycle
6. Billing: PMPM invoicing via Stripe + contract

---

## 3. Feature Specifications

### F-01: Signal Layer

**Active signals:**
- Urge dial (0–10, haptic-snapped, 3-second capture)
- Emotion picker (6 options: craving, anxiety, anger, sadness, boredom, shame)
- 1-line text note (optional)
- Voice note (15s max, optional)
- HALT check (quad-toggle: Hungry / Angry / Lonely / Tired)

**Passive signals:**
- HealthKit / Google Fit: HRV, heart rate, sleep duration + stage, active energy
- Wearable SDKs (opt-in): Oura, Whoop, Fitbit → detailed HRV + stress proxies
- Phone telemetry (opt-in, on-device only): screen unlocks per hour, app-switching entropy, typing cadence variance
- Location class (not raw coords): geofence-derived category (home / work / "risk zone")
- Calendar density (event count / free blocks, opt-in)
- Time-of-day + day-of-week
- Weather (via user location bucket)

**Acceptance criteria:**
- Active input ≤5 seconds to complete
- Passive signals never transmit raw biometrics to cloud
- Permission requested only in-context, never bundled
- Per-signal granular opt-out
- Data retention: user-configurable (default 180 days)

### F-02: State Estimation Engine

**Outputs (internal model state):**
- `urge_intensity` ∈ [0, 10] with volatility and 2h trajectory
- `relapse_risk_next_2h` ∈ [0, 1], `next_8h`, `next_24h`
- `emotion_state` ∈ categorical + intensity
- `halt_state` (4 bools)
- `baseline_distance` (σ units from personal rolling baseline)
- `context_class` (home / work / risk zone / transit / other)

**Architecture:**
- On-device LSTM (sequence length 72h, inference every 5 min in foreground / 20 min in background)
- Personal baseline maintained locally (30-day rolling window)
- Federated learning weekly update to shared prior model

**Acceptance criteria:**
- <400ms inference time on median device (iPhone 12-class)
- <2% battery draw per day
- False positive rate on T3 recommendation <8%
- Explainability: each state output has top-2 contributing signals

### F-03: Intervention Orchestrator

**4-tier policy:**

| Tier | Trigger | UI | Max frequency |
|------|---------|----|--------------:|
| T0 | Ambient | Subtle home-screen indicator, no interruption | — |
| T1 | Urge rising | Push: "quick 60s?" | Budget-capped per day (default 4) |
| T2 | Urge elevated | Structured 90–180s workflow | User-initiated or predicted high-risk |
| T3 | Crisis / SOS | Full-screen, 1 button, reduced-choice | Always available |
| T4 | Severe (self-harm ideation) | Deterministic handoff to crisis line | Immediate |

**Nudge budget:**
- Hard cap per day (default 4, user-configurable 0–8)
- Cooldown between nudges (default 90 min)
- Context suppression: if 2 consecutive same-context nudges dismissed, suppress that context 7 days

**Tool selection (T2+):**
- Contextual bandit (per user, per context, per tool) with population prior
- Exploration bound: at most 15% deviation from best-known tool in any context
- Never explore at T3 — use highest-confidence tool only

**Acceptance criteria:**
- T3 launch-to-first-button <800ms cold
- Notification permission retention >70% at D30
- Nudge dismissal rate <35% (above = we're over-delivering)

### F-04: Coping Toolkit

Minimum set at v1.0:

| Tool | Duration | Evidence base | Indication |
|------|----------|--------------|------------|
| **Urge Surfing** | 2–10 min | MBRP (Marlatt, Bowen, Witkiewitz) | Cravings, compulsions |
| **Box Breathing** | 90 s | Autonomic regulation research | Acute anxiety, pre-craving |
| **4-7-8 Breathing** | 60 s | Vagal tone | Rapid de-escalation |
| **TIPP** (Temperature / Intense exercise / Paced breathing / Paired relaxation) | 3–5 min | DBT (Linehan) | Crisis-grade distress |
| **Cognitive Defusion** | 2–5 min | ACT (Hayes) | Persistent thoughts |
| **Implementation-Intention Replay** | 30 s | Gollwitzer | Known-context pre-urge |
| **Body Scan** | 5–15 min | MBSR | Post-escalation reset |
| **Contact-a-Human** | Variable | Accountability research | Any tier |
| **Self-Compassion Break** | 2 min | Neff, Breines | Post-lapse, shame-state |

**Each tool spec includes:**
- Script (audio + text)
- Duration range
- Indication / contraindication
- Entry state requirements
- Exit state capture (helped / neutral / didn't help / made worse)
- Voice-first alternative (where possible)

**Content ownership:**
- All scripts written by licensed clinicians (contract)
- Annual review cycle
- Attribution to underlying research visible in-app ("Based on [paper, year]")

### F-05: Relapse Engine

**Pre-relapse window:**
- Elevated risk detected → proactive T1 nudge + optional accountability outreach offer
- Temporary adjustment to environmental suggestions ("Consider lowering exposure today")

**Relapse event:**
- One-tap report
- No streak shaming
- Immediate compassion screen
- Optional: why it happened (free-text or voice)
- Continuous streak: honestly reset
- Resilience streak: **not reset**

**Post-relapse protocol (24–72h):**
- Reduced-friction mode (simplified UI)
- Automatic lowering of trigger-exposure recommendations
- Elevated supportive check-in cadence
- Functional-analysis workflow (required within 48h for best pattern learning)
- Optional: connect-with-sponsor / counselor / crisis line

**Explicit design rules:**
- No loss aversion copy ("don't lose your progress")
- No comparative framing ("most users avoid relapse")
- No "failure" / "broken" / "ruined" vocabulary ever

### F-06: Awareness Journal

**Structured mode (default):**
- CBT thought-record: situation / automatic thought / emotion + intensity / behavior / outcome / alternative thought
- Prompt is adaptive based on context (post-urge prompts differ from daily review)

**Voice-first mode:**
- Record up to 120s
- On-device transcription (Whisper-small)
- LLM-assisted structuring into CBT fields (user reviews before save)
- Raw audio never leaves device unless user explicitly exports

**Unstructured mode:**
- Plain free-form entry (power-user option)

**Storage:**
- E2E encrypted (client-side key, derived from user passphrase + device secret)
- Server sees only pattern-extracted metadata, never content

### F-07: Progress Dashboard

**Three views:**

1. **Today**
   - State indicator (calm / elevated / crisis-nearby)
   - Today's urges logged / handled
   - Next recommended action (if any)
   - Quick-access to last-used tool

2. **Patterns**
   - 7-day urge intensity heatmap
   - Top 3 trigger contexts (time, location, emotion)
   - Tool efficacy ranking (per user)
   - HALT-state correlation

3. **Trajectory**
   - Continuous streak (shown, de-emphasized)
   - **Resilience streak** (primary, visually dominant)
   - 30-day urge volume trend
   - Intervention efficacy trend
   - Milestone markers (first 10 urges handled, first month of logging, etc.)

**Rendering rules:**
- No red "failure" colors anywhere
- No comparison to other users
- Insights shown only when confidence > 0.7

### F-08: Personalization Engine

**Inputs:**
- Per-user historical state + intervention + outcome tuples
- Population prior (aggregated, federated)
- User-declared preferences
- Content engagement signals

**Outputs:**
- Next-best intervention for current state
- Optimal nudge timing for upcoming windows
- Content recommendation rank
- Daily check-in time suggestion

**Architecture:**
- Contextual bandit (LinUCB or Thompson sampling)
- Reward = weighted combination of:
  - Self-reported helpfulness (5-point)
  - Urge subsidence (dial drop over 15 min)
  - No-relapse flag (24h window)

**Guardrails:**
- Never deploy unvalidated intervention at T3
- Never recommend intervention user has marked "don't suggest"
- Exploration capped at 15% deviation
- Weekly retraining cadence

### F-09: Content Delivery System

- Microlearning modules (60–180s)
- Surfaced in-context, not pushed
- Deeper depth unlockable as user engages
- No "Lesson 37 of 100" guilt architecture
- Clinically reviewed quarterly
- Accessibility: screen-reader complete, captions mandatory

### F-10: Reminder & Nudge System

- Context-triggered, not clock-based (except explicit user-chosen check-in time)
- Budget-capped (default 4/day)
- Adaptive: suppress on dismissal patterns, surface on engagement
- Never shame-adjacent copy
- User can set nudge-free windows (work blocks, sleep)

### F-11: Privacy & Safety Features (Product-Visible)

- **App-lock:** biometric or PIN to open
- **Generic icon + name mode:** app appears as "Reflect" or "Compass"
- **Hidden from recents / task switcher** (iOS + Android)
- **Quick-erase:** 3-tap full local data wipe
- **No-cloud mode:** opt out of all cloud sync (degrades personalization, honest tradeoff disclosure)
- **Export my data** (JSON + PDF)
- **Delete my account** (full purge, 30-day grace period)

### F-12: Crisis Escalation (T4)

**Triggers:**
- User explicit: "I'm having thoughts of self-harm" button
- Pattern-detected: NLP on journal/voice flags concerning content (clinically-validated classifier, ≥98% recall)
- User dials crisis help

**Response:**
- Deterministic flow — **never LLM-generated; never a network round-trip on the safety path**
- Catalog bundled on-device (mobile) and statically pre-rendered (`crisis.disciplineos.com`) so loss of connectivity does not degrade the surface
- Immediate display of **per-locale hotline directory** (see F-16 and `../Technicals/10_Integrations.md §22`):
  - Examples: en-US → 988; en-GB → 116 123 (Samaritans); fr-FR → 3114; ar-SA → 920033360; fa-IR → Omid Behzisti 1480; en-CA → 988
  - Directory is per-country × per-locale; quarterly verification with clinical sign-off
- Text Line (where available in the user's country)
- Local emergency number ("911", "112", "999", "15" etc. rendered by locale)
- User-configured emergency contact
- Follow-up check-in 24h later (sensitive copy, opt-out easy)
- Event logged to `safety.log` (10-year retention + legal hold) for clinical review; if user has clinician connection, clinician receives notice per patient-selected scope

**Legal:** Clear disclaimers; never claim to provide medical care; copy per locale reviewed by local legal counsel.

### F-13: Psychometric Assessment System

**Purpose:** Administer validated self-report instruments at appropriate cadence to produce a clinical-grade trajectory per user. Spec: `../Technicals/13_Analytics_Reporting.md §6`.

**Instruments (launch):**
- PHQ-9 (depression) + PHQ-2 (screening)
- GAD-7 (anxiety) + GAD-2 (screening)
- AUDIT-C (hazardous drinking screen) + AUDIT (full)
- DAST-10 (substance use)
- PSS-10 (perceived stress)
- WHO-5 (wellbeing)
- DTCQ-8 (drug-taking confidence) — where validated translation available
- URICA (stages of change)
- Readiness Ruler
- C-SSRS (suicide severity) — clinician-gated paths only

**Administration:**
- Cadence: baseline at onboarding, then 2-weekly for primary (PHQ-9, GAD-7, AUDIT/AUDIT-C), 4-weekly for supplementary
- Adaptive skip logic for PHQ/GAD (answer PHQ-2 first, escalate to PHQ-9 only on positive screen)
- C-SSRS triggered only on concerning content in journal or explicit user request; flows only via `safety.log` path
- Pause / defer options (not mandatory)

**Scoring:**
- **`assessment.scoring.correctness` SLI = 100%** — any deviation from published reference table blocks the build
- Scoring functions property-tested against reference rows with citation source in `psychometric_instruments` table
- Version-pinned; score schema migration requires clinical sign-off
- Translations must be validated (published citation recorded); no self-translation for clinical instruments

**Output surfaces:**
- User: trajectory with reliable change index (RCI) shown only when confidence met
- Clinician: trajectory with reference ranges + confidence intervals + test-retest reliability notation
- Internal research: de-identified per HIPAA Safe Harbor, stored in research warehouse

**Acceptance criteria:**
- All 11 launch instruments scored against published reference tables with 100% agreement
- Translation coverage for en/fr/ar/fa matches validated-translation matrix in `../Technicals/15_Internationalization.md §8`
- Gaps (e.g. DTCQ-8 AR/FA) handled by instrument substitution, never unvalidated translation
- Safety-item detection (PHQ-9 Q9, C-SSRS) writes to `safety.log` with zero-drop reliability

### F-14: Reporting & Analytics

**Purpose:** Deliver four audiences their audience-correct view without cross-contaminating privacy levels. Spec: `../Technicals/13_Analytics_Reporting.md`.

**Four surfaces:**
1. **User** — weekly reflection + monthly story + patterns card. Protective framing rules P1-P6 (no loss-aversion, no comparison to population, no "failure" vocabulary). Insights gated by confidence ≥ 0.7 and by RCI where applicable.
2. **Clinician** — trajectory view with reference ranges + reliable-change markers + session-prep summaries (PDF, FHIR R4 Observation, HL7 v2 ORU).
3. **Enterprise** — aggregate dashboards with k-anonymity ≥ 5 + differential privacy (ε = 1.0) enforced at the SQL view layer so application bugs cannot leak. Minimum cohort size: 5.
4. **Internal product** — PHI-free event allow-list shipped to PostHog + server-side ClickHouse analytics.

**Framing rules (user + clinician output):**
- P1: No loss aversion ("don't lose your progress" forbidden)
- P2: No population comparisons ("most users handle this" forbidden)
- P3: No streak shaming (continuous streak de-emphasized; resilience streak primary)
- P4: Confidence gates (insight shown only when confidence ≥ 0.7)
- P5: Clinical terminology reserved for clinician surface
- P6: Non-clinical reframe required for any score shown to user (e.g. PHQ-9 trajectory shown as "how you've been feeling" with validated-score option to expand)

**Out of scope at v1.0:** public research API, researcher BAA-scope warehouse access (Phase 5).

**Acceptance criteria:**
- Framing-rule tests P1-P6 green in CI
- k-anon cohort size gate tested at 3, 5, 10, 25, 100
- DP noise envelope within expected variance range
- Enterprise report byte-identical reproducibility (same inputs → same bytes)
- Quarterly re-identification red-team finding log clean

### F-15: Web Surfaces (5 Next.js apps)

**Purpose:** Parity surface for mobile users + dedicated clinician/enterprise entry points + a crisis origin. Spec: `../Technicals/16_Web_Application.md`.

| Sub-surface | Hostname | At launch |
|-------------|----------|-----------|
| Marketing | `www.disciplineos.com` | Full site, SEO-tuned, LCP ≤ 2.0s / INP ≤ 150ms / CLS ≤ 0.05 |
| Web app | `app.disciplineos.com` | Check-in, journal, tool library, insights, crisis access (parity with mobile where feasible) |
| Clinician portal | `clinicians.disciplineos.com` | Invite-only alpha — patient linking + trajectories + PDF/FHIR/HL7 export |
| Enterprise portal | `enterprise.disciplineos.com` | Pilot only — SSO-mandatory, aggregate reports only |
| Crisis (static) | `crisis.disciplineos.com` | Pre-rendered HTML/CSS/JS, zero network dependency after first paint, 99.99% SLO |

**Feature parity (mobile vs web):**
- Journal, check-in, tool library, insights, psychometric: yes
- Voice journal: mobile only at launch (desktop later)
- Biometric capture (HealthKit, Health Connect): mobile only — web shows manual-entry form
- Push notifications: mobile primary; web via Web Push (VAPID, opt-in)
- Crisis: available on all surfaces; mobile+web-crisis are the primary safety surfaces

**Shared infrastructure (monorepo):**
- `packages/design-system/` — shared tokens, per-platform primitives
- `packages/i18n-catalog/` — single source of truth for all 4 locales
- `packages/safety-directory/` — per-country hotline directory
- `packages/api-client/` — typed client to backend

**Acceptance criteria:**
- All 5 origins live with per-origin CloudFront + WAF
- Strict CSP with per-request nonces on all surfaces
- CSRF double-submit on all state-changing requests
- HSTS preload on all hostnames
- axe-core WCAG 2.2 AA green on `web-marketing` / `web-app`; AAA contrast on `web-clinician`
- Playwright `test_web_sos_is_deterministic` green (no network interception changes T3 outcome)
- PWA offline cache includes crisis content on `web-app`

### F-16: Internationalization (i18n) — en / fr / ar / fa + RTL

**Purpose:** Launch at parity across four locales with strict clinical safety. Spec: `../Technicals/15_Internationalization.md`.

**Launch locales:**
- `en` (English) — default and reference source
- `fr` (French) — LTR, Latin script
- `ar` (Arabic, Modern Standard Arabic) — RTL
- `fa` (Persian, Iranian) — RTL; **requires Vazirmatn** font (not an Arabic-first font); Shamsi calendar option

**Locale negotiation:** user preference > OS locale > `Accept-Language` > default `en`. Persisted on `users.locale`.

**Typography:**
- Inter (Latin scripts)
- IBM Plex Sans Arabic (Arabic)
- Vazirmatn (Persian)
- 1.15× type scale + 1.6 line-height for Arabic + Persian

**Digits:** Latin always for clinical scores (PHQ-9, GAD-7, etc.) enforced by formatter. User-configurable for non-clinical display (`users.digit_preference`).

**Calendars:** Gregorian primary; Hijri (Arabic locales) and Shamsi (Persian locale) as secondary / display-only options (`users.calendar_preference`).

**RTL rules:** Layout mirrors, icon directions reviewed per-icon (back arrow flips; play button does not; charts x-axis mirrors). CI gate: no physical-direction CSS tokens in web code (`paddingLeft` etc. forbidden — use `paddingInlineStart`).

**Translation workflow:**
- Clinical translator → back-translator → reviewer sign-off for all safety/psychometric content
- Source-of-truth catalog in `packages/i18n-catalog/`
- Lokalise (Enterprise BAA) for translator collaboration
- **No machine translation on shipped content** — CI linter fingerprints outputs
- Arabic plural coverage: all 6 CLDR categories (zero/one/two/few/many/other) required for any pluralized string

**Per-locale launch gate (5 criteria, see roadmap §4 I4):** safety content reviewed, psychometric validated translations attached, hotline directory ≤ 90-day freshness, typography validated on golden devices, native-speaker QA pass on onboarding + crisis.

**Acceptance criteria:**
- All 4 locales ship at parity; no locale "coming soon" in the UI
- Playwright smoke passes in en + ar (proves LTR + RTL)
- axe-core green in all 4 locales
- Font availability tested on low-end Android, iPhone SE, desktop Safari/Chrome/Firefox
- MT-fingerprint heuristic green on all translated safety strings

### F-17: Help Center

**Purpose:** Intensive in-app + web help content that teaches mechanism, not just UI. Spec: `../Docs/Help/` (authored separately).

**Content scope (v1.0):**
- Getting started (onboarding reinforcement)
- Understanding the 4-tier intervention system (T0-T4)
- Each coping tool explained with evidence base + when-to-use (urge surfing, TIPP, box breathing, etc.)
- Psychometric assessments explained (what PHQ-9 measures, why we use it, what a trajectory means)
- Relapse protocol in plain language
- Safety resources per country + locale
- Privacy & data controls (how to export, quick-erase, account deletion)
- FAQ

**Surfacing:**
- In-app (mobile) as a dedicated Help tab
- On `web-app` under `/help`
- On `www-marketing` under `/help` (public-readable subset, no PHI-adjacent content)
- Content deep-linkable from tool screens (context-sensitive help icon)

**Authoring discipline:**
- English source; fr/ar/fa via clinical translator workflow per F-16
- Citations to peer-reviewed sources where clinical claims are made
- Reviewed quarterly by Clinical Content Lead
- No machine translation

**Acceptance criteria:**
- Help tab green in all 4 locales at launch
- Public Help pages indexed and LCP ≤ 2.0s
- Reading-level check (Flesch-Kincaid target grade ≤ 9 for user-facing pages)

### F-18: Methodology Whitepapers

**Purpose:** Transparency moat — publish research-grade documentation of methodology, clinical evidence base, privacy architecture, safety framework, and research roadmap. Spec: `../Docs/Whitepapers/`.

**Whitepapers (v1.0):**
1. **Methodology** — how the closed-loop intervention model works; references Marlatt & Gordon 1985 RP, Nahum-Shani et al. 2018 JITAI, Gollwitzer implementation intentions.
2. **Clinical Evidence Base** — psychometric instruments used and their validation (Kroenke 2001 PHQ-9, Spitzer 2006 GAD-7, Bush 1998 AUDIT-C, Cohen 1983 PSS, Topp 2015 WHO-5, plus translation-specific validations — AlHadi 2017 Arabic PHQ-9, Dadfar & Kabir 2016 Persian PHQ-9, etc.)
3. **Privacy Architecture** — envelope encryption, E2E for journal, k-anonymity, differential privacy, audit immutability.
4. **Safety Framework** — deterministic T3/T4, safety classifier validation, per-locale safety content, clinical escalation protocol.
5. **Research Roadmap** — planned RCTs, IRB process, publication goals.

**Hosting:**
- `www.disciplineos.com/research` — public PDFs + HTML
- Every clinical claim linked back to its whitepaper

**Acceptance criteria:**
- All 5 whitepapers published before v1.0 launch
- Clinical Advisory Board sign-off on Methodology + Clinical Evidence Base
- Citations real, resolvable, and DOI-linked where possible
- Reviewed + updated annually

---

## 4. User Flow Diagrams (Textual)

### Onboarding flow
```
Install → Welcome (3 slides) → Privacy posture → Behavior selection →
Goal setting → Permissions (health / notifications / optional location) →
Baseline assessment → First if-then plan → First tool (box breath) →
Check-in cadence → Dashboard first-view → Push-permission nudge
```

### Active urge flow (T3 SOS)
```
[Widget tap / watch complication / home SOS] →
T3 full-screen (< 800ms) → Single large "Start" button →
[Default tool workflow] →
Exit state capture (2 taps) →
Optional voice note →
Pattern analytics updated →
[Dashboard return]
```

### Relapse flow
```
"I lapsed" tap → Compassion screen → Reduced-friction mode enabled →
(within 48h) Functional analysis workflow →
Elevated support cadence begins →
72h later: automatic cadence return + pattern report offered
```

---

## 5. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance (mobile)** | T3 cold launch < 800ms; warm < 200ms; ML inference < 400ms median |
| **Performance (web-marketing)** | LCP ≤ 2.0s; INP ≤ 150ms; CLS ≤ 0.05 |
| **Performance (web-app)** | TTI ≤ 3.0s; LCP ≤ 2.5s |
| **Reliability (overall)** | 99.9% availability at launch |
| **Reliability (T3 crisis path)** | **99.99% from v1.0** on mobile + `crisis.disciplineos.com` (not deferred) |
| **Security** | TLS 1.3 externally; AES-256 at rest; envelope encryption with per-user DEK; WebAuthn/passkeys primary; TOTP fallback; EdDSA Ed25519 JWT via AWS KMS |
| **Auth** | Mandatory MFA; 15-min access + 30-day rolling refresh; family rotation with reuse detection; step-up for sensitive actions (5-min freshness) |
| **Logging** | 4-stream isolation (app/audit/safety/security) with IAM-isolated writer roles; audit log S3 Object Lock compliance mode; zero PHI in `app.log` |
| **Privacy** | SOC 2 Type I at launch, Type II by end of Phase 3; HIPAA BAA with all processors; GDPR/UK DPA compliant from launch; k-anonymity ≥ 5 + DP on enterprise reports at SQL view layer |
| **Accessibility** | WCAG 2.2 AA baseline across all surfaces; AAA contrast on `web-clinician`; screen-reader full support; captions on all audio |
| **Localization** | **en, fr, ar, fa at v1.0 launch parity** (Arabic + Persian are RTL); strict per-locale launch gate; no machine translation on clinical content ever |
| **Battery** | < 2% daily drain for passive signals (mobile) |
| **Storage** | < 150MB app + < 250MB local data (configurable retention) |
| **Offline** | Full T3 crisis catalog + hotline directory bundled on-device (mobile) and pre-rendered (web-crisis) |

---

## 6. Success Metrics & Acceptance Criteria

**Product-level (must hit to be v1.0):**
- D30 retention ≥ 25% in closed beta; ≥ 30% at public launch
- D90 retention ≥ 18% at public launch
- Paid conversion ≥ 4.5% at 30 days
- Net Promoter Score ≥ 45 (category typical 20)
- Crisis-path SLO met: **99.99% on mobile + `web-crisis`** for 30 consecutive days pre-launch
- Zero data incidents
- Zero T3/T4 mishandling incidents reviewed by clinical advisors
- Per-locale parity: no launch locale retention below 80% of `en` baseline at D90
- `assessment.scoring.correctness` = 100%
- Audit log Merkle chain verification green continuously
- Refresh-token family reuse-detection test green in CI
- Per-stream log IAM isolation test green in CI
- axe-core WCAG 2.2 AA green across all 4 locales on all web surfaces

**Feature-level:** Each F-01 through F-18 has individual acceptance criteria (see above).

---

## 7. Out of Scope for v1.0 (Deferred)

- Community features (Year 2+ — possibly never; tradeoff with clinical framing)
- Coach marketplace (Year 3+)
- Clinician portal **GA** (Phase 3; alpha available at v1.0)
- Enterprise admin **self-serve SSO/SCIM** (Phase 3; hand-rolled pilots available at v1.0)
- Researcher API (Phase 5)
- Minors (never at launch; possibly Year 3+ with separate design, separate consent, separate risk model)
- Insurance reimbursement integration (post-FDA clearance — Phase 4+)
- Voice journal on web (mobile only at v1.0; web in Phase 3)
- Biometric capture on web (HealthKit / Health Connect are mobile-only; manual entry on web)
- Additional locales beyond en/fr/ar/fa (Phase 3 adds de/es/pt-BR; same per-locale launch gate applies)
- Cross-vertical beyond alcohol (cannabis in Phase 3, gated on retention + cross-vertical transfer learning validation)
- LLM on safety path (never — this is an architectural commitment, not a deferral)

---

## 8. Open Product Questions

1. Do we require a wearable at signup, or graceful degrade without one?
2. What is the default for push-notification permission ask — onboarding step 9 or after first urge logged?
3. Should the resilience streak be explained at onboarding, or revealed contextually after first relapse?
4. ~~What is the minimum privacy posture before an enterprise pilot can begin~~ **Resolved:** SOC 2 Type I audit opened + HIPAA BAA with all processors complete before first paying pilot onboards.
5. Do we launch without the voice journal if Whisper-small on-device latency is poor on older devices? (Fallback: structured CBT-field entry remains primary; voice is opt-in)
6. For the Persian (`fa`) locale, do we default the secondary calendar to Shamsi (Solar Hijri) or keep Gregorian-only and let users opt into Shamsi? *Leaning: Gregorian primary + Shamsi display toggle in Settings — clinical scores always Gregorian + Latin digits to avoid ambiguity.*
7. For Arabic (`ar`), which regional variant do we target in market copy? *Current plan: MSA (Modern Standard Arabic) across markets, with explicit acknowledgment in the help center; dialectal copy not attempted.*
8. Which Persian (`fa`) regional variant for hotlines and content? *Current plan: Iranian Persian; Afghan Dari and Tajik are separate locales for future consideration.*
9. On `web-app`, do we expose psychometric instrument completion or require users to take them on mobile? *Leaning: available on both; mobile primary for push-reminder cadence.*
10. For the clinician alpha at v1.0 — invite-only, how many clinicians do we onboard and how do we select them? *Current plan: 10-25 clinical advisors + their consenting patients, selected by Head of Clinical.*

See [07_Roadmap](07_Roadmap.md) for when each is decided.
