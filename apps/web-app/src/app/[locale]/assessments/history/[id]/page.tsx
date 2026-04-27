'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';
import { usePhiAudit } from '@/hooks/usePhiAudit';

interface AssessmentHistoryDetail {
  id: string;
  instrument: string;
  completedAt: string;
  score: number;
  maxScore: number;
  severity: string;
  band: string;
}

function formatHistoryDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function AssessmentHistoryInner({ locale, sessionId }: { locale: string; sessionId: string }) {
  usePhiAudit('/assessments/history/[id]');
  const t = useTranslations();
  const router = useRouter();

  const entry: AssessmentHistoryDetail = {
    id: sessionId,
    instrument: 'PHQ-9',
    completedAt: new Date().toISOString(),
    score: 8,
    maxScore: 27,
    severity: 'Mild',
    band: '5–9',
  };

  return (
    <Layout locale={locale}>
      <div className="space-y-6 max-w-2xl mx-auto">
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => { router.push(`/${locale}/assessments`); }}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
              <path d="M19 12H5M12 5l-7 7 7 7"/>
            </svg>
            {t('nav.assessments')}
          </button>
        </nav>

        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {entry.instrument}
          </h1>
          <time
            dateTime={entry.completedAt}
            className="mt-1 block text-sm text-ink-tertiary"
          >
            {formatHistoryDate(entry.completedAt)}
          </time>
        </header>

        <Card>
          <div className="space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-ink-tertiary">Score</span>
              <span className="rounded-full bg-surface-tertiary px-3 py-0.5 text-sm font-semibold text-ink-primary">
                {entry.severity}
              </span>
            </div>
            <p className="text-3xl font-bold tabular-nums text-ink-primary">
              <span className="clinical-number tabular-nums">{entry.score}/{entry.maxScore}</span>
            </p>
            <p className="text-xs text-ink-quaternary">
              Severity band: {entry.band}
            </p>
          </div>
        </Card>

        <footer className="pt-2 text-center">
          <a
            href={`/${locale}/crisis`}
            className="text-xs text-ink-quaternary hover:text-signal-crisis transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30 rounded"
          >
            {t('checkIn.needHelp')}
          </a>
        </footer>
      </div>
    </Layout>
  );
}

export default function AssessmentHistoryPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): React.JSX.Element {
  const { locale, id } = use(params);
  return <AssessmentHistoryInner locale={locale} sessionId={id} />;
}
