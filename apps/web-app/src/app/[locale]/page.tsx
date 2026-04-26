'use client';

import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { StreakWidget } from '@/components/StreakWidget';
import { PatternCard } from '@/components/PatternCard';
import { QuickActions } from '@/components/QuickActions';
import { StateIndicator } from '@/components/StateIndicator';
import { MoodSparkline } from '@/components/MoodSparkline';
import { useStreak, usePatterns, useStateEstimate, useCheckInHistory } from '@/hooks/useDashboardData';

export default function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <DashboardInner locale={locale} />;
}

function DashboardInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const streak = useStreak();
  const patterns = usePatterns();
  const state = useStateEstimate();
  const checkInHistory = useCheckInHistory();

  const isLoading = streak.isLoading || patterns.isLoading || state.isLoading || checkInHistory.isLoading;

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
              {t('app.welcome.title')}
            </h1>
            <p className="mt-1 text-sm text-ink-tertiary">{t('app.welcome.body')}</p>
          </div>
          <a
            href={`/${locale}/crisis`}
            className="hidden items-center gap-2 rounded-lg bg-signal-crisis px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-signal-crisis/90 active:bg-signal-crisis/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30 lg:inline-flex"
          >
            <span aria-hidden="true">🚨</span>
            {t('crisis.cta.primary')}
          </a>
        </header>

        <QuickActions locale={locale} />

        <section aria-labelledby="state-heading">
          <h2 id="state-heading" className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary">
            {t('common.state.online')}
          </h2>
          <StateIndicator data={state.data} isLoading={state.isLoading} />
        </section>

        <section aria-labelledby="streak-heading">
          <h2 id="streak-heading" className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary">
            Streaks
          </h2>
          <StreakWidget data={streak.data} isLoading={streak.isLoading} />
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="lg:col-span-2" aria-labelledby="patterns-heading">
            <h2 id="patterns-heading" className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary">
              Insights
            </h2>
            <div className="space-y-3">
              {patterns.isLoading && (
                <>
                  <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
                    <div className="h-4 w-20 rounded bg-surface-tertiary animate-pulse" />
                    <div className="mt-3 h-4 w-3/4 rounded bg-surface-tertiary animate-pulse" />
                  </div>
                  <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
                    <div className="h-4 w-20 rounded bg-surface-tertiary animate-pulse" />
                    <div className="mt-3 h-4 w-3/4 rounded bg-surface-tertiary animate-pulse" />
                  </div>
                </>
              )}
              {patterns.data?.map((pattern) => (
                <PatternCard key={pattern.pattern_id} pattern={pattern} />
              ))}
              {!patterns.isLoading && patterns.data?.length === 0 && (
                <p className="py-8 text-center text-sm text-ink-quaternary">
                  No patterns detected yet. Keep checking in — insights appear with more data.
                </p>
              )}
            </div>
          </section>

          <aside aria-label="Dashboard sidebar" className="space-y-6">
            <MoodSparkline data={checkInHistory.data} isLoading={isLoading} />

            <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
              <p className="text-sm font-medium text-ink-primary">Daily tip</p>
              <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                When an urge rises, wait 60 seconds before acting. Urges peak and fall like waves —
                most pass within 3–5 minutes.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </Layout>
  );
}
