# 16 — Web Application

**Document:** Web application architecture across marketing, user app, clinician portal, and enterprise portal
**Status:** Authoritative, production target
**Audience:** Web engineers, design system, backend, SEO, clinical, compliance
**Upstream dependencies:** 03_API_Specification, 04_Mobile_Architecture, 07_Security_Privacy, 14_Authentication_Logging, 15_Internationalization

---

## 1. Purpose

Mobile (iOS + Android) is the primary product surface, but the web is **a first-class product surface**, not a landing-page afterthought. The web carries four distinct sub-surfaces:

| Sub-surface | Primary audience | Authentication |
|---|---|---|
| **Marketing** (`www.disciplineos.com`) | Prospective users, press, partners, clinicians evaluating | Public |
| **User app** (`app.disciplineos.com`) | Signed-in consumer users | Consumer session |
| **Clinician portal** (`clinician.disciplineos.com`) | Licensed clinicians, with patient-granted scope | Clinician session (MFA mandatory) |
| **Enterprise portal** (`enterprise.disciplineos.com`) | Employer, university, health-plan admins | SSO (SAML/OIDC), MFA mandatory |

Each sub-surface is a separate Next.js application in the monorepo. They share design tokens and utilities but are deployed independently with separate CDN configs, separate WAF rules, and separate observability dashboards. This isolation is intentional: a marketing-site regression should never be capable of affecting clinician-portal availability, and vice versa.

---

## 2. Why four apps instead of one

- **Blast radius.** A bug or compromise in marketing (high-change, heavy CMS usage, public-facing) must not touch clinician or enterprise surfaces (low-change, PHI-adjacent, regulated).
- **Auth surface separation.** Marketing is unauthenticated; clinician portal enforces MFA; enterprise portal enforces SSO. Running these in one app means conditional auth flows scattered through middleware — the higher-trust surfaces deserve their own perimeter.
- **Observability and SLOs.** Clinician portal availability is a clinical commitment (a clinician cannot see their patient's safety indicators). Marketing site availability is a business commitment. Different SLOs, different on-call treatment, different release cadences.
- **Build & deploy cadence.** Marketing iterates daily; clinician/enterprise portals ship on the regulated release train with release notes and clinical review.
- **Compliance.** Enterprise portal lives on the HIPAA BAA-covered perimeter. Marketing does not need to. Keeping them separate means the marketing team can iterate without HIPAA-review gating every copy change.

---

## 3. Stack

Per app (with minor variations):

- **Framework:** Next.js 15 with App Router; React 19.
- **Language:** TypeScript 5.6 with `strict: true` and `noUncheckedIndexedAccess`.
- **Styling:** Tailwind CSS v4 with shared design tokens (see §6). CSS uses logical properties throughout (see 15_Internationalization §4.1).
- **Server components:** Default. Client components only for interactive surfaces.
- **Data fetching:** TanStack Query for client-side; React server components for SSR/RSC data.
- **API client:** Shared `@disciplineos/api-client` package with typed routes (generated from OpenAPI — see 03_API_Specification).
- **Auth:** Clerk (see 14_Authentication_Logging) with Next.js middleware for session verification; our server JWT in an httpOnly cookie.
- **i18n:** `next-intl` with locale-aware routing (`/en`, `/fr`, `/ar`, `/fa`) and server-side locale negotiation (15_Internationalization).
- **Forms:** React Hook Form + Zod.
- **Charts:** Visx (D3 primitives) with our own locale-aware wrappers; charts flip in RTL (15_Internationalization §4.3).
- **Testing:** Vitest (unit), Playwright (E2E), axe-core (accessibility).
- **Hosting:** AWS Amplify or ECS Fargate behind CloudFront; decision per-app in 08_Infrastructure_DevOps.

---

## 4. What the web user app does and does not do

The consumer web app provides **feature parity with mobile for all non-crisis, non-biometric surfaces**:

| Feature | Mobile | Web user app |
|---|:-:|:-:|
| Daily check-in | ✓ | ✓ |
| Urge logging (T1/T2 interventions) | ✓ | ✓ |
| Journaling (text) | ✓ | ✓ |
| Weekly Reflection | ✓ | ✓ |
| Monthly Story | ✓ | ✓ |
| Psychometric assessments | ✓ | ✓ |
| Psychometric trajectories | ✓ | ✓ |
| Patterns view | ✓ | ✓ |
| Settings (profile, locale, clinician link, data export) | ✓ | ✓ |
| Crisis mode (T3) | ✓ primary | ✓ available, but mobile is directed as primary |
| On-device biometric signal intake (HR, HRV, sleep, activity) | ✓ | – (no comparable web capability) |
| Voice journal recording | ✓ | – (v1; v2 via WebAudio) |
| Push notifications | ✓ | ✓ via Web Push API |
| Apple Watch / Wear OS | ✓ | n/a |
| Widgets | ✓ | n/a |

### 4.1 Crisis (T3) on web

T3 is supported on web but the experience is **directed to mobile when both are available**. The rationale: the mobile app has offline-first deterministic T3 content (pre-bundled); a web client on a flaky network is a worse substrate for crisis support. The web T3 screen:

- Is fully static HTML/CSS/JS pre-rendered at build, no runtime API dependency.
- Is served from a separate origin (`crisis.disciplineos.com`) with its own uptime SLO (99.99%) and its own on-call.
- Offers the same tools (urge surf, TIPP 60s, call support) with the same copy (same locale catalog).
- Offers a "continue on mobile" deeplink that opens the app if installed.
- Never calls the LLM. Same rule as mobile: tested by `test_sos_is_deterministic` equivalent in the web test suite.

### 4.2 Biometric data on web

The web app does not capture wearable or biometric data. If the user is linked to HealthKit or Health Connect on mobile, those signals still flow server-side and are visible in the web app's analytics/trajectory views — but the web app is read-only for those streams. This is explicit in the UI.

---

## 5. Clinician portal

The clinician portal is primarily a **web product**. A licensed clinician uses a browser on a laptop in their practice; they do not want to review 14 patient dashboards on a phone. A small mobile-responsive variant exists for on-call convenience but is not a replacement.

### 5.1 Scope (v1)

- Patient list (only patients who have actively linked this clinician)
- Per-patient overview:
  - Psychometric trajectory charts (PHQ-9, GAD-7, PSS-10, WHO-5, AUDIT-C) with RCI annotations
  - Safety flags (PHQ-9 item 9, any C-SSRS positive)
  - Adherence timeline
  - Latest session note (from the patient's linked self-entry, if shared)
  - Clinical summary PDF download
  - FHIR R4 export download
  - HL7 v2 ORU download
- Request for expanded scope (requires patient approval via mobile)
- Clinician profile & MFA

### 5.2 Out of scope (v1)

- Direct clinical messaging (asynchronous messaging is a regulated channel and requires separate BAA analysis; v2).
- Tele-health video (never in scope — we integrate with partners, not build this).
- Prescribing (never in scope).
- Billing / superbills (v2).

### 5.3 Scope-gated rendering

Every patient-data view on the clinician portal checks `clinician_links.scopes` server-side before rendering. Missing scope → the section is not rendered at all (not a disabled/greyed view — literally absent). This is a privacy-protective default; a clinician should not see "journal share: NOT GRANTED" as a prompt to ask the patient to grant it.

### 5.4 Clinician MFA

MFA is mandatory and non-bypassable on this portal (14_Authentication_Logging §2.4).

### 5.5 Export controls

Downloads (PDF, FHIR, HL7) write an `audit.log` entry with clinician id, patient id, format, and timestamp. Documents are watermarked with clinician name and generation timestamp. The PDF is digitally signed so the recipient health system can verify authenticity.

---

## 6. Enterprise portal

The enterprise portal is a web product used by employer EAP administrators, university counseling center admins, and health plan program managers.

### 6.1 Scope (v1)

- Cohort size and enrollment cadence
- Aggregate engagement (DAU/MAU, retention) — k-anonymized
- Aggregate outcomes: PHQ-9, GAD-7, WHO-5 trajectories at cohort level with DP-noise (see 13_Analytics_Reporting §6)
- Crisis-path engagement rate (aggregate)
- Intervention acceptance rate (aggregate)
- Monthly signed-PDF report download
- Program configuration (branding on signup page, eligibility rules, SSO configuration)
- User provisioning via SCIM 2.0

### 6.2 Out of scope

- Any individual user data, including pseudonymous
- Any data export that could enable re-identification
- Messaging to cohort members (handled by a separate opt-in-per-user communication surface, not via enterprise admin)

### 6.3 Enterprise SSO

SSO is **mandatory** for enterprise admins. The enterprise portal does not offer a password sign-in form. Supported: SAML 2.0, OIDC. Reference IdPs: Okta, Azure AD, Google Workspace, Ping, OneLogin.

### 6.4 Portal-level k-anonymity and DP enforcement

The portal consults a **restricted SQL view** for all cohort data (see 13_Analytics_Reporting §6.4). Application code has no path to raw data. A test suite attempts to SELECT individual-level data via the portal's credentials and asserts failure.

---

## 7. Marketing site

### 7.1 Scope

- Home, product, features, pricing, clinician landing, enterprise landing
- **Help center** (see 18_Help_Content below) — hosted at `www.disciplineos.com/help` with full-text search, per-locale content
- **Whitepapers & research** — hosted at `www.disciplineos.com/research`
- Legal: Privacy Policy, Terms of Service, HIPAA Notice of Privacy Practices, Accessibility Statement
- Signup / download app CTAs

### 7.2 SEO and performance

- Server-rendered with minimal client JS.
- Core Web Vitals targets: LCP ≤ 2.0s, INP ≤ 150ms, CLS ≤ 0.05 at the 75th percentile.
- Sitemap per locale; hreflang on every page.
- Structured data: `MobileApplication`, `Organization`, `Article` on whitepapers, `FAQPage` on FAQ.
- `robots.txt` allows crawling; `/app`, `/clinician`, `/enterprise` subdomains disallowed from crawl.

### 7.3 CMS

Help content and whitepapers are authored as MDX in the repo (`content/help/`, `content/whitepapers/`). Marketing copy changes flow through a clinical-review gate **if** they touch product claims (efficacy, outcomes, clinical endorsement); plain marketing updates do not.

### 7.4 Content Security Policy

Strict CSP on all web surfaces:
- `default-src 'self'`; no inline scripts, no eval
- `script-src 'self' 'nonce-{…}'` with per-request nonces
- `img-src 'self' data: https://assets.disciplineos.com`
- `connect-src 'self' https://api.disciplineos.com https://sentry.internal`
- `frame-ancestors 'none'` everywhere; enterprise portal additionally refuses framing
- `upgrade-insecure-requests`
- Report-only mode during rollout, then enforcement

HSTS: `max-age=63072000; includeSubDomains; preload`; submitted to the preload list.

---

## 8. Design system

A shared design system lives in `packages/design-system/` and is consumed by mobile, all four web apps, and the email/PDF templates.

### 8.1 Shared tokens

- Colors (`graphite`, `signalBlue`, `calm`, `elevated`, `crisis`) — same semantics across platforms
- Spacing scale, radius scale
- Type scale — locale-aware (Latin vs Arabic/Persian — see 15_Internationalization §5.3)
- Motion durations and easings (with a `reduced-motion` variant)
- Z-index scale

### 8.2 Not shared

- Component primitives. React Native components (Pressable, View) and web components (HTMLButtonElement-based) have different accessibility models and cannot be a single component library. Each platform has its own component primitives that **implement the same token contract**.

### 8.3 Crisis palette

The `crisis` color and the T3 layout follow the same rules across platforms (04_Mobile_Architecture §X). The web T3 screen uses the same palette and the same deterministic copy catalog.

---

## 9. Accessibility (WCAG 2.2 AA)

All four web apps target WCAG 2.2 AA. The clinician portal additionally targets AAA for contrast, because clinicians use it for long periods and color-contrast fatigue is a known problem.

- Every interactive element has a visible focus indicator with ≥3:1 contrast against background.
- Form errors are announced via `aria-live="polite"`; crisis prompts use `aria-live="assertive"`.
- Every chart has a text-alternative table view (accessed via a toggle).
- Every page passes an axe-core CI check at build; regressions block merge.
- Keyboard navigation works for every user journey; tested in E2E suite.
- Reduced-motion is honored throughout.

---

## 10. Authentication on web

See 14_Authentication_Logging for the full spec. Web-specific notes:

- Session JWT in `httpOnly`, `Secure`, `SameSite=Strict` cookie.
- CSRF protection via double-submit cookie pattern for state-changing endpoints; GET endpoints are safe by construction.
- Clerk hosts the signup/login UI; we embed via Clerk's React components.
- Clerk token → our `/v1/auth/exchange` → our cookie; Clerk token is discarded after exchange.
- Sensitive actions require step-up auth (14_Authentication_Logging §2.8); web implements this via an overlay modal that re-prompts for passkey/TOTP.
- Concurrent sessions are allowed across devices; a dashboard shows all active sessions and allows per-device revocation.

---

## 11. Data export on web

The web app is the **canonical surface for full data export** (HIPAA Right of Access). Mobile can initiate export but downloads are more reliable on desktop browsers, and the export bundle (PDF + JSON + FHIR) is sized for desktop download. Export generation is asynchronous — the user gets an email when ready.

---

## 12. Progressive Web App (PWA) posture

- The consumer web app ships a service worker with an offline fallback for already-visited screens and the crisis content.
- "Install" is offered on supporting browsers but is not pushed aggressively — the native apps are the better mobile experience.
- Web push notifications available on supported browsers; opt-in at first value-moment, not on page load.

---

## 13. Rate limiting and abuse

- API calls from web are subject to the same rate limits as mobile (03_API_Specification) plus an additional per-origin limit at the edge (CloudFront + WAF).
- The enterprise portal has stricter rate limits given it holds admin credentials.
- Signup from web has anti-bot measures (hCaptcha self-hosted, behavioral signals) gated in front of Clerk.

---

## 14. Observability per sub-surface

Each app ships with:

- Sentry self-hosted project (separate project per app)
- OpenTelemetry browser SDK → same collector path as backend; `app.version`, `app.name`, `locale`, `tenant` tagged
- Core Web Vitals → same metric pipeline
- User-reportable diagnostic bundle endpoint

Dashboards per sub-surface are pre-built in Grafana; on-call rota is explicitly split by sub-surface.

---

## 15. Monorepo layout

```
apps/
├── mobile/                 (existing)
├── web-marketing/          www.disciplineos.com
├── web-app/                app.disciplineos.com (consumer)
├── web-clinician/          clinician.disciplineos.com
├── web-enterprise/         enterprise.disciplineos.com
└── web-crisis/             crisis.disciplineos.com (static, minimal)
packages/
├── design-system/          shared tokens + primitives per platform
├── api-client/             typed client generated from OpenAPI
├── i18n-catalog/           compiled string catalog
├── safety-directory/       per-locale hotline directory
├── eslint-config/
└── tsconfig/
```

---

## 16. Launch phasing (web)

The web apps launch on a staggered schedule:

| Phase | Surface | Gate |
|---|---|---|
| Phase 1 | Marketing + help + whitepapers | Copy, legal, SEO review |
| Phase 1 | Crisis static site | Safety review (same standard as mobile T3) |
| Phase 2 | Consumer web app | Feature parity with mobile (non-biometric surfaces) + full 4-locale content + WCAG AA |
| Phase 2 | Clinician portal | Clinical advisory sign-off + full audit-log verification + MFA mandated |
| Phase 3 | Enterprise portal | First enterprise contract signed + SSO reference implementations validated + k-anon/DP test suite green |

No sub-surface launches without its gate met, regardless of schedule pressure.

---

## 17. Out of scope

- Browser extension
- Email-only interface (not in roadmap)
- Desktop applications (Electron etc.) — mobile + web covers the need

---

## 18. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-18 | Initial authoritative specification |
