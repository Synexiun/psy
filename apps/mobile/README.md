# Mobile — Discipline OS

React Native app (iOS + Android + watchOS/Wear OS) that delivers the closed-loop intervention experience.

## Stack

See `Docs/Technicals/04_Mobile_Architecture.md` for the full picture. Headlines:

- **React Native 0.76** with New Architecture (Fabric + TurboModules) on by default, Hermes.
- **Expo SDK 52+** managed workflow with prebuild for native module integration.
- **State:** Zustand + MMKV persistence.
- **Networking:** tanstack-query + reconnecting-websocket.
- **Navigation:** react-navigation v7 native stack.
- **Native modules (to be built):**
  - `DisciplineSignals` — Swift/Kotlin, HealthKit/Health Connect + state classifier inference.
  - `DisciplineCrisis` — separate module for T3 path, loads independently of JS bundle.
  - `DisciplineWatch` — watchOS complication + quick actions.
  - `DisciplineWidget` — iOS widget + Android widget.

## Source layout (target)

```
src/
├── app/                    App root, providers, routing
├── screens/                Feature screens
├── features/
│   ├── intervention/
│   ├── signal/
│   ├── memory/             Journals, voice
│   ├── resilience/         Streaks, state
│   ├── pattern/
│   └── identity/
├── components/             Design system primitives
├── core/
│   ├── api/
│   ├── store/
│   ├── crypto/
│   ├── telemetry/
│   └── offline/
├── native/                 TurboModule TS specs
└── theme/
```

## Phase 0 target (Months 0–3)

Minimal staff-only app:
- Clerk sign-in (passkey).
- HealthKit read permission + aggregation into 60s windows on-device.
- Manual check-in UI (morning + evening).
- Manual urge-log UI (no bandit yet — tool library is hardcoded).
- Journal entry (text only; voice deferred to Phase 1).
- SOS screen with deterministic crisis template.
- No backend sync at first — local SQLite only.

## Bootstrapping (to run)

This directory is currently a spec. To initialize:

```bash
cd apps/mobile

# Generate the Expo app — will populate ios/, android/, app.json, etc.
pnpm dlx create-expo-app@latest . --template blank-typescript

# Install project deps listed in package.json
pnpm install

# Generate native projects
pnpm exec expo prebuild --clean

# Run
pnpm exec expo run:ios
# or
pnpm exec expo run:android
```

After initialization, the `src/` structure above should be created and the scaffolded `App.tsx` replaced with the providers + router in `src/app/`.

## Conventions

- **No `any`.** TypeScript strict mode. `any` is a lint error.
- **No inline styles for anything but one-off debugging.** Use the design tokens in `src/theme/`.
- **No direct `fetch` calls.** Always go through `src/core/api/`.
- **Every feature folder owns its types.** Cross-feature types live in `src/core/types/`.
- **Tests co-located:** `feature.test.ts` next to `feature.ts`.

## Performance budgets (enforced in CI)

- Cold start to first-frame (T3 path): **<800ms**
- Warm entry to crisis UI: **<200ms**
- Dashboard p95 frame time: **<16ms (60fps)**
- Crash-free sessions: **>99.8%**
- Bundle size: **<25MB installed** (excluding on-device ML models)

## Testing

- **Unit:** Jest.
- **Component:** React Native Testing Library.
- **E2E:** Detox (iOS + Android) for 20 golden flows — see `Docs/Technicals/09_Testing_QA.md` §6.
