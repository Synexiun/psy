# Executive Summary — Discipline OS

**Company (provisional):** Discipline OS, Inc.
**Product:** Discipline OS — a behavioral intervention platform
**Stage:** Pre-seed / Seed
**Ask:** $4.5M–6.5M seed to reach v1.0 + 12 months of post-launch runway
**Prepared:** April 2026

---

## 1. The One-Sentence Pitch

**Discipline OS is the first cross-vertical behavioral operating system that predicts and intercepts impulse moments — cravings, panic, procrastination, emotional reactivity — in real time, then learns from every urge and every lapse to build lasting self-regulation.**

Not a tracker. Not a meditation app. Not a sobriety app. The thing that happens *between the urge and the action*.

---

## 2. The Problem

Every human fights the same battle: the gap between what they *intend* to do and what they *actually* do. The mental-health app market addresses this poorly:

- **Habit trackers** (Streaks, Habitica) are passive logs. They track, they don't intervene.
- **Sobriety apps** (I Am Sober, Nomo) are vertical and shame-based. Their streak-reset UX drives catastrophic churn on relapse day.
- **Meditation apps** (Calm, Headspace) work upstream. They build baseline capacity but do nothing at the moment of decision.
- **CBT chatbots** (Wysa, Woebot) are conversational. They're not embedded in real-time context.
- **Digital blockers** (Freedom, Opal) address screen-based triggers only. Useless for physical cravings or emotional spirals.

**The result:** 70% of users abandon mental-health apps within 100 days. Nobody is winning the moment of decision.

---

## 3. The Solution

Discipline OS is architected as a **closed behavioral control loop**:

```
SIGNAL → STATE ESTIMATION → INTERVENTION → REFLECTION → PERSONALIZATION → (loop)
```

- **Signal layer** captures active inputs (3-second urge dial) and passive context (HRV, location class, sleep debt, phone-usage patterns).
- **State estimation** fuses signals into urge intensity, relapse-risk probability, and HALT-state (Hungry/Angry/Lonely/Tired).
- **Intervention orchestrator** uses a 4-tier policy (ambient → nudge → structured workflow → crisis SOS) to deliver exactly the right support at exactly the right moment.
- **Coping toolkit** contains evidence-based workflows: Urge Surfing (Marlatt), TIPP (DBT), Cognitive Defusion (ACT), Implementation-Intention Replay (Gollwitzer), Box Breathing, Contact-a-Human.
- **Reflection layer** runs structured CBT protocols (situation → thought → feeling → behavior → outcome → alternative thought), not free journaling.
- **Personalization engine** uses a contextual bandit to learn which interventions work for *this user* in *this context*.

---

## 4. The Key Insight — Why We Win

**Two moments decide the category: the moment of urge, and the moment after a relapse.**

Every competitor gets *one* right. None gets both. That's the whole opportunity.

Our defensible design choices:
1. **Resilience streak** (urges handled — never resets) runs in parallel to continuous-days streak. Kills the Abstinence Violation Effect churn pattern.
2. **Compassion-first relapse protocol** (24–72h elevated support). Industry's streak-reset shame is scientifically wrong and commercially lossy — we flip it.
3. **Cross-vertical learned model.** One user, many behaviors, one engine. Nobody else does this seriously.
4. **Real wearable inference.** Most apps pull HealthKit data and ignore it. We use HRV to inform state estimation with clinical depth.
5. **Crisis tools free forever.** Ethical line + reputational moat.

---

## 5. Market Opportunity

| Segment | TAM | Serviceable |
|---------|-----|-------------|
| US consumer mental wellness apps | $6.2B (2026) | $1.1B |
| Addiction recovery (US) | $42B clinical + $1.8B digital | $300M digital |
| Corporate wellness / EAP | $58B global | $4B US digital subset |
| Digital therapeutics (global) | $9.1B (2026) → $32B (2030) | $1.2B addressable |
| **Aggregate SAM** | | **~$6.6B** |

Growth: Digital mental health is growing 22% CAGR; digital therapeutics 28% CAGR through 2030.

Our wedge market: **alcohol reduction / abstinence** (largest single-vertical willingness to pay; most developed digital-therapeutic reimbursement pathway).

---

## 6. Business Model — Three Revenue Streams

| Stream | Pricing | Role | Year 3 Mix |
|--------|---------|------|------------|
| **Consumer (Freemium)** | $11.99/mo Plus · $19.99/mo Pro · $24.99/mo Family | Volume, algorithm training, brand | 55% |
| **Enterprise EAP / Employer** | $5–8 PMPM | Scale revenue lever | 35% |
| **Clinician Edition** | $49/mo per therapist (40 clients) | Clinical credibility channel | 10% |
| Long-term expansion: Clinical SKU (FDA SaMD) | Insurance-reimbursed | Category lock-in | Y4+ |

---

## 7. Financial Summary

| Year | Users | ARR | Burn | Team |
|------|-------|-----|------|------|
| Y1 (pre-launch to v1.0) | — | $0 | $4.2M | 14 |
| Y2 (post-launch) | 85k paid | $8.1M | $6.8M | 28 |
| Y3 | 240k paid + 40 enterprise contracts | $28M | Breakeven trajectory | 52 |
| Y4 | 520k paid + 180 enterprise | $74M | Profitable | 95 |
| Y5 | 1.1M paid + Clinical SKU live | $165M | EBITDA positive | 160 |

See [06_Financial_Projections](06_Financial_Projections.md) for detail.

---

## 8. Traction Plan — First 18 Months

1. **Months 1–3: Mechanical-Turk validation.** SMS + human-in-loop intervention for 50 users, single vertical (alcohol). Prove interventions reduce urge escalation. Cost: $40k.
2. **Months 3–6: Clinical advisory board + v0.5 scaffold.** Recruit 3 clinical advisors (RPM, MBRP, JITAI). Build React Native shell, ingest layer, 3 core tools.
3. **Months 6–10: v0.5 closed paid beta.** 500 paying users ($9/mo during beta). Single vertical. Measure D30/D90 retention vs. category baseline.
4. **Months 10–14: v1.0 build.** Cross-vertical expansion, personalization engine, wearable integration, structured relapse protocol.
5. **Months 14–18: v1.0 launch.** Consumer + first enterprise pilots. Target: 15k paid users by month 18.

**Gate condition:** Do not expand cross-vertical until single-vertical D90 retention exceeds 25%.

---

## 9. Team & Hiring

**Founding team required:**
- CEO (product + behavioral depth)
- CTO (mobile + ML)
- Head of Clinical (licensed psychologist with RP/MBRP publications)

**First-10 hires:**
- 2 senior mobile engineers (1 iOS, 1 Android native depth)
- 2 backend/ML engineers
- 1 data scientist
- 1 product designer (mobile + clinical UX)
- 1 clinical content lead
- 1 growth / marketing lead
- 1 operations / compliance lead

See [10_Team_Hiring](10_Team_Hiring.md).

---

## 10. Why Now

Three converging tailwinds:

1. **Wearable penetration crossed 35% of US adults in 2025.** HRV-informed interventions are finally feasible at scale.
2. **Digital therapeutic reimbursement codes went live** (CMS, select private payers) in 2025 — a clinical SKU has a clear monetization path.
3. **Post-pandemic mental-health normalization.** Users are willing to pay, employers are willing to fund, clinicians are willing to prescribe — all at historic highs.

---

## 11. Why This Team

(To be filled in with actual founder bios. Conditions from research report:)

- Clinical depth in the DNA (advisor-level minimum)
- Real mobile-UX craft (this category punishes mediocre UX)
- Discipline to refuse investor pressure toward streaks, badges, growth hacks
- Patience for a 14–18 month timeline before scaling

---

## 12. Risk Summary & Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Retention collapse at D30–60 | Critical | Resilience-streak + context-gated engagement |
| Relapse-day shame spiral | Critical | Compassion protocol + dual-metric dashboard |
| T3/T4 crisis mishandling | Catastrophic | Deterministic workflow, never LLM, human handoff for self-harm |
| Regulatory (FDA, GDPR) | High | Two-SKU: wellness-first, clinical on parallel track |
| Trust / privacy breach | Critical | Edge ML, E2E voice journals, SOC 2 from Y1, HIPAA BAAs |
| Apple/Google commoditization | Medium | Wearable depth + clinical credentials + cross-vertical moat |

See [08_Risk_Compliance](08_Risk_Compliance.md).

---

## 13. The Ask

**$5.5M seed round (preferred)** at target post-money ~$28M, 18-month runway to v1.0 + 6 months post-launch buffer.

Use of funds:
- 58% engineering & ML (14 eng hires across 18 months)
- 18% clinical advisory + content (3 advisors, licensed content team)
- 14% design & product
- 6% growth (held low — we are not paying for vanity installs)
- 4% operations, legal, compliance (SOC 2, HIPAA prep)

**Alternative:** $4.2M with 12-month runway to v0.5 paid beta only.

---

## 14. The Bet

Most entrants in this space will ship a tracker with AI sprinkled on top and die at D60. A small number will build the actual thing: **a cross-vertical, intervention-first, clinically-grounded operating system that treats relapse with compassion and the moment-of-urge with utility.**

The winner of that race becomes the Calm of discipline — a category-defining platform with both consumer scale and clinical defensibility. The window is 18–24 months. After that, Apple or a well-funded competitor will claim the position.

**Build it if — and only if — you can hold the line on the six conditions.** Otherwise it will fail expensively.

See [07_Roadmap](07_Roadmap.md) for execution detail.
