# web-app

Authenticated user surface — the web mirror of the Discipline OS mobile app. Four locales (en, fr, ar, fa) with RTL support.

## Purpose

- Let users complete the same core flows from a browser as they can from mobile:
  check-ins, assessments, journal, patterns, coping tools, SOS.
- Serve as the primary surface for users on constrained devices who cannot install
  the native app (Phase 2 launch requirement).

## Auth model

- Clerk as the identity provider.
- WebAuthn / passkeys as the primary authenticator.
- Step-up re-authentication required for:
  - Viewing or exporting journal content.
  - Clinician-shared data access.
  - Account-level destructive actions (delete, change passphrase, wipe).

See `Docs/Technicals/14_Authentication_Logging.md` for the full flow.

## Safety

- The crisis path at `/[locale]/crisis` is **public** — no auth gate. This is enforced
  in `src/middleware.ts` and verified by a dedicated Playwright test.
- Crisis interactions never touch the server's structured-data pipeline; they go through
  the static safety directory shipped with the bundle.

## Non-goals

- No clinician or enterprise surfaces — those live in `web-clinician` and `web-enterprise`.
- No marketing content; the landing page lives in `web-marketing`.

## Scripts

- `pnpm dev` — local dev at http://localhost:3020
- `pnpm test:e2e` — Playwright
- `pnpm test:a11y` — axe-core accessibility checks (gated in CI)

## Reliability targets

LCP ≤ 2.5 s (p75), INP ≤ 200 ms, auth step-up round-trip ≤ 1.5 s (p95).
See `Docs/Technicals/16_Web_Application.md §Performance`.
