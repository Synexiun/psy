'use client';

import * as React from 'react';
import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';

// ---------------------------------------------------------------------------
// Toggle component
// ---------------------------------------------------------------------------

interface ToggleProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
}

function Toggle({ id, checked, onChange, label, description }: ToggleProps): React.ReactElement {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div className="min-w-0">
        <label htmlFor={id} className="block text-sm font-medium text-ink-primary cursor-pointer">
          {label}
        </label>
        {description !== undefined && (
          <p className="mt-0.5 text-xs text-ink-tertiary leading-snug">{description}</p>
        )}
      </div>
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 min-h-[44px] min-w-[44px] justify-center ${
          checked ? 'bg-accent-bronze' : 'bg-border-emphasis'
        }`}
        aria-label={label}
      >
        <span
          className={`pointer-events-none h-5 w-5 rounded-full bg-white shadow-sm ring-0 transition-transform duration-base ${
            checked ? 'translate-x-2.5' : '-translate-x-2.5'
          }`}
        />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function NotificationsInner({ locale }: { locale: string }): React.ReactElement {
  const t = useTranslations();
  const router = useRouter();

  const [pushEnabled, setPushEnabled] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(true);

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
            {t('settings.sections.notifications.title')}
          </h1>
        </header>

        {/* Notification toggles — API wiring deferred to Phase 5 Task 7.5 */}
        <Card className="divide-y divide-border-subtle p-0 overflow-hidden">
          <div className="px-5">
            <Toggle
              id="toggle-push"
              checked={pushEnabled}
              onChange={setPushEnabled}
              label={t('settings.sections.notifications.pushNotifications')}
              description={t('settings.sections.notifications.pushDescription')}
            />
          </div>
          <div className="px-5">
            <Toggle
              id="toggle-email"
              checked={emailEnabled}
              onChange={setEmailEnabled}
              label={t('settings.sections.notifications.weeklyInsights')}
              description={t('settings.sections.notifications.emailDescription')}
            />
          </div>
        </Card>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function NotificationsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <NotificationsInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.settings
 *   settings.sections.notifications.title / .pushNotifications / .pushDescription
 *   settings.sections.notifications.weeklyInsights / .emailDescription
 */
