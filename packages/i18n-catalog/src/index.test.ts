import { describe, it, expect } from 'vitest';
import { negotiateLocale, isRtl, loadCatalog, getEnglishCatalog, DEFAULT_LOCALE, SUPPORTED_LOCALES } from './index';

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
