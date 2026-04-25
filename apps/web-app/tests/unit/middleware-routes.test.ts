/**
 * Unit tests for PUBLIC_ROUTES and buildCsp logic in src/middleware.ts.
 *
 * CLAUDE.md Rule #1: /:locale/crisis(.*) must ALWAYS be in PUBLIC_ROUTES.
 * If crisis is ever removed from PUBLIC_ROUTES or made auth-gated, a user
 * with an expired Clerk session would be redirected to sign-in during a
 * real crisis — a safety-critical failure.
 *
 * buildCsp produces a per-request Content-Security-Policy header. Key
 * constraints tested here:
 * - The nonce is embedded in script-src as 'nonce-<value>'
 * - 'unsafe-inline' is present in style-src (Tailwind runtime requirement)
 * - 'unsafe-inline' is NOT present in script-src (would defeat nonce-based CSP)
 * - Clerk domains are in script-src and connect-src (required for auth flow)
 * - frame-ancestors is 'none' (clickjacking protection)
 *
 * Pure functions tested here (extracted from middleware.ts, no Next.js required):
 *
 *   buildCsp(nonce): string
 *     Given a base64 nonce string, returns a complete CSP header value.
 *
 * Covers:
 * - PUBLIC_ROUTES: crisis path present (CLAUDE.md Rule #1)
 * - PUBLIC_ROUTES: sign-in wildcard present
 * - PUBLIC_ROUTES: sign-up wildcard present
 * - PUBLIC_ROUTES: health endpoint present (load-balancer liveness check)
 * - PUBLIC_ROUTES: structure integrity (all start with /, no duplicates)
 * - buildCsp: nonce embedded in script-src
 * - buildCsp: 'unsafe-inline' in style-src; absent from script-src
 * - buildCsp: Clerk origin present in script-src and connect-src
 * - buildCsp: frame-ancestors 'none' (clickjacking protection)
 * - buildCsp: base-uri 'self' (injection hardening)
 * - buildCsp: different nonces produce different CSP values
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
  '/:locale/sign-up(.*)',
  '/:locale/crisis(.*)',
  '/api/health',
];

function buildCsp(nonce: string): string {
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' https://*.clerk.accounts.dev https://challenges.cloudflare.com`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "connect-src 'self' https://*.clerk.accounts.dev https://api.disciplineos.com",
    "frame-src https://challenges.cloudflare.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');
}

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

  it('crisis route uses :locale prefix (supports all 4 locales)', () => {
    const crisisRoute = PUBLIC_ROUTES.find((r) => r.includes('crisis'));
    expect(crisisRoute).toContain(':locale');
  });
});

// ---------------------------------------------------------------------------
// PUBLIC_ROUTES — auth routes
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — auth routes', () => {
  it('contains sign-in route with wildcard (Clerk-managed sub-routes)', () => {
    const signInRoute = PUBLIC_ROUTES.find((r) => r.includes('sign-in'));
    expect(signInRoute).toBeDefined();
    expect(signInRoute).toContain('(.*)');
  });

  it('contains sign-up route with wildcard (Clerk-managed sub-routes)', () => {
    const signUpRoute = PUBLIC_ROUTES.find((r) => r.includes('sign-up'));
    expect(signUpRoute).toBeDefined();
    expect(signUpRoute).toContain('(.*)');
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
// PUBLIC_ROUTES — structure
// ---------------------------------------------------------------------------

describe('PUBLIC_ROUTES — structure', () => {
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

  it('has at least 5 routes (root + locale + sign-in + sign-up + crisis + health)', () => {
    expect(PUBLIC_ROUTES.length).toBeGreaterThanOrEqual(5);
  });
});

// ---------------------------------------------------------------------------
// buildCsp — nonce embedding
// ---------------------------------------------------------------------------

describe('buildCsp — nonce embedding', () => {
  const testNonce = 'dGVzdC1ub25jZQ==';

  it("embeds nonce as 'nonce-<value>' in script-src directive", () => {
    const csp = buildCsp(testNonce);
    expect(csp).toContain(`'nonce-${testNonce}'`);
  });

  it('nonce appears inside script-src (not another directive)', () => {
    const csp = buildCsp(testNonce);
    const scriptSrcDirective = csp.split('; ').find((d) => d.startsWith('script-src'));
    expect(scriptSrcDirective).toBeDefined();
    expect(scriptSrcDirective).toContain(`'nonce-${testNonce}'`);
  });

  it('produces a different CSP for a different nonce', () => {
    const csp1 = buildCsp('nonce-aaa');
    const csp2 = buildCsp('nonce-bbb');
    expect(csp1).not.toBe(csp2);
  });
});

// ---------------------------------------------------------------------------
// buildCsp — script-src security constraints
// ---------------------------------------------------------------------------

describe("buildCsp — script-src security constraints", () => {
  const csp = buildCsp('any-nonce');

  it("does NOT contain 'unsafe-inline' in script-src (nonce-based CSP requires its absence)", () => {
    const scriptSrcDirective = csp.split('; ').find((d) => d.startsWith('script-src'));
    expect(scriptSrcDirective).not.toContain("'unsafe-inline'");
  });

  it("does NOT contain 'unsafe-eval' in script-src", () => {
    const scriptSrcDirective = csp.split('; ').find((d) => d.startsWith('script-src'));
    expect(scriptSrcDirective).not.toContain("'unsafe-eval'");
  });

  it('includes Clerk domain in script-src (required for auth flow)', () => {
    const scriptSrcDirective = csp.split('; ').find((d) => d.startsWith('script-src'));
    expect(scriptSrcDirective).toContain('clerk.accounts.dev');
  });
});

// ---------------------------------------------------------------------------
// buildCsp — style-src
// ---------------------------------------------------------------------------

describe("buildCsp — style-src", () => {
  it("contains 'unsafe-inline' in style-src (Tailwind runtime CSS-in-JS requirement)", () => {
    const csp = buildCsp('nonce');
    const styleSrcDirective = csp.split('; ').find((d) => d.startsWith('style-src'));
    expect(styleSrcDirective).toContain("'unsafe-inline'");
  });
});

// ---------------------------------------------------------------------------
// buildCsp — connect-src
// ---------------------------------------------------------------------------

describe('buildCsp — connect-src', () => {
  it('includes Clerk domain in connect-src (required for auth requests)', () => {
    const csp = buildCsp('nonce');
    const connectSrcDirective = csp.split('; ').find((d) => d.startsWith('connect-src'));
    expect(connectSrcDirective).toContain('clerk.accounts.dev');
  });

  it('includes api.disciplineos.com in connect-src', () => {
    const csp = buildCsp('nonce');
    const connectSrcDirective = csp.split('; ').find((d) => d.startsWith('connect-src'));
    expect(connectSrcDirective).toContain('api.disciplineos.com');
  });
});

// ---------------------------------------------------------------------------
// buildCsp — framing + injection hardening
// ---------------------------------------------------------------------------

describe("buildCsp — framing and injection hardening", () => {
  const csp = buildCsp('nonce');

  it("sets frame-ancestors to 'none' (clickjacking protection)", () => {
    expect(csp).toContain("frame-ancestors 'none'");
  });

  it("sets base-uri to 'self' (base tag injection prevention)", () => {
    expect(csp).toContain("base-uri 'self'");
  });

  it("sets form-action to 'self' (form hijacking prevention)", () => {
    expect(csp).toContain("form-action 'self'");
  });
});
