# API Specification — Discipline OS

## 1. Conventions

- **Base URL:** `https://api.disciplineos.com`
- **Versioning:** URL-based — `/v1/...` → `/v2/...`. No version sunset within 18 months of successor release.
- **Auth:** Our own EdDSA-signed session JWT (issued via `/v1/auth/exchange` after Clerk login), validated by API gateway. Full spec: [14_Authentication_Logging](14_Authentication_Logging.md).
- **Content-Type:** `application/json` for REST. `application/protobuf` optional for signal upload (bandwidth optimization).
- **Time format:** RFC3339 UTC — `2026-04-18T14:32:00Z`. All clinical exports use ISO 8601 regardless of user locale.
- **IDs:** UUIDv7 (time-sortable) for all entity IDs.
- **Pagination:** Cursor-based. `?limit=50&cursor=<opaque>`.
- **Idempotency:** `Idempotency-Key` header required on all non-GET operations. Server stores for 24h.
- **Rate limits:** Per-user + per-IP. Burst + sustained limits. `429` with `Retry-After`.
- **Errors:** RFC 7807 Problem Details.
- **Localization:** Server honors `Accept-Language` for one-shot responses and `users.locale` (authoritative) for server-generated content (emails, push, PDFs). See [15_Internationalization](15_Internationalization.md) §3.3.
- **Step-up auth:** Sensitive actions return `401` with `WWW-Authenticate: step_up, max_age=300` if the session's last re-authentication is older than 5 minutes. See [14](14_Authentication_Logging.md) §2.8.

---

## 2. Authentication

### 2.1 Session exchange (Clerk → server JWT)

```
POST /v1/auth/session
Authorization: Bearer <clerk_jwt>

→ 200
{
  "server_session_token": "eyJ...",
  "expires_at": "2026-04-18T15:32:00Z",
  "user_id": "018f5aa0-...",
  "refresh_token": "rf_..."
}
```

### 2.2 Session refresh

```
POST /v1/auth/refresh
{ "refresh_token": "rf_..." }
→ 200 { "server_session_token": "...", "expires_at": "..." }
```

### 2.3 Device registration

```
POST /v1/auth/devices
{
  "platform": "ios" | "android",
  "device_model": "iPhone15,3",
  "os_version": "18.2.1",
  "app_version": "1.3.0",
  "push_token": "APNs-or-FCM-token",
  "device_attestation": "<DeviceCheck/Play Integrity token>"
}
→ 201 { "device_id": "...", "registered_at": "..." }
```

---

## 3. Identity & Profile

### 3.1 Current user

```
GET /v1/me
→ 200
{
  "id": "018f...",
  "handle": "kai",
  "timezone": "America/Los_Angeles",
  "locale": "en-US",
  "created_at": "2026-01-12T...",
  "subscription": {
    "tier": "plus",
    "status": "active",
    "current_period_end": "2026-05-12T..."
  },
  "flags": {
    "app_lock_enabled": true,
    "alt_icon_enabled": false
  }
}
```

### 3.2 Update profile

```
PATCH /v1/me
{ "timezone": "America/New_York", "locale": "en-US" }
→ 200 <updated user>
```

### 3.3 Clinical profile

```
GET /v1/me/profile
PATCH /v1/me/profile
{
  "target_behaviors": ["alcohol", "doomscroll"],
  "baseline_severity": 6,
  "ema_frequency": "twice_daily",
  "crisis_contact": {
    "name": "Alex",
    "phone": "+1-555-...",
    "relationship": "partner"
  },
  "local_hotline_country": "US"
}
```

The `crisis_contact` field is encrypted application-side before hitting the DB.

---

## 4. Signal Upload

### 4.1 Batch signal upload (from device)

Client submits aggregated windows only. Sampling rates per signal are device-enforced.

```
POST /v1/signals/windows
Content-Type: application/json

{
  "windows": [
    {
      "ts": "2026-04-18T14:30:00Z",
      "window_seconds": 60,
      "hrv_rmssd_ms": 32.5,
      "hr_bpm": 78,
      "step_count": 12,
      "phone_unlock_count": 3,
      "scroll_velocity_ema": 1.82,
      "geofence_risk": 0,
      "signal_source": "apple_watch",
      "device_confidence": 0.97
    },
    ...
  ]
}
→ 202 { "accepted": 47, "rejected": 0 }
```

- **Compression:** gzip required for payloads >4KB.
- **Batching:** clients send every 5 minutes normally, every 60 seconds during elevated-state episodes.
- **Offline:** client-side SQLite queue retains up to 48h of unsent windows.

### 4.2 Latest state estimate

State is computed on-device and mirrored to server. Server also recomputes for audit but doesn't surface differences to user.

```
POST /v1/state/estimate
{
  "ts": "2026-04-18T14:32:00Z",
  "state_label": "elevated",
  "confidence": 0.84,
  "feature_hash": "sha256:...",
  "model_version": "state_classifier_v0.9.2"
}
→ 204
```

---

## 5. Intervention Lifecycle

### 5.1 User-initiated urge log (T2/T3 entry)

```
POST /v1/urges
Idempotency-Key: <uuid>
{
  "started_at": "2026-04-18T14:32:00Z",
  "intensity_start": 7,
  "trigger_tags": ["stress", "work_deadline"],
  "location_context": "work",
  "origin": "self_reported"
}
→ 201
{
  "urge_id": "018f...",
  "recommended_tool": {
    "tool_variant": "urge_surf_5min",
    "rationale": "Your last 4 urges were handled with urge surfing.",
    "bandit_arm": "urge_surf_5min:ctx_work_high",
    "intervention_id": "018f..."
  }
}
```

The `recommended_tool` comes from the contextual bandit policy. Latency budget: **p95 < 400ms warm, < 800ms cold.**

### 5.2 SOS trigger (T3 crisis)

```
POST /v1/sos
Idempotency-Key: <uuid>
{
  "started_at": "2026-04-18T14:32:00Z"
}
→ 201
{
  "urge_id": "...",
  "intervention_id": "...",
  "payload": {
    "ui_template": "crisis_flow_v3",
    "tools_hardcoded": ["urge_surf", "tipp_60s", "call_support"],
    "support_contact": {
      "name": "Alex",
      "phone": "+1-555-..."
    },
    "local_hotline": "988"
  }
}
```

**Crisis rule:** the response is served from pre-cached payload on the device when possible. Network call is fire-and-forget; the UI must render crisis flow even if the call times out.

### 5.3 Resolve urge

```
POST /v1/urges/{urge_id}/resolve
{
  "intensity_peak": 8,
  "intensity_end": 3,
  "handled": true,
  "note": "Walked around the block, called Alex."
}
→ 200 { "urge": {...}, "streak": {...} }
```

### 5.4 Record outcome

```
POST /v1/interventions/{intervention_id}/outcome
{
  "outcome_type": "handled",
  "post_state_label": "calm",
  "user_note": "Worked. 7 → 3 in about 4 minutes."
}
→ 201 { "outcome_id": "..." }
```

### 5.5 Nudge acknowledgement (T1)

```
POST /v1/interventions/{intervention_id}/ack
{
  "ack": "accepted" | "snoozed" | "dismissed"
}
→ 204
```

---

## 6. Relapse Protocol

### 6.1 Report relapse

```
POST /v1/relapses
Idempotency-Key: <uuid>
{
  "occurred_at": "2026-04-18T21:15:00Z",
  "behavior": "alcohol",
  "severity": 3,
  "context_tags": ["social", "anniversary"]
}
→ 201
{
  "relapse_id": "...",
  "next_steps": [
    "compassion_message",
    "review_prompt",
    "streak_update_summary"
  ],
  "resilience_streak_days": 87,
  "resilience_urges_handled_total": 142
}
```

Server responds with explicit confirmation that resilience streak was preserved — the client must display this affirmation.

### 6.2 Complete relapse review

```
POST /v1/relapses/{relapse_id}/review
{
  "journal_id": "...",
  "ave_score": 4,
  "context_tags_refined": ["social", "anniversary", "low_sleep"]
}
→ 200
```

---

## 7. Journals & Memory

### 7.1 Create journal entry

```
POST /v1/journals
{
  "kind": "evening",
  "content": "Long day. Managed the 5pm window by taking a walk.",
  "mood_score": 2,
  "tags": ["work", "handled"],
  "linked_urge_id": null
}
→ 201 { "journal_id": "...", "embedded": true }
```

Server encrypts `content` on write. Returns `embedded: true` after async embedding completes (usually <500ms).

### 7.2 List journals

```
GET /v1/journals?from=2026-04-01&to=2026-04-18&limit=50
→ 200 { "journals": [...], "next_cursor": "..." }
```

### 7.3 Search journals (semantic + keyword)

```
POST /v1/journals/search
{
  "query": "times I felt overwhelmed at work",
  "limit": 10
}
→ 200 { "results": [ { "journal_id": "...", "score": 0.89, "excerpt": "..." } ] }
```

### 7.4 Voice session

```
POST /v1/voice/sessions
{ "started_at": "2026-04-18T14:32:00Z" }
→ 201 { "session_id": "...", "upload_url": "https://s3-presigned..." }

PUT <upload_url>
Body: <opus-encoded audio>
→ 200

POST /v1/voice/sessions/{session_id}/finalize
→ 202 { "transcript_status": "processing" }

GET /v1/voice/sessions/{session_id}
→ 200 {
  "status": "complete",
  "journal_id": "...",
  "blob_purge_at": "2026-04-21T14:32:00Z"
}
```

---

## 8. Patterns & Insights

### 8.1 Current patterns

```
GET /v1/patterns?active=true
→ 200
{
  "patterns": [
    {
      "id": "...",
      "kind": "temporal",
      "summary": "Urges peak Fridays 5-7pm, 4 of last 5 weeks.",
      "confidence": 0.78,
      "actionable": true,
      "suggested_action": "pre_commitment_window"
    }
  ]
}
```

### 8.2 Dismiss pattern

```
POST /v1/patterns/{id}/dismiss
{ "reason": "not_useful" | "false_pattern" | "not_now" }
→ 204
```

### 8.3 Weekly report

```
GET /v1/reports/weekly?week=2026-W16
→ 200
{
  "week": "2026-W16",
  "urges_logged": 12,
  "urges_handled": 10,
  "relapses": 1,
  "resilience_streak_days": 87,
  "continuous_streak_days": 5,
  "top_triggers": ["work_deadline", "evening_alone"],
  "pattern_highlights": [...],
  "recommendations": [...]
}
```

---

## 9. Streak & State

### 9.1 Current streak

```
GET /v1/streak
→ 200
{
  "continuous_days": 5,
  "continuous_streak_start": "2026-04-13T...",
  "resilience_days": 87,
  "resilience_urges_handled_total": 142,
  "resilience_streak_start": "2026-01-21T..."
}
```

### 9.2 Today's state summary

```
GET /v1/today
→ 200
{
  "current_state": "elevated",
  "state_confidence": 0.81,
  "risk_windows_today": [
    { "start": "2026-04-18T17:00:00Z", "end": "2026-04-18T19:00:00Z", "kind": "predicted_urge" }
  ],
  "check_in_due": true,
  "open_interventions": []
}
```

---

## 10. Notifications & Nudges

### 10.1 Nudge preferences

```
GET /v1/nudges/prefs
PATCH /v1/nudges/prefs
{
  "quiet_hours": { "start": "22:00", "end": "06:00" },
  "max_per_day": 4,
  "channels": ["push", "widget"],
  "ambient_widget_enabled": true
}
```

### 10.2 Server-pushed nudge (delivery via APNs/FCM)

```
Payload (APNs alert):
{
  "aps": { "alert": { "title": "...", "body": "..." }, "sound": null, "category": "NUDGE_T1" },
  "intervention_id": "...",
  "tier": 1,
  "tool_variant": "box_breath_4_7_8"
}
```

On tap, deep-link: `disciplineos://intervention/{intervention_id}`.

---

## 11. Subscriptions & Billing

### 11.1 Current subscription

```
GET /v1/billing/subscription
→ 200 { "tier": "plus", "status": "active", "current_period_end": "..." }
```

### 11.2 Start checkout (web)

```
POST /v1/billing/checkout
{ "tier": "pro", "billing_cycle": "monthly" }
→ 201 { "checkout_url": "https://checkout.stripe.com/..." }
```

### 11.3 Upload IAP receipt (mobile)

```
POST /v1/billing/iap
{
  "platform": "ios",
  "receipt": "base64...",
  "product_id": "plus_monthly"
}
→ 200 { "subscription": {...} }
```

### 11.4 Cancel

```
POST /v1/billing/cancel
{ "reason": "not_using" | "too_expensive" | "other", "feedback_text": "optional" }
→ 200 { "canceled_at": "...", "access_until": "..." }
```

No retention dark patterns. No "are you sure" loops. One tap, clear confirmation.

---

## 12. Clinician Portal (v2)

### 12.1 Patient list (clinician)

```
GET /v1/clinician/patients?status=active
→ 200 { "patients": [ { "patient_user_id": "...", "handle": "...", "linked_at": "...", "last_active": "..." } ] }
```

### 12.2 Patient dashboard (clinician, consented access)

```
GET /v1/clinician/patients/{patient_id}/dashboard
→ 200
{
  "resilience_days": 87,
  "urges_last_30d": 42,
  "handled_rate": 0.83,
  "relapses_last_30d": 1,
  "patterns": [...],
  "recent_journals_excerpt_count": 12   // Clinician sees count not content unless patient shares
}
```

### 12.3 Send check-in prompt to patient

```
POST /v1/clinician/patients/{patient_id}/prompts
{ "kind": "reflection", "body": "How did Thursday go?" }
→ 201
```

Every clinician read/write logs an entry in `audit_logs`.

---

## 13. Enterprise Admin

### 13.1 Aggregate report (no PHI)

```
GET /v1/enterprise/{org_id}/reports/monthly
→ 200
{
  "active_members": 1420,
  "engagement_rate": 0.41,
  "aggregate_wuh": 0.68,
  "retention_6mo": 0.58
}
```

Minimum cohort size of **200 members** for any aggregate metric — rows below threshold are withheld. Re-identification attack surface analysis reviewed annually.

---

## 14. Data Export & Delete

### 14.1 Export

```
POST /v1/me/export
→ 202 { "export_id": "...", "ready_at_estimate": "2026-04-18T15:00:00Z" }

GET /v1/me/export/{export_id}
→ 200 { "status": "ready", "download_url": "https://s3-presigned...", "expires_at": "..." }
```

Export format: JSON bundle of all user-owned rows + CSV of time-series + zipped journal text.

### 14.2 Delete account

```
DELETE /v1/me
Body: { "confirmation_phrase": "DELETE MY ACCOUNT" }
→ 202 { "deletion_scheduled_at": "...", "recovery_until": "2026-05-18T..." }
```

### 14.3 Quick-erase (immediate)

```
POST /v1/me/quick-erase
{ "confirmation_phrase": "ERASE NOW" }
→ 202 { "erase_id": "...", "completes_by": "2026-04-18T14:42:00Z" }
```

Completes in under 10 minutes. Confirmation email sent to registered address.

---

## 15. WebSocket / Realtime

### 15.1 Connection

```
wss://api.disciplineos.com/v1/realtime
Authorization: Bearer <server_session_token>
```

### 15.2 Messages

**Server → client:**

```
{ "type": "intervention_delivered", "intervention_id": "...", "tier": 1, "payload": {...} }
{ "type": "pattern_updated", "pattern_id": "...", "summary": "..." }
{ "type": "streak_updated", "continuous_days": 6, "resilience_days": 87 }
{ "type": "clinician_message", "from": "...", "body": "..." }
```

**Client → server:**

```
{ "type": "heartbeat" }
{ "type": "state_change", "state_label": "elevated", "confidence": 0.8 }
```

Heartbeat expected every 30s. Missed 3 in a row → server closes socket.

---

## 16. Errors

All errors conform to RFC 7807:

```
{
  "type": "https://api.disciplineos.com/errors/validation",
  "title": "Invalid request",
  "status": 400,
  "detail": "urge_event.intensity_start must be 0-10",
  "instance": "urn:req:018f..."
}
```

Canonical error codes (subset):

| Status | Type | When |
|--------|------|------|
| 400 | validation | Schema or domain validation failed |
| 401 | unauthenticated | Missing/invalid token |
| 403 | forbidden | Authenticated but no access |
| 404 | not_found | Resource unknown |
| 409 | conflict | Idempotency collision or concurrent update |
| 422 | unprocessable | Valid but semantically rejected |
| 429 | rate_limited | Retry-After provided |
| 451 | policy_refused | Crisis fallback — never return 500 on T3 path |
| 500 | internal | Server failure (logged, traced) |
| 503 | unavailable | Dependency down |

### 451 rationale (T3 path)

On T3 (crisis) endpoints, if the server cannot safely fulfill the request (e.g., internal classifier failure), it returns **451 with a deterministic fallback payload** rather than 500. The client treats this as a successful-degraded response and shows the hardcoded crisis UI.

---

## 17. Rate Limits

| Path class | Per-user | Per-IP |
|------------|----------|--------|
| Signal upload | 300/min | 1000/min |
| Urge/SOS/Outcome | 60/min | 200/min |
| Journal writes | 120/min | 400/min |
| Reads | 600/min | 2000/min |
| Auth | 30/min | 60/min |

SOS is **never** rate-limited at the per-user level below 10/min. A user can always reach crisis mode.

---

## 18. Versioning Policy

- **Minor (additive):** New field, new endpoint, non-breaking enum addition. Current version header `X-API-Minor`.
- **Major:** Breaking changes require a new `/vN/` path with 18-month deprecation overlap.
- Clients send `X-Client-Version: <semver>`. Server logs per-version usage to inform deprecation.

---

## 19. Observability Headers

All responses include:

```
X-Request-ID: 018f...
X-Trace-ID: 018f...
X-SLO-Tier: T3_CRISIS | T2_WORKFLOW | T1_NUDGE | T0_READ
X-Server-Timing: db;dur=23, ml;dur=47, total;dur=112
```

---

## 20. Psychometric endpoints

Full behavior: [12_Psychometric_System](12_Psychometric_System.md) §9.

```
GET  /v1/psychometric/due
     → Which instruments are due for this user now. Scheduler-driven; respects
       "never during an urge window" and "one instrument per session" rules.

POST /v1/psychometric/assessments
     Body: { instrument_id, version, responses: [...] }
     → 201 {
         assessment_id,
         total_score,            // deterministic via pure scoring fn
         subscale_scores,
         severity_band,          // cited bands, not LLM-interpreted
         rci_vs_baseline,
         rci_vs_previous,
         clinically_significant_change,
         safety_actions: [...]   // e.g. "escalate_t4" if PHQ-9 item 9 ≥ 1
       }

GET  /v1/psychometric/assessments?instrument=phq9&limit=50
     → List of past assessments with provenance

GET  /v1/psychometric/trajectories?instrument=phq9&window=180d
     → Trajectory series for chart rendering, with RCI annotations and
       framing ready to consume on the user surface.

GET  /v1/psychometric/preferences
POST /v1/psychometric/preferences
     → User-configurable cadence, opt-outs per instrument, quiet-hours.
```

Safety items (PHQ-9 item 9, C-SSRS positives) trigger immediate T4 routing at submission time. The API always returns the safety action in the response envelope. The client must always honor it.

---

## 21. Insights & reporting

Full behavior: [13_Analytics_Reporting](13_Analytics_Reporting.md) §9.

### 21.1 User insights (framing-applied)

```
GET /v1/insights/today
    → Home card payload with resilience-days headline, urges handled today, etc.
      Framing rules P1–P6 already applied server-side.

GET /v1/insights/week?week_of=2026-04-13
    → Weekly Reflection, pre-rendered by Sunday 16:00 local.

GET /v1/insights/month?month=2026-04
    → Monthly Story.

GET /v1/insights/patterns
    → Patterns currently surfaceable to the user (confidence-gated, explained).

GET /v1/insights/trajectory?instrument=phq9&window=180d
    → User-facing version of the trajectory (protective framing — RCI-gated,
      no "worst ever" superlatives, no T3 events in the series).
```

### 21.2 Full data export (HIPAA Right of Access)

```
POST /v1/me/export
     Body: { scopes: ["profile","journals","psychometric","audit", ...] }
     → 202 { export_id, status: "queued" }
     Step-up auth required.

GET  /v1/me/export/{export_id}/status
     → { status: "ready" | "processing" | "failed", download_url?, expires_at? }

GET  /v1/me/audit?from=2026-01-01&to=2026-04-18
     → The user's own audit trail (what was accessed, by whom, when).

POST /v1/me/quick-erase
     → 202 { confirmation_token_required: true }
     Step-up auth + 24h soft-delete window; hard-delete then cascades (see 07).
```

### 21.3 Clinician-facing reporting

All endpoints are scope-gated by `clinician_links.scopes` for the target patient.

```
GET /v1/clinician/patients
    → Patients who have actively linked this clinician.

GET /v1/clinician/patients/{user_id}/summary?format=pdf|fhir|hl7v2
    → Clinical summary. Digitally signed. Audit-logged.

GET /v1/clinician/patients/{user_id}/trajectories?instrument=phq9&window=90d
    → Scientific-rigor version (no protective smoothing).

GET /v1/clinician/patients/{user_id}/adherence
    → Assessment completion cadence and gaps.
```

### 21.4 Enterprise portal

```
GET /v1/enterprise/{contract_id}/report?period=2026-04
    → Aggregate report. Enforces k-anonymity ≥ 5 per cell, cohort ≥ 25 required,
      differential-privacy noise on published figures. See 13 §6.

GET /v1/enterprise/{contract_id}/provisioning/scim/v2/Users
POST /v1/enterprise/{contract_id}/provisioning/scim/v2/Users
    → SCIM 2.0 provisioning/deprovisioning. SSO required to even call these.
```

---

## 22. Authentication endpoints (full)

Full spec: [14_Authentication_Logging](14_Authentication_Logging.md) §2.

```
POST /v1/auth/exchange
     Body: { clerk_token }
     → { server_session_token, refresh_token, expires_at, user_id }

POST /v1/auth/refresh
     Body: { refresh_token }
     → { server_session_token, refresh_token, expires_at }
     Reuse of a previously-rotated refresh token kills the entire session
     family and forces re-auth on all devices.

POST /v1/auth/step-up
     Body: { method: "passkey" | "totp" | "password", credential: ... }
     → { step_up_token, valid_until }

POST /v1/auth/sessions/revoke
     Body: { session_id? }  // omit to revoke all sessions except current

GET  /v1/auth/sessions
     → List of active sessions with device and last-seen info.

POST /v1/auth/mfa/enroll
POST /v1/auth/mfa/verify
POST /v1/auth/mfa/disable   // step-up + 72h grace for clinician-linked accounts
GET  /v1/auth/mfa/backup-codes/regenerate   // step-up required
```

---

## 23. Web-surface notes

- The web apps use our session JWT in an `httpOnly`, `Secure`, `SameSite=Strict` cookie. CSRF protection via double-submit cookie pattern for state-changing endpoints.
- The crisis static page at `crisis.disciplineos.com` does **not** call this API. It renders pre-bundled deterministic content. The deeplink-to-mobile flow is an unauthenticated universal link.
- Enterprise portal endpoints refuse requests without a valid SSO-issued session (SAML or OIDC). Password sessions are rejected on these endpoints even if otherwise valid.

Clients attach these to telemetry for latency budgeting.
