/**
 * Pattern endpoint helpers.
 */

import type { ApiClient } from '../index';
import {
  PatternListResponseSchema,
  PatternDismissRequestSchema,
  type Pattern,
  type DismissReason,
} from '../schemas/pattern';

export interface GetPatternsOptions {
  active?: boolean;
  limit?: number;
}

/**
 * GET /v1/patterns
 * Returns active patterns for the authenticated user.
 */
export async function getPatterns(
  client: ApiClient,
  options: GetPatternsOptions = {},
): Promise<Pattern[]> {
  const params = new URLSearchParams();
  if (options.active !== undefined) params.set('active', String(options.active));
  if (options.limit !== undefined) params.set('limit', String(options.limit));
  const qs = params.size > 0 ? `?${params.toString()}` : '';
  const data = await client.get<unknown>(`v1/patterns${qs}`);
  return PatternListResponseSchema.parse(data).patterns;
}

/**
 * POST /v1/patterns/{id}/dismiss
 * Dismisses a pattern. Returns void on 204.
 */
export async function dismissPattern(
  client: ApiClient,
  patternId: string,
  reason: DismissReason,
): Promise<void> {
  const body = PatternDismissRequestSchema.parse({ reason });
  await client.post<unknown>(`v1/patterns/${patternId}/dismiss`, body);
}
