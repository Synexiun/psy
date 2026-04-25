/**
 * Unit tests for relapse Zod schemas.
 *
 * CLAUDE.md non-negotiable #3: resilience_streak_days in the response must always
 * be present and nonnegative so the UI can display the compassion-first affirmation
 * that resilience was preserved after a relapse (rule #3/#4).
 *
 * RelapseReportRequestSchema: severity is 1–10 (must not accept 0 or 11);
 * context_tags max 16 entries.
 *
 * Covers:
 * - RelapseReportRequestSchema: valid payload; severity bounds (1–10); context_tags max 16;
 *   required fields; datetime format
 * - RelapseNextStepSchema: accepts all 3 values; rejects unknown
 * - RelapseReportResponseSchema: includes resilience_streak_days (rule #3); rejects negative;
 *   accepts empty next_steps; rejects unknown next_step; rejects non-UUID relapse_id
 * - RelapseReviewRequestSchema: all fields optional; rejects ave_score out of range;
 *   rejects context_tags_refined over 16 items
 */

import { describe, it, expect } from 'vitest';
import {
  RelapseReportRequestSchema,
  RelapseNextStepSchema,
  RelapseReportResponseSchema,
  RelapseReviewRequestSchema,
} from './relapse';

// ---------------------------------------------------------------------------
// RelapseReportRequestSchema
// ---------------------------------------------------------------------------

const validRequest = {
  occurred_at: '2026-04-23T08:00:00Z',
  behavior: 'Used substance',
  severity: 5,
  context_tags: ['stress', 'isolation'],
};

describe('RelapseReportRequestSchema', () => {
  it('accepts valid relapse report request', () => {
    expect(RelapseReportRequestSchema.safeParse(validRequest).success).toBe(true);
  });

  it('accepts empty context_tags array', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, context_tags: [] }).success).toBe(true);
  });

  it('accepts severity = 1 (lower bound)', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, severity: 1 }).success).toBe(true);
  });

  it('accepts severity = 10 (upper bound)', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, severity: 10 }).success).toBe(true);
  });

  it('rejects severity = 0 (below lower bound)', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, severity: 0 }).success).toBe(false);
  });

  it('rejects severity = 11 (above upper bound)', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, severity: 11 }).success).toBe(false);
  });

  it('rejects non-integer severity', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, severity: 5.5 }).success).toBe(false);
  });

  it('accepts exactly 16 context_tags (max boundary)', () => {
    const tags = Array.from({ length: 16 }, (_, i) => `tag_${i}`);
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, context_tags: tags }).success).toBe(true);
  });

  it('rejects 17 context_tags (exceeds max of 16)', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `tag_${i}`);
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, context_tags: tags }).success).toBe(false);
  });

  it('rejects non-datetime occurred_at', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...validRequest, occurred_at: '2026-04-23' }).success).toBe(false);
  });

  it('rejects missing behavior', () => {
    const { behavior: _, ...rest } = validRequest;
    expect(RelapseReportRequestSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects missing occurred_at', () => {
    const { occurred_at: _, ...rest } = validRequest;
    expect(RelapseReportRequestSchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// RelapseNextStepSchema
// ---------------------------------------------------------------------------

describe('RelapseNextStepSchema', () => {
  const validSteps = ['compassion_message', 'review_prompt', 'streak_update_summary'] as const;

  for (const step of validSteps) {
    it(`accepts next step: ${step}`, () => {
      expect(RelapseNextStepSchema.safeParse(step).success).toBe(true);
    });
  }

  it('contains exactly 3 next step values', () => {
    expect(validSteps).toHaveLength(3);
  });

  it('rejects unknown next step', () => {
    expect(RelapseNextStepSchema.safeParse('dismiss').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// RelapseReportResponseSchema — resilience_streak_days (CLAUDE.md rule #3)
// ---------------------------------------------------------------------------

const validResponse = {
  relapse_id: '550e8400-e29b-41d4-a716-446655440000',
  next_steps: ['compassion_message'],
  resilience_streak_days: 47,
  resilience_urges_handled_total: 89,
};

describe('RelapseReportResponseSchema', () => {
  it('accepts valid relapse response', () => {
    expect(RelapseReportResponseSchema.safeParse(validResponse).success).toBe(true);
  });

  it('includes resilience_streak_days (non-negotiable rule #3 — resilience preserved after relapse)', () => {
    const result = RelapseReportResponseSchema.safeParse(validResponse);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.resilience_streak_days).toBe(47);
    }
  });

  it('accepts resilience_streak_days = 0 (nonnegative)', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...validResponse, resilience_streak_days: 0 }).success).toBe(true);
  });

  it('rejects negative resilience_streak_days (rule #3)', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...validResponse, resilience_streak_days: -1 }).success).toBe(false);
  });

  it('accepts empty next_steps array', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...validResponse, next_steps: [] }).success).toBe(true);
  });

  it('accepts multiple next_steps', () => {
    expect(RelapseReportResponseSchema.safeParse({
      ...validResponse,
      next_steps: ['compassion_message', 'review_prompt'],
    }).success).toBe(true);
  });

  it('rejects unknown next_step in array', () => {
    expect(RelapseReportResponseSchema.safeParse({
      ...validResponse,
      next_steps: ['you_failed'],
    }).success).toBe(false);
  });

  it('rejects non-UUID relapse_id', () => {
    expect(RelapseReportResponseSchema.safeParse({
      ...validResponse,
      relapse_id: 'not-a-uuid',
    }).success).toBe(false);
  });

  it('rejects missing resilience_streak_days', () => {
    const { resilience_streak_days: _, ...rest } = validResponse;
    expect(RelapseReportResponseSchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// RelapseReviewRequestSchema
// ---------------------------------------------------------------------------

describe('RelapseReviewRequestSchema', () => {
  it('accepts empty object (all fields optional)', () => {
    expect(RelapseReviewRequestSchema.safeParse({}).success).toBe(true);
  });

  it('accepts valid journal_id as UUID', () => {
    expect(RelapseReviewRequestSchema.safeParse({
      journal_id: '550e8400-e29b-41d4-a716-446655440001',
    }).success).toBe(true);
  });

  it('rejects journal_id that is not a UUID', () => {
    expect(RelapseReviewRequestSchema.safeParse({ journal_id: 'not-a-uuid' }).success).toBe(false);
  });

  it('accepts ave_score = 0 (lower bound)', () => {
    expect(RelapseReviewRequestSchema.safeParse({ ave_score: 0 }).success).toBe(true);
  });

  it('accepts ave_score = 10 (upper bound)', () => {
    expect(RelapseReviewRequestSchema.safeParse({ ave_score: 10 }).success).toBe(true);
  });

  it('rejects ave_score = 11 (above upper bound)', () => {
    expect(RelapseReviewRequestSchema.safeParse({ ave_score: 11 }).success).toBe(false);
  });

  it('rejects ave_score = -1 (below lower bound)', () => {
    expect(RelapseReviewRequestSchema.safeParse({ ave_score: -1 }).success).toBe(false);
  });

  it('accepts exactly 16 context_tags_refined (max boundary)', () => {
    const tags = Array.from({ length: 16 }, (_, i) => `tag_${i}`);
    expect(RelapseReviewRequestSchema.safeParse({ context_tags_refined: tags }).success).toBe(true);
  });

  it('rejects 17 context_tags_refined (exceeds max of 16)', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `tag_${i}`);
    expect(RelapseReviewRequestSchema.safeParse({ context_tags_refined: tags }).success).toBe(false);
  });
});
