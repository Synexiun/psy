# Data Model — Discipline OS

## 1. Philosophy

1. **Minimize by default.** Every field justifies its existence with a product or clinical reason.
2. **Separate biometric from behavioral.** Raw signals live in time-series tables with aggressive retention; derived features live in warm relational tables.
3. **Append-only for clinical evidence.** Outcomes, interventions, relapse events never mutate — they are immutable audit records.
4. **User-owned.** Every row has a clear user owner, and deletion cascades are tested in CI.
5. **Encrypt sensitive columns at rest.** Journal text, voice URIs, crisis-context fields use application-layer envelope encryption (AWS KMS DEKs).
6. **Retention policies declared per table.** No "forever" defaults.

---

## 2. Database Topology

| Store | Purpose | Retention |
|-------|---------|-----------|
| PostgreSQL 16 (primary) | Relational entities, users, subscriptions, interventions, outcomes | Indefinite for user-owned; config-driven for audit |
| TimescaleDB hypertables | Time-series biometric aggregates, signal windows, telemetry | 400 days hot, 2 years warm (aggregated) |
| Redis 7 | Session cache, rate limits, push-queue, short-term state | Volatile |
| pgvector | Journal embeddings, pattern prototypes | Same as source row |
| S3 (encrypted) | Voice blobs (ephemeral), data exports, backup | Voice: 72h then delete; exports: 30 days |
| ElasticSearch (v2) | Journal/memory full-text search | Tied to source |

---

## 3. Core Entities

### 3.1 `users`

```sql
CREATE TABLE users (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id           TEXT UNIQUE NOT NULL,             -- Clerk user ID
  email_hash            BYTEA NOT NULL,                   -- SHA-256 for lookup
  email_encrypted       BYTEA NOT NULL,                   -- KMS-wrapped
  handle                TEXT UNIQUE,                      -- Optional display name
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_active_at        TIMESTAMPTZ,
  timezone              TEXT NOT NULL DEFAULT 'UTC',      -- IANA tz id
  locale                TEXT NOT NULL DEFAULT 'en',       -- BCP 47; launch: en|fr|ar|fa (+regional)
  calendar_preference   TEXT NOT NULL DEFAULT 'gregorian'
                        CHECK (calendar_preference IN ('gregorian','gregorian_with_hijri','gregorian_with_shamsi')),
  digit_preference      TEXT NOT NULL DEFAULT 'auto'
                        CHECK (digit_preference IN ('auto','latin')),
  app_lock_enabled      BOOLEAN NOT NULL DEFAULT false,
  alt_icon_enabled      BOOLEAN NOT NULL DEFAULT false,
  mfa_enrolled          BOOLEAN NOT NULL DEFAULT false,   -- computed; clinician/enterprise require true
  consent_version       TEXT NOT NULL,                    -- Consent doc version
  deleted_at            TIMESTAMPTZ,                      -- Soft delete marker
  purge_scheduled_at    TIMESTAMPTZ                       -- Hard-delete window
);

CREATE INDEX idx_users_external ON users(external_id);
CREATE INDEX idx_users_email_hash ON users(email_hash);
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_users_locale ON users(locale);
```

**Retention:** Soft-delete on account close → 30-day recovery → hard-delete on day 31 (or user-triggered quick-erase within 10 minutes).

**i18n fields:** `locale`, `calendar_preference`, `digit_preference` are authoritative for server-rendered content (email, push, PDF export). See [15_Internationalization](15_Internationalization.md) for negotiation rules and the reason clinical scores must use Latin digits even when `digit_preference = auto`.

### 3.2 `user_profiles`

Clinical profile kept separate from `users` to isolate PHI access.

```sql
CREATE TABLE user_profiles (
  user_id               UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  target_behaviors      TEXT[] NOT NULL DEFAULT '{}',     -- enum: alcohol, cannabis, porn, binge_eating, doomscroll, custom
  baseline_severity     SMALLINT,                         -- 1-10 self-rated
  clinical_referral     BOOLEAN NOT NULL DEFAULT false,
  ema_frequency         TEXT NOT NULL DEFAULT 'twice_daily',
  crisis_contact_json   BYTEA,                            -- KMS-wrapped; name/phone/relationship
  local_hotline_country TEXT NOT NULL DEFAULT 'US',
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.3 `subscriptions`

```sql
CREATE TABLE subscriptions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tier                  TEXT NOT NULL,                    -- free, plus, pro, family, enterprise, clinical
  status                TEXT NOT NULL,                    -- trial, active, past_due, canceled, expired
  iap_receipt_ref       TEXT,                             -- App Store / Play Store reference
  stripe_customer_id    TEXT,
  stripe_sub_id         TEXT,
  current_period_start  TIMESTAMPTZ,
  current_period_end    TIMESTAMPTZ,
  trial_ends_at         TIMESTAMPTZ,
  canceled_at           TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(status);
```

---

## 4. Signal & State

### 4.1 `signals_windows` (TimescaleDB hypertable)

Aggregated biometric windows uploaded from device. **Raw samples never leave device.**

```sql
CREATE TABLE signals_windows (
  user_id               UUID NOT NULL,
  ts                    TIMESTAMPTZ NOT NULL,             -- Window start
  window_seconds        SMALLINT NOT NULL,                -- 60, 300, 900
  hrv_rmssd_ms          REAL,
  hr_bpm                REAL,
  respiration_rate      REAL,
  skin_temp_delta_c     REAL,
  step_count            INTEGER,
  sleep_quality_score   REAL,
  phone_unlock_count    SMALLINT,
  scroll_velocity_ema   REAL,
  time_of_day_bucket    SMALLINT,                         -- 0-23
  geofence_risk         SMALLINT,                         -- 0 none, 1-3 risk levels
  signal_source         TEXT NOT NULL,                    -- apple_watch, oura, whoop, fitbit, phone_only
  device_confidence     REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY (user_id, ts, window_seconds)
);

SELECT create_hypertable('signals_windows', 'ts', chunk_time_interval => INTERVAL '7 days');
SELECT add_retention_policy('signals_windows', INTERVAL '400 days');

-- Continuous aggregate for weekly trends
CREATE MATERIALIZED VIEW signals_daily
WITH (timescaledb.continuous) AS
SELECT user_id,
       time_bucket('1 day', ts) AS day,
       AVG(hrv_rmssd_ms) AS avg_hrv,
       AVG(hr_bpm) AS avg_hr,
       SUM(phone_unlock_count) AS unlocks,
       AVG(sleep_quality_score) AS sleep_q
FROM signals_windows
GROUP BY user_id, day;
```

### 4.2 `state_estimates`

Output of on-device state classifier; one record per inference tick.

```sql
CREATE TABLE state_estimates (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ts                    TIMESTAMPTZ NOT NULL,
  state_label           TEXT NOT NULL,                    -- calm, elevated, pre_urge, urge, crisis
  confidence            REAL NOT NULL,
  feature_hash          TEXT NOT NULL,                    -- Hash of inputs for reproducibility
  model_version         TEXT NOT NULL
);

SELECT create_hypertable('state_estimates', 'ts', chunk_time_interval => INTERVAL '30 days');
CREATE INDEX idx_state_user_ts ON state_estimates(user_id, ts DESC);
```

---

## 5. Intervention & Outcome

### 5.1 `urge_events`

```sql
CREATE TABLE urge_events (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  started_at            TIMESTAMPTZ NOT NULL,
  resolved_at           TIMESTAMPTZ,
  origin                TEXT NOT NULL,                    -- self_reported, predicted, sos
  tier_triggered        SMALLINT NOT NULL,                -- 0-4
  intensity_start       SMALLINT,                         -- 0-10
  intensity_peak        SMALLINT,
  intensity_end         SMALLINT,
  trigger_tags          TEXT[] NOT NULL DEFAULT '{}',     -- stress, boredom, loneliness, social, ...
  location_context      TEXT,                             -- coarse: home, work, transit, social
  handled               BOOLEAN,                          -- NULL until outcome recorded
  handled_at            TIMESTAMPTZ,
  relapse_id            UUID,                             -- FK to relapse_events if applicable
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_urge_user_started ON urge_events(user_id, started_at DESC);
CREATE INDEX idx_urge_relapse ON urge_events(relapse_id) WHERE relapse_id IS NOT NULL;
```

### 5.2 `interventions`

Every intervention fired at a user — T0 through T4.

```sql
CREATE TABLE interventions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  urge_event_id         UUID REFERENCES urge_events(id),
  tier                  SMALLINT NOT NULL,                -- 0-4
  kind                  TEXT NOT NULL,                    -- ambient_widget, nudge, coping_tool, human_handoff, ...
  tool_variant          TEXT,                             -- urge_surf_5min, box_breath_4_7_8, tipp_60s, ...
  delivered_at          TIMESTAMPTZ NOT NULL,
  channel               TEXT NOT NULL,                    -- push, in_app, widget, complication, haptic
  latency_ms            INTEGER,                          -- Time from trigger → delivery
  bandit_arm            TEXT,                             -- For contextual bandit analytics
  bandit_context_hash   TEXT,
  policy_version        TEXT NOT NULL,
  completed             BOOLEAN,
  completed_at          TIMESTAMPTZ,
  skipped               BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_int_user_delivered ON interventions(user_id, delivered_at DESC);
CREATE INDEX idx_int_urge ON interventions(urge_event_id);
CREATE INDEX idx_int_bandit ON interventions(bandit_arm, policy_version);
```

### 5.3 `outcomes`

Immutable record of intervention outcome — used for bandit reward signal and clinical evidence.

```sql
CREATE TABLE outcomes (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  intervention_id       UUID NOT NULL UNIQUE REFERENCES interventions(id),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recorded_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  outcome_type          TEXT NOT NULL,                    -- handled, partial, relapsed, no_response
  reward_scalar         REAL NOT NULL,                    -- -1.0 to 1.0 for bandit
  post_state_label      TEXT,
  user_note_id          UUID REFERENCES journals(id)
);
```

### 5.4 `relapse_events`

**This is the clinically sacred table.** Compassion-first semantics encoded in schema.

```sql
CREATE TABLE relapse_events (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  occurred_at           TIMESTAMPTZ NOT NULL,
  reported_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  behavior              TEXT NOT NULL,                    -- Matches target_behaviors
  severity              SMALLINT,                         -- 1-5 user-assessed
  context_tags          TEXT[] NOT NULL DEFAULT '{}',
  ave_score             SMALLINT,                         -- Abstinence Violation Effect severity 1-10
  review_completed      BOOLEAN NOT NULL DEFAULT false,
  review_completed_at   TIMESTAMPTZ,
  journal_id            UUID REFERENCES journals(id),
  streak_continuous_broken BOOLEAN NOT NULL DEFAULT true, -- Continuous streak resets
  streak_resilience_preserved BOOLEAN NOT NULL DEFAULT true, -- Resilience streak never resets
  pattern_signals_json  JSONB                             -- What led up; populated by pattern engine
);

CREATE INDEX idx_relapse_user_occurred ON relapse_events(user_id, occurred_at DESC);
```

Note: `streak_resilience_preserved` is hard-coded true by column default — no product code path can reset it. This is enforced at the schema level because this is the core brand promise.

---

## 6. Journals & Voice

### 6.1 `journals`

```sql
CREATE TABLE journals (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  kind                  TEXT NOT NULL,                    -- morning, evening, urge_note, relapse_review, freeform
  content_encrypted     BYTEA NOT NULL,                   -- KMS envelope
  content_hash          BYTEA NOT NULL,                   -- For dedup/verification
  word_count            INTEGER NOT NULL,
  mood_score            SMALLINT,                         -- -5 to +5
  linked_urge_id        UUID REFERENCES urge_events(id),
  linked_relapse_id     UUID REFERENCES relapse_events(id),
  embedding             vector(1024),                     -- pgvector
  tags                  TEXT[] NOT NULL DEFAULT '{}',
  source                TEXT NOT NULL DEFAULT 'text'      -- text, voice_transcript
);

CREATE INDEX idx_journal_user_created ON journals(user_id, created_at DESC);
CREATE INDEX idx_journal_embedding ON journals USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 6.2 `voice_sessions`

Voice blobs are ephemeral — transcript is persisted, audio is deleted.

```sql
CREATE TABLE voice_sessions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  started_at            TIMESTAMPTZ NOT NULL,
  ended_at              TIMESTAMPTZ,
  duration_ms           INTEGER,
  transcript_journal_id UUID REFERENCES journals(id),
  s3_blob_key           TEXT,                             -- Null after 72h purge
  blob_purged_at        TIMESTAMPTZ,
  mood_signal           JSONB                             -- Prosody-derived features
);
```

**Retention rule:** `s3_blob_key` is purged via scheduled job 72 hours after `ended_at`. Enforced by a nightly reconciliation job plus S3 lifecycle policy.

---

## 7. Pattern Engine

### 7.1 `patterns`

```sql
CREATE TABLE patterns (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind                  TEXT NOT NULL,                    -- temporal, contextual, physiological, compound
  summary               TEXT NOT NULL,
  confidence            REAL NOT NULL,
  supporting_event_ids  UUID[] NOT NULL,
  first_observed_at     TIMESTAMPTZ NOT NULL,
  last_observed_at      TIMESTAMPTZ NOT NULL,
  dismissed             BOOLEAN NOT NULL DEFAULT false,
  presented_count       INTEGER NOT NULL DEFAULT 0
);
```

---

## 8. Enterprise & Clinician

### 8.1 `enterprise_contracts`

```sql
CREATE TABLE enterprise_contracts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_name              TEXT NOT NULL,
  contact_email         TEXT NOT NULL,
  pmpm_rate_cents       INTEGER NOT NULL,
  eligible_member_count INTEGER,
  contract_start        DATE NOT NULL,
  contract_end          DATE NOT NULL,
  baa_signed_at         TIMESTAMPTZ,
  sso_config_json       JSONB,
  reporting_config_json JSONB
);
```

### 8.2 `clinician_links`

```sql
CREATE TABLE clinician_links (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinician_user_id     UUID NOT NULL REFERENCES users(id),
  patient_user_id       UUID NOT NULL REFERENCES users(id),
  status                TEXT NOT NULL,                    -- pending, active, revoked
  patient_consent_at    TIMESTAMPTZ,
  revoked_at            TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (clinician_user_id, patient_user_id)
);
```

Every read from the clinician portal against patient data checks `status = 'active'` and logs an entry in `audit_logs`.

---

## 9. Audit & Compliance

### 9.1 `audit_logs`

Append-only. Every PHI access — by user, clinician, or internal operator — logged.

```sql
CREATE TABLE audit_logs (
  id                    BIGSERIAL PRIMARY KEY,
  ts                    TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor_user_id         UUID,
  actor_role            TEXT NOT NULL,                    -- user, clinician, admin, system
  action                TEXT NOT NULL,                    -- read, write, export, delete, ...
  resource_type         TEXT NOT NULL,
  resource_id           UUID,
  target_user_id        UUID,
  request_ip_hash       BYTEA,
  request_metadata      JSONB
);

SELECT create_hypertable('audit_logs', 'ts', chunk_time_interval => INTERVAL '30 days');
SELECT add_retention_policy('audit_logs', INTERVAL '7 years');   -- HIPAA requirement
```

### 9.2 `consent_records`

```sql
CREATE TABLE consent_records (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  consent_type          TEXT NOT NULL,                    -- tos, privacy, research, clinician_link
  consent_version       TEXT NOT NULL,
  granted_at            TIMESTAMPTZ NOT NULL,
  revoked_at            TIMESTAMPTZ,
  evidence_hash         BYTEA NOT NULL                    -- Hash of the shown document
);
```

---

## 10. Derived / Analytics

### 10.1 `daily_user_rollups` (materialized view)

Refreshed hourly by background job. Used by dashboard endpoints to avoid recomputation.

```sql
CREATE MATERIALIZED VIEW daily_user_rollups AS
SELECT
  u.id AS user_id,
  DATE_TRUNC('day', i.delivered_at) AS day,
  COUNT(DISTINCT ue.id) AS urges_logged,
  COUNT(DISTINCT CASE WHEN ue.handled THEN ue.id END) AS urges_handled,
  COUNT(DISTINCT i.id) AS interventions_delivered,
  COUNT(DISTINCT re.id) AS relapses
FROM users u
LEFT JOIN urge_events ue ON ue.user_id = u.id
LEFT JOIN interventions i ON i.user_id = u.id
LEFT JOIN relapse_events re ON re.user_id = u.id
GROUP BY u.id, day;

CREATE UNIQUE INDEX idx_dur_user_day ON daily_user_rollups(user_id, day);
```

### 10.2 `streak_state`

```sql
CREATE TABLE streak_state (
  user_id                    UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  continuous_streak_start    TIMESTAMPTZ,
  continuous_days            INTEGER NOT NULL DEFAULT 0,
  resilience_streak_start    TIMESTAMPTZ NOT NULL,
  resilience_days            INTEGER NOT NULL DEFAULT 0,   -- Never decreases
  resilience_urges_handled   INTEGER NOT NULL DEFAULT 0,   -- Never decreases
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

A database trigger enforces that `resilience_days` and `resilience_urges_handled` are monotonically non-decreasing. Attempts to decrement raise `INVALID_RESILIENCE_MUTATION`.

---

## 11. Indexes, Partitioning, Performance

- Every `user_id`-scoped table indexed on `(user_id, timestamp DESC)` for the dominant access pattern ("show me this user's recent …").
- TimescaleDB hypertables for high-write, time-ranged data: `signals_windows`, `state_estimates`, `audit_logs`.
- `interventions` partitioned by month at ~10M rows/month projected Y3.
- pgvector IVFFlat index on journal embeddings; re-indexed nightly.

---

## 12. Retention & Deletion

| Data | Hot retention | Cold retention | Notes |
|------|---------------|----------------|-------|
| Raw biometric samples | 0 (device-only) | — | Never uploaded |
| `signals_windows` (60s) | 30 days | — | Aggregated into daily |
| `signals_daily` | 400 days | 2 years | For pattern engine |
| `state_estimates` | 90 days | — | |
| `urge_events` | Indefinite (user-owned) | — | |
| `interventions` | Indefinite (user-owned) | — | |
| `outcomes` | Indefinite (clinical evidence) | — | |
| `relapse_events` | Indefinite (user-owned) | — | |
| `journals` | Indefinite | — | User can delete individually |
| `voice_sessions.s3_blob_key` | 72 hours | — | Ephemeral |
| `audit_logs` | 7 years | — | HIPAA |
| `patterns` | 2 years | — | Recomputable |
| Soft-deleted users | 30 days recovery | — | Then hard delete |

### Hard-delete pipeline

1. User triggers "Delete my account" or "Quick erase."
2. Soft delete flag + `purge_scheduled_at = now() + interval '30 days'` (or `+ '10 minutes'` for quick-erase).
3. Nightly `purge_worker` job scans for expired rows, issues `DELETE` cascades, verifies with row-count assertions, and writes a final `audit_log` entry.
4. For quick-erase, a separate immediate purge job runs in under 10 minutes.

---

## 13. Encryption at Column Level

Fields marked `_encrypted BYTEA` use a per-user DEK derived from the org-level KMS key. Encryption/decryption happens in the app layer before/after DB access (envelope pattern):

```
plaintext → AES-256-GCM(DEK) → ciphertext  (stored)
DEK        → KMS.Encrypt(KEK) → wrapped_DEK (stored alongside)
```

Wrapped DEK stored in `user_encryption_keys`; KEK rotation on 90-day cadence.

```sql
CREATE TABLE user_encryption_keys (
  user_id           UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  wrapped_dek       BYTEA NOT NULL,
  kek_version       INTEGER NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  rotated_at        TIMESTAMPTZ
);
```

---

## 14. Migrations

- Tool: **Alembic** (SQLAlchemy migrations).
- Naming: `YYYYMMDD_NN_description.py`.
- All migrations must include `up()` and `down()`.
- Destructive migrations (drop column, drop table) require a 2-step ship: deprecation → remove in subsequent release.
- Migration linting in CI blocks: un-indexed `user_id` columns, missing `ON DELETE`, un-retention-policied hypertables.

---

## 15. Schema Evolution Policy

- Additive changes: ship anytime.
- Rename/drop: requires two-phase deploy (new column + backfill + switch + remove after 14 days).
- Breaking changes to API-exposed columns: require API version bump.

---

## 16. Cross-Reference to Code

| Table | Owning service module |
|-------|----------------------|
| `users`, `user_profiles` | `discipline.identity` |
| `subscriptions` | `discipline.billing` |
| `signals_windows`, `state_estimates` | `discipline.signal` |
| `urge_events`, `interventions`, `outcomes` | `discipline.intervention` |
| `relapse_events` | `discipline.clinical` |
| `journals`, `voice_sessions` | `discipline.memory` |
| `patterns` | `discipline.pattern` |
| `enterprise_contracts`, `clinician_links` | `discipline.enterprise` |
| `audit_logs`, `consent_records` | `discipline.compliance` |
| `streak_state` | `discipline.resilience` |
| `psychometric_instruments`, `psychometric_assessments`, `psychometric_change_events`, `psychometric_preferences` | `discipline.psychometric` — see [12](12_Psychometric_System.md) §8 for full DDL |
| `psychometric_trajectories`, `daily_user_rollups` | `discipline.analytics` — see [13](13_Analytics_Reporting.md) §3.2–3.3 |

---

## 17. Tables defined in other documents

Some operational tables are specified in their owning-subsystem document to keep the schema close to the logic:

- **Psychometric** — `psychometric_instruments`, `psychometric_assessments`, `psychometric_change_events`, `psychometric_preferences` are defined in [12_Psychometric_System](12_Psychometric_System.md) §8.
- **Analytics** — `daily_user_rollups` is the materialized backbone of user-facing trajectories; `psychometric_trajectories` is the derived store used for chart rendering. Both are specified in [13_Analytics_Reporting](13_Analytics_Reporting.md) §3.
- **Auth session** — refresh token families, active-session registry, and the clerk↔server id mapping live in Redis (volatile) and in a small `auth_session_families` Postgres table for reuse-detection forensics; specified in [14_Authentication_Logging](14_Authentication_Logging.md) §2.

All tables across documents obey the same conventions declared in §1 (minimization, retention, append-only clinical evidence, user-owned, encryption at rest, retention policy per table).
