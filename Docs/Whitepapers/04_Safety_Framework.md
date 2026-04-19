# Safety Framework — Crisis Response, Classifier Governance, and Clinical Oversight

**Version:** 1.0
**Audience:** Clinical Advisory Board, regulators, on-call engineering, enterprise customers' medical directors
**Abstract:** A behavioral health product must treat the safety path as a first-class engineering surface with its own architecture, its own SLOs, and its own governance. This document describes the Discipline OS safety framework: the design commitments that govern the crisis path (T3) and the escalation path (T4), the training and validation of the safety classifier, the per-locale hotline directory, the clinical oversight structure, and the incident-response runbook.

---

## 1. Design Commitments

These are architectural commitments, not preferences. Changing any of them requires Clinical Advisory Board sign-off.

1. **Deterministic.** The crisis path uses no large language model, no probabilistic routing, no experimental A/B test. Every user in every locale receives the same content for the same trigger.

2. **Offline-capable.** The full T3/T4 catalog is bundled on-device (mobile) and pre-rendered as static HTML on `crisis.disciplineos.com`. Loss of network does not degrade the surface.

3. **No safety path on a critical dependency we do not control.** Clerk auth failing must not disable the crisis button. LLM provider outage must not affect the crisis path. Postgres replica failover must not affect the crisis button's first paint.

4. **Latency as safety metric.** The crisis button goes from tap to first actionable screen in < 800ms cold, < 200ms warm, on mobile. `web-crisis` first-paint under 1.5s on 3G. **These are hard launch gates, not targets.**

5. **Per-locale.** Every supported locale has per-country hotline directories, locale-validated crisis copy reviewed by a clinical translator and a reviewer, and a culturally-appropriate flow (e.g. emergency numbers that actually work — 112 for EU, 911 for North America, 15 for France for medical, 999 for UK etc.).

6. **Logged, immutably.** Every safety-relevant event writes to `safety.log` (10-year retention + legal hold) with Merkle chaining and S3 Object Lock compliance mode. See `../Technicals/14_Authentication_Logging.md §9`.

7. **Audited by clinicians, monthly.** Sampled safety events are reviewed by on-call clinical advisors. False-negative patterns feed back into classifier retraining and catalog revisions.

---

## 2. The Four Tiers Revisited from the Safety Lens

| Tier | Safety implication |
|------|---------------------|
| **T0 (Ambient)** | No safety implication in itself; serves as the baseline state against which T1+ is detected. |
| **T1 (Urge rising)** | Low-stakes nudge; budget-capped; over-intervention fatigues the user and raises the risk they'll ignore a real T3. |
| **T2 (Urge elevated)** | Structured workflow. Tool selection by bandit. Still not a safety-grade surface — bandit exploration allowed. |
| **T3 (Crisis / SOS)** | **Safety-grade.** Deterministic tool selection (best-known for this user in this context). Offline catalog. 800ms cold-launch bar. |
| **T4 (Self-harm ideation)** | **Escalation.** Deterministic handoff to crisis line + per-locale hotline directory + user-configured emergency contact + clinician notification (if linked). |

The reason T3 and T4 are separated: T3 is about reducing urge intensity for a behavior the user is trying to change. T4 is about when the situation has moved beyond the scope of a behavioral app into a mental-health emergency. The system is designed so a T4 trigger from within a T3 flow is instant and visible, not buried.

---

## 3. T3 Crisis Path — Architecture

### 3.1 Catalog

The T3 catalog is a versioned, clinically-reviewed set of:
- Coping tool scripts (text + audio) per tool per locale
- Per-country hotline directory (§5)
- Decision-tree for "which tool first" given user state and history
- Follow-up templates (post-flow helpfulness capture, 24h follow-up)

Catalog is stored:
- **On-device (mobile):** bundled with the app binary; updated via OTA with clinical sign-off per update.
- **On `crisis.disciplineos.com`:** pre-rendered at build time; served via CloudFront; zero network dependency after first paint.
- **In the backend:** as a source-of-truth store; changes flow into a build step that regenerates both mobile bundles and the static site.

### 3.2 Tool selection at T3

Unlike T2 where a bandit selects, T3 uses a deterministic **highest-confidence tool** rule:

```
T3_tool(user, context) =
  argmax over tools in user's reviewed-effective set
    of (reward posterior mean for (user, tool, context))
  with tie-break by global efficacy
```

No exploration. No A/B test. If a user has not used the product long enough to have a posterior, we default to **Urge Surfing** (the safest, most-researched, best-generalized tool for acute craving) or **TIPP** (for crisis-grade distress).

### 3.3 Latency budget

| Segment | Budget |
|---------|--------|
| Cold launch (app not resident) | 600ms |
| App frame to T3 screen paint | 100ms |
| T3 interactive (buttons responsive) | 100ms |
| **Total T3 cold** | **800ms** |

For `web-crisis`: pre-rendered static HTML/CSS loads under 1.5s on 3G (verified in Playwright with network throttling on every PR).

### 3.4 Safety SLO

`sos.availability = 99.99%` over any rolling 30-day window, measured separately on each safety surface (iOS, Android, `web-crisis`). Violation triggers incident response (§9).

---

## 4. T4 Escalation Path — Self-Harm / Imminent Danger

### 4.1 Triggers

1. **User explicit.** Any screen with a visible "I'm having thoughts of self-harm" button; reachable in ≤ 2 taps from anywhere in the app.
2. **Safety classifier flag.** When the classifier running on journal or voice transcript content emits a high-confidence positive.
3. **PHQ-9 item 9 positive.** Any non-zero response on the suicide-ideation item during standard administration.
4. **C-SSRS positive.** Any positive response on items 1–6 of the C-SSRS severity scale (see `02_Clinical_Evidence_Base.md §2.10`).

### 4.2 Response

All of the following within 1 second of trigger:

1. **Per-locale hotline directory** (§5) displayed prominently.
2. **Local emergency number** (911, 112, 999, 15, etc.) rendered by locale, with tap-to-call.
3. **Crisis Text Line** where available.
4. **User-configured emergency contact** (if user has one), with pre-written SMS template the user can send with one confirmation tap.
5. **Deterministic supportive copy**, not LLM-generated, reviewed by clinical translator per locale.
6. **Follow-up check-in scheduled for 24h**, with sensitive opt-out.
7. **Event logged to `safety.log`** with timestamp, trigger source, and response chosen by user (if any). No journal content in the log — only the fact of trigger and the category.
8. **Clinician notification** if user has a linked clinician and has opted into emergency notification, within patient-selected scope.

### 4.3 What T4 does NOT do

- Does not call emergency services on the user's behalf. This is a conscious choice: unilateral emergency calls carry concrete risks (police response to a mental health crisis has been documented to produce additional harm in some demographics). We facilitate; the user acts.
- Does not block the user from using the rest of the app. The T4 flow is a resource, not a quarantine.
- Does not shame-nudge ("please contact this number"). Copy is supportive and non-coercive.

---

## 5. Per-Locale Hotline Directory

The hotline directory is keyed on (country × locale) and updated quarterly with clinical sign-off. Example entries:

| Country | Locale | Entry | Last verified |
|---------|--------|-------|----------------|
| US | en | 988 Suicide & Crisis Lifeline, Crisis Text Line HOME→741741, 911 | 2026-03-15 |
| UK | en | Samaritans 116 123, SHOUT text 85258, 999 | 2026-03-15 |
| Canada | en | 988 Suicide Crisis Helpline, 911 | 2026-03-15 |
| France | fr | 3114 (national suicide prevention), 15 (medical SAMU) | 2026-03-15 |
| Canada | fr | 988, 911 | 2026-03-15 |
| Saudi Arabia | ar | 920033360 (National Mental Health Helpline), 997 (Red Crescent) | 2026-03-15 |
| Egypt | ar | 08008880700 (General Secretariat of Mental Health), 123 | 2026-03-15 |
| UAE | ar | 800-HOPE (800-4673), 999 | 2026-03-15 |
| Iran | fa | Omid Behzisti 1480 (Welfare Organization Crisis Line), 115 | 2026-03-15 |

Directory structure (YAML) lives in `packages/safety-directory/` and is consumed identically by mobile and web surfaces.

**Verification protocol:** Quarterly automated check that the number accepts calls (handled by a designated contractor with clinical training, with explicit consent of the service), plus direct confirmation with the provider's public update channel. Missing verification within 90 days → automatic alert to Clinical Content Lead; hotline flagged "last verified > 90 days" in the UI with a clinician-reviewed fallback.

---

## 6. Safety Classifier — Training, Validation, Governance

### 6.1 Purpose

The safety classifier examines natural-language content (journal text, voice transcripts) for indicators of imminent self-harm or crisis-level distress. It is an input to T4 trigger decisions, never the sole decision.

### 6.2 Architecture

- Pretrained multilingual transformer (supports all 4 launch locales)
- Fine-tuned on a clinically-annotated dataset per locale
- **Runs on-device** — content never leaves the device for classification

### 6.3 Training data

- Clinician-annotated journal excerpts (synthetic + reshaped public corpora)
- Positive class: clear indicators of self-harm ideation, plan, intent, or behavior
- Negative class: distress, craving, anger, frustration that does NOT cross the safety threshold
- Per-locale training data with native-speaker clinician annotation
- Version-controlled; training corpus hash recorded with each model version
- No production user content used for training without explicit opt-in consent for the research warehouse (Phase 4+ RCT data under IRB only)

### 6.4 Performance bar

| Metric | Launch bar |
|--------|-----------|
| Recall (sensitivity) | **≥ 0.98** on held-out validation set |
| Precision | ≥ 0.75 (we accept more false positives to preserve recall) |
| F2 score (weights recall 2× precision) | Reported but not gating |
| Per-locale recall | ≥ 0.95 per launch locale (may be lower than global due to smaller per-locale validation set; above this we accept; below this we do not ship that locale) |

### 6.5 Dual-signal safeguard

The classifier decision is combined with a **keyword safety net**: a per-locale list of high-signal tokens maintained by clinical content lead. A keyword match triggers T4 regardless of classifier confidence. This prevents a classifier blind spot from missing a clear case.

### 6.6 Monthly review

Clinical advisors review a randomized sample of:
- False negatives (safety events that occurred without T4 firing) — highest priority
- Low-confidence positives (model fired but barely above threshold)
- Edge cases flagged by on-call during the month

Findings feed:
- Training set augmentation for the next model version
- Keyword list revisions
- Catalog copy revisions

### 6.7 Regression prevention

Every model version must clear the same validation set at the same bar. Any drop in recall ≥ 1 percentage point blocks the release. A rollback path is always maintained; rollback decision is Clinical Advisory + Head of Clinical joint sign-off.

### 6.8 Explicit non-goals

- We do not try to predict suicide statistically — this is a screening/routing tool, not a predictive risk-score.
- We do not replace C-SSRS — C-SSRS is the clinical instrument; the classifier is a routing aid.
- We do not claim medical-device accuracy. The product is not FDA-cleared at v1.0.

---

## 7. Clinical Oversight

### 7.1 Clinical Advisory Board

- Minimum 5 members: one psychiatrist, one licensed addiction clinician, one clinical psychologist, one psychometrician, one public-health or epidemiology background. At least one member culturally and clinically fluent in each launch locale (en, fr, ar, fa) — in practice, this may be a rotating member from the appropriate region.
- Quarterly review of: safety incidents, classifier performance, catalog updates, instrument additions, research roadmap.
- Annual review of: overall methodology, whitepapers, risk register.
- Any member can unilaterally require a pause of a specific product surface on safety grounds; resumption requires Board-level review.

### 7.2 Clinical Content Lead (staff)

- Owns the T3/T4 catalog, the psychometric instrument set, the hotline directory, the classifier training process.
- Reports to Head of Clinical, not to Engineering or Product.
- Has release veto on any change to the safety surface.

### 7.3 Head of Clinical (staff)

- Senior clinical leader; C-suite adjacent.
- Signs off on every release that touches the safety surface, the psychometric layer, or the classifier.
- Attends the Clinical Advisory Board meetings.

### 7.4 On-call clinical rotation

- 24/7 clinical on-call from public launch onward.
- Responsible for live triage of safety incidents, review of elevated-risk cases routed from the product, and coordination with external crisis services where appropriate.

---

## 8. Specific Populations and Risk Adaptations

### 8.1 Minors

**Not permitted.** The product does not onboard users under 18 at v1.0. Age is verified at signup; enterprise onboarding flows verify via HR attestation. A future minor offering (Phase 5+) would be a separate product with a separate risk model.

### 8.2 Users in active withdrawal

- Onboarding screens for severity. Users who self-report severe alcohol withdrawal symptoms (consistent with CIWA-Ar ≥ 10 equivalent) are presented with a clinical disclaimer recommending medical consultation; the product does not attempt to manage medical-grade withdrawal.

### 8.3 Users with recent suicide attempt

- If user discloses recent attempt during onboarding, the product orients toward supportive use plus clinical follow-up rather than standard closed-loop engagement. Clinical Content Lead has approved the onboarding flow for this population.

### 8.4 Users on concurrent medications or treatment

- The product does not assume no concurrent treatment. Copy is written to complement, not compete with, existing clinical care.
- Journal / clinician share feature is positioned for this use case.

---

## 9. Safety Incident Response

### 9.1 Incident classes

| Class | Definition | Response |
|-------|-----------|----------|
| **SI-P0** | Confirmed safety surface outage (`sos.availability` breach) OR confirmed classifier miss that contributed to harm | Immediate paging; Head of Clinical + CTO + on-call clinical; war-room within 15 min |
| **SI-P1** | Safety surface degradation OR classifier miss without confirmed harm | Paged within 30 min; triage within 2h |
| **SI-P2** | Catalog content issue (stale hotline number, translation concern) | Ticketed within 24h |

### 9.2 Runbook essentials

- On SI-P0, `crisis.disciplineos.com` serves as the fallback surface — always available even if the API is down.
- On safety-classifier-related SI-P0, dual-signal keyword net continues functioning; rollback to previous model version is pre-wired.
- Post-incident review is mandatory, written, and shared with Clinical Advisory Board within 2 weeks.
- Patterns trigger catalog revision, classifier retraining, or surface re-architecture as appropriate.

### 9.3 Breach and disclosure

- If a safety incident involves confirmed user harm, disclosure follows applicable regulation (HIPAA breach notification, HBNR, state rules).
- If a class of users is affected, transparent communication to that class.
- Aggregate incident data included in annual clinical report (no PHI).

---

## 10. What Would Cause Us To Pull a Surface

We state this explicitly because commitment is only real if the edge cases are pre-committed:

- `sos.availability` drops below 99.9% (one "9" below SLO) for 7 consecutive days on any safety surface → that surface is pulled until restored and reviewed.
- Classifier recall drops below 0.95 globally or 0.90 in any launch locale for a confirmed validation set → classifier is rolled back to prior version; if prior is insufficient, locale classifier is disabled and dual-signal keyword net becomes sole trigger, with banner disclosure.
- Confirmed clinical harm traceable to product design → Clinical Advisory Board convenes within 48h; surface or feature paused until review complete.
- Regulatory action → immediate compliance with the specific order; contest in parallel if warranted.

---

## 11. References

- **Posner, K., et al. (2011).** Columbia-Suicide Severity Rating Scale. *American Journal of Psychiatry*, 168(12), 1266–1277.
- **Kroenke, K., Spitzer, R. L., & Williams, J. B. W. (2001).** The PHQ-9. *Journal of General Internal Medicine*, 16(9), 606–613.
- **Nahum-Shani, I., et al. (2018).** JITAI design principles. *Annals of Behavioral Medicine*, 52(6), 446–462.
- **Torous, J., Bucci, S., Bell, I. H., Kessing, L. V., Faurholt-Jepsen, M., Whelan, P., Carvalho, A. F., Keshavan, M., Linardon, J., & Firth, J. (2021).** The growing field of digital psychiatry: current evidence and the future of apps, social media, chatbots, and virtual reality. *World Psychiatry*, 20(3), 318–335. https://doi.org/10.1002/wps.20883
- **Larsen, M. E., Nicholas, J., & Christensen, H. (2016).** A systematic assessment of smartphone tools for suicide prevention. *PLOS ONE*, 11(4), e0152285. https://doi.org/10.1371/journal.pone.0152285
- **Martinengo, L., Van Galen, L., Lum, E., Kowalski, M., Subramaniam, M., & Car, J. (2019).** Suicide prevention and depression apps' suicide risk assessment and management: a systematic assessment of adherence to clinical guidelines. *BMC Medicine*, 17, 231. https://doi.org/10.1186/s12916-019-1461-z
- **US FDA (2022).** *Software as a Medical Device (SaMD): Clinical Evaluation — Guidance for Industry and Food and Drug Administration Staff.*
- **AAMI TIR45:2012.** Guidance on the use of AGILE practices in the development of medical device software.
- **IEC 62304:2006 + A1:2015.** Medical device software — Software life cycle processes.
- **ISO 14971:2019.** Medical devices — Application of risk management.
