'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card, Badge } from '@disciplineos/design-system';
import { InsightCard } from '@disciplineos/design-system';
import { usePhiAudit } from '@/hooks/usePhiAudit';
import { usePatterns } from '@/hooks/usePatterns';
import { formatPercentClinical } from '@disciplineos/i18n-catalog';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Tone map for pattern types — drives the Badge colour
const TYPE_TONES = {
  temporal: 'calm',
  contextual: 'neutral',
  physiological: 'warning',
  compound: 'warning',
} as const satisfies Record<string, 'calm' | 'neutral' | 'warning'>;

// ---------------------------------------------------------------------------
// Inner component (client)
// ---------------------------------------------------------------------------

function PatternDetailInner({ locale, patternId }: { locale: string; patternId: string }) {
  usePhiAudit('/patterns/[id]');
  const t = useTranslations();
  const router = useRouter();
  const { data: patterns } = usePatterns();

  const pattern = (patterns ?? []).find((p) => p.pattern_id === patternId);

  if (!pattern) {
    return (
      <Layout locale={locale}>
        <div className="space-y-6 max-w-2xl mx-auto">
          <p className="text-sm text-ink-tertiary">{t('reports.notFound')}</p>
        </div>
      </Layout>
    );
  }

  const tone: 'calm' | 'neutral' | 'warning' =
    (TYPE_TONES as Record<string, 'calm' | 'neutral' | 'warning'>)[pattern.pattern_type] ??
    'neutral';

  return (
    <Layout locale={locale}>
      <div className="space-y-6 max-w-2xl mx-auto">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => router.push(`/${locale}/patterns`)}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
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
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
            {t('patterns.title')}
          </button>
        </nav>

        {/* Header */}
        <header>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
              {t(`patterns.typeLabels.${pattern.pattern_type}`)}
            </h1>
            <Badge tone={tone}>{t(`patterns.typeLabels.${pattern.pattern_type}`)}</Badge>
          </div>
          <p className="mt-1 text-sm text-ink-quaternary">
            {t('patterns.confidenceLabel')}:{' '}
            <span className="clinical-number tabular-nums">
              {formatPercentClinical(Math.round(pattern.confidence * 100))}
            </span>
          </p>
        </header>

        {/* Full insight card */}
        <InsightCard
          id={pattern.pattern_id}
          headline={t(`patterns.typeLabels.${pattern.pattern_type}`)}
          body={pattern.description}
          locale={locale}
        />

        {/* Metadata card */}
        {Object.keys(pattern.metadata).length > 0 && (
          <Card>
            <h2 className="text-sm font-semibold text-ink-primary mb-3">
              {t('patterns.detectedLabel')}
            </h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(pattern.metadata).map(([key, value]) => (
                <span
                  key={key}
                  className="inline-flex items-center rounded-md bg-surface-tertiary px-2 py-1 text-xs text-ink-secondary"
                >
                  {key}: {String(value).slice(0, 40)}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Crisis footer */}
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

// ---------------------------------------------------------------------------
// Page export — server shell with async params, renders client inner
// ---------------------------------------------------------------------------

export default function PatternDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): React.JSX.Element {
  const { locale, id } = use(params);
  return <PatternDetailInner locale={locale} patternId={id} />;
}
