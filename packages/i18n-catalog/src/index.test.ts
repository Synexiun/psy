import { describe, it, expect } from 'vitest';
import {
  negotiateLocale,
  isRtl,
  loadCatalog,
  getEnglishCatalog,
  DEFAULT_LOCALE,
  SUPPORTED_LOCALES,
  formatNumberClinical,
  formatScoreWithMax,
  formatPercentClinical,
  formatRciDelta,
} from './index';

describe('i18n-catalog', () => {
  it('has correct default and supported locales', () => {
    expect(DEFAULT_LOCALE).toBe('en');
    expect(SUPPORTED_LOCALES).toEqual(['en', 'fr', 'ar', 'fa']);
  });

  it('identifies RTL locales', () => {
    expect(isRtl('ar')).toBe(true);
    expect(isRtl('fa')).toBe(true);
    expect(isRtl('en')).toBe(false);
    expect(isRtl('fr')).toBe(false);
  });

  it('negotiateLocale picks exact match', () => {
    expect(negotiateLocale('fr-FR, fr;q=0.9, en;q=0.8')).toBe('fr');
  });

  it('negotiateLocale falls back to primary language tag', () => {
    expect(negotiateLocale('ar-SA')).toBe('ar');
  });

  it('negotiateLocale falls back to default for unsupported', () => {
    expect(negotiateLocale('de-DE')).toBe('en');
  });

  it('negotiateLocale handles null/undefined', () => {
    expect(negotiateLocale(null)).toBe('en');
    expect(negotiateLocale(undefined)).toBe('en');
  });

  it('negotiateLocale respects q-weight ordering', () => {
    expect(negotiateLocale('de;q=0.9, fr;q=0.8, en;q=0.7')).toBe('fr');
    expect(negotiateLocale('de;q=0.9, es;q=0.8, en;q=0.7')).toBe('en');
  });

  it('loads English catalog synchronously', async () => {
    const catalog = await loadCatalog('en');
    expect(catalog._meta.locale).toBe('en');
    expect(catalog.app.name).toBe('Discipline OS');
  });

  it('getEnglishCatalog returns en catalog', () => {
    const catalog = getEnglishCatalog();
    expect(catalog._meta.locale).toBe('en');
  });
});

// ---------------------------------------------------------------------------
// formatNumberClinical — CLAUDE.md Rule #9: always Latin digits
// ---------------------------------------------------------------------------

describe('formatNumberClinical', () => {
  it('formats integer 0 as "0"', () => {
    expect(formatNumberClinical(0)).toBe('0');
  });

  it('formats PHQ-9 max score (27) as "27"', () => {
    expect(formatNumberClinical(27)).toBe('27');
  });

  it('formats GAD-7 max score (21) as "21"', () => {
    expect(formatNumberClinical(21)).toBe('21');
  });

  it('output is ASCII-only (no Arabic-Indic or Persian digits)', () => {
    for (const n of [0, 1, 9, 14, 27, 100]) {
      const result = formatNumberClinical(n);
      for (const ch of result) {
        expect(ch.charCodeAt(0)).toBeLessThan(128);
      }
    }
  });

  it('does not include thousands separator for large numbers', () => {
    expect(formatNumberClinical(1000)).toBe('1000');
  });
});

// ---------------------------------------------------------------------------
// formatScoreWithMax
// ---------------------------------------------------------------------------

describe('formatScoreWithMax', () => {
  it('formats "score/max" pattern', () => {
    expect(formatScoreWithMax(8, 27)).toBe('8/27');
  });

  it('handles zero score', () => {
    expect(formatScoreWithMax(0, 21)).toBe('0/21');
  });

  it('handles score equal to max', () => {
    expect(formatScoreWithMax(27, 27)).toBe('27/27');
  });

  it('output is ASCII-only', () => {
    const result = formatScoreWithMax(14, 27);
    for (const ch of result) {
      expect(ch.charCodeAt(0)).toBeLessThan(128);
    }
  });
});

// ---------------------------------------------------------------------------
// formatPercentClinical — CLAUDE.md Rule #9: always Latin digits
// ---------------------------------------------------------------------------

describe('formatPercentClinical', () => {
  it('formats 0% as "0%"', () => {
    expect(formatPercentClinical(0)).toBe('0%');
  });

  it('formats 100% as "100%"', () => {
    expect(formatPercentClinical(100)).toBe('100%');
  });

  it('rounds to 0 decimals by default', () => {
    expect(formatPercentClinical(72.4)).toBe('72%');
    expect(formatPercentClinical(72.6)).toBe('73%');
  });

  it('respects decimals argument', () => {
    expect(formatPercentClinical(72.345, 1)).toBe('72.3%');
  });

  it('output is ASCII-only (no non-Latin digits)', () => {
    const result = formatPercentClinical(85);
    for (const ch of result) {
      expect(ch.charCodeAt(0)).toBeLessThan(128);
    }
  });

  it('always appends percent sign', () => {
    expect(formatPercentClinical(50)).toMatch(/%$/);
  });
});

// ---------------------------------------------------------------------------
// formatRciDelta — always show sign, always Latin digits
// ---------------------------------------------------------------------------

describe('formatRciDelta', () => {
  it('positive delta gets leading "+"', () => {
    expect(formatRciDelta(2.5)).toBe('+2.5');
  });

  it('negative delta keeps "-"', () => {
    expect(formatRciDelta(-3.2)).toBe('-3.2');
  });

  it('zero delta gets leading "+"', () => {
    expect(formatRciDelta(0)).toBe('+0.0');
  });

  it('respects decimals argument', () => {
    expect(formatRciDelta(1.567, 2)).toBe('+1.57');
  });

  it('output is ASCII-only', () => {
    for (const delta of [-5.0, 0, 1.2, 10.5]) {
      const result = formatRciDelta(delta);
      for (const ch of result) {
        expect(ch.charCodeAt(0)).toBeLessThan(128);
      }
    }
  });
});
