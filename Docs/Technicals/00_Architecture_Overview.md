# Architecture Overview — Discipline OS

**Product surfaces:** iOS + Android + Web (marketing, consumer app, clinician portal, enterprise portal, crisis static).
**Launch locales:** `en`, `fr`, `ar`, `fa` (Arabic and Persian are right-to-left).
**First-class subsystems:** [Psychometric](12_Psychometric_System.md) · [Analytics & Reporting](13_Analytics_Reporting.md) · [Authentication & Logging](14_Authentication_Logging.md) · [Internationalization](15_Internationalization.md) · [Web](16_Web_Application.md).

## 1. System Philosophy

Discipline OS is a **closed behavioral control loop**. The architecture is the loop, not any single screen:

```
          ┌────────────────────────────────────────────────┐
          │                                                │
          ▼                                                │
     ┌─────────┐   ┌───────────┐   ┌──────────────┐   ┌──┴─────────┐
     │ SIGNAL  │──▶│  STATE    │──▶│ INTERVENTION │──▶│ REFLECTION │
     │ LAYER   │   │ ESTIMATION│   │ ORCHESTRATOR │   │ & LEARNING │
     └─────────┘   └───────────┘   └──────────────┘   └────────────┘
         ▲              ▲                 │                   │
         │              │                 ▼                   ▼
         │         ┌──────────┐     ┌──────────┐       ┌───────────┐
         └─────────│ CONTEXT  │     │ COPING   │       │PERSONALIZ.│
                   │ LAYER    │     │ TOOLKIT  │       │ ENGINE    │
                   └──────────┘     └──────────┘       └───────────┘
```

Every component exists to serve one of three loops:
- **Moment loop** (seconds–minutes): urge detected → intervention → outcome logged
- **Day loop** (24h): end-of-day reflection → user model update → tomorrow's nudge tuning
- **Epoch loop** (weekly / monthly): pattern report → user review → commitment adjustment

---

## 2. High-Level System Diagram

### 2.1 Client surfaces

The product runs on three client surfaces. See [16_Web_Application](16_Web_Application.md) for the full web breakdown.

```
┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────────────┐
│ iOS app          │   │ Android app      │   │ Web                           │
│ React Native +   │   │ React Native +   │   │ Next.js 15 per sub-surface:   │
│ native modules   │   │ native modules   │   │  www / app / clinician /      │
│ HealthKit, Watch │   │ Health Connect,  │   │  enterprise / crisis          │
│ widgets          │   │ Wear OS tiles    │   │  Locales: en, fr, ar, fa      │
└────────▲─────────┘   └────────▲─────────┘   └──────────────▲────────────────┘
         │                      │                             │
         └──────────────────────┴──────────────TLS 1.3─────────┘
                                               │
                                               ▼
                                 CloudFront + WAF (per-origin)
                                               │
                                               ▼
                                     FastAPI modular monolith
```

### 2.2 Backend

```
┌────────────────────────────────────────────────────────────────────────────┐
│                             MOBILE CLIENT                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ React Native (JS/TS) UI Layer                                        │  │
│  │ ── Screens, Components, State (Zustand) ──                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
│  │ Native Modules (iOS) │  │ Native (Android)    │  │ On-device ML     │   │
│  │ ─ HealthKit          │  │ ─ Google Fit        │  │ ─ CoreML (iOS)   │   │
│  │ ─ CoreLocation       │  │ ─ LocationManager   │  │ ─ TFLite (Android)│  │
│  │ ─ Notifications      │  │ ─ Notifications     │  │ ─ Whisper-small  │   │
│  │ ─ Watch complication │  │ ─ Tiles API         │  │ ─ Personal LSTM  │   │
│  └──────────────────────┘  └─────────────────────┘  └──────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Local SQLite (SQLCipher encrypted) + Secure Enclave keys              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────▲─────────────────────────────────────────┘
                                   │  TLS 1.3, mTLS for sensitive endpoints
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              EDGE / CDN                                    │
│                        (CloudFront + AWS WAF)                              │
└──────────────────────────────────▲─────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION TIER                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ FastAPI Modular Monolith (Python 3.12+)                              │  │
│  │ ─────────────────────────────────────────────────────────────────── │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │ │ Identity │ │  Signal  │ │ Interven-│ │ Reflect  │ │ Clinical │   │  │
│  │ │ Module   │ │  Module  │ │ tion Mod.│ │ ion Mod. │ │ Module   │   │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │ │ Pattern  │ │  Content │ │  Billing │ │Enterprise│ │  Safety  │   │  │
│  │ │ Module   │ │  Module  │ │  Module  │ │ Module   │ │ Module   │   │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ WebSocket Gateway (Crisis push, real-time state sync)                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Background Workers (Celery + Redis)                                   │  │
│  │ ─ Pattern computation  ─ Model retraining  ─ Insight generation      │  │
│  │ ─ Notification scheduling  ─ Report generation                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────▲─────────────────────────────────────────┘
                                   │
   ┌───────────────────────────────┼───────────────────────────────┐
   ▼                               ▼                               ▼
┌────────────────┐    ┌─────────────────────────┐    ┌─────────────────────┐
│ PostgreSQL 16  │    │  TimescaleDB (Hypertbl) │    │ Redis (Cache +      │
│ (Primary OLTP) │    │  ─ Urge events          │    │  Queue + Streams)   │
│ ─ Users        │    │  ─ Biosensor telemetry  │    └─────────────────────┘
│ ─ Subscriptions│    │  ─ Intervention outcomes│
│ ─ Content meta │    │  ─ Context snapshots    │
│ ─ Audit logs   │    └─────────────────────────┘
└────────────────┘
   │                               │
   ▼                               ▼
┌────────────────────┐    ┌─────────────────────────┐
│ S3 (Blob)          │    │ pgvector (Retrieval)    │
│ ─ Voice journals   │    │ ─ Content embeddings    │
│   (E2E encrypted)  │    │ ─ Similar-user features │
│ ─ User exports     │    └─────────────────────────┘
└────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL SERVICES                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Clerk (Auth) │ │ Stripe (Pay) │ │ OneSignal    │ │ Anthropic    │      │
│  │              │ │              │ │ (Push)       │ │ (Content LLM)│      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ PostHog      │ │ Sentry       │ │ Grafana      │ │ Datadog      │      │
│  │ (Analytics)  │ │ (Errors)     │ │ (Metrics)    │ │ (APM, opt.)  │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Map

### 3.1 Mobile Client Components

| Component | Purpose | Tech |
|-----------|---------|------|
| UI Layer | Screens, navigation, state | React Native + Zustand |
| Native Bridge | iOS/Android device APIs | Swift/Kotlin native modules |
| On-device ML | Urge prediction, NLP | CoreML, TFLite |
| Local Store | Encrypted local DB | SQLCipher SQLite |
| Secure Keys | Encryption keys | Secure Enclave / Keystore |
| Background Tasks | Passive telemetry collection | iOS BGProcessingTask, Android WorkManager |
| Widget / Watch | Fast-path entry | SwiftUI widgets, WearOS tiles |
| Notification Handler | Push actions, deep-links | Native |

### 3.2 Backend Modules (Modular Monolith)

| Module | Responsibilities | Primary doc |
|--------|-----------------|---|
| **Identity** | Session exchange, MFA, SSO (SAML/OIDC), SCIM, step-up auth, profile, consent | [14](14_Authentication_Logging.md) |
| **Signal** | Ingest check-ins, passive telemetry, wearable data | [05](05_Backend_Services.md) |
| **State** | State estimation outputs, relapse risk scoring | [06](06_ML_AI_Architecture.md) |
| **Intervention** | Orchestrator policy, tool selection, delivery | [05](05_Backend_Services.md) |
| **Reflection** | Journals, structured CBT prompts, voice journals | [05](05_Backend_Services.md) |
| **Pattern** | Pattern computation, insights | [05](05_Backend_Services.md) |
| **Content** | Content delivery, microlearning, RAG | [05](05_Backend_Services.md) |
| **Personalization** | Contextual bandit, next-best-intervention | [06](06_ML_AI_Architecture.md) |
| **Safety** | T4 classifier, crisis escalation, safety logging | [07](07_Security_Privacy.md) |
| **Clinical** | Clinician portal API, outcomes export | [16](16_Web_Application.md) §5 |
| **Enterprise** | Admin portal API, SCIM, aggregate reporting | [16](16_Web_Application.md) §6 |
| **Billing** | Stripe integration, subscription state | [05](05_Backend_Services.md) |
| **Notification** | Push scheduling, context-aware triggers | [10](10_Integrations.md) |
| **Psychometric** | Instrument catalog, scoring engine, trajectories, safety items | [12](12_Psychometric_System.md) |
| **Analytics** | User insights (framed), patterns surfacing, rollups | [13](13_Analytics_Reporting.md) |
| **Reports** | Clinical PDF, FHIR R4, HL7 v2 ORU, user export, enterprise aggregates | [13](13_Analytics_Reporting.md) |
| **Content (i18n)** | Per-locale safety directory, intervention scripts, help content | [15](15_Internationalization.md) |
| **Shared: logging streams** | app / audit (7y) / safety (10y) / security log streams | [14](14_Authentication_Logging.md) §4 |

### 3.3 Data Stores

| Store | Purpose | Sizing (Y3) |
|-------|---------|-----------:|
| PostgreSQL | OLTP, user profiles, relational | ~300 GB |
| TimescaleDB | Time-series events, biosensors | ~5 TB |
| Redis | Cache, queues, streams | ~32 GB |
| S3 | Voice, exports, backups | ~12 TB |
| pgvector | Content + user embeddings | ~100 GB |

---

## 4. Data Flow: A Complete Moment

### User-initiated SOS (T3)

```
[User taps SOS on widget]
    │
    ▼
[iOS widget → App Intent → open app into Crisis scene]
    │ <200ms native
    ▼
[Crisis Scene pre-loaded at app launch — not waiting on network]
    │
    ▼
[Default tool workflow starts immediately]
    │
    ▼   (async)
[Outcome logged to local SQLite]
    │
    ▼
[Background sync pushes to backend when connectivity restored]
    │
    ▼
[Signal ingestion → Pattern module → Personalization bandit update]
    │
    ▼
[Next-best tool recommendation updated for this user+context]
```

**Critical:** every step except the final personalization update is local. The user never waits on the network during a crisis.

### System-initiated urge prediction

```
[On-device LSTM running every 5 min in foreground]
    │
    ▼
[Detects urge-risk spike: urge_prob(t+30min) > threshold]
    │
    ▼
[Check local nudge budget, cooldown, quiet hours]
    │
    ▼
[If passes → schedule local notification]
    │    (no backend call — runs on device)
    ▼
[User sees notification]
    │
    ▼
[User taps → quick tool workflow]
    │
    ▼
[Outcome captured + synced]
```

### Daily reflection

```
[Evening prompt appears (user-chosen time)]
    │
    ▼
[User completes 60s check-in in app]
    │
    ▼
[Local SQLite write → Background sync]
    │
    ▼
[Backend Signal module ingests]
    │
    ▼
[Aggregated daily → TimescaleDB]
    │
    ▼
[Pattern module runs nightly job (batch)]
    │
    ▼
[If actionable insight surfaced → available in dashboard tomorrow]
```

---

## 5. Deployment Topology

### Production

- **Region:** AWS us-east-1 (primary), us-west-2 (failover), eu-central-1 (Y2)
- **Availability Zones:** 3 AZs in primary region
- **Networking:** VPC with private subnets for DB, public subnets for ALB only
- **Compute:** ECS Fargate for API; Next.js web apps on Fargate or Amplify per-surface (see [16](16_Web_Application.md) §3)
- **Database:** RDS PostgreSQL Multi-AZ + TimescaleDB extension
- **Cache / session:** ElastiCache Redis with failover
- **Columnar analytics:** ClickHouse (in-VPC, HIPAA perimeter) for server-side analytics ([13](13_Analytics_Reporting.md) §7.2)
- **CDN:** CloudFront, distinct distribution per web sub-surface
- **WAF:** AWS WAF rules + custom rate limits, per-origin policies
- **Immutable audit storage:** S3 with Object Lock (compliance mode) for `audit.log` (7y) and `safety.log` (10y) ([14](14_Authentication_Logging.md) §4.1)

### Environments

| Environment | Purpose | Data |
|-------------|---------|------|
| `local` | Developer laptops | Fake fixtures |
| `dev` | Shared dev cluster | Seeded fake data, no real users |
| `staging` | Pre-prod mirror | Scrubbed real-shaped data or synthetic |
| `production` | Real users | Live |
| `clinical` | Clinical SKU (Y3+) | HIPAA-segregated, BAA scope |

### EU Deployment (Y2+)

Separate AWS eu-west-1 deployment with data residency:
- EU users served from EU region only
- Cross-region replication only for non-PHI metadata
- Separate DB instances, separate S3 buckets

---

## 6. Scalability Strategy

### Traffic Phases

| Scale | DAU | Approach |
|-------|-----|----------|
| Launch | 5k | Single-region monolith, standard sizing |
| 50k DAU | 50k | Vertical scaling, read replicas |
| 250k DAU | 250k | Extract Signal + State modules to dedicated services |
| 1M+ DAU | 1M+ | Multi-region active-active, service mesh |

### Scale-Out Triggers

- TimescaleDB write throughput > 70% capacity → add write replicas
- Postgres CPU > 65% for 5 days sustained → vertical upgrade
- API p95 latency drift > 20% over baseline → architectural review
- Redis memory > 75% → cluster resize

### The Golden Rule

**Don't extract services until one of them is both slow and independently scalable.** Premature microservices have killed more startups than slow monoliths.

---

## 7. Fault Tolerance & Graceful Degradation

### Crisis Path (T3) Must Never Fail

- Every T3 tool is functional **fully offline** on device
- Crisis UI pre-loaded in memory at app launch
- Local SQLite guarantees state persistence through network failures
- Multiple push providers (OneSignal + native APNs fallback)
- On-device T4 (crisis escalation) has hard-coded numbers — never dynamic

### Non-Crisis Degradation

| Failed component | Fallback |
|------------------|----------|
| Backend API down | App fully functional, sync deferred |
| On-device ML model corrupted | Revert to population prior |
| Push service down | Next backend sync triggers catch-up |
| Personalization engine down | Use last cached recommendation |
| Pattern module down | Existing cached insights shown |
| Voice transcription fails | User can retype manually |
| LLM content generation fails | Pre-cached content served |

---

## 8. Security Architecture at a Glance

(Detail in [07 Security & Privacy](07_Security_Privacy.md))

- TLS 1.3 all in-transit
- AES-256 at rest (DB, S3)
- E2E encryption for voice journals (user-held keys via device Secure Enclave / Keystore)
- Pseudonymization at ingestion (user_id → opaque ID for analytics storage)
- Role-based access + just-in-time elevation for support
- Full audit log, immutable, offline-shipped
- Zero-trust model: every service authenticates every call

---

## 9. Observability Architecture

- **Tracing:** OpenTelemetry across all services + mobile → Grafana Tempo
- **Metrics:** Prometheus → Grafana
- **Logs:** structured JSON → Loki
- **Error tracking:** Sentry (mobile + backend)
- **Product analytics:** PostHog self-hosted
- **SLO tracking:** error budgets enforced at CI

**Separation of concerns:** product analytics and therapeutic data live in different stores with different access controls. Engineers can query product analytics; no one gets raw therapeutic data outside of consented, audited flows.

---

## 10. Build-vs-Buy Decisions

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Auth | Buy (Clerk) | Well-solved, not our value-add |
| Payments | Buy (Stripe + App Store + Play) | Same |
| Push | Buy (OneSignal) with native APNs/FCM fallback | Failover matters |
| Analytics | Buy (PostHog self-hosted) | Privacy posture, extensibility |
| LLM inference | Buy (Anthropic) | Not our moat |
| Wearable SDKs | Build wrappers | Critical tight integration |
| On-device ML | Build | Core differentiator, privacy requirement |
| Therapeutic content | Commission from licensed clinicians | Quality + legal |
| Crisis classifier | Build with clinical oversight | Safety-critical |
| Email | Buy (Postmark or Resend) | Standard |
| Error tracking | Buy (Sentry) | Standard |

---

## 11. Architecture Decision Record (ADR) Summary

Selected ADRs locked at architecture design. Full ADRs in `/decisions/` directory.

- **ADR-001:** React Native over Flutter — wearable SDK ecosystem + native escape hatch
- **ADR-002:** Modular monolith over microservices at launch — velocity over premature abstraction
- **ADR-003:** PostgreSQL + TimescaleDB over separate time-series — operational simplicity
- **ADR-004:** Edge ML for inference, cloud for training — privacy requirement
- **ADR-005:** Clerk for auth (v1), custom at scale — ship fast, migrate when enterprise demands
- **ADR-006:** Anthropic for LLM content — API quality, safety posture
- **ADR-007:** AWS over GCP — HIPAA ecosystem maturity
- **ADR-008:** Contextual bandit over reinforcement learning — explainability, safety
- **ADR-009:** E2E for voice/journal, not for structured data — operational tradeoff
- **ADR-010:** No microservices until 250k DAU — premature decomposition is costly

---

## 12. Summary

The architecture is deliberately boring in its bones: a modular monolith with a Postgres family, React Native mobile apps, Next.js web apps, and AWS infrastructure. Where it gets interesting is in the principles layered on top:

- **The crisis path is local, deterministic, offline-capable** on mobile, and pre-rendered static on web.
- **The personalization engine is distributed between device and cloud.**
- **Privacy is architectural, not a checklist.** Auth, logging, and the audit trail are first-class systems ([14](14_Authentication_Logging.md)).
- **Psychometric instruments and reporting are first-class products**, not feature garnish ([12](12_Psychometric_System.md), [13](13_Analytics_Reporting.md)).
- **Four locales including two RTL scripts, with validated-only clinical translations.** ([15](15_Internationalization.md))
- **Scale comes from simplicity, not distributed complexity.**

Every detail that follows in subsequent docs reinforces these principles.
