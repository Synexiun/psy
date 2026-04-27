'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';

// ---------------------------------------------------------------------------
// Locale options
// ---------------------------------------------------------------------------

const LOCALE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Français' },
  { value: 'ar', label: 'العربية' },
  { value: 'fa', label: 'فارسی' },
] as const;

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function MoonIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4 shrink-0"
      aria-hidden="true"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function SunIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4 shrink-0"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function AppearanceInner({ locale }: { locale: string }): React.ReactElement {
  const t = useTranslations();
  const router = useRouter();
  // usePathname from next/navigation returns the full path including locale prefix.
  // Strip the leading /<locale> segment so we can reconstruct with the new locale.
  const rawPathname = usePathname() ?? '';
  const { theme, setTheme } = useTheme();

  // Default theme is dark; treat undefined as dark
  const isDark = theme !== 'light';

  function handleLocaleChange(newLocale: string): void {
    // Strip existing locale prefix (e.g. /en/settings/appearance -> /settings/appearance)
    const pathnameWithoutLocale = rawPathname.replace(/^\/[a-z]{2}(\/|$)/, '/');
    router.push(`/${newLocale}${pathnameWithoutLocale === '/' ? '' : pathnameWithoutLocale}`);
  }

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => router.push(`/${locale}/settings`)}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded min-h-[44px] transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.75}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
              aria-hidden="true"
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
            {t('nav.settings')}
          </button>
        </nav>

        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('settings.sections.appearance.title')}
          </h1>
        </header>

        {/* Theme section */}
        <section aria-labelledby="theme-section-heading">
          <h2
            id="theme-section-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('settings.sections.appearance.theme')}
          </h2>
          <Card className="p-4">
            <p className="text-xs text-ink-tertiary mb-3">
              {t('settings.sections.appearance.themeDescription')}
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                aria-pressed={isDark}
                onClick={() => setTheme('dark')}
                data-testid="theme-dark-btn"
                className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 min-h-[44px] ${
                  isDark
                    ? 'border-accent-bronze bg-accent-bronze/10 text-accent-bronze'
                    : 'border-border-subtle bg-transparent text-ink-secondary hover:bg-surface-tertiary'
                }`}
              >
                <MoonIcon />
                {t('settings.sections.appearance.themeDark')}
              </button>
              <button
                type="button"
                aria-pressed={!isDark}
                onClick={() => setTheme('light')}
                data-testid="theme-light-btn"
                className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 min-h-[44px] ${
                  !isDark
                    ? 'border-accent-bronze bg-accent-bronze/10 text-accent-bronze'
                    : 'border-border-subtle bg-transparent text-ink-secondary hover:bg-surface-tertiary'
                }`}
              >
                <SunIcon />
                {t('settings.sections.appearance.themeLight')}
              </button>
            </div>
          </Card>
        </section>

        {/* Language section */}
        <section aria-labelledby="language-section-heading">
          <h2
            id="language-section-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('settings.sections.appearance.language')}
          </h2>
          <Card className="divide-y divide-border-subtle p-0 overflow-hidden">
            <p className="px-4 pt-3 pb-1 text-xs text-ink-tertiary">
              {t('settings.sections.appearance.languageDescription')}
            </p>
            {LOCALE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                aria-pressed={locale === opt.value}
                onClick={() => handleLocaleChange(opt.value)}
                data-testid={`locale-${opt.value}-btn`}
                className={`flex w-full items-center justify-between px-4 py-3 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-inset min-h-[44px] ${
                  locale === opt.value
                    ? 'bg-accent-bronze/10 text-accent-bronze font-medium'
                    : 'text-ink-secondary hover:bg-surface-tertiary'
                }`}
              >
                <span>{opt.label}</span>
                {locale === opt.value && (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-4 w-4 shrink-0"
                    aria-hidden="true"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            ))}
          </Card>
        </section>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function AppearancePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <AppearanceInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.settings
 *   settings.sections.appearance.title / .theme / .themeDescription
 *   settings.sections.appearance.themeDark / .themeLight
 *   settings.sections.appearance.language / .languageDescription
 */
