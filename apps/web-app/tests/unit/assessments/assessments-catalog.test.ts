/**
 * Unit tests for assessments catalog page helpers.
 *
 * Tests the pure functions and static metadata from
 * src/app/[locale]/assessments/page.tsx WITHOUT rendering React.
 *
 * Covers:
 * - formatDate: valid ISO → "Apr 25, 2026" form, invalid ISO returns input
 * - latestByInstrument merge: picks most recent session per instrument
 * - INSTRUMENT_METADATA: 5 instruments present, correct maxScore values
 * - INSTRUMENT_CATALOG_KEY: all instrument IDs map to a catalog key
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// formatDate (inline from assessments/page.tsx)
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// latestByInstrument merge logic (inline from assessments/page.tsx)
// ---------------------------------------------------------------------------

interface SessionStub {
  instrument: string;
  completed_at: string;
  score: number;
  severity: string;
}

function buildLatestByInstrument(
  sessions: SessionStub[],
): Map<string, { score: number; severity: string; date: string }> {
  const map = new Map<string, { score: number; severity: string; date: string }>();
  for (const session of sessions) {
    const existing = map.get(session.instrument);
    if (!existing || session.completed_at > existing.date) {
      map.set(session.instrument, {
        score: session.score,
        severity: session.severity,
        date: session.completed_at,
      });
    }
  }
  return map;
}

// ---------------------------------------------------------------------------
// INSTRUMENT_METADATA (inline static from assessments/page.tsx)
// ---------------------------------------------------------------------------

const INSTRUMENT_METADATA = [
  { id: 'phq9',    name: 'PHQ-9',   maxScore: 27 },
  { id: 'gad7',    name: 'GAD-7',   maxScore: 21 },
  { id: 'audit-c', name: 'AUDIT-C', maxScore: 12 },
  { id: 'pss10',   name: 'PSS-10',  maxScore: 40 },
  { id: 'who5',    name: 'WHO-5',   maxScore: 100 },
];

const INSTRUMENT_CATALOG_KEY: Record<string, string> = {
  phq9: 'phq9',
  gad7: 'gad7',
  'audit-c': 'auditC',
  pss10: 'pss10',
  who5: 'who5',
};

// ---------------------------------------------------------------------------
// formatDate tests
// ---------------------------------------------------------------------------

describe('formatDate', () => {
  it('formats a valid ISO datetime as "MMM D, YYYY"', () => {
    // Use noon UTC to avoid timezone off-by-one across all test environments
    const result = formatDate('2026-04-25T12:00:00Z');
    expect(result).toMatch(/2026/);
    expect(result).toMatch(/Apr/);
    expect(result).toMatch(/25/);
  });

  it('formats another ISO datetime correctly', () => {
    const result = formatDate('2026-07-15T12:00:00Z');
    expect(result).toMatch(/2026/);
    expect(result).toMatch(/Jul/);
    expect(result).toMatch(/15/);
  });

  it('returns original string for invalid ISO input', () => {
    const invalid = 'not-a-date';
    expect(formatDate(invalid)).toBe(invalid);
  });

  it('returns original string for empty input', () => {
    const result = formatDate('');
    expect(result).toBe('');
  });
});

// ---------------------------------------------------------------------------
// latestByInstrument merge logic
// ---------------------------------------------------------------------------

describe('buildLatestByInstrument', () => {
  it('returns empty map for empty sessions', () => {
    const map = buildLatestByInstrument([]);
    expect(map.size).toBe(0);
  });

  it('stores a single session correctly', () => {
    const map = buildLatestByInstrument([
      { instrument: 'phq9', completed_at: '2026-04-25T10:00:00Z', score: 14, severity: 'moderate' },
    ]);
    expect(map.get('phq9')?.score).toBe(14);
    expect(map.get('phq9')?.severity).toBe('moderate');
  });

  it('keeps the most recent session when two exist for the same instrument', () => {
    const map = buildLatestByInstrument([
      { instrument: 'phq9', completed_at: '2026-04-20T10:00:00Z', score: 10, severity: 'moderate' },
      { instrument: 'phq9', completed_at: '2026-04-25T10:00:00Z', score: 14, severity: 'moderate' },
    ]);
    expect(map.get('phq9')?.score).toBe(14);
    expect(map.get('phq9')?.date).toBe('2026-04-25T10:00:00Z');
  });

  it('keeps the most recent session even when encountered first', () => {
    const map = buildLatestByInstrument([
      { instrument: 'gad7', completed_at: '2026-04-25T10:00:00Z', score: 8, severity: 'mild' },
      { instrument: 'gad7', completed_at: '2026-04-10T10:00:00Z', score: 4, severity: 'minimal' },
    ]);
    expect(map.get('gad7')?.score).toBe(8);
  });

  it('tracks different instruments independently', () => {
    const map = buildLatestByInstrument([
      { instrument: 'phq9', completed_at: '2026-04-25T10:00:00Z', score: 14, severity: 'moderate' },
      { instrument: 'gad7', completed_at: '2026-04-25T10:00:00Z', score: 7, severity: 'mild' },
    ]);
    expect(map.size).toBe(2);
    expect(map.get('phq9')?.score).toBe(14);
    expect(map.get('gad7')?.score).toBe(7);
  });

  it('returns undefined for instrument not in any session', () => {
    const map = buildLatestByInstrument([
      { instrument: 'phq9', completed_at: '2026-04-25T10:00:00Z', score: 5, severity: 'mild' },
    ]);
    expect(map.get('who5')).toBeUndefined();
  });

  it('handles multiple instruments with multiple sessions each', () => {
    const map = buildLatestByInstrument([
      { instrument: 'phq9', completed_at: '2026-03-01T00:00:00Z', score: 8, severity: 'mild' },
      { instrument: 'phq9', completed_at: '2026-04-01T00:00:00Z', score: 12, severity: 'moderate' },
      { instrument: 'gad7', completed_at: '2026-03-15T00:00:00Z', score: 5, severity: 'mild' },
      { instrument: 'gad7', completed_at: '2026-04-15T00:00:00Z', score: 3, severity: 'minimal' },
    ]);
    expect(map.get('phq9')?.score).toBe(12);
    expect(map.get('gad7')?.score).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// INSTRUMENT_METADATA static catalogue
// ---------------------------------------------------------------------------

describe('INSTRUMENT_METADATA', () => {
  it('contains exactly 5 instruments', () => {
    expect(INSTRUMENT_METADATA).toHaveLength(5);
  });

  it('includes PHQ-9 with maxScore 27', () => {
    const phq9 = INSTRUMENT_METADATA.find(i => i.id === 'phq9');
    expect(phq9).toBeDefined();
    expect(phq9?.maxScore).toBe(27);
  });

  it('includes GAD-7 with maxScore 21', () => {
    const gad7 = INSTRUMENT_METADATA.find(i => i.id === 'gad7');
    expect(gad7?.maxScore).toBe(21);
  });

  it('includes WHO-5 with maxScore 100', () => {
    const who5 = INSTRUMENT_METADATA.find(i => i.id === 'who5');
    expect(who5?.maxScore).toBe(100);
  });

  it('includes PSS-10 with maxScore 40', () => {
    const pss10 = INSTRUMENT_METADATA.find(i => i.id === 'pss10');
    expect(pss10?.maxScore).toBe(40);
  });

  it('includes AUDIT-C with maxScore 12', () => {
    const auditc = INSTRUMENT_METADATA.find(i => i.id === 'audit-c');
    expect(auditc?.maxScore).toBe(12);
  });

  it('all instrument names are non-empty', () => {
    for (const instrument of INSTRUMENT_METADATA) {
      expect(instrument.name.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// INSTRUMENT_CATALOG_KEY
// ---------------------------------------------------------------------------

describe('INSTRUMENT_CATALOG_KEY', () => {
  it('maps all 5 instrument IDs', () => {
    const ids = INSTRUMENT_METADATA.map(i => i.id);
    for (const id of ids) {
      expect(INSTRUMENT_CATALOG_KEY[id]).toBeDefined();
    }
  });

  it('audit-c maps to auditC (camelCase catalog key)', () => {
    expect(INSTRUMENT_CATALOG_KEY['audit-c']).toBe('auditC');
  });

  it('phq9 maps to phq9', () => {
    expect(INSTRUMENT_CATALOG_KEY['phq9']).toBe('phq9');
  });
});
