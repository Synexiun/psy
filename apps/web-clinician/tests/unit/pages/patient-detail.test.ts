/**
 * Unit tests for pure helpers from the individual patient detail page.
 *
 * Tests inline-extracted data and functions from
 * src/app/[locale]/clients/[patientId]/page.tsx.
 *
 * PHI boundary note: this page is behind TWO auth gates:
 *   1. Middleware role check (clinician role required)
 *   2. StepUpGate Clerk re-verification before rendering individual data
 *
 * The stub data must be clinically coherent so developers can reason about
 * the UI without needing real patient data. Key constraints tested here:
 *
 *   - All patient IDs are obviously-fake UUIDs (no real PHI in stubs)
 *   - journalEntryCount must be 0 for any patient without 'journal' scope
 *     — otherwise a journal count is leaked to an unauthorized clinician
 *   - PHQ-9 scores must be in [0, 27]; GAD-7 scores in [0, 21]
 *   - urgeIntensity values must be in [1, 10]
 *   - formatDate uses UTC methods (Latin digits — CLAUDE.md Rule #9)
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// STUB_PATIENTS (inline from page.tsx)
// ---------------------------------------------------------------------------

interface AssessmentScore {
  date: string;
  instrument: string;
  score: number;
  severity: string;
}

interface CheckInEntry {
  date: string;
  urgeIntensity: number;
  notes: string;
}

interface PatientStub {
  displayIndex: number;
  patientId: string;
  scopes: string[];
  lastCheckIn: string;
  checkIns: CheckInEntry[];
  assessmentScores: AssessmentScore[];
  journalEntryCount: number;
}

const STUB_PATIENTS: Record<string, PatientStub> = {
  '00000000-0000-0000-0000-000000000001': {
    displayIndex: 1,
    patientId: '00000000-0000-0000-0000-000000000001',
    scopes: ['check_ins', 'assessments'],
    lastCheckIn: '2026-04-22',
    checkIns: [
      { date: '2026-04-22', urgeIntensity: 3, notes: '' },
      { date: '2026-04-19', urgeIntensity: 6, notes: '' },
      { date: '2026-04-15', urgeIntensity: 4, notes: '' },
    ],
    assessmentScores: [
      { date: '2026-04-01', instrument: 'PHQ-9', score: 11, severity: 'Moderate' },
      { date: '2026-03-01', instrument: 'PHQ-9', score: 14, severity: 'Moderate' },
      { date: '2026-02-01', instrument: 'PHQ-9', score: 17, severity: 'Moderately Severe' },
      { date: '2026-04-01', instrument: 'GAD-7', score: 8, severity: 'Moderate' },
      { date: '2026-03-01', instrument: 'GAD-7', score: 10, severity: 'Moderate' },
    ],
    journalEntryCount: 0,
  },
  '00000000-0000-0000-0000-000000000002': {
    displayIndex: 2,
    patientId: '00000000-0000-0000-0000-000000000002',
    scopes: ['check_ins', 'assessments', 'journal'],
    lastCheckIn: '2026-04-20',
    checkIns: [
      { date: '2026-04-20', urgeIntensity: 7, notes: '' },
      { date: '2026-04-17', urgeIntensity: 5, notes: '' },
      { date: '2026-04-12', urgeIntensity: 8, notes: '' },
    ],
    assessmentScores: [
      { date: '2026-04-05', instrument: 'PHQ-9', score: 7, severity: 'Mild' },
      { date: '2026-03-05', instrument: 'PHQ-9', score: 9, severity: 'Mild' },
      { date: '2026-04-05', instrument: 'GAD-7', score: 5, severity: 'Mild' },
      { date: '2026-03-05', instrument: 'GAD-7', score: 7, severity: 'Mild' },
    ],
    journalEntryCount: 12,
  },
};

// ---------------------------------------------------------------------------
// formatDate (inline from page.tsx — UTC-based for Latin-digit compliance)
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  const d = new Date(iso);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const patients = Object.values(STUB_PATIENTS);

// ---------------------------------------------------------------------------
// STUB_PATIENTS — shape and count
// ---------------------------------------------------------------------------

describe('STUB_PATIENTS', () => {
  it('has exactly 2 stub patients', () => {
    expect(patients).toHaveLength(2);
  });

  it('all patientIds are obviously-fake zero-filled UUIDs (no real PHI)', () => {
    for (const p of patients) {
      // Fake stubs follow the pattern 00000000-0000-0000-0000-00000000000N
      expect(p.patientId).toMatch(/^0{8}-0{4}-0{4}-0{4}-0{10}[0-9]+$/);
    }
  });

  it('all patientIds are valid UUID format', () => {
    for (const p of patients) {
      expect(p.patientId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/,
      );
    }
  });

  it('displayIndex starts at 1 (Patient #1, not #0)', () => {
    expect(patients[0]?.displayIndex).toBe(1);
  });

  it('displayIndex values are unique', () => {
    const indices = patients.map((p) => p.displayIndex);
    expect(new Set(indices).size).toBe(indices.length);
  });

  it('all lastCheckIn values parse as valid ISO dates', () => {
    for (const p of patients) {
      const d = new Date(p.lastCheckIn);
      expect(Number.isNaN(d.getTime())).toBe(false);
    }
  });

  it('all patients have check_ins scope', () => {
    for (const p of patients) {
      expect(p.scopes).toContain('check_ins');
    }
  });

  it('all patients have assessments scope', () => {
    for (const p of patients) {
      expect(p.scopes).toContain('assessments');
    }
  });
});

// ---------------------------------------------------------------------------
// PHI scope gate — journalEntryCount must be 0 without journal scope
// ---------------------------------------------------------------------------

describe('STUB_PATIENTS — journal scope gate', () => {
  it('patients without journal scope have journalEntryCount of 0 (no count leakage)', () => {
    const withoutJournal = patients.filter((p) => !p.scopes.includes('journal'));
    for (const p of withoutJournal) {
      expect(p.journalEntryCount).toBe(0);
    }
  });

  it('patients with journal scope may have non-zero journalEntryCount', () => {
    const withJournal = patients.filter((p) => p.scopes.includes('journal'));
    expect(withJournal.length).toBeGreaterThan(0);
    // At least one patient with journal scope has a count > 0
    const hasNonZeroCount = withJournal.some((p) => p.journalEntryCount > 0);
    expect(hasNonZeroCount).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// checkIns — urge intensity range (1–10)
// ---------------------------------------------------------------------------

describe('STUB_PATIENTS — checkIn urgeIntensity', () => {
  it('all urge intensity values are in the [1, 10] range', () => {
    for (const p of patients) {
      for (const c of p.checkIns) {
        expect(c.urgeIntensity).toBeGreaterThanOrEqual(1);
        expect(c.urgeIntensity).toBeLessThanOrEqual(10);
      }
    }
  });

  it('all checkIn dates parse as valid ISO dates', () => {
    for (const p of patients) {
      for (const c of p.checkIns) {
        const d = new Date(c.date);
        expect(Number.isNaN(d.getTime())).toBe(false);
      }
    }
  });

  it('all patients have at least 2 check-in entries (enough for trend display)', () => {
    for (const p of patients) {
      expect(p.checkIns.length).toBeGreaterThanOrEqual(2);
    }
  });
});

// ---------------------------------------------------------------------------
// assessmentScores — clinical score range validation
// ---------------------------------------------------------------------------

describe('STUB_PATIENTS — PHQ-9 score range', () => {
  it('all PHQ-9 scores are in [0, 27] (validated instrument range)', () => {
    for (const p of patients) {
      const phq9 = p.assessmentScores.filter((s) => s.instrument === 'PHQ-9');
      for (const score of phq9) {
        expect(score.score).toBeGreaterThanOrEqual(0);
        expect(score.score).toBeLessThanOrEqual(27);
      }
    }
  });

  it('PHQ-9 severity labels are non-empty strings', () => {
    for (const p of patients) {
      const phq9 = p.assessmentScores.filter((s) => s.instrument === 'PHQ-9');
      for (const score of phq9) {
        expect(score.severity.length).toBeGreaterThan(0);
      }
    }
  });
});

describe('STUB_PATIENTS — GAD-7 score range', () => {
  it('all GAD-7 scores are in [0, 21] (validated instrument range)', () => {
    for (const p of patients) {
      const gad7 = p.assessmentScores.filter((s) => s.instrument === 'GAD-7');
      for (const score of gad7) {
        expect(score.score).toBeGreaterThanOrEqual(0);
        expect(score.score).toBeLessThanOrEqual(21);
      }
    }
  });

  it('all assessment score dates parse as valid ISO dates', () => {
    for (const p of patients) {
      for (const score of p.assessmentScores) {
        const d = new Date(score.date);
        expect(Number.isNaN(d.getTime())).toBe(false);
      }
    }
  });

  it('all instrument names are non-empty strings', () => {
    for (const p of patients) {
      for (const score of p.assessmentScores) {
        expect(score.instrument.length).toBeGreaterThan(0);
      }
    }
  });
});

// ---------------------------------------------------------------------------
// formatDate — UTC-based Latin-digit compliance (CLAUDE.md Rule #9)
// ---------------------------------------------------------------------------

describe('formatDate', () => {
  it('formats ISO date string as YYYY-MM-DD', () => {
    expect(formatDate('2026-04-22')).toBe('2026-04-22');
  });

  it('formats ISO datetime as date-only', () => {
    expect(formatDate('2026-04-22T14:30:00Z')).toBe('2026-04-22');
  });

  it('uses UTC date — midnight boundary test', () => {
    expect(formatDate('2026-04-22T23:00:00Z')).toBe('2026-04-22');
  });

  it('pads single-digit month', () => {
    expect(formatDate('2026-03-05')).toBe('2026-03-05');
  });

  it('pads single-digit day', () => {
    expect(formatDate('2026-04-05')).toBe('2026-04-05');
  });

  it('output contains only ASCII characters (Latin digits, Rule #9)', () => {
    const result = formatDate('2026-04-22');
    for (const ch of result) {
      expect(ch.charCodeAt(0)).toBeLessThan(128);
    }
  });

  it('output matches YYYY-MM-DD format', () => {
    expect(formatDate('2026-11-30')).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('matches the UTC date from lastCheckIn values in STUB_PATIENTS', () => {
    for (const p of patients) {
      const formatted = formatDate(p.lastCheckIn);
      expect(formatted).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });
});
