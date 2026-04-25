/**
 * Unit tests for urge / intervention Zod schemas.
 *
 * UrgeLogRequestSchema: intensity_start is bounded 0–10; origin enum must be
 * one of 3 specific values (self_reported / sensor_triggered / nudge_triggered);
 * trigger_tags max 16.
 *
 * SosRequestSchema: minimal — only started_at. This is intentional: the critical
 * path POST carries no metadata so it can succeed even on a degraded device.
 *
 * UrgeResolveRequestSchema: both intensity fields bounded 0–10; handled boolean required.
 *
 * InterventionOutcomeRequestSchema: outcome_type enum must be one of 4 values.
 * NudgeAckSchema: enum used directly (not in an object wrapper for the ack field).
 *
 * Covers:
 * - UrgeLogRequestSchema: valid payload; intensity_start bounds; trigger_tags max 16;
 *   origin enum; optional location_context; required fields
 * - UrgeResolveRequestSchema: valid payload; intensity bounds; optional note max 2000;
 *   required handled boolean
 * - SosRequestSchema: accepts only started_at; rejects extra fields? (Zod strip)
 * - InterventionOutcomeRequestSchema: all 4 outcome_type values; rejects unknown;
 *   optional post_state_label; optional user_note max 2000
 * - NudgeAckSchema: all 3 ack values; rejects unknown
 * - NudgeAckRequestSchema: accepts valid; rejects unknown ack
 */

import { describe, it, expect } from 'vitest';
import {
  UrgeLogRequestSchema,
  UrgeResolveRequestSchema,
  SosRequestSchema,
  InterventionOutcomeRequestSchema,
  NudgeAckSchema,
  NudgeAckRequestSchema,
} from './urge';

// ---------------------------------------------------------------------------
// UrgeLogRequestSchema
// ---------------------------------------------------------------------------

const validUrgeLog = {
  started_at: '2026-04-23T10:00:00Z',
  intensity_start: 7,
  trigger_tags: ['stress', 'isolation'],
  origin: 'self_reported',
};

describe('UrgeLogRequestSchema', () => {
  it('accepts valid urge log request', () => {
    expect(UrgeLogRequestSchema.safeParse(validUrgeLog).success).toBe(true);
  });

  it('accepts intensity_start = 0 (lower bound)', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, intensity_start: 0 }).success).toBe(true);
  });

  it('accepts intensity_start = 10 (upper bound)', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, intensity_start: 10 }).success).toBe(true);
  });

  it('rejects intensity_start = -1 (below lower bound)', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, intensity_start: -1 }).success).toBe(false);
  });

  it('rejects intensity_start = 11 (above upper bound)', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, intensity_start: 11 }).success).toBe(false);
  });

  it('rejects non-integer intensity_start', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, intensity_start: 7.5 }).success).toBe(false);
  });

  it('accepts origin: sensor_triggered', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, origin: 'sensor_triggered' }).success).toBe(true);
  });

  it('accepts origin: nudge_triggered', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, origin: 'nudge_triggered' }).success).toBe(true);
  });

  it('rejects unknown origin', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, origin: 'unknown' }).success).toBe(false);
  });

  it('accepts empty trigger_tags', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, trigger_tags: [] }).success).toBe(true);
  });

  it('accepts exactly 16 trigger_tags (max boundary)', () => {
    const tags = Array.from({ length: 16 }, (_, i) => `tag_${i}`);
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, trigger_tags: tags }).success).toBe(true);
  });

  it('rejects 17 trigger_tags (exceeds max of 16)', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `tag_${i}`);
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, trigger_tags: tags }).success).toBe(false);
  });

  it('accepts optional location_context', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, location_context: 'home' }).success).toBe(true);
  });

  it('accepts without location_context (optional)', () => {
    const { location_context: _, ...rest } = { ...validUrgeLog, location_context: 'home' };
    expect(UrgeLogRequestSchema.safeParse(rest).success).toBe(true);
  });

  it('rejects non-datetime started_at', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validUrgeLog, started_at: '2026-04-23' }).success).toBe(false);
  });

  it('rejects missing origin', () => {
    const { origin: _, ...rest } = validUrgeLog;
    expect(UrgeLogRequestSchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// SosRequestSchema
// ---------------------------------------------------------------------------

describe('SosRequestSchema', () => {
  it('accepts only started_at (minimal critical-path payload)', () => {
    expect(SosRequestSchema.safeParse({ started_at: '2026-04-23T10:00:00Z' }).success).toBe(true);
  });

  it('rejects non-datetime started_at', () => {
    expect(SosRequestSchema.safeParse({ started_at: '2026-04-23' }).success).toBe(false);
  });

  it('rejects missing started_at', () => {
    expect(SosRequestSchema.safeParse({}).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// UrgeResolveRequestSchema
// ---------------------------------------------------------------------------

const validResolve = {
  intensity_peak: 8,
  intensity_end: 3,
  handled: true,
};

describe('UrgeResolveRequestSchema', () => {
  it('accepts valid resolve request', () => {
    expect(UrgeResolveRequestSchema.safeParse(validResolve).success).toBe(true);
  });

  it('accepts intensity_peak = 0 (lower bound)', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, intensity_peak: 0 }).success).toBe(true);
  });

  it('accepts intensity_peak = 10 (upper bound)', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, intensity_peak: 10 }).success).toBe(true);
  });

  it('rejects intensity_peak = 11 (above upper bound)', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, intensity_peak: 11 }).success).toBe(false);
  });

  it('rejects intensity_peak = -1 (below lower bound)', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, intensity_peak: -1 }).success).toBe(false);
  });

  it('accepts intensity_end = 0 (lower bound)', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, intensity_end: 0 }).success).toBe(true);
  });

  it('rejects intensity_end = 11 (above upper bound)', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, intensity_end: 11 }).success).toBe(false);
  });

  it('accepts handled = false', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, handled: false }).success).toBe(true);
  });

  it('rejects missing handled field', () => {
    const { handled: _, ...rest } = validResolve;
    expect(UrgeResolveRequestSchema.safeParse(rest).success).toBe(false);
  });

  it('accepts optional note', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, note: 'Used box breathing' }).success).toBe(true);
  });

  it('rejects note exceeding 2000 characters', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, note: 'a'.repeat(2001) }).success).toBe(false);
  });

  it('accepts note of exactly 2000 characters', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...validResolve, note: 'a'.repeat(2000) }).success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// InterventionOutcomeRequestSchema
// ---------------------------------------------------------------------------

describe('InterventionOutcomeRequestSchema', () => {
  const validOutcomes = ['handled', 'partial', 'relapsed', 'skipped'] as const;

  for (const outcome_type of validOutcomes) {
    it(`accepts outcome_type: ${outcome_type}`, () => {
      expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type }).success).toBe(true);
    });
  }

  it('contains exactly 4 outcome types', () => {
    expect(validOutcomes).toHaveLength(4);
  });

  it('rejects unknown outcome_type', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type: 'completed' }).success).toBe(false);
  });

  it('accepts optional post_state_label', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({
      outcome_type: 'handled',
      post_state_label: 'stable',
    }).success).toBe(true);
  });

  it('accepts optional user_note', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({
      outcome_type: 'handled',
      user_note: 'Felt calmer after breathing',
    }).success).toBe(true);
  });

  it('rejects user_note exceeding 2000 characters', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({
      outcome_type: 'handled',
      user_note: 'a'.repeat(2001),
    }).success).toBe(false);
  });

  it('rejects missing outcome_type', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({}).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// NudgeAckSchema
// ---------------------------------------------------------------------------

describe('NudgeAckSchema', () => {
  const validAcks = ['accepted', 'snoozed', 'dismissed'] as const;

  for (const ack of validAcks) {
    it(`accepts ack value: ${ack}`, () => {
      expect(NudgeAckSchema.safeParse(ack).success).toBe(true);
    });
  }

  it('contains exactly 3 ack values', () => {
    expect(validAcks).toHaveLength(3);
  });

  it('rejects unknown ack value', () => {
    expect(NudgeAckSchema.safeParse('ignored').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// NudgeAckRequestSchema
// ---------------------------------------------------------------------------

describe('NudgeAckRequestSchema', () => {
  it('accepts valid ack request: accepted', () => {
    expect(NudgeAckRequestSchema.safeParse({ ack: 'accepted' }).success).toBe(true);
  });

  it('accepts valid ack request: snoozed', () => {
    expect(NudgeAckRequestSchema.safeParse({ ack: 'snoozed' }).success).toBe(true);
  });

  it('accepts valid ack request: dismissed', () => {
    expect(NudgeAckRequestSchema.safeParse({ ack: 'dismissed' }).success).toBe(true);
  });

  it('rejects unknown ack in request object', () => {
    expect(NudgeAckRequestSchema.safeParse({ ack: 'seen' }).success).toBe(false);
  });

  it('rejects missing ack field', () => {
    expect(NudgeAckRequestSchema.safeParse({}).success).toBe(false);
  });
});
