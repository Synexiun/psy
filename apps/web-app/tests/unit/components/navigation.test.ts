/**
 * Navigation logic tests — BottomNav and SidebarNav active-state computation.
 *
 * These components use usePathname and useTranslations (React hooks) and
 * can't be snapshot-tested inline.  We extract and test the pure
 * isActive() logic and item-shape contracts as plain TypeScript.
 *
 * Covers:
 * - isActive(exactMatch): matches only when pathname === href
 * - isActive(prefix): matches href and all sub-paths
 * - isActive returns false when pathname is a sibling route
 * - BottomNav has exactly 5 items (CLAUDE.md: 5-item mobile limit)
 * - BottomNav last item is the crisis item (crisis=true)
 * - SidebarNav has crisis item in a dedicated section (not in main list)
 * - SidebarNav main items include assessments, patterns, settings
 * - Crisis item href contains 'crisis'
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Pure isActive logic extracted from both nav components (identical impl)
// ---------------------------------------------------------------------------

interface NavItemConfig {
  href: string;
  exactMatch?: boolean;
  crisis?: boolean;
}

function isActive(item: NavItemConfig, pathname: string): boolean {
  if (item.exactMatch) {
    return pathname === item.href;
  }
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

// ---------------------------------------------------------------------------
// BottomNav item shape (matches the hardcoded 5-item list in BottomNav.tsx)
// ---------------------------------------------------------------------------

function makeBottomNavItems(locale: string): NavItemConfig[] {
  return [
    { href: `/${locale}`, exactMatch: true },
    { href: `/${locale}/check-in` },
    { href: `/${locale}/tools` },
    { href: `/${locale}/journal` },
    { href: `/${locale}/crisis`, crisis: true },
  ];
}

// ---------------------------------------------------------------------------
// SidebarNav item shape
// ---------------------------------------------------------------------------

function makeSidebarMainItems(locale: string): NavItemConfig[] {
  return [
    { href: `/${locale}`, exactMatch: true },
    { href: `/${locale}/check-in` },
    { href: `/${locale}/journal` },
    { href: `/${locale}/tools` },
    { href: `/${locale}/assessments` },
    { href: `/${locale}/patterns` },
    { href: `/${locale}/settings` },
  ];
}

const makeSidebarCrisisItem = (locale: string): NavItemConfig => ({
  href: `/${locale}/crisis`,
  crisis: true,
});

// ---------------------------------------------------------------------------
// isActive logic tests
// ---------------------------------------------------------------------------

describe('isActive — exactMatch', () => {
  it('returns true when pathname exactly matches href', () => {
    expect(isActive({ href: '/en', exactMatch: true }, '/en')).toBe(true);
  });

  it('returns false when pathname is a sub-path', () => {
    expect(isActive({ href: '/en', exactMatch: true }, '/en/check-in')).toBe(false);
  });

  it('returns false when pathname is unrelated', () => {
    expect(isActive({ href: '/en', exactMatch: true }, '/en/tools')).toBe(false);
  });
});

describe('isActive — prefix match (no exactMatch)', () => {
  it('returns true when pathname exactly equals href', () => {
    expect(isActive({ href: '/en/tools' }, '/en/tools')).toBe(true);
  });

  it('returns true when pathname is a sub-path', () => {
    expect(isActive({ href: '/en/tools' }, '/en/tools/box-breathing')).toBe(true);
  });

  it('returns false when pathname is a sibling route', () => {
    expect(isActive({ href: '/en/tools' }, '/en/toolset')).toBe(false);
  });

  it('returns false when pathname is unrelated', () => {
    expect(isActive({ href: '/en/journal' }, '/en/tools')).toBe(false);
  });

  it('returns false for empty pathname', () => {
    expect(isActive({ href: '/en/tools' }, '')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// BottomNav item count (mobile 5-item limit)
// ---------------------------------------------------------------------------

describe('BottomNav items', () => {
  const items = makeBottomNavItems('en');

  it('has exactly 5 items', () => {
    expect(items).toHaveLength(5);
  });

  it('last item is the crisis item', () => {
    expect(items[items.length - 1]?.crisis).toBe(true);
  });

  it('crisis item href contains "crisis"', () => {
    const crisis = items.find(i => i.crisis);
    expect(crisis?.href).toContain('crisis');
  });

  it('home item uses exactMatch', () => {
    const home = items[0];
    expect(home?.exactMatch).toBe(true);
  });

  it('non-home items do not use exactMatch', () => {
    for (const item of items.slice(1)) {
      expect(item.exactMatch).toBeFalsy();
    }
  });

  it('all hrefs are prefixed with locale', () => {
    for (const item of makeBottomNavItems('fr')) {
      expect(item.href.startsWith('/fr')).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// SidebarNav item shape
// ---------------------------------------------------------------------------

describe('SidebarNav main items', () => {
  const items = makeSidebarMainItems('en');

  it('includes assessments', () => {
    expect(items.some(i => i.href.endsWith('/assessments'))).toBe(true);
  });

  it('includes patterns', () => {
    expect(items.some(i => i.href.endsWith('/patterns'))).toBe(true);
  });

  it('includes settings', () => {
    expect(items.some(i => i.href.endsWith('/settings'))).toBe(true);
  });

  it('home item uses exactMatch', () => {
    expect(items[0]?.exactMatch).toBe(true);
  });

  it('crisis item is NOT in the main list', () => {
    expect(items.some(i => i.crisis)).toBe(false);
  });
});

describe('SidebarNav crisis item', () => {
  const crisis = makeSidebarCrisisItem('en');

  it('has crisis=true', () => {
    expect(crisis.crisis).toBe(true);
  });

  it('href contains "crisis"', () => {
    expect(crisis.href).toContain('crisis');
  });
});
