# web-marketing

Public marketing site for Discipline OS. No authentication. No PHI. Ships in four locales (en, fr, ar, fa) with RTL support for Arabic and Persian.

## Purpose

- Explain what Discipline OS is to prospective users, employers, clinicians, and researchers.
- Route visitors in crisis to the static crisis path (`/crisis`, served by `web-crisis`) with a single click from any page.
- Link to the whitepapers (methodology, clinical evidence, privacy architecture, safety framework, research roadmap).
- SEO-first; crawlers welcome.

## Stack

- Next.js 15 (App Router)
- React 19
- next-intl 3 (locale routing via `[locale]` segment and `as-needed` prefix)
- Tailwind CSS v4 (CSS-first config, `@theme` block in `src/app/globals.css`)
- Shared packages: `@disciplineos/design-system`, `@disciplineos/i18n-catalog`

## Non-goals

- No authenticated surfaces. All user-data surfaces live in `web-app`.
- No safety-critical paths. The crisis page is served by `web-crisis` (static, 99.99% SLO).

## Scripts

- `pnpm dev` — local dev at http://localhost:3010
- `pnpm build` — production build
- `pnpm typecheck` — tsc --noEmit
- `pnpm test:e2e` — Playwright end-to-end

## Reliability target

LCP ≤ 2.5 s (p75, 4G), INP ≤ 200 ms, CLS ≤ 0.1. See `Docs/Technicals/16_Web_Application.md §Performance`.
