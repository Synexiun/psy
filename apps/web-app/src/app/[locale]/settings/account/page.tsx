'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useUser } from '@clerk/nextjs';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function AccountInner({ locale }: { locale: string }): React.ReactElement {
  const t = useTranslations();
  const { user } = useUser();
  const router = useRouter();

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
            {t('settings.sections.account.title')}
          </h1>
        </header>

        {/* Account info */}
        <Card className="divide-y divide-border-subtle p-0 overflow-hidden">
          <div className="px-5 py-4">
            <p className="text-xs font-medium text-ink-quaternary uppercase tracking-wide mb-1">
              {t('settings.sections.account.displayName')}
            </p>
            <p className="text-sm font-medium text-ink-primary">
              {user?.fullName ?? user?.firstName ?? '—'}
            </p>
          </div>
          <div className="px-5 py-4">
            <p className="text-xs font-medium text-ink-quaternary uppercase tracking-wide mb-1">
              {t('settings.sections.account.email')}
            </p>
            <p className="text-sm text-ink-primary">
              {user?.primaryEmailAddress?.emailAddress ?? '—'}
            </p>
            <p className="mt-0.5 text-xs text-ink-quaternary">
              {t('settings.sections.account.emailReadOnly')}
            </p>
          </div>
          <div className="px-5 py-4">
            <a
              href="https://accounts.discipline.app/user"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded min-h-[44px] transition-colors"
            >
              {t('settings.sections.account.manageAccount')}
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
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </a>
          </div>
        </Card>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function AccountPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <AccountInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.settings
 *   settings.sections.account.title / .displayName / .email / .emailReadOnly / .manageAccount
 */
