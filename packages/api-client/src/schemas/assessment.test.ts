/**
 * Unit tests for assessment Zod schemas.
 *
 * Safety note: AssessmentSubmitResponseSchema.safety_actions includes
 * 'escalate_t4' — the T4 crisis escalation action. These tests verify the
 * schema correctly accepts/rejects the full safety action enum and that
 * total_score/rci values are properly constrained.
 */

import { describe, it, expect } from 'vitest';
import {
  AssessmentKindSchema,
  AssessmentResponseItemSchema,
  AssessmentSubmitRequestSchema,
  SeverityBandSchema,
  SafetyActionSchema,
  AssessmentSubmitResponseSchema,
  DueAssessmentSchema,
  DueAssessmentsResponseSchema,
} from './assessment';

// ---------------------------------------------------------------------------
// AssessmentKindSchema (re-exported from parent schemas.ts)
// ---------------------------------------------------------------------------

describe('AssessmentKindSchema', () => {
  it('accepts phq9', () => {
    expect(AssessmentKindSchema.safeParse('phq9').success).toBe(true);
  });

  it('accepts gad7', () => {
    expect(AssessmentKindSchema.safeParse('gad7').success).toBe(true);
  });

  it('accepts audit_c (underscore form in API schema)', () => {
    expect(AssessmentKindSchema.safeParse('audit_c').success).toBe(true);
  });

  it('accepts audit (full instrument)', () => {
    expect(AssessmentKindSchema.safeParse('audit').success).toBe(true);
  });

  it('accepts who5', () => {
    expect(AssessmentKindSchema.safeParse('who5').success).toBe(true);
  });

  it('accepts pss10', () => {
    expect(AssessmentKindSchema.safeParse('pss10').success).toBe(true);
  });

  it('rejects unknown instrument', () => {
    expect(AssessmentKindSchema.safeParse('unknown').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AssessmentResponseItemSchema
// ---------------------------------------------------------------------------

describe('AssessmentResponseItemSchema', () => {
  it('accepts valid item+value pair', () => {
    expect(AssessmentResponseItemSchema.safeParse({ item: 1, value: 0 }).success).toBe(true);
  });

  it('accepts value 0 (nonnegative lower bound)', () => {
    expect(AssessmentResponseItemSchema.safeParse({ item: 1, value: 0 }).success).toBe(true);
  });

  it('rejects negative value', () => {
    expect(AssessmentResponseItemSchema.safeParse({ item: 1, value: -1 }).success).toBe(false);
  });

  it('rejects item 0 (must be positive)', () => {
    expect(AssessmentResponseItemSchema.safeParse({ item: 0, value: 1 }).success).toBe(false);
  });

  it('rejects non-integer value', () => {
    expect(AssessmentResponseItemSchema.safeParse({ item: 1, value: 1.5 }).success).toBe(false);
  });

  it('rejects missing value field', () => {
    expect(AssessmentResponseItemSchema.safeParse({ item: 1 }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AssessmentSubmitRequestSchema
// ---------------------------------------------------------------------------

const validSubmitRequest = {
  instrument_id: 'phq9',
  version: 'phq9_v1',
  responses: [
    { item: 1, value: 2 },
    { item: 2, value: 1 },
  ],
};

describe('AssessmentSubmitRequestSchema', () => {
  it('accepts valid submit request', () => {
    expect(AssessmentSubmitRequestSchema.safeParse(validSubmitRequest).success).toBe(true);
  });

  it('accepts empty responses array', () => {
    expect(AssessmentSubmitRequestSchema.safeParse({ ...validSubmitRequest, responses: [] }).success).toBe(true);
  });

  it('rejects unknown instrument_id', () => {
    expect(AssessmentSubmitRequestSchema.safeParse({ ...validSubmitRequest, instrument_id: 'invalid' }).success).toBe(false);
  });

  it('rejects missing version', () => {
    const { version: _, ...rest } = validSubmitRequest;
    expect(AssessmentSubmitRequestSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects invalid response item (negative value)', () => {
    expect(AssessmentSubmitRequestSchema.safeParse({
      ...validSubmitRequest,
      responses: [{ item: 1, value: -1 }],
    }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// SeverityBandSchema
// ---------------------------------------------------------------------------

describe('SeverityBandSchema', () => {
  const bands = ['none', 'minimal', 'mild', 'moderate', 'moderately_severe', 'severe'] as const;

  for (const band of bands) {
    it(`accepts severity band: ${band}`, () => {
      expect(SeverityBandSchema.safeParse(band).success).toBe(true);
    });
  }

  it('contains exactly 6 bands', () => {
    expect(bands).toHaveLength(6);
  });

  it('rejects unknown severity band', () => {
    expect(SeverityBandSchema.safeParse('extreme').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// SafetyActionSchema — safety-critical: escalate_t4 must be accepted
// ---------------------------------------------------------------------------

describe('SafetyActionSchema', () => {
  it('accepts escalate_t4 (T4 crisis escalation — CLAUDE.md non-negotiable #1)', () => {
    expect(SafetyActionSchema.safeParse('escalate_t4').success).toBe(true);
  });

  it('accepts notify_clinician', () => {
    expect(SafetyActionSchema.safeParse('notify_clinician').success).toBe(true);
  });

  it('accepts show_crisis_resources', () => {
    expect(SafetyActionSchema.safeParse('show_crisis_resources').success).toBe(true);
  });

  it('accepts schedule_followup', () => {
    expect(SafetyActionSchema.safeParse('schedule_followup').success).toBe(true);
  });

  it('rejects unknown safety action', () => {
    expect(SafetyActionSchema.safeParse('dismiss').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AssessmentSubmitResponseSchema
// ---------------------------------------------------------------------------

const validSubmitResponse = {
  assessment_id: '123e4567-e89b-12d3-a456-426614174000',
  total_score: 14,
  severity_band: 'moderate',
  safety_actions: ['show_crisis_resources'],
  completed_at: '2026-04-25T10:00:00Z',
};

describe('AssessmentSubmitResponseSchema', () => {
  it('accepts minimal valid response', () => {
    expect(AssessmentSubmitResponseSchema.safeParse(validSubmitResponse).success).toBe(true);
  });

  it('accepts escalate_t4 in safety_actions array', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      safety_actions: ['escalate_t4'],
    }).success).toBe(true);
  });

  it('accepts multiple safety actions including escalate_t4', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      safety_actions: ['escalate_t4', 'notify_clinician'],
    }).success).toBe(true);
  });

  it('accepts empty safety_actions array', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      safety_actions: [],
    }).success).toBe(true);
  });

  it('accepts optional subscale_scores', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      subscale_scores: { somatic: 5, cognitive: 9 },
    }).success).toBe(true);
  });

  it('accepts optional rci_vs_baseline as null', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      rci_vs_baseline: null,
    }).success).toBe(true);
  });

  it('accepts optional rci_vs_previous as a number', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      rci_vs_previous: -1.96,
    }).success).toBe(true);
  });

  it('accepts optional clinically_significant_change as boolean', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      clinically_significant_change: true,
    }).success).toBe(true);
  });

  it('rejects negative total_score', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      total_score: -1,
    }).success).toBe(false);
  });

  it('rejects invalid uuid for assessment_id', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      assessment_id: 'not-a-uuid',
    }).success).toBe(false);
  });

  it('rejects unknown severity_band', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      severity_band: 'catastrophic',
    }).success).toBe(false);
  });

  it('rejects unknown safety action in array', () => {
    expect(AssessmentSubmitResponseSchema.safeParse({
      ...validSubmitResponse,
      safety_actions: ['dismiss'],
    }).success).toBe(false);
  });

  it('rejects missing assessment_id', () => {
    const { assessment_id: _, ...rest } = validSubmitResponse;
    expect(AssessmentSubmitResponseSchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// DueAssessmentSchema
// ---------------------------------------------------------------------------

const validDue = {
  instrument_id: 'gad7',
  version: 'gad7_v1',
  due_reason: 'scheduled',
  due_at: '2026-04-26T09:00:00Z',
};

describe('DueAssessmentSchema', () => {
  it('accepts valid due assessment', () => {
    expect(DueAssessmentSchema.safeParse(validDue).success).toBe(true);
  });

  it('accepts due_reason: clinician_requested', () => {
    expect(DueAssessmentSchema.safeParse({ ...validDue, due_reason: 'clinician_requested' }).success).toBe(true);
  });

  it('accepts due_reason: triggered_by_state', () => {
    expect(DueAssessmentSchema.safeParse({ ...validDue, due_reason: 'triggered_by_state' }).success).toBe(true);
  });

  it('rejects unknown due_reason', () => {
    expect(DueAssessmentSchema.safeParse({ ...validDue, due_reason: 'manual' }).success).toBe(false);
  });

  it('rejects missing version', () => {
    const { version: _, ...rest } = validDue;
    expect(DueAssessmentSchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// DueAssessmentsResponseSchema
// ---------------------------------------------------------------------------

describe('DueAssessmentsResponseSchema', () => {
  it('accepts empty due list', () => {
    expect(DueAssessmentsResponseSchema.safeParse({ due: [] }).success).toBe(true);
  });

  it('accepts multiple due assessments', () => {
    expect(DueAssessmentsResponseSchema.safeParse({
      due: [
        { instrument_id: 'phq9', version: 'phq9_v1', due_reason: 'scheduled', due_at: '2026-04-26T09:00:00Z' },
        { instrument_id: 'gad7', version: 'gad7_v1', due_reason: 'scheduled', due_at: '2026-04-26T09:00:00Z' },
      ],
    }).success).toBe(true);
  });

  it('rejects missing due field', () => {
    expect(DueAssessmentsResponseSchema.safeParse({}).success).toBe(false);
  });

  it('rejects invalid item in due array', () => {
    expect(DueAssessmentsResponseSchema.safeParse({
      due: [{ instrument_id: 'unknown', version: 'v1', due_reason: 'scheduled', due_at: '2026-04-26T09:00:00Z' }],
    }).success).toBe(false);
  });
});
