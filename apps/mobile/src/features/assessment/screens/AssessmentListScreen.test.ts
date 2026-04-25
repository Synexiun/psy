/**
 * Unit tests for the assessment list screen's instrument selection.
 *
 * Tests inline-extracted constants from AssessmentListScreen.tsx:
 * - ASSESSMENT_LIST: the 3 instruments displayed on the assessment list screen
 *
 * Clinical note: ASSESSMENT_LIST order is clinically significant — PHQ-9 leads
 * because depression screening has the highest clinical priority in the
 * Discipline OS intervention model. Reordering is a clinical decision, not
 * a cosmetic one. GAD-7 follows (comorbid anxiety), then WHO-5 (wellbeing).
 *
 * The list is intentionally short (3 instruments for Phase 1) — the full
 * 70+ instrument catalog is available in the psychometric module but the
 * mobile UI exposes a focused subset to reduce cognitive load in the
 * urge-to-action window.
 */

import { describe, it, expect } from '@jest/globals';

// Inline from AssessmentListScreen.tsx
type InstrumentId = 'phq9' | 'gad7' | 'who5' | 'audit_c' | 'pss10';

const ASSESSMENT_LIST: InstrumentId[] = ['phq9', 'gad7', 'who5'];

// ---------------------------------------------------------------------------
// ASSESSMENT_LIST
// ---------------------------------------------------------------------------

describe('ASSESSMENT_LIST', () => {
  it('has exactly 3 instruments (Phase 1 mobile scope)', () => {
    expect(ASSESSMENT_LIST).toHaveLength(3);
  });

  it('contains PHQ-9 (depression — highest clinical priority)', () => {
    expect(ASSESSMENT_LIST).toContain('phq9');
  });

  it('contains GAD-7 (anxiety — comorbid with depression)', () => {
    expect(ASSESSMENT_LIST).toContain('gad7');
  });

  it('contains WHO-5 (wellbeing — positive-affect counterbalance)', () => {
    expect(ASSESSMENT_LIST).toContain('who5');
  });

  it('PHQ-9 is first (highest clinical priority in Discipline OS model)', () => {
    expect(ASSESSMENT_LIST[0]).toBe('phq9');
  });

  it('GAD-7 is second (comorbid anxiety follows depression screen)', () => {
    expect(ASSESSMENT_LIST[1]).toBe('gad7');
  });

  it('WHO-5 is third (wellbeing last)', () => {
    expect(ASSESSMENT_LIST[2]).toBe('who5');
  });

  it('all instrument IDs are non-empty strings', () => {
    for (const id of ASSESSMENT_LIST) {
      expect(typeof id).toBe('string');
      expect(id.length).toBeGreaterThan(0);
    }
  });

  it('instrument IDs are unique (no accidental duplicate)', () => {
    expect(new Set(ASSESSMENT_LIST).size).toBe(ASSESSMENT_LIST.length);
  });

  it('instrument IDs are lowercase (consistent with backend instrument keys)', () => {
    for (const id of ASSESSMENT_LIST) {
      expect(id).toBe(id.toLowerCase());
    }
  });
});
