# Backend Services — Discipline OS

## 1. Overall Shape

**FastAPI modular monolith.** A single deployable with strict internal module boundaries. Extract services only when measurable scale or team pressure demands it.

Rationale: we are a 10-engineer team. Microservices tax is real (distributed tracing, eventual consistency, coordinated releases). The latency boundary that matters — mobile → edge — is the same whether the backend is 1 process or 30. We stay a monolith until we can't.

---

## 2. Module Map

```
src/discipline/
├── app.py                         # FastAPI app factory, middleware, routing
├── config/
├── identity/                      # Users, auth exchange, session, MFA, SSO, SCIM, step-up — see 14
│   ├── auth_exchange.py           #   Clerk → our JWT
│   ├── session.py                 #   Redis-backed session registry
│   ├── sensitive_action.py        #   Step-up auth middleware
│   ├── mfa.py                     #   TOTP / WebAuthn / backup codes
│   ├── sso.py                     #   SAML + OIDC federations
│   ├── scim.py                    #   SCIM 2.0 provisioning
│   └── router.py
├── billing/                       # Subscriptions, Stripe, IAP
├── signal/                        # Signal ingest, aggregation, state store
├── intervention/                  # Urge lifecycle, bandit, tool registry
├── clinical/                      # Relapse protocol, streak engine
├── memory/                        # Journals, voice, embeddings, search
├── pattern/                       # Pattern miner, insights (substrate for analytics)
├── resilience/                    # Streak state machine
├── psychometric/                  # Instruments, scoring, trajectories, safety — see 12
│   ├── router.py
│   ├── scheduler.py               #   Never during urge window; 1 instrument per session
│   ├── scoring/                   #   Pure, version-pinned scoring fns per instrument
│   │   ├── phq9.py, gad7.py, audit_c.py, audit.py, dast10.py, pss10.py,
│   │   ├── who5.py, dtcq8.py, urica.py, readiness_ruler.py, cssrs.py, ...
│   ├── safety_items.py            #   PHQ-9 item 9 / C-SSRS → T4 routing
│   └── trajectories.py            #   RCI computation vs baseline + previous
├── analytics/                     # User insights, rollups, protective framing — see 13
│   ├── router.py                  #   /v1/insights/*
│   ├── rollups.py                 #   daily_user_rollups builder
│   ├── framing.py                 #   Rules P1–P6 applied to user-facing outputs
│   ├── weekly_reflection.py       #   Template renderer — no LLM
│   └── monthly_story.py
├── reports/                       # Clinical PDF, FHIR, HL7, user export, enterprise aggregates — see 13
│   ├── router.py
│   ├── clinical_pdf.py            #   Pinned fonts, reproducible, digitally signed
│   ├── fhir_observation.py        #   FHIR R4 Observation bundles
│   ├── hl7v2_oru.py               #   HL7 v2.5.1 ORU^R01
│   ├── user_export.py             #   HIPAA Right of Access
│   └── enterprise.py              #   k-anon + differential-privacy aggregates
├── enterprise/                    # Org admin, contract mgmt, SCIM targets
├── compliance/                    # Audit logs, consent, retention workers
├── ml/                            # Server-side model serving, training pipelines
├── llm/                           # Anthropic client, prompt library, safety filters
│                                  # Never on safety path; never on report generation
├── notifications/                 # Push dispatcher, nudge scheduler
├── content/                       # Per-locale content — see 15
│   ├── safety_directory.py        #   Per-locale, per-country hotline directory
│   ├── intervention_content.py    #   Per-locale intervention scripts
│   └── help.py                    #   Per-locale help article loader
├── exports/                       # Legacy path, being absorbed into reports/
└── shared/                        # Cross-cutting
    ├── logging/                   #   Stream-aware: app / audit / safety / security
    │   ├── streams.py
    │   ├── redact.py              #     PHI redaction with source-level lint + sink-level filter
    │   ├── envelope.py
    │   └── middleware.py          #     request_id, trace_id propagation
    ├── i18n/
    │   ├── negotiation.py         #     Accept-Language + users.locale resolution
    │   ├── formatters.py          #     Locale-aware date/time/number formatters
    │   ├── bidi.py                #     Bidi isolate helpers for mixed strings
    │   └── catalog.py             #     Server-side catalog (emails, push, PDF)
    ├── tracing.py
    ├── encryption.py
    ├── kms.py
    └── db.py
└── workers/                       # Background jobs (RQ / Celery)
    ├── rollup_builder.py          # Nightly daily_user_rollups
    ├── report_generator.py        # Async clinical and enterprise reports
    ├── retention_purger.py        # Quick-erase and scheduled purges
    ├── export_bundler.py          # HIPAA Right of Access bundles
    └── audit_shipper.py           # Ship audit.log → S3 Object Lock
```

Each module owns its DB tables. Inter-module calls go through typed interface classes, not raw DB queries across boundaries. A linter in CI checks that no module imports another's `repository.py` or `models.py`.

**Stream isolation for logging.** `analytics`, `reports`, `psychometric`, and user-facing modules write through the `shared.logging.streams` boundary. Only `compliance` and `shared.logging` can write to `audit.log` and `safety.log`. IAM on the log-shipping role enforces this at the infrastructure layer too (see [14](14_Authentication_Logging.md) §4.1).

---

## 3. Key Services (per module)

### 3.1 `identity`

- `UserService.create_from_clerk(external_id, email)`
- `UserService.get_current(session_token)`
- `UserService.soft_delete(user_id)`
- `UserService.quick_erase(user_id)` — triggers erase pipeline
- `DeviceService.register(user_id, device_spec, attestation_token)`
- `DeviceService.revoke(device_id)`
- `SessionService.exchange_clerk_token(clerk_jwt) → ServerSession`
- `SessionService.refresh(refresh_token) → ServerSession`

Depends on: Clerk SDK, KMS, audit_logs.

### 3.2 `billing`

- `SubscriptionService.create_from_iap(user_id, iap_receipt) → Subscription`
- `SubscriptionService.upgrade(user_id, target_tier)`
- `SubscriptionService.cancel(user_id, reason)` — no dark patterns
- `WebhookHandler.stripe(event)`
- `WebhookHandler.apple_s2s(payload)` — App Store Server Notifications
- `WebhookHandler.google_play(payload)`

Depends on: Stripe SDK, StoreKit verifier, Google Play Developer API.

### 3.3 `signal`

- `SignalIngestService.accept_batch(user_id, windows[])` — validates, deduplicates, writes hypertable.
- `StateService.record_estimate(user_id, state_estimate)`
- `StateService.latest_state(user_id) → StateEstimate | None`
- `SignalSourceService.device_capabilities(user_id) → DeviceCaps` (for ingest policy decisions)

Upstream: mobile POST `/v1/signals/windows`.
Downstream: pattern engine, intervention trigger evaluator.

### 3.4 `intervention`

This is the heart.

- `UrgeService.open(user_id, input: UrgeInput) → UrgeEvent + RecommendedIntervention`
- `UrgeService.resolve(urge_id, outcome: UrgeResolution)`
- `SOSService.trigger(user_id) → CrisisPayload`
- `NudgeDispatcher.evaluate_and_send()` — called by scheduler every 5min
- `OutcomeService.record(intervention_id, outcome)` — feeds bandit
- `ToolRegistry.get_tool(variant) → Tool` — static registry of deterministic tools

#### Bandit service

- `BanditService.select(context: BanditContext) → bandit_arm`
- `BanditService.update(bandit_arm, reward)` — async; model weights updated hourly

Bandit context vector: state_label, state_confidence, time_of_day_bucket, day_of_week, recent_handled_rate, recent_tool_variants, trigger_tags. Output: top-3 tool variants with exploration rate 15%.

**T3 safety rule:** `SOSService.trigger` returns a fully deterministic payload from a compiled template. LLM never involved. Bandit not consulted. This path is hard-coded on purpose.

### 3.5 `clinical`

- `RelapseService.report(user_id, input) → RelapseEvent + ClinicalResponse`
- `RelapseService.complete_review(relapse_id, input)`
- `AVEAssessor.score(relapse_event, journal) → AVEScore`
- `AbstinenceVsModerationPolicy.apply(user_profile, relapse_event)` — returns appropriate post-event messaging template

The `ClinicalResponse` returned from `report` includes compassion-template + resilience-preserved flag + recommended next steps.

### 3.6 `memory`

- `JournalService.create(user_id, input) → Journal`
- `JournalService.search(user_id, query: str | VectorQuery, limit) → SearchResult[]`
- `VoiceService.create_session(user_id) → VoiceSession + presigned_upload`
- `VoiceService.finalize(session_id) → queues transcription job`
- `EmbeddingWorker.embed(journal_id)` — uses `text-embedding-3-small` via Anthropic-equivalent or local model

### 3.7 `pattern`

- `PatternMinerJob.run(user_id)` — scheduled nightly, more often for high-activity users
- `PatternService.active(user_id) → Pattern[]`
- `PatternService.dismiss(pattern_id, reason)`

Pattern detectors shipped:
1. **Temporal** — peak windows within day / week.
2. **Contextual** — co-occurring tags (work stress, social drinking).
3. **Physiological** — HRV dips preceding urge by 10–30 min.
4. **Compound** — chained signals.

### 3.8 `resilience` (streak engine)

- `StreakService.apply_handled(user_id)` — increments resilience + continuous
- `StreakService.apply_relapse(user_id)` — resets continuous, increments resilience
- `StreakService.current(user_id) → StreakState`

State machine enforced in code + DB trigger. Unit tests cover every legal transition.

### 3.9 `enterprise`

- `OrgService.provision(...)` — B2B onboarding
- `ClinicianLinkService.invite(clinician_user_id, patient_email)`
- `ClinicianLinkService.patient_consents(patient_user_id, link_id)`
- `ReportService.monthly(org_id) → AggregateReport` — enforces cohort-size floor of 200

### 3.10 `compliance`

- `AuditLogger.emit(event: AuditEvent)` — fire-and-forget to hypertable
- `ConsentService.grant(user_id, consent_type, version)`
- `ConsentService.latest(user_id, consent_type) → ConsentRecord`
- `RetentionWorker.run_daily()` — purges expired data, enforces tombstone policy
- `QuickEraseWorker.run()` — runs every minute; processes queued quick-erase requests

### 3.11 `ml`

- `ModelRegistry.active(model_kind) → ModelRef`
- `ModelRegistry.promote(version, cohort: int)` — rollout 1/10/100%
- `TrainingPipeline.run_offline()` — Airflow DAG
- `InferenceService.urge_risk_forecast(user_id, horizon_min)` — used only for server-side reports, not real-time decisioning

### 3.12 `llm`

- `LLMClient.generate_reflection_prompt(context) → str`
- `LLMClient.summarize_week(user_id) → WeeklyReport`
- `SafetyFilter.run(prompt, response)` — pre and post filter

**LLM use cases restricted to:**
- Weekly report narrative
- Reflection prompts (template-based, not free-form)
- Pattern explanation ("here's what we noticed")
- Journal title suggestions

**Explicitly forbidden LLM use cases:**
- Crisis responses (T3/T4) — deterministic only
- Clinical guidance — never
- Diagnosis-adjacent language — filtered
- Relapse messaging — deterministic compassion templates only

Per-user LLM budget: 10 requests/day free, 40/day Plus, 200/day Pro. Enforced at gateway.

### 3.13 `notifications`

- `PushDispatcher.send(user_id, payload, slo_tier)`
- `NudgeScheduler.run_every_5min()` — evaluates candidates via intervention.NudgeDispatcher
- Provider adapters: APNsAdapter, FCMAdapter
- **Quiet hours enforced at dispatch**, even if scheduler triggers.

---

## 4. Request Lifecycle

```
Client → ALB → FastAPI (uvicorn/gunicorn) → middleware chain → router → service → repository → DB
                                    ↓                            ↓
                            OpenTelemetry             async.task_queue (Redis → workers)
```

### Middleware stack (outermost first)

1. Request ID + trace context injection
2. Rate limiter (SlowAPI + Redis)
3. Auth (session token → user resolver)
4. Idempotency key check
5. Tier classification (annotate response with `X-SLO-Tier`)
6. Exception handler (emits RFC 7807)

### T3 crisis path optimization

A dedicated ASGI sub-app mounted at `/v1/sos` avoids the full middleware chain:
- No rate limiter (crisis must not be limited).
- No tenant header resolution (pre-auth device attestation is accepted).
- Pre-warmed worker pool on SOS endpoints; always keeps N>=2 workers free.

---

## 5. Background Workers

**Stack:** RQ (Redis Queue) for most jobs, Celery beat for periodic scheduling. Airflow for complex training DAGs only.

| Worker | Trigger | Purpose |
|--------|---------|---------|
| `signal_aggregator` | Every 1 min | Rolls up minute-windows into day buckets |
| `pattern_miner` | Per-user nightly | Recomputes patterns |
| `bandit_updater` | Hourly | Incorporates last hour of outcomes into bandit weights |
| `embedding_worker` | Event-driven | Computes embeddings on new journals |
| `voice_transcriber` | Event-driven | Whisper-small → journal |
| `voice_purger` | Every 15 min | Hard-deletes S3 voice blobs > 72h |
| `retention_worker` | Daily | Applies retention policies |
| `quick_erase_worker` | Every 1 min | Executes quick-erase within 10 min SLA |
| `push_dispatcher` | Event-driven | Sends push notifications |
| `nudge_scheduler` | Every 5 min | Evaluates T1 nudge candidates |
| `stripe_webhook_processor` | Event-driven | From Redis-pubsub queue |
| `audit_log_flusher` | Every 10s | Ships buffered audit events |
| `export_builder` | Event-driven | Builds user data export |
| `model_refresher` | Daily | Pulls new ML model versions, smoke tests |
| `report_generator` | Monthly | Enterprise aggregate reports |

Concurrency: workers run on ECS Fargate auto-scaled from CloudWatch queue-depth metrics.

---

## 6. Database Access

### 6.1 Driver

- **asyncpg** for raw reads/writes, wrapped by a thin query builder (`pypika`-ish) rather than full ORM.
- **SQLAlchemy Core** used selectively for migrations (Alembic) and for audit-log schema modeling.

Rationale: rejected SQLAlchemy ORM for hot paths due to latency and opacity of its query generation. Explicit queries are safer in this clinical context.

### 6.2 Pooling

- PgBouncer in transaction mode at 2000 client connections, 100 backend connections per RDS instance.
- Redis connection pool: 500 per worker.

### 6.3 Read/write split

- RDS primary + 2 read replicas.
- Read replicas used for dashboards, reports, journal search.
- Write-after-read consistency required for: intervention + outcome pair, urge + resolve pair — reads must go to primary in these flows.

---

## 7. Caching

| Layer | Use | TTL |
|-------|-----|-----|
| Redis (shared cache) | User session, flags, rate limit counters, latest state estimate | 5–60 min |
| CloudFront | Static assets, marketing site | 1 day |
| In-process LRU | Bandit weights, tool registry, pattern prototypes | 15 min |
| ETag on GET endpoints | Read-after-write optimization | conditional |

---

## 8. Feature Flags & Config

- **Local flags:** checked in `config/flags.py`, environment-driven.
- **Runtime flags:** ConfigCat or self-hosted `Unleash` for per-cohort rollout.
- **Crisis flags:** none. T3 behavior is never behind a flag.

---

## 9. Error Budgets

Each service module owns an error budget tied to the affected SLO tier:

| Module | SLO tier | Monthly error budget |
|--------|----------|---------------------|
| `intervention` (T3 path) | 99.95% | 21.6 min |
| `intervention` (T2 path) | 99.9% | 43.2 min |
| `clinical` | 99.9% | 43.2 min |
| `signal` | 99.5% | 3.6 hrs |
| `pattern` | 99.0% | 7.2 hrs |
| `memory` | 99.5% | 3.6 hrs |

Violating budget blocks non-reliability feature work until recovered.

---

## 10. Testing Layers

- **Unit:** pytest, hermetic. Coverage >80% overall, >95% for `intervention` and `clinical`.
- **Integration:** docker-compose Postgres + Redis + localstack S3. Every module has integration tests for its HTTP surface.
- **Contract:** Pact-python between mobile and backend for REST surface + pactflow verification.
- **Load:** Locust scenarios for SOS burst, daily check-in stampede, signal ingest storm.
- **Chaos:** Fault injection on Redis, RDS replica lag, Clerk outages in staging.

---

## 11. Observability

- **Metrics:** Prometheus scrape on `/internal/metrics`; Grafana dashboards per module.
- **Tracing:** OpenTelemetry with Tempo or Grafana Cloud.
- **Logs:** Loki; structured JSON with request_id + user_id_hash.
- **Key SLIs** dashboarded:
  - p50 / p95 / p99 for every HTTP route
  - SOS response time distribution (hard-gated in CI)
  - Bandit exploration vs exploitation ratio
  - Outcome recording lag
  - Worker queue depth
  - PHI-access audit coverage (should be 100%)

---

## 12. Deployment

- **Runtime:** ECS Fargate behind an ALB, two AZs.
- **API sizing:** 12 tasks (2 vCPU, 4GB) steady state; auto-scale to 40 based on RPS.
- **Workers:** separate service, scaled on queue-depth.
- **Rollout:** blue/green via CodeDeploy, health checks gate traffic shift.
- **Rollback:** automated on SLO violation during 10-min canary.

---

## 13. Internal APIs

Selected internal (non-public) endpoints used by admin tooling + clinical operations:

- `POST /internal/metrics` — Prometheus scrape
- `POST /internal/admin/users/{id}/audit-export` — admin-signed tokens only, mfa-gated
- `POST /internal/admin/retention/purge-now` — quick-erase override for legal holds
- `POST /internal/admin/model-promote` — model rollout
- `GET  /internal/admin/slo` — current SLO state

All internal endpoints require operator SSO (Google Workspace) + mfa; all actions audit-logged with extra fidelity.

---

## 14. Service Boundaries We Will Extract Later

When we outgrow the monolith, these are the natural extraction points (in priority order):

1. **ML inference service** — GPU separation from CPU workers, independent scaling.
2. **Signal ingest service** — write volume is the noisiest neighbor.
3. **Pattern engine** — batch-heavy, tolerates independent deployment cadence.
4. **LLM gateway** — cost + safety isolation; already behaves like a service boundary today.
5. **Enterprise reporting** — different SLA class (nightly) from user-facing APIs.

We will not extract earlier than these pressures demand. Premature extraction cost ≥ 0.5 engineer-years of coordination overhead.
