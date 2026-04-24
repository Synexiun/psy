/**
 * Pattern schemas — mirrors `GET /v1/patterns` and `POST /v1/patterns/{id}/dismiss`.
 * Shape is authoritative in Docs/Technicals/03_API_Specification.md §8.
 */

import { z } from 'zod';

export const PatternKindSchema = z.enum([
  'temporal',
  'contextual',
  'physiological',
  'compound',
]);
export type PatternKind = z.infer<typeof PatternKindSchema>;

export const PatternSchema = z.object({
  id: z.string().uuid(),
  kind: PatternKindSchema,
  summary: z.string(),
  confidence: z.number().min(0).max(1),
  actionable: z.boolean(),
  suggested_action: z.string().nullable().optional(),
});
export type Pattern = z.infer<typeof PatternSchema>;

export const PatternListResponseSchema = z.object({
  patterns: z.array(PatternSchema),
});
export type PatternListResponse = z.infer<typeof PatternListResponseSchema>;

export const DismissReasonSchema = z.enum(['not_useful', 'false_pattern', 'not_now']);
export type DismissReason = z.infer<typeof DismissReasonSchema>;

export const PatternDismissRequestSchema = z.object({
  reason: DismissReasonSchema,
});
export type PatternDismissRequest = z.infer<typeof PatternDismissRequestSchema>;
