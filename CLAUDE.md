# CLAUDE.md — Guidance for Claude Code sessions

This file tells Claude Code what kind of project this is and how to be useful here. Read first.

## What this project is

**Discipline OS** — a clinical-grade behavioral intervention platform for users in vulnerable psychological states (addiction relapse prevention, compulsive behavior cycles). The product is a closed-loop system that detects rising urges and delivers just-in-time interventions at the 60–180 second window between urge and action.

The platform ships across three first-class surfaces — **iOS** (React Native 0.76), **Android** (React Native 0.76), and **Web** — and the web itself is five distinct Next.js 15 apps differentiated by trust model:

- `apps/web-marketing` — public marketing site (no auth)
- `apps/web-app` — authenticated user app (Clerk, WebAuthn/passkeys + step-up re-auth)
- `apps/web-clinician` — clinician portal (role-gated; PHI boundary with audit correlation)
- `apps/web-enterprise` — enterprise admin (aggregate-only, k ≥ 5)
- `apps/web-crisis` — static-export crisis page, 99.99% SLO, no auth, no API dependency

Launch locales: **`en` (source-of-truth), `fr`, `ar`, `fa`.** Arabic and Persian are RTL; Persian requires Vazirmatn (not an Arabic-first font). Clinical scores always render in Latin digits.

This is **clinical-grade software**. A bug here isn't a dropped request — it's a missed intervention for a user in crisis. Treat all work accordingly.

## Authoritative source of truth

The full spec is in `Docs/bUSINESS/` (12 files), `Docs/Technicals/` (17 files, 00–16), `Docs/Whitepapers/` (peer-reviewed-citation foundation docs), and `Docs/Help/` (per-locale shipped help articles). If anything in this CLAUDE.md conflicts with those docs, **the docs win**. Update this file to match, don't edit away from them.

Quick map:
- `Docs/Technicals/00_Architecture_Overview.md` — system map
- `Docs/Technicals/01_Tech_Stack.md` — pinned versions
- `Docs/Technicals/02_Data_Model.md` — schema
- `Docs/Technicals/07_Security_Privacy.md` — non-negotiable privacy stance
- `Docs/Technicals/12_Psychometric_System.md` — PHQ-9, GAD-7, AUDIT, WHO-5, etc. — validated instruments, scoring, safety items
- `Docs/Technicals/13_Analytics_Reporting.md` — instruments, scoring, RCI, P1–P6 framing rules, FHIR export
- `Docs/Technicals/14_Authentication_Logging.md` — Clerk v6 + WebAuthn + step-up; four-stream logging (app/audit/safety/security)
- `Docs/Technicals/15_Internationalization.md` — locale negotiation, RTL, no-MT rule, Latin-digit rule, safety-directory freshness
- `Docs/Technicals/16_Web_Application.md` — five Next.js surfaces, CSP per surface, PHI boundary, static crisis export
- `Docs/Whitepapers/01_Methodology.md` → `02_Clinical_Evidence_Base.md` → `03_Privacy_Architecture.md` → `04_Safety_Framework.md` → `05_Research_Roadmap.md` — peer-reviewed-citation foundation
- `Docs/Help/` — 16 shipped help articles, EN source-of-truth; fr/ar/fa validated translations carry per-locale last-reviewed timestamps
- `Docs/bUSINESS/09_Brand_Positioning.md` — voice, copy principles

## Non-negotiable rules (do not ship code that violates these)

1. **T3/T4 crisis flows are deterministic.** Never call the LLM in a crisis path. Never rely on a network round-trip to render crisis UI. Never feature-flag crisis behavior. The `apps/web-crisis` surface is a Next.js `output: 'export'` app: it must render with static HTML + `tel:` / `sms:` links and function with JavaScript disabled.
2. **Raw biometric samples never leave the device.** If you find code that uploads raw HR / HRV / accelerometer data, flag it as a P0 bug.
3. **Resilience streak never resets.** The `streak_state.resilience_days` column is monotonically non-decreasing. A DB trigger enforces this; application code must never attempt to decrement.
4. **Relapse copy is compassion-first.** No "you failed," no "streak reset" framing. Templates live in `shared-rules/relapse_templates.json` and require clinical QA sign-off to change.
5. **No advertising SDKs, ever.** No attribution, no session replay, no behavioral fingerprinting. If a library advertises "user insights," check its privacy policy before adding.
6. **Audit logs are append-only and tamper-evident.** Every PHI read/write emits an audit record to the `audit` log stream, which is Merkle-chained (HMAC-SHA256 over the previous record) using `AUDIT_CHAIN_SECRET`. Do not introduce direct DB access from outside the authorization gate. Don't unify `app` + `audit` streams to simplify config — they have different retention (30 days vs 6 years) and IAM for a reason.
7. **Voice blobs hard-delete at 72h.** Enforced by S3 lifecycle + worker. Never extend retention without a DPIA.
8. **No machine translation of clinical content.** PHQ-9, GAD-7, C-SSRS items, intervention scripts, crisis copy, and any safety-adjacent UI ship only with validated-translation sources or native-reviewer sign-off (`_meta.reviewedBy` populated, `_meta.status: "released"`). An unreviewed catalog blocks the locale from release; it never ships behind a "beta translation" disclaimer. `fr`, `ar`, and `fa` catalogs are currently `status: "draft"`.
9. **Latin digits for every clinical score.** PHQ-9 totals, GAD-7 totals, RCI deltas, percentages in reports, streak day counts — render Latin digits regardless of locale. `discipline.shared.i18n.formatters.format_number_clinical` enforces this server-side; client surfaces mirror the rule. Body copy may localize digits; clinical values never do. Reason: Kroenke 2001 / Spitzer 2006 reference totals are numeric and clinicians must read them identically across locales.
10. **Safety directory stale → locale blocked.** `packages/safety-directory/src/hotlines.json` (mirrored to `services/api/data/safety/hotlines.json`) has a 90-day `reviewWindowDays`. An entry whose `verifiedAt` is older blocks the release for that country-locale. CI enforces byte-for-byte equality between the two copies.
11. **PHI boundary always emits `X-Phi-Boundary: 1`.** Any clinician-portal or backend route that reads PHI sets this response header so the log correlator can cross-reference the audit stream with the app stream.
12. **Edit over Write.** Prefer editing existing files to creating new ones, especially docs. Don't create new markdown docs unless explicitly requested.

## Tech stack (cite `01_Tech_Stack.md` for versions)

- **Mobile:** React Native 0.76 (New Architecture, Fabric, TurboModules), Swift + Kotlin native modules, MMKV persistence, Zustand + TanStack Query.
- **Web:** Next.js 15 (App Router, Server Components), React 19, Tailwind v4 (CSS-first `@theme`), next-intl 3.22+ (`defineRouting` + `createMiddleware`), TanStack Query, Visx for clinical charts. Five distinct Next.js apps — see §"What this project is".
- **Shared web packages:** `@disciplineos/design-system` (tokens + primitives), `@disciplineos/api-client` (Zod + ky with `ApiError` class + retry policy limited to GET + idempotent statuses), `@disciplineos/i18n-catalog`, `@disciplineos/safety-directory`.
- **Backend:** FastAPI (Python 3.12+), modular monolith. asyncpg, Alembic migrations. Modules include `psychometric`, `analytics`, `reports`, `content`, `auth`, `shared.i18n`, `shared.logging`.
- **DB:** PostgreSQL 16 + TimescaleDB + pgvector. Redis 7 for cache.
- **Infra:** AWS (ECS Fargate), Terraform 1.8+, GitHub Actions.
- **Auth:** Clerk v6 with WebAuthn/passkeys as primary factor; step-up re-auth required for PHI views and destructive actions. Custom server session JWT for backend.
- **Logging:** Four independent streams — `app` (30 d), `audit` (6 y, HMAC-SHA256 Merkle chain), `safety` (2 y, Merkle chain), `security` (1 y) — each with separate IAM and retention. Configured under `services/api/src/discipline/shared/logging/`.
- **LLM:** Anthropic Claude API — Haiku 4.5 / Sonnet 4.6 routed. Never Opus in user-visible path. Never on a crisis path.
- **Observability:** OpenTelemetry → Loki / Prometheus / Tempo + Grafana.
- **TypeScript:** `tsconfig.base.json` at repo root — strict options include `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`. All packages extend it.

## How to make changes in this repo

### Documentation (most likely case pre-launch)

- Docs live in `Docs/bUSINESS/` or `Docs/Technicals/`.
- Follow the existing structure (numbered sections, tables where useful, cross-references to sibling docs).
- Do not create new top-level doc folders without discussion.

### Code (when scaffolding is populated)

- **Backend:** module-per-domain under `services/api/src/discipline/`. Each module owns its DB tables; cross-module calls go through typed service interfaces, not raw DB joins (a CI linter blocks cross-module `repository.py` / `models.py` imports). See `05_Backend_Services.md` §2. New modules added this phase: `psychometric`, `analytics`, `reports`, `content`.
- **Mobile:** feature-per-folder under `apps/mobile/src/features/`. Zustand for state, tanstack-query for server state, MMKV for persistence. See `04_Mobile_Architecture.md` §3.
- **Web:** each `apps/web-*` is a self-contained Next.js app with its own `middleware.ts` matching its trust model.
  - `web-marketing` — public; CSP excludes `'unsafe-eval'`, includes only marketing analytics origins.
  - `web-app` — `clerkMiddleware` wrapping `createMiddleware(routing)` from next-intl; `/:locale/crisis(.*)` is in `PUBLIC_ROUTES` so the crisis path is never auth-gated.
  - `web-clinician` — adds `sessionClaims.roles.includes('clinician')` check and rewrites to `/forbidden` on mismatch. PHI-boundary routes set `X-Phi-Boundary: 1`.
  - `web-enterprise` — same shape with `enterprise_admin` role. All rendered numbers go through the k ≥ 5 / DP view layer.
  - `web-crisis` — `next.config.mjs` has `output: 'export'`, no Clerk, no next-intl runtime dep, no shared `i18n-catalog` import. All translations inlined as a static `COPY` dict in `src/lib/locale.ts`. Reason: must render when everything else is down.
- **Shared packages:** changes to `packages/i18n-catalog/src/catalogs/en.json` (the source-of-truth) require parallel keys in `fr.json`, `ar.json`, `fa.json` with `_meta.status: "draft"` until native review. `packages/safety-directory/src/hotlines.json` edits must update both the package copy and the `services/api/data/safety/hotlines.json` mirror in the same PR.
- **Tests accompany every change.** Coverage bars: 80% overall, 95% for `intervention` / `clinical` / `resilience` / `psychometric` / `safety_items`, 100% branch coverage on T3 flows.
- **Every PR touches one domain.** Cross-cutting changes (schema + backend + mobile + web in one PR) are rejected in review — the exception is a locale catalog change, which updates all four locale files in one PR by design.

### Clinical-adjacent changes

Any change that affects user-facing copy, the safety classifier, relapse flow, or LLM prompts is **clinical-QA-gated**. Don't merge without clinical sign-off — that's an explicit release checklist item.

## Common pitfalls to avoid

- **Don't call OpenAI / Anthropic from the mobile or web app directly.** All LLM calls route through `services/api/src/discipline/llm/` so the safety filter runs and quotas are enforced.
- **Don't use `requests` or `httpx` ad-hoc from a backend route.** Outbound HTTP goes through a shared client in `shared/http.py` with egress allow-list, tracing, and timeouts.
- **Don't add a new intervention tool variant without a deterministic fallback.** Every tool variant in the `ToolRegistry` must render correctly offline.
- **Don't add background work without registering it in the worker manifest.** Orphan jobs are untracked for reliability.
- **Don't soften the bandit by hand-picking tools.** If you think the bandit is wrong, log an outcome → it learns. Direct overrides are forbidden except for safety escalation.
- **Don't import `next-intl` or `@disciplineos/i18n-catalog` into `apps/web-crisis`.** That surface is intentionally dependency-lean; translations are inlined. Adding a runtime dep breaks the 99.99% SLO guarantee.
- **Don't remove a `/:locale/crisis(.*)` match from `isPublic` in web-app / web-clinician / web-enterprise middleware.** The crisis path must be reachable even when Clerk is mid-outage or a user's session is invalid.
- **Don't paraphrase a validated psychometric instrument.** PHQ-9, GAD-7, AUDIT-C, C-SSRS, WHO-5, PSS-10 items are quoted verbatim from the published source; any reword invalidates the score.
- **Don't hand-roll severity thresholds.** PHQ-9 severity bands come from Kroenke 2001 and are pinned in `services/api/src/discipline/psychometric/scoring/phq9.py` as `PHQ9_SEVERITY_THRESHOLDS`. Same for GAD-7 (Spitzer 2006) and RCI thresholds (Jacobson & Truax 1991).
- **Don't add a shared client dependency into `packages/api-client` that isn't tree-shakable.** Every web surface bundles this; heavy deps inflate LCP on `web-marketing` (public) and violate the static size budget on `web-crisis`.
- **Don't mix log streams in a single call.** `get_stream_logger(LogStream.AUDIT)` and `get_stream_logger(LogStream.APP)` have different processors; routing an audit event into the app stream silently loses it from the 6-year retention pool.

## Dev environment

Windows is a supported dev target for backend + web + infra work; mobile iOS builds require macOS. Linux is the reference production OS.

Commands (once scaffolding runs):

```bash
# Format / lint / typecheck
pnpm run lint
pnpm run typecheck
cd services/api && uv run ruff check . && uv run mypy .

# Test
pnpm test
cd services/api && uv run pytest -q

# Start local stack
docker compose up -d        # postgres, redis, localstack
cd services/api && uv run uvicorn discipline.app:app --reload
cd apps/mobile && pnpm exec expo start

# Web surfaces — each on its own port
pnpm --filter @disciplineos/web-marketing dev    # :3010 public
pnpm --filter @disciplineos/web-app dev          # :3020 authenticated
pnpm --filter @disciplineos/web-clinician dev    # :3030 clinician PHI
pnpm --filter @disciplineos/web-enterprise dev   # :3040 enterprise admin
pnpm --filter @disciplineos/web-crisis build && pnpm --filter @disciplineos/web-crisis start  # :3050 static export
```

When working cross-package (e.g. adding a key in `@disciplineos/i18n-catalog`), rebuild the package before the consuming web surface picks it up:

```bash
pnpm --filter @disciplineos/i18n-catalog build
pnpm --filter @disciplineos/web-app dev
```

## Making a release

Release procedure is in `Docs/Technicals/08_Infrastructure_DevOps.md` §8. Summary:
- Every merge to `main` → auto-deploys to staging.
- Prod promotion is human-gated except for hotfixes.
- Canary gate: 10 min at 10% traffic before full shift.
- Rollback is armed automatically.

## Working with me (Claude)

- **Skim the docs before proposing architecture changes.** The "why" is usually in the docs — don't re-litigate.
- **Use `Grep` / `Glob` aggressively** for cross-ref lookups before asking me to explain something.
- **Explain trade-offs, don't just pick.** Especially on clinical-adjacent changes — I want to see the alternatives you considered.
- **Flag when something is clinically ambiguous.** Defer to clinical QA / advisors rather than guessing.
- **Treat user data as untouchable.** Never paste real user data into a conversation, even for debugging.
- **Cross-doc updates are not optional.** When you add or extend a first-class system (Auth/Logging, Psychometric, a new web surface, a new locale), sweep every sibling doc — `Docs/Technicals/README.md`, `00_Architecture_Overview.md`, `01_Tech_Stack.md`, `02_Data_Model.md`, `03_API_Specification.md`, `05_Backend_Services.md`, `07_Security_Privacy.md`, `08_Infrastructure_DevOps.md`, `09_Testing_QA.md`, `10_Integrations.md`, `11_Technical_Roadmap.md`, and `Docs/bUSINESS/02_Product_Requirements.md` — before declaring the task complete. Partial updates produce a doc set that contradicts itself, which for a clinical product is a defect.
- **Don't machine-translate clinical content to "unblock" a locale.** Leave the key untranslated (fall back to `en` at render time) and surface it in the locale-review queue. This is the opposite of most i18n workflows; it is correct for this product.
- **Don't propose removing the `web-crisis` surface duplication** (inlined translations, no shared package imports). The duplication is load-bearing — it is the reason the surface can keep a 99.99% SLO.

## Where to look when you're stuck

- `Docs/Technicals/00_Architecture_Overview.md` — data flow diagrams for common paths (SOS, urge, relapse).
- `Docs/Technicals/11_Technical_Roadmap.md` — phase-by-phase capability unlock.
- `Docs/Technicals/13_Analytics_Reporting.md` — validated instruments, scoring, RCI thresholds, P1–P6 framing rules, FHIR R4 export.
- `Docs/Technicals/14_Authentication_Logging.md` — the full auth model (Clerk v6 + WebAuthn + step-up) and the four-stream logging architecture.
- `Docs/Technicals/15_Internationalization.md` — locale negotiation, RTL layout, no-MT policy, Latin-digit rule, safety-directory freshness.
- `Docs/Technicals/16_Web_Application.md` — the five Next.js surfaces, CSP per surface, PHI boundary, static-crisis strategy.
- `Docs/Whitepapers/02_Clinical_Evidence_Base.md` — peer-reviewed-citation rationale for every psychometric instrument and the RCI approach.
- `Docs/Whitepapers/04_Safety_Framework.md` — T0–T4 escalation design and the offline crisis contract.
- `Docs/bUSINESS/08_Risk_Compliance.md` — the risk register (R-01 through R-15) frames most "why are we doing it this way" questions.

## What this repo is not

- Not a general-purpose habit tracker. (`Docs/bUSINESS/01_Product_Strategy.md` §3 — anti-patterns we refuse.)
- Not a journaling app. Journals are a supporting surface, not the product.
- Not a crisis hotline replacement. (`Docs/Technicals/06_ML_AI_Architecture.md` §8 — safety classifier + human handoff.)
- Not an AI therapist. Never role-played as one, even by mistake.

---

_Last updated: 2026-04-18._
