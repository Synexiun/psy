/**
 * Shared response/request schemas (Zod).
 * These mirror the server-authored OpenAPI contract in Docs/Technicals/03_API_Specification.md.
 * Keep shapes in sync with the server — breaks here catch drift at the client boundary.
 */

import { z } from 'zod';

export const LocaleSchema = z.enum(['en', 'fr', 'ar', 'fa']);
export type Locale = z.infer<typeof LocaleSchema>;

export const UserProfileSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  displayName: z.string().nullable(),
  locale: LocaleSchema,
  createdAt: z.string().datetime(),
});
export type UserProfile = z.infer<typeof UserProfileSchema>;

export const AssessmentKindSchema = z.enum([
  'phq9',
  'gad7',
  'audit',
  'audit_c',
  'dast10',
  'pss10',
  'who5',
  'dtcq8',
  'urica',
  'readiness_ruler',
  'cssrs',
  'phq2',
  'gad2',
]);
export type AssessmentKind = z.infer<typeof AssessmentKindSchema>;

export const AssessmentScoreSchema = z.object({
  kind: AssessmentKindSchema,
  takenAt: z.string().datetime(),
  total: z.number().int().nonnegative(),
  severity: z.enum(['none', 'mild', 'moderate', 'moderately_severe', 'severe']).nullable(),
  item9Flag: z.boolean().optional(),
  rawItems: z.array(z.number().int()).readonly().optional(),
});
export type AssessmentScore = z.infer<typeof AssessmentScoreSchema>;

export const UrgeDialSchema = z.object({
  id: z.string().uuid(),
  loggedAt: z.string().datetime(),
  intensity: z.number().int().min(0).max(10),
  context: z.string().nullable(),
  triggerTags: z.array(z.string()).readonly(),
});
export type UrgeDial = z.infer<typeof UrgeDialSchema>;

export const StreakSchema = z.object({
  daysClean: z.number().int().nonnegative(),
  urgesHandled: z.number().int().nonnegative(),
  lastUrgeAt: z.string().datetime().nullable(),
});
export type Streak = z.infer<typeof StreakSchema>;
