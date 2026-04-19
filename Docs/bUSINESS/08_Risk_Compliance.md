# Risk & Compliance — Discipline OS

## 1. Risk Framework

Risks classified by:
- **Severity:** Catastrophic / Critical / High / Medium / Low
- **Likelihood:** Near-certain / Likely / Possible / Unlikely / Rare
- **Owner:** Founder / Clinical / Legal / Eng / Ops

Top-risk register reviewed monthly. Critical+ reviewed weekly.

---

## 2. Top-Priority Risks

### R-01: User experiences acute psychiatric crisis, app fails them
- **Severity:** Catastrophic
- **Likelihood:** Near-certain (will happen at scale)
- **Owner:** Head of Clinical
- **Mitigation:**
  - T4 deterministic escalation (never LLM-generated)
  - NLP classifier flags self-harm content in journals (clinically validated)
  - 988 + Crisis Text Line + local emergency always one-tap
  - User-configured emergency contact supported
  - 24h follow-up check-in after T4 events
  - Clinical advisor on retainer for incident review
  - Clear legal disclaimers throughout onboarding
- **Residual risk:** Medium (cannot eliminate, must manage)

### R-02: Data breach exposes sensitive behavioral data
- **Severity:** Catastrophic
- **Likelihood:** Possible
- **Owner:** CTO
- **Mitigation:**
  - Edge ML keeps biometric data on-device
  - E2E encryption for journals + voice
  - Minimal cloud data (pseudonymized at ingestion)
  - SOC 2 Type II from Y1 Q4
  - Quarterly pen-tests (external)
  - Bug bounty program from Y1 Q3
  - Incident response playbook + drills
  - Cyber insurance $10M (Y2+)
- **Residual risk:** Low-Medium

### R-03: D30 / D90 retention misses targets
- **Severity:** Critical (existential to business)
- **Likelihood:** Possible
- **Owner:** Head of Product + CEO
- **Mitigation:**
  - Validation in Phase 0 before build
  - Closed paid beta with retention gate
  - Retention is primary KPI, not DAU
  - Resilience streak + compassion-first relapse design
  - No scheduled over-notification
  - Cohort analysis weekly
- **Residual risk:** Medium

### R-04: Regulatory action (FDA, FTC, State AG)
- **Severity:** Critical
- **Likelihood:** Possible
- **Owner:** Legal + Head of Clinical
- **Mitigation:**
  - Wellness-first positioning with strict language discipline
  - No unsupported efficacy claims
  - FTC Mental Health App Guidance (2024) reviewed quarterly
  - FDA pre-submission meeting before clinical-SKU launch
  - State AG monitoring (CA CMIA, WA My Health My Data Act)
  - Consumer-protection counsel retained
- **Residual risk:** Low

### R-05: Clinical advisor departure or public disavowal
- **Severity:** Critical
- **Likelihood:** Unlikely
- **Owner:** CEO
- **Mitigation:**
  - 3 advisors (not 1) for redundancy
  - Multi-year advisory agreements with reasonable equity
  - Transparent methodology (if we do right, advisors stay)
  - Bench of 5 additional candidates identified
  - Never commit to clinical claims advisors haven't reviewed
- **Residual risk:** Low

### R-06: Over-reliance on the app (behavioral dependency)
- **Severity:** High
- **Likelihood:** Likely
- **Owner:** Head of Clinical + Product
- **Mitigation:**
  - Fade-out design: prompts reduce as user builds skill
  - Explicit language framing app as scaffold, not solution
  - "Graduation" flow after 180 days
  - No engagement-maximization dark patterns
  - Session-length nudges ("You've used PDOS a lot today — go live your life")
- **Residual risk:** Medium

### R-07: Notification fatigue causes permission revocation
- **Severity:** High
- **Likelihood:** Likely
- **Owner:** Head of Product
- **Mitigation:**
  - Hard daily nudge budget (default 4)
  - Context-suppression after 2 dismissals
  - Cooldowns between nudges
  - User-configurable quiet hours
  - Adaptive learning of optimal timing per user
- **Residual risk:** Medium

### R-08: Competitive commoditization by Apple or Google
- **Severity:** High
- **Likelihood:** Possible
- **Owner:** CEO
- **Mitigation:**
  - Depth moat (cross-vertical, wearable integration, clinical)
  - Enterprise + clinical revenue diversification
  - Category ownership via analyst relationships
  - Move faster than incumbents to claim positioning
- **Residual risk:** Medium

### R-09: Under-capitalization or funding environment deterioration
- **Severity:** High
- **Likelihood:** Possible
- **Owner:** CEO + CFO
- **Mitigation:**
  - 18-month runway target always
  - Quarterly burn review with board
  - Revenue milestones designed to extend runway
  - Fallback scope reduction plan (cut international + enterprise timing)
  - Multiple investor relationships maintained
- **Residual risk:** Medium

### R-10: Insider misuse of user data
- **Severity:** Critical
- **Likelihood:** Unlikely
- **Owner:** CTO + Head of People
- **Mitigation:**
  - Role-based access control, least privilege
  - Just-in-time access for support
  - Full audit log, immutable
  - Quarterly access reviews
  - Pre-employment background checks for roles with PHI access
  - Termination process includes immediate access revocation
- **Residual risk:** Low

### R-11: Coercion scenarios (abusive partner accesses app)
- **Severity:** High
- **Likelihood:** Possible
- **Owner:** Head of Product + Security
- **Mitigation:**
  - App-lock with biometric + PIN
  - Hidden-from-recents
  - Generic icon / name mode
  - Quick-erase (3-tap full wipe)
  - No-cloud mode
  - Never display sensitive content in notifications
  - Never display on lock screen
- **Residual risk:** Low

### R-12: Legal discovery of relapse / usage data in litigation
- **Severity:** High
- **Likelihood:** Possible (at scale)
- **Owner:** Legal
- **Mitigation:**
  - Data minimization at schema level
  - User-controlled retention (default 180 days, adjustable)
  - Delete-my-data flow complete purge
  - Subpoena policy published (push back where legally possible)
  - No-cloud mode for highest-sensitivity users
- **Residual risk:** Medium

### R-13: Algorithmic bias in interventions across demographics
- **Severity:** High
- **Likelihood:** Likely (unaddressed)
- **Owner:** Head of ML + Clinical
- **Mitigation:**
  - Fairness testing in model evaluation (demographic parity, equalized odds)
  - Training data diversity monitoring
  - Population subgroup performance reporting
  - External audit annually (Y2+)
  - Adverse-impact thresholds trigger model rollback
- **Residual risk:** Medium

### R-14: T4 false negatives (missed crisis signal)
- **Severity:** Catastrophic
- **Likelihood:** Possible
- **Owner:** Head of Clinical + ML
- **Mitigation:**
  - Conservative classifier (bias toward false positive)
  - Multiple signal paths (explicit button + NLP + pattern)
  - Clinical advisor reviews classifier quarterly
  - Any incident triggers classifier retraining + review
- **Residual risk:** Medium

### R-15: Payment processor, App Store policy shift
- **Severity:** Medium
- **Likelihood:** Possible
- **Owner:** Ops
- **Mitigation:**
  - Diversified payment rails (Stripe + App Store + Google Play)
  - Monitor Apple/Google policy announcements
  - Web-based subscription option where legally permitted
- **Residual risk:** Low

---

## 3. Compliance Posture

### Data Protection Frameworks

| Framework | Status / Target | Applies to |
|-----------|-----------------|-----------|
| **SOC 2 Type I** | Y1 Q4 | All operations |
| **SOC 2 Type II** | Y2 Q1 | All operations |
| **HIPAA-ready** | Y1 Q4 | Clinician edition, Clinical SKU |
| **GDPR compliant** | Launch day (if EU serving) | EU users |
| **UK DPA 2018 compliant** | Launch day (if UK serving) | UK users |
| **CCPA / CPRA** | Launch day | California users |
| **WA My Health My Data Act** | Launch day (if WA users) | Washington users |
| **HITRUST CSF** | Y3 | Enterprise positioning |
| **ISO 27001** | Y3 | International enterprise |
| **ISO 13485** | Y3 (clinical SKU) | Quality management |
| **FDA 21 CFR Part 11** | Y3 (clinical SKU) | Electronic records |
| **FDA QSR (21 CFR 820)** | Y4 | Clinical SKU post-clearance |

### Regulatory Strategy

**Wellness positioning (Y1–Y3):**
- No claim to diagnose, treat, cure, or prevent disease
- No medical-device classification
- FTC guidance compliance
- Consumer protection focus

**Clinical SKU track (parallel Y1–Y4):**
- FDA SaMD (Software as Medical Device)
- Pathway: De Novo or 510(k) depending on predicate
- Primary indication: Alcohol Use Disorder (mild to moderate)
- Clinical trial: 400-patient RCT
- Submission: Y3 Q3
- Target clearance: Y4 Q1

### International Strategy

**Phase 1:** US launch (Y1–Y2)
**Phase 2:** UK + EU (Y2)
- GDPR: full compliance; DPO appointed; EU data residency
- UK DPA: separate regulatory entity
- DTAC (digital technology assessment criteria) for NHS relationships
**Phase 3:** DACH + France (Y3)
- DiGA (Germany) pathway consideration for clinical SKU
**Phase 4:** APAC (Y4+)

---

## 4. Ethical Framework

### Principles

1. **Autonomy:** User always in control. Every suggestion can be declined.
2. **Transparency:** User can understand why any recommendation was made.
3. **Beneficence:** Every feature must benefit the user — not the company first.
4. **Non-maleficence:** Harm-reduction design. Worst-case scenarios tested for.
5. **Justice:** Equal quality across demographics; no exploitation of vulnerable populations.
6. **Privacy:** Default to minimal data; user-controlled retention.

### Ethical Lines (Non-Negotiable)

- No data licensing, sale, or sharing outside strict operational need
- No advertising to users
- No dark patterns in acquisition, retention, or monetization
- No targeting of minors at launch
- No incentive structures that reward inappropriate acquisition
- No crisis-moment paywalls
- No fabrication or curation bias in outcomes data

### Ethics Review

- Internal ethics committee: CEO, Head of Clinical, 1 external advisor, Head of Legal
- Meets quarterly or on any feature with ethical implications
- Can block feature launches (founder cannot override without board documentation)

---

## 5. Legal Structure & IP

### Company Structure
- Delaware C-Corp (standard for US venture-backed)
- IP assignment agreements from all employees and contractors
- Clinical advisor agreements with IP terms for methodology contributions

### IP Strategy
- **Trade secret:** personalization algorithms, state estimation models
- **Trademark:** Discipline OS name + logo in key markets
- **Patents:** selective, defensive (not aggressive)
  - State estimation from multi-signal fusion
  - Compassion-first relapse protocol UX (design patent)
  - Cross-vertical model architecture
- **Open source:** no critical components open-sourced without review

### Contract Templates

- Master Service Agreement (enterprise)
- Business Associate Agreement (HIPAA, enterprise + clinical)
- Data Processing Addendum (GDPR)
- Clinical advisor agreement
- Privacy policy (public)
- Terms of Service (public)
- Subject matter expert (clinical content) work-for-hire

### Insurance

| Policy | Amount | Timing |
|--------|-------:|-------|
| General liability | $2M | Launch |
| Technology E&O | $5M | Launch |
| Cyber liability | $10M | Y2 |
| D&O | $5M | Series A |
| Product liability (Clinical SKU) | $15M | Y3 |
| Employment practices | $2M | Y2 |

---

## 6. Safety Incident Response

### T4 Crisis Incident
1. Real-time alert to on-call clinical reviewer
2. Review within 24h of any T4 event
3. Clinical advisor review weekly of all T4 events
4. Classifier accuracy tracked per event
5. Any missed crisis signal triggers same-week classifier retraining

### Data Incident (Breach / Near-miss)
1. Incident response team activated within 2h of detection
2. Initial scope assessment within 12h
3. Customer notification within 72h (GDPR requirement, but we apply globally)
4. Public disclosure if >1,000 users affected or PHI involved
5. Post-mortem published within 30 days
6. Root-cause remediation tracked to closure

### Regulatory Inquiry
1. Legal activated immediately, no direct response without counsel
2. Preservation of relevant records
3. Cooperative stance default
4. External counsel engaged for significant matters (state AG, FDA, FTC)

---

## 7. Compliance Investment

Annual compliance spend projection:

| Category | Y1 | Y2 | Y3 | Y4 |
|----------|----|----|----|----|
| SOC 2 audit | $50k | $75k | $85k | $100k |
| Pen-testing + bug bounty | $60k | $90k | $140k | $200k |
| Privacy / security tooling | $40k | $100k | $180k | $280k |
| Legal (routine + compliance) | $120k | $220k | $350k | $500k |
| External audits (privacy, fairness) | $0 | $75k | $125k | $200k |
| Clinical regulatory | $80k | $380k | $750k | $400k |
| Insurance | $45k | $110k | $220k | $380k |
| **Total** | **$395k** | **$1.05M** | **$1.85M** | **$2.06M** |

Compliance is an investment, not a cost line item. The trust it buys is the moat.

---

## 8. Summary

This is a category where trust is the asset. The company that builds it fastest wins — and the company that loses it fastest disappears.

Our compliance and ethical posture is deliberately *more* rigorous than competitors. Not because we're required to — because the trust we earn compounds into retention, which compounds into unit economics, which compounds into financial sustainability. Every dollar spent on compliance returns $3–5 in retention over a 3-year horizon.

The only way this discipline breaks is founder impatience. Every investor pitch, every growth-team meeting, every quarterly review must reinforce: we hold these lines even when they're expensive. They're what makes the business possible.
