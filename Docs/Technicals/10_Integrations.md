# Integrations — Discipline OS

## 1. Integration Philosophy

1. **Every integration is a potential failure point.** Design for graceful degradation.
2. **No integration is load-bearing for T3.** Crisis flow must work with every third party offline.
3. **Signed BAAs or equivalent** for every integration that touches PHI.
4. **Vendor lock-in is a cost.** Prefer abstractions that allow swapping.
5. **Privacy-compatible first.** We do not integrate with advertising, attribution, or behavior-modeling SDKs.

---

## 2. Integration Map

| Partner | Domain | PHI? | Status v1.0 | Criticality |
|---------|--------|------|-------------|-------------|
| **Apple HealthKit** | iOS health data | Yes (on-device only) | Yes | High |
| **Android Health Connect** | Android health data | Yes (on-device only) | Yes | High |
| **Apple Watch / watchOS** | Wearable + complication | Yes (device-only) | Yes | Medium |
| **Wear OS** | Wearable | Yes (device-only) | Y1.5 | Low |
| **Oura** | Wearable sleep + HRV | Yes | Yes (OAuth) | Medium |
| **Whoop** | Wearable recovery | Yes | Yes (OAuth) | Medium |
| **Fitbit (Google)** | Wearable | Yes | Yes (OAuth) | Medium |
| **Garmin** | Wearable | Yes | Y2 | Low |
| **Clerk** | Auth, MFA, SAML/OIDC SSO, SCIM 2.0 | Yes (identity only) | Yes | High |
| **Enterprise IdPs (Okta/Azure AD/Google Workspace/Ping/OneLogin)** | SSO for enterprise tenants | Yes (identity only) | Yes | High |
| **Anthropic Claude API** | LLM content gen | No (system boundaries; **never on safety path**) | Yes | Medium |
| **Stripe** | Payments (web) | No (tokenized) | Yes | High |
| **Apple IAP / Google Play Billing** | Mobile payments | No | Yes | High |
| **APNs** | iOS push | No | Yes | High |
| **FCM** | Android push | No | Yes | High |
| **Web Push (VAPID)** | Web push notifications | No | Yes | Medium |
| **Twilio** | Voice/SMS (enterprise-tier optional) | Yes | Y2 | Low |
| **PostHog** (self-hosted) | Analytics | No (PHI-free event layer) | Yes | Medium |
| **Sentry** (self-hosted) | Crash reporting (mobile + 5 web apps + backend) | No (scrubbed) | Yes | Medium |
| **Lokalise** | Translation management (Enterprise BAA) | No (translators see catalog only) | Yes | Medium |
| **ElevenLabs** | Optional TTS for guided tools | No | Y1.5 | Low |
| **988 Lifeline (US)** | Crisis routing | No (tel: link) | Yes | High |
| **Per-locale hotline directory** | Country/locale-specific crisis hotlines (fr/ar/fa regions) | No (public directory) | Yes | High |

---

## 3. Apple HealthKit

### 3.1 Permissions requested

- Read: heart rate, HRV (SDNN, RMSSD), respiratory rate, step count, sleep analysis, mindful minutes, skin temperature wrist, workouts, standing/active energy.
- Write: mindful minutes (when user completes a tool).

### 3.2 Data flow

1. App requests permission on onboarding (explained contextually).
2. `HKObserverQuery` + `HKAnchoredObjectQuery` attach to each metric.
3. Native module aggregates samples into 60s/5min windows on-device.
4. Aggregates written to local SQLite; raw samples discarded from app memory after aggregation.
5. Windows optionally uploaded to `/v1/signals/windows` (user-toggleable).

### 3.3 Background delivery

- `HKHealthStore.enableBackgroundDelivery` for HR + HRV — allows elevated-state detection while app is backgrounded.
- Respects Low Power Mode: frequency halved.

### 3.4 Missing data handling

- Users without wearables: phone-only signals (unlocks, scroll velocity, step count via motion).
- State classifier retrained periodically for phone-only cohort; confidence thresholds adjusted higher.

### 3.5 Cross-device reconciliation

- HealthKit merges from multiple sources (Apple Watch + Oura, for example) — we prefer the "most authoritative" source per metric, documented in code.

---

## 4. Android Health Connect

### 4.1 Permissions

Equivalent read scopes: heart rate, HRV, sleep, steps, active calories, respiratory rate (where available).

### 4.2 Data flow

- `HealthConnectClient` for reads.
- Passive callback registration for real-time updates where supported.
- Foreground service only during elevated-state windows to keep passive delivery active on newer Androids.

### 4.3 Fragmentation

- Device-matrix tested: Pixel, Samsung S-series, OnePlus, Xiaomi.
- Samsung Health integration path considered Y2 (duplicative with Health Connect for most metrics).

---

## 5. Wearables (OAuth APIs)

Used when the user opts to grant additional data beyond what HealthKit / Health Connect surfaces.

### 5.1 Oura

- OAuth2 to Oura API v2.
- Pulls: readiness, sleep stages, HRV detail, temperature deviation.
- **Polling** rather than webhook (Oura has no webhook); every 15min via worker.
- User scope: read-only.

### 5.2 Whoop

- OAuth2 to Whoop API v1.
- Pulls: recovery score, strain, sleep.
- Webhook-based event delivery.

### 5.3 Fitbit

- OAuth2 via Google/Fitbit API.
- Pulls: HRV, sleep, heart rate, activity.
- Webhook subscription-based.
- Fitbit rate limits tracked; exponential backoff on 429.

### 5.4 Disconnection handling

- Token expiry surfaced as a "reconnect" prompt at next login.
- Background token refresh where API supports.
- Failed refreshes: degrade gracefully, inform user, keep phone-only signal path active.

---

## 6. Clerk

### 6.1 Scope

- Email + passkey + OAuth (Google, Apple) sign-in.
- Session management.
- mfa for staff accounts.
- Organization support for enterprise v2.

### 6.2 Custom session exchange

Discipline OS issues its **own** server session JWT after exchanging the Clerk token. This means our session, not Clerk's, drives user authorization inside the platform.

### 6.3 User lifecycle hooks

- `user.created` → create `users` row, default profile.
- `user.deleted` → trigger soft-delete pipeline.
- `session.ended` → no action (we trust our own).
- `session.revoked` → revoke server-side sessions for that user.

### 6.4 Transition plan

- At 500K users or v2 enterprise, evaluate moving off Clerk to a self-managed Ory Kratos or Supertokens stack.
- Migration dual-writes tokens for 90 days.

---

## 7. Anthropic Claude API

### 7.1 Usage patterns

- **Model routing:** Haiku 4.5 for most generation; Sonnet 4.6 for longer narrative (monthly letter); Opus 4.7 for internal reasoning tasks only (never user-visible outputs).
- **Prompt caching:** system prompts cached (they're identical across users) — significant cost savings.
- **Streaming** for weekly report; non-streaming for prompts that require safety-filter pass before display.

### 7.2 Rate + cost controls

- Per-user quota enforced before call.
- Global rate limit at 200 req/s.
- Budget alarm at 80% of monthly budget → degrade to template-only for non-paying users.

### 7.3 Safety pipeline

1. Pre-input scrubbing (PII, redactions).
2. Anthropic `input_schema` / structured outputs where applicable.
3. Post-output safety filter (local classifier).
4. Output cached only if safety-approved.
5. User-visible only after final review.

### 7.4 Failover

- If Anthropic is unavailable:
  - Weekly report falls back to a template-based version.
  - Reflection prompts fall back to a static library.
  - No crisis surface depends on Anthropic — ever.

### 7.5 BAA

- Signed BAA with Anthropic before any PHI-adjacent content sent.
- Audit review of what context we send quarterly.

---

## 8. Payment Processors

### 8.1 Apple IAP + Google Play Billing

- Primary mobile revenue path.
- Server-to-server notification subscriptions.
- StoreKit 2 on iOS for subscription entitlements.
- Play Billing Library 7+ on Android.
- Receipt verification server-side before entitlement grants.

### 8.2 Stripe (web + enterprise)

- Web subscriptions (small volume initially).
- Enterprise billing (invoice-based + Stripe Billing).
- Tokenized cards only; no card data on our infrastructure.
- SCA-compliant for EU.
- Webhook endpoints with signed payload verification.
- BAA with Stripe covering the subset of fields that could cross.

### 8.3 Cross-platform entitlement

- User's tier is truth-of-record in our DB (not in IAP).
- IAP and Stripe are both sources; we reconcile nightly.
- Users switching platform pick up entitlement after next IAP confirmation.

---

## 9. Push Notifications

### 9.1 APNs

- Token-based auth (p8 key).
- Critical alerts entitlement requested (enterprise/clinical SKU only).
- `apns-priority: 10` for T3, `5` for T1/T2.
- Collapse IDs used to prevent notification pile-up for nudge storms.
- NSE (Notification Service Extension) decorates payloads with rich content.

### 9.2 FCM

- Admin SDK for server-side dispatch.
- HTTP v1 API (v0 deprecated).
- Data-only messages for silent state updates; notification payloads for user-visible.
- Android 13+ notification permission handled at onboarding.

### 9.3 Delivery metrics

- Emitted from device on receipt via silent-push companion → allows us to measure actual delivery SLO, not just server send.
- Undelivered push triggers fallback channel (in-app on next foreground).

---

## 10. Crisis Resources

### 10.1 US: 988 Suicide & Crisis Lifeline

- `tel:988` link in crisis UI.
- No integration beyond the dial link; we do not proxy calls.
- Marketing partnership explored Y2.

### 10.2 International hotlines

- Maintained config table (`crisis_hotlines`) with country-code → hotline mapping.
- Refreshed quarterly from authoritative sources (IASP, SAMHSA).
- UI surfaces the appropriate hotline based on user's registered country + device locale.

### 10.3 Enterprise EAP integration (optional)

- Some enterprise customers have EAPs (Employee Assistance Programs) with dedicated phone lines.
- Clients can configure a custom "call your EAP" option in crisis UI.
- Phone number stored encrypted; shown only inside the user's own app.

---

## 11. Analytics

### 11.1 PostHog (self-hosted)

- Event-based analytics.
- **No PII in events.** We track event kind, cohort properties, engagement signals — never user content.
- Feature flags also drivable from PostHog as alternative to ConfigCat.
- Self-hosted on our own infra so event data never leaves our controlled environment.

### 11.2 Aggregates only for leadership

- Leadership dashboards powered by daily rollups, not raw events.
- Individual-level event lookup restricted to engineers + requires audit log entry + justification.

### 11.3 What we don't do

- No Segment-style customer data platforms.
- No attribution SDKs (Adjust, Appsflyer) — we do not run ad attribution.
- No Facebook / TikTok / Google pixels anywhere.

---

## 12. Error Reporting

### 12.1 Sentry

- Client + server.
- PII scrubbing configured at transport (message, breadcrumbs, extras sanitized).
- DSN rotated annually.
- Issue triage SLA: P1 within 4h, P2 within 24h.

### 12.2 Native crash reporting

- Crashlytics on mobile (supplemented by Sentry).
- Symbolication pipeline integrated in EAS build.

---

## 13. Email

### 13.1 Transactional

- AWS SES for transactional emails (welcome, email verification, export-ready, account-delete-initiated).
- DKIM + SPF + DMARC enforced.
- Send-from domain rotation strategy to minimize phishing abuse.

### 13.2 Marketing

- Deliberately minimal. Product-led organic primarily.
- If used: Customer.io or Resend; full unsubscribe compliance.

---

## 14. Marketing Site

### 14.1 Stack

- Next.js (React) SSR + ISR.
- Vercel-hosted (separate from product infra).
- No tracking scripts beyond a privacy-respecting analytics (Plausible or Fathom).
- CSP enforced; no inline scripts.

### 14.2 Key flows

- Waitlist signup (GDPR-compliant consent).
- App Store / Play Store deep-linked redirects.
- Methodology pages (long-form, SEO-optimized).
- Privacy + security pages.

---

## 15. Clinician Portal

### 15.1 Stack

- Next.js React + TypeScript.
- Separate auth realm (Clerk organization or Auth0 alternative).
- Deployed separately; isolated from consumer app infra at the ALB level.
- All reads/writes routed through same modular monolith backend via the `enterprise` / `clinical` modules.

### 15.2 Feature scope v2

- Patient list (consented only).
- Aggregate per-patient trend view.
- Secure messaging inbox to patients.
- Monthly insight export for session notes.

---

## 16. Calendar Integration (Y2)

### 16.1 Use case

- Pre-commitment: user sees risk-window on Friday 5pm and wants to auto-add "walk with Jamie" to calendar.
- Post-relapse review: calendar events surfaced as context.

### 16.2 Approach

- Google Calendar API (OAuth) + Apple Calendar (CalDAV / EventKit).
- Read-only by default; write only on explicit user action.
- No always-on syncing — minimal footprint.

---

## 17. Homekit / Smart Home (experimental, Y2+)

### 17.1 Premise

Some users want lighting or environmental changes as a "coping tool" (dim lights, play calming audio).

### 17.2 Scope

- Apple HomeKit shortcut invocation only; no on-behalf automation.
- Explicit user setup; opt-in per action.

---

## 18. Voice Assistants

### 18.1 Siri Shortcuts (iOS)

- "Hey Siri, urge check" → opens urge log.
- "Hey Siri, I'm struggling" → triggers crisis UI + starts urge-surf.
- Accessibility value: hands-free access in high-stress moments.

### 18.2 Google Assistant (Android)

- App Actions for urge log + SOS.
- Limited by current Google Assistant intent system.

### 18.3 No Alexa / no smart speakers.
- Rationale: household exposure risk. "My app heard that" is a privacy nightmare for intimate-threat users.

---

## 19. Integration Lifecycle

### 19.1 Onboarding a new integration

1. Propose in architecture review with PHI classification.
2. Security + legal review (BAA, DPIA if needed).
3. Build behind a feature flag.
4. Dogfood 30 days internal + beta.
5. Rollout 1% → 10% → 100%.
6. Document in this file + runbook.

### 19.2 Retiring an integration

- 90-day deprecation window.
- User-visible comms on dashboard.
- Data export offered where applicable.
- API keys rotated out; third-party deletion request issued.

---

## 20. What We Will Not Integrate With

- Ad networks
- Behavioral fingerprinting SDKs (Fullstory, Hotjar, LogRocket) — session replay is incompatible with PHI privacy
- Social login that requires public profile sharing
- Any tool without a BAA if it would touch PHI
- Any integration whose ToS reserves right to train on our user data
- **Any LLM provider on the crisis path (T3) or report-generation path.** The LLM never participates in producing numeric clinical values, scoring, or PDF content.
- **Any machine-translation service on shipped localized content.** MT is allowed only inside translator-facing tooling; a human translator signs off before content ships (see [15](15_Internationalization.md) §10).

---

## 21. Enterprise SSO reference integrations

Full spec: [14_Authentication_Logging](14_Authentication_Logging.md) §2.6. Reference implementations tested at launch:

- **Okta** — SAML 2.0 and OIDC; SCIM 2.0
- **Microsoft Entra ID (Azure AD)** — SAML 2.0 and OIDC; SCIM 2.0
- **Google Workspace** — SAML 2.0 and OIDC; SCIM 2.0 via third-party
- **Ping Identity** — SAML 2.0; OIDC
- **OneLogin** — SAML 2.0; OIDC; SCIM 2.0

Any other IdP that implements the same standards is supported; non-standard IdPs require a commercial conversation, not engineering work.

---

## 22. Per-locale hotline directory

Safety-critical structured data integration. Each entry is country- and locale-scoped, verified quarterly, versioned. Stored in `packages/safety-directory/` and bundled in every client release.

- `en-US`: 988 Suicide & Crisis Lifeline, Crisis Text Line (741741), Veterans Crisis Line
- `en-GB`: Samaritans (116 123), SHOUT text (85258)
- `en-CA`: 988, Kids Help Phone
- `fr-FR`: 3114 (suicide écoute), SOS Amitié
- `fr-CA`: 988 Canada (français)
- `ar-SA`: 920033360 (الخط الساخن للصحة النفسية); خط نجد 1919
- `ar-EG`: local resources per country verification
- `ar-AE`: local resources per country verification
- `fa-IR`: Omid Behzisti Line (1480)
- plus more per region as validated

A user's detected country (not locale alone) determines the shown directory. Updates to the directory are a separate, independently-gated release with clinical sign-off.
