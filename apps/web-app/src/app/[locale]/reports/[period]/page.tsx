'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card, RCIDelta } from '@disciplineos/design-system';
import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import { usePhiAudit } from '@/hooks/usePhiAudit';
import { useReportDetail } from '@/hooks/useReports';
import { FhirExportButton } from '@/components/FhirExportButton';

function ReportDetailInner({ locale, periodId }: { locale: string; periodId: string }) {
  usePhiAudit('/reports/[period]');
  const t = useTranslations();
  const router = useRouter();
  const { period } = useReportDetail(periodId);

  if (!period) {
    return (
      <Layout locale={locale}>
        <div className="space-y-6 max-w-2xl mx-auto">
          <p className="text-sm text-ink-tertiary">{t('reports.notFound')}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout locale={locale}>
      <div className="space-y-6 max-w-2xl mx-auto">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => router.push(`/${locale}/reports`)}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
              <path d="M19 12H5M12 5l-7 7 7 7"/>
            </svg>
            {t('reports.title')}
          </button>
        </nav>

        {/* Header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {period.label}
          </h1>
          <p className="mt-1 text-sm text-ink-quaternary">
            {period.start_date} &ndash; {period.end_date}
          </p>
        </header>

        {/* PHQ-9 card */}
        <Card>
          <h2 className="text-sm font-semibold text-ink-primary mb-3">PHQ-9</h2>
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="text-xs text-ink-quaternary">{t('reports.scoreStart')}</span>
              <span className="ml-1 text-sm font-medium text-ink-primary clinical-number tabular-nums">
                {formatNumberClinical(period.phq9_start)}
              </span>
              <span className="mx-2 text-ink-quaternary">&rarr;</span>
              <span className="text-xs text-ink-quaternary">{t('reports.scoreEnd')}</span>
              <span className="ml-1 text-sm font-medium text-ink-primary clinical-number tabular-nums">
                {formatNumberClinical(period.phq9_end)}
              </span>
            </div>
            <RCIDelta delta={period.phq9_rci_delta} />
          </div>
        </Card>

        {/* GAD-7 card */}
        <Card>
          <h2 className="text-sm font-semibold text-ink-primary mb-3">GAD-7</h2>
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="text-xs text-ink-quaternary">{t('reports.scoreStart')}</span>
              <span className="ml-1 text-sm font-medium text-ink-primary clinical-number tabular-nums">
                {formatNumberClinical(period.gad7_start)}
              </span>
              <span className="mx-2 text-ink-quaternary">&rarr;</span>
              <span className="text-xs text-ink-quaternary">{t('reports.scoreEnd')}</span>
              <span className="ml-1 text-sm font-medium text-ink-primary clinical-number tabular-nums">
                {formatNumberClinical(period.gad7_end)}
              </span>
            </div>
            <RCIDelta delta={period.gad7_rci_delta} />
          </div>
        </Card>

        {/* Resilience card */}
        <Card>
          <h2 className="text-sm font-semibold text-ink-primary mb-3">{t('reports.resilience')}</h2>
          <div className="flex gap-8">
            <div>
              <p className="text-xs text-ink-quaternary">{t('reports.resilienceDays')}</p>
              <p className="text-xl font-semibold text-ink-primary clinical-number tabular-nums">
                {formatNumberClinical(period.resilience_days)}
              </p>
            </div>
            <div>
              <p className="text-xs text-ink-quaternary">{t('reports.urgesHandled')}</p>
              <p className="text-xl font-semibold text-ink-primary clinical-number tabular-nums">
                {formatNumberClinical(period.urges_handled)}
              </p>
            </div>
          </div>
        </Card>

        {/* FHIR Export */}
        <section aria-labelledby="fhir-export-heading">
          <h2
            id="fhir-export-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('reports.exportHeading')}
          </h2>
          <Card>
            <p className="text-xs text-ink-tertiary mb-3">{t('reports.exportDescription')}</p>
            <FhirExportButton
              periodId={periodId}
              locale={locale}
              label={t('reports.exportButton')}
              stepUpLabel={t('reports.exportStepUpRequired')}
              errorLabel={t('reports.exportError')}
            />
          </Card>
        </section>

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

export default function ReportDetailPage({
  params,
}: {
  params: Promise<{ locale: string; period: string }>;
}): React.JSX.Element {
  const { locale, period } = use(params);
  return <ReportDetailInner locale={locale} periodId={period} />;
}
