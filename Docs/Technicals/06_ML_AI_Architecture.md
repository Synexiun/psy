# ML & AI Architecture — Discipline OS

## 1. Philosophy

1. **Edge-first by default.** Inference that can run on-device, runs on-device.
2. **Smallest model that works.** A 400KB quantized classifier beats a cloud LLM for state estimation — we don't pay a 200ms RTT on every heartbeat.
3. **Probabilistic, not deterministic, everywhere except crisis.** T3/T4 is never ML-output-dependent.
4. **Bounded LLM use.** Claude is our content writer, not our therapist.
5. **Transparent models first.** We prefer logistic regression, GBMs, small LSTMs over deep opaque nets for clinical defensibility.
6. **Human-in-the-loop for anything clinical-adjacent.** Methodology review on every model trained with clinical intent.

---

## 2. Model Inventory

| # | Model | Job | Type | Runs on | Update cadence |
|---|-------|-----|------|---------|----------------|
| 1 | State classifier | Label (calm / elevated / pre-urge / urge / crisis) | 4-layer MLP on 30-min features | iOS/Android | Monthly |
| 2 | Urge predictor | Forecast next-urge probability & horizon | 2-layer LSTM with attention | iOS/Android | Monthly |
| 3 | Intervention bandit | Pick tool variant | Thompson-sampled contextual bandit | Server + device cache | Hourly weights |
| 4 | Pattern miner | Detect temporal/contextual patterns | Rule + statistical (FP-growth, DTW) | Server batch | Nightly |
| 5 | Prosody mood | Voice→arousal/valence | Wav2Vec2 distilled, 1.8MB | Device only | Quarterly |
| 6 | Transcript | Voice→text | Whisper-small (244MB iOS) or Whisper-base server-side | Device preferred, server fallback | Quarterly |
| 7 | Journal embeddings | Semantic search + cluster | `text-embedding-3-small` equivalent, 1024-dim | Server | Immutable v-pinned |
| 8 | Relapse risk (aggregate) | Population-level risk for analytics | Survival model | Server batch | Weekly |
| 9 | Content generator | Weekly report narrative, reflection prompts | Claude API (Haiku 4.5 / Sonnet 4.6 routed) | Cloud | External |
| 10 | Safety classifier | Suicide ideation / self-harm flagging in journals | Calibrated binary classifier | Server | Monthly, methodology-reviewed |

---

## 3. State Classifier

**Goal:** at each inference tick, produce a label + calibrated confidence.

**Features (per 30-min window):**
- HRV RMSSD (mean, std, delta-from-baseline)
- HR (mean, std, delta-from-baseline)
- Respiration rate
- Skin temperature delta
- Step count (last 60 min)
- Phone unlock count
- Scroll velocity EMA
- Time-of-day bucket (cyclic encoding)
- Geofence risk (categorical, 0–3)
- Prior-window state label (as feature — autoregressive)

Training data: early cohort comes from our internal simulated/staff data, Month 6–8 from beta users with labeled urge/non-urge windows, Month 14+ from supervised learning + RLHF-style click-signal.

**Architecture:** 4-layer MLP, 128→64→32→output. ReLU, dropout 0.2. 5-way softmax. Quantized to int8 post-training.

**Size budget:** 400KB.
**Latency budget:** <50ms on device.

**Calibration:** isotonic regression on validation set; confidence output is probability-calibrated. Under-confident predictions (<0.6) produce "neutral" UI state, not escalation.

**Failure mode:** if model returns error or confidence <0.4, system falls back to rule-based heuristic ("HR > baseline + 15bpm and unlocks > 10 in 5min → elevated"). Rule never returns urge or crisis labels.

---

## 4. Urge Predictor

**Goal:** forecast probability of an urge in the next 0–120 minutes.

**Features:** last 48h of state labels + signal windows + contextual flags (day-of-week, weather if available).

**Architecture:** 2-layer LSTM + attention, 64 hidden units, sigmoid output for prob, regression head for horizon.

**Training:**
- Labels from self-reported urges + handled / relapse outcomes.
- Class imbalance handled via focal loss.
- Per-user fine-tuning layer (adapter pattern) — last 50 events reweight the output.

**Quantization:** mixed-precision, ~2.5MB on disk.
**Latency:** <120ms on device.

**Uses:**
- Pre-empt T1 nudges — "next 90 min look elevated for you."
- Surface Friday 6pm-style pattern timing.
- Gate ambient widget state rendering.

**Constraint:** predictor **never** unilaterally triggers a T3 experience. Crisis only escalates from confirmed user signal.

---

## 5. Intervention Bandit

**Goal:** pick the tool variant most likely to produce "handled" outcome given context.

**Why bandit instead of full RL:** bandits are sample-efficient, interpretable, and well-studied in health intervention research (see Liao, Murphy — SARA, HeartSteps).

**Algorithm:** Thompson-sampled contextual bandit with neural network outputs (not linear) — aka Neural Bandit.

**Context vector:**
- state_label (one-hot)
- state_confidence
- time_of_day_bucket
- day_of_week
- recent_handled_rate (last 7 days)
- recent_tool_variants_tried (last 5)
- trigger_tags (bag-of-words over 12 known tags)
- urge_intensity_start

**Reward:**
- `+1.0` handled
- `+0.3` partial handle (intensity reduction >50%)
- `-1.0` relapse (to that behavior within 4h)
- `0.0` no response / no data

**Arms:** every tool variant in the `ToolRegistry` (~25 variants at launch).

**Exploration rate:** 15% ε-greedy floor — ensures we don't collapse to a single tool early.

**Training cadence:** weights updated hourly from last-24h outcomes, deployed via model registry.

**Per-user personalization:** the bandit aggregates globally but a per-user adapter biases toward tools the user has confirmed helpful. This blend is 70% global / 30% personal until user has 50 outcomes, then 50/50.

**Guardrails:**
- Tool variants flagged "high-effort" (5+ min) deprioritized when state is high-arousal or geolocation is "transit."
- Tool variants requiring private space deprioritized when signals suggest public context.
- Bandit output always top-3, user sees top-1 but "try another" reveals top-2 and top-3.

---

## 6. Pattern Miner

**Goal:** produce actionable, human-readable patterns for the "weekly insights" surface.

**Pattern types:**

1. **Temporal:** FP-growth over `(hour_of_day, day_of_week)` with minimum support 3 occurrences in 4 weeks.
2. **Contextual:** chi-squared test over trigger tags for elevation association.
3. **Physiological:** Granger-causality on HRV vs. urge events.
4. **Compound:** sequence mining (PrefixSpan) over labeled signal sequences preceding urges.

**Output:** `Pattern` object with:
- Plain-language summary
- Supporting event IDs (evidence)
- Confidence (Bayesian posterior from occurrence vs. expected)
- Suggested action (tied to action templates)

**Privacy:** everything runs on aggregated per-user data. No cross-user joins in pattern mining — cross-user learning happens in model training, not pattern generation.

---

## 7. Voice Pipeline

### 7.1 Transcription

- **Primary:** on-device Whisper-small (en) — 244MB, ships with app on iOS/Android Pro devices.
- **Fallback:** server-side Whisper-base for lower-end devices (e.g., Android <API 33).
- Voice blobs transit end-to-end encrypted S3, purged at 72h.

### 7.2 Prosody

Distilled Wav2Vec2 model emits frame-level arousal/valence. Aggregated over the session. Surfaced as "voice tone" sparkline in journal detail view. Never labels "distressed" — that's clinical-adjacent and reserved for safety classifier.

---

## 8. Safety Classifier

**This is the most important model in the system for downside risk.**

**Goal:** flag journals (text or transcribed voice) containing signals of suicidal ideation or self-harm intent, routing to T4 human handoff.

**Design:**
- Dual-signal: a BERT-base classifier fine-tuned on annotated clinical corpora + a hand-curated keyword/phrase list (belt + braces).
- Output: `risk = {none, low_concern, elevated, imminent}`.
- Threshold calibration tuned for **high recall** (false positives acceptable; false negatives catastrophic).
- Target: recall ≥ 98% on held-out validation; precision ≥ 40% (we accept 2.5:1 noise ratio).

**Pipeline:**
1. Every journal entry scored post-write.
2. If `elevated` or `imminent` → silent alert to on-call clinical operator (NOT user-visible alarm — that could retraumatize).
3. `imminent` → in-app nudge to connect to hotline + crisis flow; operator SLA 30-min outreach if user has consented to clinical oversight.

**Review cadence:** monthly evaluation; any missed case is reviewed with clinical advisors. Model updates require clinical advisor sign-off.

**User communication:** disclosed in onboarding: "Sometimes our system will detect a journal entry that suggests you might benefit from extra support. We may follow up with a gentle check-in."

---

## 9. LLM Integration (Claude API)

### 9.1 Approved use cases

| Use case | Model routed | Context size | Latency budget |
|----------|-------------|--------------|----------------|
| Weekly report narrative | Haiku 4.5 | ~2k in / 400 out | <3s |
| Reflection prompt generation | Haiku 4.5 | ~500 in / 100 out | <2s |
| Journal title suggestion | Haiku 4.5 | ~200 in / 20 out | <1s |
| Pattern explanation | Sonnet 4.6 | ~1k in / 200 out | <2s |
| Monthly "state of you" letter | Sonnet 4.6 | ~3k in / 600 out | <5s |

### 9.2 Forbidden use cases

- T3 crisis messaging (deterministic only)
- Relapse post-event messaging (deterministic compassion templates)
- Any free-form advice to users
- Any role-play ("I'm your therapist") stance
- Diagnosis-adjacent output

### 9.3 Prompt architecture

All prompts live in `src/discipline/llm/prompts/` as versioned templates. Each prompt includes:
- **System:** role boundaries, safety rules, output format spec.
- **User:** structured context injection.
- **Constraints:** explicit "do not" list (don't diagnose, don't claim efficacy, don't reference streaks in moralizing language).

### 9.4 Safety filter chain

1. **Pre-LLM input filter:** strip PII beyond what's necessary. Redact user crisis-context phone number before sending. Reject if safety-classifier flagged content in the last 24h (escalate to human, skip LLM).
2. **Post-LLM output filter:** scan for forbidden patterns (diagnostic language, absolutes like "you'll never," shame-adjacent phrases). Flagged outputs replaced with a deterministic fallback template.
3. **Output review in shadow mode:** first 30 days of any new prompt, every output is stored + sampled for clinical advisor review before being user-visible.

### 9.5 Cost management

- Per-user quota (see tier quotas in backend services doc).
- Per-org enterprise caps.
- Degraded mode: if monthly spend > budget, fall back to template-only outputs for non-paying users.
- Anthropic prompt caching used aggressively for system prompts (they're identical across users).

---

## 10. Embeddings & Vector Search

**Model:** 1024-dim text embeddings. We start with Anthropic/OpenAI embeddings; migrate to a self-hosted alternative (BGE-M3 or similar) once cost + volume pressures justify.

**Store:** pgvector with IVFFlat (100 lists) for the first 1M vectors, HNSW after.

**Uses:**
- Semantic search of user's own journals.
- Journal-cluster-based pattern detection.
- "Find similar moments" UX in weekly report.

**Never:**
- Cross-user search (each user's vector space is logically isolated).
- Content-based recommendation of other users' content.

---

## 11. Model Training Pipeline

### 11.1 Data lake

- Biometric window aggregates (non-PII) → S3 parquet, partitioned by date.
- Labeled urge/outcome events → separate S3 prefix with BAA-scope.
- Journals never enter the training lake — training on journal text is forbidden without opt-in clinical trial consent.

### 11.2 Orchestration

- Airflow DAGs for scheduled training.
- SageMaker Training Jobs for compute.
- Experiments tracked in MLflow.
- Every promoted model version pinned with:
  - Training dataset hash
  - Code commit SHA
  - Hyperparameters
  - Evaluation metrics
  - Clinical advisor sign-off (for safety + clinical models)

### 11.3 Validation gates

- State classifier: holdout accuracy ≥ 87%, calibration ECE < 0.05.
- Urge predictor: AUROC ≥ 0.78, Brier score ≤ 0.18.
- Bandit: offline counterfactual eval (IPS estimator) > baseline + 5%.
- Safety classifier: recall ≥ 98% with false-positive rate ≤ 2.5×.

Failing any gate blocks promotion.

---

## 12. Federated Learning (v2+)

Post-launch, for users who opt in:
- Local gradient computation against a global model.
- **Secure aggregation** (Bonawitz et al. protocol) before server sees updates.
- Differential privacy noise (ε=3) added at aggregation.
- Monthly global update pushed back to devices.

This is **not** shipped v1.0 — it's a Y2 privacy-moat deliverable.

---

## 13. Cross-Vertical Model

A flagship differentiator: patterns learned on alcohol users generalize to cannabis users because the underlying urge→intervention→outcome dynamics share physiology.

**Implementation:**
- Feature encoder shared across verticals.
- Vertical-specific heads fine-tuned on per-vertical labels.
- Transfer-learning eval: adding a new vertical cold-starts at ≥80% of mature vertical performance within 4 weeks.

Methodology paper published externally on this — a public-research moat.

---

## 14. Experimentation

- A/B infrastructure: GrowthBook or in-house.
- Unit of randomization: `user_id` (sticky bucket).
- **Clinical A/B guardrails:**
  - No experiment ever varies T3/T4 behavior.
  - Experiments touching messaging around relapse require clinical advisor sign-off.
  - Every clinical-adjacent experiment is pre-registered with hypothesis, metric, decision rule.
  - Experiments monitored daily for harm indicators: relapse rate increase, journal safety-flag rate, churn in vulnerable cohorts.

---

## 15. Explainability

User-facing:
- Pattern cards show "based on 6 Fridays in the last 4 weeks" — never a model confidence number.
- Intervention recommendation shows the human rationale, not the bandit arm id.

Internal/compliance-facing:
- SHAP values logged for state classifier and urge predictor per prediction (for clinical audit).
- Bandit arm choice logged with context vector + Thompson sample.

---

## 16. Bias & Fairness

Monitored monthly:
- State classifier accuracy by demographic subgroups (age, gender, device type proxies).
- Bandit arm distribution by subgroup — no tool variant should be systematically deprived from any group.
- Safety classifier recall by demographic — no group should have worse recall.

Intervention if any subgroup gap > 5% on accuracy or > 10% on bandit arm distribution.

---

## 17. Shadow Mode & Canary

Every new model trained:
1. **Shadow mode**: runs in parallel with production, outputs logged, no user impact. 14 days minimum.
2. **Canary**: 1% of users, 72 hours. SLO gates: latency, memory, crash rate, outcome signal.
3. **10% rollout**: 72 hours, same gates + engagement signal.
4. **100% rollout**: after clean canary window.

Automated rollback on:
- Latency regression >15%
- Memory regression >10%
- Crash rate >1.5× baseline
- Outcome regression (handled rate down >3% at significance)

---

## 18. Model Governance

- All models registered in internal MLOps registry.
- Each model carries a "model card": intended use, training data, metrics, limitations, last review date.
- Clinical + safety-adjacent models require quarterly re-review.
- Model deprecation policy: 90-day shadow period before removal.
