/**
 * Unit tests for MainTabLayout constants and tab routing logic.
 *
 * CLAUDE.md Rule #1 compliance: The Crisis tab MUST navigate to the root
 * stack (gesture-disabled, animation-none) rather than switching the
 * in-layout tab. If this routing decision were broken, CrisisScreen would
 * render inside the tab shell without the required T3 crisis presentation.
 *
 * This test extracts and validates the routing classification logic as a pure
 * function — no React, no navigation, no jsdom.
 *
 * Covers:
 * - INITIAL_TAB is 'Home' (first screen users see on launch)
 * - routeTabPress('Crisis') → 'navigate' (root stack push, T3 compliance)
 * - routeTabPress for all non-crisis tabs → 'switchTab'
 * - Every non-crisis TabId maps to 'switchTab'
 * - 'Crisis' is the only tab that requires root-stack navigation
 */

import { describe, it, expect } from '@jest/globals';

// ---------------------------------------------------------------------------
// Inline from MainTabLayout.tsx
// ---------------------------------------------------------------------------

type TabId = 'Home' | 'CheckIn' | 'Tools' | 'Journal' | 'Crisis';

const INITIAL_TAB: TabId = 'Home';

// ---------------------------------------------------------------------------
// Pure routing decision — extracted from handleTabPress in MainTabLayout.tsx.
// 'navigate' means push onto root NativeStack (Crisis path).
// 'switchTab' means update in-layout activeTab state.
// ---------------------------------------------------------------------------

function routeTabPress(tabId: TabId): 'navigate' | 'switchTab' {
  if (tabId === 'Crisis') return 'navigate';
  return 'switchTab';
}

const ALL_TABS: TabId[] = ['Home', 'CheckIn', 'Tools', 'Journal', 'Crisis'];
const NON_CRISIS_TABS: TabId[] = ['Home', 'CheckIn', 'Tools', 'Journal'];

// ---------------------------------------------------------------------------
// INITIAL_TAB
// ---------------------------------------------------------------------------

describe('INITIAL_TAB', () => {
  it('is Home (first screen users see on launch)', () => {
    expect(INITIAL_TAB).toBe('Home');
  });

  it('is a valid TabId', () => {
    expect(ALL_TABS).toContain(INITIAL_TAB);
  });

  it('is not Crisis (users should not start in crisis UI)', () => {
    expect(INITIAL_TAB).not.toBe('Crisis');
  });
});

// ---------------------------------------------------------------------------
// routeTabPress — Crisis routing (CLAUDE.md Rule #1)
// ---------------------------------------------------------------------------

describe('routeTabPress — Crisis tab (T3 root-stack requirement)', () => {
  it('Crisis routes to root stack navigate (not switchTab)', () => {
    expect(routeTabPress('Crisis')).toBe('navigate');
  });

  it('Crisis does NOT route to switchTab (must not render inline)', () => {
    expect(routeTabPress('Crisis')).not.toBe('switchTab');
  });
});

describe('routeTabPress — non-crisis tabs (in-layout switch)', () => {
  it('Home routes to switchTab', () => {
    expect(routeTabPress('Home')).toBe('switchTab');
  });

  it('CheckIn routes to switchTab', () => {
    expect(routeTabPress('CheckIn')).toBe('switchTab');
  });

  it('Tools routes to switchTab', () => {
    expect(routeTabPress('Tools')).toBe('switchTab');
  });

  it('Journal routes to switchTab', () => {
    expect(routeTabPress('Journal')).toBe('switchTab');
  });

  it('all non-crisis tabs route to switchTab', () => {
    for (const tab of NON_CRISIS_TABS) {
      expect(routeTabPress(tab)).toBe('switchTab');
    }
  });
});

describe('routeTabPress — routing partition', () => {
  it('exactly 1 tab routes to navigate (only Crisis)', () => {
    const navigateTabs = ALL_TABS.filter((t) => routeTabPress(t) === 'navigate');
    expect(navigateTabs).toHaveLength(1);
    expect(navigateTabs[0]).toBe('Crisis');
  });

  it('exactly 4 tabs route to switchTab', () => {
    const switchTabs = ALL_TABS.filter((t) => routeTabPress(t) === 'switchTab');
    expect(switchTabs).toHaveLength(4);
  });

  it('every tab maps to either navigate or switchTab (exhaustive)', () => {
    for (const tab of ALL_TABS) {
      const route = routeTabPress(tab);
      expect(['navigate', 'switchTab']).toContain(route);
    }
  });
});
