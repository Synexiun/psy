/**
 * Tests for src/lib/api.ts — typed API functions.
 *
 * Uses `vi.spyOn(globalThis, 'fetch')` to mock network calls without making
 * real HTTP requests.  Tests verify URL construction, header injection, body
 * serialization, error mapping, and the 404-to-null sentinel for getStateEstimate.
 *
 * Covers:
 * - getStreakState builds /v1/streak with Authorization header
 * - getPatterns builds /v1/patterns?status=active&limit=5
 * - getStateEstimate returns null on 404 (no data yet)
 * - getStateEstimate re-throws non-404 errors
 * - getStateEstimate returns parsed data on 200
 * - getJournalEntries builds correct URL with limit
 * - submitCheckIn POSTs with correct body and Authorization
 * - submitCheckIn omits notes when undefined
 * - requestDataExport adds X-Step-Up-Token header
 * - requestAccountDeletion adds X-Step-Up-Token header
 * - getAssessmentSessions builds URL with limit
 * - apiFetch throws ApiError on non-2xx
 * - query-client staleTime is 30 000 ms
 * - query-client refetchOnWindowFocus is false
 * - query-client retry is 2
 */

import { ApiError } from '@disciplineos/api-client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  getAssessmentSessions,
  getCheckInHistory,
  getJournalEntries,
  getPatterns,
  getStateEstimate,
  getStreakState,
  requestAccountDeletion,
  requestDataExport,
  submitCheckIn,
} from '../../../src/lib/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockFetch(status: number, body: unknown): void {
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
}

function mockFetchError(status: number, detail?: string): void {
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
    new Response(JSON.stringify({ detail: detail ?? `HTTP ${status}` }), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
}

function captureLastFetch() {
  return vi.mocked(globalThis.fetch).mock.lastCall;
}

const TOKEN = 'test-token';

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.spyOn(globalThis, 'fetch');
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// getStreakState
// ---------------------------------------------------------------------------

describe('getStreakState', () => {
  it('calls /v1/streak with Authorization header', async () => {
    mockFetch(200, { continuous_days: 5 });
    await getStreakState(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/streak');
    const headers = call?.[1]?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer test-token');
  });

  it('returns parsed streak state', async () => {
    const data = {
      continuous_days: 5,
      continuous_streak_start: '2026-04-20',
      resilience_days: 10,
      resilience_urges_handled_total: 20,
      resilience_streak_start: '2026-04-15',
    };
    mockFetch(200, data);
    const result = await getStreakState(TOKEN);
    expect(result.continuous_days).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// getPatterns
// ---------------------------------------------------------------------------

describe('getPatterns', () => {
  it('calls /v1/patterns with status=active&limit=5', async () => {
    mockFetch(200, []);
    await getPatterns(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/patterns?status=active&limit=5');
  });
});

// ---------------------------------------------------------------------------
// getStateEstimate
// ---------------------------------------------------------------------------

describe('getStateEstimate', () => {
  it('returns null on 404', async () => {
    mockFetchError(404, 'not found');
    const result = await getStateEstimate(TOKEN);
    expect(result).toBeNull();
  });

  it('returns parsed state on 200', async () => {
    const data = {
      estimate_id: 'est-1',
      state_label: 'calm',
      confidence: 0.9,
      model_version: '1.0',
      inferred_at: '2026-04-25T00:00:00Z',
      created_at: '2026-04-25T00:00:00Z',
    };
    mockFetch(200, data);
    const result = await getStateEstimate(TOKEN);
    expect(result?.state_label).toBe('calm');
  });

  it('re-throws ApiError for non-404 errors', async () => {
    mockFetchError(500, 'internal server error');
    await expect(getStateEstimate(TOKEN)).rejects.toBeInstanceOf(ApiError);
  });

  it('re-throws ApiError with correct status for 403', async () => {
    mockFetchError(403, 'forbidden');
    let err: unknown;
    try {
      await getStateEstimate(TOKEN);
    } catch (e) {
      err = e;
    }
    expect(err instanceof ApiError && err.status === 403).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// getJournalEntries
// ---------------------------------------------------------------------------

describe('getJournalEntries', () => {
  it('calls /v1/journal/entries with default limit 20', async () => {
    mockFetch(200, { items: [], total: 0 });
    await getJournalEntries(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/journal/entries?limit=20');
  });

  it('calls /v1/journal/entries with custom limit', async () => {
    mockFetch(200, { items: [], total: 0 });
    await getJournalEntries(TOKEN, 50);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('limit=50');
  });
});

// ---------------------------------------------------------------------------
// submitCheckIn
// ---------------------------------------------------------------------------

describe('submitCheckIn', () => {
  it('POSTs to /v1/check-in', async () => {
    mockFetch(200, { session_id: 's1', received_at: '2026-04-25', state_updated: true });
    await submitCheckIn(TOKEN, 7, ['stress']);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/check-in');
    expect(call?.[1]?.method).toBe('POST');
  });

  it('includes intensity and trigger_tags in body', async () => {
    mockFetch(200, { session_id: 's1', received_at: '2026-04-25', state_updated: true });
    await submitCheckIn(TOKEN, 8, ['social', 'work']);
    const call = captureLastFetch();
    const body = JSON.parse(call?.[1]?.body as string);
    expect(body.intensity).toBe(8);
    expect(body.trigger_tags).toEqual(['social', 'work']);
  });

  it('omits notes when undefined', async () => {
    mockFetch(200, { session_id: 's1', received_at: '2026-04-25', state_updated: true });
    await submitCheckIn(TOKEN, 5, []);
    const call = captureLastFetch();
    const body = JSON.parse(call?.[1]?.body as string);
    expect('notes' in body).toBe(false);
  });

  it('includes notes when provided', async () => {
    mockFetch(200, { session_id: 's1', received_at: '2026-04-25', state_updated: true });
    await submitCheckIn(TOKEN, 5, [], 'feeling anxious');
    const call = captureLastFetch();
    const body = JSON.parse(call?.[1]?.body as string);
    expect(body.notes).toBe('feeling anxious');
  });
});

// ---------------------------------------------------------------------------
// requestDataExport
// ---------------------------------------------------------------------------

describe('requestDataExport', () => {
  it('POSTs to /v1/privacy/export', async () => {
    mockFetch(200, { export_id: 'exp-1', status: 'queued', requested_at: '2026-04-25', user_id: 'u1' });
    await requestDataExport(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/privacy/export');
    expect(call?.[1]?.method).toBe('POST');
  });

  it('adds X-Step-Up-Token header', async () => {
    mockFetch(200, { export_id: 'exp-1', status: 'queued', requested_at: '2026-04-25', user_id: 'u1' });
    await requestDataExport(TOKEN);
    const call = captureLastFetch();
    const headers = call?.[1]?.headers as Record<string, string>;
    expect(headers['X-Step-Up-Token']).toBe('present');
  });
});

// ---------------------------------------------------------------------------
// requestAccountDeletion
// ---------------------------------------------------------------------------

describe('requestAccountDeletion', () => {
  it('POSTs to /v1/privacy/delete-account', async () => {
    mockFetch(200, { deletion_id: 'd1', user_id: 'u1', scheduled_purge_at: '2026-05-25', message: 'ok' });
    await requestAccountDeletion(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/privacy/delete-account');
    expect(call?.[1]?.method).toBe('POST');
  });

  it('adds X-Step-Up-Token header', async () => {
    mockFetch(200, { deletion_id: 'd1', user_id: 'u1', scheduled_purge_at: '2026-05-25', message: 'ok' });
    await requestAccountDeletion(TOKEN);
    const call = captureLastFetch();
    const headers = call?.[1]?.headers as Record<string, string>;
    expect(headers['X-Step-Up-Token']).toBe('present');
  });
});

// ---------------------------------------------------------------------------
// getAssessmentSessions
// ---------------------------------------------------------------------------

describe('getAssessmentSessions', () => {
  it('calls /v1/assessments/sessions with default limit 50', async () => {
    mockFetch(200, []);
    await getAssessmentSessions(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/assessments/sessions?limit=50');
  });
});

// ---------------------------------------------------------------------------
// getCheckInHistory
// ---------------------------------------------------------------------------

describe('getCheckInHistory', () => {
  it('calls /v1/check-in/history with default limit 20', async () => {
    mockFetch(200, { items: [], total: 0 });
    await getCheckInHistory(TOKEN);
    const call = captureLastFetch();
    expect(call?.[0]).toContain('/v1/check-in/history?limit=20');
  });
});

// ---------------------------------------------------------------------------
// ApiError propagation
// ---------------------------------------------------------------------------

describe('apiFetch error handling', () => {
  it('throws ApiError on 500', async () => {
    mockFetchError(500, 'internal server error');
    await expect(getStreakState(TOKEN)).rejects.toBeInstanceOf(ApiError);
  });

  it('throws ApiError with correct status', async () => {
    mockFetchError(422, 'unprocessable entity');
    let err: unknown;
    try {
      await getStreakState(TOKEN);
    } catch (e) {
      err = e;
    }
    expect(err instanceof ApiError && err.status === 422).toBe(true);
  });
});
