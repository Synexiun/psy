/**
 * Unit tests for web-marketing i18n concerns.
 *
 * These validate the routing table and locale negotiation without
 * spinning up a Next.js runtime.
 */

import { describe, expect, it } from 'vitest';

import { routing } from '@/i18n/routing';

describe('routing', () => {
  it('exports the four launch locales', () => {
    expect(routing.locales).toEqual(['en', 'fr', 'ar', 'fa']);
  });

  it('default locale is en', () => {
    expect(routing.defaultLocale).toBe('en');
  });

  it('locale prefix strategy is as-needed', () => {
    expect((routing as Record<string, unknown>).localePrefix).toBe('as-needed');
  });
});
