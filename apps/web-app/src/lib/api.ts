/**
 * Typed API functions for the web-app dashboard.
 *
 * Each function accepts an explicit `token: string` so the caller (a TanStack
 * Query `queryFn`) controls when the Clerk JWT is fetched — no hooks are called
 * inside this module. This keeps the module usable from both client components
 * and, in the future, Route Handlers (where `useAuth` is unavailable).
 *
 * Error contract: every non-2xx response throws an `ApiError` with a `status`
 * (HTTP code) and `message`. Callers that need to distinguish 404 from 500 can
 * check `err.status`.
 */

import { ApiError } from '@disciplineos/api-client';

// ---------------------------------------------------------------------------
// Base URL
// ---------------------------------------------------------------------------

const BASE_URL =
  (process.env['NEXT_PUBLIC_API_URL'] ?? process.env['NEXT_PUBLIC_API_BASE_URL'] ?? 'http://localhost:8000').replace(
    /\/$/,
    '',
  );

// ---------------------------------------------------------------------------
// Response type definitions
// (shapes derived from the FastAPI Pydantic models in the backend routers)
// ---------------------------------------------------------------------------

/** Mirrors `StreakState` in `services/api/src/discipline/resilience/router.py` */
export interface StreakState {
  continuous_days: number;
  continuous_streak_start: string | null;
  resilience_days: number;
  resilience_urges_handled_total: number;
  resilience_streak_start: string;
}

/** Mirrors `PatternItem` in `services/api/src/discipline/pattern/router.py` */
export interface Pattern {
  pattern_id: string;
  pattern_type: string;
  detector: string;
  confidence: number;
  description: string;
  metadata: Record<string, unknown>;
  status: string;
  dismissed_at: string | null;
  dismiss_reason: string | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors `StateEstimateItem` in `services/api/src/discipline/signal/router.py` */
export interface StateEstimate {
  estimate_id: string;
  state_label: string;
  confidence: number;
  model_version: string;
  inferred_at: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Internal fetch helper
// ---------------------------------------------------------------------------

/**
 * Typed `fetch` wrapper. Throws `ApiError` on non-2xx responses.
 * Returns `null` on HTTP 404 so callers can distinguish "no data yet" from
 * genuine server errors — used by `getStateEstimate`.
 */
async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await globalThis.fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    let code: ApiError['code'] = 'server_error';
    try {
      const body = (await response.json()) as { detail?: string; code?: ApiError['code'] };
      if (body.detail) message = body.detail;
      if (body.code) code = body.code;
    } catch {
      // response body was not JSON — keep the default message
    }
    throw new ApiError(response.status, { code, message });
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

/**
 * GET /v1/streak
 * Returns the current streak state for the authenticated user.
 */
export async function getStreakState(token: string): Promise<StreakState> {
  return apiFetch<StreakState>('/v1/streak', token);
}

/**
 * GET /v1/patterns?status=active&limit=5
 * Returns the five most recent active patterns for the authenticated user.
 */
export async function getPatterns(token: string): Promise<Pattern[]> {
  return apiFetch<Pattern[]>('/v1/patterns?status=active&limit=5', token);
}

/**
 * GET /v1/signals/state
 * Returns the most recent state estimate, or `null` if none exists yet
 * (the backend returns 404 when no estimate has been recorded).
 */
export async function getStateEstimate(token: string): Promise<StateEstimate | null> {
  try {
    return await apiFetch<StateEstimate>('/v1/signals/state', token);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

// ---------------------------------------------------------------------------
// Journal API
// ---------------------------------------------------------------------------

/** Mirrors `JournalItem` in `services/api/src/discipline/memory/router.py` */
export interface JournalItem {
  journal_id: string;
  title: string | null;
  body_preview: string;
  mood_score: number | null;
  created_at: string;
}

/** Mirrors `JournalList` in `services/api/src/discipline/memory/router.py` */
export interface JournalList {
  items: JournalItem[];
  total: number;
}

/**
 * GET /v1/journal/entries?limit={limit}
 * Returns paginated journal entries for the authenticated user.
 */
export async function getJournalEntries(token: string, limit = 20): Promise<JournalList> {
  return apiFetch<JournalList>(`/v1/journal/entries?limit=${limit}`, token);
}

// ---------------------------------------------------------------------------
// Privacy API
// ---------------------------------------------------------------------------

/** Mirrors `ExportResponse` in `services/api/src/discipline/privacy/router.py` */
export interface ExportResponse {
  export_id: string;
  user_id: string;
  status: string;
  requested_at: string;
  expires_at: string;
  data: Record<string, unknown>;
}

/** Mirrors `DeleteAccountResponse` in `services/api/src/discipline/privacy/router.py` */
export interface DeleteAccountResponse {
  deletion_id: string;
  user_id: string;
  scheduled_purge_at: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Check-in API
// ---------------------------------------------------------------------------

/** Mirrors `CheckInResponse` in `services/api/src/discipline/check_in/router.py` */
export interface CheckInResponse {
  session_id: string;
  received_at: string;
  state_updated: boolean;
}

/** Mirrors `CheckInHistoryItem` in `services/api/src/discipline/check_in/router.py` */
export interface CheckInHistoryItem {
  session_id: string;
  intensity: number;
  trigger_tags: string[];
  checked_in_at: string;
}

/** Mirrors `CheckInHistory` in `services/api/src/discipline/check_in/router.py` */
export interface CheckInHistory {
  items: CheckInHistoryItem[];
  total: number;
}

/**
 * POST /v1/check-in
 * Submits a manual urge check-in (intensity + trigger tags + optional notes).
 */
export async function submitCheckIn(
  token: string,
  intensity: number,
  triggerTags: string[],
  notes?: string,
): Promise<CheckInResponse> {
  return apiFetch<CheckInResponse>('/v1/check-in', token, {
    method: 'POST',
    body: JSON.stringify({
      intensity,
      trigger_tags: triggerTags,
      ...(notes !== undefined ? { notes } : {}),
    }),
  });
}

/**
 * GET /v1/check-in/history?limit=N
 * Returns the most recent check-ins for the authenticated user, newest first.
 * `limit` defaults to 20 and is capped at 100 by the backend.
 */
export async function getCheckInHistory(token: string, limit = 20): Promise<CheckInHistory> {
  return apiFetch<CheckInHistory>(`/v1/check-in/history?limit=${limit}`, token);
}

// ---------------------------------------------------------------------------
// Privacy API
// ---------------------------------------------------------------------------

/**
 * POST /v1/privacy/export
 * Requests a full data export for the authenticated user.
 * Requires a step-up token header (stub value used until Clerk step-up is wired).
 */
export async function requestDataExport(token: string): Promise<ExportResponse> {
  return apiFetch<ExportResponse>('/v1/privacy/export', token, {
    method: 'POST',
    headers: { 'X-Step-Up-Token': 'present' },
  });
}

// ---------------------------------------------------------------------------
// Assessment API
// ---------------------------------------------------------------------------

/** Mirrors `AssessmentSessionHistoryItem` in the psychometric router */
export interface AssessmentSessionHistoryItem {
  session_id: string;
  instrument: string;
  score: number;
  severity: string;
  safety_flag: boolean;
  completed_at: string;
}

/**
 * GET /v1/assessments/sessions?limit={limit}
 * Returns the most recent completed assessment sessions for the authenticated user.
 */
export async function getAssessmentSessions(
  token: string,
  limit = 50,
): Promise<AssessmentSessionHistoryItem[]> {
  return apiFetch<AssessmentSessionHistoryItem[]>(
    `/v1/assessments/sessions?limit=${limit}`,
    token,
  );
}

// ---------------------------------------------------------------------------
// Privacy API (continued)
// ---------------------------------------------------------------------------

/**
 * POST /v1/privacy/delete-account
 * Schedules account deletion for the authenticated user.
 * Requires a step-up token header (stub value used until Clerk step-up is wired).
 */
export async function requestAccountDeletion(
  token: string,
  reason?: string,
): Promise<DeleteAccountResponse> {
  return apiFetch<DeleteAccountResponse>('/v1/privacy/delete-account', token, {
    method: 'POST',
    headers: { 'X-Step-Up-Token': 'present' },
    body: JSON.stringify(reason !== undefined ? { reason } : {}),
  });
}
