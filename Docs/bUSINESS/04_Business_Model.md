# Business Model — Discipline OS

## 1. Revenue Streams Overview

Five revenue streams, staged over 5 years:

| Stream | Launch | Y3 share of ARR | Y5 share of ARR |
|--------|--------|----------------:|----------------:|
| Consumer subscription | Month 12 | 55% | 40% |
| Enterprise EAP / employer | Month 18 | 35% | 38% |
| Clinician Edition | Month 24 | 10% | 12% |
| Clinical SKU (reimbursed) | Year 3+ | 0% | 8% |
| Treatment center / white-label | Year 3+ | 0% | 2% |

Aggressively diversified by Year 5 — no single stream >40%.

---

## 2. Consumer Subscription — Pricing

### Tier Structure

| Tier | Price | Content |
|------|-------|---------|
| **Free** | $0 | Active tracking, 1 coping tool (Box Breathing), basic relapse logging, manual check-ins, SOS crisis escalation always free |
| **Plus** | $11.99/mo · $79/yr | Full coping toolkit, context-aware nudges, relapse engine, wearable integration, weekly pattern reports |
| **Pro** | $19.99/mo · $149/yr | All of Plus + AI personalization, advanced pattern analytics, accountability integrations, priority support, multi-behavior tracking (Y2+) |
| **Family** | $24.99/mo · $179/yr | Up to 5 accounts, shared accountability (opt-in, privacy-preserving) |

### Pricing Rationale

- **Benchmark:** Calm $69.99/yr, Headspace $69.99/yr, Wysa $99/yr, Intellect $89/yr, Reframe $79/yr
- **Positioning:** Pro premium-priced above category to signal clinical-grade depth
- **Trial:** 7-day free trial on Plus and Pro; no credit card required for Free tier
- **Discounts:** 20% off annual vs. monthly (standard pattern), student tier 50% off (lightweight verification)
- **Regional:** Purchasing-power-parity adjustment for emerging markets (Y2+)

### Why Not Lower Priced

- $4.99/mo tier tested mentally: attracts price-shoppers, destroys LTV, and implicitly positions us as commodity. Avoided.
- Lifetime deals: eliminate recurring revenue and adversely select for churn-risk users. Avoided.

### Paywall Design

- **Crisis tool (T3 SOS) FREE forever.** Ethical line.
- Free tier real utility, not stub — designed for users who truly can't pay.
- Paywall placement: after first 14 days of use, during pattern-insight unlock, or during relapse recovery (when intervention depth matters most).
- Never lock sobriety progress behind paywall.
- Cancel anytime, one-tap, no retention dark patterns.

---

## 3. Enterprise EAP / Employer

### Pricing Structure

| Seat Band | PMPM | Annual Contract Value |
|-----------|------|----------------------|
| 100–500 employees | $7.50 PMPM | $9k–45k |
| 500–2,000 | $6.25 PMPM | $37.5k–150k |
| 2,000–10,000 | $5.50 PMPM | $132k–660k |
| 10,000+ | $5.00 PMPM + implementation fee | $600k+ |

**Contract structure:**
- Minimum 12 months
- Annual billing or quarterly
- 90% utilization threshold for price holds (low engagement → renegotiate)
- ROI guarantee available at 5k+ seats: net savings of $50 PMPM in claims or credit back

### Value Proposition to Employers

1. **Preventive mental-health coverage.** Replaces EAP hotline (typical 2–4% utilization) with 25–35% engagement.
2. **Claims reduction.** Digital behavioral intervention studies (when good) show 15–25% reduction in behavioral-health-related utilization.
3. **Absenteeism reduction.** Correlates with mental-health ROI (typical 2:1 to 4:1 PEPM savings).
4. **DEI / wellness optics.** Visible, substantive wellness benefit.
5. **Confidentiality.** Zero individual data to employer (aggregate only, k-anonymous).

### Sales Process

- Months 12–18: pilot with 3–5 employers (free, structured outcomes)
- Month 18+: direct sales to HR / benefits leaders
- Month 24+: EAP vendor distribution (Lyra Health, Spring Health, Modern Health, etc. — partner, not compete)
- Month 30+: benefits-consultant channel (Mercer, Willis Towers Watson, Aon)

### Enterprise-Specific Features

- SSO (SAML, OIDC)
- SCIM user provisioning
- Aggregate dashboard (k-anonymous outcomes only)
- PMPM invoicing
- Custom onboarding with employer brand (co-brand, not white-label)
- Admin portal with zero individual data

---

## 4. Clinician Edition

### Pricing

- **$49/mo per clinician, up to 40 active patients**
- $1.22 per patient per month at full utilization
- Bulk: $39/mo per clinician at groups of 10+ licenses

### Value Proposition

- **Bridges 6-days-between-sessions gap.** This is the real clinical problem.
- **Outcome visibility** — which interventions work between sessions
- **CPT code billing support** — where clinician bills for remote therapeutic monitoring (RTM) or digital therapeutic, we provide evidence package
- **Integration** — ghost charting into leading EMR via FHIR (Epic, Cerner) — Y3+

### Clinician UX

- Separate app / web portal (not same as patient app)
- Patient invites clinician by 6-digit code
- Patient controls sharing scope (full / summary / outcomes only)
- Clinician never sees raw journal content unless patient explicitly shares
- Real-time risk-flag alerts (opt-in by patient)

### Acquisition

- KOL relationships (clinical advisors as first conduit)
- Presentations at APA / NAADAC / ACA conferences
- Academic partnerships for outcomes studies
- Direct outreach to addiction/anxiety specialists

---

## 5. Clinical SKU (Year 3+)

### Pathway

- **Primary indication target:** Alcohol Use Disorder (AUD), mild-to-moderate
- **Classification:** FDA SaMD (Software as Medical Device), De Novo or 510(k)
- **Clinical trial:** 400-patient RCT, 12-week primary endpoint (reduced heavy drinking days), 24-week secondary
- **Timeline:** Trial Y2–Y3, submission Y3, clearance target Y3 Q4 or Y4

### Reimbursement

- **US Medicare:** new CPT codes 98975, 98976, 98977, 98980, 98981 (digital therapeutic monitoring) — ~$18–52/mo depending on code mix
- **US Private payers:** following CMS lead, 2025–2026
- **State Medicaid:** slower, some state progress (NY, MA, CA)

### Revenue Model

- Prescription-based; patient not charged directly
- Payer reimbursement per month of active use
- ARPU: $15–40/mo depending on payer mix
- Typical patient duration: 6–12 months prescribed

### Operational Needs

- Clinical operations team (Y3 hire)
- Pharmacovigilance / adverse event reporting
- Quality management system (ISO 13485 aligned)
- FDA Quality System Regulation (QSR) compliance
- 6–10x engineering overhead on clinical SKU vs. wellness SKU

---

## 6. Treatment Center / White-Label (Year 3+)

- Enterprise licensing to IOPs, residential programs, treatment centers
- $15k–35k/yr base + $25–60 per active patient per month
- White-label (custom brand) or co-brand
- Outcomes reporting included
- Sales cycle: 6–12 months per contract

---

## 7. Explicitly Rejected Revenue Streams

- **Data licensing** (aggregated, de-identified, or otherwise). Ethical and reputational line. Reinforced in every doc.
- **Advertising.** Period.
- **Lifetime deals.** Destroy LTV, adverse-select for churn.
- **Affiliate / referral programs paying commission on sign-ups.** Risk of incentivizing inappropriate acquisition into vulnerable populations.
- **Freemium-to-paid conversion via crisis moment.** Never paywall the moment of greatest need.

---

## 8. Unit Economics

### Consumer (Plus tier target)

| Metric | Target | Commentary |
|--------|--------|-----------|
| Gross margin | 82% | App-store fees (15–30%), server, content amortization |
| CAC | $55 | Paid + organic blend |
| ARPU (mo) | $9.80 | Blended Plus + Pro + Family |
| Payback | 7 mo | Acceptable for subscription |
| Avg subscription life | 14 mo | Conservative early; targets 22 mo at Y3 |
| LTV | $185 | Target 3.3x CAC |
| Annual churn | 42% | Aggressive target; category typical 60%+ |

### Enterprise

| Metric | Target | Commentary |
|--------|--------|-----------|
| Gross margin | 78% | Sales + CS + implementation overhead |
| CAC | $8,500 | Per contract, including sales cost |
| ACV | $120k | Average across bands Y3 |
| Payback | 9 mo | |
| Net revenue retention | 110% | Expansion within account |
| Contract life (avg) | 3.4 yr | Strong ceiling |
| LTV | $450k | |

### Clinician Edition

| Metric | Target | Commentary |
|--------|--------|-----------|
| Gross margin | 81% | |
| CAC | $220 | Heavy organic + KOL channel |
| ARPU (mo) | $45 | Blended at utilization |
| Payback | 5 mo | |
| LTV | $1,100 | |

### Clinical SKU

Economics depend on payer mix. Conservative model:
- ARPU $22/mo
- 8-mo average duration
- 78% gross margin (regulatory overhead)
- LTV per patient $140
- Acquisition via clinician referral (CAC near zero, but enables clinician channel)

---

## 9. Financial Model Inputs

| Input | Y1 | Y2 | Y3 | Y4 | Y5 |
|-------|----|----|----|----|----|
| Consumer paid users | 0 | 85k | 240k | 520k | 1.1M |
| Consumer ARPU (mo) | — | $9.40 | $9.80 | $10.20 | $10.70 |
| Enterprise contracts | 0 | 8 | 40 | 180 | 400 |
| Enterprise avg ACV | — | $85k | $120k | $145k | $165k |
| Clinician subs | 0 | 40 | 480 | 2,100 | 4,800 |
| Clinical SKU lives | 0 | 0 | 0 | 15k | 45k |

See [06_Financial_Projections](06_Financial_Projections.md) for the full P&L rollup.

---

## 10. Pricing Evolution Roadmap

- **Year 1–2:** current tier structure
- **Year 2:** introduce Family tier
- **Year 2:** introduce student + nonprofit tier (50% off Plus)
- **Year 3:** price increase on new subscribers (+$2/mo) after clinical efficacy data published
- **Year 3:** test annual-only tier at $59/yr (lower barrier for committed users)
- **Year 4:** consider Enterprise-only features (e.g., admin analytics) creating genuine Pro-tier-plus ceiling

---

## 11. Summary

Discipline OS's business model is deliberately diversified across consumer volume, enterprise scale, and clinical defensibility. Consumer subscription is the foundation and brand; enterprise is the scale lever; clinical is the category lock-in.

**Key structural advantage:** each stream strengthens the others.
- Consumer volume produces training data that improves the personalization engine → makes enterprise outcomes stronger → supports clinical efficacy claims.
- Clinical credibility validates enterprise purchase decisions and elevates consumer brand.
- Enterprise contracts provide the scale revenue that funds the multi-year clinical SKU investment.

This interdependence is the real business-model moat.
