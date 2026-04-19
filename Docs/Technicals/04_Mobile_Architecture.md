# Mobile Architecture — Discipline OS

## 1. Platform Targets

| Platform | Minimum version | Rationale |
|----------|-----------------|-----------|
| iOS | 17.0 | HealthKit deep features, Live Activities, CoreML stable |
| iPadOS | 17.0 | Secondary surface |
| watchOS | 10.0 | Complication, HRV, DigitalCrown input |
| Android | API 31 (Android 12) | Health Connect, LiteRT, BiometricPrompt v2 |
| Wear OS | 4.0 | Complication, Tiles |

## 2. Framework Choice

**React Native 0.76 with New Architecture (Fabric + TurboModules) on by default, Hermes engine, plus Swift and Kotlin native modules where necessary.**

Rationale:
- **Shared UI across iOS + Android** is essential — we ship a closed-loop behavior change product that must feel identical. Parity bugs between two native codebases are lethal in crisis flows.
- **React Native's New Architecture** closes the historical perf gap. Fabric gives synchronous layout, TurboModules remove bridge overhead.
- **Native modules** handle HealthKit, CoreML, HomeKit, Watch, Widgets, app-lock, background tasks — areas where RN abstraction is either incomplete or imposes unacceptable latency.
- **Hermes** precompiled bytecode gives sub-second cold-start on T3 path.

Rejected alternatives: Flutter (watchOS story weak, HealthKit coverage immature), native-only (double cost, parity risk), Capacitor/PWA (latency fatal for T3).

---

## 3. Top-Level Module Layout

```
apps/mobile/
├── src/
│   ├── app/                    # Root app, providers, routing
│   ├── screens/                # Feature screens (check_in, urge_log, crisis, patterns, ...)
│   ├── features/
│   │   ├── intervention/
│   │   ├── signal/
│   │   ├── memory/             # Journals, voice
│   │   ├── resilience/         # Streaks, state
│   │   ├── pattern/
│   │   └── identity/
│   ├── components/             # Design system primitives
│   ├── core/
│   │   ├── api/                # REST + WS clients
│   │   ├── store/              # Zustand + MMKV persistence
│   │   ├── crypto/
│   │   ├── telemetry/
│   │   └── offline/            # SQLite queue
│   ├── native/                 # TypeScript TurboModule specs
│   └── theme/
├── ios/
│   ├── DisciplineOS/
│   ├── DisciplineSignals/      # Swift package: HealthKit, CoreML
│   ├── DisciplineCrisis/       # Swift package: crisis UI + Live Activity
│   ├── DisciplineWidget/       # Widget extension
│   ├── DisciplineWatch/        # watchOS target
│   └── DisciplineShieldExt/    # Screen Time Shield extension (optional)
├── android/
│   ├── app/
│   ├── signals/                # Kotlin: Health Connect, LiteRT
│   ├── crisis/                 # Kotlin: crisis Activity
│   ├── wear/
│   └── widget/
└── shared-rules/               # JSON: T3 deterministic scripts
```

---

## 4. State Management

**Zustand stores** organized by feature, persisted via MMKV (sync, encrypted) for hot state:

| Store | Shape | Persistence |
|-------|-------|-------------|
| `useIdentity` | user, session, device | MMKV |
| `useResilience` | continuous + resilience streaks, today's state | MMKV |
| `useIntervention` | active intervention, queued nudges | Memory + MMKV snapshot |
| `useSignals` | recent windows, state estimate | Memory only |
| `useJournal` | drafts, recent entries | MMKV |
| `usePatterns` | active patterns, dismissed set | MMKV |
| `useTelemetry` | buffered events, failure queue | MMKV |

Rejected: Redux Toolkit (too much boilerplate), Jotai (team unfamiliar), MobX (reactivity debugging is painful).

### 4.1 Offline mutation queue

SQLite (via op-sqlite for sync perf) stores queued mutations:

```ts
interface QueuedOp {
  id: string;
  kind: 'urge_create' | 'outcome_record' | 'journal_write' | 'signal_upload';
  payload: object;
  created_at: string;
  attempts: number;
  last_error?: string;
}
```

Workers flush every 30s and on app foreground. Max retry 10 with exponential backoff. Capacity 10,000 ops.

---

## 5. Networking

### 5.1 REST client

- `tanstack-query` for cache + invalidation.
- `ky` under the hood.
- Interceptor attaches `X-Request-ID`, session token, client version.
- Automatic retry on 5xx with exponential backoff, **except T3 endpoints** which fail fast to deterministic fallback.

### 5.2 WebSocket

- `reconnecting-websocket` with jittered backoff.
- Heartbeat every 25s, reconnect on 3 missed.
- Unified message dispatcher pushes to Zustand store reducers.

### 5.3 Crisis path (T3) — fast lane

A separate `crisisClient` bypasses query cache:

```ts
async function triggerSOS(localSignal: UrgeInput) {
  // 1. Optimistically render crisis UI from cached template
  crisisUI.render(prebakedTemplate);
  
  // 2. Fire-and-forget network call with 600ms timeout
  crisisClient.postSOS(localSignal, { timeout: 600 }).catch(noop);
  
  // 3. Start local tool immediately, no await on network
  startUrgeSurf();
}
```

The T3 SLO is **<200ms from tap to first-frame** on warm app; network success is a nice-to-have, not a requirement.

---

## 6. Native Modules

### 6.1 iOS — `DisciplineSignals`

Swift package with TurboModule bridge. Responsibilities:

- HealthKit subscription to heart rate, HRV (RMSSD), respiratory rate, step count, sleep analysis.
- Aggregates raw samples into 60s windows on-device — raw samples never exit.
- Runs CoreML state classifier (quantized, ~400KB model).
- Writes aggregates to local SQLite.

```swift
@objc(DisciplineSignals)
final class DisciplineSignals: NSObject, RCTBridgeModule {
  @objc func startBackgroundObservers(_ resolve: @escaping RCTPromiseResolveBlock,
                                      reject: @escaping RCTPromiseRejectBlock) { ... }
  @objc func currentStateEstimate(_ resolve: ...) { /* returns label + confidence */ }
  @objc func evictRawSamplesOlderThan(_ minutes: NSNumber) { ... }
}
```

### 6.2 iOS — `DisciplineCrisis`

Dedicated Swift module for T3/T4 flow so it loads independently of main JS bundle:

- Pre-cached SwiftUI views for crisis flow.
- Native haptic + audio fallback.
- Live Activity (Dynamic Island) integration for in-flight urge timer.
- Can be launched directly from control-center quick action, Siri shortcut, or widget.

### 6.3 iOS — Widget + Lock Screen

- State "weather" widget: calm / elevated / pre-urge (never labels "urge" to avoid outing).
- Quick-action: tap-to-check-in, tap-to-log-urge, tap-to-SOS.
- Lock-screen complication for watch users.

### 6.4 Android — `disciplinesignals` (Kotlin)

- Health Connect read permissions (subset of HealthKit equivalent).
- Background service with foreground notification during elevated states.
- LiteRT (TensorFlow Lite successor) runs state classifier.
- Room DB for local windows.

### 6.5 Android — crisis path

- Standalone `CrisisActivity` started via notification action or homescreen shortcut.
- FLAG_KEEP_SCREEN_ON, FLAG_SHOW_WHEN_LOCKED for immediate availability.
- BiometricPrompt for app-lock bypass in authorized crisis flow (configurable).

---

## 7. On-Device ML

### 7.1 Models shipped with app

| Model | Size | Input | Output | Cadence |
|-------|------|-------|--------|---------|
| State classifier | ~400KB quantized | 30-min signal window | label + confidence | Every 60s while awake, every 5min background |
| Urge predictor (LSTM) | ~2.5MB quantized | 48h feature sequence | risk score (0-1), horizon (0-120min) | Every 5min |
| Intervention scorer (bandit) | ~150KB | state + context | top-K tools | On urge trigger |
| Prosody mood | ~1.8MB | 5s audio chunks | arousal, valence | Voice sessions only |

### 7.2 Update mechanism

- Models signed by server, verified on download.
- OTA via CloudFront. Rollout gated 1% → 10% → 100% with canary monitoring.
- Model version pinned with app version; rollbacks possible.
- A/B testing controlled per-user via server flag.

### 7.3 Privacy constraints

- Raw biometric samples never leave device.
- Only derived state estimates + handled outcomes are uploaded.
- Federated learning eligible users opt-in; gradient aggregation via secure aggregation protocol.

---

## 8. Storage

### 8.1 Layers

| Layer | Tech | Use |
|-------|------|-----|
| Settings | MMKV (encrypted) | User prefs, flags |
| State | MMKV + Zustand persist | Hot app state |
| Structured | SQLite (op-sqlite) | Signal windows, mutation queue, cached events |
| Large blobs | FS (NSFileProtectionComplete iOS, EncryptedFile Android) | Voice blobs pre-upload |
| Secrets | Keychain / Keystore | Server tokens, encryption DEKs |

### 8.2 Encryption on device

- File-level: platform file protection (Complete or CompleteUnlessOpen).
- Column-level for journals: AES-256-GCM with Keychain-backed key.
- App-lock: biometric gate that wipes in-memory keys; reopening requires reauth.

### 8.3 Quick-erase

Single call wipes:
1. MMKV namespaces (overwrite then delete).
2. SQLite files (overwrite first 1MB, delete).
3. Keychain/Keystore entries for this app.
4. HealthKit historical samples (iOS only if user consents to extended erase).
5. Server-side erase request queued (best-effort; completes within 10 min).
6. App signs out and exits.

---

## 9. Navigation

- **`react-navigation/native` v7** with native stack per platform.
- Route structure kept flat for T3 — crisis screen is root-level, not nested.
- Deep links:
  - `disciplineos://urge/new`
  - `disciplineos://sos`
  - `disciplineos://intervention/{id}`
  - `disciplineos://relapse/review/{id}`
  - `disciplineos://journal/new`

Crisis deep link bypasses auth gate (crisis is for users in trouble, some of whom may struggle to log in).

---

## 10. Design System

- Primitive components wrap react-native-gesture-handler and Reanimated v3.
- Tokens fed from the shared design-tokens package (`theme/tokens.ts`).
- Typography, color, spacing, elevation, motion tokens — all exported for both iOS and Android SwiftUI/Compose companions.
- Accessibility:
  - Dynamic Type / fontScale honored.
  - VoiceOver / TalkBack labels on every actionable element.
  - Minimum 4.5:1 contrast (AA).
  - Haptic equivalents to every audio cue.

---

## 11. Accessibility & Crisis-State UX

Unique rules for crisis flows:
- Text ≥20pt in crisis flow, regardless of user font pref.
- Buttons ≥64pt tap target.
- No destructive actions reachable within 2 taps of crisis screen.
- No confirmation dialogs on primary crisis actions (friction = failure).
- Calm-palette only, no red alerts.
- Haptic on every state transition.

---

## 12. Background Processing

### 12.1 iOS

- `BGProcessingTask` for nightly signal aggregation + model refresh.
- `BGAppRefreshTask` for every 15-20min state estimate check.
- Live Activities for in-flight urge sessions.
- HKHealthStore background delivery for HRV anomalies.

### 12.2 Android

- `WorkManager` periodic + one-time workers.
- Foreground service only during elevated state (user-visible justification).
- Health Connect passive callbacks.

### 12.3 Battery budget

- Target <3% daily battery for normal use, <6% during active urges.
- Observed via Battery telemetry on internal builds.
- CI fails if synthetic day exceeds budget.

---

## 13. Notifications

- iOS: Notification Service Extension decorates T1/T2 payloads (e.g., inline tool suggestion).
- Category-based actions:
  - `NUDGE_T1`: accept / snooze / dismiss
  - `URGE_T2`: open / sos
  - `SOS_T3`: open (priority, critical alert opt-in required)
- Critical alert entitlement requested only for T3 if user has clinician-supervised enterprise account.

---

## 14. Feature Flags

`configcat` or self-hosted equivalent; flags fetched on app launch, cached for 24h, with server-push invalidation via WS. All crisis behavior is **not** feature-flagged — always-on by design.

---

## 15. Testing

- **Unit:** Jest for pure logic.
- **Component:** React Native Testing Library.
- **E2E:** Detox (iOS + Android) for golden flows — onboarding, urge log, SOS, relapse review.
- **Perf:** `react-native-performance` + custom frame-timing for T3 flows.
- **Device farm:** Firebase Test Lab (Android) + BrowserStack App Live (iOS) for real-device matrix.
- **Regression:** 
  - Crisis flow E2E runs on every PR.
  - Latency budget asserted in CI (T3 < 200ms synthetic warm, < 800ms cold).

---

## 16. Build & Release

- **EAS Build** (Expo Application Services) for standard RN apps; **Fastlane** lanes for native module updates.
- Dual release train: stable (weekly) + beta (daily).
- Code push via Expo Updates for JS-only fixes **except** crisis flow (crisis is bundle-locked to platform-installed version for safety).
- Release gates enforced in CI: latency SLO, crash-free sessions >99.8%, unit coverage >80% for `features/intervention`.

---

## 17. Observability

- Crashlytics + Sentry for fatal + non-fatal errors.
- OpenTelemetry spans emitted for every user-visible operation.
- Battery, network, memory sampled and shipped as metrics.
- Per-screen "time to interactive" tracked.

---

## 18. Security

- Certificate pinning (native, SSL-kill-switch on build type).
- Root/jailbreak detection — warn, do not block (users in trouble shouldn't be locked out).
- App-lock: biometric with configurable grace period, pin fallback.
- Alt-app-icon (Settings → Privacy) for privacy-sensitive users.
- Screen-capture suppression on journals and crisis screens (iOS `isScreenCaptured` check, Android `FLAG_SECURE`).

---

## 19. Internationalization

**Launch locales (v1): `en`, `fr`, `ar`, `fa` (Arabic and Persian are right-to-left).** Full architecture: [15_Internationalization](15_Internationalization.md).

### 19.1 RTL

- `I18nManager.isRTL` drives global layout mirroring. `I18nManager.forceRTL()` is called on first launch based on detected locale, and `react-native-restart` is used to apply the direction change without a logout.
- All flexbox layouts use `start`/`end`, never `left`/`right`. Lint rule `no-physical-direction` blocks physical-direction properties in new code.
- Directional icons (back arrow, progress chevron) pass through a `mirror-on-rtl` helper; neutral icons (heart, moon) are not mirrored.
- Swipe-to-dismiss and back gestures reverse in RTL. Detox golden flows are run in both LTR and RTL.
- Trajectory chart x-axis mirrors in RTL; bar chart categorical axes mirror; y-axis (up = more) does not mirror.

### 19.2 Typography

| Script | Primary font | Fallback |
|---|---|---|
| Latin | Inter v4 | system-ui |
| Arabic | IBM Plex Sans Arabic | Noto Sans Arabic |
| Persian | Vazirmatn v33 | IBM Plex Sans Arabic |

Arabic and Persian body copy is sized 1.15× the Latin equivalent with line-height 1.6 (vs 1.5 for Latin). These overrides are part of the theme token bundle that's swapped per-locale.

### 19.3 Digits

- Latin 0–9 always for clinical scores (PHQ-9, GAD-7, etc.) regardless of locale. Clinical export interoperability requires this.
- Arabic-Indic (٠–٩) in `ar`, Persian (۰–۹) in `fa` for user-facing dates, durations, non-clinical counts — when `digit_preference` = `auto`.
- Users can override with `digit_preference = latin` in Settings.

### 19.4 Calendars

- Gregorian default for all locales.
- Secondary Hijri (Islamic) annotation available in `ar` Settings.
- Secondary Shamsi/Jalali annotation available in `fa` Settings.
- Internal storage always Gregorian UTC.

### 19.5 Translation workflow

- String catalog via `i18next` + `i18next-icu` with ICU MessageFormat; XLIFF at rest, compiled per platform at build.
- **Arabic 6 plural categories** (zero/one/two/few/many/other) are enforced — missing branches fail CI.
- **Machine translation is prohibited** for shipped content. LLM drafts are allowed internally only as translator-aid; a human clinical translator signs off on safety-critical and clinical-framing copy per locale.

### 19.6 Safety content per locale

- Crisis (T3) content is bundled per locale on-device. No runtime translation call on the crisis path.
- The hotline directory per-locale is loaded at app start; a missing directory for the detected country + locale falls back to English + the 988 Lifeline if US, or surfaces a "please add a local contact" prompt otherwise — with the failure logged to `safety.log`.
- A locale does not ship until all safety-critical copy has been clinically reviewed and signed off (see [15_Internationalization](15_Internationalization.md) §9.1).

### 19.7 Psychometric instrument coverage per locale

Not every instrument has a validated translation in every locale. The scheduler consults `psychometric_instruments` rows for the user's locale and skips instruments without a validated translation. Coverage matrix: [15_Internationalization](15_Internationalization.md) §8.1.

---

## 20. Mobile-specific SLOs

| Metric | Target |
|--------|--------|
| Cold start (T3 entry) | <800ms |
| Warm entry to crisis UI | <200ms |
| Urge log submit (online) | <500ms |
| Background signal aggregation cycle | <15s |
| Crash-free sessions | >99.8% |
| p95 frame time on dashboard | <16ms (60fps) |
| Voice session start to recording | <500ms |
