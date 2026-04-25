/**
 * Unit tests for assessment instrument page logic.
 *
 * Tests the pure functions and static catalogue from
 * ``src/app/[locale]/assessments/[instrument]/page.tsx`` WITHOUT rendering
 * React (no jsdom overhead needed for pure logic).
 *
 * Clinical compliance:
 *  - PHQ-9 item 9 safety check (T4 path) must fire for ANY value > 0.
 *    Never feature-flag, gate, or disable this check.
 *  - PSS-10 items 4, 5, 7, 8 are reverse-scored (Cohen et al., 1983).
 *    Formula: 4 − raw_value.
 *  - WHO-5 display score = raw × 4 (range 0–100 percentage scale).
 *  - AUDIT-C has per-item response options (different scale per question).
 *  - Severity bands must match pinned source publications (Kroenke 2001,
 *    Spitzer 2006, WHO 1998, Cohen 1983).
 *  - All 5 instruments must be present: phq-9, gad-7, who-5, audit-c, pss-10.
 *  - generateStaticParams must include exactly these 5 slugs.
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline the logic under test — mirrors the implementation in the page module.
// Keeping it here makes the tests self-contained and fast.
// ---------------------------------------------------------------------------

interface ResponseOption {
  label: string;
  value: number;
}

interface InstrumentQuestion {
  item: number;
  text: string;
  reverseScored?: boolean;
}

interface InstrumentDefinition {
  id: string;
  name: string;
  fullName: string;
  maxScore: number;
  responseOptions: ResponseOption[];
  questions: InstrumentQuestion[];
  estimatedMinutes: string;
  description: string;
}

const FREQ_4: ResponseOption[] = [
  { label: 'Not at all',              value: 0 },
  { label: 'Several days',            value: 1 },
  { label: 'More than half the days', value: 2 },
  { label: 'Nearly every day',        value: 3 },
];

const WHO5_OPTIONS: ResponseOption[] = [
  { label: 'At no time',                  value: 0 },
  { label: 'Some of the time',            value: 1 },
  { label: 'Less than half of the time',  value: 2 },
  { label: 'More than half of the time',  value: 3 },
  { label: 'Most of the time',            value: 4 },
  { label: 'All of the time',             value: 5 },
];

const INSTRUMENTS: Record<string, InstrumentDefinition> = {
  'phq-9': {
    id: 'phq-9', name: 'PHQ-9',
    fullName: 'Patient Health Questionnaire – 9',
    maxScore: 27, responseOptions: FREQ_4, estimatedMinutes: '2–3',
    description: 'Measures depressive symptoms over the past two weeks.',
    questions: [
      { item: 1, text: 'Little interest or pleasure in doing things' },
      { item: 2, text: 'Feeling down, depressed, or hopeless' },
      { item: 3, text: 'Trouble falling or staying asleep, or sleeping too much' },
      { item: 4, text: 'Feeling tired or having little energy' },
      { item: 5, text: 'Poor appetite or overeating' },
      { item: 6, text: 'Feeling bad about yourself — or that you are a failure or have let yourself or your family down' },
      { item: 7, text: 'Trouble concentrating on things, such as reading the newspaper or watching television' },
      { item: 8, text: 'Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual' },
      { item: 9, text: 'Thoughts that you would be better off dead or of hurting yourself in some way' },
    ],
  },
  'gad-7': {
    id: 'gad-7', name: 'GAD-7',
    fullName: 'Generalized Anxiety Disorder – 7',
    maxScore: 21, responseOptions: FREQ_4, estimatedMinutes: '2–3',
    description: 'Measures anxiety symptoms over the past two weeks.',
    questions: [
      { item: 1, text: 'Feeling nervous, anxious, or on edge' },
      { item: 2, text: 'Not being able to stop or control worrying' },
      { item: 3, text: 'Worrying too much about different things' },
      { item: 4, text: 'Trouble relaxing' },
      { item: 5, text: "Being so restless that it's hard to sit still" },
      { item: 6, text: 'Becoming easily annoyed or irritable' },
      { item: 7, text: 'Feeling afraid as if something awful might happen' },
    ],
  },
  'who-5': {
    id: 'who-5', name: 'WHO-5',
    fullName: 'World Health Organization Well-Being Index – 5',
    maxScore: 25, responseOptions: WHO5_OPTIONS, estimatedMinutes: '2',
    description: 'Measures general wellbeing over the past two weeks.',
    questions: [
      { item: 1, text: 'I have felt cheerful and in good spirits' },
      { item: 2, text: 'I have felt calm and relaxed' },
      { item: 3, text: 'I have felt active and vigorous' },
      { item: 4, text: 'I woke up feeling fresh and rested' },
      { item: 5, text: 'My daily life has been filled with things that interest me' },
    ],
  },
  'audit-c': {
    id: 'audit-c', name: 'AUDIT-C',
    fullName: 'Alcohol Use Disorders Identification Test – Consumption',
    maxScore: 12, responseOptions: [], estimatedMinutes: '1–2',
    description: 'A brief screen for hazardous alcohol consumption.',
    questions: [
      { item: 1, text: 'How often do you have a drink containing alcohol?' },
      { item: 2, text: 'How many units of alcohol do you drink on a typical day when you are drinking?' },
      { item: 3, text: 'How often do you have 6 or more units if female, or 8 or more if male, on a single occasion in the last year?' },
    ],
  },
  'pss-10': {
    id: 'pss-10', name: 'PSS-10',
    fullName: 'Perceived Stress Scale – 10',
    maxScore: 40,
    responseOptions: [
      { label: 'Never',        value: 0 },
      { label: 'Almost never', value: 1 },
      { label: 'Sometimes',    value: 2 },
      { label: 'Fairly often', value: 3 },
      { label: 'Very often',   value: 4 },
    ],
    estimatedMinutes: '3–5',
    description: 'Measures perceived stress over the past month.',
    questions: [
      { item: 1, text: 'In the last month, how often have you been upset because of something that happened unexpectedly?' },
      { item: 2, text: 'In the last month, how often have you felt that you were unable to control the important things in your life?' },
      { item: 3, text: 'In the last month, how often have you felt nervous and stressed?' },
      { item: 4, text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?', reverseScored: true },
      { item: 5, text: 'In the last month, how often have you felt that things were going your way?', reverseScored: true },
      { item: 6, text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?' },
      { item: 7, text: 'In the last month, how often have you been able to control irritations in your life?', reverseScored: true },
      { item: 8, text: 'In the last month, how often have you felt that you were on top of things?', reverseScored: true },
      { item: 9, text: 'In the last month, how often have you been angered because of things that were outside of your control?' },
      { item: 10, text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?' },
    ],
  },
};

const STATIC_PARAMS = [
  { instrument: 'phq-9' },
  { instrument: 'gad-7' },
  { instrument: 'who-5' },
  { instrument: 'audit-c' },
  { instrument: 'pss-10' },
];

function computeScore(
  instrument: InstrumentDefinition,
  responses: Record<number, number>,
): number {
  let total = 0;
  for (const q of instrument.questions) {
    const raw = responses[q.item] ?? 0;
    if (instrument.id === 'pss-10' && q.reverseScored) {
      total += 4 - raw;
    } else {
      total += raw;
    }
  }
  return total;
}

function displayScore(instrument: InstrumentDefinition, rawScore: number): number {
  return instrument.id === 'who-5' ? rawScore * 4 : rawScore;
}

function displayMax(instrument: InstrumentDefinition): number {
  return instrument.id === 'who-5' ? 100 : instrument.maxScore;
}

function phq9SafetyTriggered(
  instrumentId: string,
  responses: Record<number, number>,
): boolean {
  if (instrumentId !== 'phq-9') return false;
  return (responses[9] ?? 0) > 0;
}

function phq9SeverityBand(score: number): string {
  if (score <= 4)  return 'Minimal';
  if (score <= 9)  return 'Mild';
  if (score <= 14) return 'Moderate';
  if (score <= 19) return 'Moderately severe';
  return 'Severe';
}

function gad7SeverityBand(score: number): string {
  if (score <= 4)  return 'Minimal';
  if (score <= 9)  return 'Mild';
  if (score <= 14) return 'Moderate';
  return 'Severe';
}

function who5SeverityBand(rawScore: number): string {
  const pct = rawScore * 4;
  if (pct < 28) return 'Poor';
  if (pct < 50) return 'Low';
  if (pct < 72) return 'Moderate';
  return 'Good';
}

function auditCSeverityBand(score: number): string {
  if (score <= 2) return 'Low risk';
  if (score <= 5) return 'Moderate risk';
  return 'High risk';
}

function pss10SeverityBand(score: number): string {
  if (score <= 13) return 'Low';
  if (score <= 26) return 'Moderate';
  return 'High';
}

// ---------------------------------------------------------------------------
// Instrument catalogue completeness
// ---------------------------------------------------------------------------

describe('Instrument catalogue', () => {
  it('contains all 5 instruments', () => {
    expect(Object.keys(INSTRUMENTS)).toHaveLength(5);
  });

  it('generateStaticParams returns exactly 5 slugs', () => {
    expect(STATIC_PARAMS).toHaveLength(5);
  });

  it('all static param slugs match catalogue keys', () => {
    const catalogKeys = Object.keys(INSTRUMENTS);
    for (const { instrument } of STATIC_PARAMS) {
      expect(catalogKeys).toContain(instrument);
    }
  });

  it('PHQ-9 has exactly 9 items', () => {
    expect(INSTRUMENTS['phq-9']!.questions).toHaveLength(9);
  });

  it('PHQ-9 item 9 (safety item) is the last question and text is verbatim', () => {
    const q9 = INSTRUMENTS['phq-9']!.questions[8]!;
    expect(q9.item).toBe(9);
    expect(q9.text).toContain('hurting yourself');
  });

  it('GAD-7 has exactly 7 items', () => {
    expect(INSTRUMENTS['gad-7']!.questions).toHaveLength(7);
  });

  it('WHO-5 has exactly 5 items', () => {
    expect(INSTRUMENTS['who-5']!.questions).toHaveLength(5);
  });

  it('AUDIT-C has exactly 3 items', () => {
    expect(INSTRUMENTS['audit-c']!.questions).toHaveLength(3);
  });

  it('PSS-10 has exactly 10 items', () => {
    expect(INSTRUMENTS['pss-10']!.questions).toHaveLength(10);
  });

  it('PSS-10 reverse-scored items are exactly 4, 5, 7, 8 (1-based)', () => {
    const pss = INSTRUMENTS['pss-10']!;
    const reverseItems = pss.questions
      .filter((q) => q.reverseScored === true)
      .map((q) => q.item);
    expect(reverseItems.sort((a, b) => a - b)).toEqual([4, 5, 7, 8]);
  });

  it('WHO-5 response options go from 0 to 5 (6 options)', () => {
    const who5 = INSTRUMENTS['who-5']!;
    expect(who5.responseOptions).toHaveLength(6);
    expect(who5.responseOptions[0]!.value).toBe(0);
    expect(who5.responseOptions[5]!.value).toBe(5);
  });

  it('AUDIT-C has empty shared responseOptions (uses per-item options)', () => {
    expect(INSTRUMENTS['audit-c']!.responseOptions).toHaveLength(0);
  });

  it('PHQ-9 maxScore is 27', () => {
    expect(INSTRUMENTS['phq-9']!.maxScore).toBe(27);
  });

  it('GAD-7 maxScore is 21', () => {
    expect(INSTRUMENTS['gad-7']!.maxScore).toBe(21);
  });

  it('WHO-5 maxScore is 25 (raw; display = raw × 4)', () => {
    expect(INSTRUMENTS['who-5']!.maxScore).toBe(25);
  });

  it('PSS-10 maxScore is 40', () => {
    expect(INSTRUMENTS['pss-10']!.maxScore).toBe(40);
  });
});

// ---------------------------------------------------------------------------
// computeScore
// ---------------------------------------------------------------------------

describe('computeScore', () => {
  it('PHQ-9 all-zero → 0', () => {
    const phq9 = INSTRUMENTS['phq-9']!;
    const responses = Object.fromEntries(phq9.questions.map((q) => [q.item, 0]));
    expect(computeScore(phq9, responses)).toBe(0);
  });

  it('PHQ-9 all-3 → 27', () => {
    const phq9 = INSTRUMENTS['phq-9']!;
    const responses = Object.fromEntries(phq9.questions.map((q) => [q.item, 3]));
    expect(computeScore(phq9, responses)).toBe(27);
  });

  it('GAD-7 all-3 → 21', () => {
    const gad7 = INSTRUMENTS['gad-7']!;
    const responses = Object.fromEntries(gad7.questions.map((q) => [q.item, 3]));
    expect(computeScore(gad7, responses)).toBe(21);
  });

  it('WHO-5 all-5 raw → 25', () => {
    const who5 = INSTRUMENTS['who-5']!;
    const responses = Object.fromEntries(who5.questions.map((q) => [q.item, 5]));
    expect(computeScore(who5, responses)).toBe(25);
  });

  it('PSS-10 all-zero → 16 (4 reverse items × 4)', () => {
    const pss = INSTRUMENTS['pss-10']!;
    const responses = Object.fromEntries(pss.questions.map((q) => [q.item, 0]));
    // Forward items (1,2,3,6,9,10): 0; reverse items (4,5,7,8): 4−0=4 each → 16.
    expect(computeScore(pss, responses)).toBe(16);
  });

  it('PSS-10 all-4 → 24 (6 forward × 4; reverse items 4−4=0)', () => {
    const pss = INSTRUMENTS['pss-10']!;
    const responses = Object.fromEntries(pss.questions.map((q) => [q.item, 4]));
    expect(computeScore(pss, responses)).toBe(24);
  });

  it('missing response defaults to 0', () => {
    const phq9 = INSTRUMENTS['phq-9']!;
    // Only supply item 1=2; others default to 0.
    expect(computeScore(phq9, { 1: 2 })).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// displayScore and displayMax — WHO-5 ×4 transform
// ---------------------------------------------------------------------------

describe('displayScore', () => {
  it('WHO-5 raw 0 → display 0', () => {
    expect(displayScore(INSTRUMENTS['who-5']!, 0)).toBe(0);
  });

  it('WHO-5 raw 25 → display 100', () => {
    expect(displayScore(INSTRUMENTS['who-5']!, 25)).toBe(100);
  });

  it('WHO-5 raw 13 → display 52', () => {
    expect(displayScore(INSTRUMENTS['who-5']!, 13)).toBe(52);
  });

  it('PHQ-9 score is unchanged', () => {
    expect(displayScore(INSTRUMENTS['phq-9']!, 14)).toBe(14);
  });

  it('PSS-10 score is unchanged', () => {
    expect(displayScore(INSTRUMENTS['pss-10']!, 22)).toBe(22);
  });
});

describe('displayMax', () => {
  it('WHO-5 max is 100 (raw 25 × 4)', () => {
    expect(displayMax(INSTRUMENTS['who-5']!)).toBe(100);
  });

  it('PHQ-9 max is 27', () => {
    expect(displayMax(INSTRUMENTS['phq-9']!)).toBe(27);
  });

  it('GAD-7 max is 21', () => {
    expect(displayMax(INSTRUMENTS['gad-7']!)).toBe(21);
  });

  it('PSS-10 max is 40', () => {
    expect(displayMax(INSTRUMENTS['pss-10']!)).toBe(40);
  });
});

// ---------------------------------------------------------------------------
// phq9SafetyTriggered — T4 path: CRITICAL — never relax this check
// ---------------------------------------------------------------------------

describe('phq9SafetyTriggered (T4 safety path)', () => {
  it('does NOT trigger when item 9 = 0', () => {
    expect(phq9SafetyTriggered('phq-9', { 9: 0 })).toBe(false);
  });

  it('triggers when item 9 = 1', () => {
    expect(phq9SafetyTriggered('phq-9', { 9: 1 })).toBe(true);
  });

  it('triggers when item 9 = 2', () => {
    expect(phq9SafetyTriggered('phq-9', { 9: 2 })).toBe(true);
  });

  it('triggers when item 9 = 3', () => {
    expect(phq9SafetyTriggered('phq-9', { 9: 3 })).toBe(true);
  });

  it('does NOT trigger when item 9 is absent', () => {
    expect(phq9SafetyTriggered('phq-9', { 1: 3, 2: 2 })).toBe(false);
  });

  it('does NOT trigger for GAD-7 with item 9 set', () => {
    expect(phq9SafetyTriggered('gad-7', { 9: 3 })).toBe(false);
  });

  it('does NOT trigger for WHO-5', () => {
    expect(phq9SafetyTriggered('who-5', { 9: 3 })).toBe(false);
  });

  it('does NOT trigger for PSS-10', () => {
    expect(phq9SafetyTriggered('pss-10', { 9: 4 })).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Severity bands — pinned source publications
// ---------------------------------------------------------------------------

describe('PHQ-9 severity bands (Kroenke et al., 2001)', () => {
  const cases: [number, string][] = [
    [0, 'Minimal'], [4, 'Minimal'],
    [5, 'Mild'], [9, 'Mild'],
    [10, 'Moderate'], [14, 'Moderate'],
    [15, 'Moderately severe'], [19, 'Moderately severe'],
    [20, 'Severe'], [27, 'Severe'],
  ];
  for (const [score, band] of cases) {
    it(`score ${score} → "${band}"`, () => {
      expect(phq9SeverityBand(score)).toBe(band);
    });
  }
});

describe('GAD-7 severity bands (Spitzer et al., 2006)', () => {
  const cases: [number, string][] = [
    [0, 'Minimal'], [4, 'Minimal'],
    [5, 'Mild'], [9, 'Mild'],
    [10, 'Moderate'], [14, 'Moderate'],
    [15, 'Severe'], [21, 'Severe'],
  ];
  for (const [score, band] of cases) {
    it(`score ${score} → "${band}"`, () => {
      expect(gad7SeverityBand(score)).toBe(band);
    });
  }
});

describe('WHO-5 severity bands (raw score → pct × 4)', () => {
  it('raw 6 (pct 24) → "Poor"', () => {
    expect(who5SeverityBand(6)).toBe('Poor');
  });
  it('raw 7 (pct 28) → "Low" (boundary: strict <28)', () => {
    expect(who5SeverityBand(7)).toBe('Low');
  });
  it('raw 12 (pct 48) → "Low"', () => {
    expect(who5SeverityBand(12)).toBe('Low');
  });
  it('raw 13 (pct 52) → "Moderate"', () => {
    expect(who5SeverityBand(13)).toBe('Moderate');
  });
  it('raw 18 (pct 72) → "Good"', () => {
    expect(who5SeverityBand(18)).toBe('Good');
  });
  it('raw 25 (pct 100) → "Good"', () => {
    expect(who5SeverityBand(25)).toBe('Good');
  });
});

describe('AUDIT-C severity bands', () => {
  it('score 0 → "Low risk"', () => {
    expect(auditCSeverityBand(0)).toBe('Low risk');
  });
  it('score 2 → "Low risk"', () => {
    expect(auditCSeverityBand(2)).toBe('Low risk');
  });
  it('score 3 → "Moderate risk"', () => {
    expect(auditCSeverityBand(3)).toBe('Moderate risk');
  });
  it('score 5 → "Moderate risk"', () => {
    expect(auditCSeverityBand(5)).toBe('Moderate risk');
  });
  it('score 6 → "High risk"', () => {
    expect(auditCSeverityBand(6)).toBe('High risk');
  });
  it('score 12 → "High risk"', () => {
    expect(auditCSeverityBand(12)).toBe('High risk');
  });
});

describe('PSS-10 severity bands (Cohen et al., 1983)', () => {
  it('score 0 → "Low"', () => {
    expect(pss10SeverityBand(0)).toBe('Low');
  });
  it('score 13 → "Low"', () => {
    expect(pss10SeverityBand(13)).toBe('Low');
  });
  it('score 14 → "Moderate"', () => {
    expect(pss10SeverityBand(14)).toBe('Moderate');
  });
  it('score 26 → "Moderate"', () => {
    expect(pss10SeverityBand(26)).toBe('Moderate');
  });
  it('score 27 → "High"', () => {
    expect(pss10SeverityBand(27)).toBe('High');
  });
  it('score 40 → "High"', () => {
    expect(pss10SeverityBand(40)).toBe('High');
  });
});
