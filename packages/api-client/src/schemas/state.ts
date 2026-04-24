/**
 * State estimate schemas — mirrors `GET /v1/today` and state estimate fields.
 * Shape is authoritative in Docs/Technicals/03_API_Specification.md §9.2.
 *
 * State labels map to the T0–T4 tier system described in
 * Docs/Whitepapers/04_Safety_Framework.md.
 */

import { z } from 'zod';

export const StateLabelSchema = z.enum([
  'stable',
  'baseline',
  'elevated',
  'rising_urge',
  'peak_urge',
  'post_urge',
]);
export type StateLabel = z.infer<typeof StateLabelSchema>;

export const RiskWindowSchema = z.object({
  start: z.string().datetime(),
  end: z.string().datetime(),
  kind: z.enum(['predicted_urge', 'historical_peak', 'contextual_risk']),
});
export type RiskWindow = z.infer<typeof RiskWindowSchema>;

export const TodaySummarySchema = z.object({
  current_state: StateLabelSchema,
  state_confidence: z.number().min(0).max(1),
  risk_windows_today: z.array(RiskWindowSchema),
  check_in_due: z.boolean(),
  open_interventions: z.array(z.unknown()),
});
export type TodaySummary = z.infer<typeof TodaySummarySchema>;

/** Minimal state estimate shape posted to `POST /v1/state/estimate`. */
export const StateEstimateUploadSchema = z.object({
  ts: z.string().datetime(),
  state_label: StateLabelSchema,
  confidence: z.number().min(0).max(1),
  feature_hash: z.string(),
  model_version: z.string(),
});
export type StateEstimateUpload = z.infer<typeof StateEstimateUploadSchema>;
