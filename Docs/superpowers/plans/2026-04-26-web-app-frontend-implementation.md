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

- [ ] Write the test — at least 6 cases:
  - `<div>{phq9Score}</div>` → flagged
  - `<div>{score}</div>` → flagged
  - `<div>{formatNumberClinical(score)}</div>` → ok
  - `<div className="clinical-number">{score}</div>` → ok
  - `<div>{regularCount}</div>` → ok (not clinical)
  - `<span>{user.intensity}</span>` → flagged (member-expression form)
- [ ] Run to fail.
- [ ] Implement.
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

- [ ] Write the test — fixtures with paths set via the rule-tester `filename` option. ≥4 invalid (one each from crisis/companion × esm/cjs) + ≥2 valid (same imports from non-crisis paths).
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
- [ ] `pnpm lint` passes from `apps/web-app`
- [ ] All three rules each have ≥6 unit-test cases

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
- [ ] Write `workbox-config.cjs` that precaches the crisis page route + the safety-directory JSON for the *current locale* only (Phase 0 scope per spec §8.5). Use `precacheAndRoute` with a glob for the default locale's `/crisis` HTML.
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
- [ ] Add the `chromatic` script: `"chromatic": "chromatic --exit-zero-on-changes"`.
- [ ] Add a GitHub Actions workflow `apps/web-app/.github/workflows/chromatic.yml` (or amend an existing repo-level workflow) that runs Chromatic on PRs touching `apps/web-app/` or `packages/design-system/`.
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

## Chunk 4: Phase 1 — Generic primitives (28 components)

**Time estimate:** 1 week.

**Approach:** TDD per component. Each primitive lands as: failing test → implementation → Storybook story (4 variants: dark+light × en+ar) → commit. The template is identical for each; the engineer follows it 28 times.

**Component template (apply to each):**

````markdown
### Task 4.X: <ComponentName>

**Files:**
- Create: `packages/design-system/src/primitives/<ComponentName>.tsx`
- Create: `packages/design-system/src/primitives/__tests__/<ComponentName>.test.tsx`
- Create: `packages/design-system/src/primitives/__stories__/<ComponentName>.stories.tsx`

- [ ] Write failing test: rendered name, props pass-through, accessible role, RTL behavior if applicable
- [ ] Run to fail
- [ ] Implement (Radix wrapper if applicable; tokens via Tailwind class names that map to CSS vars)
- [ ] Add story: dark + light × en + ar variants
- [ ] Run to pass; visual smoke in Storybook
- [ ] Commit
````

**The 16 generic primitives, in dependency order:**

| Order | Component | Notes / dependencies |
|-------|-----------|----------------------|
| 4.1 | `Button` | extracted from current `web.tsx` |
| 4.2 | `Card` | |
| 4.3 | `Input` | |
| 4.4 | `Textarea` | |
| 4.5 | `Spinner` | |
| 4.6 | `Divider` | |
| 4.7 | `Badge` | |
| 4.8 | `Skeleton` | shimmer suppressed under reduced motion |
| 4.9 | `Tooltip` | Radix Tooltip wrap |
| 4.10 | `ProgressRing` | |
| 4.11 | `Slider` | Radix Slider wrap; logical-property aware (RTL drag direction inverts) |
| 4.12 | `RadioGroup` | Radix |
| 4.13 | `CheckboxGroup` | composition of Radix Checkboxes |
| 4.14 | `Switch` | Radix |
| 4.15 | `Select` | Radix |
| 4.16 | `TabNav` | Radix Tabs |

**Then the layout primitives (depend on 4.1–4.16):**

| Order | Component | Notes |
|-------|-----------|-------|
| 4.17 | `Dialog` | Radix Dialog wrap |
| 4.18 | `Sheet` | Radix Dialog (side variant) |
| 4.19 | `Toast` | Radix Toast |
| 4.20 | `PageShell` | the page-level layout shell |
| 4.21 | `WizardShell` | multi-step shell with save-and-resume |

**Then the data primitives (depend on Visx — install in 4.22 first):**

| Order | Component | Notes |
|-------|-----------|-------|
| 4.22 | `Sparkline` | **Visx-backed; preserves existing prop contract** (`data`, `color`, `strokeWidth`); update `MoodSparkline` consumer in same PR |
| 4.23 | `Stat` | hero number + label + delta; uses `formatNumberClinical` for clinical context |
| 4.24 | `Trend` | Stat + Sparkline composition |
| 4.25 | `RingChart` | multi-segment ProgressRing extension |
| 4.26 | `BarChart` | Visx |
| 4.27 | `Banner` | |
| 4.28 | `EmptyState` | |

**Sub-task at the end of Chunk 4:**

### Task 4.29: Delete the legacy `primitives.tsx` and `web.tsx`

**Files:**
- Delete: `apps/web-app/src/components/primitives.tsx`
- Delete: `packages/design-system/src/primitives/web.tsx`
- Delete: `packages/design-system/src/primitives/web.test.ts`
- Modify: `packages/design-system/src/index.ts` (re-export from new per-component files via `primitives/index.ts`)
- Modify: every consumer that imports from the old paths (use Grep to find them)

- [ ] Grep for old import paths: `grep -r "design-system/src/primitives/web" D:/Psycho/apps D:/Psycho/packages`
- [ ] Update each consumer to import from the new per-component path or from the package root (`@disciplineos/design-system`)
- [ ] Run full test + lint + typecheck
- [ ] Commit

### Phase 1 chunk-completion checklist

- [ ] All 28 generic primitives ship with tests + stories + Chromatic baseline approved
- [ ] No remaining imports from the old `web.tsx` or `primitives.tsx`
- [ ] Storybook story shelf shows all 28, each in 4 variants
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green from every package
- [ ] No regression in existing E2E

**Stop here. Run plan-document-reviewer.**

---

## Chunk 5: Phase 2 — Clinical primitives (8 components) + clinical mirrors

**Time estimate:** 1 week.

**Preconditions** (re-check before starting, per top-of-plan precondition list):
- `shared-rules/relapse_templates.json` exists
- `discipline/clinical/` Python module exposes the deterministic-selection function
- `services/api/src/discipline/safety/emergency_numbers.py` exists

**Approach:** Same TDD-per-component template as Chunk 4. The clinical contracts (Latin digits, deterministic render, no LLM) are the *test names*: every clinical primitive's test file includes ≥1 test that asserts the rule. Examples are listed in spec §9.2.

| Order | Component | Critical contract tests |
|-------|-----------|-------------------------|
| 5.1 | `formatters.ts` (re-export `formatNumberClinical` from `@disciplineos/i18n-catalog`) | `formatNumberClinical_returns_latin_digits_in_fa_locale`, `formatNumberClinical_returns_latin_digits_in_ar_locale` |
| 5.2 | `clinical-mirrors.ts` (the `estimateStateClientMirror` function) | `estimateStateClientMirror_parity_with_server_for_all_intensities_0_to_10` (parameterized over 0–10) |
| 5.3 | `BreathingPulse` (motion) | reads `useReducedMotion`; suppressed under either signal |
| 5.4 | `ResilienceRing` | `dashboard_resilienceRing_value_never_decrements_across_renders` (Rule #3) |
| 5.5 | `UrgeSlider` | `urgeSlider_value_renders_latin_in_arabic_context` (Rule #9) |
| 5.6 | `SeverityBand` | `severityBand_uses_pinned_phq9_thresholds_not_hand_rolled` (imports `PHQ9_SEVERITY_THRESHOLDS` from a TS mirror of the backend constant; Vitest gate ensures the constant is imported, not redefined) |
| 5.7 | `RCIDelta` | follows Jacobson & Truax 1991; ●●●/●●○/●○○ scale; tested across all transitions |
| 5.8 | `CompassionTemplate` | `compassionTemplate_renders_verbatim_no_interpolation` (Rule #4); `relapseSurface_does_not_contain_streak_reset_copy`; consumes JSON template; deterministic |
| 5.9 | `CrisisCard` | `crisisCard_drops_entries_older_than_90_days` (Rule #10); `crisisCard_falls_back_to_icasa_when_all_local_stale` |
| 5.10 | `InsightCard` | dismiss/snooze/acknowledge lifecycle from Sprint 108 contract; tested across all state transitions |
| 5.11 | `safety/emergency-numbers.ts` constant + Vitest cross-stack equivalence | `frontend_emergency_numbers_match_backend_byte_equivalence` (CI runs `python -m json.dumps` on backend file, `JSON.stringify` on frontend file, byte-equal) |

### Task 5.12: Clinical-contracts cross-cutting test file

**Files:**
- Create: `apps/web-app/tests/unit/clinical-contracts.test.ts`

A single Vitest file that aggregates the cross-cutting gates that aren't per-component — e.g., `phi_routes_emit_boundary_header` (will pass once Chunk 6 ships middleware), `crisisRoute_has_zero_llm_imports` (works against the source tree), `companionRoute_has_zero_llm_imports`, `localeFallback_draft_key_falls_back_to_en_silently`.

Some gates may be marked `it.todo` until the prerequisite chunk ships; the file documents the contract.

- [ ] Write the file. Use `import.meta.glob('**/app/**/{crisis,companion}/**/*.{ts,tsx}')` to enumerate routes for the LLM-import gate.
- [ ] Run; some pass, some `todo`. Commit.

### Phase 2 chunk-completion checklist

- [ ] All 11 clinical tasks land with tests
- [ ] Storybook stories for clinical primitives in 4 variants
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green
- [ ] Clinical-contracts test file exists and passes for the gates that don't require Chunk 6+

**Stop here. Run plan-document-reviewer.**

---

## Chunk 6: Phase 3 — Existing screens refresh

**Time estimate:** 1 week.

**Approach (task per existing screen):** for each of the 6 existing screens, the task is "refresh onto the new system, no IA change, update E2E selectors in the same PR." Split per screen so each PR is small.

| Order | Task | Screen | Files modified | E2E updated |
|-------|------|--------|----------------|-------------|
| 6.1 | Refresh Dashboard | `apps/web-app/src/app/[locale]/page.tsx` + `components/StreakWidget.tsx`, `StateIndicator.tsx`, `PatternCard.tsx`, `QuickActions.tsx` | `tests/e2e/dashboard.spec.ts` |
| 6.2 | Refresh Check-in | `apps/web-app/src/app/[locale]/check-in/page.tsx` (use `UrgeSlider`) | `tests/e2e/check-in.spec.ts` |
| 6.3 | Refresh Tools landing + detail | `apps/web-app/src/app/[locale]/tools/page.tsx` + `tools/[slug]/page.tsx` (new) | `tests/e2e/tools.spec.ts` |
| 6.4 | Refresh Journal | `journal/page.tsx`, `journal/new/page.tsx`, `journal/[id]/page.tsx` (new) | `tests/e2e/journal.spec.ts` |
| 6.5 | Refresh Assessments + take instrument + new history | `assessments/page.tsx`, `assessments/[instrument]/page.tsx`, `assessments/history/[id]/page.tsx` (new) | `tests/e2e/assessments.spec.ts` |
| 6.6 | Refresh Settings shell + 4 sub-pages | `settings/page.tsx`, `settings/{account,notifications,privacy,appearance}/page.tsx` | settings has no E2E currently; add a smoke spec |
| 6.7 | New TopBar + SidebarNav refresh + BottomNav refresh + NotificationsDrawer + ThemeToggle + LocaleSwitcher + WordmarkSvg | `components/{TopBar,SidebarNav,BottomNav,NotificationsDrawer,ThemeToggle,LocaleSwitcher,WordmarkSvg}.tsx` | covered by every screen's E2E |
| 6.8 | Refresh `/crisis` route (POLISH-OR-REBUILD per spec §5.1) | `app/[locale]/crisis/page.tsx` — verify it is a Server Component; if it uses `'use client'`, rewrite as Server Component | `tests/e2e/crisis.spec.ts` (add `--javaScriptEnabled=false` assertion) |
| 6.9 | Middleware: emit `X-Phi-Boundary: 1` on the canonical PHI route list | `src/middleware.ts` | `tests/unit/middleware-routes.test.ts` |
| 6.10 | Client-side `useAuditPhi` hook + `apiFetch` interceptor | `src/hooks/useAuditPhi.ts`, `src/lib/api.ts` | new spec `tests/e2e/phi-audit.spec.ts` (asserts `/api/audit/phi-read` is called) |

**Per-task acceptance:**
- The screen renders in dark + light × en + ar without regression
- E2E green for the touched spec
- Lint, typecheck, unit tests green
- Visual review in Storybook (for components) before merging

### Phase 3 chunk-completion checklist

- [ ] All 6 existing screens refreshed
- [ ] TopBar + sidebar + bottom-nav refreshed; NotificationsDrawer functional (bell triggers Sheet)
- [ ] PHI middleware live + audited
- [ ] `pnpm test:e2e` green for all existing specs

**Stop here. Run plan-document-reviewer.**

---

## Chunk 7: Phase 4 — New screens

**Time estimate:** 2 weeks.

**Pre-task: clinical-QA scheduling** — see R8 in spec §11. Pre-book reviewer slots for Companion + Reports + FHIR schema *before* this chunk starts.

| Order | Task | Files | Dependencies / blockers |
|-------|------|-------|-------------------------|
| 7.1 | Reports landing + detail | `app/[locale]/reports/page.tsx`, `reports/[period]/page.tsx`; `hooks/useReports.ts`; `tests/e2e/reports.spec.ts` | clinical-QA on RCIDelta interpretation; FHIR schema sign-off (parallel with implementation) |
| 7.2 | Patterns landing + detail | `app/[locale]/patterns/page.tsx`, `patterns/[id]/page.tsx`; `hooks/usePatterns.ts`; `tests/e2e/patterns.spec.ts` | InsightCard from Chunk 5 |
| 7.3 | Library landing + category + article | `app/[locale]/library/page.tsx`, `library/[category]/page.tsx`, `library/[category]/[slug]/page.tsx`; `hooks/useLibrary.ts`; `tests/e2e/library.spec.ts` | content team supplies categories + initial article slugs (5 categories per spec §5.5) |
| 7.4 | Companion | `app/[locale]/companion/page.tsx`; `hooks/useCompanion.ts`; `tests/e2e/companion.spec.ts` | CompassionTemplate from Chunk 5; `companionRoute_has_zero_llm_imports` gate green; clinical-QA review on copy + flow |
| 7.5 | Notifications config (`/settings/notifications`) + bell-drawer Sheet content | `app/[locale]/settings/notifications/page.tsx` (already created in 6.6 shell); `components/NotificationsDrawer.tsx` (already created in 6.7) — fill out content here | `hooks/useNotifications.ts` |
| 7.6 | Appearance settings (theme + locale + motion) | `app/[locale]/settings/appearance/page.tsx` | uses `useTheme` from `next-themes`, `LocaleSwitcher`, and a new "Reduce ambient motion" toggle that flips `[data-ambient-motion]` on `<html>` |

**Per-task acceptance:**
- E2E covers golden path + ≥2 edge cases
- A11y: axe-core scan zero serious/critical
- Stub data sufficient to render every state in Storybook + dev mode

### Phase 4 chunk-completion checklist

- [ ] All 5 new screens shipped and reachable from nav
- [ ] Clinical-QA sign-off on Companion copy and Reports interpretation
- [ ] FHIR R4 export schema approved + endpoint stubbed
- [ ] axe-core matrix expanded to cover new routes
- [ ] No `'use client'` in `companion/page.tsx`; no LLM imports anywhere under that route

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
| 8.12 Canary deploy 10% × 10min | per `Docs/Technicals/08_Infrastructure_DevOps.md` §8 |
| 8.13 Monitor: error rate, LCP per route, axe-core production scan, PHI audit-stream coverage | Grafana dashboards (separate spec) |
| 8.14 Full traffic shift | Auto if canary green |
| 8.15 v1.1 backlog captured | Cut: Reports DataTable, BreadCrumbs, CommandMenu (Cmd-K), ContextMenu, SplitView, dedicated ErrorBoundary, web-clinician/web-enterprise visual refresh |

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
