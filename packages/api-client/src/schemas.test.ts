import { describe, it, expect } from 'vitest';
import {
  LocaleSchema,
  AssessmentKindSchema,
  UserProfileSchema,
  AssessmentScoreSchema,
  UrgeDialSchema,
  StreakSchema,
} from './schemas';

describe('LocaleSchema', () => {
  it('accepts supported locales', () => {
    expect(LocaleSchema.safeParse('en').success).toBe(true);
    expect(LocaleSchema.safeParse('fr').success).toBe(true);
    expect(LocaleSchema.safeParse('ar').success).toBe(true);
    expect(LocaleSchema.safeParse('fa').success).toBe(true);
  });

  it('rejects unsupported locales', () => {
    expect(LocaleSchema.safeParse('de').success).toBe(false);
    expect(LocaleSchema.safeParse('').success).toBe(false);
  });
});

describe('AssessmentKindSchema', () => {
  it('accepts phq9', () => {
    expect(AssessmentKindSchema.safeParse('phq9').success).toBe(true);
  });

  it('rejects unknown kind', () => {
    expect(AssessmentKindSchema.safeParse('unknown').success).toBe(false);
  });
});

describe('UserProfileSchema', () => {
  it('accepts a valid profile', () => {
    const result = UserProfileSchema.safeParse({
      id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      email: 'user@example.com',
      displayName: 'Alex',
      locale: 'en',
      createdAt: '2024-01-01T00:00:00Z',
    });
    expect(result.success).toBe(true);
  });

  it('rejects invalid uuid', () => {
    const result = UserProfileSchema.safeParse({
      id: 'not-a-uuid',
      email: 'user@example.com',
      displayName: null,
      locale: 'en',
      createdAt: '2024-01-01T00:00:00Z',
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AssessmentScoreSchema
// ---------------------------------------------------------------------------

describe('AssessmentScoreSchema', () => {
  it('accepts a valid score with all fields', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'phq9',
      takenAt: '2026-04-25T00:00:00Z',
      total: 14,
      severity: 'moderate',
      item9Flag: false,
      rawItems: [0, 1, 2, 3, 2, 1, 2, 3, 0],
    });
    expect(result.success).toBe(true);
  });

  it('accepts score with null severity', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'who5',
      takenAt: '2026-04-25T00:00:00Z',
      total: 60,
      severity: null,
    });
    expect(result.success).toBe(true);
  });

  it('accepts score without optional fields', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'gad7',
      takenAt: '2026-04-25T00:00:00Z',
      total: 7,
      severity: 'mild',
    });
    expect(result.success).toBe(true);
  });

  it('rejects negative total', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'phq9',
      takenAt: '2026-04-25T00:00:00Z',
      total: -1,
      severity: null,
    });
    expect(result.success).toBe(false);
  });

  it('rejects unknown severity band', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'phq9',
      takenAt: '2026-04-25T00:00:00Z',
      total: 14,
      severity: 'catastrophic',
    });
    expect(result.success).toBe(false);
  });

  it('rejects unknown kind', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'imaginary_scale',
      takenAt: '2026-04-25T00:00:00Z',
      total: 0,
      severity: null,
    });
    expect(result.success).toBe(false);
  });

  it('accepts item9Flag as boolean', () => {
    const result = AssessmentScoreSchema.safeParse({
      kind: 'phq9',
      takenAt: '2026-04-25T00:00:00Z',
      total: 2,
      severity: 'none',
      item9Flag: true,
    });
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// UrgeDialSchema
// ---------------------------------------------------------------------------

describe('UrgeDialSchema', () => {
  it('accepts a valid urge dial entry', () => {
    const result = UrgeDialSchema.safeParse({
      id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      loggedAt: '2026-04-25T10:30:00Z',
      intensity: 7,
      context: 'felt stressed at work',
      triggerTags: ['stress', 'fatigue'],
    });
    expect(result.success).toBe(true);
  });

  it('accepts null context', () => {
    const result = UrgeDialSchema.safeParse({
      id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      loggedAt: '2026-04-25T10:30:00Z',
      intensity: 3,
      context: null,
      triggerTags: [],
    });
    expect(result.success).toBe(true);
  });

  it('rejects intensity above 10', () => {
    const result = UrgeDialSchema.safeParse({
      id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      loggedAt: '2026-04-25T10:30:00Z',
      intensity: 11,
      context: null,
      triggerTags: [],
    });
    expect(result.success).toBe(false);
  });

  it('rejects intensity below 0', () => {
    const result = UrgeDialSchema.safeParse({
      id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      loggedAt: '2026-04-25T10:30:00Z',
      intensity: -1,
      context: null,
      triggerTags: [],
    });
    expect(result.success).toBe(false);
  });

  it('rejects invalid uuid', () => {
    const result = UrgeDialSchema.safeParse({
      id: 'not-a-uuid',
      loggedAt: '2026-04-25T10:30:00Z',
      intensity: 5,
      context: null,
      triggerTags: [],
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// StreakSchema
// ---------------------------------------------------------------------------

describe('StreakSchema', () => {
  it('accepts a valid streak', () => {
    const result = StreakSchema.safeParse({
      daysClean: 12,
      urgesHandled: 47,
      lastUrgeAt: '2026-04-20T08:00:00Z',
    });
    expect(result.success).toBe(true);
  });

  it('accepts null lastUrgeAt (new user)', () => {
    const result = StreakSchema.safeParse({
      daysClean: 0,
      urgesHandled: 0,
      lastUrgeAt: null,
    });
    expect(result.success).toBe(true);
  });

  it('rejects negative daysClean', () => {
    const result = StreakSchema.safeParse({
      daysClean: -1,
      urgesHandled: 0,
      lastUrgeAt: null,
    });
    expect(result.success).toBe(false);
  });

  it('rejects negative urgesHandled', () => {
    const result = StreakSchema.safeParse({
      daysClean: 0,
      urgesHandled: -1,
      lastUrgeAt: null,
    });
    expect(result.success).toBe(false);
  });
});
