/**
 * Urge / intervention schemas — mirrors `POST /v1/urges`, `POST /v1/sos`,
 * `POST /v1/urges/{id}/resolve`, and `POST /v1/interventions/{id}/outcome`.
 * Shape is authoritative in Docs/Technicals/03_API_Specification.md §5.
 */

import { z } from 'zod';

// ---------------------------------------------------------------------------
// Urge log (T2/T3 entry)
// ---------------------------------------------------------------------------

export const UrgeLogRequestSchema = z.object({
  started_at: z.string().datetime(),
  intensity_start: z.number().int().min(0).max(10),
  trigger_tags: z.array(z.string()).max(16),
  location_context: z.string().optional(),
  origin: z.enum(['self_reported', 'sensor_triggered', 'nudge_triggered']),
});
export type UrgeLogRequest = z.infer<typeof UrgeLogRequestSchema>;

export const RecommendedToolSchema = z.object({
  tool_variant: z.string(),
  rationale: z.string(),
  bandit_arm: z.string(),
  intervention_id: z.string().uuid(),
});
export type RecommendedTool = z.infer<typeof RecommendedToolSchema>;

export const UrgeLogResponseSchema = z.object({
  urge_id: z.string().uuid(),
  recommended_tool: RecommendedToolSchema,
});
export type UrgeLogResponse = z.infer<typeof UrgeLogResponseSchema>;

// ---------------------------------------------------------------------------
// SOS (T3 crisis)
// ---------------------------------------------------------------------------

export const SosRequestSchema = z.object({
  started_at: z.string().datetime(),
});
export type SosRequest = z.infer<typeof SosRequestSchema>;

export const SosSupportContactSchema = z.object({
  name: z.string(),
  phone: z.string(),
});

export const SosResponseSchema = z.object({
  urge_id: z.string().uuid(),
  intervention_id: z.string().uuid(),
  payload: z.object({
    ui_template: z.string(),
    tools_hardcoded: z.array(z.string()),
    support_contact: SosSupportContactSchema.nullable().optional(),
    local_hotline: z.string().nullable().optional(),
  }),
});
export type SosResponse = z.infer<typeof SosResponseSchema>;

// ---------------------------------------------------------------------------
// Resolve urge
// ---------------------------------------------------------------------------

export const UrgeResolveRequestSchema = z.object({
  intensity_peak: z.number().int().min(0).max(10),
  intensity_end: z.number().int().min(0).max(10),
  handled: z.boolean(),
  note: z.string().max(2000).optional(),
});
export type UrgeResolveRequest = z.infer<typeof UrgeResolveRequestSchema>;

// ---------------------------------------------------------------------------
// Intervention outcome
// ---------------------------------------------------------------------------

export const InterventionOutcomeRequestSchema = z.object({
  outcome_type: z.enum(['handled', 'partial', 'relapsed', 'skipped']),
  post_state_label: z.string().optional(),
  user_note: z.string().max(2000).optional(),
});
export type InterventionOutcomeRequest = z.infer<typeof InterventionOutcomeRequestSchema>;

export const InterventionOutcomeResponseSchema = z.object({
  outcome_id: z.string().uuid(),
});
export type InterventionOutcomeResponse = z.infer<typeof InterventionOutcomeResponseSchema>;

// ---------------------------------------------------------------------------
// Nudge acknowledgement
// ---------------------------------------------------------------------------

export const NudgeAckSchema = z.enum(['accepted', 'snoozed', 'dismissed']);
export type NudgeAck = z.infer<typeof NudgeAckSchema>;

export const NudgeAckRequestSchema = z.object({
  ack: NudgeAckSchema,
});
export type NudgeAckRequest = z.infer<typeof NudgeAckRequestSchema>;
