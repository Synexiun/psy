/**
 * Psychometric assessment endpoint helpers.
 *
 * Safety rule: after `submitAssessment`, callers MUST inspect
 * `response.safety_actions`. If it contains `escalate_t4`, the caller must
 * immediately route to the T4 crisis flow. Do not display a score before
 * handling safety actions. See CLAUDE.md non-negotiable #1.
 *
 * Score display rule: render `total_score` using Latin digits regardless of
 * locale (`format_number_clinical` on the client). See CLAUDE.md rule #9.
 */

import type { ApiClient } from '../index';
import {
  AssessmentSubmitRequestSchema,
  AssessmentSubmitResponseSchema,
  DueAssessmentsResponseSchema,
  type AssessmentSubmitRequest,
  type AssessmentSubmitResponse,
  type DueAssessmentsResponse,
} from '../schemas/assessment';
import type { AssessmentKind } from '../schemas';

/**
 * GET /v1/psychometric/due
 * Returns which instruments are due for the authenticated user right now.
 */
export async function getDueAssessments(client: ApiClient): Promise<DueAssessmentsResponse> {
  const data = await client.get<unknown>('v1/psychometric/due');
  return DueAssessmentsResponseSchema.parse(data);
}

/**
 * POST /v1/psychometric/assessments
 * Submits a completed assessment. Always check `safety_actions` on the response.
 */
export async function submitAssessment(
  client: ApiClient,
  request: AssessmentSubmitRequest,
): Promise<AssessmentSubmitResponse> {
  const body = AssessmentSubmitRequestSchema.parse(request);
  const data = await client.post<unknown>('v1/psychometric/assessments', body);
  return AssessmentSubmitResponseSchema.parse(data);
}

/**
 * GET /v1/psychometric/assessments
 * Lists past assessments for a given instrument.
 */
export async function listAssessments(
  client: ApiClient,
  instrument: AssessmentKind,
  limit = 50,
): Promise<unknown[]> {
  const data = await client.get<{ assessments: unknown[] }>(
    `v1/psychometric/assessments?instrument=${instrument}&limit=${limit}`,
  );
  return data.assessments;
}
