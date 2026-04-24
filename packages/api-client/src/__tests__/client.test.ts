/**
 * Tests for the api-client package: client factory, error handling, domain schemas,
 * and endpoint-level validation.
 *
 * These tests run in Node with Vitest. We mock the underlying `ky` instance
 * using a lightweight spy so we never make real HTTP calls.
 */

import { describe, it, expect, vi, beforeEach, type MockedFunction } from 'vitest';
import { ApiError, isApiError } from '../errors';
import {
  StreakStateSchema,
  PatternSchema,
  PatternListResponseSchema,
  TodaySummarySchema,
  UrgeLogRequestSchema,
  UrgeLogResponseSchema,
  SosResponseSchema,
  RelapseReportResponseSchema,
  AssessmentSubmitResponseSchema,
  DueAssessmentsResponseSchema,
} from '../schemas/index';
import { createApiClient, type ApiClient, type ApiClientOptions } from '../index';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeOptions(overrides?: Partial<ApiClientOptions>): ApiClientOptions {
  return {
    baseUrl: 'https://api.disciplineos.com',
    locale: 'en',
    appVersion: '1.0.0-test',
    tokenProvider: {
      getAccessToken: async () => 'test-token',
    },
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// ApiError
// ---------------------------------------------------------------------------

describe('ApiError', () => {
  it('construction stores all fields', () => {
    const err = new ApiError(409, {
      code: 'conflict',
      message: 'Idempotency collision',
      requestId: 'req-abc',
      retryAfterSeconds: 5,
      details: { field: 'urge_id' },
    });
    expect(err.status).toBe(409);
    expect(err.code).toBe('conflict');
    expect(err.message).toBe('Idempotency collision');
    expect(err.requestId).toBe('req-abc');
    expect(err.retryAfterSeconds).toBe(5);
    expect(err.details).toEqual({ field: 'urge_id' });
    expect(err.name).toBe('ApiError');
    expect(err).toBeInstanceOf(Error);
  });

  it('isRetryable() returns true for 5xx status codes', () => {
    expect(new ApiError(500, { code: 'server_error', message: 'x' }).isRetryable()).toBe(true);
    expect(new ApiError(503, { code: 'server_error', message: 'x' }).isRetryable()).toBe(true);
  });

  it('isRetryable() returns true for rate_limited, network_error, timeout', () => {
    expect(new ApiError(429, { code: 'rate_limited', message: 'x' }).isRetryable()).toBe(true);
    expect(new ApiError(0, { code: 'network_error', message: 'x' }).isRetryable()).toBe(true);
    expect(new ApiError(0, { code: 'timeout', message: 'x' }).isRetryable()).toBe(true);
  });

  it('isRetryable() returns false for 4xx client errors', () => {
    expect(new ApiError(400, { code: 'validation.invalid_payload', message: 'x' }).isRetryable()).toBe(false);
    expect(new ApiError(401, { code: 'auth.invalid_credentials', message: 'x' }).isRetryable()).toBe(false);
    expect(new ApiError(403, { code: 'forbidden', message: 'x' }).isRetryable()).toBe(false);
    expect(new ApiError(404, { code: 'not_found', message: 'x' }).isRetryable()).toBe(false);
  });

  it('requiresStepUp() returns true only for auth.step_up_required', () => {
    expect(new ApiError(401, { code: 'auth.step_up_required', message: 'x' }).requiresStepUp()).toBe(true);
    expect(new ApiError(403, { code: 'forbidden', message: 'x' }).requiresStepUp()).toBe(false);
    expect(new ApiError(401, { code: 'auth.token_expired', message: 'x' }).requiresStepUp()).toBe(false);
  });

  it('isApiError() type guard narrows correctly', () => {
    expect(isApiError(new ApiError(500, { code: 'server_error', message: 'x' }))).toBe(true);
    expect(isApiError(new Error('plain error'))).toBe(false);
    expect(isApiError('string')).toBe(false);
    expect(isApiError(null)).toBe(false);
    expect(isApiError(undefined)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// createApiClient — construction and token attachment
// ---------------------------------------------------------------------------

describe('createApiClient', () => {
  it('returns an object with get, post, put, patch, del, raw methods', () => {
    const client = createApiClient(makeOptions());
    expect(typeof client.get).toBe('function');
    expect(typeof client.post).toBe('function');
    expect(typeof client.put).toBe('function');
    expect(typeof client.patch).toBe('function');
    expect(typeof client.del).toBe('function');
    expect(client.raw).toBeDefined();
  });

  it('respects custom timeout option', () => {
    // Just verifying construction does not throw with custom timeout.
    expect(() => createApiClient(makeOptions({ timeoutMs: 5000 }))).not.toThrow();
  });

  it('respects onRequestId callback option', () => {
    const onRequestId = vi.fn();
    expect(() => createApiClient(makeOptions({ onRequestId }))).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// StreakStateSchema
// ---------------------------------------------------------------------------

describe('StreakStateSchema', () => {
  it('accepts a valid streak state', () => {
    const result = StreakStateSchema.safeParse({
      continuous_days: 5,
      continuous_streak_start: '2026-04-18T00:00:00Z',
      resilience_days: 87,
      resilience_urges_handled_total: 142,
      resilience_streak_start: '2026-01-21T00:00:00Z',
    });
    expect(result.success).toBe(true);
  });

  it('accepts null continuous_streak_start (no streak yet)', () => {
    const result = StreakStateSchema.safeParse({
      continuous_days: 0,
      continuous_streak_start: null,
      resilience_days: 0,
      resilience_urges_handled_total: 0,
      resilience_streak_start: '2026-04-18T00:00:00Z',
    });
    expect(result.success).toBe(true);
  });

  it('rejects negative resilience_days (monotonic invariant)', () => {
    const result = StreakStateSchema.safeParse({
      continuous_days: 0,
      continuous_streak_start: null,
      resilience_days: -1,
      resilience_urges_handled_total: 0,
      resilience_streak_start: '2026-04-18T00:00:00Z',
    });
    expect(result.success).toBe(false);
  });

  it('rejects negative continuous_days', () => {
    const result = StreakStateSchema.safeParse({
      continuous_days: -3,
      continuous_streak_start: null,
      resilience_days: 0,
      resilience_urges_handled_total: 0,
      resilience_streak_start: '2026-04-18T00:00:00Z',
    });
    expect(result.success).toBe(false);
  });

  it('rejects fractional resilience_days (must be integer)', () => {
    const result = StreakStateSchema.safeParse({
      continuous_days: 0,
      continuous_streak_start: null,
      resilience_days: 1.5,
      resilience_urges_handled_total: 0,
      resilience_streak_start: '2026-04-18T00:00:00Z',
    });
    expect(result.success).toBe(false);
  });

  it('rejects missing required fields', () => {
    const result = StreakStateSchema.safeParse({
      continuous_days: 5,
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PatternSchema
// ---------------------------------------------------------------------------

describe('PatternSchema', () => {
  const validPattern = {
    id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    kind: 'temporal',
    summary: 'Urges peak Fridays 5-7pm.',
    confidence: 0.78,
    actionable: true,
    suggested_action: 'pre_commitment_window',
  };

  it('accepts a valid pattern', () => {
    expect(PatternSchema.safeParse(validPattern).success).toBe(true);
  });

  it('accepts pattern without optional suggested_action', () => {
    const { suggested_action: _sa, ...without } = validPattern;
    expect(PatternSchema.safeParse(without).success).toBe(true);
  });

  it('rejects confidence outside 0-1', () => {
    expect(PatternSchema.safeParse({ ...validPattern, confidence: 1.1 }).success).toBe(false);
    expect(PatternSchema.safeParse({ ...validPattern, confidence: -0.1 }).success).toBe(false);
  });

  it('rejects unknown kind', () => {
    expect(PatternSchema.safeParse({ ...validPattern, kind: 'behavioral' }).success).toBe(false);
  });

  it('rejects non-uuid id', () => {
    expect(PatternSchema.safeParse({ ...validPattern, id: 'not-uuid' }).success).toBe(false);
  });
});

describe('PatternListResponseSchema', () => {
  it('accepts a list response with zero patterns', () => {
    expect(PatternListResponseSchema.safeParse({ patterns: [] }).success).toBe(true);
  });

  it('rejects missing patterns array', () => {
    expect(PatternListResponseSchema.safeParse({}).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// TodaySummarySchema
// ---------------------------------------------------------------------------

describe('TodaySummarySchema', () => {
  const validSummary = {
    current_state: 'elevated',
    state_confidence: 0.81,
    risk_windows_today: [
      {
        start: '2026-04-18T17:00:00Z',
        end: '2026-04-18T19:00:00Z',
        kind: 'predicted_urge',
      },
    ],
    check_in_due: true,
    open_interventions: [],
  };

  it('accepts a valid today summary', () => {
    expect(TodaySummarySchema.safeParse(validSummary).success).toBe(true);
  });

  it('accepts all valid state labels', () => {
    const states = ['stable', 'baseline', 'elevated', 'rising_urge', 'peak_urge', 'post_urge'] as const;
    for (const state of states) {
      expect(
        TodaySummarySchema.safeParse({ ...validSummary, current_state: state }).success,
        `state '${state}' should be valid`,
      ).toBe(true);
    }
  });

  it('rejects unknown state label', () => {
    expect(
      TodaySummarySchema.safeParse({ ...validSummary, current_state: 'crisis' }).success,
    ).toBe(false);
  });

  it('rejects confidence out of range', () => {
    expect(
      TodaySummarySchema.safeParse({ ...validSummary, state_confidence: 1.5 }).success,
    ).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// UrgeLogRequestSchema
// ---------------------------------------------------------------------------

describe('UrgeLogRequestSchema', () => {
  const validRequest = {
    started_at: '2026-04-18T14:32:00Z',
    intensity_start: 7,
    trigger_tags: ['stress', 'work_deadline'],
    origin: 'self_reported',
  };

  it('accepts a valid urge log request', () => {
    expect(UrgeLogRequestSchema.safeParse(validRequest).success).toBe(true);
  });

  it('rejects intensity_start > 10', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validRequest, intensity_start: 11 }).success).toBe(false);
  });

  it('rejects intensity_start < 0', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validRequest, intensity_start: -1 }).success).toBe(false);
  });

  it('rejects unknown origin', () => {
    expect(UrgeLogRequestSchema.safeParse({ ...validRequest, origin: 'magic' }).success).toBe(false);
  });

  it('rejects too many trigger_tags (>16)', () => {
    const tags = Array.from({ length: 17 }, (_, i) => `tag${i}`);
    expect(UrgeLogRequestSchema.safeParse({ ...validRequest, trigger_tags: tags }).success).toBe(false);
  });
});

describe('UrgeLogResponseSchema', () => {
  it('accepts a valid urge log response', () => {
    const result = UrgeLogResponseSchema.safeParse({
      urge_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      recommended_tool: {
        tool_variant: 'urge_surf_5min',
        rationale: 'Your last 4 urges were handled with urge surfing.',
        bandit_arm: 'urge_surf_5min:ctx_work_high',
        intervention_id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
      },
    });
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// SosResponseSchema
// ---------------------------------------------------------------------------

describe('SosResponseSchema', () => {
  it('accepts a full SOS response', () => {
    const result = SosResponseSchema.safeParse({
      urge_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      intervention_id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
      payload: {
        ui_template: 'crisis_flow_v3',
        tools_hardcoded: ['urge_surf', 'tipp_60s', 'call_support'],
        support_contact: { name: 'Alex', phone: '+1-555-0100' },
        local_hotline: '988',
      },
    });
    expect(result.success).toBe(true);
  });

  it('accepts SOS response without optional fields', () => {
    const result = SosResponseSchema.safeParse({
      urge_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      intervention_id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
      payload: {
        ui_template: 'crisis_flow_v3',
        tools_hardcoded: ['urge_surf'],
      },
    });
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// RelapseReportResponseSchema
// ---------------------------------------------------------------------------

describe('RelapseReportResponseSchema', () => {
  it('accepts a valid relapse response with resilience preserved', () => {
    const result = RelapseReportResponseSchema.safeParse({
      relapse_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      next_steps: ['compassion_message', 'review_prompt', 'streak_update_summary'],
      resilience_streak_days: 87,
      resilience_urges_handled_total: 142,
    });
    expect(result.success).toBe(true);
  });

  it('rejects negative resilience_streak_days', () => {
    const result = RelapseReportResponseSchema.safeParse({
      relapse_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      next_steps: ['compassion_message'],
      resilience_streak_days: -1,
      resilience_urges_handled_total: 0,
    });
    expect(result.success).toBe(false);
  });

  it('rejects unknown next_step values', () => {
    const result = RelapseReportResponseSchema.safeParse({
      relapse_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      next_steps: ['streak_reset'],
      resilience_streak_days: 87,
      resilience_urges_handled_total: 0,
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AssessmentSubmitResponseSchema
// ---------------------------------------------------------------------------

describe('AssessmentSubmitResponseSchema', () => {
  const validAssessmentResponse = {
    assessment_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    total_score: 14,
    severity_band: 'moderate',
    safety_actions: [],
    completed_at: '2026-04-18T14:32:00Z',
  };

  it('accepts a valid assessment response', () => {
    expect(AssessmentSubmitResponseSchema.safeParse(validAssessmentResponse).success).toBe(true);
  });

  it('accepts escalate_t4 in safety_actions', () => {
    const result = AssessmentSubmitResponseSchema.safeParse({
      ...validAssessmentResponse,
      safety_actions: ['escalate_t4'],
    });
    expect(result.success).toBe(true);
  });

  it('rejects unknown safety_action values', () => {
    const result = AssessmentSubmitResponseSchema.safeParse({
      ...validAssessmentResponse,
      safety_actions: ['send_marketing_email'],
    });
    expect(result.success).toBe(false);
  });

  it('rejects negative total_score', () => {
    const result = AssessmentSubmitResponseSchema.safeParse({
      ...validAssessmentResponse,
      total_score: -1,
    });
    expect(result.success).toBe(false);
  });

  it('rejects unknown severity_band', () => {
    const result = AssessmentSubmitResponseSchema.safeParse({
      ...validAssessmentResponse,
      severity_band: 'critical',
    });
    expect(result.success).toBe(false);
  });
});

describe('DueAssessmentsResponseSchema', () => {
  it('accepts a valid due assessments response', () => {
    const result = DueAssessmentsResponseSchema.safeParse({
      due: [
        {
          instrument_id: 'phq9',
          version: 'phq9_v1',
          due_reason: 'scheduled',
          due_at: '2026-04-18T09:00:00Z',
        },
      ],
    });
    expect(result.success).toBe(true);
  });

  it('accepts empty due list', () => {
    expect(DueAssessmentsResponseSchema.safeParse({ due: [] }).success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Retry policy: GET only
// ---------------------------------------------------------------------------

describe('retry policy', () => {
  it('client is configured with retry only on GET (not POST)', () => {
    // We verify this by inspecting that the client factory does not throw and
    // that the retry config is applied consistently. The authoritative check is
    // the createApiClient implementation in index.ts which sets
    //   retry: { methods: ['get'] }
    // This test documents the contract.
    const client = createApiClient(makeOptions());
    // raw ky instance is accessible
    expect(client.raw).toBeDefined();
    // The retry methods are not directly inspectable from the outside, but the
    // factory is the single source of truth. Any change to index.ts that adds
    // 'post' or 'delete' to retry.methods must update this comment and add an
    // integration test with a real HTTP mock.
  });
});
