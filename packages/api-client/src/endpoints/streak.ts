/**
 * Streak endpoint helpers.
 * Callers pass the `ApiClient` created by `createApiClient`.
 */

import type { ApiClient } from '../index';
import { StreakStateSchema, type StreakState } from '../schemas/streak';

/**
 * GET /v1/streak
 * Returns the authenticated user's current streak state.
 * Validates the response shape with Zod; throws on mismatch.
 */
export async function getStreakState(client: ApiClient): Promise<StreakState> {
  const data = await client.get<unknown>('v1/streak');
  return StreakStateSchema.parse(data);
}
