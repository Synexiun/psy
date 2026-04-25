/**
 * PHQ-9, GAD-7, and WHO-5 scoring band boundary tests.
 *
 * These tests pin the exact clinical threshold values defined by peer-reviewed
 * citations so a refactor cannot silently shift a band boundary:
 *
 *   PHQ-9: Kroenke, Spitzer & Williams (2001) — pinned in 12_Psychometric_System.md §3.1
 *     0–4  Minimal or none
 *     5–9  Mild
 *     10–14 Moderate
 *     15–19 Moderately severe
 *     20–27 Severe
 *
 *   GAD-7: Spitzer et al. (2006) — pinned in 12_Psychometric_System.md §3.2
 *     0–4  Minimal
 *     5–9  Mild
 *     10–14 Moderate
 *     15–21 Severe
 *
 *   WHO-5: WHO (1998) — raw × 4 = percentage (0–100)
 *     ≥ 72  Good well-being   (raw ≥ 18)
 *     52–71 Moderate well-being (raw 13–17)
 *     < 52  Low well-being    (raw ≤ 12)
 *
 * PHQ-9 item 9 (index 8) safety flag:
 *   Any response ≥ 1 on the suicidal ideation item MUST set safetyFlag.
 *   CLAUDE.md Rule #1: T3/T4 flows are deterministic — this flag drives the
 *   crisis navigation, so the boundary test (response 0 vs 1) is safety-critical.
 *
 * Latin-digit rule (CLAUDE.md Rule #9):
 *   displayScoreString must be ASCII-only regardless of locale or platform.
 */

import { scoreInstrument } from './store';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a PHQ-9 response set summing to exactly `total` (items 0–7 share the load; item 8 = 0). */
function phq9Responses(total: number, item9 = 0): Record<number, number> {
  const r: Record<number, number> = {};
  let remaining = total;
  for (let i = 0; i < 8; i++) {
    const value = Math.min(3, remaining);
    r[i] = value;
    remaining -= value;
  }
  r[8] = item9;
  return r;
}

/** Build a GAD-7 response set summing to exactly `total`. */
function gad7Responses(total: number): Record<number, number> {
  const r: Record<number, number> = {};
  let remaining = total;
  for (let i = 0; i < 7; i++) {
    const value = Math.min(3, remaining);
    r[i] = value;
    remaining -= value;
  }
  return r;
}

/** Build a WHO-5 response set summing to exactly `raw` (items 0–4 each 0–5). */
function who5Responses(raw: number): Record<number, number> {
  const r: Record<number, number> = {};
  let remaining = raw;
  for (let i = 0; i < 5; i++) {
    const value = Math.min(5, remaining);
    r[i] = value;
    remaining -= value;
  }
  return r;
}

function isAsciiOnly(s: string): boolean {
  return Array.from(s).every((c) => c.charCodeAt(0) < 128);
}

// ---------------------------------------------------------------------------
// PHQ-9 band boundaries (Kroenke 2001)
// ---------------------------------------------------------------------------

describe('PHQ-9 severity band boundaries (Kroenke 2001)', () => {
  it('score 4 → Minimal (last minimal score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(4));
    expect(r.raw).toBe(4);
    expect(r.severityLabel).toMatch(/minimal/i);
  });

  it('score 5 → Mild (first mild score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(5));
    expect(r.raw).toBe(5);
    expect(r.severityLabel).toMatch(/mild/i);
  });

  it('score 9 → Mild (last mild score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(9));
    expect(r.raw).toBe(9);
    expect(r.severityLabel).toMatch(/mild/i);
  });

  it('score 10 → Moderate (first moderate score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(10));
    expect(r.raw).toBe(10);
    expect(r.severityLabel).toMatch(/moderate/i);
  });

  it('score 14 → Moderate (last moderate score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(14));
    expect(r.raw).toBe(14);
    expect(r.severityLabel).toMatch(/moderate/i);
    expect(r.severityLabel).not.toMatch(/severe/i);
  });

  it('score 15 → Moderately severe (first mod-severe score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(15));
    expect(r.raw).toBe(15);
    expect(r.severityLabel).toMatch(/moderately severe/i);
  });

  it('score 19 → Moderately severe (last mod-severe score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(19));
    expect(r.raw).toBe(19);
    expect(r.severityLabel).toMatch(/moderately severe/i);
  });

  it('score 20 → Severe (first severe score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(20));
    expect(r.raw).toBe(20);
    expect(r.severityLabel).toMatch(/severe/i);
    expect(r.severityLabel).not.toMatch(/moderate/i);
  });

  it('score 27 → Severe (maximum score)', () => {
    const r = scoreInstrument('phq9', phq9Responses(24, 3)); // 24 across items 0–7, item9=3
    expect(r.raw).toBe(27);
    expect(r.severityLabel).toMatch(/severe/i);
  });

  it('displayScoreString is ASCII-only at each boundary', () => {
    for (const score of [0, 4, 5, 9, 10, 14, 15, 19, 20, 27]) {
      const r = scoreInstrument('phq9', phq9Responses(Math.min(score, 24), score === 27 ? 3 : 0));
      expect(isAsciiOnly(r.displayScoreString)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// PHQ-9 item 9 safety flag — suicidal ideation boundary (safety-critical)
// ---------------------------------------------------------------------------

describe('PHQ-9 item 9 safety flag (suicidal ideation — CLAUDE.md Rule #1)', () => {
  it('item 9 response = 0 → safetyFlag false', () => {
    const r = scoreInstrument('phq9', phq9Responses(0, 0));
    expect(r.safetyFlag).toBe(false);
  });

  it('item 9 response = 1 → safetyFlag true (boundary)', () => {
    const r = scoreInstrument('phq9', phq9Responses(0, 1));
    expect(r.safetyFlag).toBe(true);
  });

  it('item 9 response = 3 → safetyFlag true', () => {
    const r = scoreInstrument('phq9', phq9Responses(0, 3));
    expect(r.safetyFlag).toBe(true);
  });

  it('safetyFlag true at any severity band (can occur with low scores)', () => {
    // Low overall score (score = 1 across items 0–7) but item 9 = 1
    const r = scoreInstrument('phq9', { ...phq9Responses(1, 0), 8: 1 });
    expect(r.safetyFlag).toBe(true);
    expect(r.severityLabel).toMatch(/minimal/i);
  });
});

// ---------------------------------------------------------------------------
// GAD-7 band boundaries (Spitzer 2006)
// ---------------------------------------------------------------------------

describe('GAD-7 severity band boundaries (Spitzer 2006)', () => {
  it('score 4 → Minimal (last minimal score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(4));
    expect(r.raw).toBe(4);
    expect(r.severityLabel).toMatch(/minimal/i);
  });

  it('score 5 → Mild (first mild score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(5));
    expect(r.raw).toBe(5);
    expect(r.severityLabel).toMatch(/mild/i);
  });

  it('score 9 → Mild (last mild score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(9));
    expect(r.raw).toBe(9);
    expect(r.severityLabel).toMatch(/mild/i);
  });

  it('score 10 → Moderate (first moderate score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(10));
    expect(r.raw).toBe(10);
    expect(r.severityLabel).toMatch(/moderate/i);
  });

  it('score 14 → Moderate (last moderate score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(14));
    expect(r.raw).toBe(14);
    expect(r.severityLabel).toMatch(/moderate/i);
    expect(r.severityLabel).not.toMatch(/severe/i);
  });

  it('score 15 → Severe (first severe score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(15));
    expect(r.raw).toBe(15);
    expect(r.severityLabel).toMatch(/severe/i);
  });

  it('score 21 → Severe (maximum score)', () => {
    const r = scoreInstrument('gad7', gad7Responses(21));
    expect(r.raw).toBe(21);
    expect(r.severityLabel).toMatch(/severe/i);
  });

  it('GAD-7 never sets safetyFlag (no suicidal ideation item)', () => {
    for (const score of [0, 5, 10, 15, 21]) {
      const r = scoreInstrument('gad7', gad7Responses(score));
      expect(r.safetyFlag).toBe(false);
    }
  });

  it('displayScoreString is ASCII-only at each boundary', () => {
    for (const score of [0, 4, 5, 9, 10, 14, 15, 21]) {
      const r = scoreInstrument('gad7', gad7Responses(score));
      expect(isAsciiOnly(r.displayScoreString)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// WHO-5 band boundaries (WHO 1998)
// ---------------------------------------------------------------------------

describe('WHO-5 well-being band boundaries (WHO 1998)', () => {
  it('raw 18 → display 72 → Good well-being (boundary)', () => {
    const r = scoreInstrument('who5', who5Responses(18));
    expect(r.raw).toBe(18);
    expect(r.displayScore).toBe(72);
    expect(r.severityLabel).toMatch(/good well-being/i);
  });

  it('raw 17 → display 68 → Moderate well-being (just below Good threshold)', () => {
    const r = scoreInstrument('who5', who5Responses(17));
    expect(r.raw).toBe(17);
    expect(r.displayScore).toBe(68);
    expect(r.severityLabel).toMatch(/moderate well-being/i);
  });

  it('raw 13 → display 52 → Moderate well-being (boundary)', () => {
    const r = scoreInstrument('who5', who5Responses(13));
    expect(r.raw).toBe(13);
    expect(r.displayScore).toBe(52);
    expect(r.severityLabel).toMatch(/moderate well-being/i);
  });

  it('raw 12 → display 48 → Low well-being (just below Moderate threshold)', () => {
    const r = scoreInstrument('who5', who5Responses(12));
    expect(r.raw).toBe(12);
    expect(r.displayScore).toBe(48);
    expect(r.severityLabel).toMatch(/low well-being/i);
  });

  it('raw 0 → display 0 → Low well-being (minimum)', () => {
    const r = scoreInstrument('who5', who5Responses(0));
    expect(r.raw).toBe(0);
    expect(r.displayScore).toBe(0);
    expect(r.severityLabel).toMatch(/low well-being/i);
  });

  it('raw 25 → display 100 → Good well-being (maximum)', () => {
    const r = scoreInstrument('who5', who5Responses(25));
    expect(r.raw).toBe(25);
    expect(r.displayScore).toBe(100);
    expect(r.severityLabel).toMatch(/good well-being/i);
  });

  it('WHO-5 never sets safetyFlag', () => {
    for (const raw of [0, 12, 13, 17, 18, 25]) {
      const r = scoreInstrument('who5', who5Responses(raw));
      expect(r.safetyFlag).toBe(false);
    }
  });

  it('displayScoreString is ASCII-only at each boundary', () => {
    for (const raw of [0, 12, 13, 17, 18, 25]) {
      const r = scoreInstrument('who5', who5Responses(raw));
      expect(isAsciiOnly(r.displayScoreString)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// Compassion message content — CLAUDE.md Rule #4 (compassion-first framing)
// ---------------------------------------------------------------------------

describe('scoreInstrument — compassion-first message framing (CLAUDE.md Rule #4)', () => {
  it('PHQ-9 compassion message never says "you failed" or "streak reset"', () => {
    for (const score of [0, 5, 10, 15, 20]) {
      const r = scoreInstrument('phq9', phq9Responses(score));
      expect(r.compassionMessage.toLowerCase()).not.toContain('you failed');
      expect(r.compassionMessage.toLowerCase()).not.toContain('streak reset');
    }
  });

  it('GAD-7 compassion message never contains stigmatising framing', () => {
    for (const score of [0, 5, 10, 15]) {
      const r = scoreInstrument('gad7', gad7Responses(score));
      expect(r.compassionMessage.toLowerCase()).not.toContain('you failed');
      expect(r.compassionMessage).not.toMatch(/weak|loser|failure/i);
    }
  });

  it('PHQ-9 severe message suggests reaching out (not shame)', () => {
    const r = scoreInstrument('phq9', phq9Responses(20));
    expect(r.compassionMessage.toLowerCase()).toMatch(/reach out|mental health|professional|crisis/);
  });

  it('WHO-5 low message acknowledges difficulty compassionately', () => {
    const r = scoreInstrument('who5', who5Responses(0));
    expect(r.compassionMessage.toLowerCase()).toMatch(/difficult|support|someone/);
  });
});
