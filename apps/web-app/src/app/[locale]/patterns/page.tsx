'use client';

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';
import { InsightCard } from '@disciplineos/design-system';
import { usePhiAudit } from '@/hooks/usePhiAudit';
import { usePatterns } from '@/hooks/usePatterns';
import { formatPercentClinical } from '@disciplineos/i18n-catalog';

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

function PatternsInner({ locale }: { locale: string }) {
  usePhiAudit('/patterns');
  const t = useTranslations();
  const { data: patterns, isLoading } = usePatterns();

  const activePatterns = (patterns ?? []).filter((p) => p.status === 'active');

  function handleDismiss(id: string): void {
    // Fire-and-forget: in Phase 5, call POST /v1/patterns/{id}/dismiss
    // InsightCard handles local state — we just log the intent here.
    void id;
  }

  function handleSnooze(id: string, duration: '24h' | '7d'): void {
    // Fire-and-forget: in Phase 5, call POST /v1/patterns/{id}/snooze
    void id;
    void duration;
  }

  function handleAcknowledge(id: string): void {
    // Fire-and-forget: in Phase 5, call POST /v1/patterns/{id}/acknowledge
    void id;
  }

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('patterns.title')}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">{t('patterns.subtitle')}</p>
        </header>

        <section aria-labelledby="active-patterns-heading">
          <h2
            id="active-patterns-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('patterns.activeHeading')}
          </h2>

          {isLoading ? (
            <div className="space-y-3" aria-busy="true" aria-label="Loading patterns">
              {[0, 1].map((i) => (
                <div
                  key={i}
                  className="h-[108px] animate-pulse rounded-xl bg-surface-tertiary"
                  aria-hidden="true"
                />
              ))}
            </div>
          ) : activePatterns.length === 0 ? (
            <Card>
              <p className="text-sm text-ink-tertiary text-center py-4">{t('patterns.empty')}</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {activePatterns.map((pattern) => (
                <div
                  key={pattern.pattern_id}
                  className="space-y-1"
                  data-testid={`pattern-item-${pattern.pattern_id}`}
                >
                  <InsightCard
                    id={pattern.pattern_id}
                    headline={
                      (isKnownPatternType(pattern.pattern_type)
                        ? t(`patterns.typeLabels.${pattern.pattern_type}`)
                        : pattern.pattern_type) +
                      ' — ' +
                      formatPercentClinical(Math.round(pattern.confidence * 100)) +
                      ' ' +
                      t('patterns.confidenceLabel')
                    }
                    body={pattern.description}
                    locale={locale}
                    onDismiss={handleDismiss}
                    onSnooze={handleSnooze}
                    onAcknowledge={handleAcknowledge}
                  />
                  <a
                    href={`/${locale}/patterns/${pattern.pattern_id}`}
                    className="inline-flex items-center gap-1 text-xs text-ink-quaternary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
                    data-testid={`pattern-detail-link-${pattern.pattern_id}`}
                  >
                    {t('patterns.viewDetails')}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 16 16"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={1.5}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-3 w-3"
                      aria-hidden="true"
                    >
                      <path d="M3 8h10M9 4l4 4-4 4" />
                    </svg>
                  </a>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export — server shell with async params, renders client inner
// ---------------------------------------------------------------------------

export default function PatternsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <PatternsInner locale={locale} />;
}
