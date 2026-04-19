# Execution Roadmap — Discipline OS

## Overview

Five phases over 60 months. Each phase has a **gate** — if the gate condition isn't met, the next phase does not start. This discipline is what separates a category-defining product from a graveyard of half-built features.

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0: Validation (M1–3) ──[Gate: urge-reduction signal]      │
│                              │                                   │
│ Phase 1: v0.5 Beta (M4–14) ──[Gate: D90 retention > 15%]         │
│                              │                                   │
│ Phase 2: v1.0 Launch (M14–18)─[Gate: D90 retention > 25%]        │
│                              │                                   │
│ Phase 3: Expansion (M18–30) ─[Gate: Enterprise pilot conversions]│
│                              │                                   │
│ Phase 4: Clinical SKU (M30–48)[Gate: Clinical trial endpoint]    │
│                              │                                   │
│ Phase 5: Platform (Y5+)                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0 — Validation (Months 1–3)

**Goal:** Prove that timely intervention actually reduces urge escalation. Before writing production code.

### Method

- **50 alcohol-reduction participants** recruited from Reframe / r/stopdrinking / SMART communities
- **8-week structured study**
- **No app** — SMS + human coach-in-loop
- **Randomized into 2 arms:** intervention group (receives coaching SMS on self-reported urges) vs. control (tracking only)
- **Primary endpoint:** self-reported urge escalation rate (did the urge peak or did it get acted on?)
- **Secondary:** weekly drinking days, subjective control, willingness-to-pay for a real product

### Deliverables

- Study protocol (IRB-lite review via clinical advisor)
- 8-week data + statistical analysis
- Participant interview transcripts (qualitative)
- Product-requirement refinements from findings
- Go / no-go recommendation

### Gate

**Statistically meaningful urge-reduction signal in intervention group vs. control (p < 0.1 acceptable at this scale; effect size > 0.4).**

If no signal → redesign intervention model before building. Worst outcome: a shipping product that doesn't work.

### Team (Phase 0)

- Founder(s)
- 1 clinical advisor (paid part-time)
- 2 coach-operators (contract)
- 1 data analyst (contract)

### Budget: ~$40k–60k

---

## Phase 1 — v0.5 Closed Paid Beta (Months 4–14)

**Goal:** Build the first version of the app and validate retention beats category baseline.

### Workstreams (Parallel)

#### Engineering
- Months 4–7: Signal ingestion, state estimation scaffold, 3 coping tools (Box Breathing, Urge Surfing, TIPP), relapse logging
- Months 7–10: Intervention orchestrator, personalization engine v1, relapse protocol, basic dashboard
- Months 10–14: Voice journaling, wearable integration (Apple Health first), iOS polish, Android port

#### Clinical
- Months 4–6: Clinical advisory board recruited (3 advisors); coping tool scripts drafted
- Months 6–9: Clinical review of all tools + T3/T4 escalation protocols
- Months 9–14: Methodology paper draft, pre-print submitted

#### Product / Design
- Months 4–6: Design system, onboarding flow, core UI
- Months 6–9: Relapse UX (high-stakes, compassion-first)
- Months 9–14: Iterative polish with beta feedback

#### Legal / Compliance
- Months 4–8: Privacy policy, ToS, DPA templates
- Months 8–14: SOC 2 Type I readiness; HIPAA review; FTC guidance audit

#### Growth
- Months 4–8: Waitlist + founder content engine (1 piece / week)
- Months 8–12: Waitlist → beta invites, payment integration
- Months 12–14: Prep for v1.0 launch marketing

### Milestones

- **M7:** Alpha app functional, founder team daily drives
- **M9:** Private alpha with 150 friendly users
- **M11:** Paid beta opens with 500 users at $9/mo
- **M13:** Beta retention data available (D60+ by now on early cohort)
- **M14:** Gate review

### Gate

**D90 retention > 15%** in closed paid beta.

(Category typical: 8–12%. We're targeting modest outperformance at this stage; v1.0 target is 25%.)

### Team at end of Phase 1 (~18 people)

- Engineering: 8 (3 mobile, 3 backend, 2 ML/data)
- Product / Design: 3
- Clinical: 2 (head + content lead; 3 advisors contract)
- Growth / Marketing: 2
- Operations / Legal / Compliance: 2
- Leadership: 1 (CEO) + CTO + Head of Clinical

### Budget: ~$4.0M (seed funding)

---

## Phase 2 — v1.0 Public Launch (Months 14–18)

**Goal:** Scale to 15k paid users while maintaining D90 retention > 25%.

### Workstreams

#### Engineering
- Scale infrastructure (handle 10x signup burst)
- Android feature parity with iOS
- Performance optimization (T3 < 800ms verified)
- Observability / error budget enforcement

#### Clinical
- Outcomes measurement pipeline (consented, ethical, publishable)
- Quarterly clinical review cadence
- Prep for Phase 3 clinical trial design

#### Product
- Refine based on beta learnings
- Integrate Oura, Whoop, Fitbit (beyond just HealthKit/Google Fit)
- Localization planning (Spanish start)

#### Growth
- Launch PR (embargoed exclusive + founder podcast tour)
- Paid acquisition carefully scaled (CAC gated)
- Content engine amplified
- Reddit and community engagement

#### Operations
- SOC 2 Type II in progress
- First enterprise pilot conversations (Month 14 start)
- Support team scaled

### Milestones

- **M14:** App Store launch (US iOS + Android)
- **M15:** First enterprise pilot contract signed (free)
- **M16:** 5,000 paid users
- **M17:** Outcomes report published
- **M18:** 15,000 paid users; gate review

### Gate

**D90 retention > 25% on post-launch paid cohort.**

If miss: extend iteration before Phase 3. Do not press cross-vertical expansion until single-vertical retention proves out.

### Team: ~28

### Budget: ~$2.8M (last portion of seed)

---

## Phase 3 — Expansion (Months 18–30)

**Goal:** Cross-vertical feature parity + enterprise scale + international.

### Workstream Priorities

#### Cross-Vertical Build (v2.0)
- Add verticals: procrastination, panic/anxiety, emotional reactivity, binge eating
- Generalize signal + state + intervention models
- Cross-vertical pattern detection (e.g., procrastination correlates with afternoon stress)

#### Enterprise Scale
- First paid contracts close (M18–21)
- Dedicated enterprise seller hired (M18)
- Customer success function launched
- EAP partner conversations begin

#### International
- UK + EU launch (M24)
- GDPR + UK DPA full compliance
- Spanish localization live

#### Clinician Edition
- Soft launch M24
- Clinical advisor amplification
- KOL relationships

#### Clinical Path
- Clinical trial design (Alcohol Use Disorder, 400 patients)
- IRB + FDA pre-submission meeting
- Trial site identification and contracts

### Milestones

- **M20:** v2.0 launch (cross-vertical)
- **M22:** Series A closed ($18M target)
- **M24:** UK launch; Clinician Edition soft launch
- **M27:** 40 enterprise contracts
- **M30:** 240k paid users; clinical trial enrolling; gate review

### Gate

**$4M+ enterprise ARR; D90 retention holding > 25%.**

### Team: ~52

### Budget: ~$12M (seed extension + Series A)

---

## Phase 4 — Clinical SKU (Months 30–48)

**Goal:** FDA clearance for AUD (Alcohol Use Disorder); reimbursed prescription channel open.

### Workstream Priorities

#### Clinical Trial
- Months 24–36: enrollment + 24-week primary endpoint
- Months 36–42: analysis + FDA submission
- Months 42–48: clearance (target) + commercial launch prep

#### Clinical Operations
- Build clinical ops team (quality management, pharmacovigilance)
- ISO 13485-aligned QMS
- FDA Quality System Regulation compliance

#### Product
- Clinical SKU features: adherence monitoring, clinician integration, FHIR export
- Privacy upgrades for PHI handling
- Audit logging hardening

#### Commercial
- Payer relationships (Medicare + 2–3 private payers)
- Clinician prescribing workflow
- Clinical specialty sales (distinct from enterprise motion)

### Milestones

- **M36:** Trial primary endpoint analysis
- **M42:** FDA submission
- **M46:** Clearance (target) or response
- **M48:** Commercial clinical SKU launch

### Gate

**FDA clearance achieved; 2+ payer contracts signed.**

### Team: ~95

### Budget: ~$20M (Series A + early Series B or B avoidance via revenue)

---

## Phase 5 — Platform (Year 5+)

**Goal:** Category-defining platform with durable moats.

### Workstreams

- Open SDK for third-party coping tools
- White-label for treatment centers
- Second clinical indication (anxiety or binge eating)
- Advanced biomarker integration (continuous glucose, etc.)
- International clinical clearances (UK NICE, EU MDR)
- Category leadership (analyst positioning, industry standards)

### KPIs

- 1.1M+ consumer paid users
- 400+ enterprise contracts
- 45k+ clinically-prescribed lives
- $165M+ ARR
- Profitable, EBITDA-positive
- 3+ peer-reviewed outcome publications

---

## Critical Path Dependencies

The dependencies that cannot be parallelized or accelerated:

1. **Clinical advisory recruitment** (M2–4) blocks all clinical work
2. **State estimation validation** (M5–7) blocks orchestrator work
3. **Beta retention data** (M11–13) blocks v1.0 launch decision
4. **SOC 2 Type I** (M10–14) blocks first enterprise pilot
5. **SOC 2 Type II** (M18–24) blocks Fortune 500 enterprise
6. **Clinical trial enrollment** (M24–36) blocks FDA submission
7. **FDA clearance** (M42–48) blocks Clinical SKU commercial launch

---

## Monthly Operational Cadence

- **Weekly:** engineering standup, retention review, clinical-escalation review
- **Bi-weekly:** product-clinical alignment, growth funnel review
- **Monthly:** company all-hands, financial review, board update (post-seed)
- **Quarterly:** strategic review, roadmap adjustment, board meeting
- **Annually:** clinical methodology paper, outcomes report, strategic offsite

---

## Decision Log (Key Decisions Locked)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Mechanical-Turk validation before code | $40k to derisk the entire premise |
| 2 | Wedge = alcohol | Willingness to pay + clinical pathway + community |
| 3 | iOS first, then Android | Demographic fit of target persona |
| 4 | React Native + native modules | Cross-platform velocity, native where critical |
| 5 | Edge ML (CoreML/TFLite) for inference | Privacy as moat |
| 6 | Clinical SKU parallel path from Y1 | Retrofit is 10x harder |
| 7 | No gamification | Category anti-pattern |
| 8 | Resilience streak | Core differentiator |
| 9 | Free crisis tool forever | Ethical line |
| 10 | No data licensing | Ethical line |

These decisions are locked. Revisiting them requires founder + advisor + clinical lead alignment.

---

## Risk Log (High-Severity, Continuously Monitored)

| Risk | Owner | Monitoring |
|------|-------|-----------|
| D30/D90 retention miss | Head of Product | Weekly |
| Clinical advisor departure | CEO | Monthly check-ins |
| T4 mishandling incident | Head of Clinical | Real-time alerts |
| Data breach | CTO | Continuous |
| FDA classification surprise | Head of Clinical + Legal | Quarterly |
| Apple/Google commoditizing feature | CEO | Quarterly review |
| Key hire loss | CEO | Compensation review every 12 mo |

---

## What Would Cause a Re-Plan

- D90 beta retention < 12% → redesign before v1.0
- Clinical advisor publicly withdraws → delay v1.0 until replacement
- Major data incident at competitor → accelerate our trust messaging
- FDA precedent against similar apps → adjust clinical SKU timeline
- Funding environment deteriorates → extend runway by compressing scope (cut international or enterprise)

This roadmap is a plan, not a promise. Quarterly reviews with the board adjust based on reality.
