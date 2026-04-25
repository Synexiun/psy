/**
 * Zod schema contract tests for api-client sub-schemas.
 *
 * These tests verify that each schema accepts valid payloads and rejects
 * invalid ones. Schema tests are fast, dependency-free, and catch API
 * contract drift before integration.
 *
 * Clinical notes:
 *  - RelapseReportResponseSchema: resilience_streak_days and
 *    resilience_urges_handled_total are nonnegative — negative values
 *    would violate CLAUDE.md Rule #3 (resilience never decrements).
 *  - StateLabelSchema must contain every T0–T4 tier label so crisis
 *    routing logic can rely on exhaustive enum validation.
 */

import { describe, it, expect } from 'vitest';
import {
  PatternKindSchema,
  PatternSchema,
  PatternListResponseSchema,
  DismissReasonSchema,
  PatternDismissRequestSchema,
} from './pattern';
import {
  RelapseReportRequestSchema,
  RelapseReportResponseSchema,
  RelapseNextStepSchema,
  RelapseReviewRequestSchema,
} from './relapse';
import {
  StateLabelSchema,
  RiskWindowSchema,
  TodaySummarySchema,
  StateEstimateUploadSchema,
} from './state';
import {
  UrgeLogRequestSchema,
  UrgeLogResponseSchema,
  SosRequestSchema,
  SosResponseSchema,
  UrgeResolveRequestSchema,
  InterventionOutcomeRequestSchema,
  NudgeAckSchema,
  NudgeAckRequestSchema,
} from './urge';
import { StreakStateSchema } from './streak';

// ---------------------------------------------------------------------------
// Pattern schemas
// ---------------------------------------------------------------------------

describe('PatternKindSchema', () => {
  it('accepts temporal', () => {
    expect(PatternKindSchema.safeParse('temporal').success).toBe(true);
  });

  it('accepts contextual', () => {
    expect(PatternKindSchema.safeParse('contextual').success).toBe(true);
  });

  it('accepts physiological', () => {
    expect(PatternKindSchema.safeParse('physiological').success).toBe(true);
  });

  it('accepts compound', () => {
    expect(PatternKindSchema.safeParse('compound').success).toBe(true);
  });

  it('rejects unknown kind', () => {
    expect(PatternKindSchema.safeParse('behavioral').success).toBe(false);
  });
});

describe('PatternSchema', () => {
  const valid = {
    id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    kind: 'temporal',
    summary: 'Urge intensity peaks at 5–7 PM on weekdays.',
    confidence: 0.82,
    actionable: true,
    suggested_action: 'Log urge before 5 PM',
  };

  it('accepts a valid pattern', () => {
    expect(PatternSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts null suggested_action', () => {
    expect(PatternSchema.safeParse({ ...valid, suggested_action: null }).success).toBe(true);
  });

  it('accepts omitted suggested_action (optional)', () => {
    const { suggested_action: _, ...withoutSuggested } = valid;
    expect(PatternSchema.safeParse(withoutSuggested).success).toBe(true);
  });

  it('rejects invalid uuid', () => {
    expect(PatternSchema.safeParse({ ...valid, id: 'not-uuid' }).success).toBe(false);
  });

  it('rejects confidence > 1', () => {
    expect(PatternSchema.safeParse({ ...valid, confidence: 1.01 }).success).toBe(false);
  });

  it('rejects confidence < 0', () => {
    expect(PatternSchema.safeParse({ ...valid, confidence: -0.1 }).success).toBe(false);
  });
});

describe('PatternListResponseSchema', () => {
  it('accepts empty patterns list', () => {
    expect(PatternListResponseSchema.safeParse({ patterns: [] }).success).toBe(true);
  });

  it('accepts list with one pattern', () => {
    expect(PatternListResponseSchema.safeParse({
      patterns: [{
        id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
        kind: 'contextual',
        summary: 'Work stress co-occurs with urges.',
        confidence: 0.74,
        actionable: false,
      }],
    }).success).toBe(true);
  });
});

describe('DismissReasonSchema', () => {
  it('accepts not_useful', () => {
    expect(DismissReasonSchema.safeParse('not_useful').success).toBe(true);
  });

  it('accepts false_pattern', () => {
    expect(DismissReasonSchema.safeParse('false_pattern').success).toBe(true);
  });

  it('accepts not_now', () => {
    expect(DismissReasonSchema.safeParse('not_now').success).toBe(true);
  });

  it('rejects unknown reason', () => {
    expect(DismissReasonSchema.safeParse('irrelevant').success).toBe(false);
  });
});

describe('PatternDismissRequestSchema', () => {
  it('accepts valid dismiss reason', () => {
    expect(PatternDismissRequestSchema.safeParse({ reason: 'not_useful' }).success).toBe(true);
  });

  it('rejects missing reason', () => {
    expect(PatternDismissRequestSchema.safeParse({}).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Relapse schemas
// ---------------------------------------------------------------------------

describe('RelapseReportRequestSchema', () => {
  const valid = {
    occurred_at: '2026-04-25T18:30:00Z',
    behavior: 'gaming',
    severity: 5,
    context_tags: ['stress', 'fatigue'],
  };

  it('accepts a valid relapse report', () => {
    expect(RelapseReportRequestSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts empty context_tags', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...valid, context_tags: [] }).success).toBe(true);
  });

  it('rejects severity below 1', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...valid, severity: 0 }).success).toBe(false);
  });

  it('rejects severity above 10', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...valid, severity: 11 }).success).toBe(false);
  });

  it('rejects more than 16 context_tags', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `tag-${i}`);
    expect(RelapseReportRequestSchema.safeParse({ ...valid, context_tags: tags }).success).toBe(false);
  });

  it('rejects non-datetime occurred_at', () => {
    expect(RelapseReportRequestSchema.safeParse({ ...valid, occurred_at: '2026-04-25' }).success).toBe(false);
  });
});

describe('RelapseNextStepSchema', () => {
  it('accepts compassion_message', () => {
    expect(RelapseNextStepSchema.safeParse('compassion_message').success).toBe(true);
  });

  it('accepts review_prompt', () => {
    expect(RelapseNextStepSchema.safeParse('review_prompt').success).toBe(true);
  });

  it('accepts streak_update_summary', () => {
    expect(RelapseNextStepSchema.safeParse('streak_update_summary').success).toBe(true);
  });

  it('rejects unknown next step', () => {
    expect(RelapseNextStepSchema.safeParse('shame_message').success).toBe(false);
  });
});

describe('RelapseReportResponseSchema — resilience fields are nonnegative (CLAUDE.md Rule #3)', () => {
  const valid = {
    relapse_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    next_steps: ['compassion_message'],
    resilience_streak_days: 47,
    resilience_urges_handled_total: 89,
  };

  it('accepts a valid relapse report response', () => {
    expect(RelapseReportResponseSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts resilience_streak_days = 0', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...valid, resilience_streak_days: 0 }).success).toBe(true);
  });

  it('rejects negative resilience_streak_days (Rule #3: resilience never decrements)', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...valid, resilience_streak_days: -1 }).success).toBe(false);
  });

  it('rejects negative resilience_urges_handled_total', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...valid, resilience_urges_handled_total: -1 }).success).toBe(false);
  });

  it('rejects invalid uuid for relapse_id', () => {
    expect(RelapseReportResponseSchema.safeParse({ ...valid, relapse_id: 'not-uuid' }).success).toBe(false);
  });
});

describe('RelapseReviewRequestSchema', () => {
  it('accepts empty object (all optional)', () => {
    expect(RelapseReviewRequestSchema.safeParse({}).success).toBe(true);
  });

  it('accepts all fields present', () => {
    expect(RelapseReviewRequestSchema.safeParse({
      journal_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      ave_score: 7,
      context_tags_refined: ['stress'],
    }).success).toBe(true);
  });

  it('rejects ave_score above 10', () => {
    expect(RelapseReviewRequestSchema.safeParse({ ave_score: 11 }).success).toBe(false);
  });

  it('rejects more than 16 context_tags_refined', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `t-${i}`);
    expect(RelapseReviewRequestSchema.safeParse({ context_tags_refined: tags }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// State schemas
// ---------------------------------------------------------------------------

describe('StateLabelSchema — T0–T4 tier labels', () => {
  const labels = ['stable', 'baseline', 'elevated', 'rising_urge', 'peak_urge', 'post_urge'];

  for (const label of labels) {
    it(`accepts ${label}`, () => {
      expect(StateLabelSchema.safeParse(label).success).toBe(true);
    });
  }

  it('rejects unknown state label', () => {
    expect(StateLabelSchema.safeParse('crisis').success).toBe(false);
  });

  it('has exactly 6 valid states', () => {
    expect(labels).toHaveLength(6);
  });
});

describe('RiskWindowSchema', () => {
  const valid = {
    start: '2026-04-25T17:00:00Z',
    end: '2026-04-25T19:00:00Z',
    kind: 'predicted_urge',
  };

  it('accepts a valid risk window', () => {
    expect(RiskWindowSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts historical_peak', () => {
    expect(RiskWindowSchema.safeParse({ ...valid, kind: 'historical_peak' }).success).toBe(true);
  });

  it('accepts contextual_risk', () => {
    expect(RiskWindowSchema.safeParse({ ...valid, kind: 'contextual_risk' }).success).toBe(true);
  });

  it('rejects unknown kind', () => {
    expect(RiskWindowSchema.safeParse({ ...valid, kind: 'imminent_crisis' }).success).toBe(false);
  });

  it('rejects non-datetime start', () => {
    expect(RiskWindowSchema.safeParse({ ...valid, start: '2026-04-25' }).success).toBe(false);
  });
});

describe('TodaySummarySchema', () => {
  const valid = {
    current_state: 'stable',
    state_confidence: 0.91,
    risk_windows_today: [],
    check_in_due: false,
    open_interventions: [],
  };

  it('accepts a valid today summary', () => {
    expect(TodaySummarySchema.safeParse(valid).success).toBe(true);
  });

  it('accepts state_confidence = 0', () => {
    expect(TodaySummarySchema.safeParse({ ...valid, state_confidence: 0 }).success).toBe(true);
  });

  it('rejects state_confidence > 1', () => {
    expect(TodaySummarySchema.safeParse({ ...valid, state_confidence: 1.01 }).success).toBe(false);
  });

  it('rejects unknown current_state', () => {
    expect(TodaySummarySchema.safeParse({ ...valid, current_state: 'unknown' }).success).toBe(false);
  });
});

describe('StateEstimateUploadSchema', () => {
  const valid = {
    ts: '2026-04-25T10:00:00Z',
    state_label: 'elevated',
    confidence: 0.85,
    feature_hash: 'abc123def456',
    model_version: 'v1.2.0',
  };

  it('accepts a valid state estimate upload', () => {
    expect(StateEstimateUploadSchema.safeParse(valid).success).toBe(true);
  });

  it('rejects confidence < 0', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...valid, confidence: -0.1 }).success).toBe(false);
  });

  it('rejects invalid ts format', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...valid, ts: 'not-a-datetime' }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Urge schemas
// ---------------------------------------------------------------------------

describe('UrgeLogRequestSchema', () => {
  const valid = {
    started_at: '2026-04-25T17:30:00Z',
    intensity_start: 7,
    trigger_tags: ['stress'],
    origin: 'self_reported',
  };

  it('accepts a valid urge log request', () => {
    expect(UrgeLogRequestSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts all origin values', () => {
    for (const origin of ['self_reported', 'sensor_triggered', 'nudge_triggered']) {
      expect(UrgeLogRequestSchema.safeParse({ ...valid, origin }).success).toBe(true);
    }
  });

  it('accepts optional location_context', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...valid, location_context: 'at home' }).success).toBe(true);
  });

  it('rejects intensity_start > 10', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...valid, intensity_start: 11 }).success).toBe(false);
  });

  it('rejects intensity_start < 0', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...valid, intensity_start: -1 }).success).toBe(false);
  });

  it('rejects more than 16 trigger_tags', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `t${i}`);
    expect(UrgeLogRequestSchema.safeParse({ ...valid, trigger_tags: tags }).success).toBe(false);
  });
});

describe('UrgeLogResponseSchema', () => {
  const valid = {
    urge_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    recommended_tool: {
      tool_variant: 'box_breathing',
      rationale: 'Effective for 5 PM urges',
      bandit_arm: 'arm-3',
      intervention_id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    },
  };

  it('accepts a valid urge log response', () => {
    expect(UrgeLogResponseSchema.safeParse(valid).success).toBe(true);
  });

  it('rejects invalid urge_id uuid', () => {
    expect(UrgeLogResponseSchema.safeParse({ ...valid, urge_id: 'not-uuid' }).success).toBe(false);
  });

  it('rejects invalid intervention_id uuid in recommended_tool', () => {
    expect(UrgeLogResponseSchema.safeParse({
      ...valid,
      recommended_tool: { ...valid.recommended_tool, intervention_id: 'not-uuid' },
    }).success).toBe(false);
  });
});

describe('SosRequestSchema', () => {
  it('accepts a valid SOS request', () => {
    expect(SosRequestSchema.safeParse({ started_at: '2026-04-25T17:00:00Z' }).success).toBe(true);
  });

  it('rejects non-datetime started_at', () => {
    expect(SosRequestSchema.safeParse({ started_at: '2026-04-25' }).success).toBe(false);
  });
});

describe('SosResponseSchema', () => {
  const valid = {
    urge_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    intervention_id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    payload: {
      ui_template: 'sos_v1',
      tools_hardcoded: ['grounding_5_4_3_2_1'],
      support_contact: null,
      local_hotline: null,
    },
  };

  it('accepts a valid SOS response', () => {
    expect(SosResponseSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts support_contact with name and phone', () => {
    expect(SosResponseSchema.safeParse({
      ...valid,
      payload: { ...valid.payload, support_contact: { name: 'Alex', phone: '+1-555-0101' } },
    }).success).toBe(true);
  });

  it('accepts local_hotline string', () => {
    expect(SosResponseSchema.safeParse({
      ...valid,
      payload: { ...valid.payload, local_hotline: '988' },
    }).success).toBe(true);
  });
});

describe('UrgeResolveRequestSchema', () => {
  const valid = {
    intensity_peak: 8,
    intensity_end: 3,
    handled: true,
  };

  it('accepts a valid resolve request', () => {
    expect(UrgeResolveRequestSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts optional note', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...valid, note: 'Used box breathing.' }).success).toBe(true);
  });

  it('rejects intensity_peak > 10', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...valid, intensity_peak: 11 }).success).toBe(false);
  });

  it('rejects intensity_end < 0', () => {
    expect(UrgeResolveRequestSchema.safeParse({ ...valid, intensity_end: -1 }).success).toBe(false);
  });
});

describe('InterventionOutcomeRequestSchema', () => {
  it('accepts handled outcome', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type: 'handled' }).success).toBe(true);
  });

  it('accepts partial outcome', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type: 'partial' }).success).toBe(true);
  });

  it('accepts relapsed outcome', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type: 'relapsed' }).success).toBe(true);
  });

  it('accepts skipped outcome', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type: 'skipped' }).success).toBe(true);
  });

  it('rejects unknown outcome_type', () => {
    expect(InterventionOutcomeRequestSchema.safeParse({ outcome_type: 'ignored' }).success).toBe(false);
  });
});

describe('NudgeAckSchema', () => {
  it('accepts accepted', () => {
    expect(NudgeAckSchema.safeParse('accepted').success).toBe(true);
  });

  it('accepts snoozed', () => {
    expect(NudgeAckSchema.safeParse('snoozed').success).toBe(true);
  });

  it('accepts dismissed', () => {
    expect(NudgeAckSchema.safeParse('dismissed').success).toBe(true);
  });

  it('rejects unknown ack', () => {
    expect(NudgeAckSchema.safeParse('ignored').success).toBe(false);
  });
});

describe('NudgeAckRequestSchema', () => {
  it('accepts valid ack', () => {
    expect(NudgeAckRequestSchema.safeParse({ ack: 'accepted' }).success).toBe(true);
  });

  it('rejects invalid ack value', () => {
    expect(NudgeAckRequestSchema.safeParse({ ack: 'unknown' }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Streak schema
// ---------------------------------------------------------------------------

describe('StreakStateSchema — resilience_days is nonnegative (CLAUDE.md Rule #3)', () => {
  const valid = {
    continuous_days: 12,
    continuous_streak_start: '2026-04-11T00:00:00Z',
    resilience_days: 47,
    resilience_urges_handled_total: 89,
    resilience_streak_start: '2026-03-07T00:00:00Z',
  };

  it('accepts a valid streak state', () => {
    expect(StreakStateSchema.safeParse(valid).success).toBe(true);
  });

  it('accepts continuous_streak_start as null', () => {
    expect(StreakStateSchema.safeParse({ ...valid, continuous_streak_start: null }).success).toBe(true);
  });

  it('accepts resilience_days = 0', () => {
    expect(StreakStateSchema.safeParse({ ...valid, resilience_days: 0 }).success).toBe(true);
  });

  it('rejects negative continuous_days', () => {
    expect(StreakStateSchema.safeParse({ ...valid, continuous_days: -1 }).success).toBe(false);
  });

  it('rejects negative resilience_days (Rule #3: resilience never decrements)', () => {
    expect(StreakStateSchema.safeParse({ ...valid, resilience_days: -1 }).success).toBe(false);
  });

  it('rejects negative resilience_urges_handled_total', () => {
    expect(StreakStateSchema.safeParse({ ...valid, resilience_urges_handled_total: -1 }).success).toBe(false);
  });

  it('rejects non-datetime resilience_streak_start', () => {
    expect(StreakStateSchema.safeParse({ ...valid, resilience_streak_start: '2026-03-07' }).success).toBe(false);
  });
});
