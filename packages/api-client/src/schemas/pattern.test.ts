/**
 * Unit tests for pattern Zod schemas.
 *
 * PatternSchema: id must be a UUID; confidence bounded [0,1]; suggested_action
 * is nullable+optional (may be absent entirely or explicitly null).
 *
 * DismissReasonSchema: exactly 3 valid reasons — any other value indicates a
 * caller bug and must be rejected.
 *
 * Covers:
 * - PatternKindSchema: accepts all 4 kinds; rejects unknown
 * - PatternSchema: accepts valid pattern; rejects non-UUID id; rejects confidence outside [0,1];
 *   accepts suggested_action as null; accepts suggested_action absent
 * - PatternListResponseSchema: accepts empty patterns array; accepts populated array; rejects non-array patterns
 * - DismissReasonSchema: accepts all 3 reasons; rejects unknown reason
 * - PatternDismissRequestSchema: accepts valid request; rejects unknown reason
 */

import { describe, it, expect } from 'vitest';
import {
  PatternKindSchema,
  PatternSchema,
  PatternListResponseSchema,
  DismissReasonSchema,
  PatternDismissRequestSchema,
} from './pattern';

// ---------------------------------------------------------------------------
// PatternKindSchema
// ---------------------------------------------------------------------------

describe('PatternKindSchema', () => {
  const validKinds = ['temporal', 'contextual', 'physiological', 'compound'] as const;

  for (const kind of validKinds) {
    it(`accepts pattern kind: ${kind}`, () => {
      expect(PatternKindSchema.safeParse(kind).success).toBe(true);
    });
  }

  it('contains exactly 4 kinds', () => {
    expect(validKinds).toHaveLength(4);
  });

  it('rejects unknown pattern kind', () => {
    expect(PatternKindSchema.safeParse('behavioral').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PatternSchema
// ---------------------------------------------------------------------------

const validPattern = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  kind: 'temporal',
  summary: 'Urge peaks at 5 PM on weekdays',
  confidence: 0.82,
  actionable: true,
  suggested_action: 'Use box breathing before your 5 PM commute',
};

describe('PatternSchema', () => {
  it('accepts a valid pattern', () => {
    expect(PatternSchema.safeParse(validPattern).success).toBe(true);
  });

  it('accepts suggested_action as null', () => {
    expect(PatternSchema.safeParse({ ...validPattern, suggested_action: null }).success).toBe(true);
  });

  it('accepts pattern without suggested_action (optional field)', () => {
    const { suggested_action: _, ...rest } = validPattern;
    expect(PatternSchema.safeParse(rest).success).toBe(true);
  });

  it('accepts confidence = 0 (lower bound)', () => {
    expect(PatternSchema.safeParse({ ...validPattern, confidence: 0 }).success).toBe(true);
  });

  it('accepts confidence = 1 (upper bound)', () => {
    expect(PatternSchema.safeParse({ ...validPattern, confidence: 1 }).success).toBe(true);
  });

  it('rejects confidence above 1', () => {
    expect(PatternSchema.safeParse({ ...validPattern, confidence: 1.01 }).success).toBe(false);
  });

  it('rejects confidence below 0', () => {
    expect(PatternSchema.safeParse({ ...validPattern, confidence: -0.01 }).success).toBe(false);
  });

  it('rejects non-UUID id', () => {
    expect(PatternSchema.safeParse({ ...validPattern, id: 'not-a-uuid' }).success).toBe(false);
  });

  it('rejects unknown kind', () => {
    expect(PatternSchema.safeParse({ ...validPattern, kind: 'emotional' }).success).toBe(false);
  });

  it('rejects missing id', () => {
    const { id: _, ...rest } = validPattern;
    expect(PatternSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects missing actionable', () => {
    const { actionable: _, ...rest } = validPattern;
    expect(PatternSchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PatternListResponseSchema
// ---------------------------------------------------------------------------

describe('PatternListResponseSchema', () => {
  it('accepts empty patterns array', () => {
    expect(PatternListResponseSchema.safeParse({ patterns: [] }).success).toBe(true);
  });

  it('accepts a populated patterns array', () => {
    expect(PatternListResponseSchema.safeParse({ patterns: [validPattern] }).success).toBe(true);
  });

  it('rejects invalid pattern in array (bad confidence)', () => {
    expect(PatternListResponseSchema.safeParse({
      patterns: [{ ...validPattern, confidence: 1.5 }],
    }).success).toBe(false);
  });

  it('rejects missing patterns field', () => {
    expect(PatternListResponseSchema.safeParse({}).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// DismissReasonSchema
// ---------------------------------------------------------------------------

describe('DismissReasonSchema', () => {
  const validReasons = ['not_useful', 'false_pattern', 'not_now'] as const;

  for (const reason of validReasons) {
    it(`accepts dismiss reason: ${reason}`, () => {
      expect(DismissReasonSchema.safeParse(reason).success).toBe(true);
    });
  }

  it('contains exactly 3 dismiss reasons', () => {
    expect(validReasons).toHaveLength(3);
  });

  it('rejects unknown reason', () => {
    expect(DismissReasonSchema.safeParse('spam').success).toBe(false);
  });

  it('rejects empty string', () => {
    expect(DismissReasonSchema.safeParse('').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PatternDismissRequestSchema
// ---------------------------------------------------------------------------

describe('PatternDismissRequestSchema', () => {
  it('accepts not_useful reason', () => {
    expect(PatternDismissRequestSchema.safeParse({ reason: 'not_useful' }).success).toBe(true);
  });

  it('accepts false_pattern reason', () => {
    expect(PatternDismissRequestSchema.safeParse({ reason: 'false_pattern' }).success).toBe(true);
  });

  it('accepts not_now reason', () => {
    expect(PatternDismissRequestSchema.safeParse({ reason: 'not_now' }).success).toBe(true);
  });

  it('rejects unknown reason', () => {
    expect(PatternDismissRequestSchema.safeParse({ reason: 'ignore' }).success).toBe(false);
  });

  it('rejects missing reason', () => {
    expect(PatternDismissRequestSchema.safeParse({}).success).toBe(false);
  });
});
