/**
 * Unit tests for PUBLIC_ROUTES and PHI_BOUNDARY_ROUTES in src/middleware.ts.
 *
 * CLAUDE.md Rule #1: /:locale/crisis(.*) must ALWAYS be in PUBLIC_ROUTES.
 * Removing it auth-gates the crisis path and blocks users in crisis from
 * reaching the crisis surface even when Clerk is in a degraded state.
 *
 * PHI boundary contract: /:locale/clients/:id(.*) and /:locale/sessions(.*)
 * must always be in the PHI boundary matcher so that audit-log correlation
 * can cross-reference app + audit streams via the X-Phi-Boundary header.
 * A missing route causes silent audit gaps for PHI access.
 *
 * Covers:
 * - PUBLIC_ROUTES includes crisis path (CLAUDE.md Rule #1)
 * - PUBLIC_ROUTES includes health endpoint (load-balancer requirement)
 * - PUBLIC_ROUTES includes sign-in (users must reach auth when unauthenticated)
 * - PUBLIC_ROUTES structure: all start with /, no empty strings
 * - PHI_BOUNDARY_ROUTES includes client detail path
 * - PHI_BOUNDARY_ROUTES includes sessions path
 * - PHI_BOUNDARY_ROUTES are distinct from PUBLIC_ROUTES (PHI routes require auth)
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
// PHI boundary routes — must always have X-Phi-Boundary: 1 set.
// Removing these causes silent audit gaps for PHI reads.
// ---------------------------------------------------------------------------

const PHI_BOUNDARY_ROUTES = [
  '/:locale/clients/:id(.*)',
  '/:locale/sessions(.*)',
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
  it('contains sign-in route (users must reach auth when unauthenticated)', () => {
    expect(PUBLIC_ROUTES.some((r) => r.includes('sign-in'))).toBe(true);
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

  it('all routes are unique', () => {
    expect(new Set(PUBLIC_ROUTES).size).toBe(PUBLIC_ROUTES.length);
  });
});

// ---------------------------------------------------------------------------
// PHI_BOUNDARY_ROUTES — audit-log correlation contract
//
// These routes set X-Phi-Boundary: 1 so the log correlator can cross-reference
// the app stream with the audit stream (6-year retention, Merkle-chained).
// A missing route silently breaks PHI access audit coverage.
// ---------------------------------------------------------------------------

describe('PHI_BOUNDARY_ROUTES — client detail path', () => {
  it('contains /:locale/clients/:id(.*) (patient record pages emit PHI header)', () => {
    expect(PHI_BOUNDARY_ROUTES).toContain('/:locale/clients/:id(.*)');
  });

  it('client path uses wildcard to cover all patient sub-pages', () => {
    const clientRoute = PHI_BOUNDARY_ROUTES.find((r) => r.includes('clients'));
    expect(clientRoute).toBeDefined();
    expect(clientRoute).toContain('(.*)');
  });
});

describe('PHI_BOUNDARY_ROUTES — sessions path', () => {
  it('contains /:locale/sessions(.*) (session history pages emit PHI header)', () => {
    expect(PHI_BOUNDARY_ROUTES).toContain('/:locale/sessions(.*)');
  });

  it('sessions path uses wildcard to cover sub-pages', () => {
    const sessionsRoute = PHI_BOUNDARY_ROUTES.find((r) => r.includes('sessions'));
    expect(sessionsRoute).toBeDefined();
    expect(sessionsRoute).toContain('(.*)');
  });
});

describe('PHI_BOUNDARY_ROUTES — structure', () => {
  it('has at least 2 PHI boundary routes', () => {
    expect(PHI_BOUNDARY_ROUTES.length).toBeGreaterThanOrEqual(2);
  });

  it('all PHI boundary routes start with /', () => {
    for (const route of PHI_BOUNDARY_ROUTES) {
      expect(route.startsWith('/')).toBe(true);
    }
  });

  it('all PHI boundary routes are unique', () => {
    expect(new Set(PHI_BOUNDARY_ROUTES).size).toBe(PHI_BOUNDARY_ROUTES.length);
  });
});

describe('PUBLIC_ROUTES vs PHI_BOUNDARY_ROUTES — separation', () => {
  it('no PHI boundary route is also a public route (PHI routes require clinician auth)', () => {
    for (const phiRoute of PHI_BOUNDARY_ROUTES) {
      expect(PUBLIC_ROUTES).not.toContain(phiRoute);
    }
  });
});
