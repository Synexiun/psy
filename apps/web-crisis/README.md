# web-crisis

Static crisis surface for Discipline OS. **99.99% reliability target.** This is the "if everything else is down, this still shows you the right number" page.

## Design constraints

- **No auth.** The user is never asked to sign in before seeing hotlines.
- **No runtime dependencies on the main API.** Data comes from the bundled `@disciplineos/safety-directory`. Build once, deploy, serve forever.
- **Static export** (`output: 'export'`) — the build output is plain HTML + CSS + minimal JS. Deploys to any CDN.
- **Minimal JS.** The core path (see a number → tap to call) works with JavaScript disabled.
- **Large touch targets** (≥56px for the primary CTA, 44px for secondary). High-contrast focus ring for keyboard users.
- **No tracking scripts, no analytics SDKs, no error reporters that beacon per-render.** Click events fire a single anonymized beacon to the safety analytics pipeline, and the page works whether or not that beacon succeeds.

## Routing

- `/` → redirects to `/en/` (static meta refresh).
- `/[locale]/` → crisis index for a locale (en, fr, ar, fa).
- All locale pages are pre-generated at build time via `generateStaticParams`.

## Hotline data

Sourced from `@disciplineos/safety-directory`. Reviewed every 90 days; stale entries block the locale launch. See `Docs/Whitepapers/04_Safety_Framework.md §Hotline directory`.

## Deploy

- Primary: S3 + CloudFront with failover to a second region.
- Cache: `Cache-Control: public, max-age=300, stale-while-revalidate=86400` — the page can go stale for a day rather than return an error.
- Synthetic monitor: hits the page every 60 s from 3 regions; PagerDuty on any failure.

## Scripts

- `pnpm dev` — local dev at http://localhost:3050
- `pnpm build` — produces `out/` for static hosting
- `pnpm test:offline` — Playwright scenario that disables the network after load and confirms all CTAs still work
