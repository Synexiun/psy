import { describe, it, expect } from 'vitest';
import { LocaleSchema, AssessmentKindSchema, UserProfileSchema } from './schemas';

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
