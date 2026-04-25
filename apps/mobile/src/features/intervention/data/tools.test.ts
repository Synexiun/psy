/**
 * Unit tests for the mobile coping tool catalog.
 *
 * Tests TOOLS constant and getToolById() from tools.ts.
 *
 * Critical: toolId values are stable identifiers stored in ToolUsage records
 * in the intervention store. Renaming any toolId after ship is a breaking
 * change — existing ToolUsage rows would silently fail lookup. These tests
 * pin the exact toolId strings as a regression contract.
 *
 * Clinical notes:
 * - STOP Technique has exactly 4 steps (one per letter: S/T/O/P). A truncated
 *   step list would omit a letter and render an incomplete mnemonic.
 * - 5-4-3-2-1 Grounding has exactly 5 steps (one per sense). A missing sense
 *   breaks the clinical technique.
 * - Box Breathing must have hasBreathingAnimation: true — ToolDetailScreen
 *   branches on this flag to render the animated breathing guide.
 */

import { describe, it, expect } from '@jest/globals';
import { TOOLS, getToolById } from './tools';
import type { ToolCategory } from './tools';

const VALID_CATEGORIES: ReadonlySet<ToolCategory> = new Set([
  'Breathing',
  'Grounding',
  'Body',
  'Mindfulness',
  'Behavioural',
]);

// ---------------------------------------------------------------------------
// List-level tests
// ---------------------------------------------------------------------------

describe('TOOLS list', () => {
  it('has exactly 8 tools', () => {
    expect(TOOLS).toHaveLength(8);
  });

  it('all toolIds are non-empty strings', () => {
    for (const tool of TOOLS) {
      expect(typeof tool.toolId).toBe('string');
      expect(tool.toolId.length).toBeGreaterThan(0);
    }
  });

  it('toolIds are unique (no accidental duplicates — each must be a distinct DB key)', () => {
    const ids = TOOLS.map((t) => t.toolId);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('toolIds are lowercase kebab-case (stable URL/DB-safe identifiers)', () => {
    for (const tool of TOOLS) {
      expect(tool.toolId).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
    }
  });

  it('all names are non-empty', () => {
    for (const tool of TOOLS) {
      expect(tool.name.length).toBeGreaterThan(0);
    }
  });

  it('all taglines are non-empty', () => {
    for (const tool of TOOLS) {
      expect(tool.tagline.length).toBeGreaterThan(0);
    }
  });

  it('all fullDescriptions are non-empty', () => {
    for (const tool of TOOLS) {
      expect(tool.fullDescription.length).toBeGreaterThan(0);
    }
  });

  it('all durationMinutes are positive integers', () => {
    for (const tool of TOOLS) {
      expect(Number.isInteger(tool.durationMinutes)).toBe(true);
      expect(tool.durationMinutes).toBeGreaterThan(0);
    }
  });

  it('all categories are valid ToolCategory values', () => {
    for (const tool of TOOLS) {
      expect(VALID_CATEGORIES.has(tool.category)).toBe(true);
    }
  });

  it('all tools have at least 2 steps', () => {
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

  it('names are unique', () => {
    const names = TOOLS.map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
  });
});

// ---------------------------------------------------------------------------
// Category coverage — each category must appear at least once
// ---------------------------------------------------------------------------

describe('TOOLS category coverage', () => {
  it('includes at least one Breathing tool', () => {
    expect(TOOLS.some((t) => t.category === 'Breathing')).toBe(true);
  });

  it('includes at least one Grounding tool', () => {
    expect(TOOLS.some((t) => t.category === 'Grounding')).toBe(true);
  });

  it('includes at least one Body tool', () => {
    expect(TOOLS.some((t) => t.category === 'Body')).toBe(true);
  });

  it('includes at least one Mindfulness tool', () => {
    expect(TOOLS.some((t) => t.category === 'Mindfulness')).toBe(true);
  });

  it('includes at least one Behavioural tool', () => {
    expect(TOOLS.some((t) => t.category === 'Behavioural')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// toolId stability contract (breaking change guard for ToolUsage records)
// ---------------------------------------------------------------------------

describe('toolId stability', () => {
  const knownIds = [
    'box-breathing',
    '5-4-3-2-1-grounding',
    'progressive-muscle-relaxation',
    'cold-water-reset',
    'urge-surfing',
    'stop-technique',
    'compassion-meditation',
    'delay-and-distract',
  ];

  it('all known toolIds are present in TOOLS', () => {
    const actualIds = new Set(TOOLS.map((t) => t.toolId));
    for (const id of knownIds) {
      expect(actualIds.has(id)).toBe(true);
    }
  });

  it('TOOLS contains exactly the known toolIds (no silent additions or renames)', () => {
    const actualIds = TOOLS.map((t) => t.toolId).sort();
    expect(actualIds).toEqual([...knownIds].sort());
  });
});

// ---------------------------------------------------------------------------
// Box Breathing — clinical + animation flag
// ---------------------------------------------------------------------------

describe('Box Breathing', () => {
  const tool = TOOLS.find((t) => t.toolId === 'box-breathing');

  it('exists in TOOLS', () => {
    expect(tool).toBeDefined();
  });

  it('category is Breathing', () => {
    expect(tool?.category).toBe('Breathing');
  });

  it('has exactly 5 steps (4-4-4-4 cycle plus repeat instruction)', () => {
    expect(tool?.steps).toHaveLength(5);
  });

  it('durationMinutes is 4', () => {
    expect(tool?.durationMinutes).toBe(4);
  });

  it('hasBreathingAnimation is true (ToolDetailScreen renders animated guide)', () => {
    expect(tool?.hasBreathingAnimation).toBe(true);
  });

  it('first step instructs inhaling', () => {
    expect(tool?.steps[0]?.toLowerCase()).toContain('inhale');
  });

  it('includes a "hold" step', () => {
    expect(tool?.steps.some((s) => s.toLowerCase().includes('hold'))).toBe(true);
  });

  it('includes an "exhale" step', () => {
    expect(tool?.steps.some((s) => s.toLowerCase().includes('exhale'))).toBe(true);
  });

  it('includes a repeat instruction', () => {
    expect(tool?.steps.some((s) => s.toLowerCase().includes('repeat'))).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 5-4-3-2-1 Grounding — clinical technique validation
// ---------------------------------------------------------------------------

describe('5-4-3-2-1 Grounding', () => {
  const tool = TOOLS.find((t) => t.toolId === '5-4-3-2-1-grounding');

  it('exists in TOOLS', () => {
    expect(tool).toBeDefined();
  });

  it('category is Grounding', () => {
    expect(tool?.category).toBe('Grounding');
  });

  it('has exactly 5 steps (one per sense — technique correctness)', () => {
    expect(tool?.steps).toHaveLength(5);
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
// STOP Technique — mnemonic integrity (S/T/O/P)
// ---------------------------------------------------------------------------

describe('STOP Technique', () => {
  const tool = TOOLS.find((t) => t.toolId === 'stop-technique');

  it('exists in TOOLS', () => {
    expect(tool).toBeDefined();
  });

  it('category is Mindfulness', () => {
    expect(tool?.category).toBe('Mindfulness');
  });

  it('has exactly 4 steps (one per letter: S, T, O, P)', () => {
    expect(tool?.steps).toHaveLength(4);
  });

  it('first step starts with S — Stop', () => {
    expect(tool?.steps[0]?.toUpperCase()).toContain('S —');
  });

  it('second step starts with T — Take a breath', () => {
    expect(tool?.steps[1]?.toUpperCase()).toContain('T —');
  });

  it('third step starts with O — Observe', () => {
    expect(tool?.steps[2]?.toUpperCase()).toContain('O —');
  });

  it('fourth step starts with P — Proceed', () => {
    expect(tool?.steps[3]?.toUpperCase()).toContain('P —');
  });
});

// ---------------------------------------------------------------------------
// Cold Water Reset — body intervention
// ---------------------------------------------------------------------------

describe('Cold Water Reset', () => {
  const tool = TOOLS.find((t) => t.toolId === 'cold-water-reset');

  it('exists in TOOLS', () => {
    expect(tool).toBeDefined();
  });

  it('category is Body', () => {
    expect(tool?.category).toBe('Body');
  });

  it('durationMinutes is 2 (shortest intervention)', () => {
    expect(tool?.durationMinutes).toBe(2);
  });

  it('first step involves getting water (a sink or bottle)', () => {
    const step = tool?.steps[0]?.toLowerCase() ?? '';
    expect(step.includes('sink') || step.includes('water')).toBe(true);
  });

  it('hasBreathingAnimation is not set (only box-breathing uses animated guide)', () => {
    expect(tool?.hasBreathingAnimation).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// Duration distribution
// ---------------------------------------------------------------------------

describe('Tool durations', () => {
  it('shortest tool is Cold Water Reset (2 min)', () => {
    const min = Math.min(...TOOLS.map((t) => t.durationMinutes));
    expect(min).toBe(2);
    expect(TOOLS.find((t) => t.durationMinutes === 2)?.toolId).toBe('cold-water-reset');
  });

  it('longest tool is Progressive Muscle Relaxation (10 min)', () => {
    const max = Math.max(...TOOLS.map((t) => t.durationMinutes));
    expect(max).toBe(10);
    expect(TOOLS.find((t) => t.durationMinutes === 10)?.toolId).toBe('progressive-muscle-relaxation');
  });
});

// ---------------------------------------------------------------------------
// getToolById
// ---------------------------------------------------------------------------

describe('getToolById', () => {
  it('returns the correct tool for a known toolId', () => {
    const tool = getToolById('box-breathing');
    expect(tool).toBeDefined();
    expect(tool?.name).toBe('Box Breathing');
  });

  it('returns undefined for an unknown toolId', () => {
    expect(getToolById('nonexistent-tool')).toBeUndefined();
  });

  it('returns undefined for an empty string', () => {
    expect(getToolById('')).toBeUndefined();
  });

  it('is case-sensitive (toolIds are lowercase)', () => {
    expect(getToolById('Box-Breathing')).toBeUndefined();
    expect(getToolById('BOX-BREATHING')).toBeUndefined();
  });

  it('returns urge-surfing tool', () => {
    const tool = getToolById('urge-surfing');
    expect(tool?.category).toBe('Mindfulness');
  });

  it('returns delay-and-distract tool', () => {
    const tool = getToolById('delay-and-distract');
    expect(tool?.category).toBe('Behavioural');
  });

  it('returns compassion-meditation tool', () => {
    const tool = getToolById('compassion-meditation');
    expect(tool?.category).toBe('Mindfulness');
  });

  it('result matches direct TOOLS array lookup', () => {
    for (const tool of TOOLS) {
      expect(getToolById(tool.toolId)).toBe(tool);
    }
  });
});
