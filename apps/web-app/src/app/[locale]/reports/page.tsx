'use client';

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card, RCIDelta } from '@disciplineos/design-system';
import { usePhiAudit } from '@/hooks/usePhiAudit';
import { useReports } from '@/hooks/useReports';

function ReportsInner({ locale }: { locale: string }) {
  usePhiAudit('/reports');
  const t = useTranslations();
  const { periods } = useReports();

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('reports.title')}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">{t('reports.subtitle')}</p>
        </header>

        <section aria-labelledby="report-periods-heading">
          <h2
            id="report-periods-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('reports.periodsHeading')}
          </h2>
          {periods.length === 0 ? (
            <Card>
              <p className="text-sm text-ink-tertiary text-center py-4">{t('reports.empty')}</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {periods.map((period) => (
                <a
                  key={period.period_id}
                  href={`/${locale}/reports/${period.period_id}`}
                  data-testid={`report-period-${period.period_id}`}
                  className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded-xl"
                >
                  <Card hover>
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-ink-primary">{period.label}</p>
                        <p className="mt-0.5 text-xs text-ink-quaternary">
                          {period.start_date} &ndash; {period.end_date}
                        </p>
                      </div>
                      <div className="shrink-0">
                        {/* eslint-disable-next-line @disciplineos/discipline/clinical-numbers-must-format */}
                        <RCIDelta delta={period.phq9_rci_delta} />
                      </div>
                    </div>
                  </Card>
                </a>
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}

export default function ReportsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <ReportsInner locale={locale} />;
}
