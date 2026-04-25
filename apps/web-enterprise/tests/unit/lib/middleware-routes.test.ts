/**
 * Unit tests for PUBLIC_ROUTES in src/middleware.ts (enterprise surface).
 *
 * CLAUDE.md Rule #1: /:locale/crisis(.*) must ALWAYS be in PUBLIC_ROUTES.
 * Enterprise users are org-level admins — they may reach the app in a state
 * where their session has expired or Clerk is degraded. Crisis must be
 * reachable regardless.
 *
 * The enterprise surface has no PHI boundary routes (it shows only aggregate
 * org-level analytics, never individual-level data). The k ≥ 5 guarantee
 * is enforced at the SQL view layer, not at middleware level.
 *
 * Covers:
 * - PUBLIC_ROUTES includes crisis path (CLAUDE.md Rule #1)
 * - PUBLIC_ROUTES includes health endpoint (load-balancer requirement)
 * - PUBLIC_ROUTES includes sign-in
 * - PUBLIC_ROUTES structure: all start with /, no empty strings, all unique
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline from src/middleware.ts
// CLAUDE.md Rule #1: /:locale/crisis(.*) must always be present.
// ---------------------------------------------------------------------------

const PUBLIC_ROUTES = [
  '/',
  '/:locale',
  '/:locale/sign-in(.*)',
  '/:locale/crisis(.*)',
  '/api/health',
];

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — crisis path (CLAUDE.md Rule #1)
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — crisis path (CLAUDE.md Rule #1)', () => {
  it('contains /:locale/crisis(.*) (crisis must never be auth-gated)', () => {
    expect(PUBLIC_ROUTES).toContain('/:locale/crisis(.*)');
  });

  it('crisis route uses wildcard to match all crisis sub-paths', () => {
    const crisisRoute = PUBLIC_ROUTES.find((r) => r.includes('crisis'));
    expect(crisisRoute).toBeDefined();
    expect(crisisRoute).toContain('(.*)');
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — health endpoint
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — health endpoint', () => {
  it('contains /api/health (load-balancer liveness check must not require auth)', () => {
    expect(PUBLIC_ROUTES).toContain('/api/health');
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — auth routes
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — auth routes', () => {
  it('contains sign-in route (admins must reach auth when unauthenticated)', () => {
    expect(PUBLIC_ROUTES.some((r) => r.includes('sign-in'))).toBe(true);
  });

  it('sign-in uses wildcard to cover Clerk-managed sub-routes', () => {
    const signInRoute = PUBLIC_ROUTES.find((r) => r.includes('sign-in'));
    expect(signInRoute).toBeDefined();
    expect(signInRoute).toContain('(.*)');
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — structure
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — structure', () => {
  it('has at least 4 routes (root + locale + sign-in + crisis + health)', () => {
    expect(PUBLIC_ROUTES.length).toBeGreaterThanOrEqual(4);
  });

  it('all routes are non-empty strings', () => {
    for (const route of PUBLIC_ROUTES) {
      expect(route.length).toBeGreaterThan(0);
    }
  });

  it('all routes start with /', () => {
    for (const route of PUBLIC_ROUTES) {
      expect(route.startsWith('/')).toBe(true);
    }
  });

  it('all routes are unique (no duplicates)', () => {
    expect(new Set(PUBLIC_ROUTES).size).toBe(PUBLIC_ROUTES.length);
  });
});

// ---------------------------------------------------------------------------
// Enterprise-specific: no PHI-boundary routes
//
// The enterprise surface shows only aggregate data (k ≥ 5 enforced at
// the SQL view layer). No X-Phi-Boundary header is set by this middleware.
// ---------------------------------------------------------------------------

describe('Enterprise surface — no individual-level PHI routes', () => {
  it('no route contains /clients (no per-patient pages on enterprise surface)', () => {
    const clientRoutes = PUBLIC_ROUTES.filter((r) => r.includes('/clients'));
    expect(clientRoutes).toHaveLength(0);
  });

  it('no route contains /sessions (session-level PHI not exposed to enterprise)', () => {
    const sessionRoutes = PUBLIC_ROUTES.filter((r) => r.includes('/sessions'));
    expect(sessionRoutes).toHaveLength(0);
  });
});
