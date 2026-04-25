/**
 * Unit tests for pure data and helpers in UrgeLogScreen.
 *
 * Tests inline-extracted constants and functions from UrgeLogScreen.tsx:
 * - TRIGGER_KEYS: clinical trigger taxonomy (8 keys)
 * - TRIGGER_LABELS: display string for each trigger key
 * - intensityColor: maps 1-10 intensity → urgency color token
 * - NOTES_MAX_CHARS: 280 character limit
 *
 * Clinical notes:
 * - intensityColor at value 7 must return color.crisis (red), NOT color.elevated.
 *   The threshold at 7 aligns with the T2 trigger window for crisis-level urge detection.
 *   A regression here could visually understate a high-intensity urge as "elevated" (amber)
 *   when it is in the crisis (red) range.
 * - TRIGGER_LABELS must have an entry for every TRIGGER_KEY — a missing label would
 *   render an undefined value in the chip UI, breaking the trigger selection flow.
 */

import { describe, it, expect } from '@jest/globals';
import { color } from '@theme/tokens';

// ---------------------------------------------------------------------------
// Inline from UrgeLogScreen.tsx
// ---------------------------------------------------------------------------

const NOTES_MAX_CHARS = 280;

type TriggerKey =
  | 'stress'
  | 'boredom'
  | 'socialPressure'
  | 'loneliness'
  | 'anger'
  | 'anxiety'
  | 'celebration'
  | 'fatigue';

const TRIGGER_KEYS: TriggerKey[] = [
  'stress',
  'boredom',
  'socialPressure',
  'loneliness',
  'anger',
  'anxiety',
  'celebration',
  'fatigue',
];

const TRIGGER_LABELS: Record<TriggerKey, string> = {
  stress: 'Stress',
  boredom: 'Boredom',
  socialPressure: 'Social pressure',
  loneliness: 'Loneliness',
  anger: 'Anger',
  anxiety: 'Anxiety',
  celebration: 'Celebration',
  fatigue: 'Fatigue',
};

function intensityColor(value: number): string {
  if (value <= 3) return color.calm;
  if (value <= 6) return color.elevated;
  return color.crisis;
}

// ---------------------------------------------------------------------------
// NOTES_MAX_CHARS
// ---------------------------------------------------------------------------

describe('NOTES_MAX_CHARS', () => {
  it('is 280 characters (Twitter-length — familiar and achievable)', () => {
    expect(NOTES_MAX_CHARS).toBe(280);
  });

  it('is a positive integer', () => {
    expect(Number.isInteger(NOTES_MAX_CHARS)).toBe(true);
    expect(NOTES_MAX_CHARS).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// TRIGGER_KEYS
// ---------------------------------------------------------------------------

describe('TRIGGER_KEYS', () => {
  it('has exactly 8 trigger categories', () => {
    expect(TRIGGER_KEYS).toHaveLength(8);
  });

  it('all keys are non-empty strings', () => {
    for (const key of TRIGGER_KEYS) {
      expect(key.length).toBeGreaterThan(0);
    }
  });

  it('all keys are unique', () => {
    expect(new Set(TRIGGER_KEYS).size).toBe(TRIGGER_KEYS.length);
  });

  it('includes the core clinical triggers', () => {
    expect(TRIGGER_KEYS).toContain('stress');
    expect(TRIGGER_KEYS).toContain('anxiety');
    expect(TRIGGER_KEYS).toContain('loneliness');
    expect(TRIGGER_KEYS).toContain('anger');
  });

  it('includes positive-affect trigger (celebration) — urges can be positively triggered', () => {
    expect(TRIGGER_KEYS).toContain('celebration');
  });
});

// ---------------------------------------------------------------------------
// TRIGGER_LABELS
// ---------------------------------------------------------------------------

describe('TRIGGER_LABELS', () => {
  it('has a label for every trigger key (no missing display strings)', () => {
    for (const key of TRIGGER_KEYS) {
      expect(TRIGGER_LABELS[key]).toBeDefined();
      expect(typeof TRIGGER_LABELS[key]).toBe('string');
      expect(TRIGGER_LABELS[key].length).toBeGreaterThan(0);
    }
  });

  it('has the same number of entries as TRIGGER_KEYS', () => {
    expect(Object.keys(TRIGGER_LABELS)).toHaveLength(TRIGGER_KEYS.length);
  });

  it('stress maps to Stress', () => {
    expect(TRIGGER_LABELS.stress).toBe('Stress');
  });

  it('socialPressure maps to human-readable label (not camelCase)', () => {
    // camelCase key must never appear verbatim in the UI
    const label = TRIGGER_LABELS.socialPressure;
    expect(label).not.toBe('socialPressure');
    expect(label.length).toBeGreaterThan(0);
  });

  it('all labels start with uppercase (consistent chip display)', () => {
    for (const label of Object.values(TRIGGER_LABELS)) {
      expect(label[0]).toBe(label[0]?.toUpperCase());
    }
  });
});

// ---------------------------------------------------------------------------
// intensityColor — clinical urgency mapping
// ---------------------------------------------------------------------------

describe('intensityColor — calm zone (0–3)', () => {
  it('value 0 returns calm color', () => {
    expect(intensityColor(0)).toBe(color.calm);
  });

  it('value 1 returns calm color', () => {
    expect(intensityColor(1)).toBe(color.calm);
  });

  it('value 3 returns calm color (upper boundary of calm zone)', () => {
    expect(intensityColor(3)).toBe(color.calm);
  });

  it('calm color is the teal token (#6FB3B8)', () => {
    expect(color.calm).toBe('#6FB3B8');
  });
});

describe('intensityColor — elevated zone (4–6)', () => {
  it('value 4 returns elevated color (first step above calm)', () => {
    expect(intensityColor(4)).toBe(color.elevated);
  });

  it('value 5 returns elevated color', () => {
    expect(intensityColor(5)).toBe(color.elevated);
  });

  it('value 6 returns elevated color (upper boundary of elevated zone)', () => {
    expect(intensityColor(6)).toBe(color.elevated);
  });

  it('elevated color is the amber token (#E8A85B)', () => {
    expect(color.elevated).toBe('#E8A85B');
  });
});

describe('intensityColor — crisis zone (7–10)', () => {
  it('value 7 returns crisis color (T2 threshold: must NOT return elevated)', () => {
    expect(intensityColor(7)).toBe(color.crisis);
    expect(intensityColor(7)).not.toBe(color.elevated);
  });

  it('value 8 returns crisis color', () => {
    expect(intensityColor(8)).toBe(color.crisis);
  });

  it('value 10 returns crisis color (maximum intensity)', () => {
    expect(intensityColor(10)).toBe(color.crisis);
  });

  it('crisis color is the red token (#D14B3E)', () => {
    expect(color.crisis).toBe('#D14B3E');
  });
});

describe('intensityColor — zone transitions', () => {
  it('calm and elevated are distinct colors', () => {
    expect(intensityColor(3)).not.toBe(intensityColor(4));
  });

  it('elevated and crisis are distinct colors', () => {
    expect(intensityColor(6)).not.toBe(intensityColor(7));
  });

  it('calm and crisis are distinct colors', () => {
    expect(intensityColor(1)).not.toBe(intensityColor(9));
  });
});
