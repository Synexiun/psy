/**
 * Relapse endpoint helpers.
 *
 * Copy rule: the response from `reportRelapse` always includes
 * `resilience_streak_days`. The caller MUST display the resilience-preserved
 * affirmation to the user. Never show "streak reset" framing.
 * See CLAUDE.md non-negotiable #3/#4 and shared-rules/relapse_templates.json.
 */

import type { ApiClient } from '../index';
import {
  RelapseReportRequestSchema,
  RelapseReportResponseSchema,
  RelapseReviewRequestSchema,
  type RelapseReportRequest,
  type RelapseReportResponse,
  type RelapseReviewRequest,
} from '../schemas/relapse';

/**
 * POST /v1/relapses
 * Requires `Idempotency-Key` header.
 */
export async function reportRelapse(
  client: ApiClient,
  request: RelapseReportRequest,
  idempotencyKey: string,
): Promise<RelapseReportResponse> {
  const body = RelapseReportRequestSchema.parse(request);
  const data = await client.post<unknown>('v1/relapses', body, {
    headers: { 'Idempotency-Key': idempotencyKey },
  });
  return RelapseReportResponseSchema.parse(data);
}

/**
 * POST /v1/relapses/{relapse_id}/review
 */
export async function submitRelapseReview(
  client: ApiClient,
  relapseId: string,
  request: RelapseReviewRequest,
): Promise<void> {
  const body = RelapseReviewRequestSchema.parse(request);
  await client.post<unknown>(`v1/relapses/${relapseId}/review`, body);
}
