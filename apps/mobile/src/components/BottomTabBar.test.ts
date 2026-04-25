/**
 * Unit tests for BottomTabBar tab configuration.
 *
 * TAB_CONFIG is the source of truth for mobile navigation structure.
 * Key constraints:
 *
 * - Exactly 5 tabs (matches the web-app BottomNav 5-item limit, CLAUDE.md)
 * - Crisis tab is LAST — positioned consistently with web BottomNav
 * - Crisis tab label is "Support" (not "Crisis") — avoids alarm framing on every open
 * - All tabs have accessibility labels (VoiceOver / TalkBack support)
 * - TabIds are unique (each tab renders at most one screen)
 */

import { describe, it, expect } from '@jest/globals';
import { TAB_CONFIG } from './BottomTabBar';
import type { TabId } from './BottomTabBar';

const VALID_TAB_IDS: ReadonlySet<TabId> = new Set([
  'Home',
  'CheckIn',
  'Tools',
  'Journal',
  'Crisis',
]);

// ---------------------------------------------------------------------------
// TAB_CONFIG list
// ---------------------------------------------------------------------------

describe('TAB_CONFIG', () => {
  it('has exactly 5 tabs', () => {
    expect(TAB_CONFIG).toHaveLength(5);
  });

  it('all tab IDs are unique', () => {
    const ids = TAB_CONFIG.map((t) => t.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('all tab IDs are valid TabId values', () => {
    for (const tab of TAB_CONFIG) {
      expect(VALID_TAB_IDS.has(tab.id)).toBe(true);
    }
  });

  it('all labels are non-empty strings', () => {
    for (const tab of TAB_CONFIG) {
      expect(tab.label.length).toBeGreaterThan(0);
    }
  });

  it('all icons are non-empty strings', () => {
    for (const tab of TAB_CONFIG) {
      expect(tab.icon.length).toBeGreaterThan(0);
    }
  });

  it('all accessibility labels are non-empty strings', () => {
    for (const tab of TAB_CONFIG) {
      expect(tab.accessibilityLabel.length).toBeGreaterThan(0);
    }
  });

  it('icons are unique (no two tabs share the same icon)', () => {
    const icons = TAB_CONFIG.map((t) => t.icon);
    expect(new Set(icons).size).toBe(icons.length);
  });
});

// ---------------------------------------------------------------------------
// Crisis tab — clinical safety design constraints
// ---------------------------------------------------------------------------

describe('Crisis tab', () => {
  const crisisTab = TAB_CONFIG.find((t) => t.id === 'Crisis');

  it('exists in TAB_CONFIG', () => {
    expect(crisisTab).toBeDefined();
  });

  it('is the LAST tab (consistent position reduces search time in crisis)', () => {
    expect(TAB_CONFIG[TAB_CONFIG.length - 1]?.id).toBe('Crisis');
  });

  it('label is "Support" not "Crisis" (avoids alarm framing on every app open)', () => {
    expect(crisisTab?.label).toBe('Support');
    expect(crisisTab?.label).not.toBe('Crisis');
  });

  it('accessibilityLabel mentions getting support', () => {
    const label = crisisTab?.accessibilityLabel.toLowerCase() ?? '';
    expect(label.includes('support') || label.includes('crisis')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Navigation order — expected tab sequence
// ---------------------------------------------------------------------------

describe('TAB_CONFIG order', () => {
  it('Home is first tab', () => {
    expect(TAB_CONFIG[0]?.id).toBe('Home');
  });

  it('CheckIn is second tab', () => {
    expect(TAB_CONFIG[1]?.id).toBe('CheckIn');
  });

  it('all 5 known tab IDs appear in the correct declared order', () => {
    const ids = TAB_CONFIG.map((t) => t.id);
    expect(ids).toEqual(['Home', 'CheckIn', 'Tools', 'Journal', 'Crisis']);
  });
});
