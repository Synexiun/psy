# Discipline OS

> **The moment between the urge and the action.**
>
> A behavioral operating system that's there when it counts — and learns from every try.

---

## What this repo contains

```
D:/Psycho/
├── README.md                   ← you are here
├── CLAUDE.md                   ← onboarding for Claude Code sessions
├── Docs/
│   ├── Research/               ← original 4 AI research synthesis inputs
│   ├── bUSINESS/               ← 12-doc business spec (strategy → team)
│   ├── Technicals/             ← 17-doc technical spec (00–16: architecture → roadmap → web/auth/i18n/analytics)
│   ├── Whitepapers/            ← 5 research-grade whitepapers (methodology, clinical evidence, privacy, safety, research roadmap)
│   └── Help/                   ← 16 shipped in-product help articles (EN source; fr/ar/fa validated translations)
├── apps/
│   ├── mobile/                 ← React Native 0.76 (iOS + Android + Watch)
│   ├── web-marketing/          ← Next.js 15 public marketing site (www)
│   ├── web-app/                ← Next.js 15 authenticated user app (app)
│   ├── web-clinician/          ← Next.js 15 clinician portal (clinicians, role-gated PHI)
│   ├── web-enterprise/         ← Next.js 15 enterprise admin (aggregate-only, k ≥ 5)
│   └── web-crisis/             ← Next.js 15 static-export crisis page (99.99% SLO, no auth)
├── packages/
│   ├── design-system/          ← shared tokens + primitives (web for now; RN later)
│   ├── api-client/             ← typed client (Zod schemas + ky, shared across web surfaces)
│   ├── i18n-catalog/           ← en/fr/ar/fa catalogs (ar/fa marked draft pending native review)
│   └── safety-directory/       ← hotlines/emergency numbers (mirrored to services/api/data/safety/)
├── services/
│   └── api/                    ← FastAPI modular monolith (psychometric, analytics, reports, content, auth, …)
├── infra/
│   └── terraform/              ← AWS infrastructure as code
├── scripts/                    ← dev scripts
├── tsconfig.base.json          ← strict TS base (noUncheckedIndexedAccess, exactOptionalPropertyTypes, …)
├── .editorconfig
├── .gitignore
├── package.json                ← pnpm workspaces root
└── pnpm-workspace.yaml
```

## Reading path by role

| If you are… | Start with |
|-------------|-----------|
| **An investor** | `Docs/bUSINESS/00_Executive_Summary.md` → `03_Market_Analysis.md` → `06_Financial_Projections.md` |
| **A clinical advisor** | `Docs/bUSINESS/01_Product_Strategy.md` → `Docs/Technicals/13_Analytics_Reporting.md` → `Docs/Technicals/06_ML_AI_Architecture.md` §8–9 → `Docs/Whitepapers/02_Clinical_Evidence_Base.md` |
| **A backend engineer** | `Docs/Technicals/00_Architecture_Overview.md` → `02_Data_Model.md` → `05_Backend_Services.md` → `14_Authentication_Logging.md` |
| **A mobile engineer** | `Docs/Technicals/00_Architecture_Overview.md` → `04_Mobile_Architecture.md` → `10_Integrations.md` |
| **A web engineer** | `Docs/Technicals/16_Web_Application.md` → `15_Internationalization.md` → `14_Authentication_Logging.md` §web |
| **A clinician-portal engineer** | `Docs/Technicals/16_Web_Application.md` §web-clinician → `13_Analytics_Reporting.md` → `Docs/Whitepapers/04_Safety_Framework.md` |
| **An ML engineer** | `Docs/Technicals/06_ML_AI_Architecture.md` → `13_Analytics_Reporting.md` → `02_Data_Model.md` |
| **A security / compliance engineer** | `Docs/Technicals/07_Security_Privacy.md` → `14_Authentication_Logging.md` → `08_Infrastructure_DevOps.md` → `Docs/Whitepapers/03_Privacy_Architecture.md` |
| **A localization lead** | `Docs/Technicals/15_Internationalization.md` → `packages/i18n-catalog/` → `packages/safety-directory/` |
| **A PM / designer** | `Docs/bUSINESS/02_Product_Requirements.md` → `09_Brand_Positioning.md` → `Docs/Technicals/16_Web_Application.md` §design-system |

## Current project status

**Pre-seed / Phase 0 (Bedrock).** Spec + scaffolding complete across all product surfaces; no production-bound code yet.

- **Documentation:** 17 technical docs (00–16), 12 business docs, a whitepapers folder citing peer-reviewed instruments (PHQ-9 Kroenke 2001, GAD-7 Spitzer 2006, C-SSRS Posner 2011, RCI Jacobson & Truax 1991, …), and a help-article tree under `Docs/Help/` per locale.
- **Mobile (`apps/mobile/`):** React Native 0.76 scaffolding per `04_Mobile_Architecture.md`.
- **Web (`apps/web-*`):** Five Next.js 15 sub-surfaces scaffolded with distinct trust models (public marketing, authenticated app, clinician-role PHI, enterprise-admin k ≥ 5 aggregate, static crisis export).
- **Shared packages:** `design-system`, `api-client` (Zod + ky), `i18n-catalog` (en is source-of-truth; fr/ar/fa catalogs are `status: "draft"` pending native-reviewer sign-off), `safety-directory` (9 country-locale entries, mirrored byte-for-byte into the API service).
- **Backend (`services/api/`):** FastAPI modular monolith with the following modules scaffolded — `psychometric` (PHQ-9, GAD-7 scoring with Jacobson & Truax RCI thresholds, safety routing on PHQ-9 item 9), `analytics` (P1–P6 framing rules, ≥ 3-point sparse gate), `reports` (FHIR R4 Observation, HIPAA Right-of-Access, enterprise engagement), `content` (safety directory, intervention scripts, help articles), and a 4-stream logging subsystem (app / audit / safety / security) with Merkle-chained tamper-evidence on audit + safety.
- **Locales:** `en`, `fr`, `ar`, `fa`. Arabic + Persian are RTL; clinical scores always render in Latin digits (clinical-fidelity rule). No machine translation of shipped clinical content — ever.

Phase 0 per `Docs/Technicals/11_Technical_Roadmap.md` §2 is:

1. Landing page (`apps/web-marketing`) + waitlist.
2. Static crisis page (`apps/web-crisis`) live on its own domain with 99.99% SLO.
3. Staff-only iOS app (local-only, HealthKit + check-in).
4. Mechanical-turk intervention loop with ~15 volunteers.
5. Minimal backend scaffolding (auth, logging, safety directory, psychometric scoring).
6. Instrumented telemetry across all 4 streams.

**Gate to Phase 1:** clinical signal (handled-outcome lift), 10/15 volunteers request continued access, seed round closed, CTO + Head of Clinical + 3 engineers hired, safety-directory review within the 90-day freshness window for every launch locale.

## Getting started (once scaffolding is initialized)

Prerequisites:
- Node 20+, pnpm 9.12+
- Python 3.12+, `uv` or `pdm`
- Docker Desktop
- Terraform 1.8+
- Xcode 16+ (iOS), Android Studio Hedgehog+ (Android)

Bootstrap:

```bash
# Monorepo deps
pnpm install

# Backend
cd services/api
uv sync
uv run alembic upgrade head
uv run uvicorn discipline.app:app --reload

# Mobile
cd apps/mobile
pnpm install
pnpm exec expo prebuild
pnpm exec expo run:ios            # or run:android

# Web surfaces (from repo root; each runs on a distinct port)
pnpm --filter @disciplineos/web-marketing dev    # port 3010 — public
pnpm --filter @disciplineos/web-app dev          # port 3020 — authenticated user app (Clerk)
pnpm --filter @disciplineos/web-clinician dev    # port 3030 — clinician role, PHI boundary
pnpm --filter @disciplineos/web-enterprise dev   # port 3040 — enterprise admin, k ≥ 5 aggregate
pnpm --filter @disciplineos/web-crisis dev       # port 3050 — static export (no auth, no API dep)

# Verify shared-package builds (run in topological order)
pnpm --filter @disciplineos/design-system build
pnpm --filter @disciplineos/api-client build
pnpm --filter @disciplineos/i18n-catalog build
pnpm --filter @disciplineos/safety-directory build
```

### Locales & RTL

The web and mobile surfaces ship in four locales: `en` (source-of-truth), `fr`, `ar`, `fa`. Arabic and Persian render right-to-left; clinical scores (PHQ-9 totals, RCI deltas, percentages in reports) always render in Latin digits regardless of UI language — see `Docs/Technicals/15_Internationalization.md` §4.

The `fr`, `ar`, and `fa` catalogs in `packages/i18n-catalog/src/catalogs/` are marked `_meta.status: "draft"` until a native reviewer signs off. CI blocks a locale launch if the catalog has unreviewed keys or if the safety directory is older than 90 days.

### Safety directory

Emergency/hotline data lives in two places that must match byte-for-byte:
- `packages/safety-directory/src/hotlines.json` (client surfaces)
- `services/api/data/safety/hotlines.json` (backend + clinician exports)

CI fails on drift. Entries older than `reviewWindowDays` (90) block release for that locale.

## Core principles (binding)

See `Docs/Technicals/README.md` §"Core Technical Principles" — summarized:

1. **Edge-first privacy.** Raw biometric data never leaves the device.
2. **Deterministic crisis path.** T3/T4 flows are hard-coded, never LLM-generated, and the `web-crisis` surface is a static export that does not require auth or a live API.
3. **Modular monolith first.** No premature microservices.
4. **Clinical-grade schema from day 1.** Psychometric instruments (PHQ-9, GAD-7, C-SSRS, etc.) are scored to their published severity bands with version pinning in the DB.
5. **Observability-driven.** Four log streams (app / audit / safety / security) with separate retention and IAM; audit + safety Merkle-chained for tamper-evidence.
6. **Security as code.** Threat model per feature. WebAuthn/passkeys primary; step-up re-auth for PHI views and destructive actions.
7. **Radical data minimization.** Enterprise views operate at k ≥ 5 with differential privacy at the SQL view layer.
8. **Clinical fidelity across locales.** Latin digits on every clinical score; no machine translation of shipped clinical content; safety directory review cadence ≤ 90 days per locale.

## Category anti-patterns we refuse

From `Docs/bUSINESS/01_Product_Strategy.md` §4 and `Docs/Technicals/15_Internationalization.md` §"No-MT rule":

- Streaks as primary motivator
- Shame-coded relapse UI
- Ad-supported tiers
- Gamification for its own sake
- Transformation marketing
- Per-feature dark patterns
- AI-as-therapist positioning
- **Machine-translated clinical content.** PHQ-9 / GAD-7 / C-SSRS items, crisis copy, and intervention scripts ship only with validated-translation or native-reviewer sign-off. An unreviewed catalog blocks the locale from release — it never ships with a disclaimer.
- **Crisis UI that depends on auth, JavaScript, or a live API.** The crisis page must render from static HTML + `tel:` links even if everything else is down.
- **Localized digits in clinical scores.** A PHQ-9 total of 17 renders as `17`, never as `١٧` or `۱۷`, regardless of locale.

Any PR that introduces these is a non-starter, even behind a flag.

## Contact

This is a pre-seed project. Founder contact in `Docs/bUSINESS/00_Executive_Summary.md`.

## License

All rights reserved until public repository license is determined (post-seed).
