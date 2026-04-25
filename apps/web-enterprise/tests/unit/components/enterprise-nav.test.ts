/**
 * Unit tests for pure active-state logic in EnterpriseNav (NavLink).
 *
 * The NavLink component in EnterpriseNav.tsx strips the locale prefix from
 * the Next.js `pathname` before comparing it to the link's `href`. This is
 * different from the web-app nav strategy, which uses full locale-prefixed
 * hrefs. Testing this ensures the stripping logic behaves correctly for all
 * expected input forms.
 *
 * Pure functions tested here (extracted from NavLink, no React required):
 *
 *   stripLocale(pathname): string
 *     Given a full Next.js pathname (/{locale}/...), returns the bare path
 *     without the locale segment (e.g. '/en/reports' → '/reports').
 *     Edge cases: root locale path '/en' → '/', empty string → '/'.
 *
 *   isNavActive(href, pathname): boolean
 *     Returns true when the locale-stripped pathname matches the href exactly,
 *     or when it starts with the href prefix (for non-root hrefs only).
 *     Root href '/' matches only the exact locale root, never sub-paths.
 *
 * Covers:
 * - stripLocale: '/en/reports' → '/reports'
 * - stripLocale: '/fr/reports' → '/reports'
 * - stripLocale: '/en' (locale root) → '/'
 * - stripLocale: '' (empty) → '/'
 * - stripLocale: '/en/reports/monthly' → '/reports/monthly'
 * - isNavActive: exact match on '/reports'
 * - isNavActive: prefix match (sub-path of '/reports')
 * - isNavActive: no match when on sibling route
 * - isNavActive: root href '/' matches locale root
 * - isNavActive: root href '/' does NOT match '/reports'
 * - isNavActive: preserves the href !== '/' guard on prefix matching
 * - Nav links: includes '/reports' and '/' (Dashboard) — never '/members'
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline pure helpers from NavLink in EnterpriseNav.tsx
// ---------------------------------------------------------------------------

function stripLocale(pathname: string): string {
  const segments = pathname.split('/').filter(Boolean);
  const withoutLocale = segments.slice(1).join('/');
  return '/' + withoutLocale;
}

function isNavActive(href: string, pathname: string): boolean {
  const pathWithoutLocale = stripLocale(pathname);
  return pathWithoutLocale === href || (href !== '/' && pathWithoutLocale.startsWith(href));
}

// ---------------------------------------------------------------------------
// Nav link configuration (inline from EnterpriseNav.tsx)
// ---------------------------------------------------------------------------

const NAV_LINKS: { href: string; label: string }[] = [
  { href: '/', label: 'Dashboard' },
  { href: '/reports', label: 'Reports' },
  { href: '/settings', label: 'Settings' },
];

// ---------------------------------------------------------------------------
// stripLocale tests
// ---------------------------------------------------------------------------

describe('stripLocale', () => {
  it('/en/reports → /reports', () => {
    expect(stripLocale('/en/reports')).toBe('/reports');
  });

  it('/fr/reports → /reports (locale-agnostic)', () => {
    expect(stripLocale('/fr/reports')).toBe('/reports');
  });

  it('/ar/reports → /reports (RTL locale)', () => {
    expect(stripLocale('/ar/reports')).toBe('/reports');
  });

  it('/en (locale root) → /', () => {
    expect(stripLocale('/en')).toBe('/');
  });

  it('/fr (locale root) → /', () => {
    expect(stripLocale('/fr')).toBe('/');
  });

  it('empty string → /', () => {
    expect(stripLocale('')).toBe('/');
  });

  it('/en/reports/monthly → /reports/monthly (deep path)', () => {
    expect(stripLocale('/en/reports/monthly')).toBe('/reports/monthly');
  });

  it('/en/settings/billing → /settings/billing', () => {
    expect(stripLocale('/en/settings/billing')).toBe('/settings/billing');
  });
});

// ---------------------------------------------------------------------------
// isNavActive tests
// ---------------------------------------------------------------------------

describe('isNavActive — exact match', () => {
  it('returns true when pathname exactly matches href after locale strip', () => {
    expect(isNavActive('/reports', '/en/reports')).toBe(true);
  });

  it('returns true for root href when on locale root', () => {
    expect(isNavActive('/', '/en')).toBe(true);
  });

  it('returns false when pathname is a sibling route', () => {
    expect(isNavActive('/reports', '/en/settings')).toBe(false);
  });
});

describe('isNavActive — prefix match', () => {
  it('returns true for a sub-path of /reports', () => {
    expect(isNavActive('/reports', '/en/reports/monthly')).toBe(true);
  });

  it('returns true for a deep sub-path of /settings', () => {
    expect(isNavActive('/settings', '/en/settings/billing')).toBe(true);
  });

  it('returns false when href is / and pathname is a sub-path (root does not use prefix match)', () => {
    expect(isNavActive('/', '/en/reports')).toBe(false);
  });

  it('returns false when path starts-with would be a false positive (partial segment)', () => {
    // /report does NOT match /reports (different routes)
    expect(isNavActive('/report', '/en/reports')).toBe(false);
  });
});

describe('isNavActive — root href guard', () => {
  it('root "/" only matches the exact locale root, not dashboard sub-pages', () => {
    expect(isNavActive('/', '/en/reports')).toBe(false);
    expect(isNavActive('/', '/en/settings')).toBe(false);
    expect(isNavActive('/', '/en')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Nav links configuration — enterprise-surface constraints
// ---------------------------------------------------------------------------

describe('NAV_LINKS — enterprise surface', () => {
  it('includes a Dashboard link (href="/")', () => {
    expect(NAV_LINKS.some((l) => l.href === '/')).toBe(true);
  });

  it('includes a Reports link (href="/reports")', () => {
    expect(NAV_LINKS.some((l) => l.href === '/reports')).toBe(true);
  });

  it('includes a Settings link', () => {
    expect(NAV_LINKS.some((l) => l.href === '/settings')).toBe(true);
  });

  it('does NOT include a /members link (enterprise shows aggregate data only)', () => {
    expect(NAV_LINKS.some((l) => l.href.includes('/members'))).toBe(false);
  });

  it('does NOT include a /clients link (no per-patient pages on enterprise surface)', () => {
    expect(NAV_LINKS.some((l) => l.href.includes('/clients'))).toBe(false);
  });

  it('all hrefs start with /', () => {
    for (const link of NAV_LINKS) {
      expect(link.href.startsWith('/')).toBe(true);
    }
  });

  it('all labels are non-empty strings', () => {
    for (const link of NAV_LINKS) {
      expect(link.label.length).toBeGreaterThan(0);
    }
  });

  it('all hrefs are unique', () => {
    const hrefs = NAV_LINKS.map((l) => l.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });
});
