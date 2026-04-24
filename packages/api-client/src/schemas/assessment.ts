/**
 * Psychometric assessment schemas — mirrors `POST /v1/psychometric/assessments`,
 * `GET /v1/psychometric/due`, and related endpoints.
 * Shape is authoritative in Docs/Technicals/03_API_Specification.md §20
 * and Docs/Technicals/12_Psychometric_System.md.
 *
 * Safety note: if `safety_actions` includes `escalate_t4` the client MUST
 * immediately route to the T4 crisis flow. The API always returns this field;
 * the client must always honor it (CLAUDE.md non-negotiable #1).
 *
 * Scoring note: `total_score` and `severity_band` are computed by validated
 * deterministic functions server-side (Kroenke 2001 / Spitzer 2006 bands).
 * Never re-compute or interpret these client-side.
 */

import { z } from 'zod';
import { AssessmentKindSchema } from '../schemas';

export { AssessmentKindSchema };

export const AssessmentResponseItemSchema = z.object({
  item: z.number().int().positive(),
  value: z.number().int().nonnegative(),
});
export type AssessmentResponseItem = z.infer<typeof AssessmentResponseItemSchema>;

export const AssessmentSubmitRequestSchema = z.object({
  instrument_id: AssessmentKindSchema,
  /** Instrument definition version, e.g. "phq9_v1". Provided by the due-list response. */
  version: z.string(),
  responses: z.array(AssessmentResponseItemSchema),
});
export type AssessmentSubmitRequest = z.infer<typeof AssessmentSubmitRequestSchema>;

export const SeverityBandSchema = z.enum([
  'none',
  'minimal',
  'mild',
  'moderate',
  'moderately_severe',
  'severe',
]);
export type SeverityBand = z.infer<typeof SeverityBandSchema>;

export const SafetyActionSchema = z.enum([
  'escalate_t4',
  'notify_clinician',
  'show_crisis_resources',
  'schedule_followup',
]);
export type SafetyAction = z.infer<typeof SafetyActionSchema>;

export const AssessmentSubmitResponseSchema = z.object({
  assessment_id: z.string().uuid(),
  total_score: z.number().int().nonnegative(),
  subscale_scores: z.record(z.number()).optional(),
  severity_band: SeverityBandSchema,
  rci_vs_baseline: z.number().nullable().optional(),
  rci_vs_previous: z.number().nullable().optional(),
  clinically_significant_change: z.boolean().nullable().optional(),
  safety_actions: z.array(SafetyActionSchema),
  completed_at: z.string().datetime(),
});
export type AssessmentSubmitResponse = z.infer<typeof AssessmentSubmitResponseSchema>;

export const DueAssessmentSchema = z.object({
  instrument_id: AssessmentKindSchema,
  version: z.string(),
  due_reason: z.enum(['scheduled', 'clinician_requested', 'triggered_by_state']),
  due_at: z.string().datetime(),
});
export type DueAssessment = z.infer<typeof DueAssessmentSchema>;

export const DueAssessmentsResponseSchema = z.object({
  due: z.array(DueAssessmentSchema),
});
export type DueAssessmentsResponse = z.infer<typeof DueAssessmentsResponseSchema>;
