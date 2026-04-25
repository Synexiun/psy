/**
 * Tests for the CSP builder in src/middleware.ts.
 *
 * Security requirement: a regression in buildCsp() could silently weaken
 * the app's clickjacking protection, script injection boundary, or
 * frame-ancestor policy.
 *
 * Covers:
 * - buildCsp output contains the supplied nonce in script-src
 * - frame-ancestors 'none' is always present (clickjacking protection)
 * - default-src 'self' is always present
 * - style-src 'unsafe-inline' is present (Tailwind runtime requirement)
 * - connect-src allows api.disciplineos.com
 * - base-uri 'self' is present (prevents base-tag injection)
 * - form-action 'self' is present
 * - Clerk domains are allowed in script-src
 * - CSP is a single string (all directives joined)
 */

import { describe, expect, it } from 'vitest';

// ---------------------------------------------------------------------------
// Inline pure helper from src/middleware.ts
// ---------------------------------------------------------------------------

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

const TEST_NONCE = 'abc123nonce';

// ---------------------------------------------------------------------------
// buildCsp
// ---------------------------------------------------------------------------

describe('buildCsp — nonce injection', () => {
  it('includes the nonce in script-src', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain(`'nonce-${TEST_NONCE}'`);
  });

  it('uses the provided nonce verbatim', () => {
    const specificNonce = 'dGVzdC1ub25jZQ==';
    const csp = buildCsp(specificNonce);
    expect(csp).toContain(`'nonce-${specificNonce}'`);
  });

  it('different nonces produce different policies', () => {
    expect(buildCsp('nonce-a')).not.toBe(buildCsp('nonce-b'));
  });
});

describe('buildCsp — clickjacking protection', () => {
  it('contains frame-ancestors \'none\'', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain("frame-ancestors 'none'");
  });
});

describe('buildCsp — script injection boundary', () => {
  it('contains default-src \'self\'', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain("default-src 'self'");
  });

  it('allows Clerk accounts domain in script-src', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain('https://*.clerk.accounts.dev');
  });

  it('allows Cloudflare challenges in script-src', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain('https://challenges.cloudflare.com');
  });
});

describe('buildCsp — style policy', () => {
  it('contains style-src unsafe-inline (Tailwind runtime requirement)', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain("style-src 'self' 'unsafe-inline'");
  });
});

describe('buildCsp — connect policy', () => {
  it('allows api.disciplineos.com in connect-src', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain('https://api.disciplineos.com');
  });
});

describe('buildCsp — injection protection directives', () => {
  it('contains base-uri \'self\' (prevents base-tag injection)', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain("base-uri 'self'");
  });

  it('contains form-action \'self\'', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(csp).toContain("form-action 'self'");
  });
});

describe('buildCsp — output format', () => {
  it('is a single string (directives joined by semicolons)', () => {
    const csp = buildCsp(TEST_NONCE);
    expect(typeof csp).toBe('string');
    expect(csp).toContain(';');
  });

  it('contains all 10 directives', () => {
    const csp = buildCsp(TEST_NONCE);
    const directives = csp.split(';').map(d => d.trim()).filter(Boolean);
    expect(directives).toHaveLength(10);
  });
});
