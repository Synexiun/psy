# Tech Stack — Discipline OS

Every technology choice with version, rationale, and alternative considered.

**Surfaces covered here:** iOS, Android, Web (marketing, consumer, clinician, enterprise, crisis). See [16_Web_Application](16_Web_Application.md) for the per-surface web breakdown and [15_Internationalization](15_Internationalization.md) for the i18n stack decisions.

---

## 1. Mobile — Client Application

### React Native 0.76 (New Architecture, Fabric renderer, TurboModules)

- **Why:** Cross-platform velocity with a small team; native escape hatch where needed.
- **New Architecture specifically:** Fabric renderer + TurboModules eliminate legacy bridge latency; critical for T3 <800ms SLO.
- **Alternative considered:** Flutter (rejected — weaker wearable SDK ecosystem); fully native Swift + Kotlin (rejected — 1.8x engineering cost at this stage).
- **Native modules we will write:**
  - HealthKit bridge (Swift)
  - Google Fit bridge (Kotlin)
  - BackgroundTasks (Swift + Kotlin)
  - Widget data provider (SwiftUI + Kotlin Tile)
  - CoreML inference bridge (Swift)
  - TensorFlow Lite inference bridge (Kotlin)

### Supporting libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `zustand` | ^5.0 | Client state management (lighter than Redux) |
| `@tanstack/react-query` | ^5.0 | Server state sync |
| `react-navigation` | ^7.0 | Navigation |
| `expo-modules-core` | Latest | When selectively useful |
| `react-native-mmkv` | ^3.0 | Fast key-value store (pre-SQLite) |
| `@op-engineering/op-sqlite` | Latest | Fast SQLite + SQLCipher integration |
| `react-native-webrtc` | (deferred) | For future voice-coach features |
| `react-native-reanimated` | ^3.0 | Animations (used sparingly) |
| `react-native-gesture-handler` | ^2.0 | Gestures |
| `i18next` + `react-i18next` + `i18next-icu` | Latest | i18n with ICU MessageFormat |
| `react-native-localize` | ^3.0 | Device locale detection |
| `react-native-restart` | ^0.0.27 | Reload on locale/RTL toggle |

### Local Database

- **SQLite via SQLCipher** — AES-256 encrypted at rest
- Keys stored in iOS Keychain / Android Keystore (Secure Enclave-backed)

### Bundler / Build

- **Metro** (standard) with custom `metro.config.js` for heavy-asset rules
- **EAS Build** or self-hosted (Expo's EAS for simplicity at launch, consider self-hosted at scale)

### Mobile Testing

- Jest (unit)
- Detox (E2E)
- Maestro (E2E, modern alternative considered)
- XCUITest + Espresso (critical path native tests)

---

## 2. Backend — API & Services

### Python 3.12+ with FastAPI

- **Why Python:** ML-adjacent team alignment (same language for data science, backend, model serving)
- **Why FastAPI:** async-native, excellent OpenAPI generation, type hints throughout, battle-tested at scale
- **Alternative considered:** NestJS (TypeScript) for stack-unified team; rejected because ML ecosystem is Python-native
- **Go was considered** for performance — rejected because team leverage on Python for ML tooling is too valuable

### Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ^0.110 | Web framework |
| `uvicorn` | ^0.27 | ASGI server |
| `pydantic` | ^2.6 | Validation + serialization |
| `sqlalchemy` | ^2.0 | ORM (for relational) |
| `alembic` | ^1.13 | Migrations |
| `psycopg` | ^3.1 | Postgres async driver |
| `celery` | ^5.3 | Background jobs |
| `redis` | ^5.0 | Cache + broker |
| `pydantic-settings` | ^2.2 | Config management |
| `httpx` | ^0.27 | HTTP client |
| `tenacity` | ^8.2 | Retry logic |
| `structlog` | ^24.1 | Structured logging |
| `opentelemetry-api` | Latest | Tracing |
| `anthropic` | Latest | Claude API client |
| `posthog` | Latest | Analytics SDK |
| `stripe` | Latest | Payments |

### Package Management

- **uv** (Astral) — fast dependency resolver
- `pyproject.toml` as single source of truth
- `uv.lock` committed

### Python Tooling

- **Ruff** — linter + formatter
- **mypy** — strict type checking
- **pytest** — testing

---

## 3. Databases

### PostgreSQL 16

- Primary OLTP store
- Managed via AWS RDS Multi-AZ
- Version 16 specifically for improved replication and query performance
- **Backup:** automated daily + point-in-time recovery (35-day window)
- **Read replicas:** added at 50k DAU

### TimescaleDB 2.14+ (extension on the same Postgres)

- Hypertables for time-series data
- Continuous aggregates for dashboard queries
- Compression policies (7 days raw → 30 days compressed → cold after 180)
- **Why same Postgres:** operational simplicity vs. separate InfluxDB/Timestream; extracted only at scale
- **Alternative considered:** separate InfluxDB — rejected for ops complexity; Timestream — rejected for vendor lock

### Redis 7

- Cache, queue broker, Redis Streams at early scale
- ElastiCache managed
- Cluster mode from Day 1 for horizontal scaling

### pgvector (extension)

- Content embeddings, user-similarity features
- Used for RAG on content library
- 1536-dim (OpenAI ada) or 3072-dim (Anthropic) depending on embedder choice

### S3

- Blob storage (voice journals, exports, clinical trial data)
- AES-256 server-side encryption
- Versioning enabled
- Cross-region replication for EU compliance

---

## 4. On-Device ML

### iOS: CoreML

- **Why:** Apple Neural Engine hardware acceleration
- **Model format:** `.mlpackage`
- **Tooling:** `coremltools` Python library for export from PyTorch / TF
- **Size target:** <30MB per model

### Android: TensorFlow Lite / LiteRT

- **Why:** Best Android on-device ML support, GPU + NNAPI delegates
- **Model format:** `.tflite`
- **Tooling:** TF Lite converter

### Models Run On-Device

| Model | Size | Purpose |
|-------|------|---------|
| Urge-trajectory LSTM | ~8MB | Short-horizon urge prediction |
| Context classifier | ~2MB | Home / work / risk-zone classification |
| Whisper-small (distilled) | ~120MB | Voice journal transcription |
| CBT-structure extractor | ~15MB | Parse transcribed voice into CBT fields |

### Model Distribution

- Embedded in app bundle (versioned)
- Post-launch: delta updates via secure CDN
- Fallback: if local model fails, cloud inference available for non-crisis paths

---

## 5. Cloud ML

### AWS SageMaker

- Training pipelines
- Federated learning aggregator
- Batch inference for pattern detection
- Model registry + versioning

### Libraries

- **PyTorch 2.3+** for model authoring
- **scikit-learn** for classic models (bandit baselines)
- **Vowpal Wabbit** considered for contextual bandit (fast, production-proven)
- **River** considered for online learning

### LLM Integration

- **Primary:** Anthropic Claude API
  - Haiku 4.5 for high-volume, cost-sensitive content tasks
  - Sonnet 4.6 for reflection-prompt adaptation and nuanced content
  - Opus 4.7 reserved for quality-critical content generation (rare use)
- **Bounded use:**
  - Content generation (gated by clinical review)
  - Voice journal structuring
  - Never at T3/T4 crisis paths
- **Cache policy:** aggressive prompt caching (5-min TTL per Anthropic standard)
- **Safety:** strict content policy; no medical advice generation

---

## 6. Authentication

Full spec: **[14_Authentication_Logging](14_Authentication_Logging.md).**

### Clerk (identity provider)

- **Why:** passkey-first, OAuth, MFA, SAML/OIDC enterprise SSO, SCIM 2.0, Enterprise BAA available.
- **Alternative considered:** Auth0 (higher cost at scale), WorkOS (enterprise-strong but consumer-weaker), rolling our own (auth UI is a fatal DIY surface for a small team — rejected).
- We do not use Clerk's session on the backend hot path. We exchange Clerk's token for our **own EdDSA-signed session JWT** via `/v1/auth/exchange`, cached in Redis, signed via KMS.

### Session

- 15-minute access JWT (EdDSA/Ed25519 via AWS KMS)
- 30-day rolling refresh token in device keychain (iOS) / EncryptedSharedPreferences + StrongBox (Android) / `httpOnly Secure SameSite=Strict` cookie (web)
- Refresh family rotation; reuse detection kills the family and forces re-auth
- Session revocation via Redis key presence (`sid_active:{sid}`)
- Sensitive actions (export, clinician-link, MFA-change) require step-up auth within 5 min

### MFA

- **TOTP** (RFC 6238, any authenticator app)
- **WebAuthn / Passkeys** (FIDO2) — recommended default; Apple Authentication Services, Android CredentialManager, WebAuthn L3
- SMS as legacy fallback only (disabled by default; phishable; unreliable in MENA)
- Mandatory for clinician and enterprise admin accounts

### Enterprise SSO + provisioning

- **SAML 2.0** and **OIDC** federations supported per tenant (Okta, Azure AD, Google Workspace, Ping, OneLogin as reference IdPs)
- **SCIM 2.0** for user provisioning/deprovisioning

---

## 7. Payments

### Stripe (web + Android web-purchase)

- Subscription management
- Invoicing (enterprise)
- Tax handling (Stripe Tax)
- Webhooks for state sync

### App Store / Google Play Billing

- iOS in-app purchases
- Android in-app billing (Play)
- Server-to-server notifications handled
- 15–30% platform fee accepted (no fight at launch)

### Enterprise Billing

- Direct invoicing via Stripe
- Net 30 standard
- Annual contracts with quarterly invoicing option

---

## 8. Push Notifications

### OneSignal (primary)

- Cross-platform push
- Segmentation + scheduling
- A/B testing built in
- BAA available for HIPAA scope

### Native fallback

- APNs direct for critical paths (iOS)
- FCM direct for critical paths (Android)
- Fallback to native when OneSignal unavailable

### Never

- Push provider used for PHI content
- Push notifications reveal sensitive content on lock screen
- Push notifications used as primary channel for T4 crisis communication

---

## 9. Analytics & Product Telemetry

### PostHog (self-hosted)

- **Why:** Privacy-aligned, self-hostable, extensible, good for health data
- **Alternative considered:** Amplitude (too permissive for our data sensitivity), Mixpanel (same concern), Rudderstack + Snowflake (overkill)
- Deployment: self-hosted Kubernetes cluster (AWS EKS)
- Data never leaves our infrastructure

### Product analytics scope

- Feature usage
- Funnel tracking
- Retention cohorts
- Never: content of journals, specific urges, biometric values

### Therapeutic data analytics

- Separate, access-controlled path
- Custom query layer, no ad-hoc SQL access without review

### ClickHouse (server-side analytics)

- **Why:** columnar store for high-throughput analytical queries over operational facts (intervention acceptance vs. 30-day PHQ-9 change, etc.)
- Deployed in-VPC on the HIPAA perimeter; same KMS scope as Postgres
- Accessed only by named analysts with audit logging on every query
- See [13_Analytics_Reporting](13_Analytics_Reporting.md) §7.2

### Reporting pipelines

- User insights (protective framing) — Python workers, template-based rendering, no LLM in path
- Clinical PDFs — WeasyPrint or ReportLab with pinned fonts, digitally signed
- FHIR R4 Observation bundles, HL7 v2.5.1 ORU^R01 — native Python serialization
- Enterprise reports — k-anonymized + differentially-private aggregates from SQL views

---

## 10. Observability

### Tracing — OpenTelemetry → Grafana Tempo

- End-to-end distributed tracing
- Mobile SDK → backend → DB
- Baggage for request correlation

### Metrics — Prometheus → Grafana

- Custom metrics per module
- SLO tracking
- Error budget computation

### Logging — structured JSON → Loki

- Loki for log aggregation
- Grafana for query
- Retention: 30 days standard, 1 year for security-relevant

### Error tracking — Sentry self-hosted (in-VPC)

- Mobile crashes
- Web (5 projects — one per Next.js app)
- Backend exceptions
- PHI scrubber applied to every report (same redaction layer as server logs)
- Source maps uploaded on every release

### Log streams — see [14_Authentication_Logging](14_Authentication_Logging.md) §4

Four separate streams with distinct retention, destinations, and IAM:

| Stream | Retention | Destination |
|---|---|---|
| `app.log` | 90 days hot / 2 years cold | CloudWatch + S3 |
| `audit.log` | 7 years | S3 Object Lock (compliance mode) |
| `safety.log` | 10 years | S3 Object Lock + legal-hold on T4 |
| `security.log` | 2 years | CloudWatch + SIEM |

### APM — optional Datadog (Year 3+)

- Only if we need it
- Sentry + Grafana should cover 95% of needs through Y2

---

## 11. Infrastructure

### AWS (primary cloud)

- **Why:** HIPAA BAA maturity, clinical ISV ecosystem, multi-region support
- **Regions:** us-east-1 (primary), us-west-2 (failover), eu-west-1 (EU from Y2)
- **BAA:** executed with AWS; covers all services we use for PHI

### Key AWS Services

| Service | Purpose |
|---------|---------|
| VPC + Transit Gateway | Network |
| ECS Fargate | Container runtime (API + web apps) |
| EKS | Reserved for future microservice extraction |
| RDS Postgres | Primary database |
| ElastiCache Redis | Cache, sessions |
| S3 | Blob storage |
| S3 Object Lock | Immutable audit + safety logs (compliance mode) |
| CloudFront | CDN (distinct distribution per web sub-surface) |
| Route 53 | DNS |
| WAF | Per-origin WAF rules |
| Shield Standard | DDoS protection |
| GuardDuty | Threat detection |
| Secrets Manager | Secret rotation (90-day default) |
| KMS | Key management (envelope encryption, JWT signing) |
| CloudWatch | Native monitoring (supplementary) |
| SageMaker | ML training + batch inference |
| SES | Transactional email |

---

## 12. DevOps

### Terraform (IaC)

- All infra in Terraform
- Per-environment workspaces
- Shared modules for reusable patterns
- State in S3 + DynamoDB lock

### GitHub Actions (CI/CD)

- Trunk-based development
- Feature flags via LaunchDarkly or self-hosted equivalent
- Staged rollouts: 1% → 10% → 50% → 100%
- Automated security scans (Snyk, Trivy)

### Feature Flags — Unleash (self-hosted, in-VPC)

- Kill switches (critical for safety regressions)
- Experiment configuration — **non-clinical surfaces only**
- Gradual rollouts
- Clinical experiments (intervention copy, T1/T2 wording, crisis-path variants) are **not** product experiments; they require IRB review before launch (see `Docs/Whitepapers/04_Safety_Framework.md`)

### Secrets Management

- AWS Secrets Manager
- Rotation policies (90 days standard)
- No secrets in code, in env files, or in logs

---

## 13. Email

### Postmark or Resend

- **Why:** High deliverability, developer-friendly APIs
- **Alternative considered:** SendGrid (fine but generic), SES (lower deliverability)
- Templates in-repo, not in external tool

---

## 14. Customer Support

### Help Scout or Front

- Support ticket system
- Email integration
- Internal notes
- Zero AI auto-reply on sensitive queries

---

## 15. Web Applications

Full spec: **[16_Web_Application](16_Web_Application.md).**

Five Next.js apps:

| App | Hostname | Audience |
|---|---|---|
| `web-marketing` | `www.disciplineos.com` | Public |
| `web-app` | `app.disciplineos.com` | Signed-in consumer |
| `web-clinician` | `clinician.disciplineos.com` | Licensed clinicians |
| `web-enterprise` | `enterprise.disciplineos.com` | Enterprise admins (SSO) |
| `web-crisis` | `crisis.disciplineos.com` | Static deterministic T3 |

### Stack per app

- **Next.js 15** with App Router, React 19, TypeScript 5.6 (`strict: true`, `noUncheckedIndexedAccess`)
- **Tailwind CSS v4** with logical properties and `rtl:` / `ltr:` variants
- **Design system** — shared tokens from `packages/design-system/`; per-platform primitives
- **Radix UI** primitives (accessible, unopinionated)
- **TanStack Query** for client-side data fetching; Server Components for SSR
- **next-intl** for i18n with locale-aware routing (`/en`, `/fr`, `/ar`, `/fa`)
- **React Hook Form + Zod** for forms
- **Visx** (D3 primitives) for charts with RTL-aware wrappers
- **Sentry self-hosted** for error reporting
- **Vitest** (unit), **Playwright** (E2E), **axe-core** (accessibility, WCAG 2.2 AA / AAA for clinician portal)

### i18n libraries

- **Web:** `next-intl` with ICU MessageFormat
- **Mobile:** `i18next` + `react-i18next` + `i18next-icu`
- **Shared translation catalog:** XLIFF at rest, compiled per platform at build
- **Translation platform:** Lokalise (Enterprise BAA) — translators see only the catalog, never production data

### Fonts

| Script | Primary | Fallback |
|---|---|---|
| Latin | Inter v4 | system-ui |
| Arabic | IBM Plex Sans Arabic | Noto Sans Arabic |
| Persian | Vazirmatn v33 | IBM Plex Sans Arabic |

Per-locale font subsetting to keep bundle sizes manageable.

---

## 16. Documentation

### Code docs

- Docstrings per Python PEP 257
- TSDoc for TypeScript
- Living ADRs in `/docs/decisions/`

### API docs

- Auto-generated from FastAPI + Pydantic → OpenAPI 3.1
- Hosted at `api-docs.disciplineos.com` (gated)

### Technical / clinical methodology

- Markdown in `/docs/methodology/`
- Published pre-print version public

---

## 17. Collaboration

| Tool | Purpose |
|------|---------|
| Linear | Project management |
| GitHub | Source control + PRs |
| Slack | Async communication |
| Loom | Async video |
| Figma | Design |
| Notion | Internal wiki |
| Google Workspace | Email, calendar, docs |

---

## 18. Explicit Non-Choices

Technologies intentionally rejected:

- **MongoDB** — no strong reason to go schema-less; relational model serves us
- **Elasticsearch** — pgvector + Postgres full-text covers needs
- **Kafka** (at launch) — Redis Streams suffices until 250k DAU
- **GraphQL (as primary)** — REST + OpenAPI simpler at this scale; GraphQL optional for clinician portal
- **Ruby on Rails / Django** — FastAPI's async model is materially better for our workload
- **Swift on server (Vapor)** — niche, ecosystem weaker than Python
- **React Native with Expo Go** for beta — we use bare React Native + EAS Build for flexibility
- **Flutter** — weaker wearable integrations decisive
- **Snowflake / BigQuery** at launch — overkill; reach for analytics warehouse at Y3 only

---

## 19. Cost Estimation (Annualized, at Y3 scale ~240k paid users)

| Category | Estimated annual cost |
|----------|----------------------|
| AWS compute + storage | $420k |
| RDS + TimescaleDB | $180k |
| Redis (ElastiCache) | $95k |
| CDN / data transfer | $85k |
| Clerk (auth) | $80k |
| OneSignal | $42k |
| Sentry | $28k |
| LaunchDarkly (or alternative) | $60k |
| PostHog (self-hosted overhead) | $35k |
| Anthropic (LLM API) | $160k |
| Other SaaS (email, support, collab) | $140k |
| **Total infrastructure + SaaS** | **~$1.3M** |

Engineers + ML: ~$6.8M (see financial projections).
Ratio: ~16% of eng cost, typical for this stage.

---

## 20. Summary

The stack is selected for:
- **Velocity:** React Native + FastAPI let a small team ship fast
- **Privacy:** Edge ML + self-hosted analytics + AWS BAA
- **Clinical readiness:** architecture supports FDA SaMD trajectory
- **Long-horizon maintainability:** boring, well-supported technologies chosen over novel

No technology in this stack is "cutting edge" — every choice is production-proven in adjacent companies. In a clinical / vulnerable-user category, boring-and-reliable is the correct engineering culture.
