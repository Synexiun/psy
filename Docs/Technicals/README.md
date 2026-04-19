# Discipline OS — Technical Documentation

**Product:** Discipline OS
**Scope:** Full production architecture (not MVP)
**Surfaces:** iOS + Android + Web (marketing, consumer app, clinician portal, enterprise portal, crisis static)
**Launch locales:** English, French, Arabic, Persian (Arabic and Persian are right-to-left)
**Status:** Build-ready technical specification
**Audience:** Engineering, DevOps, Security, ML, Clinical, Compliance

---

## Document Index

| # | Document | Purpose |
|---|----------|---------|
| 00 | [Architecture Overview](00_Architecture_Overview.md) | System architecture, component map, philosophy |
| 01 | [Tech Stack](01_Tech_Stack.md) | Every technology choice, with rationale |
| 02 | [Data Model](02_Data_Model.md) | Complete database schema, entities, retention |
| 03 | [API Specification](03_API_Specification.md) | REST + WebSocket APIs, contracts, examples |
| 04 | [Mobile Architecture](04_Mobile_Architecture.md) | iOS + Android, React Native + native modules |
| 05 | [Backend Services](05_Backend_Services.md) | Modular monolith, services, jobs |
| 06 | [ML & AI Architecture](06_ML_AI_Architecture.md) | On-device + cloud ML, LLM usage, training |
| 07 | [Security & Privacy](07_Security_Privacy.md) | Encryption, threat model, compliance |
| 08 | [Infrastructure & DevOps](08_Infrastructure_DevOps.md) | AWS, Terraform, CI/CD, observability |
| 09 | [Testing & QA](09_Testing_QA.md) | Test pyramid, clinical safety testing |
| 10 | [Integrations](10_Integrations.md) | HealthKit, wearables, LLM, calendar, SSO IdPs |
| 11 | [Technical Roadmap](11_Technical_Roadmap.md) | Phased production build-out |
| 12 | [Psychometric System](12_Psychometric_System.md) | PHQ-9, GAD-7, AUDIT, WHO-5 etc. — validated instruments, scoring, safety items |
| 13 | [Analytics & Reporting](13_Analytics_Reporting.md) | User insights, clinician reports, enterprise aggregates, research warehouse |
| 14 | [Authentication & Logging](14_Authentication_Logging.md) | Auth, sessions, MFA, SSO, SCIM, audit/safety log streams, observability |
| 15 | [Internationalization](15_Internationalization.md) | i18n for EN/FR/AR/FA, RTL, typography, validated instrument translations |
| 16 | [Web Application](16_Web_Application.md) | Marketing, consumer web, clinician portal, enterprise portal, crisis static |

See also:
- `Docs/Whitepapers/` — research-backed whitepapers (methodology, clinical evidence, privacy, safety, research roadmap)
- `Docs/Help/` — intensive help content per surface, per locale

---

## Core Technical Principles

1. **Edge-first privacy.** Raw biometric data never leaves the device. ML inference runs on-device.
2. **Deterministic crisis path.** T3/T4 flows are hard-coded. Never LLM-generated. Sub-800ms SLO on mobile; static pre-rendered page on web.
3. **Modular monolith first.** Extract services only when scale demands. Premature microservices kill velocity.
4. **Clinical-grade schema from day 1.** Retrofitting clinical compliance is 10× more expensive.
5. **Observability-driven.** Every tier has SLOs + error budgets enforced at CI.
6. **Security as code.** Threat model reviewed per feature. Auth, logging, and audit trail are first-class (see [14](14_Authentication_Logging.md)).
7. **Radical data minimization.** Every stored field justifies its existence.
8. **Validated translations only.** No machine-translated clinical content. Psychometric instruments are presented only in languages where a validated translation exists.
9. **Protective framing in user-facing analytics; scientific rigor in clinician reports.** These cannot share a pipeline ([13](13_Analytics_Reporting.md)).
10. **Four product surfaces, four locales, one deterministic safety behavior.** Parity across platforms on everything except biometric capture; identical crisis copy in every locale.

---

## Tech Stack Summary (Detail in [01](01_Tech_Stack.md))

| Layer | Choice |
|-------|--------|
| Mobile | React Native 0.76+ (New Architecture) + Swift/Kotlin native modules |
| Web | Next.js 15 + React 19; Tailwind v4; next-intl for i18n |
| Backend | FastAPI (Python 3.12+) — modular monolith |
| Primary DB | PostgreSQL 16 |
| Time-series | TimescaleDB (PostgreSQL extension) |
| Cache / session | Redis 7 |
| Event streaming | Redis Streams → Kafka at scale |
| Blob storage | S3 (AWS, with Object Lock for audit/safety logs) |
| Vector store | pgvector |
| Server analytics | ClickHouse (in-VPC, HIPAA perimeter) |
| Auth | Clerk (consumer + clinician) + SAML/OIDC SSO + SCIM 2.0 (enterprise) |
| MFA | TOTP + WebAuthn/passkeys |
| On-device ML | CoreML (iOS), LiteRT (Android) |
| Cloud ML | AWS SageMaker |
| LLM | Anthropic Claude API (content generation only; never on safety path) |
| Product analytics | PostHog self-hosted (PHI-free event layer) |
| Observability | OpenTelemetry + Grafana + Tempo + Mimir + Loki |
| Error reporting | Sentry self-hosted |
| Feature flags | Unleash self-hosted |
| Translation ops | Lokalise (Enterprise BAA) |
| Fonts | Inter (Latin), IBM Plex Sans Arabic (Arabic), Vazirmatn (Persian) |
| Infrastructure | AWS (HIPAA BAA) — us-east-1 primary, us-west-2 DR, eu-central-1 Y2 |
| IaC | Terraform 1.8+ |
| CI/CD | GitHub Actions |
| E2E test | Detox (mobile), Playwright (web) |
| Accessibility | axe-core, WCAG 2.2 AA (AAA for clinician portal) |

---

## SLOs

| Path | Cold latency p95 | Warm latency p95 | Availability |
|------|------------------|------------------|:------------:|
| T3 Crisis (mobile SOS) | <800ms | <200ms | 99.99% |
| T3 Crisis (web static) | <600ms | <150ms | 99.99% |
| T2 Workflow | <1500ms | <400ms | 99.9% |
| T1 Nudge delivery | <5s (push) | — | 99.9% |
| Check-in submit | <500ms | <150ms | 99.9% |
| Psychometric assessment submit | <1500ms | <400ms | 99.95% |
| Pattern insight | <3s | <1s | 99.5% |
| Clinician portal (first paint) | <2s | <600ms | 99.9% |
| Enterprise portal | <2s | <800ms | 99.5% |
| Marketing site | <1.5s (LCP) | — | 99.95% |

Error budgets enforce these — violating tiers block feature releases.

---

## Quick Nav for New Engineers

- **New backend engineer:** [00](00_Architecture_Overview.md) → [02](02_Data_Model.md) → [05](05_Backend_Services.md) → [14](14_Authentication_Logging.md)
- **New mobile engineer:** [00](00_Architecture_Overview.md) → [04](04_Mobile_Architecture.md) → [15](15_Internationalization.md) → [10](10_Integrations.md)
- **New web engineer:** [00](00_Architecture_Overview.md) → [16](16_Web_Application.md) → [15](15_Internationalization.md) → [14](14_Authentication_Logging.md)
- **New ML engineer:** [06](06_ML_AI_Architecture.md) → [02](02_Data_Model.md) → [13](13_Analytics_Reporting.md)
- **New security engineer:** [07](07_Security_Privacy.md) → [14](14_Authentication_Logging.md) → [08](08_Infrastructure_DevOps.md)
- **Clinical lead / scientific reviewer:** [12](12_Psychometric_System.md) → [13](13_Analytics_Reporting.md) → `Docs/Whitepapers/`
- **Auditor / compliance reviewer:** [07](07_Security_Privacy.md) → [14](14_Authentication_Logging.md) → [02](02_Data_Model.md) → [08](08_Infrastructure_DevOps.md)
