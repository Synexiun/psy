/**
 * Streak schemas — mirrors `GET /v1/streak` response.
 * Shape is authoritative in Docs/Technicals/03_API_Specification.md §9.1.
 *
 * Rule: `resilience_days` is monotonically non-decreasing (DB trigger enforces
 * this server-side; validated as nonnegative here). See CLAUDE.md non-negotiable #3.
 */

import { z } from 'zod';

export const StreakStateSchema = z.object({
  continuous_days: z.number().int().nonnegative(),
  continuous_streak_start: z.string().datetime().nullable(),
  resilience_days: z.number().int().nonnegative(),
  resilience_urges_handled_total: z.number().int().nonnegative(),
  resilience_streak_start: z.string().datetime(),
});
export type StreakState = z.infer<typeof StreakStateSchema>;
