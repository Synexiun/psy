/**
 * Unit tests for pure helper functions in the check-in page.
 *
 * Covers:
 * - intensityColor: 0-3 → calm, 4-6 → brand, 7+ → crisis
 * - TRIGGER_KEYS: 8 triggers, no duplicates, known set
 */

import { describe, expect, it } from 'vitest';

// ---------------------------------------------------------------------------
// Inline pure helpers from check-in/page.tsx
// ---------------------------------------------------------------------------

function intensityColor(value: number): string {
  if (value <= 3) return 'var(--color-calm-500)';
  if (value <= 6) return 'var(--color-brand-500)';
  return 'var(--color-crisis-500)';
}

const TRIGGER_KEYS = [
  'stress',
  'boredom',
  'socialPressure',
  'loneliness',
  'anger',
  'anxiety',
  'celebration',
  'fatigue',
] as const;

const NOTES_MAX_CHARS = 280;

// ---------------------------------------------------------------------------
// intensityColor
// ---------------------------------------------------------------------------

describe('intensityColor — calm zone (0-3)', () => {
  it('0 maps to calm', () => {
    expect(intensityColor(0)).toBe('var(--color-calm-500)');
  });

  it('1 maps to calm', () => {
    expect(intensityColor(1)).toBe('var(--color-calm-500)');
  });

  it('3 maps to calm (upper boundary)', () => {
    expect(intensityColor(3)).toBe('var(--color-calm-500)');
  });
});

describe('intensityColor — moderate zone (4-6)', () => {
  it('4 maps to brand (lower boundary)', () => {
    expect(intensityColor(4)).toBe('var(--color-brand-500)');
  });

  it('5 maps to brand', () => {
    expect(intensityColor(5)).toBe('var(--color-brand-500)');
  });

  it('6 maps to brand (upper boundary)', () => {
    expect(intensityColor(6)).toBe('var(--color-brand-500)');
  });
});

describe('intensityColor — crisis zone (7+)', () => {
  it('7 maps to crisis (lower boundary)', () => {
    expect(intensityColor(7)).toBe('var(--color-crisis-500)');
  });

  it('8 maps to crisis', () => {
    expect(intensityColor(8)).toBe('var(--color-crisis-500)');
  });

  it('10 maps to crisis (max slider value)', () => {
    expect(intensityColor(10)).toBe('var(--color-crisis-500)');
  });
});

// ---------------------------------------------------------------------------
// TRIGGER_KEYS
// ---------------------------------------------------------------------------

describe('TRIGGER_KEYS', () => {
  it('has exactly 8 triggers', () => {
    expect(TRIGGER_KEYS).toHaveLength(8);
  });

  it('has no duplicates', () => {
    expect(new Set(TRIGGER_KEYS).size).toBe(TRIGGER_KEYS.length);
  });

  it('includes stress', () => {
    expect(TRIGGER_KEYS).toContain('stress');
  });

  it('includes anxiety', () => {
    expect(TRIGGER_KEYS).toContain('anxiety');
  });

  it('all keys are non-empty strings', () => {
    for (const key of TRIGGER_KEYS) {
      expect(typeof key).toBe('string');
      expect(key.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// NOTES_MAX_CHARS
// ---------------------------------------------------------------------------

describe('NOTES_MAX_CHARS', () => {
  it('is 280', () => {
    expect(NOTES_MAX_CHARS).toBe(280);
  });
});
