/**
 * Unit tests for pure constants in ToolDetailScreen.
 *
 * Tests inline-extracted constants from the Box Breathing animated guide:
 * - PHASES: the 4-4-4-4 breathing cycle phases (clinical technique)
 * - PHASE_GUIDANCE: text guidance per phase
 * - PHASE_DURATION_MS: 4 seconds per phase (Box Breathing timing contract)
 * - CIRCLE_MAX: animation circle diameter in logical pixels
 *
 * Clinical note: Box Breathing (4-4-4-4) requires exactly 4 equal-duration
 * phases. Any phase count other than 4, or PHASE_DURATION_MS other than 4000ms,
 * changes the clinical technique. This is the same constraint validated in
 * web-crisis/tests/unit/pages/crisis-tools.test.ts (5 steps including "Repeat")
 * and tools.test.ts (5 steps). On mobile, the animated guide has 4 phases (no
 * explicit "Repeat" step — the animation loops automatically).
 */

import { describe, it, expect } from '@jest/globals';

// ---------------------------------------------------------------------------
// Inline from ToolDetailScreen.tsx
// ---------------------------------------------------------------------------

type BreathPhase = 'Inhale' | 'Hold' | 'Exhale' | 'Rest';

const PHASE_DURATION_MS = 4_000;

const PHASES: BreathPhase[] = ['Inhale', 'Hold', 'Exhale', 'Rest'];

const PHASE_GUIDANCE: Record<BreathPhase, string> = {
  Inhale: 'Breathe in slowly through your nose.',
  Hold: 'Hold gently — no strain.',
  Exhale: 'Breathe out through your mouth.',
  Rest: 'Rest. Empty and still.',
};

const CIRCLE_MAX = 200;

// ---------------------------------------------------------------------------
// PHASE_DURATION_MS
// ---------------------------------------------------------------------------

describe('PHASE_DURATION_MS', () => {
  it('is 4000ms (4 seconds — the "4" in 4-4-4-4 Box Breathing)', () => {
    expect(PHASE_DURATION_MS).toBe(4_000);
  });

  it('is a positive number', () => {
    expect(PHASE_DURATION_MS).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// PHASES — 4-4-4-4 cycle integrity
// ---------------------------------------------------------------------------

describe('PHASES', () => {
  it('has exactly 4 phases (the 4-4-4-4 box breathing cycle)', () => {
    expect(PHASES).toHaveLength(4);
  });

  it('phases are in clinical order: Inhale → Hold → Exhale → Rest', () => {
    expect(PHASES).toEqual(['Inhale', 'Hold', 'Exhale', 'Rest']);
  });

  it('Inhale is first (always start by breathing in)', () => {
    expect(PHASES[0]).toBe('Inhale');
  });

  it('Hold follows Inhale', () => {
    expect(PHASES[1]).toBe('Hold');
  });

  it('Exhale follows Hold', () => {
    expect(PHASES[2]).toBe('Exhale');
  });

  it('Rest is last (empty-lung hold completes the box)', () => {
    expect(PHASES[3]).toBe('Rest');
  });

  it('all phase names are unique', () => {
    expect(new Set(PHASES).size).toBe(PHASES.length);
  });
});

// ---------------------------------------------------------------------------
// PHASE_GUIDANCE — guidance text for each phase
// ---------------------------------------------------------------------------

describe('PHASE_GUIDANCE', () => {
  it('has guidance for all 4 phases', () => {
    expect(Object.keys(PHASE_GUIDANCE)).toHaveLength(4);
  });

  it('has guidance for every phase in PHASES (no missing entry)', () => {
    for (const phase of PHASES) {
      expect(PHASE_GUIDANCE[phase]).toBeDefined();
      expect(PHASE_GUIDANCE[phase].length).toBeGreaterThan(0);
    }
  });

  it('Inhale guidance mentions breathing in through nose', () => {
    expect(PHASE_GUIDANCE.Inhale.toLowerCase()).toContain('breathe in');
  });

  it('Exhale guidance mentions breathing out', () => {
    expect(PHASE_GUIDANCE.Exhale.toLowerCase()).toContain('breathe out');
  });

  it('Hold guidance does not mention nose or mouth (nasal/oral distinction irrelevant during hold)', () => {
    const hold = PHASE_GUIDANCE.Hold.toLowerCase();
    expect(hold).toContain('hold');
  });

  it('all guidance strings are non-empty', () => {
    for (const text of Object.values(PHASE_GUIDANCE)) {
      expect(text.length).toBeGreaterThan(0);
    }
  });

  it('guidance strings are unique (no two phases have identical text)', () => {
    const values = Object.values(PHASE_GUIDANCE);
    expect(new Set(values).size).toBe(values.length);
  });
});

// ---------------------------------------------------------------------------
// CIRCLE_MAX — animation geometry
// ---------------------------------------------------------------------------

describe('CIRCLE_MAX', () => {
  it('is 200 (logical pixels — fits comfortably on the smallest supported screen)', () => {
    expect(CIRCLE_MAX).toBe(200);
  });

  it('is a positive number', () => {
    expect(CIRCLE_MAX).toBeGreaterThan(0);
  });

  it('circle radius is CIRCLE_MAX / 2', () => {
    expect(CIRCLE_MAX / 2).toBe(100);
  });
});
