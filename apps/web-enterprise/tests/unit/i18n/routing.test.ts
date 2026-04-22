import { describe, expect, it } from 'vitest';
import { routing } from '@/i18n/routing';

describe('i18n routing', () => {
  it('has four supported locales', () => {
    expect(routing.locales).toHaveLength(4);
    expect(routing.locales).toContain('en');
    expect(routing.locales).toContain('fr');
    expect(routing.locales).toContain('ar');
    expect(routing.locales).toContain('fa');
  });

  it('defaults to en', () => {
    expect(routing.defaultLocale).toBe('en');
  });
});
