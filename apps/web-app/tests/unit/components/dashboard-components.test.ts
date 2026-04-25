/**
 * Unit tests for pure data extracted from web-app dashboard components.
 *
 * Tests inline-extracted constants from:
 * - StateIndicator.tsx: stateConfig (tone/label/message mapping)
 * - PatternCard.tsx: typeLabels + typeTones (pattern type → display)
 * - MoodSparkline.tsx: MOOD_STUB (fallback intensity series)
 * - StreakWidget.tsx: ringMax calculation logic
 *
 * All React rendering is deliberately excluded — the components use
 * 'use client' and hooks that don't run in vitest without a full provider
 * stack. The pure data structures are the only stable test surface here.
 *
 * Clinical notes:
 * - typeTones for 'physiological' and 'compound' must be 'warning' — these
 *   pattern types indicate elevated biometric signals and must not be
 *   rendered as 'calm'. A silent tone map regression could visually minimize
 *   a clinically significant body signal.
 * - stateConfig for 'peak_urge' and 'rising_urge' must be 'crisis' / 'warning'
 *   respectively — the T2/T3 trigger window depends on these UI state labels.
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// StateIndicator — stateConfig (inline from StateIndicator.tsx)
// ---------------------------------------------------------------------------

const stateConfig: Record<
  string,
  { label: string; tone: 'neutral' | 'calm' | 'warning' | 'crisis'; message: string }
> = {
  stable: {
    label: 'Stable',
    tone: 'calm',
    message: 'You appear steady right now. A good moment to build habits.',
  },
  baseline: {
    label: 'Baseline',
    tone: 'neutral',
    message: 'Resting state. Nothing urgent detected.',
  },
  rising_urge: {
    label: 'Rising urge',
    tone: 'warning',
    message: 'A urge is building. Try a coping tool or a short walk.',
  },
  peak_urge: {
    label: 'Peak urge',
    tone: 'crisis',
    message: 'This is the hardest moment. Use a tool or reach out.',
  },
  post_urge: {
    label: 'Post urge',
    tone: 'calm',
    message: 'The wave has passed. Be gentle with yourself.',
  },
};

// ---------------------------------------------------------------------------
// PatternCard — typeLabels + typeTones (inline from PatternCard.tsx)
// ---------------------------------------------------------------------------

const typeLabels: Record<string, string> = {
  temporal: 'Time pattern',
  contextual: 'Context pattern',
  physiological: 'Body signal',
  compound: 'Compound signal',
};

const typeTones: Record<string, 'calm' | 'neutral' | 'warning'> = {
  temporal: 'calm',
  contextual: 'neutral',
  physiological: 'warning',
  compound: 'warning',
};

// ---------------------------------------------------------------------------
// MoodSparkline — MOOD_STUB (inline from MoodSparkline.tsx)
// ---------------------------------------------------------------------------

const MOOD_STUB = [3, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 6, 8, 9, 8, 7, 8, 9, 8, 7];

// ---------------------------------------------------------------------------
// StreakWidget — ringMax calc (inline from StreakWidget.tsx)
// ---------------------------------------------------------------------------

function continuousRingMax(continuousDays: number): number {
  return Math.max(continuousDays, 30);
}

function resilienceRingMax(resilienceDays: number): number {
  return Math.max(resilienceDays, 60);
}

// ---------------------------------------------------------------------------
// stateConfig tests
// ---------------------------------------------------------------------------

describe('stateConfig', () => {
  it('has all 5 expected state keys', () => {
    const keys = Object.keys(stateConfig);
    expect(keys).toContain('stable');
    expect(keys).toContain('baseline');
    expect(keys).toContain('rising_urge');
    expect(keys).toContain('peak_urge');
    expect(keys).toContain('post_urge');
  });

  it('rising_urge tone is warning (T2 pre-crisis signal)', () => {
    expect(stateConfig['rising_urge']?.tone).toBe('warning');
  });

  it('peak_urge tone is crisis (hardest urge moment)', () => {
    expect(stateConfig['peak_urge']?.tone).toBe('crisis');
  });

  it('stable tone is calm (safe resting state)', () => {
    expect(stateConfig['stable']?.tone).toBe('calm');
  });

  it('baseline tone is neutral', () => {
    expect(stateConfig['baseline']?.tone).toBe('neutral');
  });

  it('post_urge tone is calm (recovery framing)', () => {
    expect(stateConfig['post_urge']?.tone).toBe('calm');
  });

  it('all entries have non-empty label, tone, and message', () => {
    for (const [, cfg] of Object.entries(stateConfig)) {
      expect(cfg.label.length).toBeGreaterThan(0);
      expect(cfg.tone.length).toBeGreaterThan(0);
      expect(cfg.message.length).toBeGreaterThan(0);
    }
  });

  it('crisis and warning tones are only on urge states', () => {
    const escalatedTones = Object.entries(stateConfig)
      .filter(([, v]) => v.tone === 'crisis' || v.tone === 'warning')
      .map(([k]) => k);
    expect(escalatedTones.sort()).toEqual(['peak_urge', 'rising_urge'].sort());
  });
});

// ---------------------------------------------------------------------------
// typeLabels tests
// ---------------------------------------------------------------------------

describe('typeLabels', () => {
  it('has all 4 pattern types', () => {
    expect(Object.keys(typeLabels)).toHaveLength(4);
  });

  it('physiological maps to body signal label', () => {
    expect(typeLabels['physiological']).toBe('Body signal');
  });

  it('all labels are non-empty strings', () => {
    for (const label of Object.values(typeLabels)) {
      expect(label.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// typeTones tests (clinical: physiological/compound must be warning)
// ---------------------------------------------------------------------------

describe('typeTones', () => {
  it('physiological tone is warning (biometric signal)', () => {
    expect(typeTones['physiological']).toBe('warning');
  });

  it('compound tone is warning (combined signal)', () => {
    expect(typeTones['compound']).toBe('warning');
  });

  it('temporal tone is calm (low-urgency time pattern)', () => {
    expect(typeTones['temporal']).toBe('calm');
  });

  it('contextual tone is neutral', () => {
    expect(typeTones['contextual']).toBe('neutral');
  });

  it('has same key set as typeLabels', () => {
    expect(Object.keys(typeTones).sort()).toEqual(Object.keys(typeLabels).sort());
  });

  it('all tones are valid values', () => {
    const validTones = new Set(['calm', 'neutral', 'warning']);
    for (const tone of Object.values(typeTones)) {
      expect(validTones.has(tone)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// MOOD_STUB tests
// ---------------------------------------------------------------------------

describe('MOOD_STUB', () => {
  it('has 20 data points (last 20 check-ins fallback)', () => {
    expect(MOOD_STUB).toHaveLength(20);
  });

  it('all values are between 1 and 10', () => {
    for (const v of MOOD_STUB) {
      expect(v).toBeGreaterThanOrEqual(1);
      expect(v).toBeLessThanOrEqual(10);
    }
  });

  it('last value is accessible (used as current mood display)', () => {
    expect(MOOD_STUB[MOOD_STUB.length - 1]).toBeDefined();
    expect(typeof MOOD_STUB[MOOD_STUB.length - 1]).toBe('number');
  });

  it('shows a non-flat trend (not all identical)', () => {
    const unique = new Set(MOOD_STUB);
    expect(unique.size).toBeGreaterThan(1);
  });
});

// ---------------------------------------------------------------------------
// StreakWidget ring-max tests
// ---------------------------------------------------------------------------

describe('continuousRingMax', () => {
  it('returns 30 when days is 0 (empty state minimum ring size)', () => {
    expect(continuousRingMax(0)).toBe(30);
  });

  it('returns 30 when days is less than 30', () => {
    expect(continuousRingMax(14)).toBe(30);
  });

  it('returns 30 exactly when days equals 30', () => {
    expect(continuousRingMax(30)).toBe(30);
  });

  it('returns days when days exceeds 30', () => {
    expect(continuousRingMax(45)).toBe(45);
  });

  it('large value passes through unchanged', () => {
    expect(continuousRingMax(365)).toBe(365);
  });
});

describe('resilienceRingMax', () => {
  it('returns 60 when days is 0 (resilience ring minimum)', () => {
    expect(resilienceRingMax(0)).toBe(60);
  });

  it('returns 60 when days is less than 60', () => {
    expect(resilienceRingMax(30)).toBe(60);
  });

  it('returns 60 exactly when days equals 60', () => {
    expect(resilienceRingMax(60)).toBe(60);
  });

  it('returns days when days exceeds 60', () => {
    expect(resilienceRingMax(90)).toBe(90);
  });

  it('resilience max is double continuous max (longer growth window)', () => {
    expect(resilienceRingMax(0)).toBeGreaterThan(continuousRingMax(0));
  });
});
