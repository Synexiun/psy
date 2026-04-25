/**
 * Unit tests for enterprise dashboard pure helper logic.
 *
 * Tests inline-extracted functions from src/app/[locale]/page.tsx
 * WITHOUT rendering React.
 *
 * Critical: safeDisplay enforces the k ≥ 5 anonymity threshold at the
 * render boundary. The DB view already suppresses sub-k cells, but
 * this is the second defence-in-depth gate. Never expose cohort data
 * smaller than 5 members — it can de-anonymize individuals.
 *
 * Covers:
 * - safeDisplay: null input → "Insufficient data"
 * - safeDisplay: n < 5 → "Insufficient data"
 * - safeDisplay: n === 5 → formatted number (k-anonymity threshold exactly)
 * - safeDisplay: n > 5 → formatted number
 * - safeDisplay: always Latin digits (toLocaleString('en'))
 * - REPORT_TYPES static list (ReportsList.tsx): exactly 3 types, all have k-suppression notes
 * - WEEKLY_ENGAGEMENT: 6 weekly data points, pct values 0–100
 * - TOP_TOOLS: 5 tools, pct values sum to 100
 * - STUB_METRICS: aggregate org-level metrics (not k-suppressed — org-level totals)
 * - DEPARTMENTS: 5 dept rows, Legal row (3 members) has null suppressed cells (k < 5)
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// safeDisplay — inline from page.tsx
// k ≥ 5 enforcement: null or n < 5 → "Insufficient data"
// ---------------------------------------------------------------------------

function safeDisplay(n: number | null): string {
  if (n === null || n < 5) return 'Insufficient data';
  return n.toLocaleString('en'); // always Latin digits
}

// ---------------------------------------------------------------------------
// REPORT_TYPES (inline from ReportsList.tsx)
// ---------------------------------------------------------------------------

const REPORT_TYPES = [
  {
    id: 'monthly-engagement',
    title: 'Monthly Engagement Report',
    description: 'Aggregate tool usage, session counts, and engagement rate trends for the past calendar month. All cohorts below 5 are suppressed.',
  },
  {
    id: 'wellbeing-trends',
    title: 'Wellbeing Trends',
    description: 'WHO-5 Wellbeing Index trajectory across departments over the trailing 90 days. Requires a minimum cohort of 5 respondents per group.',
  },
  {
    id: 'tool-adoption',
    title: 'Tool Adoption Report',
    description: 'Breakdown of which coping tools were accessed, in what order, and with what frequency. Aggregate counts only — no user-level sequences.',
  },
];

// ---------------------------------------------------------------------------
// WEEKLY_ENGAGEMENT (inline from page.tsx)
// ---------------------------------------------------------------------------

const WEEKLY_ENGAGEMENT = [
  { label: 'W1', pct: 65 },
  { label: 'W2', pct: 71 },
  { label: 'W3', pct: 68 },
  { label: 'W4', pct: 74 },
  { label: 'W5', pct: 78 },
  { label: 'W6', pct: 73 },
];

// ---------------------------------------------------------------------------
// TOP_TOOLS (inline from page.tsx)
// ---------------------------------------------------------------------------

const TOP_TOOLS = [
  { rank: 1, name: 'Box Breathing', pct: 34 },
  { rank: 2, name: '5-4-3-2-1 Grounding', pct: 28 },
  { rank: 3, name: 'Urge Surfing', pct: 19 },
  { rank: 4, name: 'STOP Technique', pct: 12 },
  { rank: 5, name: 'Other', pct: 7 },
];

// ---------------------------------------------------------------------------
// safeDisplay tests — k-anonymity enforcement
// ---------------------------------------------------------------------------

describe('safeDisplay (k ≥ 5 anonymity gate)', () => {
  it('returns "Insufficient data" for null (sub-k suppressed by DB view)', () => {
    expect(safeDisplay(null)).toBe('Insufficient data');
  });

  it('returns "Insufficient data" for n = 0', () => {
    expect(safeDisplay(0)).toBe('Insufficient data');
  });

  it('returns "Insufficient data" for n = 1', () => {
    expect(safeDisplay(1)).toBe('Insufficient data');
  });

  it('returns "Insufficient data" for n = 4 (below k threshold)', () => {
    expect(safeDisplay(4)).toBe('Insufficient data');
  });

  it('returns formatted number for n = 5 (at k threshold)', () => {
    const result = safeDisplay(5);
    expect(result).not.toBe('Insufficient data');
    expect(result).toBe('5');
  });

  it('returns formatted number for n = 6 (above k threshold)', () => {
    expect(safeDisplay(6)).not.toBe('Insufficient data');
  });

  it('returns formatted number for large cohort', () => {
    const result = safeDisplay(847);
    expect(result).toBe('847');
    expect(result).not.toBe('Insufficient data');
  });

  it('never returns empty string', () => {
    expect(safeDisplay(null).length).toBeGreaterThan(0);
    expect(safeDisplay(0).length).toBeGreaterThan(0);
    expect(safeDisplay(5).length).toBeGreaterThan(0);
  });

  it('uses Latin digits (no locale-specific separators for small numbers)', () => {
    const result = safeDisplay(100);
    expect(result).toBe('100');
  });
});

// ---------------------------------------------------------------------------
// REPORT_TYPES tests
// ---------------------------------------------------------------------------

describe('REPORT_TYPES', () => {
  it('has exactly 3 report types', () => {
    expect(REPORT_TYPES).toHaveLength(3);
  });

  it('includes monthly-engagement report', () => {
    expect(REPORT_TYPES.some(r => r.id === 'monthly-engagement')).toBe(true);
  });

  it('includes wellbeing-trends report', () => {
    expect(REPORT_TYPES.some(r => r.id === 'wellbeing-trends')).toBe(true);
  });

  it('includes tool-adoption report', () => {
    expect(REPORT_TYPES.some(r => r.id === 'tool-adoption')).toBe(true);
  });

  it('all descriptions mention k-suppression or aggregate-only data', () => {
    const hasPrivacyNote = REPORT_TYPES.every(
      r => r.description.includes('5') || r.description.includes('Aggregate') || r.description.includes('cohort')
    );
    expect(hasPrivacyNote).toBe(true);
  });

  it('all report IDs are non-empty', () => {
    for (const report of REPORT_TYPES) {
      expect(report.id.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// WEEKLY_ENGAGEMENT tests
// ---------------------------------------------------------------------------

describe('WEEKLY_ENGAGEMENT', () => {
  it('has 6 weekly data points', () => {
    expect(WEEKLY_ENGAGEMENT).toHaveLength(6);
  });

  it('all pct values are between 0 and 100', () => {
    for (const point of WEEKLY_ENGAGEMENT) {
      expect(point.pct).toBeGreaterThanOrEqual(0);
      expect(point.pct).toBeLessThanOrEqual(100);
    }
  });

  it('labels are W1 through W6', () => {
    const labels = WEEKLY_ENGAGEMENT.map(p => p.label);
    expect(labels).toEqual(['W1', 'W2', 'W3', 'W4', 'W5', 'W6']);
  });
});

// ---------------------------------------------------------------------------
// TOP_TOOLS tests
// ---------------------------------------------------------------------------

describe('TOP_TOOLS', () => {
  it('has exactly 5 tools', () => {
    expect(TOP_TOOLS).toHaveLength(5);
  });

  it('pct values sum to 100 (all data accounted for)', () => {
    const total = TOP_TOOLS.reduce((acc, t) => acc + t.pct, 0);
    expect(total).toBe(100);
  });

  it('ranks are 1 through 5 in order', () => {
    const ranks = TOP_TOOLS.map(t => t.rank);
    expect(ranks).toEqual([1, 2, 3, 4, 5]);
  });

  it('all tool names are non-empty', () => {
    for (const tool of TOP_TOOLS) {
      expect(tool.name.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// STUB_METRICS (inline from page.tsx)
// ---------------------------------------------------------------------------

const STUB_METRICS = {
  activeMembers7d: 847,
  toolsUsed7d: 2341,
  avgUrgeHandledPct: 73,
  wellbeingIndex: 6.8,
};

describe('STUB_METRICS', () => {
  it('activeMembers7d is a positive integer', () => {
    expect(Number.isInteger(STUB_METRICS.activeMembers7d)).toBe(true);
    expect(STUB_METRICS.activeMembers7d).toBeGreaterThan(0);
  });

  it('toolsUsed7d is a positive integer', () => {
    expect(Number.isInteger(STUB_METRICS.toolsUsed7d)).toBe(true);
    expect(STUB_METRICS.toolsUsed7d).toBeGreaterThan(0);
  });

  it('avgUrgeHandledPct is in [0, 100]', () => {
    expect(STUB_METRICS.avgUrgeHandledPct).toBeGreaterThanOrEqual(0);
    expect(STUB_METRICS.avgUrgeHandledPct).toBeLessThanOrEqual(100);
  });

  it('wellbeingIndex is in [0, 10] (WHO-5 display range after ×4 scaling)', () => {
    expect(STUB_METRICS.wellbeingIndex).toBeGreaterThanOrEqual(0);
    expect(STUB_METRICS.wellbeingIndex).toBeLessThanOrEqual(10);
  });

  it('toolsUsed7d exceeds activeMembers7d (multiple tools per active member)', () => {
    expect(STUB_METRICS.toolsUsed7d).toBeGreaterThan(STUB_METRICS.activeMembers7d);
  });
});

// ---------------------------------------------------------------------------
// DEPARTMENTS (inline from page.tsx) — k-anonymity suppression in table data
// ---------------------------------------------------------------------------

interface DeptRow {
  name: string;
  members: number;
  active7d: number | null;
  wellbeingIndex: number | null;
}

const DEPARTMENTS: DeptRow[] = [
  { name: 'Engineering', members: 234, active7d: 189, wellbeingIndex: 6.9 },
  { name: 'Operations', members: 156, active7d: 121, wellbeingIndex: 6.6 },
  { name: 'Sales', members: 98, active7d: 74, wellbeingIndex: 7.1 },
  { name: 'HR', members: 45, active7d: 38, wellbeingIndex: 7.4 },
  { name: 'Legal', members: 3, active7d: null, wellbeingIndex: null },
];

describe('DEPARTMENTS', () => {
  it('has exactly 5 department rows', () => {
    expect(DEPARTMENTS).toHaveLength(5);
  });

  it('all department names are non-empty', () => {
    for (const dept of DEPARTMENTS) {
      expect(dept.name.length).toBeGreaterThan(0);
    }
  });

  it('all member counts are positive integers', () => {
    for (const dept of DEPARTMENTS) {
      expect(Number.isInteger(dept.members)).toBe(true);
      expect(dept.members).toBeGreaterThan(0);
    }
  });

  it('departments with members ≥ 5 have non-null active7d (no false suppression)', () => {
    const aboveK = DEPARTMENTS.filter((d) => d.members >= 5);
    for (const dept of aboveK) {
      expect(dept.active7d).not.toBeNull();
    }
  });

  it('departments with members ≥ 5 have non-null wellbeingIndex', () => {
    const aboveK = DEPARTMENTS.filter((d) => d.members >= 5);
    for (const dept of aboveK) {
      expect(dept.wellbeingIndex).not.toBeNull();
    }
  });

  it('Legal department (3 members) has null active7d (k < 5 suppression)', () => {
    const legal = DEPARTMENTS.find((d) => d.name === 'Legal');
    expect(legal).toBeDefined();
    expect(legal?.members).toBe(3);
    expect(legal?.active7d).toBeNull();
  });

  it('Legal department has null wellbeingIndex (k < 5 suppression)', () => {
    const legal = DEPARTMENTS.find((d) => d.name === 'Legal');
    expect(legal?.wellbeingIndex).toBeNull();
  });

  it('exactly 1 department has null cells (only Legal is below k threshold)', () => {
    const suppressed = DEPARTMENTS.filter((d) => d.active7d === null);
    expect(suppressed).toHaveLength(1);
    expect(suppressed[0]?.name).toBe('Legal');
  });

  it('wellbeingIndex values for non-suppressed depts are in [0, 10]', () => {
    const nonSuppressed = DEPARTMENTS.filter((d) => d.wellbeingIndex !== null);
    for (const dept of nonSuppressed) {
      expect(dept.wellbeingIndex!).toBeGreaterThanOrEqual(0);
      expect(dept.wellbeingIndex!).toBeLessThanOrEqual(10);
    }
  });

  it('department names are unique', () => {
    const names = DEPARTMENTS.map((d) => d.name);
    expect(new Set(names).size).toBe(names.length);
  });
});
