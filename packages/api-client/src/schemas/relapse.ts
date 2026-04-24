/**
 * Relapse schemas — mirrors `POST /v1/relapses` and `POST /v1/relapses/{id}/review`.
 * Shape is authoritative in Docs/Technicals/03_API_Specification.md §6.
 *
 * Copy rules: The response always includes resilience_streak_days so the UI can
 * display the affirmation that resilience was preserved (non-negotiable per CLAUDE.md #3/#4).
 */

import { z } from 'zod';

export const RelapseReportRequestSchema = z.object({
  occurred_at: z.string().datetime(),
  behavior: z.string(),
  severity: z.number().int().min(1).max(10),
  context_tags: z.array(z.string()).max(16),
});
export type RelapseReportRequest = z.infer<typeof RelapseReportRequestSchema>;

export const RelapseNextStepSchema = z.enum([
  'compassion_message',
  'review_prompt',
  'streak_update_summary',
]);
export type RelapseNextStep = z.infer<typeof RelapseNextStepSchema>;

export const RelapseReportResponseSchema = z.object({
  relapse_id: z.string().uuid(),
  next_steps: z.array(RelapseNextStepSchema),
  resilience_streak_days: z.number().int().nonnegative(),
  resilience_urges_handled_total: z.number().int().nonnegative(),
});
export type RelapseReportResponse = z.infer<typeof RelapseReportResponseSchema>;

export const RelapseReviewRequestSchema = z.object({
  journal_id: z.string().uuid().optional(),
  ave_score: z.number().int().min(0).max(10).optional(),
  context_tags_refined: z.array(z.string()).max(16).optional(),
});
export type RelapseReviewRequest = z.infer<typeof RelapseReviewRequestSchema>;
