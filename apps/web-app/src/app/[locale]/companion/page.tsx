'use client';
// WARNING: LLM-PROHIBITED ROUTE
// discipline/no-llm-on-crisis-route ESLint rule enforces this at CI level.
// Do NOT import @disciplineos/llm-client, @anthropic-ai/, openai, or claude-sdk here.
// CompassionTemplate must render deterministically from JSON — never from LLM output.

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { CompassionTemplate } from '@disciplineos/design-system';
import { useCompanion } from '@/hooks/useCompanion';

function CompanionInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { template } = useCompanion();

  return (
    <Layout locale={locale}>
      <div className="space-y-8 max-w-2xl mx-auto">
        {/* Quiet headline */}
        <header className="text-center pt-8">
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('companion.headline')}
          </h1>
          <p className="mt-2 text-sm text-ink-tertiary">{t('companion.subheadline')}</p>
        </header>

        {/* Compassion template — rendered verbatim from JSON, no LLM */}
        <CompassionTemplate
          text={template.text}
          templateId={template.id}
        />

        {/* Three deterministic next steps */}
        <section aria-labelledby="companion-next-steps-heading">
          <h2
            id="companion-next-steps-heading"
            className="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-quaternary text-center"
          >
            {t('companion.nextStepsHeading')}
          </h2>
          <div className="space-y-3">
            {/* 1. Log this moment */}
            <a
              href={`/${locale}/check-in`}
              data-testid="companion-next-step-checkin"
              className="flex items-center gap-3 rounded-xl border border-border-subtle bg-surface-secondary p-4 hover:bg-surface-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0 text-ink-secondary" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 8v4M12 16h.01"/>
              </svg>
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink-primary">{t('companion.stepCheckIn')}</p>
                <p className="text-xs text-ink-tertiary">{t('companion.stepCheckInDesc')}</p>
              </div>
            </a>

            {/* 2. Read: After a Lapse */}
            <a
              href={`/${locale}/library/understanding-addiction/after-a-lapse`}
              data-testid="companion-next-step-read"
              className="flex items-center gap-3 rounded-xl border border-border-subtle bg-surface-secondary p-4 hover:bg-surface-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0 text-ink-secondary" aria-hidden="true">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
              </svg>
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink-primary">{t('companion.stepRead')}</p>
                <p className="text-xs text-ink-tertiary">{t('companion.stepReadDesc')}</p>
              </div>
            </a>

            {/* 3. Get support */}
            <a
              href={`/${locale}/crisis`}
              data-testid="companion-next-step-crisis"
              className="flex items-center gap-3 rounded-xl border border-border-subtle bg-surface-secondary p-4 hover:bg-signal-crisis/5 hover:border-signal-crisis/30 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0 text-signal-crisis" aria-hidden="true">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.7 14.1 19.79 19.79 0 0 1 1.63 5.58 2 2 0 0 1 3.6 3.4h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 11a16 16 0 0 0 6.06 6.06l1.27-.65a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              <div className="min-w-0">
                <p className="text-sm font-medium text-signal-crisis">{t('companion.stepCrisis')}</p>
                <p className="text-xs text-ink-tertiary">{t('companion.stepCrisisDesc')}</p>
              </div>
            </a>
          </div>
        </section>
      </div>
    </Layout>
  );
}

export default function CompanionPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <CompanionInner locale={locale} />;
}
