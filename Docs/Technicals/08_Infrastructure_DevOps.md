# Infrastructure & DevOps — Discipline OS

## 1. Cloud Provider

**Primary: AWS.** Rationale:
- HIPAA BAA maturity and full services coverage.
- Deep healthcare ecosystem (SageMaker, HealthLake optionality for Y3+).
- Mobile + web push via SNS + APNs/FCM proxying.
- Strong regional coverage for Y2 EU expansion.

Rejected: GCP (HIPAA coverage is solid but ecosystem weaker for healthcare compliance tooling), Azure (too Microsoft-ecosystem coupled).

---

## 2. Account Topology

| Account | Purpose |
|---------|---------|
| **management** | AWS Organizations root, consolidated billing, SCPs |
| **log-archive** | Centralized CloudTrail + Config history; write-only from others |
| **security** | GuardDuty, Security Hub, IAM Identity Center admin |
| **prod** | Production workloads |
| **staging** | Pre-prod mirror; same topology, smaller footprint |
| **dev** | Engineer sandboxes; no PHI |
| **sandbox** | Experimentation / spikes |

Accounts linked via AWS Organizations. SCP guardrails: deny region outside approved set, deny IAM user creation (SSO only), deny disabling of CloudTrail / Config.

---

## 3. Region Strategy

| Region | Role | When |
|--------|------|------|
| us-east-1 | Primary (prod + staging + mgmt) | v1.0 launch |
| us-west-2 | DR (active/passive) | v1.0 launch |
| eu-central-1 | EU prod | Y2 |
| ca-central-1 | CA prod | Y2 (opportunistic) |

DR target: RPO 1 hour, RTO 4 hours. Quarterly failover drills.

---

## 4. Network Architecture (prod)

Separate CloudFront distributions + separate WAF policies per web origin — isolation, not sharing, is the point (see [16_Web_Application](16_Web_Application.md) §2).

```
                                   Internet
                                      │
                              ┌───────┴────────┐
                              │ Route 53 + DNS │
                              └───────┬────────┘
                                      │
         ┌──────────────────┬─────────┼─────────┬──────────────────┬───────────────┐
         ▼                  ▼         ▼         ▼                  ▼               ▼
    CloudFront         CloudFront  CloudFront CloudFront       CloudFront       CloudFront
    www (marketing)    app        clinician  enterprise        crisis (static)  api
    WAF: baseline      WAF: strict  WAF:strict+ WAF: strict+    WAF: minimal     WAF: strict
                                    MFA gate   SSO gate         (no auth path)
         │                  │         │         │                  │               │
         └─────────────────┐│         │         │                  │               │
                           ▼▼         ▼         ▼                  ▼               ▼
                   Next.js app       Next.js   Next.js           Static S3        ALB
                   (Fargate /        (Fargate) (Fargate)         + CloudFront     ↓
                    Amplify SSR)                                                  VPC (prod)
                                                                                   │
          ┌────────────────────────────────────────────────────────────────────────┘
          │
          │  ┌─────────────┐  ┌──────────────┐  ┌─────────┐  ┌──────────────────┐
          │  │ ECS Fargate │  │ ECS Fargate  │  │  RDS    │  │ ClickHouse       │
          │  │ (API)       │  │ (Workers)    │  │ Postgres│  │ (in-VPC,         │
          │  │ private     │  │ private      │  │ private │  │  HIPAA perimeter)│
          │  └─────────────┘  └──────────────┘  └─────────┘  └──────────────────┘
          │          │                │              │              │
          │  ┌───────┴────────────────┴──────────────┴──────────────┴──┐
          │  │  Redis (ElastiCache), S3 via VPC endpoints              │
          │  │  S3 with Object Lock (compliance) for audit + safety logs│
          │  │  KMS via VPC endpoints                                  │
          │  └─────────────────────────────────────────────────────────┘
          └────────────────────────────────────────────────────────────
```

### 4.1 Web sub-surface hosting

| Surface | Hostname | Deployment |
|---|---|---|
| `web-marketing` | `www.disciplineos.com` | Next.js SSR on Fargate + CloudFront |
| `web-app` | `app.disciplineos.com` | Next.js SSR on Fargate + CloudFront (authenticated) |
| `web-clinician` | `clinician.disciplineos.com` | Next.js SSR on Fargate + CloudFront (MFA gate in WAF) |
| `web-enterprise` | `enterprise.disciplineos.com` | Next.js SSR on Fargate + CloudFront (SSO gate in WAF) |
| `web-crisis` | `crisis.disciplineos.com` | Static site in S3 + CloudFront; minimal WAF; 99.99% SLO |
| `api` | `api.disciplineos.com` | FastAPI on Fargate + ALB + CloudFront |

Each is a separate CloudFront distribution with a distinct origin access policy and WAF WebACL. A regression on marketing cannot affect clinician portal availability.

### 4.2 Immutable audit storage

- `audit.log` → S3 Object Lock in **compliance mode** (no deletion for 7 years, not even by root).
- `safety.log` → S3 Object Lock in compliance mode + legal-hold capability for T4 incidents (10 years).
- Athena + Glue for compliance query over these logs.
- Log-shipper IAM role can PutObject but cannot DeleteObject, cannot shorten retention, cannot disable Object Lock.

- **3 AZs.** Private subnets for all compute + data.
- **VPC endpoints** for S3, DynamoDB, KMS, Secrets Manager — no egress to public internet for PHI-in-motion.
- **NAT Gateway** for outbound to external services (Anthropic API, Stripe, Clerk).
- **Transit Gateway** optional Y2 for cross-region private traffic.

---

## 5. Compute

### 5.1 API tier (ECS Fargate)

- **Task definition:** 2 vCPU, 4 GB, one container (uvicorn with gunicorn supervisor, 4 workers).
- **Desired count:** 12 steady state (Y1), auto-scale to 60 on RPS.
- **Scaling signals:** ALB request count per target, CPU utilization, queue depth.
- **Deployment:** blue/green via CodeDeploy.

### 5.2 Worker tier (ECS Fargate)

- Multiple services by queue type:
  - `worker-general` (4 vCPU, 8 GB, 6 tasks)
  - `worker-ml` (4 vCPU, 16 GB, 3 tasks)
  - `worker-voice` (4 vCPU, 8 GB, 4 tasks)
  - `worker-embed` (2 vCPU, 4 GB, 4 tasks)
- Scaling by CloudWatch queue-depth metric.

### 5.3 ML inference (SageMaker endpoints, later)

v1: server-side inference lives on worker tier.
v2: dedicated SageMaker real-time endpoints for urge-risk forecasts, serving latency <200ms.

### 5.4 Scheduled (EventBridge + Lambda or ECS)

- `nudge-scheduler` every 5 min
- `retention-worker` every 24h
- `voice-purger` every 15 min
- `quick-erase-worker` every 1 min
- `audit-log-flusher` every 10s

---

## 6. Data Tier

### 6.1 PostgreSQL (Amazon RDS for PostgreSQL 16)

- **Primary:** `db.r7g.2xlarge` (8 vCPU, 64 GB) — scale up to `r7g.4xlarge` as write load grows.
- **Replicas:** 2 cross-AZ read replicas.
- **Multi-AZ:** yes for primary.
- **Encryption:** KMS-CMK.
- **Backups:** automated daily, 35-day retention; final snapshot on deletion.
- **Point-in-time recovery:** enabled.
- **Connection pool:** PgBouncer sidecars in ECS tasks; transaction mode.

### 6.2 TimescaleDB

- Deployed as PostgreSQL extension on a secondary RDS instance (not the OLTP primary — heavy write and aggregate workload is separated).
- `db.r7g.2xlarge` start; scale vertically. Hypertables + continuous aggregates.

### 6.3 Redis (ElastiCache Redis 7)

- **Cluster mode disabled,** 1 primary + 2 replicas to start.
- **Upgrade to cluster mode** at ≥ 100k concurrent sessions.
- In-transit + at-rest encryption.

### 6.4 S3

- Buckets:
  - `disciplineos-prod-voice` — ephemeral, lifecycle 3-day hard-delete
  - `disciplineos-prod-exports` — 30-day expiry
  - `disciplineos-prod-backups` — versioned, MFA-delete
  - `disciplineos-prod-assets` — static, public-via-CloudFront
  - `disciplineos-prod-ml-artifacts` — signed, versioned
- Default encryption SSE-KMS with CMKs per bucket.
- Bucket policy + Block Public Access on PHI buckets.

### 6.5 Vector store

- `pgvector` on primary RDS.
- Upgrade path: Qdrant-on-Kubernetes at 10M+ vectors.

---

## 7. Infrastructure as Code

### 7.1 Terraform

- **Version:** Terraform 1.8+.
- **Module layout:** `infra/terraform/`
  - `modules/` — reusable (network, ecs-service, rds, redis, s3-phi-bucket)
  - `envs/prod/`, `envs/staging/`, `envs/dev/`
  - `platform/` — shared org-level (Organizations, IAM Identity Center, Control Tower)
- **State:** S3 + DynamoDB lock, per-env.
- **Plan on PR,** apply gated by human approval in CI.
- **Terraform Cloud or Atlantis** for apply orchestration.

### 7.2 Kubernetes (when)

Not at launch. Considered at ~30 engineers + complex stateful workloads. Fargate covers us to that scale.

### 7.3 Helm / ArgoCD / Config

- ECS task definitions generated from Terraform + parameterized per service.
- Config via Parameter Store + Secrets Manager (hierarchical).

---

## 8. CI/CD

### 8.1 Pipeline stages

```
PR open
 ├─ Lint (ruff, mypy, eslint, typecheck)
 ├─ Unit tests (pytest + Jest)
 ├─ Integration tests (docker-compose + localstack)
 ├─ Security (Bandit, Semgrep, TruffleHog, Snyk SCA)
 ├─ Contract tests (Pact verify)
 ├─ Coverage gates (80% overall; 95% intervention/clinical)
 └─ Terraform plan (if infra changed)

Merge to main
 ├─ Build (Docker image, EAS binary)
 ├─ Sign + push (ECR)
 ├─ Deploy to staging (auto)
 ├─ E2E tests against staging
 ├─ SLO / latency gate
 ├─ Manual promote to prod (except hotfixes)
 ├─ Blue/green rollout (CodeDeploy)
 ├─ Canary gate (10 min at 10% traffic)
 └─ Full traffic shift + rollback armed
```

### 8.2 Pipeline SLA

- PR → green CI: <15 min p95.
- Merge → staging: <20 min.
- Staging → prod: <30 min including canary.

### 8.3 Hotfix path

- `hotfix/*` branches bypass staging auto-deploy, require 2-reviewer approval.
- T3 hotfixes (crisis path) have a pre-agreed fast lane: <60 minutes from problem identification to deployed fix.

### 8.4 GitHub Actions runners

- Self-hosted runners on EC2 for heavier jobs.
- Managed runners for lightweight jobs.
- Secrets via OIDC → AWS role (no long-lived cloud keys in GH).

---

## 9. Mobile CI/CD

### 9.1 iOS

- **EAS Build** for React Native.
- Fastlane for native steps (signing, provisioning profiles, TestFlight, App Store).
- Code signing via App Store Connect API keys stored in GitHub.

### 9.2 Android

- **EAS Build** + Gradle for native steps.
- Play Store via Google Play Developer API.

### 9.3 Release train

- **Weekly stable** (Fri) to App Store + Play.
- **Daily beta** (TestFlight + Play beta).
- **Over-the-air updates** via Expo Updates for JS-only changes, excluding crisis flows.

### 9.4 Signing infrastructure

- Dedicated AWS KMS key for code-signing material custody.
- Rotation procedures documented, tested annually.

---

## 10. Observability

### 10.1 Logs

- **Loki** (self-hosted in ECS) + **Grafana** frontend.
- Structured JSON logs required.
- PII redaction filter applied at log ingress.
- Retention: 30 days hot, 1 year cold in S3.
- Audit logs go to separate `log-archive` account, immutable.

### 10.2 Metrics

- **Prometheus** scraping ECS tasks via ADOT (AWS Distro for OpenTelemetry).
- Long-term: **Amazon Managed Prometheus** (workspace) + Grafana Cloud or self-hosted Grafana.
- Custom metrics per service: request count, p50/p95/p99 latency, error rate, queue depth, SLO budget remaining.

### 10.3 Tracing

- **OpenTelemetry** instrumentation native in FastAPI.
- **Tempo** (self-hosted) or Grafana Cloud.
- 100% trace sampling on T3 endpoints; 10% on others.
- Trace context propagated from mobile.

### 10.4 Alerts (priority-tiered)

| Priority | Page who | Example |
|----------|----------|---------|
| P0 | On-call engineer + CTO + CISO | SOS latency p95 >1s for 5 min |
| P1 | On-call engineer | API error rate >2% for 10 min |
| P2 | Slack #ops | Queue depth > threshold |
| P3 | Daily digest | Cost anomaly, slow query |

### 10.5 Dashboards

- **User-facing SLO board** (public status page powered by StatusPage/BetterStack).
- **Internal ops board:** per-service latency, error rate, queue health.
- **Clinical safety board:** safety classifier flag rates, T3 triggers, human-handoff SLA.
- **Business health board:** DAU, WUH, cohort retention, NPS.

### 10.6 On-call

- 24/7 rotation post-launch.
- PagerDuty or Opsgenie.
- Runbooks in-repo under `docs/runbooks/`.
- SLO breach triggers paged response (P0/P1); false-alarm rate reviewed weekly.

---

## 11. SLO Enforcement

SLOs from `README.md` table encoded in Prometheus recording rules + SLO burn-rate alerts.

| Tier | Burn-rate alert thresholds |
|------|---------------------------|
| T3 (99.95%) | 1h window: 14.4× burn → P0; 6h window: 6× → P1 |
| T2 (99.9%) | Standard 1h/6h two-burn alerts |
| T1 (99.9%) | Same |

Release gates in CI: staging latency regression >15% relative to 7-day baseline blocks prod promotion.

---

## 12. Cost Management

### 12.1 Budgets + alerts

- Monthly budget per env in AWS Budgets.
- Team-level tags (`team=intervention`, `team=signal`, `team=ml`).
- Weekly cost review; anomalies paged.

### 12.2 Cost targets

| Y | Infrastructure spend |
|---|---------------------|
| 1 | $400K |
| 2 | $800K |
| 3 | $1.3M |
| 4 | $2.5M |
| 5 | $4M |

### 12.3 Optimization

- Savings Plans for steady-state ECS + RDS.
- Reserved capacity for RDS once workload stable.
- Spot for non-critical workers (embedding, pattern mining) with fallback.
- S3 Intelligent-Tiering for non-PHI, lifecycle on PHI.
- CloudFront negotiated commits.

---

## 13. Disaster Recovery

### 13.1 Recovery objectives

- **RPO:** 1 hour (max data loss tolerated).
- **RTO:** 4 hours (max downtime).
- For T3 specifically: degraded mode that serves device-cached crisis UI in under 1 minute.

### 13.2 Backup strategy

- RDS automated daily snapshots + point-in-time recovery (up to 35 days).
- Cross-region snapshot copy (us-east-1 → us-west-2) every 4 hours.
- S3 versioned + replicated cross-region for mission-critical buckets.
- Terraform state versioned + replicated.

### 13.3 Failover

- Active/passive DR in us-west-2.
- Route 53 health-check-based failover.
- Data replication via RDS cross-region read replica with promotion runbook.

### 13.4 Drills

- Quarterly tabletop (paper).
- Semi-annual real failover to DR in staging mirror.
- Annual real failover test in prod (off-hours, pre-announced to users as maintenance).

---

## 14. Release Management

### 14.1 Versioning

- Semver for API + client versions.
- Calendar versioning for infra (`2026.04.18-01`).
- Release notes in `CHANGELOG.md`, user-facing highlights separated.

### 14.2 Feature flags

- **ConfigCat** (hosted) or self-hosted Unleash.
- Flag-driven rollouts with percentage cohorts.
- Flag cleanup: any flag >90 days old without change triggers cleanup ticket.
- Crisis flow is never feature-flagged.

### 14.3 Rollback

- Blue/green rollback takes <60s (DNS not swapped; ALB target group switch).
- DB migrations: two-phase deploys with additive migrations only on first release.

---

## 15. Configuration Management

- **Non-secrets:** Parameter Store (hierarchical).
- **Secrets:** Secrets Manager, rotation 90-day.
- **Application config:** environment + per-service ECS task definition vars.
- **Feature flags:** external (see above), hot-reload at service level.

---

## 16. Service Meshing (deferred)

Not at launch. Consider at 15+ services. Until then, mTLS handled via VPC + security groups; service-to-service is in-process.

---

## 17. Build Hygiene

- Deterministic container images (BuildKit + reproducible builds for Python wheels).
- Scanned at push (ECR scan on push + Snyk).
- Unsigned images can't be deployed.
- Image retention: last 10 prod + all staging last 30 days + all release tags forever.

---

## 18. Documentation

- `docs/runbooks/` — per-service runbooks (RDS failover, Redis flush, cache invalidate, model rollback, DR drill, quick-erase hand-verify).
- `docs/adrs/` — architecture decision records.
- `docs/sre/` — SLO definitions + burn-rate policies.
- All new services carry a required README with: purpose, owner, runbook links, on-call rotation.

---

## 19. What's Deferred

- Kubernetes migration
- Service mesh
- Multi-region active/active
- Full self-hosted observability stack
- GPU inference fleet (SageMaker Serverless suffices until Y2)
- Edge compute (CloudFront Functions) for routing

Each deferral is time-boxed to a trigger: scale, team size, or product requirement.
