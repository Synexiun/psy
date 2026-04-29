'use client';

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { BackBreadcrumb } from '@/components/BackBreadcrumb';
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
// Pattern type guard
// ---------------------------------------------------------------------------

const KNOWN_PATTERN_TYPES = ['temporal', 'contextual', 'physiological', 'compound'] as const;
type KnownPatternType = typeof KNOWN_PATTERN_TYPES[number];

function isKnownPatternType(v: string): v is KnownPatternType {
  return (KNOWN_PATTERN_TYPES as readonly string[]).includes(v);
}

// ---------------------------------------------------------------------------
// Inner component (client)
// ---------------------------------------------------------------------------

function PatternDetailInner({ locale, patternId }: { locale: string; patternId: string }) {
  usePhiAudit('/patterns/[id]');
  const t = useTranslations();
  const { data: patterns, isLoading } = usePatterns();

  const pattern = (patterns ?? []).find((p) => p.pattern_id === patternId);

  if (!pattern) {
    return (
      <Layout locale={locale}>
        <div className="space-y-6 max-w-2xl mx-auto">
          <p className="text-sm text-ink-tertiary">
            {isLoading ? '' : t('patterns.notFound')}
          </p>
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
        <BackBreadcrumb label={t('patterns.title')} href={`/${locale}/patterns`} />

        {/* Header */}
        <header>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
              {isKnownPatternType(pattern.pattern_type)
                ? t(`patterns.typeLabels.${pattern.pattern_type}`)
                : pattern.pattern_type}
            </h1>
            <Badge tone={tone}>
              {isKnownPatternType(pattern.pattern_type)
                ? t(`patterns.typeLabels.${pattern.pattern_type}`)
                : pattern.pattern_type}
            </Badge>
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
          headline={
            isKnownPatternType(pattern.pattern_type)
              ? t(`patterns.typeLabels.${pattern.pattern_type}`)
              : pattern.pattern_type
          }
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
