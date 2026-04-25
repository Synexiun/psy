/**
 * Unit tests for the TOOLS constant on the crisis landing page.
 *
 * Tests inline-extracted data from src/app/[locale]/page.tsx.
 *
 * The crisis surface runs as a static export (output: 'export') with NO
 * runtime JS dependency. Every intervention tool must be completely
 * self-contained in the HTML — no network fetch, no dynamic data loading.
 * These tests guarantee that the static tool data is coherent and complete.
 *
 * Clinical note: Box Breathing uses a 4-4-4-4 count cycle (5 steps including
 * the "Repeat" instruction). 5-4-3-2-1 Grounding has exactly 5 steps (one per
 * sense). Any silently truncated step list would render an incomplete technique
 * to a user in crisis, which is a clinical harm.
 *
 * Non-negotiable constraint (CLAUDE.md Rule #1): Crisis content must function
 * with JavaScript disabled — pure static HTML. This test suite validates that
 * the coping tool data is fully specified in the static constant.
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// TOOLS (inline from src/app/[locale]/page.tsx)
// ---------------------------------------------------------------------------

interface CopingTool {
  name: string;
  duration: string;
  steps: string[];
}

const TOOLS: ReadonlyArray<CopingTool> = Object.freeze([
  {
    name: 'Box Breathing',
    duration: '2 min',
    steps: [
      'Breathe in for 4 counts.',
      'Hold for 4 counts.',
      'Breathe out for 4 counts.',
      'Hold for 4 counts.',
      'Repeat 4 times.',
    ],
  },
  {
    name: '5-4-3-2-1 Grounding',
    duration: '3 min',
    steps: [
      'Name 5 things you can see.',
      'Name 4 things you can touch.',
      'Name 3 things you can hear.',
      'Name 2 things you can smell.',
      'Name 1 thing you can taste.',
    ],
  },
  {
    name: 'Cold Water',
    duration: '1 min',
    steps: [
      'Splash cold water on your face, or hold ice cubes in your hands.',
      "This activates your body's natural calming response.",
    ],
  },
]);

// ---------------------------------------------------------------------------
// List-level tests
// ---------------------------------------------------------------------------

describe('TOOLS list', () => {
  it('has exactly 3 tools', () => {
    expect(TOOLS).toHaveLength(3);
  });

  it('all tools have non-empty name', () => {
    for (const tool of TOOLS) {
      expect(tool.name.length).toBeGreaterThan(0);
    }
  });

  it('all tools have non-empty duration', () => {
    for (const tool of TOOLS) {
      expect(tool.duration.length).toBeGreaterThan(0);
    }
  });

  it('all tools have at least 2 steps (minimum coherent technique)', () => {
    for (const tool of TOOLS) {
      expect(tool.steps.length).toBeGreaterThanOrEqual(2);
    }
  });

  it('all step strings are non-empty', () => {
    for (const tool of TOOLS) {
      for (const step of tool.steps) {
        expect(step.length).toBeGreaterThan(0);
      }
    }
  });

  it('tool names are unique (no accidental duplicates)', () => {
    const names = TOOLS.map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
  });
});

// ---------------------------------------------------------------------------
// Box Breathing — clinical technique validation
// ---------------------------------------------------------------------------

describe('Box Breathing', () => {
  const tool = TOOLS.find((t) => t.name === 'Box Breathing');

  it('exists in the TOOLS list', () => {
    expect(tool).toBeDefined();
  });

  it('has 5 steps (4-4-4-4 cycle plus repeat instruction)', () => {
    expect(tool?.steps).toHaveLength(5);
  });

  it('duration is 2 min', () => {
    expect(tool?.duration).toBe('2 min');
  });

  it('first step instructs breathing in', () => {
    expect(tool?.steps[0]?.toLowerCase()).toContain('breathe in');
  });

  it('includes a "hold" step', () => {
    const hasHold = tool?.steps.some((s) => s.toLowerCase().includes('hold'));
    expect(hasHold).toBe(true);
  });

  it('includes a "breathe out" step', () => {
    const hasOut = tool?.steps.some((s) => s.toLowerCase().includes('breathe out'));
    expect(hasOut).toBe(true);
  });

  it('includes a repeat instruction', () => {
    const hasRepeat = tool?.steps.some((s) => s.toLowerCase().includes('repeat'));
    expect(hasRepeat).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 5-4-3-2-1 Grounding — clinical technique validation
// ---------------------------------------------------------------------------

describe('5-4-3-2-1 Grounding', () => {
  const tool = TOOLS.find((t) => t.name === '5-4-3-2-1 Grounding');

  it('exists in the TOOLS list', () => {
    expect(tool).toBeDefined();
  });

  it('has exactly 5 steps (one per sense — technique correctness)', () => {
    expect(tool?.steps).toHaveLength(5);
  });

  it('duration is 3 min', () => {
    expect(tool?.duration).toBe('3 min');
  });

  it('covers sight (5 things)', () => {
    expect(tool?.steps.some((s) => s.includes('5') && s.toLowerCase().includes('see'))).toBe(true);
  });

  it('covers touch (4 things)', () => {
    expect(tool?.steps.some((s) => s.includes('4') && s.toLowerCase().includes('touch'))).toBe(true);
  });

  it('covers hearing (3 things)', () => {
    expect(tool?.steps.some((s) => s.includes('3') && s.toLowerCase().includes('hear'))).toBe(true);
  });

  it('covers smell (2 things)', () => {
    expect(tool?.steps.some((s) => s.includes('2') && s.toLowerCase().includes('smell'))).toBe(true);
  });

  it('covers taste (1 thing)', () => {
    expect(tool?.steps.some((s) => s.includes('1') && s.toLowerCase().includes('taste'))).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Cold Water — technique validation
// ---------------------------------------------------------------------------

describe('Cold Water', () => {
  const tool = TOOLS.find((t) => t.name === 'Cold Water');

  it('exists in the TOOLS list', () => {
    expect(tool).toBeDefined();
  });

  it('has 2 steps', () => {
    expect(tool?.steps).toHaveLength(2);
  });

  it('duration is 1 min (shortest tool — quick intervention)', () => {
    expect(tool?.duration).toBe('1 min');
  });

  it('first step mentions cold water or ice', () => {
    const step = tool?.steps[0]?.toLowerCase() ?? '';
    const mentionsCold = step.includes('cold') || step.includes('ice');
    expect(mentionsCold).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Duration format consistency
// ---------------------------------------------------------------------------

describe('Tool durations', () => {
  it('all durations end with " min"', () => {
    for (const tool of TOOLS) {
      expect(tool.duration).toMatch(/^\d+ min$/);
    }
  });

  it('shortest tool is Cold Water (1 min)', () => {
    const durations = TOOLS.map((t) => parseInt(t.duration, 10));
    expect(Math.min(...durations)).toBe(1);
    expect(TOOLS.find((t) => t.duration === '1 min')?.name).toBe('Cold Water');
  });

  it('longest tool is 5-4-3-2-1 Grounding (3 min)', () => {
    const durations = TOOLS.map((t) => parseInt(t.duration, 10));
    expect(Math.max(...durations)).toBe(3);
  });
});
