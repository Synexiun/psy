# Web App Frontend Design — "Quiet Strength"

- **Date:** 2026-04-26
- **Surface:** `apps/web-app` (authenticated user app)
- **Status:** Design spec — pending implementation
- **Owner:** Product + Design (this spec) → Engineering (implementation per `writing-plans`)
- **Related docs:** `Docs/Technicals/16_Web_Application.md`, `Docs/Technicals/15_Internationalization.md`, `Docs/Technicals/13_Analytics_Reporting.md`, `Docs/Technicals/14_Authentication_Logging.md`, `Docs/bUSINESS/09_Brand_Positioning.md`

---

## 1 — Context & goals

`apps/web-app` is the authenticated user app — one of five Next.js surfaces (`web-marketing`, `web-app`, `web-clinician`, `web-enterprise`, `web-crisis`). It is currently functional but visually generic: blue brand, light-only mode, emoji icons, dashboard-only IA. The backend exposes 18 routers; only 7 have user-facing surfaces today.

**Goals for this design pass:**

1. **Visual identity transformation** — replace the generic blue/light system with a brand that signals clinical-grade restraint *and* compassionate warmth. The brand register is "Quiet Strength" — disciplined like Oura, warm like Reframe, restrained like Apple Health.
2. **IA expansion to surface backend value** — five new screens (Reports, Notifications, Pattern detail, Content library, Relapse Companion) close gaps where the backend ships value the user can't see.
3. **Polish of existing screens** — six existing surfaces (Dashboard, Check-in, Tools, Journal, Assessments, Settings) refreshed onto the new system.
4. **RTL discipline from day one** — `en + ar + fa` ship in v1, `fr` follows. Every component pays the logical-properties tax at birth.
5. **Clinical contracts enforced at code level** — Latin digits (Rule #9), no-paraphrase clinical content (Rule #8), 90-day safety directory freshness (Rule #10), deterministic crisis paths (Rule #1), compassion-first relapse copy (Rule #4) — all enforced via custom ESLint rules + Vitest gates, not just review discipline.

**Non-goals:**
- Light mode redesign (light is shipped, but dark is the brand-defining default)
- `web-clinician` / `web-enterprise` redesign (downstream — separate spec when those surfaces are tackled)
- Mobile app (`apps/mobile`) — separate React Native design pass
- New backend modules — this is purely the front of existing capabilities

---

## 2 — Locked decisions

The following gates were closed during brainstorming. They are foundational and not re-litigated here.

| Gate | Choice | Rationale |
|------|--------|-----------|
| **Scope** | Full transformation (visual + IA expansion + polish), web-app only | Half-measure visual updates without IA work would leave 11 of 18 backend modules invisible to users |
| **Brand register** | ① "Quiet Strength" — disciplined + warm, dark-first, bronze + teal + serif numerals | Resolves the bedrock tension of a product called "Discipline" with a Rule #4 mandate for compassion-first copy |
| **Locales v1** | en + ar + fa (RTL parity day one); fr in v1.1 | RTL is the load-bearing decision; building components RTL-correct from birth is far cheaper than retrofitting |
| **Icon system** | Lucide base + ~12 custom signature icons | Lucide handles utility (chevrons, search, settings); custom-drawn icons carry brand only where users *feel* them — line-style for utility states, solid bronze for achievement |
| **IA scope v1** | 5 new surfaces + 6 polished existing = 11 v1 screens | Reports earns retention. Notifications enables intervention loop. Pattern detail closes Sprint 108 debt. Content library says "we teach." Companion is the moral-test surface for Rule #4 |
| **Dark-mode timing** | Dark default + light opt-in, both v1, manual toggle in Settings | Dark is the brand identity; light respects accessibility and morning/sunlit-context users; ~1.4× the design work, not 2× |
| **Display serif** | Fraunces variable, SOFT 30 / WONK 0 default | Free (SIL OFL), variable (single ~60KB woff2), SOFT axis lets us dial warmth contextually (SOFT 0 for clinical scores, SOFT 60 for compassion copy) |

---

## 3 — Brand foundation

### 3.1 Color tokens

In `apps/web-app/src/app/globals.css` Tailwind v4 `@theme`. Dark is `:root`, light is `[data-theme="light"]`.

**Dark (primary):**

```css
--surface-primary:   hsl(220 25%  8%);   /* midnight, app bg */
--surface-secondary: hsl(220 22% 11%);   /* card */
--surface-tertiary:  hsl(220 20% 14%);   /* elevated / modal */
--surface-overlay:   hsl(220 25%  8% / 0.85);  /* modal scrim */

--ink-primary:       hsl( 28 15% 94%);   /* warm-stone body */
--ink-secondary:     hsl( 28 10% 75%);
--ink-tertiary:      hsl( 28  8% 55%);   /* captions, timestamps */
--ink-quaternary:    hsl( 28  8% 35%);   /* disabled / placeholder */

--accent-bronze:     hsl( 28 65% 55%);   /* primary CTA, achievement */
--accent-bronze-soft:hsl( 28 45% 35%);
--accent-teal:       hsl(173 35% 45%);   /* calm, urge-low, breathing */
--accent-teal-soft:  hsl(173 25% 25%);

--signal-warning:    hsl( 38 70% 55%);   /* mid-band urge / PHQ-9 moderate */
--signal-crisis:     hsl(355 65% 48%);   /* oxblood — T3/T4 only */

--border-subtle:     hsl(220 15% 18%);
--border-emphasis:   hsl(220 15% 28%);
```

**Light (derived — same hues, contrast-flipped):**

```css
[data-theme="light"] {
  --surface-primary:   hsl( 28 15% 97%);
  --surface-secondary: hsl( 28 12% 94%);
  --surface-tertiary:  hsl( 28 10% 90%);
  --ink-primary:       hsl(220 25% 12%);
  --ink-secondary:     hsl(220 18% 32%);
  --ink-tertiary:      hsl(220 12% 50%);
  --accent-bronze:     hsl( 28 70% 42%);  /* darker for AA on light */
  /* … */
}
```

Theme toggle persists via `localStorage` + Clerk user metadata (so it follows the user across devices). Default for new users: `prefers-color-scheme` from OS, falling back to dark.

### 3.2 Typography

- **Body**: `Inter` variable, weights 300–700, `font-feature-settings: 'cv11', 'ss01'` (single-storey `a`, slashed `0` — clinical legibility).
- **Display**: `Fraunces` variable, default `font-variation-settings: 'SOFT' 30, 'WONK' 0`. Override `'SOFT' 60` in CompassionTemplate (warmer); `'SOFT' 0` in clinical scores (restrained).
- **Arabic**: Inter falls back to `IBM Plex Sans Arabic` for Arabic glyphs (Inter is Latin-only).
- **Persian**: `Vazirmatn` (loaded only when `locale === 'fa'` to save 85KB woff2 on other locales).

Display serif applies to Latin glyphs only. Per Rule #9, clinical numbers stay Latin even in `ar`/`fa`, so Fraunces still renders the numbers in those locales.

**Type scale (fluid `clamp()`):**

```css
--text-display-2xl: clamp(3rem, 6vw, 4.5rem);   /* hero numbers (Day 47) */
--text-display-xl:  clamp(2.25rem, 4vw, 3.5rem); /* page titles */
--text-display-lg:  clamp(1.75rem, 3vw, 2.25rem);/* section heads */
--text-display-md:  1.5rem;                      /* card titles */
--text-body-lg:     1.125rem;                    /* primary body */
--text-body-md:     1rem;                        /* default body */
--text-body-sm:     0.875rem;                    /* captions */
--text-body-xs:     0.75rem;                     /* micro / metadata */
```

All hero numbers use Fraunces + `tabular-nums` + `.clinical-number` class (forces `direction: ltr`).

### 3.3 Motion

```css
--motion-instant:    75ms;    /* taps, ripples */
--motion-fast:       150ms;   /* hover, focus */
--motion-base:       250ms;   /* state transitions */
--motion-slow:       400ms;   /* page transitions, modal enter */
--motion-deliberate: 700ms;   /* hero reveals */

--ease-default:    cubic-bezier(0.4, 0, 0.2, 1);
--ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
--ease-accelerate: cubic-bezier(0.4, 0, 1, 1);
--ease-organic:    cubic-bezier(0.5, 0.05, 0.2, 1);  /* breathing pulse */
```

**Signature breathing pulse**: `scale(1 → 1.04)` + `opacity(0.95 → 1)` over 4s inhale + 4s exhale, infinite, `--ease-organic`. Applied to: ResilienceRing center number at rest, UrgeSlider thumb when untouched, tools-landing primary CTA at rest.

Reduced motion = `prefers-reduced-motion: reduce` OR Settings "Reduce ambient motion" toggle. Either disables ambient motion. Required-for-comprehension motion (chart drawing) degrades to 200ms fade, never fully off.

### 3.4 Voice

- Numbers do the work: "Day 47," not "You've maintained your streak for 47 days."
- Quiet compassion: "Today is a new day," not "Don't beat yourself up."
- Clinical neutrality: "PHQ-9: 12 — moderate. Talk to your clinician." Not therapized.
- Crisis is operational: "Call 988 now." No softening verbs in T3/T4 copy.

---

## 4 — Component system

### 4.1 Foundation

**Radix Primitives** for: Dialog, Popover, Switch, RadioGroup, Tabs, Toast, Tooltip, Slider. We re-skin every Radix primitive with our tokens. Reason: re-implementing focus traps and `aria-*` from scratch is the #1 way to ship inaccessible clinical software.

### 4.2 Three-tier package layout

```
packages/design-system/src/
  primitives/    # generic — Button, Card, Slider, RadioGroup, …
  clinical/      # NEW — primitives with clinical contracts
  motion/        # NEW — BreathingPulse + motion utilities
apps/web-app/src/components/  # app-specific compositions
```

The `clinical/` split is load-bearing: those primitives carry contractual rules (Latin digits via `formatNumberClinical`, deterministic render path, no LLM call site) that the linter can verify by directory. A `SeverityBand` outside `clinical/` is a code-review red flag.

### 4.3 Net-new primitives (28, v1 cut)

**Generic (9, mostly Radix wrappers):** Slider, RadioGroup, CheckboxGroup, Switch, Select, TabNav, Dialog, Sheet, Toast.

**Layout & shell (5):** PageShell, TopBar (theme toggle + locale + notifications bell), SidebarNav (refresh w/ Lucide + custom icons), BottomNav (refresh), WizardShell (assessment multi-step with save-and-resume).

**Data display (4):** Stat (hero number + label + delta), Trend (Stat + Sparkline composition), RingChart (multi-segment ProgressRing extension), BarChart (Visx-wrapped, instrument trends over time).

**Feedback (2):** Banner, EmptyState.

**Clinical (7) — `clinical/` directory:**

- `ResilienceRing` — dashboard hero. Concentric: outer = last-7-days check-in completion (segments), center = day count in Fraunces with breathing pulse. Renders day count via `formatNumberClinical`.
- `UrgeSlider` — replaces inline check-in slider. Thumb breathes at rest, gradient calm→bronze→crisis along track, value renders Latin via `formatNumberClinical`.
- `SeverityBand` — chip for PHQ-9/GAD-7/AUDIT-C bands. Color + Latin number + clinical-neutral label. Bands sourced from pinned threshold constants (`PHQ9_SEVERITY_THRESHOLDS` etc.) — never hand-rolled.
- `RCIDelta` — prior score → current score → significance flag (●●● / ●●○ / ●○○) per Jacobson & Truax 1991.
- `CompassionTemplate` — relapse companion renderer. Reads from `shared-rules/relapse_templates.json`, renders with Fraunces SOFT 60. No LLM, no string interpolation of user-supplied text.
- `CrisisCard` — T3/T4 escalation card. Oxblood. `tel:` + `sms:` + safety-directory pull from local copy with `verifiedAt` ≤ 90 days check at render. Never feature-flagged.
- `InsightCard` — pattern detail with dismiss / snooze (24h, 7d) / acknowledge lifecycle (Sprint 108 contract).

**Motion (1):** `BreathingPulse` — composable wrapper. Reads `prefers-reduced-motion` AND the separate "Reduce ambient motion" Settings flag.

### 4.4 Reused / extended (existing 11)

`Button`, `Card`, `Input`, `Textarea`, `Spinner`, `Divider`, `ProgressRing`, `Badge`, `Skeleton`, `Tooltip`, `Sparkline` — get token refresh (new HSL values, dark/light dual palette). No API changes; consumers untouched. `Sparkline` implementation swapped to Visx-based for parity with `BarChart`.

### 4.5 Cut to v1.1

`BreadCrumbs`, `CommandMenu` (Cmd-K), `DataTable` (Reports uses list views v1), `Popover` (Tooltip + Sheet cover most), `ContextMenu`, `SplitView`, dedicated `ErrorBoundary` (use inline patterns).

### 4.6 Storybook

Storybook ships with v1. Every primitive has stories in {dark, light} × {en, ar} = 4 baseline variants. Storybook is also where the design-system review against WCAG happens (axe-core integration runs against every story).

---

## 5 — IA, routes, navigation

### 5.1 Route map (Next.js App Router, all under `/[locale]/`)

```
/                              Dashboard (POLISH)
/check-in                      Check-in (POLISH)
/tools                         Tools landing (POLISH)
/tools/[slug]                  Tool detail (POLISH)
/journal                       Journal list (POLISH)
/journal/new                   New entry (POLISH)
/journal/[id]                  Entry detail (NEW)
/library                       Content library (NEW)
/library/[category]            Category list (NEW)
/library/[category]/[slug]     Article detail (NEW)
/reports                       Reports landing (NEW)
/reports/[period]              Report detail (week/month/6m) (NEW)
/patterns                      Patterns landing (NEW)
/patterns/[id]                 Pattern detail w/ lifecycle (NEW)
/assessments                   Assessments landing (POLISH)
/assessments/[instrument]      Take instrument (POLISH)
/assessments/history/[id]      Past session detail (NEW)
/companion                     Relapse companion (NEW — Rule #4)
/settings                      Settings landing (POLISH)
/settings/account              Identity (POLISH)
/settings/notifications        Push + nudge config (NEW)
/settings/privacy              Export/delete (POLISH)
/settings/appearance           Theme + locale + motion (NEW)
/crisis                        In-app crisis (POLISH)
```

`/crisis` is the *in-app* surface — authenticated, full design system, primary path. The `web-crisis` static-export app at `crisis.discipline.app` remains the SLO fallback. Both must always work; the in-app surface is what users hit 99% of the time. Per Rule #1 the in-app `/crisis` uses deterministic render — no LLM, hotline data inlined from local mirror at server-render time.

`typedRoutes: true` is already enabled; every route above gets a typed `Href` and any internal `Link` to a non-existent route fails the build.

### 5.2 Sidebar (desktop)

```
[Logo + wordmark]
─────────────────
TODAY
  ◐ Home          /
  ⊕ Check-in      /check-in
─────────────────
CARE
  ⊙ Tools         /tools
  ◫ Library       /library
─────────────────
REFLECT
  ◇ Journal       /journal
  ✦ Patterns      /patterns
  ▤ Reports       /reports
─────────────────
HEALTH
  ▦ Assessments   /assessments
─────────────────
                         [footer]
  ⚙ Settings      /settings
                         [pinned bottom]
  ◉ Crisis        /crisis  (oxblood, always visible)
```

Group labels (`TODAY`, `CARE`, etc.): Inter caption, tracked +0.08em, `--ink-tertiary`. Active item: bronze 4px left-border + `--surface-secondary` background + `--ink-primary` text. Hover: `--surface-secondary` + 150ms ease.

The 12 custom signature icons live here (placeholders shown above are illustrative; final SVGs drawn at 24px line + 24px solid bronze achievement variants).

### 5.3 Bottom nav (mobile)

5 items only (cognitive max for thumb-reach navigation):

```
[Home] [Check-in] [Tools] [Journal] [Crisis]
```

Crisis tab: 56px touch target (per design-system `safety.sosButtonMinTouchTargetPx`), oxblood, always-on.

The 6 other surfaces (Library, Reports, Patterns, Assessments, Companion, Settings) are reached via a hamburger in the TopBar that opens a Sheet — *not* via a "More" tab, because "More" tabs have ~40% non-discovery rate.

### 5.4 TopBar (every page)

```
[Hamburger (mobile only)]  [Wordmark]   [Bell] [LocaleSwitcher] [ThemeToggle] [Avatar→menu]
```

Bell shows unread notification count badge. Click → notifications drawer (Sheet). Wordmark centers on mobile, left-aligns on desktop. RTL: full mirror.

### 5.5 The eleven screens (one-line essence each)

| Screen | Question it answers | Hero element |
|--------|--------------------|--------------| 
| Dashboard | "Where am I right now?" | ResilienceRing (Day N, breathing pulse) |
| Check-in | "How am I doing?" | UrgeSlider |
| Tools | "What helps right now?" | 6 intervention archetype cards |
| Tool detail | "Walk me through this" | Step sequence + optional timer |
| Library | "What can I learn?" | Category cards + article list |
| Article | "Teach me about this" | Long-form rich text |
| Reports | "Am I getting better?" | Trend stat row + RCIDelta cards |
| Patterns | "What has the system noticed?" | InsightCard list |
| Pattern detail | "Why is the system telling me this?" | Evidence + suggested action + lifecycle |
| Assessments landing | "Where am I clinically?" | Instrument cards + due dates |
| Take instrument | "Item-by-item self-rating" | WizardShell + RadioGroup per item |
| Companion | "I slipped. Now what?" | Quiet headline + CompassionTemplate |
| Settings (×4 sub) | "Adjust my experience" | Sectioned forms |
| Crisis (in-app) | "I need help now" | Tel button + safety directory |

Library categories (5): Understanding addiction, CBT skills, Mindfulness basics, Sleep & recovery, Crisis & safety. Subject to clinical-content-team adjustment during Phase 4.

Companion has no nav entry. Reached from: (a) check-in submit when user reports a slip (ghost link, never auto), (b) Tools page "After a slip" card, (c) push notification deep link. Putting it in the main nav as a daily presence would re-traumatize.

---

## 6 — Hero screens (wireframe-fidelity)

### 6.1 Dashboard

```
┌─ TopBar ────────────────────────────────────────────────┐
│ [☰] [Wordmark]              [🔔] [en▾] [☾] [Avatar]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                       Day                               │
│                  ╭─────────╮                            │
│                  │    47   │  ← Fraunces 4xl,           │
│                  ╰─────────╯    breathing pulse,        │
│                     Stable        ResilienceRing        │
│                  [Check in →]    7-segment outer        │
│                                                         │
│  ┌─ State ─────┐ ┌─ Patterns ─────┐ ┌─ Last 7 ─────┐   │
│  │ HRV: mid    │ │ Top 2 insight  │ │ Sparkline    │   │
│  │ Sleep 6.2h  │ │ previews       │ │ 7 ●●●○●●●    │   │
│  │ Sparkline   │ │ All patterns → │ │ Open journal │   │
│  └─────────────┘ └────────────────┘ └──────────────┘   │
│                                                         │
│  [Check in]  [Use a tool]  [Open journal]              │
│                                                         │
│                                  [◉ Crisis] (sticky)   │
└─────────────────────────────────────────────────────────┘
```

ResilienceRing center: Fraunces, `clinical-number`, `tabular-nums`, breathing pulse 4s+4s. State word color: stable=`--accent-teal`, rising=`--signal-warning`, peak=`--signal-crisis`. Outer ring 7 segments = last-7-days completion. CTA below ring only present if no check-in today.

**Page enter motion**: cards stagger 60ms apart, `translateY(8px → 0)` over 400ms decelerate.

**Empty (new user)**: ring shows "Day 1". State card shows "Wear your device for 3 days to see signal".

**State card decision (recommended default)**: shows raw signal interpretation ("HRV: mid, sleep 6.2h") rather than soft framing ("Stable, with mild fatigue"). Clinically literate users want raw; over-soft erodes trust.

### 6.2 Check-in

```
       How are you feeling?       ← Fraunces 2xl, calm

       ╭───────────────────────╮
       │           4            │  ← value, Fraunces lg, Latin
       │                        │
       │ ─────────●──────────── │  ← UrgeSlider, 64px tall track
       │                        │     gradient teal→bronze→crisis
       ╰───────────────────────╯
        0                    10
       stable           peak urge

       What triggered this?
       [stress] [boredom] [...]  ← 8 chip tags, multi-select

       Notes (optional)
       ┌─────────────────────┐
       │                     │   220 / 280
       └─────────────────────┘

       [Cancel]    [Log check-in →]
```

UrgeSlider: 64px track, gradient along value axis, 32px thumb breathing-pulses at rest. On drag: pulse stops, value above bounces 1→1.04 per integer step. Latin via `formatNumberClinical` regardless of locale.

**Submit → state-conditional success:**
- `stable`: "Logged. Day 47." + "Back to home"
- `rising_urge`: above + "Try a 60-second tool →" (calm Button)
- `peak_urge`: above + inline `CrisisCard` + grounding script + crisis tel-link

**"I slipped — open companion" link** (recommended default): always present at bottom of success surface, ghost-styled. Quiet door, not a billboard.

**Offline path**: ApiError on submit → optimistic local save + Banner "Saved locally — will sync when online".

### 6.3 Companion

```
┌──────────────────────────────────────────────────────┐
│ [TopBar — minimal, no breadcrumb]                    │
│                                                      │
│                                              ← 16vh empty
│                                                      │
│         Today is a new day.        ← Fraunces 3xl
│                                       SOFT 60 (warm)
│                                                      │
│                                              ← 4vh
│         [CompassionTemplate body]   ← Fraunces lg
│         2–4 sentences, deterministic   SOFT 30
│         template from JSON              ink-secondary
│                                                      │
│                                              ← 6vh
│         What helps next:            ← Inter sm tracked
│                                                      │
│         ┌──────────────────────────┐                │
│         │ ⊕  Re-check in            │                │
│         │     A new urge reading.   │                │
│         └──────────────────────────┘                │
│         ┌──────────────────────────┐                │
│         │ ◇  Journal it             │                │
│         └──────────────────────────┘                │
│         ┌──────────────────────────┐                │
│         │ 〇  Breathe                │                │
│         └──────────────────────────┘                │
│                                                      │
│                                              ← 8vh
│         Day 47 — your resilience    ← centered,
│         hasn't reset.                  ink-tertiary
│                                                      │
└──────────────────────────────────────────────────────┘
```

CompassionTemplate sourced from `shared-rules/relapse_templates.json`, deterministic selection by `discipline/clinical/compassion_templates.py`. No LLM, no string interpolation. Three next-step actions are deterministic — predictability is calming after a slip; dynamic mystery is wrong register.

**Day-N footer is the load-bearing line.** Per Rule #3, resilience days never reset. The UI surfaces the DB invariant in plain language.

**Motion**: page enters with single 800ms fade. All other motion suppressed even with motion enabled in Settings.

**A11y**: focus moves to headline on mount; screen reader announces compassion text first.

### 6.4 Reports

```
Reports                       [Week | Month | 6 months]   ← TabNav
Week of Apr 20 – Apr 26

┌─ PHQ-9 ──┐  ┌─ GAD-7 ──┐  ┌─ Check-in ──┐  ┌─ Tools ──┐
│    8     │  │    6     │  │    86%       │  │   12     │
│  ↓ 3     │  │  ↓ 2     │  │  ↑ 14 vs prev│  │ sessions │
│ improved │  │ improved │  │              │  │          │
└──────────┘  └──────────┘  └──────────────┘  └──────────┘

Clinical instruments
┌─────────────────────────────────────────┐
│ PHQ-9       [moderate]   8 ↓3   ●●○     │  ← SeverityBand,
│ ▂▃▅▆▇▆▅      Reliable improvement       │     RCIDelta scale
│              Last: today                 │
└─────────────────────────────────────────┘

Patterns active this week
[3 InsightCard previews]   [All patterns →]

Tool usage
[BarChart by archetype]
"Breath was used most after rising urges.
 Median post-tool urge dropped from 6.2 → 4.1."   ← server-computed

Share with clinician
[Generate FHIR R4 export]   "Your data, your choice."
```

Stat numbers count up from 0 → value over 800ms on mount, deceleration ease. Skipped under reduced-motion.

SeverityBand pulls labels + thresholds from pinned constants (`PHQ9_SEVERITY_THRESHOLDS` per Kroenke 2001, etc.) — never hand-rolled.

RCIDelta scale: ●●● = "marked", ●●○ = "reliable", ●○○ = "no reliable change" per Jacobson & Truax 1991.

FHIR export triggers `requestDataExport({format: 'fhir-r4'})` → backend signed-URL → user downloads zip or emails self. Step-up auth required.

**Tool-efficacy on sparse data (recommended default)**: when data is too sparse for the period, show "Not enough data this week" rather than a low-confidence number. False confidence here erodes the entire Reports surface.

---

## 7 — Cross-cutting clinical contracts

### 7.1 RTL — logical properties everywhere

Tailwind v4 logical-property utilities: `ms-/me-`, `ps-/pe-`, `start-/end-`, `border-s/-e`, `text-start/-end`.

**Custom ESLint rule** `discipline/no-physical-tailwind-properties` bans `ml-*`, `mr-*`, `pl-*`, `pr-*`, `left-*`, `right-*`, `text-left`, `text-right`. CI fail. Exceptions list (BarChart, Sparkline) marked with `eslint-disable-next-line` + reason — those handle direction in their internal render logic because time-axis directionality is data-semantic.

**Per-component RTL behavior**:
- Sidebar mirrors right edge in RTL via `dir="rtl"`
- Lucide chevrons auto-mirror via CSS; custom icons either symmetric or marked `data-mirror-rtl`
- Sparkline / BarChart: time axis flows newest-to-oldest in inline-end direction (newest right in LTR, newest left in RTL — matches reading order)
- UrgeSlider: track flows logical start-to-end; LTR drag-right=higher, RTL drag-left=higher
- ResilienceRing: rotation stays clockwise in both directions (clinical/visual standard)

**Font loading per locale** (`apps/web-app/src/app/[locale]/layout.tsx`):
- `en`, `fr`: Inter + Fraunces
- `ar`: Inter + IBM Plex Sans Arabic + Fraunces (clinical numbers)
- `fa`: Vazirmatn + Fraunces (clinical numbers); Vazirmatn loaded only when `locale === 'fa'` (saves 85KB on other locales)

### 7.2 Latin digits (Rule #9) — three layers

**Server**: `discipline.shared.i18n.formatters.format_number_clinical(value, locale)` returns Latin-Western digits regardless of locale. Used in API responses for fields in `CLINICAL_NUMERIC_FIELDS` constant.

**Client**: `formatNumberClinical(value)` from `@disciplineos/i18n-catalog`. Wraps `new Intl.NumberFormat('en-US', { useGrouping: false }).format(value)` — never honors locale.

**CSS** — `.clinical-number`:

```css
.clinical-number {
  direction: ltr;
  unicode-bidi: embed;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}
```

Applied to ResilienceRing center, every SeverityBand number, every Stat hero number, RCIDelta numbers, UrgeSlider value, assessment item totals.

**Custom ESLint rule** `discipline/clinical-numbers-must-format` scans JSX for direct render of variables matching the clinical-numeric naming pattern (`*_total`, `intensity`, `score`, `phq*`, `gad*`, `audit_c_*`, `rci_*`) without `formatNumberClinical()` wrapper or `.clinical-number` className. CI fail.

**Boundary**: clinical = a number a clinician would compare across locales (PHQ-9 = 12). Body = a UI count ("3 patterns active") — those localize per locale.

### 7.3 Locale fallback (Rule #8) — silent

next-intl behavior overridden: when key has `_meta.status: "draft"` in target locale, `useTranslations()` falls back to `en` value silently. No "translation pending" badge.

CI report: `pnpm i18n:status` enumerates draft keys per locale; release gate requires all clinical-namespace keys (assessment items, crisis copy, intervention scripts, compassion templates) be `status: "released"` for shipping locales.

### 7.4 Accessibility — WCAG 2.2 AA + clinical extensions

Baseline:
- Contrast ≥ 4.5:1 body, ≥ 3:1 large + UI components
- Focus rings: 2px `--accent-bronze`, 2px offset, visible on dark + light
- Touch targets ≥ 44×44px (Crisis ≥ 56px per `safety.sosButtonMinTouchTargetPx`)
- Every interactive has accessible name; every status change `aria-live="polite"` (or `assertive` for crisis + suicidality flags)
- Form labels visible OR `aria-label`; placeholder never the label

Clinical extensions:
- **Assessment items announce verbatim** to screen readers (Kroenke 2001 etc. — paraphrase invalidates the score)
- **PHQ-9 item 9 > 0** (suicidality) — visible CrisisCard + `aria-live="assertive"` + focus auto-moves to Crisis CTA
- **Crisis surfaces `aria-live="assertive"`** for safety directory load
- **Reduced motion** = OS `prefers-reduced-motion: reduce` OR Settings "Reduce ambient motion" toggle. Both must be off for ambient motion (breathing pulse, page-enter stagger, count-up). Required-for-comprehension motion (chart drawing) degrades to 200ms fade.

Testing layered:
- Vitest unit: each component snapshots accessible name + role + `aria-*`
- Playwright + axe-core: every screen × {dark, light} × {en, ar} — zero serious/critical gates merge
- Manual: NVDA + JAWS + VoiceOver on top 4 surfaces per release
- Focus-trap testing via Radix + Playwright `Tab`-loop

### 7.5 Safety directory freshness (Rule #10) at render

`CrisisCard` render logic:
1. Read entries for user's country-locale from local mirror
2. Drop any entry where `verifiedAt + 90 days < today`
3. If empty → fall back to ICASA international list (locale-agnostic, hand-vetted)
4. If still empty → render pinned `EMERGENCY_NUMBERS` constant + "Call your local emergency number"

CI byte-equality between `packages/safety-directory/src/hotlines.json` and `services/api/data/safety/hotlines.json` is in place; freshness check runs at render (not build) because the 90-day boundary moves daily. Cached for 1h per session via TanStack Query.

### 7.6 PHI boundary (Rule #11)

PHI-reading surfaces: Reports, Assessments history, Journal, Pattern detail.

Server response sets `X-Phi-Boundary: 1`. Client: `apiFetch` interceptor reads header → fire-and-forget POST to `/api/audit/phi-read` with `{route, renderedAt, sessionId}`. Audit stream receives both the server-side fetch event and the client-side view event — required for the regulatory chain.

Client audit failure does not block UI. Failure raises a server-side alert via security stream.

### 7.7 Crisis path determinism (Rule #1)

`/crisis` route in web-app:
- Custom ESLint rule `discipline/no-llm-on-crisis-route`: import of `@disciplineos/llm-client` from `app/[locale]/crisis/**` fails CI
- No `<Suspense>` boundaries, no client-side data fetching — fully synchronous Server Component
- Hotline data inlined from local JSON at server-render time
- `tel:` and `sms:` rendered server-side, hydrated immediately, function with JS disabled
- Service worker pre-caches `/crisis` on first visit (workbox `precache`) for offline access

The `web-crisis` static-export surface remains the SLO-grade fallback. Both surfaces consume the same hotline mirror; both work with JS disabled.

---

## 8 — Data flow, error states, offline behavior

### 8.1 TanStack Query setup

```ts
// apps/web-app/src/lib/queryClient.ts
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      retry: 2,
      retryDelay: (n) => Math.min(1000 * 2 ** n, 30_000),
      refetchOnWindowFocus: 'always',
      refetchOnReconnect: 'always',
    },
    mutations: {
      retry: 1,
      onError: (e) => dispatchToTelemetry(e),
    },
  },
})
```

**Query key convention** — hierarchical, user-scoped:

```
['user', userId, 'streak']
['user', userId, 'patterns']
['user', userId, 'state']
['user', userId, 'check-ins', { limit: 30 }]
['user', userId, 'assessments']
['user', userId, 'assessments', sessionId]
['user', userId, 'reports', { period, startDate }]
['library', { category }]                 // user-agnostic, gcTime 30m
['library', 'article', slug]
['safety-directory', country, locale]     // local-mirror-backed
```

`queryClient.invalidateQueries({queryKey: ['user', userId]})` clears everything user-scoped on logout — single line.

### 8.2 Optimistic updates — used here, NOT used here

| Surface | Optimistic? | Reason |
|---------|-------------|--------|
| Check-in submit | ✅ | Urge-window latency matters; client mirror of `_intensity_to_state` pre-computes state for correct color |
| Pattern dismiss/snooze/ack | ✅ | Pure-state lifecycle; cheap to revert |
| Notification preference toggle | ✅ | UI-only state |
| Journal entry save | ✅ | Drafts local; server canonical |
| **Assessment submit** | ❌ | Server is authoritative scorer; showing optimistic score risks displaying a *wrong* value if scoring rule changes |
| **Account deletion / data export** | ❌ | Destructive/sensitive; user must see explicit server confirmation |
| **Crisis (`/crisis`)** | ❌ | Rule #1 — deterministic, no optimistic UI anywhere |
| **Companion** | ❌ | Server selects the CompassionTemplate; client cannot pre-guess |

`estimateStateClientMirror` lives in `apps/web-app/src/lib/clinical-mirrors.ts` — explicitly named to flag the canonical logic is server-side. Has Vitest parity test against the same intensity inputs the server uses.

### 8.3 ApiError → typed UI dispatch

`@disciplineos/api-client` exports:

```ts
class ApiError extends Error {
  status: number
  code: string             // 'validation_error' | 'auth_required' | etc
  detail?: string
  fields?: Record<string, string[]>
  correlationId?: string
}
```

| Status | UI |
|--------|-----|
| 401 / `auth_required` | Redirect to `/sign-in?return=<path>` |
| 403 / `forbidden` | EmptyState "You don't have access to this" |
| 400 / `validation_error` | Inline field errors via `error.fields` |
| 404 / `not_found` | EmptyState "Not found" |
| 409 / `conflict` | Banner "Out of date — refresh" + manual refetch |
| 429 / `rate_limit` | Banner "Slow down — try again in N seconds" (from `Retry-After` header) |
| 5xx | ErrorState card with retry + correlation ID |
| Network failure (read) | Banner "You're offline — showing cached data" |
| Network failure (write, check-in) | Banner "Saved locally — will sync when online" |
| Network failure (write, other) | "Couldn't save — try again when online" |

Telemetry: every ApiError dispatches an OpenTelemetry browser-SDK span tagged with `route + status + code + correlationId`. PII scrubbed before send.

### 8.4 Loading states — layout-stable progressive

| Pattern | Where | Why |
|---------|-------|-----|
| Skeleton (preferred) | Dashboard, Reports, Library, Patterns landing | Layout-stable; subtle shimmer suppressed under reduced-motion |
| Spinner overlay | Wizard step transitions, modal data loads | Content area too small for skeleton |
| Optimistic, no loader | Check-in, pattern dismiss, journal save | UI updates immediately |

Per-route `loading.tsx` files render route-specific skeletons. Skeleton dimensions match final-layout dimensions exactly — verified via Playwright visual regression.

### 8.5 Offline behavior

Service worker (Workbox) registered in `apps/web-app/src/lib/sw-register.ts`.

**Precache (installed at first visit):**
- `/[locale]/crisis` for every shipped locale
- Local safety directory JSON (~80KB)
- Inter + Fraunces + Vazirmatn (Vazirmatn only when `fa` is shipped) woff2
- App shell HTML

**Runtime strategies:**
- API GET: `staleWhileRevalidate`, 5min
- Library articles: `cacheFirst`, 7d (psychoeducation is stable)
- Images: `cacheFirst`, 30d

**Offline write queue — check-ins ONLY:**
IndexedDB-backed (`apps/web-app/src/lib/offline-queue.ts`). Check-in submit when offline → write to queue → optimistic record visible → Banner "Saved locally". Service worker `sync` event (or app-foreground rehydration) drains queue; replays each, removes on success.

**Conflict resolution**: server timestamps win. If server detects duplicate within dedup window (recommended default: 60 seconds), it returns 409 + canonical record; client replaces optimistic with canonical, shows quiet Toast.

**Why check-ins specifically**: the urge window. A user mid-urge in a basement / on a plane / in a subway must succeed at the check-in. Other writes (journal, settings) require network with explicit retry — no silent queue for those.

**Offline indicator** in TopBar: small icon badge when offline; click reveals "You're offline — N items waiting to sync".

### 8.6 Stub mode for dev / test / Storybook

Refactor existing pattern (`NEXT_PUBLIC_USE_STUBS=true || NODE_ENV==='test'`) into a `useStubs()` hook with per-domain overrides. Stub data lives in `apps/web-app/src/lib/stubs/` — one file per domain. Consumed by:
- Storybook (every story renders against stubs)
- Playwright (`?stubs=true` URL param + middleware sets the runtime flag)
- Local dev when backend not running

Stubs richly populated — multi-week assessment history, varied pattern states, mid-period reports — so the design system is reviewed against realistic data, not edge-case empty states.

### 8.7 Real-time / refresh strategy

No WebSocket / SSE for v1. Refetch triggers:
- Window focus → if `staleTime` exceeded
- Network reconnect → all queries
- Mutation success → targeted invalidation
- Period switch on Reports → fresh fetch

Push notifications register a SW push handler that triggers targeted `invalidateQueries`; payload is metadata only (no PHI), actual data fetch flows through the standard authenticated path.

---

## 9 — Testing strategy

### 9.1 Pyramid + coverage

| Layer | % count | Tooling | Covers |
|-------|---------|---------|--------|
| Unit | ~70% | Vitest + Testing Library | Every primitive, hook, util, clinical mirror |
| E2E | ~20% | Playwright (Chromium + WebKit) | Critical paths only |
| Manual | ~10% | NVDA / JAWS / VoiceOver per release | Top-4 surfaces |

Coverage bars (per CLAUDE.md): 80% overall, **95% for `clinical/` + intervention + resilience**, **100% branch on T3/T4 crisis paths**.

### 9.2 Critical unit-test names (these are gates)

- `formatNumberClinical_returns_latin_digits_in_fa_locale`
- `formatNumberClinical_returns_latin_digits_in_ar_locale`
- `estimateStateClientMirror_parity_with_server_for_all_intensities_0_to_10`
- `severityBand_uses_pinned_phq9_thresholds_not_hand_rolled`
- `compassionTemplate_renders_verbatim_no_interpolation`
- `crisisCard_drops_entries_older_than_90_days`
- `crisisCard_falls_back_to_icasa_when_all_local_stale`
- `urgeSlider_value_renders_latin_in_arabic_context`
- `relapseSurface_does_not_contain_streak_reset_copy`
- `dashboard_resilienceRing_value_never_decrements_across_renders`
- `localeFallback_draft_key_falls_back_to_en_silently`
- `crisisRoute_has_zero_llm_imports`
- `crisisRoute_renders_tel_links_server_side`

Each maps to a CLAUDE.md rule. Failing test = unconditional merge block.

### 9.3 E2E (Playwright)

Critical paths: onboarding, check-in (×3 states), assessment full PHQ-9 with safety triggered + not triggered, /crisis with JS disabled, locale switch en→ar→fa keeps clinical numbers Latin, theme toggle persists across reload, offline check-in (network throttled).

Per locale matrix: en + ar (RTL coverage); fr + fa added in v1.1 manual review then automation.
Per theme: dark + light.
Per browser: Chromium + WebKit (Mobile Safari is 30%+ of users).

### 9.4 A11y scans (axe-core in Playwright)

Every screen × {dark, light} × {en, ar}. Zero `serious`/`critical` violations gates merge. `moderate` triaged in PR review.

### 9.5 Visual regression (Chromatic)

Every Storybook story across 4 variants {dark, light} × {en, ar} = ~150 baseline snapshots for the 37-component system. 0.1% pixel-diff threshold flags review. Approval workflow on PRs.

### 9.6 Storybook interaction tests

`@storybook/test` runs in CI against the static Storybook build: Slider keyboard nav, Dialog focus trap, RadioGroup arrow nav, Banner dismiss, Toast auto-dismiss.

### 9.7 CI merge gates

PR cannot merge if any of:
- TypeScript strict (`tsc --noEmit`)
- Vitest unit
- Playwright critical paths × {Chromium, WebKit}
- axe-core: zero serious/critical violations
- Chromatic: no unapproved diffs
- ESLint custom rules (`no-physical-tailwind-properties`, `clinical-numbers-must-format`, `no-llm-on-crisis-route`)
- `pnpm i18n:status` — no draft keys in clinical namespace for shipping locales
- safety-directory mirror byte-equality
- Per-route bundle size budget (Dashboard < 180KB JS, Reports < 220KB, Crisis < 90KB)
- LCP budget per critical route (Dashboard < 2.0s on simulated mid-tier mobile)

---

## 10 — Build sequence (9 weeks)

| Phase | Wk | Deliverable | Outcome |
|-------|----|-------------|---------|
| **0 Foundation** | 1 | Token refresh in `globals.css` (dark + light HSL, Fraunces, type scale, motion); custom ESLint rules; minimum SW (precache `/crisis` only); Storybook setup; Chromatic baseline | Existing app re-themed, no IA change; every primitive has dual-theme + dual-locale stories |
| **1 Generic primitives** | 2 | 15 new generic primitives (Slider … BarChart); Sparkline → Visx; Storybook stories per primitive | Design-system v2 ready for screen work |
| **2 Clinical primitives** | 3 | ResilienceRing, UrgeSlider, SeverityBand, RCIDelta, CompassionTemplate, CrisisCard, InsightCard, BreathingPulse; `estimateStateClientMirror` w/ parity test; clinical-contract Vitest gates | Clinical contracts enforced at unit level |
| **3 Existing screens refresh** | 4 | Dashboard, Check-in, Tools, Journal, Assessments, Settings — visual + interaction refresh, no IA change | Existing 6 screens shipped on new system; brand visible |
| **4 New screens** | 5–6 | Wk 5: Reports + Patterns. Wk 6: Library + Companion + Notifications. Companion + Reports gated by clinical-QA review | 5 new surfaces; v1 IA complete |
| **5 Cross-cutting + offline** | 7 | SW offline queue (check-ins); SW push handler; SW `/crisis` precache for all shipping locales; performance work to budgets | Production-grade reliability layer |
| **6 Polish + clinical QA** | 8 | NVDA/JAWS/VoiceOver passes on top 4; fa locale visual review (Vazirmatn render); clinical QA on Companion + Crisis + safety items; Chromatic sign-off; perf audit | Release-ready |
| **7 Launch** | 9 | Canary 10% × 10min → full shift; rollback armed; monitor error rates, LCP per route, axe-core production scan, PHI audit-stream coverage | v1 live; v1.1 backlog captured |

Aggressive but credible — Phase 0 leverages existing design-system foundation (refining tokens, not inventing primitives from zero), and Phase 4 has the most schedule risk because Companion + Reports both need clinical-QA cycles that are externally paced.

---

## 11 — Risk register

| ID | Risk | Mitigation |
|----|------|------------|
| R1 | Fraunces variable subset must include all glyphs across en/fr/ar (currency, math, punctuation) | Subset audit during Phase 0; ship full Fraunces if subset is too brittle |
| R2 | Offline queue conflict resolution: user offline 6h, 3 queued check-ins replay against fresher server state | Clinical-QA on dedup window (recommended: 60s); decide before Phase 5 |
| R3 | Push notification deep-link to Companion — payload metadata only; deep link must re-auth before showing PHI | Security review during Phase 5; align with Clerk step-up auth pattern already used for `/settings/privacy` |
| R4 | Tools landing — bandit selects suggested tools; how does this compose with the "all tools" library view? | Decision: landing = top 3 suggestions + "Browse all →" link to full library. Confirm with backend `intervention` module owner before Phase 3 |
| R5 | Reports FHIR R4 export — schema needs clinical-QA approval | Spec the export schema during Phase 4 in parallel with Reports UI; QA review before Phase 6 |
| R6 | Vazirmatn 85KB font budget on `fa` users — combined with Fraunces this is heavy on slow 3G | Defer to Phase 5 perf audit; consider `font-display: swap` + system-fa-fallback (Tahoma) as instant fallback |
| R7 | Storybook + Chromatic monthly cost (~$250/mo) | Confirm budget before Phase 0 commit; alternative is local visual diff tooling (slower review cycle) |

---

## 12 — Open decisions (recommended defaults shown; subject to confirmation during plan phase)

1. **AAA contrast for bronze CTA** — current spec at 6.8:1 (passes AA). Recommended default: keep AA, push AAA only where contrast budget allows. Push AAA across all CTAs only if accessibility lead requests.
2. **Reduce ambient motion toggle** — separate from OS reduced-motion. Recommended default: include. Surface in Settings → Appearance + a quiet "reduce motion" link in Companion footer.
3. **Sheet on desktop** — Recommended default: media-query swap (Sheet on mobile, Dialog on desktop for the same content) at the consumer level.
4. **Reflect group bundling Patterns + Reports in sidebar** — Recommended default: keep grouped (cognitive coherence > technical taxonomy).
5. **Library categories** — Recommended default: 5 categories (Understanding addiction, CBT skills, Mindfulness basics, Sleep & recovery, Crisis & safety). Subject to clinical-content-team adjustment.
6. **Dashboard State card** — Recommended default: show *raw* signal interpretation ("HRV: mid, sleep 6.2h") rather than soft framing. Clinical literacy + trust > over-soft framing.
7. **"I slipped" link on check-in success** — Recommended default: always show, ghost-styled, never prominent. A quiet door, not a billboard.
8. **Reports tool-efficacy on sparse data** — Recommended default: hide with "Not enough data this week" message. False confidence here erodes the entire Reports surface.
9. **Reduce-motion link in Companion footer** — Recommended default: include. Companion users may be in a state where breathing pulse feels intrusive even if normally tolerated.
10. **Custom ESLint rules timeline** — Recommended default: ship as Phase 0 prerequisite (~1.5 days engineering); enforcement begins Phase 1.
11. **PHI audit dispatch** — Recommended default: both server (fetch event) and client (view event). Required for the regulatory chain per Rule #11 intent.
12. **Service worker offline queue scope** — Recommended default: full queue for check-ins (Phase 5). If schedule pressure, defer to v1.1 and ship only `/crisis` precache (Rule #1 minimum).
13. **`estimateStateClientMirror` vs no client coloring** — Recommended default: mirror with parity test. Crisp UX > strict single-source-of-truth in this case (parity test catches drift).
14. **Visx for Sparkline** — Recommended default: yes. Adds ~15KB gz; unifies chart layer with BarChart.
15. **Offline check-in dedup window** — Recommended default: 60 seconds (most-recent-wins). Confirm with clinical-QA during Phase 5.
16. **Chromatic vs local visual diff** — Recommended default: Chromatic ($250/mo). Visual regression rigor matters for a 37-component system. Confirm budget.
17. **Phase ordering — existing-screens refresh before new screens** — Recommended default: keep current order. Iterative perceived improvement; lower risk.

---

## 13 — Definition of done

This spec is complete when:

1. ☐ Spec reviewed by spec-document-reviewer subagent — Approved
2. ☐ User reviews this written spec — Approved
3. ☐ Implementation plan written via `writing-plans` skill
4. ☐ Plan committed alongside this spec
5. ☐ Phase 0 work begins

A v1 implementation is shipped when:

1. ☐ All 11 v1 screens render in dark + light + en + ar
2. ☐ All critical Vitest gates passing
3. ☐ All Playwright critical paths passing on Chromium + WebKit
4. ☐ axe-core: zero serious/critical
5. ☐ Manual NVDA + JAWS + VoiceOver passes on top 4 surfaces
6. ☐ Clinical QA sign-off on Companion + Crisis + Assessment safety items + Reports
7. ☐ Performance budgets met (LCP, JS bundle per route)
8. ☐ Service worker queue successful in offline-check-in test scenarios
9. ☐ Canary 10% × 10min → full shift completed without rollback
