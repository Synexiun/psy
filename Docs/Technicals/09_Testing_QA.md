# Testing & QA — Discipline OS

## 1. Testing Philosophy

Testing this product is different from testing most software because **failure modes are clinical, not functional**. A missed push notification is a trivial bug anywhere else; here, it might be the intervention that wasn't there at the moment that mattered. Our testing strategy is built around that asymmetry.

Core principles:

1. **Crisis paths are tested to exhaustion.** T3/T4 flows get 10× the testing intensity of any other surface.
2. **Synthetic users exercise real pipelines.** We maintain personas as code.
3. **Clinical safety is a testing discipline,** not a separate review step.
4. **Beta is a testing tier.** Real-user signal gates release.
5. **Regressions are prevented with tripwires,** not just detected after.
6. **Testability is a design constraint.** Anything we can't test, we don't ship.

---

## 2. Test Pyramid

```
                          ┌──────────┐
                          │   Beta   │   (real users, 300-500 at v1.0)
                          └────┬─────┘
                               │
                       ┌───────┴────────┐
                       │  Clinical QA   │
                       │ (scripted flows│
                       │   vs advisor)  │
                       └───────┬────────┘
                               │
                    ┌──────────┴───────────┐
                    │     E2E (Detox)      │
                    │  20 golden flows     │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                │    Integration (API-level)  │
                │  ~600 tests, docker-compose │
                └──────────────┬──────────────┘
                               │
                ┌──────────────┴──────────────┐
                │          Component          │
                │   (RN + React Testing Lib)  │
                │         ~2,500 tests        │
                └──────────────┬──────────────┘
                               │
                ┌──────────────┴──────────────┐
                │            Unit             │
                │  (pytest + Jest; ~10,000)   │
                └─────────────────────────────┘
```

Coverage targets:
- Overall: **80%**
- `intervention`, `clinical`, `resilience`, `compliance`: **95%**
- Crisis flows (T3/T4): **100% — every branch**

---

## 3. Unit Tests

### 3.1 Backend (pytest)

- Hermetic; no network, no DB access at this layer — repositories mocked.
- Property-based tests via Hypothesis for state-machine logic (urge lifecycle, streak state).
- Fast: full unit suite <90s.

Critical tested logic:
- Streak state machine: every legal + illegal transition.
- Bandit arm selection: expected behavior across context permutations.
- Retention policy enforcement: computes correct delete targets.
- Safety classifier wiring: elevated/imminent outputs route correctly.

### 3.2 Mobile (Jest)

- Pure business logic in `features/**/logic/*.test.ts`.
- Reducers, selectors, offline queue, crypto helpers.
- <60s full run.

---

## 4. Integration Tests

### 4.1 Backend

- Real Postgres (docker-compose) + Redis + localstack S3.
- Each module has an integration suite: HTTP in, DB state out, side effects verified.
- Every API contract exercised with both happy + edge cases.
- Run time: <8 min in CI.

Example scenarios:
- `POST /v1/urges` → creates `urge_event`, returns bandit arm, schedules outcome watcher.
- `POST /v1/relapses` → creates `relapse_event`, streak preserved, compassion payload returned.
- `POST /v1/me/quick-erase` → all user rows deleted within 10 min window (test fast-forwards clock).

### 4.2 Mobile (component-level)

- React Native Testing Library renders full feature screens with mock providers.
- Navigation flows tested end-to-end within the JS side.

---

## 5. Contract Tests

- **Pact** between mobile app (consumer) and backend (provider).
- Every REST endpoint has a Pact contract file.
- CI fails on any drift.
- WebSocket message shapes also contracted via Pact-compatible JSON schemas.
- Third-party integrations (Anthropic, Stripe, Clerk) contract-tested via recorded VCR cassettes.

---

## 6. E2E Tests

### 6.1 Detox (React Native)

Runs on real simulators/emulators + a quarterly pass on physical devices via BrowserStack App Live.

Golden flows:

1. **Onboarding happy path** — new user, clinical profile, first check-in.
2. **Morning check-in → evening check-in** — 24h simulated.
3. **Urge log (T2) → tool → outcome recorded.**
4. **SOS (T3) → crisis flow → resolve.**
5. **Relapse report → compassion response → review.**
6. **Journal write → search.**
7. **Voice session → transcript → delete voice blob (72h simulated).**
8. **Pattern appears → dismiss.**
9. **Subscription upgrade via IAP (sandbox).**
10. **Cancellation flow.**
11. **Account deletion → recovery window.**
12. **Quick-erase → app signs out and wipes state.**
13. **Alt-icon enable → display confirms alt presentation.**
14. **App-lock → biometric → content gated.**
15. **Offline mode → queue mutations → flush on reconnect.**
16. **Push notification → deep link → intervention screen.**
17. **Widget tap → check-in shortcut.**
18. **Watch complication tap → urge log mini-flow.**
19. **Clinician invite → patient accepts → dashboard populated.**
20. **Export request → download → verify structure.**

Each runs on iOS + Android.

### 6.2 Performance E2E

- T3 flow: synthetic warm entry tests assert <200ms first-frame. 
- Dashboard scroll performance: asserts 60fps sustained over a 3s scroll.

---

## 7. Clinical QA

This is our differentiator. A **clinical QA reviewer** works with the engineering team each sprint.

Clinical QA responsibilities:
- Reviews all user-facing copy for:
  - Shame-adjacency
  - Diagnosis-adjacency
  - Absolute/guarantee language
  - Compassion-mode correctness after relapse
- Validates T3/T4 flows against deterministic scripts signed off by advisors.
- Approves every LLM prompt change before release.
- Audits monthly random sample of journals + LLM outputs (for pattern flags, never for content moralizing).

Release block: any clinical QA "blocker" flag halts the release.

---

## 8. Safety Testing

### 8.1 Adversarial inputs

- Prompts that try to elicit diagnoses or dangerous advice.
- Voice inputs simulating crisis language.
- Journal inputs containing suicidal ideation markers.

### 8.2 Safety classifier testing

- **Sensitivity set:** 500 curated positive cases (high-risk language). Required recall ≥98%.
- **Specificity set:** 2000 negative cases covering common false-positive traps ("I could kill for a drink").
- **Adversarial set:** obfuscation attempts. Required recall ≥90%.
- **Demographic slice:** recall per subgroup ≥96%.

Runs in CI on classifier PRs, monthly against live model.

### 8.3 Crisis-mode integrity

- Per-release smoke: trigger SOS, verify hardcoded payload served even with backend offline.
- Quarterly "backend-down" drill: SOS works with full network degradation.
- Device-level cache integrity: signed crisis templates verified on every app open.

---

## 9. Load Testing

### 9.1 Scenarios

- **SOS burst:** 1,000 concurrent SOS triggers → all served <800ms.
- **Check-in stampede:** 10,000 users submit within 2 min window (morning check-in surge).
- **Signal ingest storm:** 50,000 devices push 5min-windows simultaneously.
- **Notification fan-out:** 100,000 nudges dispatched in 10 min window.

Tool: Locust, scripted Python.

### 9.2 Acceptance criteria

- p95 latency within SLO under load.
- Error rate <0.1%.
- No PII in error logs.
- Resource saturation <70% at target RPS (headroom for spikes).

### 9.3 Cadence

- Pre-launch, monthly.
- Post-launch, quarterly + before any major rollout.

---

## 10. Security Testing

### 10.1 Static

- Semgrep rules (PHI-redaction, authorization check missing, insecure crypto patterns).
- Bandit (Python), SpotBugs (Java), Swift linting rules.
- Snyk / GitHub Advanced Security for dependency scanning.
- TruffleHog for secret scanning.

### 10.2 Dynamic

- OWASP ZAP automated scan against staging API.
- Burp Suite manual testing in quarterly cycles by external consultant.

### 10.3 Mobile-specific

- MobSF scans on every release binary.
- Android: OWASP MASVS verification.
- iOS: app transport security verification, entitlement audit.

---

## 11. Accessibility Testing

- Automated: `axe-core` (web), Accessibility Inspector (iOS), Accessibility Scanner (Android).
- Manual: VoiceOver / TalkBack walk-through of golden flows quarterly.
- Users with disabilities represented in beta cohort (paid research participants).
- Contrast checks on every color token change.

---

## 12. Internationalization Testing

- Pseudo-locale in CI catches hardcoded strings.
- Locale-specific date/time/number formatting test cases.
- Right-to-left stub validated to not break layout in core screens.

---

## 13. Beta Program

### 13.1 Tiers

- **Internal alpha:** 20 employees + trusted advisors. Runs continuously from Phase 0.
- **Closed beta (v0.5):** 300 invited users from waitlist. Phase 2.
- **Open beta (v0.9):** 1,500 users. Phase 3, ~60 days before v1.0.

### 13.2 Screening

- No users currently in acute suicidal ideation (self-reported at signup, scrutinized).
- Adult (18+) only at first.
- Users with supportive structure (therapist, partner) preferred for first cohorts.
- Compensation: beta access free through v1.0.

### 13.3 Consent

- Clear consent doc explaining experimental status.
- Access to hotlines prominent throughout app.
- Opt-in for weekly interviews.

### 13.4 Beta telemetry

- Extra instrumentation during beta.
- Weekly survey (5 questions).
- Bi-weekly 20-min interview with random sample of 10.
- Anonymized aggregate shared back with beta community monthly.

### 13.5 Beta release gates

Before moving beta → v1.0:
- WUH improvement > baseline at 8 weeks, statistically significant.
- Safety classifier zero missed incidents.
- Clinical advisor sign-off on methodology performance.
- No unresolved P0/P1 incidents in 30-day window.
- Cold-start p95 < 2s across device matrix.
- Crash-free sessions > 99.8%.

---

## 14. Post-Launch QA

### 14.1 Synthetic monitoring

- Synthetic transactions every 60s from multiple regions exercising SOS, check-in, urge log.
- Page if any fails.

### 14.2 Customer signal

- In-app "This didn't feel right" report on any intervention surface.
- Every report logged, triaged by clinical QA within 48h.
- Severe reports (intervention felt shaming, harmful) — clinical advisor review + root cause.

### 14.3 Weekly quality review

- Reviewed: top user reports, classifier misses, bandit regressions, LLM output samples, crisis flow telemetry, support ticket themes.
- Owners: Engineering lead + Head of Clinical + Product.
- Output: quality backlog prioritized into next sprint.

### 14.4 Incident postmortem cadence

- Every P0/P1 → blameless postmortem within 72h.
- Action items tracked; 90% completion within 30 days.
- Public postmortem for any user-impacting incident with >100 users affected.

---

## 15. Testing the Tests

- Mutation testing (Stryker for JS, mutmut for Python) quarterly on `intervention` + `clinical` modules.
- Test fixture freshness review: any fixture >12 months old re-validated against current schema.
- Flaky test policy: any test failing intermittently tagged within 72h; fixed or quarantined within 2 weeks.

---

## 16. QA Team & Process

- Embedded QA role in each squad (not a separate department).
- Dedicated **Clinical QA reviewer** (part of Clinical team, reviews at release cadence).
- Release manager rotates through engineering; owns the release checklist.

### Release checklist (abbreviated)

- [ ] All P0/P1 bugs closed
- [ ] Clinical QA sign-off on copy changes
- [ ] Load test passed against staging
- [ ] Safety classifier evaluation run
- [ ] E2E golden flows green
- [ ] SLO burn rate healthy 7 days
- [ ] Rollback plan documented
- [ ] On-call briefed
- [ ] Release notes published

---

## 17. What's Out of Scope

- Chaos engineering at v1.0 (deferred to Y2 when platform matures).
- Contract-tested SDK bindings for third-party clinicians (only internal contracts for now).
- Full IEC 62304 test traceability (staged in during Clinical SKU prep).

Each deferral is a registered design decision with a trigger for reconsideration.

---

## 18. Psychometric scoring fidelity tests

The psychometric module ([12](12_Psychometric_System.md)) has a zero-tolerance correctness requirement. Scoring drift between a versioned scoring function and its published reference is a P0.

- **Reference table per instrument.** Every instrument ships with a reference table of (responses → total_score, severity_band) pairs drawn from the original validation publication or an authoritative implementation. PHQ-9: ~200 reference rows; GAD-7: ~100; AUDIT-C + AUDIT: WHO-provided reference set; PSS-10: Cohen-provided reference set; WHO-5: WHO-provided.
- **Property test: additivity.** For scale instruments, scoring `responses` is equal to summing sub-item scores under the documented transformation (e.g., reverse-coding for WHO-5).
- **Version-pinned.** A scoring function's `version` is an input to the test; asserting `score_v1(x) == reference_v1(x)` and refusing to allow a silent upgrade.
- **Translation equivalence.** For a validated translation, the reference table is the translated-language reference; the test asserts the scoring function works identically on the localized item ordering (some translations re-ordered options).
- **SLI:** `assessment.scoring.correctness` = 100%, monitored nightly; a single drift is a pager.

---

## 19. Analytics & reporting tests

Privacy-protective behavior must be tested, not just specified ([13](13_Analytics_Reporting.md) §12).

- **Framing rule tests.** For each rule P1–P6: construct an adversarial input (a worsening trajectory; a one-point PHQ-9 delta; a week with 5 crisis entries) and assert the response body complies with the rule.
- **k-anonymity tests.** Synthetic cohorts of size 3, 5, 10, 25, 100; assert cohort < 25 refuses to render, cohort ≥ 25 with any cell < 5 suppresses that cell.
- **DP noise envelope.** Repeated generation on a fixed cohort yields varied published values with the expected noise envelope (ε = 1.0 default).
- **Report reproducibility.** Same inputs + same data_as_of → byte-identical PDF content (excluding render timestamp). Stable across deploys.
- **Re-identification red-team.** Quarterly exercise: a privacy engineer attempts to re-identify individuals from an enterprise report; findings remediated before quarterly sign-off.

---

## 20. Authentication & logging tests

Full list: [14](14_Authentication_Logging.md) §7. In-pipeline:

- **Session family reuse test.** Exercise full rotate-chain; reuse of rotated refresh kills the family and writes `auth.session_family_killed` to `audit.log`.
- **JWT PHI test (property-based).** Enumerate 200+ claim combinations; assert no PHI field ever appears.
- **Step-up test.** Sensitive actions without recent auth → 401 with `WWW-Authenticate: step_up`; after step-up, success within 5 min.
- **SSO live test.** SAML and OIDC against a dev IdP (Keycloak in a container) in CI; SCIM provisioning/deprovisioning asserted.
- **Redactor test.** ~500 crafted log lines including emails, phone numbers, ICD codes, DOB strings, journal-like text — all redacted before S3 write. Asserted as a unit test on the redactor and as an integration test through the shipper.
- **Audit gap test.** Attempt to read PHI without going through audit path; CI fails.
- **Log-stream isolation.** IAM simulation: can an `app` role write to `audit.log`? Expected: denied. Test covers prod IAM policies.

---

## 21. i18n / RTL tests

Full list: [15](15_Internationalization.md) §13. Snapshot and behavioral tests run per locale:

- **Snapshot per locale.** Every screen snapshot-tested in `en`, `fr`, `ar`, `fa`; RTL flip diffed separately. Review required on visual changes.
- **Bidi isolation.** Mixed-content strings have the Unicode isolates asserted.
- **Plural coverage.** Every count-bearing string has all required plural categories for the locale; Arabic's six categories enforced.
- **Digit correctness.** Clinical score displays use Latin digits regardless of locale. Date displays honor `digit_preference`.
- **Font availability.** Required glyphs render on every target device; `.notdef` box detection on screenshot captures.
- **RTL gesture.** Detox swipe-to-dismiss asserts reversed direction in RTL.
- **Safety content presence.** Per supported locale: every crisis string, every hotline, every intervention script has a non-empty, reviewed entry. Missing entry in a shipped locale fails CI.
- **MT fingerprint.** A heuristic lint on new translations flags suspiciously MT-looking additions for clinical review.

---

## 22. Web application tests

Full list: [16](16_Web_Application.md) §§9, 14. Per web sub-surface:

- **Playwright E2E.** Golden flows per surface; run in `en` and `ar` (RTL) at minimum.
- **axe-core on every route.** WCAG 2.2 AA; AAA for clinician portal. Regression blocks merge.
- **Web crisis static test.** `test_web_sos_is_deterministic` — asserts the crisis static page renders without any API call, has no network dependency (verified via Playwright network interception), and contains the same deterministic copy catalog as mobile.
- **CSP test.** Every response from every web origin passes the documented CSP contract; `script-src`, `frame-ancestors`, and `upgrade-insecure-requests` verified.
- **SSO integration test.** Enterprise portal refuses password sessions; accepts a SAML-issued session; rejects a SAML-issued session with mismatched audience.
