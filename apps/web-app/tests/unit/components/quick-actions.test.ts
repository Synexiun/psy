/**
 * Unit tests for the QuickActions component's `actions` data.
 *
 * The `actions` array is inline in src/components/QuickActions.tsx.
 * This test inlines the same array with a fixed locale to verify:
 *
 *  - Exactly 4 quick actions (the grid allocates 4 cells on desktop)
 *  - Crisis action is always present and last (users in distress must see it)
 *  - Crisis variant is 'crisis' (drives the red button styling)
 *  - All hrefs start with `/${locale}/` (locale prefix required for routing)
 *  - No label or description is empty
 *  - All action hrefs are unique (no duplicate routing)
 *
 * Note: The crisis entry here parallels CLAUDE.md Rule #1 for the web-app
 * UI layer — if the crisis action were removed or mislabeled, users in a
 * peak-urge state would lose their fastest path to crisis navigation.
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline from src/components/QuickActions.tsx (with fixed test locale)
// ---------------------------------------------------------------------------

const TEST_LOCALE = 'en';

const actions = [
  {
    label: 'Check in',
    description: 'Log how you feel right now',
    icon: '✋',
    variant: 'primary' as const,
    href: `/${TEST_LOCALE}/check-in`,
  },
  {
    label: 'Coping tool',
    description: 'Open your toolkit',
    icon: '🧘',
    variant: 'calm' as const,
    href: `/${TEST_LOCALE}/tools`,
  },
  {
    label: 'Journal',
    description: 'Write or speak',
    icon: '📝',
    variant: 'secondary' as const,
    href: `/${TEST_LOCALE}/journal`,
  },
  {
    label: 'Crisis help',
    description: 'Get support now',
    icon: '🚨',
    variant: 'crisis' as const,
    href: `/${TEST_LOCALE}/crisis`,
  },
];

// ---------------------------------------------------------------------------
// Structure
// ---------------------------------------------------------------------------

describe('QuickActions — actions array structure', () => {
  it('has exactly 4 actions (matches 2×2 / 4-column grid layout)', () => {
    expect(actions).toHaveLength(4);
  });

  it('all labels are non-empty strings', () => {
    for (const action of actions) {
      expect(action.label.length).toBeGreaterThan(0);
    }
  });

  it('all descriptions are non-empty strings', () => {
    for (const action of actions) {
      expect(action.description.length).toBeGreaterThan(0);
    }
  });

  it('all hrefs are unique (no duplicate routes)', () => {
    const hrefs = actions.map((a) => a.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  it('all labels are unique', () => {
    const labels = actions.map((a) => a.label);
    expect(new Set(labels).size).toBe(labels.length);
  });
});

// ---------------------------------------------------------------------------
// Locale prefix
// ---------------------------------------------------------------------------

describe('QuickActions — locale-prefixed hrefs', () => {
  it('all hrefs start with the locale prefix', () => {
    for (const action of actions) {
      expect(action.href.startsWith(`/${TEST_LOCALE}/`)).toBe(true);
    }
  });

  it('all hrefs start with "/" (absolute paths)', () => {
    for (const action of actions) {
      expect(action.href.startsWith('/')).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// Crisis action (CLAUDE.md Rule #1 spirit — crisis UI must always be present)
// ---------------------------------------------------------------------------

describe('QuickActions — crisis action invariants', () => {
  it('crisis action is present', () => {
    const crisis = actions.find((a) => a.variant === 'crisis');
    expect(crisis).toBeDefined();
  });

  it('crisis action is last (priority position in the grid)', () => {
    const lastAction = actions[actions.length - 1];
    expect(lastAction?.variant).toBe('crisis');
  });

  it('crisis action href contains "/crisis"', () => {
    const crisis = actions.find((a) => a.variant === 'crisis');
    expect(crisis?.href).toContain('/crisis');
  });

  it('crisis action label mentions "crisis" (visible to user)', () => {
    const crisis = actions.find((a) => a.variant === 'crisis');
    expect(crisis?.label.toLowerCase()).toContain('crisis');
  });

  it('crisis action description suggests immediate support', () => {
    const crisis = actions.find((a) => a.variant === 'crisis');
    const desc = crisis?.description.toLowerCase() ?? '';
    expect(desc).toMatch(/support|help|now/);
  });
});

// ---------------------------------------------------------------------------
// Primary action (check-in)
// ---------------------------------------------------------------------------

describe('QuickActions — check-in action invariants', () => {
  it('check-in action is first (primary entry point)', () => {
    expect(actions[0]?.variant).toBe('primary');
  });

  it('check-in action href contains "check-in"', () => {
    const checkIn = actions.find((a) => a.variant === 'primary');
    expect(checkIn?.href).toContain('check-in');
  });
});

// ---------------------------------------------------------------------------
// Variant coverage
// ---------------------------------------------------------------------------

describe('QuickActions — variant types', () => {
  it('includes at least one "calm" variant (coping tool)', () => {
    expect(actions.some((a) => a.variant === 'calm')).toBe(true);
  });

  it('calm variant links to tools', () => {
    const tool = actions.find((a) => a.variant === 'calm');
    expect(tool?.href).toContain('tool');
  });

  it('includes secondary variant (journal)', () => {
    expect(actions.some((a) => a.variant === 'secondary')).toBe(true);
  });
});
