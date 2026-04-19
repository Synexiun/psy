/**
 * @disciplineos/safety-directory
 *
 * Hotline directory. Shipped with every surface so the crisis path works offline
 * and at the "static crisis bundle" deployment target (see web-crisis app).
 *
 * Invariants (enforced in CI, not at runtime):
 *   - every entry must have at least one hotline OR a local emergency number.
 *   - every hotline must have either a `number` or an `sms`.
 *   - `verifiedAt` must be within `_meta.reviewWindowDays` at launch.
 */

import data from './hotlines.json';

export type Locale = 'en' | 'fr' | 'ar' | 'fa';

export interface HotlineEntry {
  id: string;
  name: string;
  number: string | null;
  sms: string | null;
  web: string | null;
  hours: string;
  cost: 'free' | string;
  verifiedAt: string;
}

export interface EmergencyNumber {
  label: string;
  number: string;
}

export interface CountryHotlines {
  country: string;
  locale: Locale;
  emergency: EmergencyNumber;
  hotlines: ReadonlyArray<HotlineEntry>;
}

export interface SafetyDirectoryMeta {
  schemaVersion: string;
  lastReviewedAt: string;
  reviewWindowDays: number;
  reviewedBy: string;
  note: string;
}

interface RawDirectory {
  _meta: SafetyDirectoryMeta;
  entries: ReadonlyArray<CountryHotlines>;
}

const directory = data as RawDirectory;

export const safetyDirectoryMeta: SafetyDirectoryMeta = directory._meta;
export const allEntries: ReadonlyArray<CountryHotlines> = directory.entries;

export const getEntry = (
  country: string,
  locale: Locale,
): CountryHotlines | undefined =>
  directory.entries.find(
    (e) => e.country.toUpperCase() === country.toUpperCase() && e.locale === locale,
  );

/**
 * Pick the best directory entry for a (country, locale) pair, falling back to:
 *   1. same country, English
 *   2. first entry for the country (any locale)
 *   3. US/en as global fallback
 */
export const resolveEntry = (
  country: string | null | undefined,
  locale: Locale,
): CountryHotlines => {
  if (country) {
    const exact = getEntry(country, locale);
    if (exact) return exact;
    const englishFallback = getEntry(country, 'en');
    if (englishFallback) return englishFallback;
    const anyLocale = directory.entries.find(
      (e) => e.country.toUpperCase() === country.toUpperCase(),
    );
    if (anyLocale) return anyLocale;
  }
  const usEn = getEntry('US', 'en');
  if (!usEn) throw new Error('safety-directory: US/en fallback missing — directory is broken');
  return usEn;
};

export const isStale = (entry: CountryHotlines, now: Date = new Date()): boolean => {
  const windowMs = directory._meta.reviewWindowDays * 24 * 60 * 60 * 1000;
  return entry.hotlines.some((h) => {
    const verified = new Date(h.verifiedAt).getTime();
    return now.getTime() - verified > windowMs;
  });
};
