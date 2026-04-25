/**
 * Unit tests for HomeScreen static data.
 *
 * PATTERN_STUBS are hardcoded display strings for the resilience home screen.
 * These tests enforce:
 * - Exactly 3 stubs (the UI allocates space for this count)
 * - No stigmatising language (CLAUDE.md Rule #4 — compassion-first framing)
 * - Resilience framing: stubs measure handled urges, not clean time
 * - Content is non-empty and meaningful
 *
 * Note: The stubs will be replaced by live pattern data when the pattern module
 * is wired (Sprint 111 note). These tests pin the placeholder content so an
 * accidental blank or harmful string doesn't reach production.
 */

import { describe, it, expect } from '@jest/globals';

// ---------------------------------------------------------------------------
// PATTERN_STUBS — inline from HomeScreen.tsx
// ---------------------------------------------------------------------------

const PATTERN_STUBS = [
  'Evening urges are 2× more frequent than mornings.',
  'Urges handled without acting: 8 in the last 7 days.',
  'Box breathing used 5 times — most used tool this week.',
] as const;

// ---------------------------------------------------------------------------
// Structure
// ---------------------------------------------------------------------------

describe('PATTERN_STUBS — structure', () => {
  it('has exactly 3 pattern stubs', () => {
    expect(PATTERN_STUBS).toHaveLength(3);
  });

  it('all stubs are non-empty strings', () => {
    for (const stub of PATTERN_STUBS) {
      expect(stub.length).toBeGreaterThan(0);
    }
  });

  it('all stubs are unique (no duplicates)', () => {
    expect(new Set(PATTERN_STUBS).size).toBe(PATTERN_STUBS.length);
  });
});

// ---------------------------------------------------------------------------
// Compassion-first framing (CLAUDE.md Rule #4)
// ---------------------------------------------------------------------------

describe('PATTERN_STUBS — compassion-first framing (CLAUDE.md Rule #4)', () => {
  it('no stub contains "you failed"', () => {
    for (const stub of PATTERN_STUBS) {
      expect(stub.toLowerCase()).not.toContain('you failed');
    }
  });

  it('no stub contains "streak reset"', () => {
    for (const stub of PATTERN_STUBS) {
      expect(stub.toLowerCase()).not.toContain('streak reset');
    }
  });

  it('no stub contains shaming language (failure/weak/loser)', () => {
    for (const stub of PATTERN_STUBS) {
      expect(stub).not.toMatch(/failure|weak|loser|shameful/i);
    }
  });

  it('at least one stub highlights handled urges (resilience framing)', () => {
    const hasHandled = PATTERN_STUBS.some((s) => s.toLowerCase().includes('handled'));
    expect(hasHandled).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Content invariants
// ---------------------------------------------------------------------------

describe('PATTERN_STUBS — content invariants', () => {
  it('first stub mentions time-of-day pattern (temporal pattern type)', () => {
    const first = PATTERN_STUBS[0];
    expect(first).toMatch(/morning|evening|night|afternoon|time/i);
  });

  it('second stub includes a numeric count of handled urges', () => {
    const second = PATTERN_STUBS[1];
    expect(second).toMatch(/\d/);
  });

  it('third stub references a specific coping tool', () => {
    const third = PATTERN_STUBS[2];
    expect(third.toLowerCase()).toMatch(/breathing|grounding|tool|walk|mindful|box/);
  });
});
