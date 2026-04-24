/**
 * State endpoint helpers.
 */

import type { ApiClient } from '../index';
import { isApiError } from '../errors';
import { TodaySummarySchema, type TodaySummary, type StateEstimateUpload } from '../schemas/state';

/**
 * GET /v1/today
 * Returns today's state summary for the authenticated user.
 * Returns `null` when no estimate has been recorded yet (server 404).
 */
export async function getTodaySummary(client: ApiClient): Promise<TodaySummary | null> {
  try {
    const data = await client.get<unknown>('v1/today');
    return TodaySummarySchema.parse(data);
  } catch (err) {
    if (isApiError(err) && err.status === 404) return null;
    throw err;
  }
}

/**
 * POST /v1/state/estimate
 * Uploads a device-computed state estimate to the server. Returns void on 204.
 * Fire-and-forget in the urge path — callers must not block the UI on this call.
 */
export async function uploadStateEstimate(
  client: ApiClient,
  estimate: StateEstimateUpload,
): Promise<void> {
  await client.post<unknown>('v1/state/estimate', estimate);
}
