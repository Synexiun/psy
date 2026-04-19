# Security & Privacy — Discipline OS

## 1. Security Posture Statement

Discipline OS operates on a **clinical-grade, privacy-maximalist, defense-in-depth** posture. Our users are in vulnerable psychological states and often hide their use of the product from partners, employers, or roommates. A security breach here is not a PR event — it is a clinical harm event. We design every subsystem accordingly.

---

## 2. Threat Model

### 2.1 Threat actors

| Actor | Motivation | Examples |
|-------|-----------|----------|
| **Opportunistic attacker** | Low-effort credential stuffing, generic bots | Credential reuse from other breaches |
| **Targeted external attacker** | High-value PHI, re-identification | Nation-state, tabloid journalism |
| **Insider (malicious)** | Curiosity, coercion, revenge | Rogue employee, compromised clinician |
| **Insider (accidental)** | Misconfiguration, operator error | PHI leaked to log aggregator |
| **Intimate threat** | Surveillance of user by partner/employer | Abusive partner searching phone |
| **Legal adversary** | Subpoena, civil discovery | Divorce attorney, employer action |
| **Regulatory adversary** | State AG compliance audits | FTC, HHS OCR, state privacy AGs |

### 2.2 Most prioritized threats

1. **Intimate threat scenarios** — an abusive partner inspecting the user's phone. Mitigations: app-lock, alt-icon, quick-erase, no lock-screen previews.
2. **Lateral movement after endpoint compromise** — attacker lands on one backend node and reaches PHI. Mitigations: envelope encryption, per-user DEK, least privilege IAM.
3. **Subpoena over-compliance** — we produce less data under compulsion because we retain less. Mitigations: data minimization, 72h voice purge, federated model.
4. **Supply-chain attack via native modules** — malicious update to a dependency. Mitigations: SBOM, pinning, signature verification on OTA, reproducible builds.
5. **Social engineering of support** — "please export my friend's data." Mitigations: mfa for staff, recorded approvals, minimum-scope access, no email-based PHI recovery.

---

## 3. Identity & Authentication

**Full spec: [14_Authentication_Logging](14_Authentication_Logging.md).** Summary here.

### 3.1 User authentication

- **IdP:** Clerk (with Enterprise BAA). We exchange Clerk tokens for our own EdDSA session JWT (15 min), refresh token rotating (30 day rolling) — refresh reuse kills the session family.
- **Passkey-first:** passkeys (WebAuthn) recommended primary across mobile and web.
- **Fallback:** email magic-link with 10-min expiry.
- **SMS:** legacy fallback only, disabled by default (phishable; unreliable in MENA).
- **MFA:** TOTP + WebAuthn; mandatory for clinician/enterprise accounts and for consumer accounts that have ever linked a clinician.
- **Step-up auth** for sensitive actions (export, clinician-link, MFA changes) within last 5 minutes.
- **Enterprise SSO:** mandatory SAML/OIDC for enterprise admins; SCIM 2.0 for provisioning.
- **Anti-abuse:** per-identity (5/min, 20/hour, 100/day) and per-IP rate limits; new-device detection emails user.

### 3.2 Device attestation

- iOS: **DeviceCheck** + **App Attest** on every registration.
- Android: **Play Integrity API** on every registration.
- Device registration state tracked; anomalies (sudden device change, new country) trigger reauth.

### 3.3 App-lock

- Biometric (Face ID / Touch ID / Fingerprint) + optional 6-digit PIN fallback.
- In-memory DEK wiped on background; reauth required on foreground.
- Configurable grace period (0s / 30s / 5min).
- "Quick exit" gesture (swipe-down from anywhere) closes app and shows generic home screen.

### 3.4 Alt-icon / alt-name

- Settings → Privacy → "Alternative app presentation."
- Pre-signed alternate icons included in binary.
- Display name changes to the selected option (Reflect / Compass / Notes).
- Notifications respect this (the alt name is used in notification title when enabled).

---

## 4. Authorization

- **Scopes:** every endpoint declares required scope (`user:self`, `user:delete`, `clinician:read_consented`, `admin:retention`, etc.).
- **Role hierarchy:** `user` → `clinician` → `org_admin` → `internal_admin`. No transitive elevation.
- **Row-level checks:** every service method that accepts a user_id validates the caller's access. Lint rule forbids direct DB access without going through an authorization gate.
- **Clinician access:** only when `clinician_links.status = 'active'` AND patient consent present. Every read logged to `audit_logs`.
- **Internal admin access:** SSO-gated, mfa-required, audit-logged with extra fidelity. Exports require peer approval ("two-person rule") captured in the audit trail.

---

## 5. Encryption

### 5.1 In transit

- TLS 1.3 everywhere. TLS 1.2 accepted only for specific legacy wearables.
- HSTS preloaded (1-year max-age, includeSubDomains).
- Certificate pinning in mobile apps; pin rotation schedule + kill-switch.
- API gateway rejects non-TLS.

### 5.2 At rest

**Three layers:**

1. **Disk/volume encryption** (AWS EBS default).
2. **Database encryption** at the RDS level (KMS).
3. **Application-layer envelope encryption** for sensitive columns: journals, voice, crisis-contact, email.

Per-user DEK, wrapped by per-environment KEK, rotated 90-day.

### 5.3 Key management

- AWS KMS for KEKs.
- Separate KMS keys for prod, staging, dev.
- Per-region keys (US-East-1 primary, US-West-2 for DR).
- Key access audited via CloudTrail.
- Dual control for key deletion (operator + engineering lead).

### 5.4 Device-level

- iOS: `NSFileProtectionComplete` for journal + voice files.
- Android: `EncryptedFile` + `EncryptedSharedPreferences`.
- Keychain/Keystore for DEKs.
- Journal DEK never persisted unwrapped — requires app-lock unlock to decrypt.

---

## 6. Data Classification

| Class | Examples | Handling |
|-------|----------|----------|
| **Public** | Marketing copy, methodology pages | Standard |
| **Internal** | Aggregate metrics, cohort stats | Staff access only |
| **Confidential** | Subscription data, email, device IDs | Encrypted at rest, audit on access |
| **Highly Sensitive (PHI)** | Journals, voice, urge events, relapse events, state labels, crisis-contact | Envelope encrypted, BAA-scope, strict audit |
| **Clinical-legal** | Safety classifier flags, clinician notes | Highly Sensitive + dual-control operator access |

Data classification declared per table in schema annotations; linted in CI.

---

## 7. Privacy Principles (binding, not aspirational)

1. **Raw biometric samples never leave device.** Only aggregates.
2. **Voice blobs purged at 72h.** Enforced by S3 lifecycle + worker + audit.
3. **No advertising SDKs.** Ever. No exceptions.
4. **No behavioral data sold.** Privacy policy says this; corporate bylaws reinforce it.
5. **Minimum retention for functionality.** Aggressive purge jobs reviewed quarterly.
6. **User-controlled export + delete.** One-tap access.
7. **Quick-erase completes in <10 minutes.**
8. **Aggregate reports require cohort size ≥ 200.** No re-identifiable subgroups.
9. **Privacy changes require user re-consent.** Not a passive "we updated our policy" email.
10. **Clinician sees what patient explicitly shares.** Default: counts only, not content.

---

## 8. Compliance Frameworks

### 8.1 HIPAA

- **BAA required:** AWS, Clerk, Stripe (where tokens cross), Anthropic (API), Twilio (SMS/voice if used).
- **Administrative safeguards:** workforce training (annual), access reviews (quarterly), incident response (documented + tested).
- **Physical safeguards:** no on-prem; cloud provider safeguards via BAA.
- **Technical safeguards:** encryption, audit logs, integrity controls, person/entity authentication, transmission security.
- **PHI minimum necessary** principle enforced at API design.

### 8.2 GDPR

- **Lawful basis:** consent (primary); legitimate interest for anti-abuse telemetry only.
- **Data subject rights:** access, portability, rectification, erasure, restrict, object. All exposed via in-app tools, 30-day SLA.
- **DPO** appointed from Month 6.
- **DPIA** completed before launch and per major feature.
- **Data residency:** EU users' PHI stored in eu-central-1 by Y2.

### 8.3 SOC 2 Type II

- Audit window begins Month 14 (with launch).
- Type I report at Month 20, Type II at Month 30.
- Controls across Security, Availability, Confidentiality, Privacy (we defer Processing Integrity).
- Automated evidence collection (Drata or Vanta).

### 8.4 FDA SaMD (Clinical SKU, Y4)

- De Novo or 510(k) pathway TBD based on predicate landscape.
- Predicate candidates: reSET-O (addiction), Somryst (insomnia) as structural references.
- QMS: ISO 13485 adoption starts Y3.
- Design history file, risk management (ISO 14971), clinical evaluation report.
- Software lifecycle processes (IEC 62304) adopted earlier for muscle memory.

### 8.5 State-level

- CCPA/CPRA: access, delete, opt-out-of-sale (moot; we don't sell). Do-not-sell signal honored.
- Washington My Health My Data Act: notable because it expands PHI-equivalent to non-HIPAA contexts; our posture already compliant.
- Other states tracked via quarterly privacy legal review.

---

## 9. Audit Logging

### 9.1 What's logged

- Every read or write of PHI tables
- Every clinician access
- Every admin action (mfa event, export, retention override, model promote)
- Every consent grant/revoke
- Every login/session refresh
- Every rate-limit exceed
- Every export request

### 9.2 What's not logged

- User content (journals, voice — the log records access, not content).
- Request bodies that contain PHI (metadata only).

### 9.3 Retention

Four distinct log streams with distinct retentions, destinations, and writers. Full spec: [14_Authentication_Logging](14_Authentication_Logging.md) §4.

| Stream | Retention | Destination | Writer role |
|---|---|---|---|
| `app.log` | 90 days hot / 2 years cold | CloudWatch + S3 | Every service |
| `audit.log` | **7 years** (HIPAA) | S3 Object Lock (compliance mode) — immutable | `compliance` + `shared.logging` only |
| `safety.log` | **10 years** (+ legal-hold on T4) | S3 Object Lock + legal-hold capability | `compliance` + `shared.logging` only |
| `security.log` | 2 years | CloudWatch + SIEM | Security subsystem |

- Integrity: hourly log signing + tamper-evident chain (Merkle-style) on `audit.log` and `safety.log`.
- Writers are IAM-isolated — a service role that writes `app.log` **cannot** write `audit.log`. A bug in application logging cannot corrupt the audit trail.
- Users can query their own audit trail via `/v1/me/audit` (HIPAA Right of Access).
- On quick-erase, audit/safety entries are **not** deleted (compliance obligation overrides user erasure — users are informed of this before confirming erase).

---

## 10. Application Security

### 10.1 Input validation

- Every route declares Pydantic schema; rejection at middleware layer.
- SQL parameterized everywhere; ORM-free hot paths use a whitelist builder.
- JSON field size caps.
- File upload: signed presigned URLs only; no direct uploads.

### 10.2 Output encoding

- Automatic JSON encoding via FastAPI.
- Web (all sub-surfaces): Content Security Policy `default-src 'self'`, `script-src 'self' 'nonce-{…}'` with per-request nonces, no inline scripts or `eval`, `frame-ancestors 'none'`, `upgrade-insecure-requests`. Enterprise portal additionally rejects framing.
- HSTS `max-age=63072000; includeSubDomains; preload` on all web origins; submitted to the preload list.
- Web Push: VAPID-signed; payloads contain no PHI.
- CSRF: double-submit cookie pattern on state-changing endpoints from web origins.

### 10.3 Known vulnerability classes

| Class | Defense |
|-------|---------|
| SQL injection | Parameterized queries, repo-level review |
| XSS (web portal) | CSP, sanitization, React default escaping |
| CSRF | SameSite cookies, CSRF tokens on state-changing forms |
| SSRF | Egress allow-list from compute, URL validators |
| XXE | JSON-first; XML parsers hardened |
| Unsafe deserialization | No binary-object deserialization of user input; Pydantic strict mode |
| Broken auth | Centralized Clerk + mandatory mfa for staff |
| Broken access control | Scope checks at decorator level; lint rule enforces |
| Insecure design | Threat modeling per feature |
| Security misconfig | Terraform-as-baseline; drift detection |
| Vulnerable components | Dependabot + SCA (Snyk / GitHub Advanced Security) |
| SSL issues | Pinning + HSTS + monitored certs |
| Logging gaps | Coverage checks on PHI routes |

### 10.4 Dependency + supply chain

- SBOM generated per release (Syft).
- OSS licenses reviewed.
- Reproducible builds for native modules (iOS: reproducible archives; Android: deterministic gradle builds).
- Signed OTA model + JS updates; signature verified on device.

---

## 11. Mobile-Specific

### 11.1 Jailbreak / root

- Detection (e.g., iOSSecuritySuite, RootBeer) runs in background.
- Posture: warn user, **do not block**. Crisis users must not be locked out because of endpoint hygiene.

### 11.2 Screenshot / screen recording

- Journal detail screens: iOS `isCaptured` check → blur on capture attempt; Android `FLAG_SECURE`.
- Crisis screens: same protection.
- Feature-flag-controlled user override (some users want to save screenshots for their clinician).

### 11.3 Clipboard hygiene

- Any copy from a journal screen sets clipboard expiry on iOS; Android sets sensitive-content flag.

### 11.4 Anti-debug

- Debugger detection in release builds; suspicious memory maps trigger a telemetry event + soft reauth.

### 11.5 Background snapshot

- iOS: blur/placeholder view set in `applicationWillResignActive` so the task-switcher snapshot shows no content.
- Android: `FLAG_SECURE` covers this.

---

## 12. Backend-Specific

### 12.1 Network

- Private subnets for ECS, RDS, Redis.
- Public subnets only for ALB.
- NAT Gateway for outbound; egress allow-list via VPC endpoints for S3, KMS.
- WAF at CloudFront + ALB; OWASP top-10 rules + rate-based rules.
- DDoS: Shield Advanced on T3 critical endpoints.

### 12.2 Secrets

- AWS Secrets Manager; rotation on 90-day cadence.
- No secret in env files checked into VCS.
- Leaked-secret scanner (TruffleHog) in CI.

### 12.3 IAM

- Least privilege per service.
- No shared roles.
- Break-glass role requires approval workflow + audit.

---

## 13. Incident Response

### 13.1 Detection

- CloudWatch + Guard Duty + AWS Security Hub.
- App-level tripwires: audit-log anomalies, sudden export spike, off-hours admin ops.
- User-reported via `security@disciplineos.com` with PGP key published.

### 13.2 Severity tiers

| Tier | Definition | SLA |
|------|-----------|-----|
| **S0** | Confirmed PHI breach, active exploit | Immediate on-call page; CISO + CEO within 1h |
| **S1** | High-risk exposure, no confirmed exfil | 2h response; full team within 4h |
| **S2** | Elevated risk, containment in progress | 6h response |
| **S3** | Low-risk; non-PHI | Standard work-hours |

### 13.3 Playbook (abbreviated)

1. Page on-call + CISO.
2. War-room (Slack channel + Zoom bridge).
3. Containment first, forensics second.
4. Communications: external comms only after leadership approval.
5. Regulatory notice: GDPR 72h, HHS OCR per HIPAA if applicable, state AGs per state laws.
6. User notice: 72h max under GDPR; faster if clearly scoped.
7. Post-mortem: within 30 days, published externally for substantial incidents.

### 13.4 Drills

- Quarterly IR tabletop with engineering + clinical + legal.
- Annual red-team engagement.
- Disaster recovery drill: failover to DR region, under 4h RTO.

---

## 14. Data Subject Requests (DSR)

- Self-service primary: export + delete in app.
- Support-assisted fallback for accessibility cases.
- Staff workflow:
  - Identity verification (multi-factor; can't be satisfied by email alone).
  - Ticket opens audit entry.
  - Peer-approval required on any non-self DSR.

---

## 15. Vendor Management

- Vendor registry with classification tiers.
- BAA required for any PHI-adjacent vendor.
- Annual review.
- Tier-1 vendors (Clerk, AWS, Anthropic, Stripe) have executive escalation contacts.

---

## 16. Data Residency

- US users: us-east-1 (primary), us-west-2 (DR).
- EU users (Y2): eu-central-1.
- Canadian users (Y2): ca-central-1.
- No cross-region replication of PHI.

---

## 17. Penetration Testing

- External pen test annually + before major release.
- Mobile-specific pen test (both platforms) annually.
- Scope includes API, mobile apps, web portal, clinician dashboard, CI/CD.
- Critical findings fixed before release.

---

## 18. Bug Bounty

Post-launch (Month 16+):
- HackerOne or Intigriti hosted.
- Safe-harbor policy.
- Reward range: $100 – $25,000 based on severity + scope.
- Out-of-scope: social engineering, DoS, physical attacks.

---

## 19. Employee Security

- Mandatory security awareness training on onboarding + annual.
- Clinical-sensitivity training additional (see onboarding doc in Business).
- Device management (MDM) for all company laptops + phones.
- Access reviews quarterly; terminated-employee cleanup <1 business day.
- No production access from personal devices.

---

## 20. What We Will Not Do

- No backdoors for law enforcement. Subpoenas honored within legal requirements; no special access paths.
- No data sold, ever.
- No trackers in app beyond our own minimal, opt-out-able telemetry.
- No clear-text PHI anywhere — logs, error messages, CI artifacts.
- No "security by obscurity" — we publish our methodology and rely on defense in depth.

---

## 21. Public Commitments

Publicly posted and reviewed annually:
- Privacy Policy
- Security page with architecture summary
- Methodology page with clinical advisors
- Transparency report (starting Y2): DSR counts, subpoena counts, breach disclosures
