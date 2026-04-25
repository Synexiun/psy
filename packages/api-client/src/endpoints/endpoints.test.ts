/**
 * Unit tests for api-client endpoint helpers.
 *
 * These helpers sit between callers (hooks, components) and the underlying
 * ApiClient. Each helper is a thin adapter — the tests here lock down the
 * three non-trivial behaviours:
 *
 * 1. `getTodaySummary` converts HTTP 404 → null (no estimate recorded yet)
 *    and re-throws all other errors.
 *
 * 2. `getPatterns` builds a query string only when options are provided;
 *    an empty options object produces a bare path with no `?`.
 *
 * 3. `listAssessments` includes the instrument name and a default limit of
 *    50 in the path; a custom limit overrides the default.
 *
 * All tests mock ApiClient with a Vitest spy so no network calls are made.
 */

import { describe, it, expect, vi } from 'vitest';
import { ApiError } from '../errors';
import { getTodaySummary, uploadStateEstimate } from './state';
import { getPatterns, dismissPattern } from './patterns';
import { getDueAssessments, listAssessments } from './assessment';
import { getStreakState } from './streak';
import { reportRelapse, submitRelapseReview } from './relapse';
import { logUrge, postSos, resolveUrge, recordOutcome, ackIntervention } from './urge';

// ---------------------------------------------------------------------------
// Minimal ApiClient mock
// ---------------------------------------------------------------------------

function makeClient(overrides?: { get?: unknown; post?: unknown }) {
  return {
    get: vi.fn().mockResolvedValue(overrides?.get ?? {}),
    post: vi.fn().mockResolvedValue(overrides?.post ?? {}),
  };
}

function makeNotFoundError(): ApiError {
  return new ApiError(404, { code: 'not_found', message: 'not found' });
}

// ---------------------------------------------------------------------------
// state.ts — getTodaySummary
// ---------------------------------------------------------------------------

describe('getTodaySummary', () => {
  it('returns null when server responds with 404 (no estimate recorded yet)', async () => {
    const client = makeClient();
    client.get.mockRejectedValue(makeNotFoundError());
    const result = await getTodaySummary(client as never);
    expect(result).toBeNull();
  });

  it('re-throws non-404 ApiError (server error should propagate)', async () => {
    const client = makeClient();
    const err = new ApiError(500, { code: 'server_error', message: 'internal error' });
    client.get.mockRejectedValue(err);
    await expect(getTodaySummary(client as never)).rejects.toThrow(ApiError);
  });

  it('re-throws non-ApiError (network errors should propagate)', async () => {
    const client = makeClient();
    client.get.mockRejectedValue(new Error('network failure'));
    await expect(getTodaySummary(client as never)).rejects.toThrow('network failure');
  });

  it('calls GET v1/today', async () => {
    const payload = {
      state_label: 'stable',
      confidence: 0.9,
      risk_windows: [],
      urged_last_7d: 0,
      urges_resolved_last_7d: 0,
      streak_days: 12,
      resilience_days: 47,
      recommended_intervention: null,
    };
    const client = makeClient({ get: payload });
    await getTodaySummary(client as never);
    expect(client.get).toHaveBeenCalledWith('v1/today');
  });
});

// ---------------------------------------------------------------------------
// state.ts — uploadStateEstimate
// ---------------------------------------------------------------------------

describe('uploadStateEstimate', () => {
  it('calls POST v1/state/estimate', async () => {
    const client = makeClient();
    const estimate = {
      state_label: 'stable' as const,
      confidence: 0.85,
      model_version: 'v1.0',
      computed_at: '2026-04-25T10:00:00Z',
    };
    await uploadStateEstimate(client as never, estimate);
    expect(client.post).toHaveBeenCalledWith('v1/state/estimate', estimate);
  });
});

// ---------------------------------------------------------------------------
// patterns.ts — getPatterns (query string construction)
// ---------------------------------------------------------------------------

describe('getPatterns — query string construction', () => {
  const validResponse = { patterns: [] };

  it('calls bare path when no options supplied', async () => {
    const client = makeClient({ get: validResponse });
    await getPatterns(client as never);
    expect(client.get).toHaveBeenCalledWith('v1/patterns');
  });

  it('calls bare path when empty options object supplied', async () => {
    const client = makeClient({ get: validResponse });
    await getPatterns(client as never, {});
    expect(client.get).toHaveBeenCalledWith('v1/patterns');
  });

  it('appends active=true when active option is true', async () => {
    const client = makeClient({ get: validResponse });
    await getPatterns(client as never, { active: true });
    expect(client.get).toHaveBeenCalledWith('v1/patterns?active=true');
  });

  it('appends active=false when active option is false', async () => {
    const client = makeClient({ get: validResponse });
    await getPatterns(client as never, { active: false });
    expect(client.get).toHaveBeenCalledWith('v1/patterns?active=false');
  });

  it('appends limit when limit option is provided', async () => {
    const client = makeClient({ get: validResponse });
    await getPatterns(client as never, { limit: 10 });
    expect(client.get).toHaveBeenCalledWith('v1/patterns?limit=10');
  });

  it('appends both active and limit when both provided', async () => {
    const client = makeClient({ get: validResponse });
    await getPatterns(client as never, { active: true, limit: 5 });
    const url = (client.get.mock.calls[0] as [string])[0];
    expect(url).toContain('active=true');
    expect(url).toContain('limit=5');
    expect(url).toContain('v1/patterns?');
  });

  it('returns the patterns array from the parsed response', async () => {
    const pattern = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      kind: 'temporal',
      summary: 'Urge peaks at 5 PM',
      confidence: 0.82,
      actionable: true,
      suggested_action: 'Use box breathing',
    };
    const client = makeClient({ get: { patterns: [pattern] } });
    const result = await getPatterns(client as never);
    expect(result).toHaveLength(1);
    expect(result[0]?.id).toBe(pattern.id);
  });
});

// ---------------------------------------------------------------------------
// patterns.ts — dismissPattern
// ---------------------------------------------------------------------------

describe('dismissPattern', () => {
  it('calls POST v1/patterns/{id}/dismiss', async () => {
    const client = makeClient();
    await dismissPattern(client as never, 'pattern-abc', 'not_useful');
    expect(client.post).toHaveBeenCalledWith(
      'v1/patterns/pattern-abc/dismiss',
      { reason: 'not_useful' },
    );
  });
});

// ---------------------------------------------------------------------------
// assessment.ts — listAssessments (default limit)
// ---------------------------------------------------------------------------

describe('listAssessments', () => {
  it('uses default limit of 50 when no limit provided', async () => {
    const client = makeClient({ get: { assessments: [] } });
    await listAssessments(client as never, 'phq9');
    expect(client.get).toHaveBeenCalledWith('v1/psychometric/assessments?instrument=phq9&limit=50');
  });

  it('uses custom limit when provided', async () => {
    const client = makeClient({ get: { assessments: [] } });
    await listAssessments(client as never, 'gad7', 10);
    expect(client.get).toHaveBeenCalledWith('v1/psychometric/assessments?instrument=gad7&limit=10');
  });

  it('returns the assessments array', async () => {
    const items = [{ session_id: 's1', score: 8 }];
    const client = makeClient({ get: { assessments: items } });
    const result = await listAssessments(client as never, 'phq9');
    expect(result).toEqual(items);
  });
});

// ---------------------------------------------------------------------------
// assessment.ts — getDueAssessments
// ---------------------------------------------------------------------------

describe('getDueAssessments', () => {
  it('calls GET v1/psychometric/due', async () => {
    const payload = {
      due: [],
      next_scheduled_at: null,
    };
    const client = makeClient({ get: payload });
    await getDueAssessments(client as never);
    expect(client.get).toHaveBeenCalledWith('v1/psychometric/due');
  });
});

// ---------------------------------------------------------------------------
// streak.ts — getStreakState
// ---------------------------------------------------------------------------

describe('getStreakState', () => {
  it('calls GET v1/streak', async () => {
    const payload = {
      continuous_days: 12,
      continuous_streak_start: '2026-04-11T00:00:00Z',
      resilience_days: 47,
      resilience_urges_handled_total: 89,
      resilience_streak_start: '2026-03-07T00:00:00Z',
    };
    const client = makeClient({ get: payload });
    await getStreakState(client as never);
    expect(client.get).toHaveBeenCalledWith('v1/streak');
  });

  it('returns the validated StreakState from the response', async () => {
    const payload = {
      continuous_days: 5,
      continuous_streak_start: null,
      resilience_days: 30,
      resilience_urges_handled_total: 42,
      resilience_streak_start: '2026-03-01T00:00:00Z',
    };
    const client = makeClient({ get: payload });
    const result = await getStreakState(client as never);
    expect(result.resilience_days).toBe(30);
  });
});

// ---------------------------------------------------------------------------
// relapse.ts — reportRelapse (CLAUDE.md rule #3/#4: resilience preserved)
// ---------------------------------------------------------------------------

describe('reportRelapse', () => {
  it('calls POST v1/relapses with Idempotency-Key header', async () => {
    const response = {
      relapse_id: '550e8400-e29b-41d4-a716-446655440000',
      next_steps: ['compassion_message'] as const,
      resilience_streak_days: 47,
      resilience_urges_handled_total: 89,
    };
    const client = makeClient({ post: response });
    const request = {
      occurred_at: '2026-04-23T08:00:00Z',
      behavior: 'test',
      severity: 5,
      context_tags: [],
    };
    await reportRelapse(client as never, request, 'idem-key-001');
    expect(client.post).toHaveBeenCalledWith(
      'v1/relapses',
      expect.objectContaining({ behavior: 'test' }),
      { headers: { 'Idempotency-Key': 'idem-key-001' } },
    );
  });

  it('returns a response containing resilience_streak_days (rule #3)', async () => {
    const response = {
      relapse_id: '550e8400-e29b-41d4-a716-446655440000',
      next_steps: ['compassion_message'] as const,
      resilience_streak_days: 47,
      resilience_urges_handled_total: 89,
    };
    const client = makeClient({ post: response });
    const result = await reportRelapse(
      client as never,
      {
        occurred_at: '2026-04-23T08:00:00Z',
        behavior: 'test',
        severity: 5,
        context_tags: [],
      },
      'idem-key-002',
    );
    expect(result.resilience_streak_days).toBe(47);
  });
});

describe('submitRelapseReview', () => {
  it('calls POST v1/relapses/{id}/review', async () => {
    const client = makeClient();
    await submitRelapseReview(client as never, 'relapse-abc', {});
    expect(client.post).toHaveBeenCalledWith(
      'v1/relapses/relapse-abc/review',
      expect.any(Object),
    );
  });
});

// ---------------------------------------------------------------------------
// urge.ts — logUrge and postSos (Idempotency-Key required)
// ---------------------------------------------------------------------------

describe('logUrge', () => {
  it('calls POST v1/urges with Idempotency-Key header', async () => {
    const response = {
      urge_id: '550e8400-e29b-41d4-a716-446655440001',
      logged_at: '2026-04-23T10:00:00Z',
      intervention_id: null,
    };
    const client = makeClient({ post: response });
    await logUrge(
      client as never,
      { started_at: '2026-04-23T10:00:00Z', intensity_start: 7, trigger_tags: ['stress'], origin: 'self_reported' as const },
      'idem-urge-001',
    );
    expect(client.post).toHaveBeenCalledWith(
      'v1/urges',
      expect.any(Object),
      { headers: { 'Idempotency-Key': 'idem-urge-001' } },
    );
  });
});

describe('postSos', () => {
  it('calls POST v1/sos with Idempotency-Key header', async () => {
    const response = {
      sos_id: '550e8400-e29b-41d4-a716-446655440002',
      received_at: '2026-04-23T10:00:00Z',
    };
    const client = makeClient({ post: response });
    await postSos(
      client as never,
      { started_at: '2026-04-23T10:00:00Z' },
      'idem-sos-001',
    );
    expect(client.post).toHaveBeenCalledWith(
      'v1/sos',
      expect.any(Object),
      { headers: { 'Idempotency-Key': 'idem-sos-001' } },
    );
  });
});

describe('resolveUrge', () => {
  it('calls POST v1/urges/{id}/resolve', async () => {
    const client = makeClient();
    await resolveUrge(client as never, 'urge-abc', {
      intensity_peak: 7,
      intensity_end: 3,
      handled: true,
    });
    expect(client.post).toHaveBeenCalledWith(
      'v1/urges/urge-abc/resolve',
      expect.any(Object),
    );
  });
});

describe('recordOutcome', () => {
  it('calls POST v1/interventions/{id}/outcome with Idempotency-Key', async () => {
    const response = {
      outcome_id: 'oc-001',
      recorded_at: '2026-04-23T10:05:00Z',
    };
    const client = makeClient({ post: response });
    await recordOutcome(
      client as never,
      'intervention-abc',
      { outcome_type: 'handled' as const },
      'idem-outcome-001',
    );
    expect(client.post).toHaveBeenCalledWith(
      'v1/interventions/intervention-abc/outcome',
      expect.any(Object),
      { headers: { 'Idempotency-Key': 'idem-outcome-001' } },
    );
  });
});

describe('ackIntervention', () => {
  it('calls POST v1/interventions/{id}/ack', async () => {
    const client = makeClient();
    await ackIntervention(client as never, 'intervention-abc', 'dismissed');
    expect(client.post).toHaveBeenCalledWith(
      'v1/interventions/intervention-abc/ack',
      { ack: 'dismissed' },
    );
  });
});
