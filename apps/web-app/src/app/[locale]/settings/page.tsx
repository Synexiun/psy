'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';

const APP_VERSION = '1.0.0-beta';

// ---------------------------------------------------------------------------
// Shared atoms
// ---------------------------------------------------------------------------

function ChevronRight(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4 shrink-0 text-ink-quaternary"
      aria-hidden="true"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

interface NavRowProps {
  label: string;
  description?: string;
  href: string;
}

function NavRow({ label, description, href }: NavRowProps): React.ReactElement {
  const router = useRouter();
  return (
    <button
      type="button"
      onClick={() => router.push(href)}
      className="flex w-full items-center justify-between gap-4 px-5 py-4 text-start hover:bg-surface-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-inset"
    >
      <div className="min-w-0">
        <p className="text-sm font-medium text-ink-primary">{label}</p>
        {description !== undefined && (
          <p className="mt-0.5 text-xs text-ink-tertiary leading-snug">{description}</p>
        )}
      </div>
      <ChevronRight />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Settings section wrapper
// ---------------------------------------------------------------------------

function Section({ title, children }: { title: string; children: React.ReactNode }): React.ReactElement {
  const id = `section-${title.toLowerCase().replace(/\s+/g, '-')}`;
  return (
    <section aria-labelledby={id}>
      <h2
        id={id}
        className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
      >
        {title}
      </h2>
      <Card className="divide-y divide-border-subtle p-0 overflow-hidden">
        {children}
      </Card>
    </section>
  );
}

function SettingsRow({ children }: { children: React.ReactNode }): React.ReactElement {
  return <div className="px-5 py-4">{children}</div>;
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function SettingsInner({ locale }: { locale: string }): React.ReactElement {
  const t = useTranslations();

  return (
    <Layout locale={locale}>
      <div className="space-y-8">
        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('nav.settings')}
          </h1>
        </header>

        {/* Navigation rows */}
        <Section title={t('nav.settings')}>
          <NavRow
            href={`/${locale}/settings/account`}
            label={t('settings.sections.account.title')}
          />
          <NavRow
            href={`/${locale}/settings/notifications`}
            label={t('settings.sections.notifications.title')}
          />
          <NavRow
            href={`/${locale}/settings/appearance`}
            label={t('settings.sections.appearance.title')}
          />
          <NavRow
            href={`/${locale}/settings/privacy`}
            label={t('settings.sections.privacy.title')}
          />
        </Section>

        {/* About section — stays inline (static content) */}
        <Section title={t('settings.sections.about.title')}>
          <SettingsRow>
            <div className="flex items-center justify-between">
              <span className="text-sm text-ink-secondary">{t('settings.sections.about.version')}</span>
              {/* Latin digits for version numbers */}
              <span className="text-sm font-mono text-ink-quaternary tabular-nums">{APP_VERSION}</span>
            </div>
          </SettingsRow>
          <SettingsRow>
            <a
              href={`/${locale}/privacy`}
              className="block text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 min-h-[44px] flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
            >
              {t('settings.sections.about.privacyPolicy')}
            </a>
          </SettingsRow>
          <SettingsRow>
            <a
              href={`/${locale}/terms`}
              className="block text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 min-h-[44px] flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
            >
              {t('settings.sections.about.terms')}
            </a>
          </SettingsRow>
        </Section>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function SettingsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <SettingsInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.settings
 *   settings.sections.account.title
 *   settings.sections.notifications.title
 *   settings.sections.appearance.title
 *   settings.sections.privacy.title
 *   settings.sections.about.title / .version / .privacyPolicy / .terms
 */
