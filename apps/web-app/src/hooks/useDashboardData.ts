'use client';

import { useAuth } from '@clerk/nextjs';
import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import {
  getStreakState,
  getPatterns,
  getStateEstimate,
  getJournalEntries,
  getCheckInHistory,
  getAssessmentSessions,
  type StreakState,
  type Pattern,
  type StateEstimate,
  type JournalList,
  type CheckInHistory,
  type AssessmentSessionHistoryItem,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Re-export canonical types under the names consumers already import
// ---------------------------------------------------------------------------

/** Streak / resilience data. Mirrors `StreakState` from the backend. */
export type StreakData = StreakState;

/**
 * Journal list data. Mirrors `JournalList` from the backend.
 */
export type JournalData = JournalList;

/**
 * Check-in history data. Mirrors `CheckInHistory` from the backend.
 */
export type CheckInHistoryData = CheckInHistory;

/**
 * Pattern data. Mirrors `Pattern` from the backend.
 * Includes the `dismissed_at`, `dismiss_reason`, and `updated_at` fields
 * returned by the real API in addition to the original stub fields.
 */
export type PatternData = Pattern;

/**
 * State estimate data. Mirrors `StateEstimate` from the backend.
 * Includes the `created_at` field returned by the real API.
 */
export type StateEstimateData = StateEstimate;

/**
 * Assessment session history item. Mirrors `AssessmentSessionHistoryItem` from the backend.
 */
export type AssessmentSessionData = AssessmentSessionHistoryItem;

// ---------------------------------------------------------------------------
// Stub data (dev / test / E2E environments)
// ---------------------------------------------------------------------------

const STREAK_STUB: StreakData = {
  continuous_days: 12,
  continuous_streak_start: '2026-04-11T00:00:00Z',
  resilience_days: 47,
  resilience_urges_handled_total: 89,
  resilience_streak_start: '2026-03-07T00:00:00Z',
};

const PATTERNS_STUB: PatternData[] = [
  {
    pattern_id: 'p1',
    pattern_type: 'temporal',
    detector: 'peak_window',
    confidence: 0.82,
    description: 'Urge intensity tends to rise between 5 PM and 7 PM on weekdays.',
    metadata: { peak_start_hour: 17, peak_end_hour: 19 },
    status: 'active',
    dismissed_at: null,
    dismiss_reason: null,
    created_at: '2026-04-20T10:00:00Z',
    updated_at: '2026-04-20T10:00:00Z',
  },
  {
    pattern_id: 'p2',
    pattern_type: 'contextual',
    detector: 'co_occurring_tags',
    confidence: 0.74,
    description: 'Work stress and social situations co-occur in 68% of logged urges.',
    metadata: { tags: ['work_stress', 'social_situation'], co_occurrence_rate: 0.68 },
    status: 'active',
    dismissed_at: null,
    dismiss_reason: null,
    created_at: '2026-04-18T10:00:00Z',
    updated_at: '2026-04-18T10:00:00Z',
  },
];

const JOURNAL_STUB: JournalData = {
  items: [
    {
      journal_id: 'j-stub-1',
      title: null,
      body_preview:
        'Woke up feeling anxious but managed to get through the morning without acting on the urge.',
      mood_score: 6,
      created_at: '2026-04-23T08:14:00Z',
    },
    {
      journal_id: 'j-stub-2',
      title: null,
      body_preview:
        'Hard evening. Ran into someone from my old crowd and felt the pull strongly. Called my sponsor instead.',
      mood_score: 4,
      created_at: '2026-04-21T21:30:00Z',
    },
  ],
  total: 2,
};

const CHECK_IN_HISTORY_STUB: CheckInHistoryData = {
  items: [3, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 6, 8, 9, 8, 7, 8, 9, 8, 7].map(
    (intensity, index) => ({
      session_id: `stub-${index}`,
      intensity,
      trigger_tags: [],
      checked_in_at: new Date(Date.now() - (19 - index) * 3_600_000).toISOString(),
    }),
  ),
  total: 20,
};

const STATE_STUB: StateEstimateData = {
  estimate_id: 's1',
  state_label: 'stable',
  confidence: 0.91,
  model_version: 'v1.2.0',
  inferred_at: '2026-04-23T10:00:00Z',
  created_at: '2026-04-23T10:00:00Z',
};

// ---------------------------------------------------------------------------
// Stub-mode flag
// ---------------------------------------------------------------------------

/**
 * Returns true when the app should skip the real API and use stub data.
 *
 * Two cases:
 *   1. `NEXT_PUBLIC_USE_STUBS=true` — E2E / manual testing against a static
 *      build where the API is intentionally absent.
 *   2. `NODE_ENV === 'test'` — unit / component tests running under Vitest or
 *      Jest where the network is unavailable.
 */
function useStubs(): boolean {
  return (
    process.env['NEXT_PUBLIC_USE_STUBS'] === 'true' ||
    process.env['NODE_ENV'] === 'test'
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/**
 * Current streak / resilience state.
 * Query key is scoped to the Clerk userId so cache is per-user.
 */
export function useStreak(): UseQueryResult<StreakData> {
  const { userId, getToken } = useAuth();
  const stubMode = useStubs();

  return useQuery<StreakData>({
    queryKey: ['streak', userId],
    queryFn: async (): Promise<StreakData> => {
      if (stubMode) return STREAK_STUB;
      const token = await getToken();
      if (token === null) throw new Error('Session expired');
      return getStreakState(token);
    },
    ...(stubMode && { initialData: STREAK_STUB }),
    staleTime: 30_000,
    retry: 2,
  });
}

/**
 * Active behavioural patterns for the current user.
 * Query key is scoped to the Clerk userId.
 */
export function usePatterns(): UseQueryResult<PatternData[]> {
  const { userId, getToken } = useAuth();
  const stubMode = useStubs();

  return useQuery<PatternData[]>({
    queryKey: ['patterns', userId],
    queryFn: async (): Promise<PatternData[]> => {
      if (stubMode) return PATTERNS_STUB;
      const token = await getToken();
      if (token === null) throw new Error('Session expired');
      return getPatterns(token);
    },
    ...(stubMode && { initialData: PATTERNS_STUB }),
    staleTime: 30_000,
    retry: 2,
  });
}

/**
 * Most recent state estimate (stable / rising_urge / peak_urge / etc.).
 * Returns `null` when no estimate has been recorded yet.
 * Query key is scoped to the Clerk userId.
 */
export function useStateEstimate(): UseQueryResult<StateEstimateData | null> {
  const { userId, getToken } = useAuth();
  const stubMode = useStubs();

  return useQuery<StateEstimateData | null>({
    queryKey: ['state', userId],
    queryFn: async (): Promise<StateEstimateData | null> => {
      if (stubMode) return STATE_STUB;
      const token = await getToken();
      if (token === null) throw new Error('Session expired');
      return getStateEstimate(token);
    },
    ...(stubMode && { initialData: STATE_STUB }),
    staleTime: 30_000,
    retry: 2,
  });
}

/**
 * Paginated journal entries for the current user.
 * Query key is scoped to the Clerk userId.
 */
export function useJournalEntries(): UseQueryResult<JournalData> {
  const { userId, getToken } = useAuth();
  const stubMode = useStubs();

  return useQuery<JournalData>({
    queryKey: ['journal', userId],
    queryFn: async (): Promise<JournalData> => {
      if (stubMode) return JOURNAL_STUB;
      const token = await getToken();
      if (token === null) throw new Error('Session expired');
      return getJournalEntries(token);
    },
    ...(stubMode && { initialData: JOURNAL_STUB }),
    staleTime: 30_000,
    retry: 2,
  });
}

/**
 * Most recent check-in history (last 20 entries by default), newest first.
 * In stub mode returns synthetic entries shaped from the MOOD_STUB intensities
 * so the MoodSparkline renders meaningful data without a live API.
 * Query key is scoped to the Clerk userId.
 */
export function useCheckInHistory(): UseQueryResult<CheckInHistoryData> {
  const { userId, getToken } = useAuth();
  const stubMode = useStubs();

  return useQuery<CheckInHistoryData>({
    queryKey: ['check-in-history', userId],
    queryFn: async (): Promise<CheckInHistoryData> => {
      if (stubMode) return CHECK_IN_HISTORY_STUB;
      const token = await getToken();
      if (token === null) throw new Error('Session expired');
      return getCheckInHistory(token);
    },
    ...(stubMode && { initialData: CHECK_IN_HISTORY_STUB }),
    staleTime: 30_000,
    retry: 2,
  });
}

const ASSESSMENT_SESSIONS_STUB: AssessmentSessionData[] = [
  {
    session_id: 'as-stub-phq9',
    instrument: 'phq9',
    score: 8,
    severity: 'Mild',
    safety_flag: false,
    completed_at: '2026-04-10T09:00:00Z',
  },
  {
    session_id: 'as-stub-gad7',
    instrument: 'gad7',
    score: 6,
    severity: 'Mild',
    safety_flag: false,
    completed_at: '2026-04-10T09:05:00Z',
  },
  {
    session_id: 'as-stub-who5',
    instrument: 'who5',
    score: 14,
    severity: 'Low wellbeing',
    safety_flag: false,
    completed_at: '2026-04-10T09:10:00Z',
  },
];

/**
 * Most recent completed assessment sessions for the current user.
 * Query key is scoped to the Clerk userId.
 */
export function useAssessmentSessions(): UseQueryResult<AssessmentSessionData[]> {
  const { userId, getToken } = useAuth();
  const stubMode = useStubs();

  return useQuery<AssessmentSessionData[]>({
    queryKey: ['assessment-sessions', userId],
    queryFn: async (): Promise<AssessmentSessionData[]> => {
      if (stubMode) return ASSESSMENT_SESSIONS_STUB;
      const token = await getToken();
      if (token === null) throw new Error('Session expired');
      return getAssessmentSessions(token);
    },
    ...(stubMode && { initialData: ASSESSMENT_SESSIONS_STUB }),
    staleTime: 30_000,
    retry: 2,
  });
}
