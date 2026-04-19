# 14 — Authentication & Logging / Observability

**Document:** Authentication, session management, audit logging, and observability
**Status:** Authoritative, production target
**Audience:** Backend, mobile, web, security, SRE, compliance
**Upstream dependencies:** 05_Backend_Services, 07_Security_Privacy, 08_Infrastructure_DevOps, 10_Integrations

---

## 1. Purpose

Authentication and logging are the product's **two most cross-cutting systems**:

- **Authentication** gates every request, every export, every clinician link, every enterprise portal session, across three product surfaces (iOS, Android, Web) and four locales (en, fr, ar, fa).
- **Logging** is the load-bearing substrate for security audit, HIPAA accounting of disclosures, SOC 2 observability evidence, production debugging, and — in a behavioral-health product — user-facing transparency about what we recorded and why.

Getting either one wrong is a class of bug that silently undermines clinical, legal, and user-trust guarantees for the life of the product. This document is authoritative.

---

## 2. Authentication

### 2.1 Identity provider

**Primary:** Clerk (with Enterprise BAA) handles the signup/login UI, credential storage, password policy, breached-password rejection, and MFA UI. We do **not** build our own auth UI.

**Rationale:** Auth UI is a known-fatal DIY surface for small teams. Credential stuffing, enumeration, breach-reuse, OAuth flow bugs, and MFA rollback attacks are all classes of bug that a specialist provider handles better than we can.

**Constraint:** Clerk issues its own session token, which is not what our backend wants to validate on every request (latency, coupling). We exchange Clerk's token for our **own server-signed session JWT** immediately after login. From that point forward, all requests carry our JWT, and the backend does not talk to Clerk on the hot path.

### 2.2 Session exchange

```
┌────────┐        ┌────────┐         ┌─────────────┐        ┌─────────┐
│ Mobile │        │ Clerk  │         │ /v1/auth/   │        │  Redis  │
│ / Web  │        │        │         │ exchange    │        │ (sess.) │
└───┬────┘        └───┬────┘         └──────┬──────┘        └────┬────┘
    │ login UI        │                     │                    │
    ├────────────────▶│                     │                    │
    │◀── clerk token ─│                     │                    │
    │                 │                     │                    │
    │ POST /v1/auth/exchange  (clerk token) │                    │
    ├────────────────────────────────────▶  │                    │
    │                                       │ verify clerk token │
    │                                       │─────▶ clerk /jwks  │
    │                                       │                    │
    │                                       │ upsert user        │
    │                                       │ issue session JWT  │
    │                                       │ write session rec  │
    │                                       ├──────────────────▶│
    │◀─ session JWT + refresh token ────────│                    │
```

Our session JWT:

- Signed with **EdDSA (Ed25519)** using keys in AWS KMS. KMS signs on request — private key never leaves the HSM boundary.
- **15-minute lifetime**; refresh token (opaque, Redis-backed) is 30-day rolling.
- Claims: `sub` (our user_id), `clerk_sub` (Clerk's id), `sid` (session id), `scope` (array), `amr` (auth methods — "pwd", "mfa_totp", "biometric", "sso"), `iat`, `exp`, `iss`, `aud`, `locale`, `tz`.
- **No PHI** in the JWT. No email, no name, no phone.

### 2.3 Refresh & revocation

- Refresh token lives **only** in secure device keychain (iOS Keychain with `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`, Android EncryptedSharedPreferences with StrongBox where available, Web `httpOnly`+`Secure`+`SameSite=Strict` cookie).
- Refresh rotates on every use. The old refresh is instantly invalidated and a new one issued. Reuse of an already-rotated refresh token is a **signal of compromise** — the entire session family is killed and the user is forced to re-authenticate across all devices.
- Server-side revocation is a Redis `SET` entry keyed by `sid`; a session is valid iff `EXISTS sid_active:{sid}` returns 1. TTL on the key matches the refresh lifetime, so revocations are cleaned up automatically.

### 2.4 Multi-factor authentication

- **All users are prompted to enable MFA on first login.** MFA is optional for consumer accounts but strongly recommended (the product handles sensitive psychometric data; MFA is a protective feature, not a bureaucratic one).
- **MFA is mandatory** for: clinician accounts, enterprise admin accounts, any account that has ever linked a clinician, any account with journal-share scope granted.
- **Methods supported:** TOTP (RFC 6238, any standard authenticator app), WebAuthn/passkeys (FIDO2), SMS as a **legacy fallback only** (disabled by default; SMS has known delivery issues in MENA and for Persian-speaking users on certain carriers, and is phishable).
- **Recovery:** 10 single-use backup codes generated at MFA enrollment, displayed once, stored by the user. Recovery also possible via verified email + 72-hour "sensitive action" delay for clinician-linked accounts.

### 2.5 Biometric app unlock (device-level)

Separate from authentication. Covered in 07_Security_Privacy. After login, the app can be locked on every background/foreground cycle with biometric unlock (FaceID/TouchID/BiometricPrompt). This is a **second gate on a still-valid session** — not a replacement for auth.

### 2.6 Sign-in methods

| Method | Consumer mobile | Consumer web | Clinician portal | Enterprise portal |
|---|:-:|:-:|:-:|:-:|
| Email + password | ✓ | ✓ | ✓ | via SSO |
| Apple Sign In | ✓ | – | – | – |
| Google Sign In | ✓ | ✓ | ✓ | – |
| Magic link (email) | ✓ | ✓ | ✓ | – |
| Passkey (WebAuthn) | ✓ | ✓ | ✓ | ✓ |
| SAML SSO | – | – | via contract | ✓ (required) |
| OIDC SSO | – | – | via contract | ✓ (required) |

Enterprise tenants **must** use SSO (SAML 2.0 or OIDC). SCIM 2.0 is provided for provisioning/deprovisioning. Enterprise tenants choose their own IdP (Okta, Azure AD, Google Workspace, etc).

### 2.7 Passkeys

Passkeys (FIDO2/WebAuthn) are the **recommended primary sign-in method** across platforms. Implementation:

- iOS 17+: Authentication Services framework, passkey-capable credential manager.
- Android 14+: CredentialManager API.
- Web: WebAuthn L3, with platform authenticator preference.

A user may register multiple passkeys across devices. Revocation is per-device. Passkey sign-in satisfies both "something you have" and "something you are" factors; a passkey + device biometric is sufficient and we do not require an additional OTP on top.

### 2.8 Sensitive actions (step-up auth)

The following actions require a **fresh authentication within the last 5 minutes** (step-up), even within an active session:

- Changing email, phone, or password
- Disabling MFA
- Linking or unlinking a clinician
- Revoking all sessions
- Requesting a full data export
- Requesting quick-erase (account deletion)
- Unlocking crisis-plan edits (the crisis plan itself is available immediately — editing it is the sensitive action)

The step-up prompt uses the strongest method the user has enrolled (passkey > TOTP > password). On failure, the attempt is rate-limited (5/hour) and audited.

### 2.9 Account lifecycle

| Event | What happens |
|---|---|
| Signup | User created; email verification required within 7 days or soft-lock |
| Email verification | `users.email_verified_at = now()`; MFA prompt shown |
| First login | Welcome flow; onboarding (see 04_Mobile_Architecture); locale captured |
| Password change | All sessions except current are revoked; user notified on every registered device |
| MFA enabled | Backup codes displayed once; all sessions except current revoked |
| MFA disabled | Sensitive-action step-up required; all sessions except current revoked; user notified |
| Clinician link requested | See 12_Psychometric_System §14 |
| Quick-erase | 24h soft-delete window with clear undo; then hard-delete cascade (see 07_Security_Privacy) |
| Inactive 24 months + no clinician link | Notification at 18, 21, 23 months; account archive at 24 months; 12-month recovery window |

### 2.10 Brute-force and abuse defenses

- Login attempts rate-limited per-identity (5/minute, 20/hour, 100/day) at Clerk + our own `/v1/auth/exchange` layer.
- Rate-limit by source IP additionally (1000/day per IP) — this blunts, not stops, credential-stuffing.
- Exponential back-off on failed attempts, returned in the 429 response body (in RFC 7807 format).
- Account lockout: after 10 consecutive failed attempts, account is soft-locked for 15 minutes; the user is emailed (without disclosing the lockout reason to the requester).
- No user enumeration: login failure messages are **uniform** regardless of whether the email exists.
- New-device detection: a successful login from an unrecognized device + IP geohash triggers an email to the user's verified address.

### 2.11 Compromise response

If a session family reuse is detected (old refresh replayed):

1. Kill the entire session family server-side (all children of the rotated root).
2. Force re-authentication with step-up on every registered device.
3. Email the user on the verified address: "We detected unusual activity on your account and signed you out everywhere. If this wasn't you, please change your password."
4. Write a `auth.session_family_killed` event to `audit_logs` with the reason.

### 2.12 Data minimization on auth

The auth system sees no PHI. It sees: email, phone (optional), name (optional), locale, tz, OAuth provider subject. It does not see: anything the user enters in-app after login.

---

## 3. Authorization

Authentication ≠ authorization. The session JWT carries coarse scopes (e.g., `consumer`, `clinician`, `enterprise_admin`). Fine-grained authorization lives in the application layer:

- **User-scoped resources:** Every operational endpoint checks `user_id in path == sub in JWT` or, for clinician access, `clinician_links.active AND scope includes resource`.
- **Enterprise-scoped resources:** Enterprise admin can only query aggregates for their own contract, enforced at SQL-view level (see 13_Analytics_Reporting §6.4).
- **Clinician-scoped resources:** Clinician can only read records for patients who have linked them with the relevant scope; `clinician_links.scopes` is consulted on every request and every access writes an audit log entry.

Authorization decisions are logged at the same fidelity as auth decisions. A denied decision is as informative as an allowed one for security monitoring.

---

## 4. Logging & observability

Logging in a behavioral-health product has competing requirements:

- **Legal:** HIPAA accounting of disclosures, SOC 2 evidence of access, GDPR Right of Access (users can request what we logged about them).
- **Clinical:** Safety-event auditability (we must be able to reconstruct exactly what a T3 crisis path did, and why).
- **Operational:** Debugging and performance.
- **Privacy:** We must not log PHI, not even accidentally in a stack trace or a 500 response body.

The architecture separates concerns by **log stream**, not just log level.

### 4.1 Log streams

| Stream | Contents | Retention | Destination | Queryable by |
|---|---|---|---|---|
| **app.log** | Structured JSON; request lifecycle, decisions, timings | 90 days hot / 2 years cold | CloudWatch Logs + S3 | SRE, on-call, product (read-only) |
| **audit.log** | Every access to PHI, every consent change, every clinician/enterprise action, every auth decision (allow+deny) | **7 years** (HIPAA) | Immutable S3 (Object Lock compliance mode) | Compliance, user (their own trail via `/v1/me/audit`) |
| **security.log** | Auth anomalies, rate-limit triggers, session family kills, suspicious IPs | 2 years | CloudWatch + SIEM | Security engineering |
| **safety.log** | T3/T4 events, hotline taps, safety-item positive, crisis-plan access | **10 years** (regulatory) | Immutable S3 (Object Lock legal-hold on T4) | Clinical lead, compliance |
| **trace** | OpenTelemetry spans | 30 days | Tempo (in-VPC) | SRE, engineering |
| **metric** | OpenTelemetry metrics | 400 days | Prometheus/Mimir (in-VPC) | SRE, engineering, SLO review |

Streams are written through separate writers with distinct IAM policies. A service role that writes `app.log` **cannot** write `audit.log`, and vice versa. This prevents a bug in application logging from corrupting the audit trail.

### 4.2 Structured log envelope

Every log line (except raw metrics/traces) is structured JSON. The envelope:

```json
{
  "ts": "2026-04-18T14:32:07.218Z",
  "stream": "app",
  "level": "info",
  "svc": "discipline-api",
  "env": "prod",
  "region": "us-east-1",
  "trace_id": "4fd0b5c1e7e9...",
  "span_id": "a2c1...",
  "request_id": "req_01HWXYZ...",
  "user_id_hashed": "sha256:abc123...",
  "tenant": "consumer",
  "module": "intervention",
  "event": "urge.handled",
  "msg": "Urge resolution recorded",
  "attrs": { "tier_used": "t2", "method": "urge_surf", "duration_ms": 142 }
}
```

- `user_id_hashed` is the SHA-256 of the user UUID with a per-environment salt. Never the raw user_id in `app.log`. Raw user_id lives only in `audit.log` and `safety.log`, where HIPAA requires it.
- `event` is from a fixed enum. Free-form strings are confined to `msg`, which is for human readers and never parsed for metrics.
- `attrs` is a PHI-safe bag of small values. Schema-checked at ingest.

### 4.3 PHI redaction

Two layers of PHI redaction:

**Layer 1 — at source.** Logging helpers accept typed arguments. A function like `log.info("urge_handled", user_id=uid, outcome=outcome)` has no place for free text. If someone writes `log.info(f"user {uid} said: {journal_text}")` — the linter rejects it (custom ruff rule `logging-no-fstring-interpolation`) and CI fails.

**Layer 2 — at sink.** A Fluent Bit filter at the log collector scans every line for PII/PHI patterns (emails, phone numbers, ICD codes, CPT codes, long free-form strings in `msg`) and redacts before durable storage. Matches are flagged to security.log for investigation.

Both layers exist because the source-level rule can be bypassed by new dependencies; the sink-level rule is defense in depth.

### 4.4 Audit log

`audit.log` is the HIPAA accounting-of-disclosures source of truth. Every PHI access writes one entry with:

- `ts` (server time, UTC)
- `actor_type`: `user` | `clinician` | `enterprise_admin` | `staff` | `system`
- `actor_id`: user_id of the accessor
- `subject_user_id`: user_id whose data was accessed (== actor_id for self-access)
- `action`: from a fixed enum (`read_profile`, `read_psychometric`, `read_journal`, `export_full`, `link_clinician`, `grant_scope`, `revoke_scope`, `admin_impersonate`, ...)
- `resource`: structured identifier of what was accessed
- `scope`: scope(s) under which access was granted
- `outcome`: `allowed` | `denied` | `partial`
- `reason`: structured reason code if denied
- `ip_hash`: hashed IP (full IP retained only in `security.log`)
- `request_id`: correlates with `app.log`

**Entries are append-only**; written to S3 with Object Lock in compliance mode, no possibility of edit or deletion for 7 years, full stop. Queryable via Athena over S3 for compliance reports.

Users can request their own audit trail via `/v1/me/audit` — this is a HIPAA Right of Access requirement.

### 4.5 Safety log

`safety.log` is a subset of audit/app logs with the highest retention (10 years) and legal-hold capability. Every T3 and T4 event writes to this stream — with no decision engine in the path that could silently drop an entry. A missing safety log entry is itself a P1 incident.

### 4.6 Tracing (OpenTelemetry)

- All services emit OTLP traces via the OTel collector (`infra/otel/config.yaml`) to Grafana Tempo.
- `trace_id` propagates through log lines (above). An engineer investigating a 500 can pivot from `app.log` entry → Tempo trace → spans → back to metrics.
- **Spans never carry PHI attributes.** `span.set_attribute("user_text", ...)` is forbidden; linter enforces.

### 4.7 Metrics

- **RED** (Rate, Errors, Duration) per endpoint, per module.
- **USE** (Utilization, Saturation, Errors) per infrastructure resource.
- **SLIs** for critical paths:
  - `sos.availability` — T3 crisis path success rate (target: 99.99%)
  - `sos.latency_p99` — T3 crisis path p99 latency (target: ≤ 600 ms including network fallback)
  - `api.auth.latency_p99` — target: ≤ 150 ms
  - `assessment.scoring.correctness` — regression-monitored at 100% (any drop is a P0)
  - `export.availability` — target: 99.9%
- Dashboards are pre-built per surface (consumer API, clinician API, enterprise portal, mobile, web) and reviewed weekly in SRE review.

### 4.8 Alerting

- **Paging alerts (P1):** Any drop in `sos.availability`, any `assessment.scoring.correctness < 100`, any audit log write failure, any T4 event that did not fire the expected callbacks, auth backend failing over 1% error rate.
- **Non-paging alerts (P2–P3):** Elevated latency, canary-deploy health, cost anomalies.
- Alert fatigue is explicitly tracked. Every paging alert that fires must be root-caused within one week; chronically noisy alerts are retired.

### 4.9 Log access for users (GDPR / HIPAA)

- `/v1/me/audit?from=...&to=...` — returns the user's access audit trail in JSON and CSV.
- `/v1/me/export` — full export includes a copy of the user's audit entries.
- On quick-erase, the audit log is **not** deleted. HIPAA and GDPR both allow this — compliance logs have a retention obligation that overrides user erasure. The user is informed of this before confirming erase.

---

## 5. Observability on mobile and web clients

### 5.1 Mobile

- **Crash reporting:** Sentry self-hosted in-VPC with PHI scrubber (same redaction as server logs). Stack traces only; no request bodies.
- **Analytics:** PostHog events (see 13_Analytics_Reporting §7.1) — PHI-free.
- **User-reportable diagnostic bundle:** User can tap "report an issue" which bundles the last 30 log entries (PHI-scrubbed), device model, OS version, app version, and uploads to a support queue. The user sees exactly what will be uploaded and can redact further.

### 5.2 Web

- Same Sentry instance, same scrubber.
- Web additionally records Core Web Vitals (LCP, INP, CLS) for SLO monitoring. These are PHI-free by definition.

### 5.3 Offline-first logs on mobile

When offline, the app buffers audit-relevant events in MMKV and flushes on reconnect. Buffer is signed per-entry so server-side tamper detection works. Buffer size is capped at 500 entries; oldest drop on overflow, and overflow itself is an audited event.

---

## 6. Backend module structure

```
services/api/src/discipline/
├── identity/
│   ├── auth_exchange.py        # /v1/auth/exchange (Clerk → our JWT)
│   ├── session.py              # session issue/refresh/revoke
│   ├── sensitive_action.py     # step-up middleware
│   ├── mfa.py                  # MFA enroll/verify (Clerk-backed)
│   ├── sso.py                  # SAML/OIDC (enterprise)
│   ├── scim.py                 # SCIM 2.0 provisioning endpoint
│   └── router.py
├── shared/
│   ├── logging/
│   │   ├── streams.py          # stream-aware logger (app/audit/security/safety)
│   │   ├── redact.py           # PHI redaction helpers
│   │   ├── envelope.py         # JSON envelope builder
│   │   └── middleware.py       # request_id, trace_id propagation
│   └── tracing.py
```

---

## 7. Test posture

- **Session family reuse test:** exercise full rotate-chain; assert family kill + user notification.
- **JWT claims test:** no PHI ever in claims (property test: enumerate 200 claim combinations).
- **Audit-log gap test:** attempt to write PHI access without going through the audit path; assert CI fails.
- **Redactor test:** ~500 crafted log lines including emails, phone numbers, dates-of-birth, ICD codes, journal-like free text; all must be redacted before S3 write.
- **Enterprise SSO test:** live SAML/OIDC against a dev IdP (Keycloak in a container); assert claims mapping, provisioning, and deprovisioning via SCIM.
- **Step-up test:** attempt sensitive actions without recent auth; assert 401 with `WWW-Authenticate: step_up`.

---

## 8. Out of scope

- In-app app-lock (biometric) — owned by 07_Security_Privacy.
- Clerk's own admin UI and billing — configured out of band.
- OS-level keychain internals — use platform primitives as documented.

---

## 9. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-18 | Initial authoritative specification including auth, session, MFA, SSO, logging streams, audit, safety log, observability |
