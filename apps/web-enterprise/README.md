# web-enterprise

Enterprise admin portal for Discipline OS. **Pilot at launch** (Phase 2). Aggregate-only — individual user data is never exposed to this surface.

## Access model

- Clerk identity provider.
- Authentication MUST present an `enterprise_admin` role claim for the organization.
- Step-up re-authentication for destructive or privacy-relevant actions (role changes, admin invites, benefit configuration changes).

## Privacy floor (hard guarantee)

- All dashboards are backed by views in `discipline.analytics` that enforce **k ≥ 5** at the SQL layer before a row can leave the database.
- Any cell where the underlying cohort has fewer than 5 individuals returns "insufficient data" — not a zero, not a masked value.
- Differential-privacy noise is applied to counts and rates for cells where the cohort is small but above the k-threshold. Parameters in `Docs/Whitepapers/03_Privacy_Architecture.md §Analytics DP budget`.

**What the employer cannot see:**
- That a specific person logged an urge, had a rough day, or used a specific tool.
- Who took a specific assessment or their score.
- Trajectories that would re-identify an individual.

## Non-goals at pilot

- No SSO federation beyond Clerk-supported providers.
- No custom reporting UI — exports are CSV of the pre-computed aggregate views.
- No payment management (handled by the separate billing service).

## Scripts

- `pnpm dev` — local dev at http://localhost:3040
- `pnpm test:e2e` — Playwright
- `pnpm typecheck`

## Audit

Every admin-level action (role grant, config change, export) is written to the `audit` log stream with justification. See `Docs/Technicals/14_Authentication_Logging.md §Audit stream`.
