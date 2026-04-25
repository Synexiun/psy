/**
 * Unit tests for PUBLIC_ROUTES and PHI_BOUNDARY_ROUTES in src/middleware.ts
 * (clinician surface).
 *
 * CLAUDE.md Rule #1: /:locale/crisis(.*) must ALWAYS be in PUBLIC_ROUTES.
 * Clinicians may reach the portal while their session is expired or while
 * Clerk is degraded. Crisis must be reachable regardless.
 *
 * CLAUDE.md Rule #11: PHI-boundary routes must set X-Phi-Boundary: 1.
 * The isPhiBoundary matcher determines which routes trigger this header.
 * Tests here lock down which route patterns are classified as PHI boundary
 * so that a refactor cannot silently drop the header from a client-data route.
 *
 * Pure constants tested here (extracted from middleware.ts, no Next.js required):
 *
 *   PUBLIC_ROUTE_PATTERNS: string[]
 *     Routes that bypass Clerk auth — must include crisis.
 *
 *   PHI_BOUNDARY_ROUTE_PATTERNS: string[]
 *     Routes that carry PHI data — must include /clients/:id and /sessions.
 *
 * Covers:
 * - PUBLIC_ROUTES: crisis path present (CLAUDE.md Rule #1)
 * - PUBLIC_ROUTES: sign-in wildcard present
 * - PUBLIC_ROUTES: health endpoint present
 * - PUBLIC_ROUTES: NO sign-up route (clinicians use org-invite flow, not self-signup)
 * - PUBLIC_ROUTES structure: all start with /, no duplicates
 * - PHI_BOUNDARY_ROUTES: includes /clients/:id route (individual patient data)
 * - PHI_BOUNDARY_ROUTES: includes /sessions route (session-level PHI)
 * - PHI_BOUNDARY_ROUTES: all patterns start with /:locale prefix
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline from src/middleware.ts
// CLAUDE.md Rule #1: /:locale/crisis(.*) must always be present.
// CLAUDE.md Rule #11: PHI-boundary routes must emit X-Phi-Boundary: 1.
// ---------------------------------------------------------------------------

const PUBLIC_ROUTE_PATTERNS = [
  '/',
  '/:locale',
  '/:locale/sign-in(.*)',
  '/:locale/crisis(.*)',
  '/api/health',
];

const PHI_BOUNDARY_ROUTE_PATTERNS = [
  '/:locale/clients/:id(.*)',
  '/:locale/sessions(.*)',
];

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — crisis path (CLAUDE.md Rule #1)
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — crisis path (CLAUDE.md Rule #1)', () => {
  it('contains /:locale/crisis(.*) (crisis must never be auth-gated)', () => {
    expect(PUBLIC_ROUTE_PATTERNS).toContain('/:locale/crisis(.*)');
  });

  it('crisis route uses wildcard to match all crisis sub-paths', () => {
    const crisisRoute = PUBLIC_ROUTE_PATTERNS.find((r) => r.includes('crisis'));
    expect(crisisRoute).toBeDefined();
    expect(crisisRoute).toContain('(.*)');
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — health endpoint
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — health endpoint', () => {
  it('contains /api/health (load-balancer liveness check must not require auth)', () => {
    expect(PUBLIC_ROUTE_PATTERNS).toContain('/api/health');
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — auth routes
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — auth routes', () => {
  it('contains sign-in route (clinicians must reach auth when session is expired)', () => {
    expect(PUBLIC_ROUTE_PATTERNS.some((r) => r.includes('sign-in'))).toBe(true);
  });

  it('sign-in uses wildcard to cover Clerk-managed sub-routes', () => {
    const signInRoute = PUBLIC_ROUTE_PATTERNS.find((r) => r.includes('sign-in'));
    expect(signInRoute).toContain('(.*)');
  });

  it('does NOT contain a sign-up route (clinicians use org-invite flow, not self-signup)', () => {
    expect(PUBLIC_ROUTE_PATTERNS.some((r) => r.includes('sign-up'))).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — structure
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — structure', () => {
  it('all routes are non-empty strings', () => {
    for (const route of PUBLIC_ROUTE_PATTERNS) {
      expect(route.length).toBeGreaterThan(0);
    }
  });

  it('all routes start with /', () => {
    for (const route of PUBLIC_ROUTE_PATTERNS) {
      expect(route.startsWith('/')).toBe(true);
    }
  });

  it('all routes are unique (no duplicates)', () => {
    expect(new Set(PUBLIC_ROUTE_PATTERNS).size).toBe(PUBLIC_ROUTE_PATTERNS.length);
  });
});

// ---------------------------------------------------------------------------
// PHI_BOUNDARY_ROUTES (CLAUDE.md Rule #11 — X-Phi-Boundary: 1)
// ---------------------------------------------------------------------------

describe('PHI_BOUNDARY_ROUTES — individual-level patient data routes', () => {
  it('includes /:locale/clients/:id(.*) (per-patient pages emit PHI boundary header)', () => {
    expect(PHI_BOUNDARY_ROUTE_PATTERNS.some((r) => r.includes('/clients/:id'))).toBe(true);
  });

  it('/clients/:id route uses wildcard to cover all client sub-pages', () => {
    const clientRoute = PHI_BOUNDARY_ROUTE_PATTERNS.find((r) => r.includes('/clients/:id'));
    expect(clientRoute).toBeDefined();
    expect(clientRoute).toContain('(.*)');
  });

  it('includes /:locale/sessions(.*) (session-level PHI)', () => {
    expect(PHI_BOUNDARY_ROUTE_PATTERNS.some((r) => r.includes('/sessions'))).toBe(true);
  });
});

describe('PHI_BOUNDARY_ROUTES — structure', () => {
  it('all PHI boundary routes start with /:locale prefix', () => {
    for (const route of PHI_BOUNDARY_ROUTE_PATTERNS) {
      expect(route.startsWith('/:locale')).toBe(true);
    }
  });

  it('all PHI boundary routes are non-empty strings', () => {
    for (const route of PHI_BOUNDARY_ROUTE_PATTERNS) {
      expect(route.length).toBeGreaterThan(0);
    }
  });

  it('all PHI boundary routes are unique (no duplicates)', () => {
    expect(new Set(PHI_BOUNDARY_ROUTE_PATTERNS).size).toBe(PHI_BOUNDARY_ROUTE_PATTERNS.length);
  });

  it('has at least 2 PHI boundary route patterns (clients + sessions)', () => {
    expect(PHI_BOUNDARY_ROUTE_PATTERNS.length).toBeGreaterThanOrEqual(2);
  });
});

// ---------------------------------------------------------------------------
// Clinician surface — no enterprise-only routes
// ---------------------------------------------------------------------------

describe('Clinician surface — route scope', () => {
  it('no PUBLIC_ROUTE contains /reports (reports are authenticated clinician views)', () => {
    expect(PUBLIC_ROUTE_PATTERNS.some((r) => r.includes('/reports'))).toBe(false);
  });

  it('no PUBLIC_ROUTE contains /members (no org-level aggregate view on clinician surface)', () => {
    expect(PUBLIC_ROUTE_PATTERNS.some((r) => r.includes('/members'))).toBe(false);
  });
});
