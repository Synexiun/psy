# Web App Frontend "Quiet Strength" Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `apps/web-app` from a generic blue/light functional surface into the "Quiet Strength" branded clinical-grade UX defined in the design spec — 11 v1 screens, 28 new + 11 refreshed primitives, dark default + light opt-in, en+ar+fa locales day one, all clinical contracts (CLAUDE.md Rules 1–12) enforced at code level.

**Architecture:** Three-tier component split (`packages/design-system/src/{primitives,clinical,motion}/`), per-locale font loading in `apps/web-app/src/app/[locale]/layout.tsx`, Tailwind v4 `@theme` for tokens, custom ESLint plugin (`tools/eslint-plugin-discipline/`) for clinical-rule enforcement, Workbox-driven service worker for offline check-in queue + crisis precache, Storybook + Chromatic for the design-system review surface.

**Tech Stack:** Next.js 15 (App Router, Server Components) · React 19 · Tailwind v4 (`@theme`) · next-intl 3.22 · Clerk v6 · TanStack Query 5 · Zustand 5 · Zod 3 · Radix Primitives · Visx (charts) · Workbox (SW) · `next-themes` (theme bootstrap) · Storybook 8 + Chromatic · Vitest + Playwright + axe-core.

**Spec:** `docs/superpowers/specs/2026-04-26-web-app-frontend-design.md` (read this before starting any chunk; the plan implements the spec, it does not re-define it).

**Source-of-truth precedence:** spec § references win when this plan and the spec diverge. CLAUDE.md Rules 1–12 win over both. If you spot a contradiction, fix the plan/spec — do not invent.

---

## How to read this plan

1. **Phase 0 (Chunks 1–3)** is bite-sized, step-by-step TDD. Execute as written. No interpretation needed.
2. **Phases 1–2 (Chunks 4–5)** are task-level with key steps named. The engineer breaks each task into 2–5 min steps as they pick it up.
3. **Phases 3–7 (Chunks 6–8)** are task definitions with files + acceptance criteria. Re-plan to step granularity at each phase boundary with current context (the screens depend on primitives that ship in the prior phase, so step-level decisions are best made when the dependencies exist).
4. **Frequent commits.** One commit per task minimum; one commit per logical step inside Phase 0.
5. **TDD discipline.** Test-first for every component, every helper, every clinical contract. The clinical contracts are the entire point — they cannot be retrofitted.
6. **DRY/YAGNI.** If two screens want the same chip, it goes in `primitives/`. If a component is built "for v1.1 too," cut it.

---

## File Structure

This is the **target** layout after the plan completes. Existing files marked `(M)`; new files marked `(C)`.

### `apps/web-app/`

```
apps/web-app/
  .storybook/                                  (C) Storybook config
    main.ts
    preview.tsx
    chromatic.config.json
  eslint.config.mjs                            (M) add custom rules
  next.config.mjs                              (M) bundle analyzer flag, headers
  package.json                                 (M) Storybook + Visx + Workbox + axe + next-themes deps
  playwright.config.ts                         (M) more projects (locales × themes)
  postcss.config.mjs                           (existing, unchanged)
  vitest.config.ts                             (M) coverage thresholds, paths
  public/
    sw.js                                      (C) Workbox-generated service worker
    fonts/                                     (existing)
  src/
    app/
      globals.css                              (M) full token refresh (~250 lines)
      layout.tsx                               (M) root: ThemeProvider from next-themes, font CSS vars
      [locale]/
        layout.tsx                             (M) locale font loader + dir attribute
        page.tsx                               (M) Dashboard
        loading.tsx                            (M) skeleton
        error.tsx                              (M) error boundary on token system
        not-found.tsx                          (M)
        check-in/page.tsx                      (M)
        tools/page.tsx                         (M)
        tools/[slug]/page.tsx                  (C) tool detail
        journal/page.tsx                       (M)
        journal/new/page.tsx                   (M)
        journal/[id]/page.tsx                  (C) entry detail
        library/page.tsx                       (C) library landing
        library/[category]/page.tsx            (C)
        library/[category]/[slug]/page.tsx     (C) article
        reports/page.tsx                       (C) reports landing
        reports/[period]/page.tsx              (C)
        patterns/page.tsx                      (C) patterns landing
        patterns/[id]/page.tsx                 (C) pattern detail
        assessments/page.tsx                   (M)
        assessments/[instrument]/page.tsx      (M)
        assessments/history/[id]/page.tsx      (C)
        companion/page.tsx                     (C) NO LLM imports here
        settings/page.tsx                      (M)
        settings/account/page.tsx              (M)
        settings/notifications/page.tsx        (C)
        settings/privacy/page.tsx              (M)
        settings/appearance/page.tsx           (C)
        crisis/page.tsx                        (M-or-C) Server Component, no LLM
    components/
      Providers.tsx                            (M) ThemeProvider added (from next-themes)
      Layout.tsx                               (M) refactored to use new shell
      TopBar.tsx                               (C) bell + locale + theme + avatar
      SidebarNav.tsx                           (M) refresh (Lucide + custom icons)
      BottomNav.tsx                            (M) refresh
      ThemeToggle.tsx                          (C)
      LocaleSwitcher.tsx                       (C)
      NotificationsDrawer.tsx                  (C) bell-triggered Sheet
      OfflineIndicator.tsx                     (C) TopBar badge
      WordmarkSvg.tsx                          (C) brand wordmark
      MoodSparkline.tsx                        (M) consume new Sparkline
      PatternCard.tsx                          (M) becomes thin Dashboard preview
      QuickActions.tsx                         (M) bronze CTA refresh
      StateIndicator.tsx                       (M) raw signal interpretation
      StreakWidget.tsx                         (M) ResilienceRing-backed
      primitives.tsx                           (DELETE) replaced by design-system
    hooks/
      useDashboardData.ts                      (M)
      useReducedMotion.ts                      (C)
      useStubs.ts                              (C)
      useOfflineQueue.ts                       (C)
      useNotifications.ts                      (C)
      useReports.ts                            (C)
      usePatterns.ts                           (C)
      useLibrary.ts                            (C)
      useCompanion.ts                          (C)
      useAuditPhi.ts                           (C) PHI-boundary client dispatch
    lib/
      api.ts                                   (M) ApiError + interceptor for X-Phi-Boundary
      query-client.ts                          (M) keys + retry policy
      clinical-mirrors.ts                      (C) estimateStateClientMirror
      sw-register.ts                           (C) register + lifecycle
      offline-queue.ts                         (C) IndexedDB-backed check-in queue
      safety/
        emergency-numbers.ts                   (C) frozen Record<CountryCode, …>
        directory-loader.ts                    (C) verifiedAt + 90d filter
      stubs/
        index.ts                               (C)
        check-in.ts                            (C)
        reports.ts                             (C)
        patterns.ts                            (C)
        library.ts                             (C)
        companion.ts                           (C)
        assessments.ts                         (C)
        notifications.ts                       (C)
    i18n/
      request.ts                               (existing, unchanged)
      routing.ts                               (existing, unchanged)
    middleware.ts                              (M) X-Phi-Boundary header on PHI routes
  tests/
    e2e/
      dashboard.spec.ts                        (M) selectors update for new shell
      check-in.spec.ts                         (M)
      assessments.spec.ts                      (M)
      crisis.spec.ts                           (M) JS-disabled assertion added
      journal.spec.ts                          (M)
      tools.spec.ts                            (M)
      reports.spec.ts                          (C)
      library.spec.ts                          (C)
      patterns.spec.ts                         (C)
      companion.spec.ts                        (C)
      offline-checkin.spec.ts                  (C)
      locale-clinical-numbers.spec.ts          (C) en/ar/fa: numbers always Latin
      theme-persist.spec.ts                    (C)
    a11y/
      every-screen.spec.ts                     (C) axe-core matrix
    unit/
      setup.ts                                 (M)
      components/                              (existing + many new)
      hooks/                                   (existing + many new)
      lib/                                     (existing + many new)
      pages/                                   (existing)
      assessments/                             (existing)
      i18n/                                    (existing)
      middleware-routes.test.ts                (M) X-Phi-Boundary header test
      clinical-contracts.test.ts               (C) cross-cutting Vitest gates
```

### `packages/design-system/`

```
packages/design-system/
  package.json                                 (M) Visx + Radix deps; remove web.tsx export
  src/
    index.ts                                   (M) re-export from new layout
    tokens.ts                                  (M) extended palette + typography scale + motion
    tokens.test.ts                             (M)
    primitives/
      index.ts                                 (C)
      Button.tsx                               (C) extracted from web.tsx
      Card.tsx                                 (C)
      Input.tsx                                (C)
      Textarea.tsx                             (C)
      Spinner.tsx                              (C)
      Divider.tsx                              (C)
      Badge.tsx                                (C)
      Skeleton.tsx                             (C)
      Tooltip.tsx                              (C) Radix Tooltip wrap
      ProgressRing.tsx                         (C)
      Sparkline.tsx                            (C) Visx-backed; same prop contract
      Slider.tsx                               (C) Radix Slider wrap
      RadioGroup.tsx                           (C) Radix
      CheckboxGroup.tsx                        (C)
      Switch.tsx                               (C) Radix
      Select.tsx                               (C) Radix
      TabNav.tsx                               (C) Radix Tabs
      Dialog.tsx                               (C) Radix Dialog
      Sheet.tsx                                (C) Radix Dialog (side variant)
      Toast.tsx                                (C) Radix Toast
      PageShell.tsx                            (C) layout shell
      WizardShell.tsx                          (C) multi-step shell
      Stat.tsx                                 (C)
      Trend.tsx                                (C) Stat + Sparkline
      RingChart.tsx                            (C)
      BarChart.tsx                             (C) Visx
      Banner.tsx                               (C)
      EmptyState.tsx                           (C)
      __stories__/                             (C) one *.stories.tsx per primitive
      __tests__/                               (C) one *.test.tsx per primitive
      web.tsx                                  (DELETE) replaced by per-component files
      web.test.ts                              (DELETE) replaced by __tests__/
    clinical/
      index.ts                                 (C)
      ResilienceRing.tsx                       (C)
      UrgeSlider.tsx                           (C)
      SeverityBand.tsx                         (C)
      RCIDelta.tsx                             (C)
      CompassionTemplate.tsx                   (C)
      CrisisCard.tsx                           (C)
      InsightCard.tsx                          (C)
      formatters.ts                            (C) formatNumberClinical re-export
      __stories__/                             (C)
      __tests__/                               (C)
    motion/
      index.ts                                 (C)
      BreathingPulse.tsx                       (C)
      __stories__/                             (C)
      __tests__/                               (C)
```

### `tools/eslint-plugin-discipline/` (new package — repo root)

```
tools/eslint-plugin-discipline/
  package.json                                 (C)
  tsconfig.json                                (C)
  src/
    index.ts                                   (C) plugin entry
    rules/
      no-physical-tailwind-properties.ts       (C)
      clinical-numbers-must-format.ts          (C)
      no-llm-on-crisis-route.ts                (C)
    clinical-numbers.ts                        (C) regex source-of-truth
  tests/
    no-physical-tailwind-properties.test.ts    (C)
    clinical-numbers-must-format.test.ts       (C)
    no-llm-on-crisis-route.test.ts             (C)
```

### Other touched paths

```
packages/i18n-catalog/src/catalogs/
  en.json                                      (M) keys for new screens
  fr.json                                      (M) draft status keys
  ar.json                                      (M) draft status keys
  fa.json                                      (M) draft status keys
packages/safety-directory/src/hotlines.json    (existing — referenced, not modified by this plan)
services/api/data/safety/hotlines.json         (existing — mirror, not modified)
shared-rules/relapse_templates.json            (PRECONDITION — must exist before Chunk 5)
services/api/src/discipline/clinical/...       (PRECONDITION — backend module must exist before Chunk 5)
```

**Backend preconditions before Chunk 5 (Phase 2 clinical primitives):**
- `shared-rules/relapse_templates.json` exists with the schema CompassionTemplate consumes (id, locale, body, axis-soft hint).
- `discipline/clinical/` Python module exposes a deterministic-selection function that returns a template id given user state. Exact filename TBD by backend; the React component depends only on the API response shape (`{template_id, body, soft_hint}`).
- `services/api/src/discipline/safety/emergency_numbers.py` exists (mirror of `apps/web-app/src/lib/safety/emergency-numbers.ts`).

If any precondition is missing when Chunk 5 starts, **stop and surface to the user**. Do not invent the backend.

---

## Quick reference: clinical-rule → enforcement mapping

For every code change, ask: "Which CLAUDE.md rule does this touch?" If you cannot answer, you do not understand the change.

| Rule | What | Where it's enforced in this plan |
|------|------|----------------------------------|
| 1 — Crisis deterministic | `/crisis` route | Chunk 2 ESLint `no-llm-on-crisis-route`; Chunk 6 Crisis screen Server Component; Chunk 8 SW precache |
| 2 — Raw biometrics local | (out of frontend scope; flag if you find a violation) | Code review |
| 3 — Resilience monotonic | ResilienceRing day count | Chunk 5 Vitest gate `dashboard_resilienceRing_value_never_decrements_across_renders` |
| 4 — Compassion-first relapse | Companion + relapse copy | Chunk 5 CompassionTemplate (deterministic, no interpolation); Chunk 7 Companion route; Chunk 2 ESLint extension covers companion route |
| 5 — No advertising SDKs | All deps | Phase 0 dependency review at every package.json edit |
| 6 — Audit append-only | PHI routes | Chunk 6 middleware + `useAuditPhi` hook + Vitest gate `phi_routes_emit_boundary_header` |
| 7 — Voice 72h hard delete | (backend; not in frontend scope) | Code review |
| 8 — No MT clinical content | i18n catalog draft fallback | Chunk 6 next-intl override + `pnpm i18n:status` CI gate |
| 9 — Latin digits clinical | All clinical numbers | Chunk 1 `.clinical-number` CSS class; Chunk 2 ESLint `clinical-numbers-must-format`; Chunk 5 `formatNumberClinical` use in every clinical primitive |
| 10 — Safety directory 90d | CrisisCard render | Chunk 5 CrisisCard render-time freshness check |
| 11 — PHI boundary header | PHI routes | Chunk 6 middleware sets header + client interceptor dispatches audit + Vitest gate |
| 12 — Edit over Write | All file changes | Engineer discipline; this plan prefers `(M)` over `(C)` where possible |

---

## Pre-flight checks (run once before Chunk 1)

- [ ] **Confirm working tree is clean** on `main`:
  ```bash
  git -C D:/Psycho status --short
  ```
  Expected: empty output OR only the previously-staged `services/api/tests/check_in/test_check_in_helpers.py` (tangential prior work — leave it alone; it is not part of this plan).
- [ ] **Pull latest:**
  ```bash
  git -C D:/Psycho pull --rebase
  ```
- [ ] **Install deps from clean state:**
  ```bash
  cd D:/Psycho && pnpm install --frozen-lockfile
  ```
- [ ] **Verify the four packages exist:**
  ```bash
  ls D:/Psycho/packages/{api-client,design-system,i18n-catalog,safety-directory}
  ```
- [ ] **Verify the design spec is committed:**
  ```bash
  git -C D:/Psycho log --oneline -- docs/superpowers/specs/2026-04-26-web-app-frontend-design.md
  ```
  Expected: at least the three commits `b0f5f8e`, `5790481`, `97ef5f0`.
- [ ] **Run the existing test suite as a baseline:**
  ```bash
  cd D:/Psycho/apps/web-app && pnpm test && pnpm test:e2e
  ```
  Expected: green. If red on `main`, fix the failing tests in a separate commit before starting Phase 0 — do not begin work on a broken baseline.

---

## Chunk 1: Phase 0a — Token system + theme + fonts

**Phase 0 = Foundation. This chunk re-themes the existing app onto the "Quiet Strength" token system without changing any IA. After this chunk lands, the existing 6 screens look brand-correct in dark + light modes; no new screens, no new primitives.**

**Time estimate:** 2–3 days.

**Acceptance for this chunk:**
- `globals.css` has the full dark + light token set + `.clinical-number` utility
- `apps/web-app/src/app/[locale]/layout.tsx` loads Inter + Fraunces unconditionally; Vazirmatn only when `locale === 'fa'`; IBM Plex Sans Arabic font stack via CSS for `ar`
- `next-themes` ThemeProvider mounted in root layout; default = `system` with explicit `dark` fallback; persistence via localStorage; future-flag for Clerk `unsafeMetadata` mirror (defer the actual write to Phase 6)
- The existing dashboard, check-in, tools, journal, assessments, settings render against the new tokens with no visible regression beyond color refresh
- Vitest unit tests for `useTheme` consumer + `useReducedMotion` pass
- `tokens.ts` in design-system updated to mirror the CSS variables (single source of truth at the CSS layer; `tokens.ts` exports the names for consumers)

---

### Task 1.1: Token-system CSS in `globals.css`

**Files:**
- Modify: `apps/web-app/src/app/globals.css` (currently 110 lines → ~250 lines)

- [ ] **Step 1: Read the current file** to see what tokens already exist.

  ```bash
  cat D:/Psycho/apps/web-app/src/app/globals.css
  ```

- [ ] **Step 2: Replace the body of `globals.css`** with the spec §3.1 + §3.2 + §3.3 token set, plus the `.clinical-number` utility from §7.2.

  Full content (overwrite — keep existing `@import "tailwindcss";` line if present at top):

  ```css
  @import "tailwindcss";

  @theme {
    /* Surfaces — dark (primary) */
    --color-surface-primary:   hsl(220 25% 8%);
    --color-surface-secondary: hsl(220 22% 11%);
    --color-surface-tertiary:  hsl(220 20% 14%);
    --color-surface-overlay:   hsl(220 25% 8% / 0.85);

    /* Ink */
    --color-ink-primary:    hsl(28 15% 94%);
    --color-ink-secondary:  hsl(28 10% 75%);
    --color-ink-tertiary:   hsl(28 8%  55%);
    --color-ink-quaternary: hsl(28 8%  35%);

    /* Accents */
    --color-accent-bronze:      hsl(28 65% 55%);
    --color-accent-bronze-soft: hsl(28 45% 35%);
    --color-accent-teal:        hsl(173 35% 45%);
    --color-accent-teal-soft:   hsl(173 25% 25%);

    /* Signals */
    --color-signal-stable:  hsl(173 45% 50%);
    --color-signal-warning: hsl(38 70% 55%);
    --color-signal-crisis:  hsl(355 65% 48%);

    /* Borders */
    --color-border-subtle:   hsl(220 15% 18%);
    --color-border-emphasis: hsl(220 15% 28%);

    /* Typography */
    --font-body:    'Inter', 'IBM Plex Sans Arabic', system-ui, sans-serif;
    --font-display: 'Fraunces', 'IBM Plex Sans Arabic', system-ui, serif;
    --font-fa:      'Vazirmatn', system-ui, sans-serif;

    --text-display-2xl: clamp(3rem, 6vw, 4.5rem);
    --text-display-xl:  clamp(2.25rem, 4vw, 3.5rem);
    --text-display-lg:  clamp(1.75rem, 3vw, 2.25rem);
    --text-display-md:  1.5rem;
    --text-body-lg:     1.125rem;
    --text-body-md:     1rem;
    --text-body-sm:     0.875rem;
    --text-body-xs:     0.75rem;

    /* Motion */
    --motion-instant:    75ms;
    --motion-fast:       150ms;
    --motion-base:       250ms;
    --motion-slow:       400ms;
    --motion-deliberate: 700ms;

    --ease-default:    cubic-bezier(0.4, 0, 0.2, 1);
    --ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
    --ease-accelerate: cubic-bezier(0.4, 0, 1, 1);
    --ease-organic:    cubic-bezier(0.5, 0.05, 0.2, 1);
  }

  :root {
    color-scheme: dark;
    background: var(--color-surface-primary);
    color: var(--color-ink-primary);
    font-family: var(--font-body);
    font-feature-settings: 'cv11', 'ss01';
  }

  [data-theme="light"] {
    color-scheme: light;
    --color-surface-primary:   hsl(28 15% 97%);
    --color-surface-secondary: hsl(28 12% 94%);
    --color-surface-tertiary:  hsl(28 10% 90%);
    --color-surface-overlay:   hsl(28 15% 97% / 0.92);
    --color-ink-primary:       hsl(220 25% 12%);
    --color-ink-secondary:     hsl(220 18% 32%);
    --color-ink-tertiary:      hsl(220 12% 50%);
    --color-ink-quaternary:    hsl(220 10% 65%);
    --color-accent-bronze:     hsl(28 70% 42%);    /* darker for AA on light */
    --color-accent-bronze-soft:hsl(28 55% 30%);
    --color-accent-teal:       hsl(173 45% 35%);
    --color-accent-teal-soft:  hsl(173 30% 25%);
    --color-signal-stable:     hsl(173 50% 35%);
    --color-signal-warning:    hsl(38 75% 42%);
    --color-signal-crisis:     hsl(355 70% 42%);
    --color-border-subtle:     hsl(28 10% 85%);
    --color-border-emphasis:   hsl(28 12% 75%);
  }

  [lang="fa"] {
    --font-body: var(--font-fa), system-ui, sans-serif;
  }

  /* Clinical-number utility — Rule #9 */
  .clinical-number {
    direction: ltr;
    unicode-bidi: embed;
    font-variant-numeric: tabular-nums;
    font-feature-settings: 'tnum';
  }

  /* Reduced-motion respect — engine-level */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }

  /* "Reduce ambient motion" Settings flag — applied via [data-ambient-motion="off"] on root */
  [data-ambient-motion="off"] .motion-ambient {
    animation: none !important;
  }
  ```

  Note the `next-themes` library uses `data-theme` on `<html>` by default, which matches our CSS attribute exactly.

- [ ] **Step 3: Run typecheck + lint to verify no token-name collisions:**

  ```bash
  cd D:/Psycho/apps/web-app && pnpm typecheck && pnpm lint
  ```
  Expected: pass.

- [ ] **Step 4: Run the existing test suite to verify no regression:**

  ```bash
  cd D:/Psycho/apps/web-app && pnpm test
  ```
  Expected: pass.

- [ ] **Step 5: Visual smoke** — start the dev server and confirm dark theme is in effect:

  ```bash
  cd D:/Psycho/apps/web-app && pnpm dev
  ```
  Open `http://localhost:3020` in a browser. Page should be midnight (`hsl(220 25% 8%)`) with warm-stone text. Stop the dev server with Ctrl-C.

- [ ] **Step 6: Commit:**

  ```bash
  git -C D:/Psycho add apps/web-app/src/app/globals.css
  git -C D:/Psycho commit -m "$(cat <<'EOF'
  feat(web-app): replace token system with Quiet Strength palette

  Implements design spec §3.1–§3.3:
  - Dark (primary) + light variants under [data-theme="light"]
  - Bronze + teal + oxblood accents
  - Inter body + Fraunces display + Vazirmatn (gated by [lang="fa"])
  - Motion + ease tokens incl. cubic-bezier(0.5, 0.05, 0.2, 1) organic
  - .clinical-number utility (Rule #9)
  - prefers-reduced-motion + [data-ambient-motion="off"] hooks

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 1.2: Mirror tokens in `packages/design-system/src/tokens.ts`

**Files:**
- Modify: `packages/design-system/src/tokens.ts`
- Modify: `packages/design-system/src/tokens.test.ts`

The CSS is the source of truth; `tokens.ts` exports the *names* so TypeScript consumers can reference them safely (e.g., `colors.accent.bronze` returns the string `"var(--color-accent-bronze)"`).

- [ ] **Step 1: Read the current tokens.ts** to see existing shape:

  ```bash
  cat D:/Psycho/packages/design-system/src/tokens.ts
  ```

- [ ] **Step 2: Write a failing test** in `tokens.test.ts` that asserts the shape:

  ```ts
  import { describe, expect, it } from 'vitest';
  import { colors, fonts, motion, easing, textScale } from './tokens';

  describe('design-system tokens', () => {
    it('exposes accent.bronze as a CSS var reference', () => {
      expect(colors.accent.bronze).toBe('var(--color-accent-bronze)');
    });
    it('exposes signal.crisis as a CSS var reference', () => {
      expect(colors.signal.crisis).toBe('var(--color-signal-crisis)');
    });
    it('exposes fonts.body, fonts.display, fonts.fa', () => {
      expect(fonts.body).toBe('var(--font-body)');
      expect(fonts.display).toBe('var(--font-display)');
      expect(fonts.fa).toBe('var(--font-fa)');
    });
    it('exposes the organic ease', () => {
      expect(easing.organic).toBe('var(--ease-organic)');
    });
    it('exposes 4 motion durations + the deliberate one', () => {
      expect(motion.instant).toBe('var(--motion-instant)');
      expect(motion.deliberate).toBe('var(--motion-deliberate)');
    });
    it('exposes the display 2xl text size', () => {
      expect(textScale.display['2xl']).toBe('var(--text-display-2xl)');
    });
  });
  ```

- [ ] **Step 3: Run the test to verify it fails:**

  ```bash
  cd D:/Psycho && pnpm --filter @disciplineos/design-system test -- tokens
  ```
  Expected: FAIL (the new shape doesn't exist yet).

- [ ] **Step 4: Replace `tokens.ts`** with the structure that satisfies the test, mirroring the CSS variable names exactly:

  ```ts
  export const colors = {
    surface: {
      primary:   'var(--color-surface-primary)',
      secondary: 'var(--color-surface-secondary)',
      tertiary:  'var(--color-surface-tertiary)',
      overlay:   'var(--color-surface-overlay)',
    },
    ink: {
      primary:    'var(--color-ink-primary)',
      secondary:  'var(--color-ink-secondary)',
      tertiary:   'var(--color-ink-tertiary)',
      quaternary: 'var(--color-ink-quaternary)',
    },
    accent: {
      bronze:     'var(--color-accent-bronze)',
      bronzeSoft: 'var(--color-accent-bronze-soft)',
      teal:       'var(--color-accent-teal)',
      tealSoft:   'var(--color-accent-teal-soft)',
    },
    signal: {
      stable:  'var(--color-signal-stable)',
      warning: 'var(--color-signal-warning)',
      crisis:  'var(--color-signal-crisis)',
    },
    border: {
      subtle:   'var(--color-border-subtle)',
      emphasis: 'var(--color-border-emphasis)',
    },
  } as const;

  export const fonts = {
    body:    'var(--font-body)',
    display: 'var(--font-display)',
    fa:      'var(--font-fa)',
  } as const;

  export const motion = {
    instant:    'var(--motion-instant)',
    fast:       'var(--motion-fast)',
    base:       'var(--motion-base)',
    slow:       'var(--motion-slow)',
    deliberate: 'var(--motion-deliberate)',
  } as const;

  export const easing = {
    default:    'var(--ease-default)',
    decelerate: 'var(--ease-decelerate)',
    accelerate: 'var(--ease-accelerate)',
    organic:    'var(--ease-organic)',
  } as const;

  export const textScale = {
    display: {
      '2xl': 'var(--text-display-2xl)',
      xl:    'var(--text-display-xl)',
      lg:    'var(--text-display-lg)',
      md:    'var(--text-display-md)',
    },
    body: {
      lg: 'var(--text-body-lg)',
      md: 'var(--text-body-md)',
      sm: 'var(--text-body-sm)',
      xs: 'var(--text-body-xs)',
    },
  } as const;

  export type Tokens = {
    colors: typeof colors;
    fonts: typeof fonts;
    motion: typeof motion;
    easing: typeof easing;
    textScale: typeof textScale;
  };
  ```

- [ ] **Step 5: Run the test to verify it passes:**

  ```bash
  cd D:/Psycho && pnpm --filter @disciplineos/design-system test -- tokens
  ```
  Expected: PASS.

- [ ] **Step 6: Update `packages/design-system/src/index.ts`** to re-export the new shape (verify the file's existing content first; only add what's missing):

  ```ts
  export * from './tokens';
  // (existing primitives export will be replaced in Chunk 4)
  ```

- [ ] **Step 7: Run typecheck across the monorepo:**

  ```bash
  cd D:/Psycho && pnpm typecheck
  ```
  Expected: pass.

- [ ] **Step 8: Commit:**

  ```bash
  git -C D:/Psycho add packages/design-system/src/tokens.ts packages/design-system/src/tokens.test.ts packages/design-system/src/index.ts
  git -C D:/Psycho commit -m "$(cat <<'EOF'
  feat(design-system): tokens.ts mirrors Quiet Strength CSS vars

  Typed exports of every CSS var in apps/web-app/src/app/globals.css
  so TS consumers reference token names rather than literal strings.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 1.3: Add `next-themes` and wrap providers

**Files:**
- Modify: `apps/web-app/package.json` (add `next-themes` dep)
- Modify: `apps/web-app/src/app/layout.tsx` (root layout)
- Modify: `apps/web-app/src/components/Providers.tsx`

**Why `next-themes` instead of writing a custom theme provider:**
- Vetted, widely-used (handles SSR theme bootstrap correctly without flash-of-incorrect-theme)
- The library writes its own pre-hydration script — we don't author raw inline JS in our code
- API matches what we want exactly: `attribute="data-theme"`, `defaultTheme="dark"`, `enableSystem`, `disableTransitionOnChange`

- [ ] **Step 1: Add the dep:**

  Edit `apps/web-app/package.json` to add `"next-themes": "^0.3.0"` to `dependencies`. Then:

  ```bash
  cd D:/Psycho && pnpm install
  ```

- [ ] **Step 2: Read the current `Providers.tsx`:**

  ```bash
  cat D:/Psycho/apps/web-app/src/components/Providers.tsx
  ```

- [ ] **Step 3: Wrap the existing provider tree with `ThemeProvider`** from `next-themes`. Edit `Providers.tsx` so the JSX looks like:

  ```tsx
  'use client';
  import { ThemeProvider } from 'next-themes';
  // …existing imports (ClerkProvider, QueryClientProvider, etc.)…

  export function Providers({ children }: { children: React.ReactNode }) {
    return (
      <ClerkProvider>
        <ThemeProvider
          attribute="data-theme"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
          themes={['dark', 'light']}
        >
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        </ThemeProvider>
      </ClerkProvider>
    );
  }
  ```

  Adapt to whatever existing wrappers are present — preserve them, add `ThemeProvider` between Clerk and QueryClient.

- [ ] **Step 4: Confirm the root `layout.tsx`** already calls `<Providers>` somewhere; if not, ensure the locale layout does. Read:

  ```bash
  cat D:/Psycho/apps/web-app/src/app/layout.tsx
  cat D:/Psycho/apps/web-app/src/app/[locale]/layout.tsx
  ```

  The next-themes library requires `<html suppressHydrationWarning>` on the `<html>` element. Add that attribute to whichever layout owns the `<html>` tag.

- [ ] **Step 5: Visual smoke** — start the dev server and verify no flash on light-mode reload:

  ```bash
  cd D:/Psycho/apps/web-app && pnpm dev
  ```
  - In DevTools: clear localStorage, hard reload — confirms default-dark behavior
  - In DevTools: `window.localStorage.setItem('theme', 'light')`, hard reload — confirms light loads instantly with no dark flash
  - Stop the dev server.

- [ ] **Step 6: Run tests + lint:**

  ```bash
  cd D:/Psycho/apps/web-app && pnpm test && pnpm typecheck && pnpm lint
  ```
  Expected: pass.

- [ ] **Step 7: Commit:**

  ```bash
  git -C D:/Psycho add apps/web-app/package.json pnpm-lock.yaml apps/web-app/src/components/Providers.tsx apps/web-app/src/app/layout.tsx apps/web-app/src/app/[locale]/layout.tsx
  git -C D:/Psycho commit -m "$(cat <<'EOF'
  feat(web-app): integrate next-themes for dark/light mode

  Uses the library's vetted SSR-safe theme bootstrap (no flash on
  light-mode reload). Default theme = dark; system preference
  considered for new users.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 1.4: Per-locale font loading in `[locale]/layout.tsx`

**Files:**
- Modify: `apps/web-app/src/app/[locale]/layout.tsx`

Inter + Fraunces load on every page. Vazirmatn loads ONLY when `locale === 'fa'` (saves ~85KB on en/fr/ar). IBM Plex Sans Arabic does not need a `next/font` instance — the CSS font stack handles glyph fallback.

- [ ] **Step 1: Read the current layout** to see existing imports:

  ```bash
  cat D:/Psycho/apps/web-app/src/app/[locale]/layout.tsx
  ```

- [ ] **Step 2: Edit the layout** to introduce the font instances and CSS-var bindings. The exact diff depends on what's there; the target shape is:

  ```tsx
  import { Inter, Fraunces, Vazirmatn } from 'next/font/google';
  import { NextIntlClientProvider } from 'next-intl';
  import { getMessages } from 'next-intl/server';
  import { notFound } from 'next/navigation';
  import { routing } from '@/i18n/routing';

  const inter = Inter({
    subsets: ['latin'],
    variable: '--font-inter',
    display: 'swap',
  });

  const fraunces = Fraunces({
    subsets: ['latin'],
    variable: '--font-fraunces',
    display: 'swap',
    axes: ['SOFT', 'WONK', 'opsz'],
  });

  const vazirmatn = Vazirmatn({
    subsets: ['arabic'],
    variable: '--font-vazirmatn',
    display: 'swap',
  });

  type Locale = (typeof routing.locales)[number];

  export default async function LocaleLayout({
    children,
    params,
  }: {
    children: React.ReactNode;
    params: Promise<{ locale: string }>;
  }) {
    const { locale } = await params;
    if (!routing.locales.includes(locale as Locale)) notFound();

    const messages = await getMessages();
    const dir = locale === 'ar' || locale === 'fa' ? 'rtl' : 'ltr';
    const isFa = locale === 'fa';

    const fontVars = `${inter.variable} ${fraunces.variable} ${isFa ? vazirmatn.variable : ''}`.trim();

    return (
      <html lang={locale} dir={dir} className={fontVars} suppressHydrationWarning>
        <body>
          <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
        </body>
      </html>
    );
  }
  ```

  Note: keep any existing exports (`generateStaticParams`, `metadata`, etc.) — only modify the imports + the function body. The `suppressHydrationWarning` on `<html>` is required by `next-themes`.

- [ ] **Step 3: Update `globals.css`** to use the next/font CSS variables instead of literal font-family strings. Edit the `@theme` font lines:

  ```css
  --font-body:    var(--font-inter), 'IBM Plex Sans Arabic', system-ui, sans-serif;
  --font-display: var(--font-fraunces), 'IBM Plex Sans Arabic', system-ui, serif;
  --font-fa:      var(--font-vazirmatn), system-ui, sans-serif;
  ```

- [ ] **Step 4: Run dev server and verify in browser:**

  ```bash
  cd D:/Psycho/apps/web-app && pnpm dev
  ```
  - Open `http://localhost:3020/en` — body in Inter, headings can use Fraunces
  - Open `http://localhost:3020/ar` — body still Inter for Latin; Arabic glyphs fall back to system Plex Arabic if installed
  - Open `http://localhost:3020/fa` — Persian text in Vazirmatn (verify network tab shows Vazirmatn woff2 loaded)
  - Open `http://localhost:3020/en` again — verify Vazirmatn is NOT loaded (network tab)

  Stop the dev server.

- [ ] **Step 5: Run tests:**

  ```bash
  cd D:/Psycho/apps/web-app && pnpm test && pnpm test:e2e -- --grep "@i18n"
  ```
  Expected: pass.

- [ ] **Step 6: Commit:**

  ```bash
  git -C D:/Psycho add apps/web-app/src/app/[locale]/layout.tsx apps/web-app/src/app/globals.css
  git -C D:/Psycho commit -m "$(cat <<'EOF'
  feat(web-app): per-locale font loading

  Inter + Fraunces ship for every locale. Vazirmatn only loads when
  locale === 'fa' (saves ~85KB on en/fr/ar). IBM Plex Sans Arabic is
  declared as a CSS fallback in the font stack — no separate next/font
  instance needed for glyph-coverage matching.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task 1.5: `useReducedMotion` hook

**Files:**
- Create: `apps/web-app/src/hooks/useReducedMotion.ts`
- Create: `apps/web-app/tests/unit/hooks/useReducedMotion.test.tsx`

Used by every motion-bearing primitive in Phase 1+. Two sources truth-OR'd: OS `prefers-reduced-motion: reduce` AND a `data-ambient-motion="off"` attribute on `<html>` (the Settings flag — actual Settings UI lands in Phase 3).

- [ ] **Step 1: Failing test:**

  ```tsx
  import { renderHook } from '@testing-library/react';
  import { afterEach, describe, expect, it, vi } from 'vitest';
  import { useReducedMotion } from '@/hooks/useReducedMotion';

  describe('useReducedMotion', () => {
    afterEach(() => {
      document.documentElement.removeAttribute('data-ambient-motion');
      vi.restoreAllMocks();
    });

    it('returns true when OS prefers reduced motion', () => {
      vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
        matches: true,
        media: '(prefers-reduced-motion: reduce)',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
        onchange: null,
      }));
      const { result } = renderHook(() => useReducedMotion());
      expect(result.current).toBe(true);
    });

    it('returns true when the Settings flag is set', () => {
      document.documentElement.setAttribute('data-ambient-motion', 'off');
      vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
        matches: false,
        media: '',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
        onchange: null,
      }));
      const { result } = renderHook(() => useReducedMotion());
      expect(result.current).toBe(true);
    });

    it('returns false when neither source signals reduced motion', () => {
      vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
        matches: false,
        media: '',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
        onchange: null,
      }));
      const { result } = renderHook(() => useReducedMotion());
      expect(result.current).toBe(false);
    });
  });
  ```

- [ ] **Step 2: Run to fail.** Expected: FAIL.

- [ ] **Step 3: Implement:**

  ```ts
  'use client';
  import { useEffect, useState } from 'react';

  export function useReducedMotion(): boolean {
    const [reduced, setReduced] = useState<boolean>(() => {
      if (typeof window === 'undefined') return false;
      const ambientOff = document.documentElement.getAttribute('data-ambient-motion') === 'off';
      const osReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      return ambientOff || osReduced;
    });

    useEffect(() => {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      const update = () => {
        const ambientOff = document.documentElement.getAttribute('data-ambient-motion') === 'off';
        setReduced(ambientOff || mq.matches);
      };
      mq.addEventListener('change', update);
      const observer = new MutationObserver(update);
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-ambient-motion'] });
      return () => {
        mq.removeEventListener('change', update);
        observer.disconnect();
      };
    }, []);

    return reduced;
  }
  ```

- [ ] **Step 4: Run to pass.** Expected: PASS.

- [ ] **Step 5: Commit:**

  ```bash
  git -C D:/Psycho add apps/web-app/src/hooks/useReducedMotion.ts apps/web-app/tests/unit/hooks/useReducedMotion.test.tsx
  git -C D:/Psycho commit -m "$(cat <<'EOF'
  feat(web-app): useReducedMotion hook

  OR's OS prefers-reduced-motion with a [data-ambient-motion="off"]
  attribute that the Settings UI will flip in Phase 3. Reactive to
  both sources via MutationObserver + media-query change listener.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Phase 0a chunk-completion checklist

- [ ] All 5 tasks committed (one or more commits each)
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green from `apps/web-app`
- [ ] `pnpm test` green from `packages/design-system`
- [ ] Existing screens visually re-themed (manual smoke at `pnpm dev`, dark + light, en + ar + fa)
- [ ] No regression in existing E2E (`pnpm test:e2e`)
- [ ] No theme flash on light-mode hard reload (`next-themes` working as expected)

**Stop here. Run plan-document-reviewer on this chunk before proceeding to Chunk 2.**

---

## Chunk 2: Phase 0b — Custom ESLint plugin (`@disciplineos/eslint-plugin-discipline`)

**Three rules, three TDD cycles, one new package. The rules are the legal infrastructure for every later chunk — without them, clinical contracts are mere convention.**

**Time estimate:** 1.5 days.

**Acceptance:**
- New package `tools/eslint-plugin-discipline` builds and is installable as a workspace dep
- Three rules ship with passing unit tests (using `@typescript-eslint/rule-tester`)
- `apps/web-app/eslint.config.mjs` activates all three rules
- Running `pnpm lint` from `apps/web-app` does not regress (existing code passes the rules; if anything fails, fix the calling code, never silence the rule)

---

### Task 2.1: Scaffold `@disciplineos/eslint-plugin-discipline` package

**Files:**
- Create: `tools/eslint-plugin-discipline/package.json`
- Create: `tools/eslint-plugin-discipline/tsconfig.json`
- Create: `tools/eslint-plugin-discipline/src/index.ts`
- Create: `tools/eslint-plugin-discipline/src/clinical-numbers.ts`
- Modify: `pnpm-workspace.yaml` (add `tools/*` if not present)

Steps:

- [ ] Create `tools/eslint-plugin-discipline/package.json`:

  ```json
  {
    "name": "@disciplineos/eslint-plugin-discipline",
    "version": "0.0.0",
    "private": true,
    "main": "src/index.ts",
    "types": "src/index.ts",
    "scripts": {
      "test": "vitest run",
      "typecheck": "tsc --noEmit"
    },
    "peerDependencies": {
      "eslint": "^9.0.0"
    },
    "devDependencies": {
      "@typescript-eslint/parser": "^8.0.0",
      "@typescript-eslint/rule-tester": "^8.0.0",
      "@typescript-eslint/utils": "^8.0.0",
      "typescript": "~5.6.2",
      "vitest": "^2.1.0"
    }
  }
  ```

- [ ] Create `tools/eslint-plugin-discipline/tsconfig.json` extending the repo base.

- [ ] Create `src/clinical-numbers.ts` — the regex source-of-truth for rule 2:

  ```ts
  export const CLINICAL_NUMERIC_PATTERNS: readonly RegExp[] = [
    /_total$/i,
    /Total$/,
    /^intensity$/i,
    /^score$/i,
    /^severity$/i,
    /^band$/i,
    /^phq9/i,
    /^phq_9_/i,
    /^gad7/i,
    /^gad_7_/i,
    /^audit_?c/i,
    /^auditC/,
    /^rci_/i,
    /^rci[A-Z]/,
  ];

  export function isClinicalNumericIdentifier(name: string): boolean {
    return CLINICAL_NUMERIC_PATTERNS.some((re) => re.test(name));
  }
  ```

- [ ] Create `src/index.ts`:

  ```ts
  import { rule as noPhysicalTailwindProperties } from './rules/no-physical-tailwind-properties';
  import { rule as clinicalNumbersMustFormat } from './rules/clinical-numbers-must-format';
  import { rule as noLlmOnCrisisRoute } from './rules/no-llm-on-crisis-route';

  export = {
    rules: {
      'no-physical-tailwind-properties': noPhysicalTailwindProperties,
      'clinical-numbers-must-format': clinicalNumbersMustFormat,
      'no-llm-on-crisis-route': noLlmOnCrisisRoute,
    },
  };
  ```

- [ ] Add the package to the root pnpm workspace by ensuring `tools/*` is in `pnpm-workspace.yaml`. Read first:

  ```bash
  cat D:/Psycho/pnpm-workspace.yaml
  ```
  If `tools/*` is not listed, edit to add:
  ```yaml
  packages:
    - 'apps/*'
    - 'packages/*'
    - 'services/*'
    - 'tools/*'
  ```

- [ ] Install:

  ```bash
  cd D:/Psycho && pnpm install
  ```

- [ ] Defer the commit until rule 1 lands. Move to Task 2.2 first, then commit them together.

---

### Task 2.2: Rule 1 — `no-physical-tailwind-properties`

**Files:**
- Create: `tools/eslint-plugin-discipline/src/rules/no-physical-tailwind-properties.ts`
- Create: `tools/eslint-plugin-discipline/tests/no-physical-tailwind-properties.test.ts`

The rule scans JSX `className` strings for banned utility classes (`ml-*`, `mr-*`, `pl-*`, `pr-*`, `left-*`, `right-*`, `text-left`, `text-right`) and reports each match with the suggested logical-property replacement.

- [ ] Write the test using `@typescript-eslint/rule-tester` with realistic invalid + valid samples (ms-/me-, ps-/pe-, etc.). Aim for ≥6 invalid + ≥4 valid cases.
- [ ] Run to fail.
- [ ] Implement the rule. Use `context.report` with a descriptive message including the suggested replacement (e.g., `"Use 'ms-4' instead of 'ml-4' for RTL support"`).
- [ ] Run on `apps/web-app` to see if any existing code violates: `cd D:/Psycho && pnpm --filter @disciplineos/web-app exec eslint src --rule '@disciplineos/discipline/no-physical-tailwind-properties: error'` (after registering the plugin in Task 2.5). If existing code violates, fix it (don't silence the rule).
- [ ] Commit (along with Task 2.1 scaffold).

---

### Task 2.3: Rule 2 — `clinical-numbers-must-format`

**Files:**
- Create: `tools/eslint-plugin-discipline/src/rules/clinical-numbers-must-format.ts`
- Create: `tools/eslint-plugin-discipline/tests/clinical-numbers-must-format.test.ts`

The rule scans JSX expression children. When the expression is a bare `{identifier}` whose name matches `isClinicalNumericIdentifier`, report unless one of the following holds:
- Wrapped in `formatNumberClinical(...)` call
- The enclosing JSX element has `className` containing `clinical-number`

- [ ] Write the test — at least 10 cases (the regex array in `clinical-numbers.ts` is broad; we need explicit positive AND negative coverage to prevent false positives that erode trust in the rule):
  - **Positive (must flag):**
    - `<div>{phq9Score}</div>` (snake_case-adjacent camelCase)
    - `<div>{score}</div>` (bare keyword)
    - `<div>{auditCScore}</div>` (camelCase variant of `audit_c`)
    - `<div>{rciDelta}</div>` (camelCase variant of `rci_`)
    - `<span>{user.intensity}</span>` (member-expression form)
  - **Negative (must NOT flag):**
    - `<div>{formatNumberClinical(score)}</div>` (already wrapped)
    - `<div className="clinical-number">{score}</div>` (CSS-class escape hatch)
    - `<div>{regularCount}</div>` (unrelated identifier)
    - `<div>{phq9Skipped}</div>` (matches `^phq9/i` but is a boolean/state flag — confirms the regex is too greedy and we must add a deny-list OR document that booleans co-located with `phq9` get a known-false-positive carve-out via `clinical-number` className wrap)
    - `<div>{auditCompleted}</div>` (matches `^auditC/` but is a boolean state — same carve-out reasoning)
- [ ] Run to fail.
- [ ] Implement. If the negative `phq9Skipped` / `auditCompleted` cases force the rule to add a `BOOLEAN_SUFFIXES = ['Skipped', 'Completed', 'Enabled', 'Pending']` deny-list before reporting, do so — the rule must not false-positive on adjacent boolean state, or developers will start sprinkling eslint-disable comments and the rule loses authority.
- [ ] Run to pass.
- [ ] Commit.

---

### Task 2.4: Rule 3 — `no-llm-on-crisis-route`

**Files:**
- Create: `tools/eslint-plugin-discipline/src/rules/no-llm-on-crisis-route.ts`
- Create: `tools/eslint-plugin-discipline/tests/no-llm-on-crisis-route.test.ts`

The rule fires on `ImportDeclaration` nodes when:
- The source file path matches `**/app/**/crisis/**` OR `**/app/**/companion/**`
- AND the import source is `@disciplineos/llm-client` (or any path containing `llm-client`)

Next.js 15 `app/` is ESM-only — `require()` is not used, so we only visit `ImportDeclaration` (no `CallExpression` for `require()`). The second test axis is import shape (default vs named), not module system.

- [ ] Write the test — fixtures with paths set via the rule-tester `filename` option. ≥4 invalid + ≥2 valid:
  - **Invalid (must flag):**
    - crisis route × default import: `import llm from '@disciplineos/llm-client'` in `app/[locale]/crisis/page.tsx`
    - crisis route × named import: `import { ask } from '@disciplineos/llm-client'` in `app/[locale]/crisis/components/CrisisCard.tsx`
    - companion route × default import: same as above but in `app/[locale]/companion/page.tsx`
    - companion route × named import: same as above but in `app/[locale]/companion/components/CompanionThread.tsx`
  - **Valid (must NOT flag):**
    - same default + named imports from `app/[locale]/journal/page.tsx` (non-crisis, non-companion path)
    - safe import from inside crisis: `import { tel } from '@disciplineos/safety-directory'` in `app/[locale]/crisis/page.tsx` (importing a non-LLM client)
- [ ] Run to fail.
- [ ] Implement.
- [ ] Run to pass.
- [ ] Commit.

---

### Task 2.5: Wire the plugin into `apps/web-app/eslint.config.mjs`

**Files:**
- Modify: `apps/web-app/package.json` (add the workspace dep)
- Modify: `apps/web-app/eslint.config.mjs`

- [ ] Add `"@disciplineos/eslint-plugin-discipline": "workspace:*"` to `apps/web-app` devDependencies.
- [ ] Run `pnpm install` from repo root.
- [ ] Read the current `eslint.config.mjs`:
  ```bash
  cat D:/Psycho/apps/web-app/eslint.config.mjs
  ```
- [ ] Add the plugin to the flat config:
  ```mjs
  import discipline from '@disciplineos/eslint-plugin-discipline';
  // …existing imports…
  export default [
    // …existing config…
    {
      files: ['src/**/*.{ts,tsx}'],
      plugins: { '@disciplineos/discipline': discipline },
      rules: {
        '@disciplineos/discipline/no-physical-tailwind-properties': 'error',
        '@disciplineos/discipline/clinical-numbers-must-format': 'error',
        '@disciplineos/discipline/no-llm-on-crisis-route': 'error',
      },
    },
  ];
  ```
- [ ] Run lint:
  ```bash
  cd D:/Psycho/apps/web-app && pnpm lint
  ```
  - If existing code triggers the new rules, **fix the code, do not silence the rule**. Examples: replace `ml-4` with `ms-4`; wrap clinical numbers with `formatNumberClinical`.
- [ ] Commit.

---

### Phase 0b chunk-completion checklist

- [ ] Plugin builds and tests pass: `pnpm --filter @disciplineos/eslint-plugin-discipline test`
- [ ] After Task 2.5 wires the plugin, **re-run all three rules against `apps/web-app/src` and confirm zero violations**: `cd D:/Psycho/apps/web-app && pnpm lint` (this is the post-wiring verification gate that Task 2.2 deferred — do it here, not earlier; if anything fires, fix the calling code, never silence the rule)
- [ ] All three rules each have ≥6 unit-test cases (rule 2: ≥10 incl. boolean false-positive negatives; rule 3: ≥6 across crisis/companion × default/named)
- [ ] Manual sanity check: temporarily plant a deliberate violation (e.g., `<div>{phq9Score}</div>` in a real component file), run lint, confirm error message, revert. Proves the rule fires on real code, not just rule-tester fixtures.

**Stop here. Run plan-document-reviewer on this chunk before proceeding.**

---

## Chunk 3: Phase 0c — Minimum service worker + Storybook + Chromatic baseline

**Time estimate:** 2 days.

**Acceptance:**
- A minimum Workbox-driven service worker registers, precaches `/[currentLocale]/crisis` HTML + the safety-directory JSON, and is gated behind `process.env.NODE_ENV === 'production'`
- Storybook 8 boots from `apps/web-app/.storybook/`; renders the existing primitives in dark + light + en + ar variants (4 variants per story)
- Chromatic project initialized; baseline snapshot uploaded
- The `useStubs` hook lands so Storybook can render against deterministic data

---

### Task 3.1: `useStubs` hook + stubs scaffold

**Files:**
- Create: `apps/web-app/src/hooks/useStubs.ts`
- Create: `apps/web-app/src/lib/stubs/index.ts`
- Create: `apps/web-app/src/lib/stubs/check-in.ts` (placeholder; expanded in Phase 1)
- Create: `apps/web-app/tests/unit/hooks/useStubs.test.tsx`

- [ ] Failing test, then implementation. The hook returns `true` when `process.env.NEXT_PUBLIC_USE_STUBS === 'true'` OR `NODE_ENV === 'test'` OR a `?stubs=true` URL param is present.
- [ ] Stubs scaffold exports a single `getStub<T>(domain, key)` accessor with TypeScript-narrowed return.
- [ ] Commit.

---

### Task 3.2: Service worker registration + Workbox build pipeline

**Files:**
- Create: `apps/web-app/src/lib/sw-register.ts`
- Create: `apps/web-app/public/sw.js` (or generated by `workbox-build`)
- Create: `apps/web-app/workbox-config.cjs`
- Modify: `apps/web-app/package.json` (add `workbox-build`, `workbox-window` devDeps)
- Modify: `apps/web-app/next.config.mjs` (no special config; Workbox runs via npm script)

- [ ] Add Workbox deps. Install.
- [ ] Write `workbox-config.cjs` that precaches the crisis page route + the safety-directory JSON for the **default routing locale `en` only** (Phase 0 single-locale minimum per spec §8.5; full `en+ar+fa` precache is deferred to Chunk 8 §8.3 in Phase 5). Use `precacheAndRoute` with the explicit glob `out/en/crisis/**/*.html` (build-time, unambiguous — do NOT use a runtime `[locale]` placeholder which Workbox can't resolve).
- [ ] Add a `pnpm sw:build` script that runs `workbox injectManifest` and emits to `public/sw.js`.
- [ ] Implement `sw-register.ts` — registers in `useEffect` on the root client component, only when `process.env.NODE_ENV === 'production'`.
- [ ] Test: write a Vitest unit test that asserts the registration is a no-op outside production.
- [ ] Smoke: run `pnpm build && pnpm start`, open in a browser, verify the SW is registered (DevTools → Application → Service Workers).
- [ ] Commit.

---

### Task 3.3: Storybook 8 setup

**Files:**
- Create: `apps/web-app/.storybook/main.ts`
- Create: `apps/web-app/.storybook/preview.tsx`
- Modify: `apps/web-app/package.json` (Storybook 8 + addons + interaction testing deps)
- Create: `packages/design-system/src/primitives/__stories__/.gitkeep` (stories will land per-component in Chunk 4)

- [ ] Add Storybook 8 + `@storybook/nextjs` + `@storybook/addon-themes` + `@storybook/test` + `@storybook/addon-a11y` to `apps/web-app/devDependencies`. Install.
- [ ] `.storybook/main.ts`:
  ```ts
  import type { StorybookConfig } from '@storybook/nextjs';
  const config: StorybookConfig = {
    stories: [
      '../../../packages/design-system/src/**/*.stories.@(ts|tsx)',
      '../src/components/**/*.stories.@(ts|tsx)',
    ],
    addons: ['@storybook/addon-essentials', '@storybook/addon-a11y', '@storybook/addon-themes', '@storybook/addon-interactions'],
    framework: { name: '@storybook/nextjs', options: {} },
  };
  export default config;
  ```
- [ ] `.storybook/preview.tsx` — wraps every story in `ThemeProvider` (from next-themes) + `NextIntlClientProvider`, with theme + locale toolbar selectors (use `@storybook/addon-themes` for the theme switcher).
- [ ] Verify Storybook boots: `cd D:/Psycho/apps/web-app && pnpm storybook` (port 6006). The story shelf will be empty for now.
- [ ] Commit.

---

### Task 3.4: Chromatic project init + baseline

**Files:**
- Create: `apps/web-app/.storybook/chromatic.config.json`
- Modify: `apps/web-app/package.json` (add `chromatic` devDep + `chromatic` script)

- [ ] Confirm with the user (one-time decision) that the Chromatic project token is provisioned and an env var is set in CI. **Do not commit a token.**
- [ ] Write `chromatic.config.json` with **`onlyStoryFiles: ["packages/design-system/src/**/*.stories.@(ts|tsx)"]`** so Chromatic snapshots ONLY design-system primitives — feature-component stories under `apps/web-app/src/components/**` churn too fast for visual-regression to be valuable, and snapshots there waste reviewer time. (Storybook itself remains broader per Task 3.3 — only Chromatic is scoped down.)
- [ ] Add the `chromatic` script: `"chromatic": "chromatic --exit-zero-on-changes"`.
- [ ] Add a GitHub Actions workflow at the **repo-root** path `D:/Psycho/.github/workflows/chromatic.yml` (GitHub Actions only reads workflows from `.github/workflows/` at the repository root — putting it under `apps/web-app/.github/` does nothing). The workflow runs Chromatic on PRs touching `apps/web-app/` or `packages/design-system/`.
- [ ] Run a local baseline once stories exist (Chunk 4); for now just commit the scaffolding.
- [ ] Commit.

---

### Phase 0c chunk-completion checklist

- [ ] SW registers in production builds; off in dev/test
- [ ] Storybook boots (`pnpm storybook` from `apps/web-app`)
- [ ] Chromatic config in place (baseline upload happens after Chunk 4)
- [ ] `pnpm typecheck && pnpm lint && pnpm test` still green

**Stop here. Run plan-document-reviewer on this chunk. Phase 0 is complete.**

---

## Chunk 4: Phase 1 — Generic primitives (20 net-new + 11 refreshed = 31 components touched)

**Time estimate:** 1 week.

**Scope reconciliation:** Spec §4.3 enumerates **28 net-new primitives total** = 9 generic + 5 layout/shell + 4 data display + 2 feedback + **7 clinical + 1 motion**. The clinical 7 + motion 1 are deferred to Chunk 5 (separate `clinical/` directory, contractual rules). Chunk 4 covers **20 net-new generic** (9 + 5 + 4 + 2) plus the **11 refreshed** (spec §4.4: Button, Card, Input, Textarea, Spinner, Divider, ProgressRing, Badge, Skeleton, Tooltip, Sparkline). Total: **31 components touched.**

**Storybook prerequisite:** Storybook + axe-core were bootstrapped in Chunk 3 (Task 3.3). This chunk consumes that infrastructure; no setup work here.

**Approach:** TDD per component. Two distinct task shapes — a **refresh** template (extract + retoken, preserve API) and a **new** template (build from scratch). Each component lands as its own commit.

---

### 4.0 — Two task templates

**Refresh template (apply to the 11 refreshed primitives — API must NOT change):**

````markdown
### Task 4.X: <ComponentName> (REFRESH)

**Files:**
- Modify (extract → its own file): `packages/design-system/src/primitives/<ComponentName>.tsx`
- Create: `packages/design-system/src/primitives/__tests__/<ComponentName>.test.tsx`
- Create: `packages/design-system/src/primitives/__stories__/<ComponentName>.stories.tsx`
- Reference: `packages/design-system/src/primitives/web.tsx` (the existing 653-line monolith; copy this component out, do not rewrite)

- [ ] Snapshot the existing prop contract from `web.tsx` (TypeScript interface + default values). Write a contract test that exercises EVERY prop with its existing semantics — this is the regression guard.
- [ ] Run contract test against the existing `web.tsx` import path to verify it passes (proves the test is honest about current behavior)
- [ ] Extract the component into its own file. Update tokens to the new Quiet Strength CSS vars (no hardcoded colors). Do NOT change the public API surface.
- [ ] Re-point the contract test at the new import path. Run — must still pass.
- [ ] Add Storybook story: dark + light × en + ar = 4 variants.
- [ ] Run axe-core on every story variant; zero serious/critical violations.
- [ ] If component supports RTL-relevant props (e.g., `Sparkline` direction, `Tooltip` side), add a `dir="rtl"` story variant.
- [ ] Commit with message: `feat(ds): refresh <ComponentName> — Quiet Strength tokens, API unchanged`
````

**New template (apply to the 20 net-new generic primitives):**

````markdown
### Task 4.X: <ComponentName> (NEW)

**Files:**
- Create: `packages/design-system/src/primitives/<ComponentName>.tsx`
- Create: `packages/design-system/src/primitives/__tests__/<ComponentName>.test.tsx`
- Create: `packages/design-system/src/primitives/__stories__/<ComponentName>.stories.tsx`

- [ ] Write failing test: rendered output, props pass-through, accessible role/name (use `@testing-library/react` + `jest-axe`), RTL behavior if directional, and (for data-driven primitives like `Stat`/`Trend`) a `useStubs` default-value path that renders without prop-drilling in design time.
- [ ] Run to fail.
- [ ] Implement — Radix wrapper if applicable (Slider, RadioGroup, Switch, Select, Tabs, Dialog, Toast); tokens via Tailwind class names that map to CSS vars; logical properties only (`ms-*`, `me-*`, `ps-*`, `pe-*`, never physical — the ESLint rule from Chunk 2 enforces this).
- [ ] Add Storybook story: dark + light × en + ar = 4 variants.
- [ ] Run axe-core on every story variant; zero serious/critical violations.
- [ ] If component is directional (`Slider` drag, `Sheet` side, `Tooltip` side, `Toast` corner), add an explicit `dir="rtl"` story variant and assert mirrored layout.
- [ ] Commit with message: `feat(ds): add <ComponentName> primitive`
````

---

### 4.1 — Refreshed primitives (11) — extract from `web.tsx`, retoken, preserve API

| Task | Component | Refresh notes |
|------|-----------|---------------|
| 4.1 | `Button` | variants: default/secondary/ghost/destructive |
| 4.2 | `Card` | header/footer slots stay |
| 4.3 | `Input` | error/disabled states |
| 4.4 | `Textarea` | resize behavior unchanged |
| 4.5 | `Spinner` | reduced-motion aware (already handled in current impl — preserve) |
| 4.6 | `Divider` | |
| 4.7 | `Badge` | variants: neutral/positive/warning/critical |
| 4.8 | `Skeleton` | shimmer animation suppressed under reduced motion |
| 4.9 | `Tooltip` | Radix Tooltip wrap (refresh — already exists in `web.tsx`) |
| 4.10 | `ProgressRing` | tokens only; geometry untouched |
| 4.11 | `Sparkline` | **Visx-backed swap; preserves prop contract** (`data`, `color`, `strokeWidth`); update `MoodSparkline` consumer in the SAME commit so existing E2E `dashboard.spec.ts` does not break |

### 4.2 — Net-new generic primitives (9) — Radix wrappers

| Task | Component | Notes |
|------|-----------|-------|
| 4.12 | `Slider` | Radix Slider; thumb behavior must mirror in RTL |
| 4.13 | `RadioGroup` | Radix |
| 4.14 | `CheckboxGroup` | composition of Radix Checkboxes |
| 4.15 | `Switch` | Radix |
| 4.16 | `Select` | Radix Select |
| 4.17 | `TabNav` | Radix Tabs |
| 4.18 | `Dialog` | Radix Dialog wrap |
| 4.19 | `Sheet` | Radix Dialog (side variant) — `dir="rtl"` flips slide direction |
| 4.20 | `Toast` | Radix Toast — corner placement flips in RTL |

### 4.3 — Net-new layout & shell primitives (5)

| Task | Component | Notes |
|------|-----------|-------|
| 4.21 | `PageShell` | the page-level layout shell |
| 4.22 | `TopBar` | theme toggle + locale switcher + notifications bell badge — mirrors fully in RTL |
| 4.23 | `SidebarNav` | Lucide + custom icons (per spec §3 — 12 custom icons land here) |
| 4.24 | `BottomNav` | mobile-shape; 5 slots max (per spec §5) |
| 4.25 | `WizardShell` | multi-step shell with save-and-resume |

### 4.4 — Net-new data-display primitives (4) — Visx-backed

> **Pre-task:** Install Visx in `packages/design-system` if not already present (`pnpm --filter @disciplineos/design-system add @visx/group @visx/scale @visx/shape @visx/axis @visx/text`). Single commit before 4.26.

| Task | Component | Notes |
|------|-----------|-------|
| 4.26 | `Stat` | hero number + label + delta; uses `formatNumberClinical` only when `clinical` prop is true (generic primitive — clinical use is opt-in) |
| 4.27 | `Trend` | Stat + Sparkline composition; takes `useStubs`-resolvable data prop |
| 4.28 | `RingChart` | multi-segment ProgressRing extension |
| 4.29 | `BarChart` | Visx; instrument trends over time |

### 4.5 — Net-new feedback primitives (2)

| Task | Component | Notes |
|------|-----------|-------|
| 4.30 | `Banner` | dismissable; severity variants (info/warning/error) |
| 4.31 | `EmptyState` | illustration slot + headline + CTA |

---

### Task 4.32: Delete the legacy `primitives.tsx` and `web.tsx` (cleanup — runs LAST, after 4.1–4.31)

**Files:**
- Delete: `apps/web-app/src/components/primitives.tsx`
- Delete: `packages/design-system/src/primitives/web.tsx`
- Delete: `packages/design-system/src/primitives/web.test.ts`
- Modify: `packages/design-system/src/index.ts` (re-export from per-component files via `primitives/index.ts`)
- Modify: every consumer that imports from the old paths

Steps:

- [ ] Use the Grep tool (NOT bash `grep`) to find all consumers in TWO patterns:
  - Direct path: pattern `from\s+['"]@disciplineos/design-system/src/primitives/web['"]` — catches `from '@disciplineos/design-system/src/primitives/web'` and the `.tsx` variant
  - Re-export path: pattern `from\s+['"]@disciplineos/design-system['"]` then check the imported symbol list against the components that previously lived only in `web.tsx`
- [ ] Update each consumer to import from `@disciplineos/design-system` (the package root barrel)
- [ ] Verify the per-component `primitives/index.ts` re-exports every symbol the old `web.tsx` exported — diff the named exports
- [ ] Run full `pnpm typecheck && pnpm lint && pnpm test` from the repo root
- [ ] Commit with message: `chore(ds): remove legacy web.tsx monolith — all primitives extracted`

---

### Per-primitive progress checklist (track here as work proceeds)

> Mark each box as the task lands. The chunk is done only when every row is checked off — including axe and (when applicable) RTL story.

| # | Component | Type | Test | Impl | Story | Axe | RTL | Committed |
|---|-----------|------|:----:|:----:|:-----:|:---:|:---:|:---------:|
| 4.1 | Button | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.2 | Card | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.3 | Input | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.4 | Textarea | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.5 | Spinner | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.6 | Divider | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.7 | Badge | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.8 | Skeleton | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.9 | Tooltip | R | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.10 | ProgressRing | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.11 | Sparkline | R | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.12 | Slider | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.13 | RadioGroup | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.14 | CheckboxGroup | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.15 | Switch | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.16 | Select | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.17 | TabNav | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.18 | Dialog | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.19 | Sheet | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.20 | Toast | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.21 | PageShell | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.22 | TopBar | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.23 | SidebarNav | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.24 | BottomNav | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.25 | WizardShell | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.26 | Stat | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.27 | Trend | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.28 | RingChart | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.29 | BarChart | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.30 | Banner | N | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4.31 | EmptyState | N | ☐ | ☐ | ☐ | ☐ | — | ☐ |
| 4.32 | (delete legacy) | — | — | ☐ | — | — | — | ☐ |

(Type: R = refresh, N = new. RTL "—" = component has no directional/positional behavior; RTL story not required.)

### Phase 1 chunk-completion checklist

- [ ] All 31 components ship with tests + stories + axe-clean + Chromatic baseline approved
- [ ] No remaining imports from the old `web.tsx` or `primitives.tsx` (verified via Grep tool with both direct-path and re-export patterns)
- [ ] Storybook story shelf shows all 31, each in 4 variants minimum (dark+light × en+ar); directional components add a 5th `dir="rtl"` variant
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green from every package
- [ ] No regression in existing E2E (`dashboard.spec.ts` updated in 4.11 commit alongside Sparkline swap)

**Stop here. Run plan-document-reviewer.**

---

## Chunk 5: Phase 2 — Clinical primitives (8 components) + clinical mirrors

**Time estimate:** 1 week.

**File-structure requirement:** All 8 clinical primitives live under `packages/design-system/src/clinical/` (NOT `primitives/`). The `clinical/` directory is load-bearing — the ESLint rule `clinical-numbers-must-format` from Chunk 2 keys off this path; primitives outside `clinical/` are not subject to the rule. Putting a clinical primitive in the wrong directory silently bypasses linting.

### Preconditions — HALT-AND-SURFACE if missing

Before starting any task in this chunk, verify the following exist. **If any are missing, STOP, do NOT proceed, and report to the user with the missing-file list and a recommendation to either (a) create them in a backend sprint first, or (b) descope the dependent clinical primitive to v1.1.**

```bash
test -f D:/Psycho/shared-rules/relapse_templates.json || echo "MISSING: shared-rules/relapse_templates.json (CompassionTemplate blocked)"
test -d D:/Psycho/services/api/src/discipline/clinical/ || echo "MISSING: discipline/clinical/ Python module (CompassionTemplate selection function blocked)"
test -f D:/Psycho/services/api/src/discipline/safety/emergency_numbers.py || echo "MISSING: emergency_numbers.py (CrisisCard data source blocked)"
```

The halt protocol is mandatory — proceeding without these files produces clinical primitives that lie about their data source, which is a CLAUDE.md non-negotiable violation (#4 — relapse copy from JSON, not hand-rolled; #1 — crisis flows deterministic with validated data).

### Approach

Same TDD-per-component template as Chunk 4 (the new template), but each clinical primitive's test file MUST include the named contract tests in the table below — the contract test name *is* the rule. The clinical-contracts manifest in §5.12 cross-references every contract by name, so missing or renaming a contract test breaks CI.

### Per-primitive task tracking (checkbox per cell)

| # | Component / file | Path | Test | Impl | Story | Axe | Committed |
|---|------------------|------|:----:|:----:|:-----:|:---:|:---------:|
| 5.1 | `formatters.ts` re-export | `apps/web-app/src/lib/formatters.ts` | ☐ | ☐ | — | — | ☐ |
| 5.2 | `clinical-mirrors.ts` | `apps/web-app/src/lib/clinical-mirrors.ts` | ☐ | ☐ | — | — | ☐ |
| 5.3 | `BreathingPulse` | `packages/design-system/src/clinical/BreathingPulse.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.4 | `ResilienceRing` | `packages/design-system/src/clinical/ResilienceRing.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.5 | `UrgeSlider` | `packages/design-system/src/clinical/UrgeSlider.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.6 | `SeverityBand` | `packages/design-system/src/clinical/SeverityBand.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.7 | `RCIDelta` | `packages/design-system/src/clinical/RCIDelta.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.8 | `CompassionTemplate` | `packages/design-system/src/clinical/CompassionTemplate.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.9 | `CrisisCard` | `packages/design-system/src/clinical/CrisisCard.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.10 | `InsightCard` | `packages/design-system/src/clinical/InsightCard.tsx` | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5.11 | `safety/emergency-numbers.ts` | `apps/web-app/src/lib/safety/emergency-numbers.ts` | ☐ | ☐ | — | — | ☐ |

### Required contract tests per task (the test name IS the rule — do not rename)

**5.1 — `formatters.ts` re-export `formatNumberClinical`:**
- `formatNumberClinical_returns_latin_digits_in_fa_locale` — input `5`, locale `fa`, expect `'5'` (NOT `'۵'`)
- `formatNumberClinical_returns_latin_digits_in_ar_locale` — input `5`, locale `ar`, expect `'5'` (NOT `'٥'`)
- `formatNumberClinical_returns_latin_digits_in_en_locale` — sanity baseline

**5.2 — `clinical-mirrors.ts` (the `estimateStateClientMirror` function for design-time stub state):**
- `estimateStateClientMirror_parity_with_server_for_all_intensities_0_to_10` — parameterized over 11 cases (0..10)

**5.3 — `BreathingPulse`:**
- `breathingPulse_inhale_exhale_phase_durations_locked_to_4000ms_each` — assert the animation's `inhale` and `exhale` phase durations are exactly 4000ms each (deterministic timing, not visual regression — read animation config or expose via `data-phase-duration` attribute for testing)
- `breathingPulse_suppressed_when_useReducedMotion_returns_true` — when the hook reports reduced motion (OS prefers-reduced-motion OR `data-ambient-motion="off"`), the component renders a static state instead of animating

**5.4 — `ResilienceRing`:**
- `dashboard_resilienceRing_value_never_decrements_across_renders` (CLAUDE.md Rule #3) — given a sequence of `value` props that include a non-monotone descent, the ring clamps to the previous max
- `resilienceRing_day_count_renders_latin_in_fa_locale` (Rule #9) — render with `locale="fa"` and `value={42}`, assert the rendered day count is `'42'` not `'۴۲'`
- `resilienceRing_day_count_renders_latin_in_ar_locale` (Rule #9) — same with `locale="ar"`, assert `'42'` not `'٤٢'`

**5.5 — `UrgeSlider`:**
- `urgeSlider_value_renders_latin_in_arabic_context` (Rule #9) — render at value 7 with `locale="ar"`, assert displayed value is `'7'`
- `urgeSlider_value_renders_latin_in_persian_context` (Rule #9) — same with `locale="fa"`
- `urgeSlider_thumb_drag_direction_inverts_in_rtl` — drag right under `dir="rtl"` decreases value (RTL mirror)

**5.6 — `SeverityBand`:**
- `severityBand_uses_pinned_phq9_thresholds_not_hand_rolled` — imports `PHQ9_SEVERITY_THRESHOLDS` from `apps/web-app/src/lib/clinical/phq9-thresholds.ts` (a TS mirror of `services/api/src/discipline/psychometric/scoring/phq9.py` `PHQ9_SEVERITY_THRESHOLDS`; the mirror is value-equal-tested in §5.12)
- `severityBand_renders_latin_score_under_fa_locale` (Rule #9) — score `15`, locale `fa`, expect `'15'`

**5.7 — `RCIDelta`:**
- `rciDelta_uses_jacobson_truax_1991_significance_thresholds` — import the threshold constant rather than redefining
- `rciDelta_renders_dot_scale_for_all_significance_levels` — ●●●/●●○/●○○ across the three transition cases
- `rciDelta_renders_latin_delta_in_fa_locale` (Rule #9) — delta `-3`, locale `fa`, expect `'-3'` not `'-۳'`

**5.8 — `CompassionTemplate`:**
- `compassionTemplate_loads_from_shared_rules_relapse_templates_json` (Rule #4) — assert templates resolve via `import templates from '@/data/relapse_templates.json'` where `@/data/relapse_templates.json` is a build-time bundling of `D:/Psycho/shared-rules/relapse_templates.json`. The component MUST NOT contain hand-rolled template strings; a Vitest gate greps the component source for any string literal containing words like `"failed"`, `"reset"`, `"streak"`, etc., and fails if found.
- `compassionTemplate_renders_verbatim_no_interpolation` (Rule #4) — given a template with `{{user_name}}`, the component does NOT substitute (interpolation is a clinical-content modification that requires QA sign-off; v1 renders verbatim)
- `relapseSurface_does_not_contain_streak_reset_copy` — scans rendered output for forbidden phrases ("streak reset", "you failed", etc.)
- `compassionTemplate_uses_fraunces_soft_60_font_axis` — visual / class-name assertion

**5.9 — `CrisisCard`:**
- `crisisCard_does_not_import_or_invoke_llm_client` (Rule #1) — component-level static analysis: scan the component's source for any reference to `@disciplineos/llm-client`, `Anthropic`, `OpenAI`, `Claude`, etc. and fail if present. (This complements the route-level gate `crisisRoute_has_zero_llm_imports` in §5.12.)
- `crisisCard_data_sourced_from_emergency_numbers_constant` — asserts the `EMERGENCY_NUMBERS` import resolves to `apps/web-app/src/lib/safety/emergency-numbers.ts`, which is byte-equivalent to backend `services/api/src/discipline/safety/emergency_numbers.py` (cross-stack gate in §5.11)
- `crisisCard_drops_entries_older_than_90_days` (Rule #10) — given an entry with `verifiedAt` 91 days ago, the entry is filtered out at render
- `crisisCard_falls_back_to_icasa_when_all_local_stale` — if every entry for the user's country is stale, fall back to international hotline (ICASA)
- `crisisCard_renders_with_javascript_disabled` — RSC-only path; no `'use client'` in this component

**5.10 — `InsightCard`:**
- `insightCard_dismiss_lifecycle_per_sprint_108_contract` — exercise dismiss / snooze (24h, 7d) / acknowledge across all transitions
- `insightCard_renders_latin_numerics_under_fa_locale` (Rule #9) — any numeric in the card body renders Latin

**5.11 — `safety/emergency-numbers.ts` constant:**
- `frontend_emergency_numbers_match_backend_byte_equivalence` — Vitest CI gate: read backend `services/api/src/discipline/safety/emergency_numbers.py`, extract the `EMERGENCY_NUMBERS` literal via Python pre-process (or re-emit as JSON in the backend build), `JSON.stringify` the frontend export, assert byte-equal

---

### Task 5.12: Clinical-contracts cross-cutting test file (CRITICAL — the contract manifest)

**File:**
- Create: `apps/web-app/tests/unit/clinical-contracts.test.ts`

This file is the **single auditable manifest** of the clinical contracts a reviewer (clinical lead, security lead, or future engineer) checks before approving a release. Every contract MUST appear here either as a re-imported assertion from the per-component test file, OR as a cross-cutting gate that doesn't fit a single component. The manifest is the source-of-truth — per-component tests are the implementation.

**Required cross-cutting gates** (some `it.todo` until later chunks ship):

```ts
// Manifest of CRITICAL contracts — every clinical primitive contributes ≥1
describe('CRITICAL clinical contracts (per CLAUDE.md non-negotiables)', () => {
  // From 5.4 — Rule #3 (resilience streak monotonic)
  it('ResilienceRing: value-never-decrements-across-renders', () => { /* re-runs the per-component assertion */ });

  // From 5.5/5.6/5.7/5.10/5.4 — Rule #9 (Latin digits for clinical scores)
  it('UrgeSlider: renders-latin-digit-in-fa', () => { /* ... */ });
  it('SeverityBand: renders-latin-score-in-fa', () => { /* ... */ });
  it('RCIDelta: renders-latin-delta-in-fa', () => { /* ... */ });
  it('ResilienceRing: day-count-latin-in-fa', () => { /* ... */ });
  it('InsightCard: renders-latin-numerics-in-fa', () => { /* ... */ });

  // From 5.8 — Rule #4 (compassion templates from JSON, no failure framing)
  it('CompassionTemplate: loads-from-shared-rules-relapse-templates-json', () => { /* ... */ });
  it('CompassionTemplate: no-failure-framing-copy', () => { /* ... */ });

  // From 5.9 — Rule #1 (no LLM on crisis path)
  it('CrisisCard: no-llm-call-component-level', () => { /* ... */ });
  it.todo('crisisRoute: zero-llm-imports-route-level (Chunk 6)'); // works after route ships
  it.todo('companionRoute: zero-llm-imports-route-level (Chunk 7)');

  // From 5.3 — deterministic motion
  it('BreathingPulse: deterministic-4s-4s-timing', () => { /* ... */ });

  // From 5.11 — Rule #10 (safety directory freshness + cross-stack equivalence)
  it('emergency-numbers: frontend-backend-byte-equivalence', () => { /* ... */ });
  it('CrisisCard: drops-stale-entries-90-day-window', () => { /* ... */ });

  // PHI-boundary header — works after Chunk 6 middleware ships
  it.todo('phi-routes: emit-x-phi-boundary-1-header (Chunk 6)');

  // Locale-fallback (no machine translation) — works after Chunk 7
  it.todo('localeFallback: draft-key-falls-back-to-en-silently (Chunk 7)');
});
```

- [ ] Write the file. For the route-level LLM-import gate (deferred to Chunk 6/7), use `import.meta.glob('**/app/**/{crisis,companion}/**/*.{ts,tsx}')` to enumerate routes when implementing.
- [ ] Run; some pass, some `it.todo`. Commit.

### Phase 2 chunk-completion checklist

- [ ] All 11 clinical tasks (5.1–5.11) land with their named contract tests passing (every test name in this chunk's tables matches a real `it(...)` in code)
- [ ] All clinical components live under `packages/design-system/src/clinical/` (not `primitives/`)
- [ ] Storybook stories for the 8 visual clinical primitives in 4 variants (5.1, 5.2, 5.11 are non-visual)
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green
- [ ] `clinical-contracts.test.ts` exists with the full manifest; gates that depend on later chunks are `it.todo` (not skipped, not deleted)

**Stop here. Run plan-document-reviewer.**

---

## Chunk 6: Phase 3 — Existing screens refresh

**Time estimate:** 1 week.

**Approach (task per existing screen):** for each of the 6 existing screens, the task is "refresh onto the new system, no IA change, update E2E selectors in the same PR." Split per screen so each PR is small.

**Naming convention:** the PHI audit hook is named **`usePhiAudit`** throughout (matches the spec's prose convention; do not drift to `useAuditPhi` — the noun-then-verb form was a draft naming).

---

### Task 6.0: Audit existing `/crisis` route → POLISH-or-REBUILD decision artifact

**Why first:** The `/crisis` refresh in 6.8 has two very different scopes depending on the audit outcome. Recording the decision before any other work begins prevents 6.8 from silently expanding mid-chunk and prevents a builder from skipping the analysis.

**Files:**
- Read-only: `apps/web-app/src/app/[locale]/crisis/page.tsx` and any colocated components

Steps:

- [ ] Read the existing `/crisis` route. Check, in order, against spec §7.7:
  - Does the page declare `'use client'`? (if yes → REBUILD)
  - Does it use any `<Suspense>` boundaries? (if yes → REBUILD)
  - Does it perform client-side data fetching (e.g., `useQuery`, `fetch` in a `useEffect`)? (if yes → REBUILD)
  - Are hotline numbers inlined from a local JSON at server-render time? (if no → REBUILD)
  - Are `tel:` / `sms:` rendered as plain anchors (works with JS disabled)? (if no → REBUILD)
- [ ] Record the decision as a one-paragraph note in the PR description for Task 6.8 (e.g., "Audit found `'use client'` + a `useEffect` fetch — REBUILD as Server Component" OR "Audit found Server Component + inlined data — POLISH only: token refresh + Lucide icons").
- [ ] No commit at this step — the decision lives in the 6.8 PR description. Move to Task 6.1.

---

### Existing-screens task table

| Order | Task | Screen | Files modified | E2E updated | Spec ref |
|-------|------|--------|----------------|-------------|----------|
| 6.1 | Refresh Dashboard (incl. PatternsPreviewTile distinct from full InsightCard) | `apps/web-app/src/app/[locale]/page.tsx` + `components/StreakWidget.tsx`, `StateIndicator.tsx`, `PatternsPreviewTile.tsx` (new — small summary tile, NOT a full InsightCard), `QuickActions.tsx` | `tests/e2e/dashboard.spec.ts` | spec §6.1 |
| 6.2 | Refresh Check-in | `apps/web-app/src/app/[locale]/check-in/page.tsx` (use `UrgeSlider` from clinical/) | `tests/e2e/check-in.spec.ts` | spec §6.2 |
| 6.3 | Refresh Tools landing + detail | `apps/web-app/src/app/[locale]/tools/page.tsx` + `tools/[slug]/page.tsx` (new) | `tests/e2e/tools.spec.ts` | spec §6.5 |
| 6.4 | Refresh Journal — **wire `usePhiAudit` (PHI route per spec §7.6)** | `journal/page.tsx`, `journal/new/page.tsx`, `journal/[id]/page.tsx` (new); add `usePhiAudit('/journal')` to list page and `usePhiAudit('/journal/[id]')` to detail page | `tests/e2e/journal.spec.ts` (assert `/api/audit/phi-read` fires on view) | spec §6.3 + §7.6 |
| 6.5 | Refresh Assessments + take instrument + new history — **wire `usePhiAudit` on history detail (PHI route per spec §7.6)** | `assessments/page.tsx`, `assessments/[instrument]/page.tsx`, `assessments/history/[id]/page.tsx` (new); add `usePhiAudit('/assessments/history/[id]')` to history detail | `tests/e2e/assessments.spec.ts` (assert audit fires on history detail view) | spec §6.4 + §7.6 |
| 6.6 | Refresh Settings shell + 4 sub-pages **(smoke spec must cover Appearance theme toggle round-trip + Locale switcher round-trip — both are new wiring)** | `settings/page.tsx`, `settings/{account,notifications,privacy,appearance}/page.tsx` | new `tests/e2e/settings-smoke.spec.ts` covering theme toggle + locale switch | spec §6.6 |
| 6.7a | Refresh TopBar + SidebarNav + BottomNav + ThemeToggle + LocaleSwitcher + WordmarkSvg (nav primitives) | `components/{TopBar,SidebarNav,BottomNav,ThemeToggle,LocaleSwitcher,WordmarkSvg}.tsx` | covered by every screen's E2E | spec §5.4 |
| 6.7b | NotificationsDrawer (Sheet behavior + bell badge + unread count — separate concern from nav primitives) | `components/NotificationsDrawer.tsx` + `hooks/useNotificationCount.ts` (stub-fed) | new `tests/e2e/notifications-drawer.spec.ts` | spec §5.4, §6.6 |
| 6.8 | Refresh `/crisis` route — POLISH or REBUILD per Task 6.0 decision | `app/[locale]/crisis/page.tsx` (per spec §7.7: no `'use client'`, no `<Suspense>`, no client fetch, hotline data inlined at server-render, `tel:`/`sms:` server-rendered, JS-disabled functional); ESLint rule `discipline/no-llm-on-crisis-route` MUST pass on this route; SW precache entry covers this route (verified via Workbox `precache.js` glob from Chunk 3 task 3.2) | `tests/e2e/crisis.spec.ts` with `--javaScriptEnabled=false` assertion AND assertion that `tel:` anchors render server-side (visible in `view-source:`) | spec §5.1 + §7.7 |
| 6.9 | **Middleware update — preserve `/:locale/crisis(.*)` in PUBLIC_ROUTES + emit `X-Phi-Boundary: 1` on canonical PHI route list** | `src/middleware.ts` (clerkMiddleware wrapping `createMiddleware(routing)`); set `X-Phi-Boundary: 1` for: `/reports*`, `/assessments/history*`, `/journal*`, `/patterns*` (per spec §7.6 — note `/api/exports/fhir-r4` lives backend-side, not in this client middleware) | `tests/unit/middleware-routes.test.ts` with TWO regression guards: (1) `crisis_route_remains_in_public_routes_after_refactor` — fails if anyone removes `/:locale/crisis(.*)` from `PUBLIC_ROUTES` (CLAUDE.md non-negotiable #1); (2) `phi_routes_emit_boundary_header` — iterates the canonical PHI route list and asserts each emits the header | spec §7.6 + CLAUDE.md "common pitfalls" |
| 6.10 | Client-side `usePhiAudit` hook + `apiFetch` interceptor | `src/hooks/usePhiAudit.ts`, `src/lib/api.ts` | new spec `tests/e2e/phi-audit.spec.ts` (asserts `/api/audit/phi-read` is called for each PHI route from §7.6) | spec §7.6 |

**Per-task acceptance:**
- The screen renders in dark + light × en + ar without regression (visual smoke before merge)
- All nav components and any directional UI use logical properties (`ms-*`/`me-*`, `start`/`end`); Storybook story passes in `dir="rtl"` for `ar`/`fa`; ESLint `no-physical-tailwind-properties` rule from Chunk 2 fires on any regression
- E2E green for the touched spec; existing E2E selectors (data-testid) updated in the SAME PR as the screen refresh (per spec §10 Phase 3 requirement)
- Lint, typecheck, unit tests green
- For PHI screens (6.4, 6.5): audit hook wiring confirmed via E2E network assertion
- Visual review in Storybook (for components) before merging

### Phase 3 chunk-completion checklist

- [ ] Task 6.0 audit decision recorded in the 6.8 PR description
- [ ] All 6 existing screens refreshed (6.1–6.6)
- [ ] TopBar + SidebarNav + BottomNav refreshed (6.7a); NotificationsDrawer functional with bell badge + unread count (6.7b)
- [ ] `/crisis` route conforms to spec §7.7 (server component, inlined hotline, JS-disabled functional, ESLint rule passing, SW precached) — 6.8
- [ ] PHI middleware live + audited; `/:locale/crisis(.*)` regression test passing — 6.9
- [ ] PHI hook wired on Journal + Assessments-history detail; audit network call verified in E2E — 6.10
- [ ] `pnpm test:e2e` green for all existing specs + new settings-smoke + notifications-drawer + phi-audit specs

**Stop here. Run plan-document-reviewer.**

---

## Chunk 7: Phase 4 — New screens (6 surfaces)

**Time estimate:** 2 weeks.

**Pre-task: clinical-QA scheduling** — see R8 in spec §11. Pre-book reviewer slots for Companion + Reports + FHIR schema *before* this chunk starts.

**Pre-task: ESLint rule extension to companion route** — Before Task 7.4 begins, confirm the `discipline/no-llm-on-crisis-route` rule from Chunk 2 already covers `app/[locale]/companion/**` (it does, per Chunk 2 Task 2.4 fixtures). Run `pnpm lint` from `apps/web-app`; rule must be active before any file is created under `companion/`. Halt if the rule is not wired.

**Locale-parity gate (applies to every task in this chunk):** Every new screen ships translation keys in `packages/i18n-catalog/src/catalogs/{en,fr,ar,fa}.json` in the SAME PR as the screen. Non-EN locales carry `_meta.status: "draft"` until native review. The `localeFallback_draft_key_falls_back_to_en_silently` Vitest gate in `clinical-contracts.test.ts` (from Chunk 5 §5.12) flips from `it.todo` to live in this chunk and asserts no untranslated key surfaces a missing-translation placeholder to users.

| Order | Task | Files | Dependencies / blockers |
|-------|------|-------|-------------------------|
| 7.1 | Reports landing + detail (incl. **FHIR R4 export download action** per spec §5.5 + CLAUDE.md cross-ref `Docs/Technicals/13_Analytics_Reporting.md`) | `app/[locale]/reports/page.tsx`, `reports/[period]/page.tsx`; `hooks/useReports.ts`; `components/FhirExportButton.tsx` (calls `/api/exports/fhir-r4`, requires step-up auth — UI handles 401-with-stepUp-required response); `tests/e2e/reports.spec.ts`; locale catalog keys for `reports.*` in en/fr/ar/fa | clinical-QA on RCIDelta interpretation; FHIR schema sign-off (parallel with implementation); step-up re-auth flow available |
| 7.2 | Patterns landing + detail — **note: PatternsPreviewTile (small dashboard summary) was built in Chunk 6 task 6.1; THIS task uses the full `InsightCard` from Chunk 5 §5.10 in a list/detail view** | `app/[locale]/patterns/page.tsx`, `patterns/[id]/page.tsx`; `hooks/usePatterns.ts`; `tests/e2e/patterns.spec.ts`; locale catalog keys for `patterns.*` | InsightCard from Chunk 5; do NOT reuse PatternsPreviewTile here |
| 7.3 | Library landing + category + article | `app/[locale]/library/page.tsx`, `library/[category]/page.tsx`, `library/[category]/[slug]/page.tsx`; `hooks/useLibrary.ts`; `tests/e2e/library.spec.ts`; locale catalog keys for `library.*` | content team supplies categories + initial article slugs (5 categories per spec §5.5) |
| 7.4 | Companion — **route is LLM-prohibited (spec §7.7); ESLint rule confirmed live via pre-task above** | `app/[locale]/companion/page.tsx`; `hooks/useCompanion.ts`; `tests/e2e/companion.spec.ts`; locale catalog keys for `companion.*` | CompassionTemplate from Chunk 5; `companionRoute_has_zero_llm_imports` gate (in `clinical-contracts.test.ts` §5.12) flips from `it.todo` to live in this chunk; clinical-QA review on copy + flow |
| 7.5 | Notifications **PREFERENCES UI ONLY** (`/settings/notifications` config screen + bell-drawer Sheet content). **Push handler is explicitly OUT OF SCOPE here — deferred to Chunk 8 Phase 5 task 8.2 pending R3 security review.** Do NOT extend `sw.js` in this task; Chunk 8 §8.2 owns that. | `app/[locale]/settings/notifications/page.tsx` (shell from 6.6); `components/NotificationsDrawer.tsx` (shell from 6.7b) — fill out content here; `hooks/useNotifications.ts`; locale catalog keys for `notifications.*` | none — pure UI/preferences; no SW changes |
| 7.6 | Appearance settings (theme + locale + motion) | `app/[locale]/settings/appearance/page.tsx`; locale catalog keys for `appearance.*` | uses `useTheme` from `next-themes` (Chunk 1), `LocaleSwitcher` (Chunk 6 §6.7a), and a new "Reduce ambient motion" toggle that flips `[data-ambient-motion]` on `<html>` (the `useReducedMotion` hook from Chunk 1 §1.5 already reads this attribute) |

**Per-task acceptance:**
- E2E covers golden path + ≥2 edge cases
- A11y: axe-core scan zero serious/critical
- Stub data (via `useStubs` from Chunk 3 §3.1) sufficient to render every state in Storybook + dev mode
- Locale catalog parity: keys exist in `en.json`, `fr.json`, `ar.json`, `fa.json`; non-EN at `_meta.status: "draft"`; locale-fallback test green
- Logical properties only (`ms-*`/`me-*`); RTL story for `ar`/`fa` passes visual review

### Phase 4 chunk-completion checklist

- [ ] All **6 new screens** shipped and reachable from nav (7.1 Reports, 7.2 Patterns, 7.3 Library, 7.4 Companion, 7.5 Notifications-prefs, 7.6 Appearance)
- [ ] Clinical-QA sign-off on Companion copy and Reports interpretation
- [ ] FHIR R4 export schema approved + endpoint stubbed; FhirExportButton wired; step-up flow exercised in E2E
- [ ] axe-core matrix expanded to cover new routes
- [ ] No `'use client'` in `companion/page.tsx`; no LLM imports anywhere under `app/[locale]/companion/**` (ESLint rule + `companionRoute_has_zero_llm_imports` Vitest gate both green)
- [ ] Locale catalog parity check passes (en/fr/ar/fa all have the new screen keys; draft-fallback test green)
- [ ] Push notification handler **NOT** added in this chunk — confirmed by `git diff` showing no edits to `public/sw.js` or related Workbox files

**Stop here. Run plan-document-reviewer.**

---

## Chunk 8: Phases 5–7 — Cross-cutting + polish + launch

**Time estimate:** 3 weeks (Phase 5 = 1, Phase 6 = 1, Phase 7 = 1).

### Phase 5 tasks (Week 7) — cross-cutting + offline

| Task | Files | Notes |
|------|-------|-------|
| 8.1 SW offline check-in queue | `src/lib/offline-queue.ts`, `src/hooks/useOfflineQueue.ts`, `tests/e2e/offline-checkin.spec.ts` | IndexedDB (idb library); 60s server-side dedup window |
| 8.2 SW push handler | `public/sw.js` (extend), `src/lib/push.ts` | **Security review per R3 BEFORE implementation** — Clerk step-up auth pattern; payload metadata only |
| 8.3 SW `/crisis` precache extended to all shipping locales | `workbox-config.cjs` | Update glob to `**/[locale]/crisis/**` for all 3 locales |
| 8.4 Performance work to budgets | various | Per-route bundle: Dashboard < 180KB, Reports < 220KB, Crisis < 90KB. LCP < 2.0s on Dashboard (mid-tier mobile) |
| 8.5 OfflineIndicator in TopBar | `components/OfflineIndicator.tsx` | Badge + expandable list of pending sync items |

### Phase 6 tasks (Week 8) — polish + clinical QA

| Task | Files | Notes |
|------|-------|-------|
| 8.6 Manual NVDA + JAWS + VoiceOver pass on top-4 surfaces | (no code change unless bugs found) | Surface bugs as separate PRs |
| 8.7 Persian (`fa`) visual review | (catalog updates if needed) | Vazirmatn render at every breakpoint |
| 8.8 Clinical QA on Companion + Crisis + safety items | (gate; copy fixes if needed) | Sign-off recorded in `docs/superpowers/specs/2026-04-26-web-app-frontend-design.md` §13 checklist |
| 8.9 Chromatic full sign-off | (UI review) | All baselines approved |
| 8.10 Performance audit | Lighthouse + WebPageTest matrix | Each route × {dark, light} × {en, ar, fa} |
| 8.11 Clerk metadata theme persistence | extend the `next-themes` integration | Mirror localStorage to Clerk `unsafeMetadata` so theme follows user across devices (use a small `useEffect` watcher on the `useTheme()` value) |

### Phase 7 tasks (Week 9) — launch

| Task | Notes |
|------|-------|
| 8.12 Verify rollback armed for `web-app` deploy pipeline (BEFORE canary) | Confirm the auto-rollback trigger (per `Docs/Technicals/08_Infrastructure_DevOps.md` §8) is wired specifically for the `web-app` surface — error-rate threshold, LCP regression threshold, and audit-stream-coverage drop all trigger automatic rollback; record the dashboard URL + threshold values in the canary PR. |
| 8.13 Canary deploy 10% × 10min | per `Docs/Technicals/08_Infrastructure_DevOps.md` §8 |
| 8.14 Monitor: error rate, LCP per route, axe-core production scan, PHI audit-stream coverage | Grafana dashboards (separate spec) |
| 8.15 Full traffic shift | Auto if canary green |
| 8.16 v1.1 backlog captured | Cut: Reports DataTable, BreadCrumbs, CommandMenu (Cmd-K), ContextMenu, SplitView, dedicated ErrorBoundary, web-clinician/web-enterprise visual refresh |

### Phases 5–7 chunk-completion checklist

- [ ] Production canary green; full shift completed
- [ ] All 9 Definition-of-Done items from spec §13 checked
- [ ] v1.1 backlog committed to a follow-up spec

**Final review: run plan-document-reviewer one more time on the full plan as a sanity sweep.**

---

## Risks during execution (mirror of spec §11 + execution-specific)

- **R-exec-1: Phase 0 token churn breaks visual-regression baselines mid-Chunk 4.** Mitigation: the Chromatic baseline is set AFTER Chunk 4 completes (every primitive in the new system) — not after Phase 0. Until then, visual regression is informational, not blocking.
- **R-exec-2: Clinical-QA latency stalls Chunk 7.** Mitigation: pre-book reviewer slots; draft Companion templates + Reports schema during Chunks 1–5 so review can begin in parallel.
- **R-exec-3: SW push handler security review (R3) blocks Chunk 8 Phase 5.** Mitigation: kick off the security review during Phase 4 (Chunk 7) so handler implementation in Phase 5 doesn't wait.
- **R-exec-4: Existing E2E tests rely on old DOM selectors.** Mitigation: each Phase 3 task explicitly bundles E2E updates with the screen refresh in the same PR (per spec §10).
- **R-exec-5: `pnpm i18n:status` fails because new screen keys land in `en.json` only.** Mitigation: every new screen ships parallel `_meta: {status: "draft"}` keys in `fr.json`, `ar.json`, `fa.json` in the same PR (CLAUDE.md guidance on cross-locale catalog edits).
- **R-exec-6: Backend preconditions for Chunk 5 not met.** Mitigation: the precondition checklist at the top of the plan halts work and surfaces to the user — do not invent the backend.

---

## Working agreements during execution

- **One commit per task** at minimum; one commit per logical step inside Phase 0 (TDD red → green → commit pattern).
- **Never silence a custom ESLint rule.** If a rule fires, fix the calling code.
- **Never paraphrase clinical content.** PHQ-9, GAD-7, AUDIT-C, C-SSRS items are quoted verbatim from the source. Translation deficit → fall back to `en` silently (next-intl override).
- **Never call the LLM from `crisis/` or `companion/`.** The ESLint rule from Chunk 2 enforces this; do not add `eslint-disable` comments to bypass.
- **Cross-doc updates not optional.** When this plan touches a first-class system (theme, locale, PHI), sweep the relevant `Docs/Technicals/` files in the same PR (CLAUDE.md guidance).
- **Plan-document-reviewer at every chunk boundary.** Do not skip.

---

## Definition of Done for the plan

The plan is complete when:

1. ✅ All 8 chunks reviewed by plan-document-reviewer and approved
2. ☐ User reviews this plan
3. ☐ Phase 0 (Chunks 1–3) execution begins under `superpowers:subagent-driven-development` (or `superpowers:executing-plans` if subagents not available)
4. ☐ Each chunk lands its commits and re-runs plan-document-reviewer at the boundary

The implementation is complete when spec §13 Definition of Done is satisfied (canary green, all gates passing, clinical-QA sign-off).
