/**
 * @disciplineos/i18n-catalog — shared translation catalogs for web surfaces.
 *
 * Loading model: the English catalog is imported eagerly as the typed shape source of truth.
 * Other locales are loaded via dynamic import so the per-locale JSON is only sent to the client
 * that actually needs it (see Docs/Technicals/16_Web_Application.md §i18n).
 *
 * The `_meta.status` field on each catalog MUST be promoted from "draft" to "native-reviewed"
 * before that locale's surface goes live. CI enforces key parity against the English source.
 */

import en from './catalogs/en.json';

export type Locale = 'en' | 'fr' | 'ar' | 'fa';
export const SUPPORTED_LOCALES: ReadonlyArray<Locale> = ['en', 'fr', 'ar', 'fa'];

export const RTL_LOCALES: ReadonlySet<Locale> = new Set(['ar', 'fa']);
export const isRtl = (locale: Locale): boolean => RTL_LOCALES.has(locale);

export type Catalog = typeof en;
export type CatalogMeta = Catalog['_meta'];

export const DEFAULT_LOCALE: Locale = 'en';

const loaders: Record<Locale, () => Promise<{ default: Catalog }>> = {
  en: () => Promise.resolve({ default: en as Catalog }),
  fr: () => import('./catalogs/fr.json') as unknown as Promise<{ default: Catalog }>,
  ar: () => import('./catalogs/ar.json') as unknown as Promise<{ default: Catalog }>,
  fa: () => import('./catalogs/fa.json') as unknown as Promise<{ default: Catalog }>,
};

export const loadCatalog = async (locale: Locale): Promise<Catalog> => {
  const loader = loaders[locale];
  const mod = await loader();
  return mod.default;
};

export const getEnglishCatalog = (): Catalog => en as Catalog;

/**
 * negotiateLocale picks the best matching supported locale from an Accept-Language header
 * (or any comma-separated list of BCP 47 tags with optional q-weights).
 * Falls back to DEFAULT_LOCALE when no supported match is found.
 */
export * from './formatters';

export const negotiateLocale = (acceptLanguage: string | null | undefined): Locale => {
  if (!acceptLanguage) return DEFAULT_LOCALE;
  const candidates = acceptLanguage
    .split(',')
    .map((part) => {
      const [tagRaw, ...params] = part.trim().split(';');
      const tag = (tagRaw ?? '').toLowerCase();
      const qParam = params.find((p) => p.trim().startsWith('q='));
      const q = qParam ? Number.parseFloat(qParam.split('=')[1] ?? '1') : 1;
      return { tag, q: Number.isFinite(q) ? q : 1 };
    })
    .sort((a, b) => b.q - a.q);

  for (const { tag } of candidates) {
    const primary = tag.split('-')[0] as Locale;
    if (SUPPORTED_LOCALES.includes(primary)) return primary;
  }
  return DEFAULT_LOCALE;
};
