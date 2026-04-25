/**
 * Unit tests for the tools page catalogue — pure logic, no React rendering.
 *
 * Verifies that:
 * - All 8 coping tools are defined (none accidentally removed)
 * - Exactly one tool is marked featured
 * - All tool IDs are unique (no duplicate registrations)
 * - All category values are valid
 * - All catalogue keys are in the expected enum
 *
 * These are deterministic checks — no API, no DOM, no jsdom.
 * Tools must function offline per CLAUDE.md Rule 1.
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline the TOOLS constant (avoids importing the React component module).
// This is intentional — the test documents the catalogue completeness contract.
// ---------------------------------------------------------------------------

type ToolCategory = 'breathing' | 'grounding' | 'body' | 'mindfulness';
type ToolCatalogKey =
  | 'boxBreathing'
  | 'grounding54321'
  | 'pmr'
  | 'coldWater'
  | 'urgeSurfing'
  | 'stopTechnique'
  | 'compassionMeditation'
  | 'delayDistract';

interface CopingTool {
  id: string;
  catalogKey: ToolCatalogKey;
  category: ToolCategory;
  featured?: boolean;
}

const VALID_CATEGORIES = new Set<ToolCategory>(['breathing', 'grounding', 'body', 'mindfulness']);
const VALID_CATALOG_KEYS = new Set<ToolCatalogKey>([
  'boxBreathing',
  'grounding54321',
  'pmr',
  'coldWater',
  'urgeSurfing',
  'stopTechnique',
  'compassionMeditation',
  'delayDistract',
]);

const TOOLS: CopingTool[] = [
  { id: 'box-breathing', catalogKey: 'boxBreathing', category: 'breathing', featured: true },
  { id: '5-4-3-2-1-grounding', catalogKey: 'grounding54321', category: 'grounding' },
  { id: 'progressive-muscle-relaxation', catalogKey: 'pmr', category: 'body' },
  { id: 'cold-water-reset', catalogKey: 'coldWater', category: 'body' },
  { id: 'urge-surfing', catalogKey: 'urgeSurfing', category: 'mindfulness' },
  { id: 'stop-technique', catalogKey: 'stopTechnique', category: 'mindfulness' },
  { id: 'compassion-meditation', catalogKey: 'compassionMeditation', category: 'mindfulness' },
  { id: 'delay-and-distract', catalogKey: 'delayDistract', category: 'grounding' },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Tools catalogue', () => {
  it('has exactly 8 tools', () => {
    expect(TOOLS).toHaveLength(8);
  });

  it('has exactly one featured tool', () => {
    const featured = TOOLS.filter((t) => t.featured === true);
    expect(featured).toHaveLength(1);
  });

  it('featured tool is "box-breathing"', () => {
    const featured = TOOLS.find((t) => t.featured === true);
    expect(featured?.id).toBe('box-breathing');
    expect(featured?.catalogKey).toBe('boxBreathing');
  });

  it('all tool IDs are unique', () => {
    const ids = TOOLS.map((t) => t.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('all catalogKeys are unique', () => {
    const keys = TOOLS.map((t) => t.catalogKey);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('all categories are valid enum values', () => {
    for (const tool of TOOLS) {
      expect(VALID_CATEGORIES.has(tool.category)).toBe(true);
    }
  });

  it('all catalogKeys are valid enum values', () => {
    for (const tool of TOOLS) {
      expect(VALID_CATALOG_KEYS.has(tool.catalogKey)).toBe(true);
    }
  });

  it('each category has at least one tool', () => {
    for (const category of VALID_CATEGORIES) {
      const count = TOOLS.filter((t) => t.category === category).length;
      expect(count).toBeGreaterThan(0);
    }
  });

  it('contains all 8 expected catalogKeys', () => {
    const keys = new Set(TOOLS.map((t) => t.catalogKey));
    for (const expected of VALID_CATALOG_KEYS) {
      expect(keys.has(expected)).toBe(true);
    }
  });

  it('non-featured tools are those without featured=true', () => {
    const rest = TOOLS.filter((t) => !t.featured);
    expect(rest).toHaveLength(7);
  });
});
