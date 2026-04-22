/**
 * Unit tests for the crisis surface locale module.
 *
 * These are pure TypeScript — no DOM, no Next.js runtime — so they run
 * under Vitest with the `node` environment and execute in milliseconds.
 */

import { describe, expect, it } from 'vitest';

import {
  COPY,
  isCrisisLocale,
  isRtl,
  SUPPORTED_LOCALES,
  type CrisisLocale,
} from '@/lib/locale';

describe('SUPPORTED_LOCALES', () => {
  it('contains exactly the four launch locales', () => {
    expect(SUPPORTED_LOCALES).toEqual(['en', 'fr', 'ar', 'fa']);
  });

  it('is frozen (read-only)', () => {
    expect(() => {
      (SUPPORTED_LOCALES as string[]).push('de');
    }).toThrow();
  });
});

describe('isCrisisLocale', () => {
  it.each(['en', 'fr', 'ar', 'fa'] as const)(
    'returns true for %s',
    (locale) => {
      expect(isCrisisLocale(locale)).toBe(true);
    },
  );

  it.each(['en-US', 'de', 'es', 'zh', ''])(
    'returns false for %s',
    (locale) => {
      expect(isCrisisLocale(locale)).toBe(false);
    },
  );
});

describe('isRtl', () => {
  it('returns true for Arabic', () => {
    expect(isRtl('ar')).toBe(true);
  });

  it('returns true for Persian', () => {
    expect(isRtl('fa')).toBe(true);
  });

  it('returns false for English', () => {
    expect(isRtl('en')).toBe(false);
  });

  it('returns false for French', () => {
    expect(isRtl('fr')).toBe(false);
  });
});

describe('COPY', () => {
  it('has an entry for every supported locale', () => {
    for (const locale of SUPPORTED_LOCALES) {
      expect(COPY[locale]).toBeDefined();
    }
  });

  it('every locale carries the same set of keys', () => {
    const enKeys = Object.keys(COPY.en).sort();
    for (const locale of SUPPORTED_LOCALES) {
      const keys = Object.keys(COPY[locale as CrisisLocale]).sort();
      expect(keys).toEqual(enKeys);
    }
  });

  it('no value is empty', () => {
    for (const locale of SUPPORTED_LOCALES) {
      const copy = COPY[locale as CrisisLocale];
      for (const [key, value] of Object.entries(copy)) {
        expect(value.length, `${locale}.${key} is empty`).toBeGreaterThan(0);
      }
    }
  });

  it('Arabic headline contains Arabic script', () => {
    expect(COPY.ar.headline).toMatch(/[\u0600-\u06FF]/);
  });

  it('Persian headline contains Persian script', () => {
    expect(COPY.fa.headline).toMatch(/[\u0600-\u06FF]/);
  });
});
