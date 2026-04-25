/**
 * Unit tests for PatientTabs pure helper logic.
 *
 * Tests inline-extracted functions from src/components/PatientTabs.tsx
 * WITHOUT rendering React.
 *
 * Covers:
 * - formatDate: UTC-based date formatting (YYYY-MM-DD)
 * - urgeIntensityColor: threshold logic (≤3/≤6/>6) for the intensity bar
 * - hasScope: PHI access gate logic
 * - journalPlural: entry count pluralization
 * - TABS: exactly 3 tabs exist (check_ins, assessments, journal)
 * - Assessment score sort: lexicographic date sort is chronological for ISO 8601
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// formatDate (inline from PatientTabs.tsx — uses UTC methods, timezone-safe)
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
}

// ---------------------------------------------------------------------------
// urgeIntensityColor (inline from bar style logic in CheckInsView)
// ---------------------------------------------------------------------------

function urgeIntensityColor(intensity: number): string {
  if (intensity <= 3) return 'hsl(142,71%,45%)';  // green
  if (intensity <= 6) return 'hsl(38,92%,50%)';   // amber
  return 'hsl(0,84%,60%)';                          // red (crisis range)
}

// ---------------------------------------------------------------------------
// hasScope — PHI access gate: scopes.includes(tab.id)
// ---------------------------------------------------------------------------

function hasScope(scopes: string[], tabId: string): boolean {
  return scopes.includes(tabId);
}

// ---------------------------------------------------------------------------
// journalPlural — entry count pluralization
// ---------------------------------------------------------------------------

function journalPlural(count: number): string {
  return count === 1 ? 'journal entry' : 'journal entries';
}

// ---------------------------------------------------------------------------
// TABS static list
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'check_ins', label: 'Check-ins' },
  { id: 'assessments', label: 'Assessments' },
  { id: 'journal', label: 'Journal' },
];

// ---------------------------------------------------------------------------
// formatDate tests
// ---------------------------------------------------------------------------

describe('formatDate', () => {
  it('formats ISO datetime as YYYY-MM-DD', () => {
    expect(formatDate('2026-04-25T14:30:00Z')).toBe('2026-04-25');
  });

  it('uses UTC date (midnight boundary)', () => {
    // 2026-04-25T23:00:00Z is still Apr 25 in UTC
    expect(formatDate('2026-04-25T23:00:00Z')).toBe('2026-04-25');
  });

  it('pads single-digit month', () => {
    expect(formatDate('2026-03-05T12:00:00Z')).toBe('2026-03-05');
  });

  it('pads single-digit day', () => {
    expect(formatDate('2026-01-07T12:00:00Z')).toBe('2026-01-07');
  });

  it('formats another valid date', () => {
    expect(formatDate('2025-12-31T12:00:00Z')).toBe('2025-12-31');
  });
});

// ---------------------------------------------------------------------------
// urgeIntensityColor tests
// ---------------------------------------------------------------------------

describe('urgeIntensityColor', () => {
  it('returns green for intensity 1', () => {
    expect(urgeIntensityColor(1)).toBe('hsl(142,71%,45%)');
  });

  it('returns green for intensity 3 (upper green bound)', () => {
    expect(urgeIntensityColor(3)).toBe('hsl(142,71%,45%)');
  });

  it('returns amber for intensity 4 (lower amber bound)', () => {
    expect(urgeIntensityColor(4)).toBe('hsl(38,92%,50%)');
  });

  it('returns amber for intensity 6 (upper amber bound)', () => {
    expect(urgeIntensityColor(6)).toBe('hsl(38,92%,50%)');
  });

  it('returns red for intensity 7 (crisis range threshold)', () => {
    expect(urgeIntensityColor(7)).toBe('hsl(0,84%,60%)');
  });

  it('returns red for intensity 10 (maximum)', () => {
    expect(urgeIntensityColor(10)).toBe('hsl(0,84%,60%)');
  });
});

// ---------------------------------------------------------------------------
// hasScope tests (PHI access gate)
// ---------------------------------------------------------------------------

describe('hasScope', () => {
  it('returns true when scope is present', () => {
    expect(hasScope(['check_ins', 'assessments'], 'check_ins')).toBe(true);
  });

  it('returns false when scope is absent', () => {
    expect(hasScope(['check_ins'], 'journal')).toBe(false);
  });

  it('returns false for empty scopes array', () => {
    expect(hasScope([], 'check_ins')).toBe(false);
  });

  it('returns true when all scopes are granted', () => {
    const allScopes = ['check_ins', 'assessments', 'journal'];
    for (const scope of allScopes) {
      expect(hasScope(allScopes, scope)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// journalPlural tests
// ---------------------------------------------------------------------------

describe('journalPlural', () => {
  it('returns singular for count 1', () => {
    expect(journalPlural(1)).toBe('journal entry');
  });

  it('returns plural for count 0', () => {
    expect(journalPlural(0)).toBe('journal entries');
  });

  it('returns plural for count 2', () => {
    expect(journalPlural(2)).toBe('journal entries');
  });

  it('returns plural for large count', () => {
    expect(journalPlural(100)).toBe('journal entries');
  });
});

// ---------------------------------------------------------------------------
// TABS static list
// ---------------------------------------------------------------------------

describe('TABS', () => {
  it('has exactly 3 tabs', () => {
    expect(TABS).toHaveLength(3);
  });

  it('includes check_ins tab', () => {
    expect(TABS.some(t => t.id === 'check_ins')).toBe(true);
  });

  it('includes assessments tab', () => {
    expect(TABS.some(t => t.id === 'assessments')).toBe(true);
  });

  it('includes journal tab', () => {
    expect(TABS.some(t => t.id === 'journal')).toBe(true);
  });

  it('all tab IDs are non-empty strings', () => {
    for (const tab of TABS) {
      expect(tab.id.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// Assessment score sort (ISO 8601 lexicographic order = chronological)
// ---------------------------------------------------------------------------

describe('assessment score sort by date', () => {
  it('sorts ascending by ISO date string', () => {
    const scores = [
      { date: '2026-04-20T10:00:00Z', score: 14 },
      { date: '2026-03-15T10:00:00Z', score: 8 },
      { date: '2026-04-01T10:00:00Z', score: 10 },
    ];
    const sorted = [...scores].sort((a, b) => a.date.localeCompare(b.date));
    expect(sorted[0]?.score).toBe(8);
    expect(sorted[1]?.score).toBe(10);
    expect(sorted[2]?.score).toBe(14);
  });

  it('ISO 8601 lexicographic sort is equivalent to chronological for same timezone', () => {
    const dates = ['2026-12-01', '2026-01-01', '2026-06-15'];
    const sorted = [...dates].sort((a, b) => a.localeCompare(b));
    expect(sorted[0]).toBe('2026-01-01');
    expect(sorted[1]).toBe('2026-06-15');
    expect(sorted[2]).toBe('2026-12-01');
  });
});
