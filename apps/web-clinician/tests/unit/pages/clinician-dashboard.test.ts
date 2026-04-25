/**
 * Unit tests for pure helpers from the clinician dashboard page.
 *
 * Tests inline-extracted pure data and functions from
 * src/app/[locale]/page.tsx WITHOUT rendering React.
 *
 * Critical: formatCheckInDate uses UTC methods (not Intl.DateTimeFormat)
 * to enforce CLAUDE.md Rule #9 — Latin digits for clinical dates regardless
 * of locale. This is the same pattern as PatientTabs.formatDate.
 *
 * Covers:
 * - formatCheckInDate: UTC-based YYYY-MM-DD formatting (Latin digits)
 * - UrgencyDot config: calm/elevated/high state → color + label mapping
 * - SCOPE_LABELS: scope ID → display label mapping
 * - STUB_PATIENTS: shape and clinical safety constraints
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// formatCheckInDate (inline from page.tsx — uses UTC methods)
// ---------------------------------------------------------------------------

function formatCheckInDate(iso: string): string {
  const d = new Date(iso);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// ---------------------------------------------------------------------------
// UrgencyDot config (inline from page.tsx)
// ---------------------------------------------------------------------------

type UrgencyState = 'calm' | 'elevated' | 'high';

const urgencyConfig: Record<UrgencyState, { color: string; label: string }> = {
  calm: { color: 'bg-[hsl(142,71%,45%)]', label: 'Calm' },
  elevated: { color: 'bg-[hsl(38,92%,50%)]', label: 'Elevated' },
  high: { color: 'bg-[hsl(0,84%,60%)]', label: 'High urgency' },
};

// ---------------------------------------------------------------------------
// SCOPE_LABELS (inline from page.tsx)
// ---------------------------------------------------------------------------

const SCOPE_LABELS: Record<string, string> = {
  check_ins: 'Check-ins',
  assessments: 'Assessments',
  journal: 'Journal',
  patterns: 'Patterns',
};

// ---------------------------------------------------------------------------
// STUB_PATIENTS (inline from page.tsx)
// ---------------------------------------------------------------------------

const STUB_PATIENTS = [
  {
    displayIndex: 1,
    patientId: '00000000-0000-0000-0000-000000000001',
    lastCheckIn: '2026-04-22',
    currentState: 'calm' as UrgencyState,
    scopes: ['check_ins', 'assessments'],
  },
  {
    displayIndex: 2,
    patientId: '00000000-0000-0000-0000-000000000002',
    lastCheckIn: '2026-04-20',
    currentState: 'elevated' as UrgencyState,
    scopes: ['check_ins', 'assessments', 'journal'],
  },
];

// ---------------------------------------------------------------------------
// formatCheckInDate tests (Latin-digit rule compliance, Rule #9)
// ---------------------------------------------------------------------------

describe('formatCheckInDate', () => {
  it('formats ISO date string as YYYY-MM-DD', () => {
    expect(formatCheckInDate('2026-04-22')).toBe('2026-04-22');
  });

  it('formats ISO datetime as date-only (drops time component)', () => {
    expect(formatCheckInDate('2026-04-22T14:30:00Z')).toBe('2026-04-22');
  });

  it('uses UTC date — midnight boundary test', () => {
    // 2026-04-22T23:00:00Z is still Apr 22 in UTC
    expect(formatCheckInDate('2026-04-22T23:00:00Z')).toBe('2026-04-22');
  });

  it('pads single-digit month', () => {
    expect(formatCheckInDate('2026-03-05')).toBe('2026-03-05');
  });

  it('pads single-digit day', () => {
    expect(formatCheckInDate('2026-04-05')).toBe('2026-04-05');
  });

  it('output contains only ASCII characters (Latin digits, Rule #9)', () => {
    const result = formatCheckInDate('2026-04-22');
    for (const ch of result) {
      expect(ch.charCodeAt(0)).toBeLessThan(128);
    }
  });

  it('output matches YYYY-MM-DD format regex', () => {
    const result = formatCheckInDate('2026-11-30');
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

// ---------------------------------------------------------------------------
// UrgencyDot config tests
// ---------------------------------------------------------------------------

describe('urgencyConfig', () => {
  it('has all 3 urgency states', () => {
    expect(Object.keys(urgencyConfig)).toHaveLength(3);
    expect(urgencyConfig).toHaveProperty('calm');
    expect(urgencyConfig).toHaveProperty('elevated');
    expect(urgencyConfig).toHaveProperty('high');
  });

  it('calm uses green color (safe resting state)', () => {
    expect(urgencyConfig['calm'].color).toContain('142');  // green hue
  });

  it('elevated uses amber color (warning state)', () => {
    expect(urgencyConfig['elevated'].color).toContain('38');  // amber hue
  });

  it('high uses red color (crisis range)', () => {
    expect(urgencyConfig['high'].color).toContain('0,84%');  // red hue (0°)
  });

  it('all states have non-empty label', () => {
    for (const { label } of Object.values(urgencyConfig)) {
      expect(label.length).toBeGreaterThan(0);
    }
  });

  it('all states have non-empty color class', () => {
    for (const { color } of Object.values(urgencyConfig)) {
      expect(color.length).toBeGreaterThan(0);
    }
  });

  it('high urgency label mentions "urgency" (not ambiguous)', () => {
    expect(urgencyConfig['high'].label.toLowerCase()).toContain('urgency');
  });
});

// ---------------------------------------------------------------------------
// SCOPE_LABELS tests
// ---------------------------------------------------------------------------

describe('SCOPE_LABELS', () => {
  it('has all 4 scope types', () => {
    expect(Object.keys(SCOPE_LABELS)).toHaveLength(4);
  });

  it('check_ins maps to Check-ins', () => {
    expect(SCOPE_LABELS['check_ins']).toBe('Check-ins');
  });

  it('assessments maps to Assessments', () => {
    expect(SCOPE_LABELS['assessments']).toBe('Assessments');
  });

  it('journal maps to Journal', () => {
    expect(SCOPE_LABELS['journal']).toBe('Journal');
  });

  it('patterns maps to Patterns', () => {
    expect(SCOPE_LABELS['patterns']).toBe('Patterns');
  });

  it('all labels are non-empty', () => {
    for (const label of Object.values(SCOPE_LABELS)) {
      expect(label.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// STUB_PATIENTS tests
// ---------------------------------------------------------------------------

describe('STUB_PATIENTS', () => {
  it('has 2 stub patients', () => {
    expect(STUB_PATIENTS).toHaveLength(2);
  });

  it('all patientIds are UUID-shaped (pseudonymous — no real names)', () => {
    for (const p of STUB_PATIENTS) {
      expect(p.patientId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
      );
    }
  });

  it('displayIndex starts at 1 (Patient #1, not #0)', () => {
    expect(STUB_PATIENTS[0]?.displayIndex).toBe(1);
  });

  it('all current states are valid UrgencyState values', () => {
    const validStates = new Set(['calm', 'elevated', 'high']);
    for (const p of STUB_PATIENTS) {
      expect(validStates.has(p.currentState)).toBe(true);
    }
  });

  it('no stub patient has "high" urgency (stubs should not trigger alert UI)', () => {
    for (const p of STUB_PATIENTS) {
      expect(p.currentState).not.toBe('high');
    }
  });

  it('all scopes are valid scope IDs', () => {
    const validScopes = new Set(Object.keys(SCOPE_LABELS));
    for (const p of STUB_PATIENTS) {
      for (const scope of p.scopes) {
        expect(validScopes.has(scope)).toBe(true);
      }
    }
  });

  it('lastCheckIn parses as valid ISO date', () => {
    for (const p of STUB_PATIENTS) {
      const d = new Date(p.lastCheckIn);
      expect(Number.isNaN(d.getTime())).toBe(false);
    }
  });
});
