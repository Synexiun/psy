'use client';

import { use, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import { Layout } from '@/components/Layout';
import { Button, Card, ProgressRing } from '@/components/primitives';
import { useAssessmentSessions } from '@/hooks/useDashboardData';

// ---------------------------------------------------------------------------
// Clinical instruments — named exactly as validated. Do NOT paraphrase.
// Severity thresholds come from pinned sources (Kroenke 2001, Spitzer 2006, etc.)
// Scores are ALWAYS rendered as Latin digits regardless of locale (see CLAUDE.md rule 9).
// ---------------------------------------------------------------------------

interface AssessmentInstrument {
  id: string;
  /** Validated short name — must not be paraphrased */
  name: string;
  /** Validated full name */
  fullName: string;
  /** Maximum possible score for the progress ring */
  maxScore: number;
  /** Ring colour token */
  color: string;
  /** Last completed date or null — populated from API */
  lastDate: string | null;
  /** Last score or null — rendered as Latin digits */
  lastScore: number | null;
  /** Severity label matching validated bands */
  lastSeverity: string | null;
}

type InstrumentCatalogKey = 'phq9' | 'gad7' | 'auditC' | 'pss10' | 'who5';

/** Maps instrument id to the assessments.instruments.* catalog key */
const INSTRUMENT_CATALOG_KEY: Record<string, InstrumentCatalogKey> = {
  phq9: 'phq9',
  gad7: 'gad7',
  'audit-c': 'auditC',
  pss10: 'pss10',
  who5: 'who5',
};

// Static instrument metadata — never paraphrase these names (validated instruments).
// Dynamic data (score, date, severity) is merged from useAssessmentSessions at render time.
const INSTRUMENT_METADATA: Omit<AssessmentInstrument, 'lastDate' | 'lastScore' | 'lastSeverity'>[] = [
  {
    id: 'phq9',
    name: 'PHQ-9',
    fullName: 'Patient Health Questionnaire-9',
    maxScore: 27,
    color: 'var(--color-signal-stable)',
  },
  {
    id: 'gad7',
    name: 'GAD-7',
    fullName: 'Generalized Anxiety Disorder-7',
    maxScore: 21,
    color: 'var(--color-accent-bronze)',
  },
  {
    id: 'audit-c',
    name: 'AUDIT-C',
    fullName: 'Alcohol Use Disorders Identification Test-C',
    maxScore: 12,
    color: 'var(--color-signal-warning)',
  },
  {
    id: 'pss10',
    name: 'PSS-10',
    fullName: 'Perceived Stress Scale-10',
    maxScore: 40,
    color: 'var(--color-signal-crisis)',
  },
  {
    id: 'who5',
    name: 'WHO-5',
    fullName: 'World Health Organization Well-Being Index (5-item)',
    maxScore: 100,
    color: 'var(--color-signal-stable)',
  },
];


function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Assessment card
// ---------------------------------------------------------------------------

function AssessmentCard({
  instrument,
  catalogKey,
  locale,
}: {
  instrument: AssessmentInstrument;
  catalogKey: InstrumentCatalogKey;
  locale: string;
}) {
  const t = useTranslations();
  const hasScore = instrument.lastScore !== null && instrument.lastDate !== null;

  return (
    <Card className="flex flex-col gap-4">
      {/* Header: name + ring */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          {/* Validated instrument name sourced from i18n catalog — never paraphrase */}
          <p className="text-base font-semibold text-ink-primary">
            {t(`assessments.instruments.${catalogKey}.name`)}
          </p>
          <p className="mt-0.5 text-xs text-ink-tertiary leading-snug">
            {t(`assessments.instruments.${catalogKey}.fullName`)}
          </p>
        </div>

        {/* Progress ring — score always Latin digits */}
        <div className="shrink-0">
          {hasScore ? (
            <ProgressRing
              value={instrument.lastScore!}
              max={instrument.maxScore}
              size={64}
              strokeWidth={6}
              color={instrument.color}
              label={
                <span className="text-sm font-bold tabular-nums clinical-number">
                  {formatNumberClinical(instrument.lastScore!)}
                </span>
              }
              sublabel={
                <span className="text-[10px] text-ink-quaternary">/ {formatNumberClinical(instrument.maxScore)}</span>
              }
              ariaLabel={`${instrument.name} score: ${formatNumberClinical(instrument.lastScore!)} out of ${formatNumberClinical(instrument.maxScore)}`}
            />
          ) : (
            <div
              className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-dashed border-border-subtle"
              aria-label={`${instrument.name} — no score yet`}
            >
              <span className="text-xs text-ink-quaternary">—</span>
            </div>
          )}
        </div>
      </div>

      {/* Last completed / severity */}
      <div className="space-y-1">
        {hasScore ? (
          <>
            <p className="text-xs text-ink-quaternary">
              {t('assessments.lastCompleted')}:{' '}
              <span className="text-ink-secondary font-medium">{formatDate(instrument.lastDate!)}</span>
            </p>
            {instrument.lastSeverity && (
              <p className="text-xs text-ink-quaternary">
                {t('assessments.score')}:{' '}
                <span className="font-medium text-ink-secondary clinical-number">
                  {formatNumberClinical(instrument.lastScore!)} — {instrument.lastSeverity}
                </span>
              </p>
            )}
          </>
        ) : (
          <p className="text-xs text-ink-quaternary italic">{t('assessments.notYetTaken')}</p>
        )}
      </div>

      {/* CTA */}
      <Button
        variant={hasScore ? 'secondary' : 'primary'}
        size="sm"
        className="w-full min-h-[44px] mt-auto"
        onClick={() => {
          window.location.href = `/${locale}/assessments/${instrument.id}`;
        }}
      >
        {t('assessments.takeAssessment')}
      </Button>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function AssessmentsInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { data: sessions } = useAssessmentSessions();

  // Merge latest session data into static instrument metadata.
  const instruments: AssessmentInstrument[] = useMemo(() => {
    const latestByInstrument = new Map<string, { score: number; severity: string; date: string }>();
    if (sessions) {
      for (const session of sessions) {
        const existing = latestByInstrument.get(session.instrument);
        if (!existing || session.completed_at > existing.date) {
          latestByInstrument.set(session.instrument, {
            score: session.score,
            severity: session.severity,
            date: session.completed_at,
          });
        }
      }
    }
    return INSTRUMENT_METADATA.map((meta) => {
      const latest = latestByInstrument.get(meta.id);
      return {
        ...meta,
        lastDate: latest?.date?.slice(0, 10) ?? null,
        lastScore: latest?.score ?? null,
        lastSeverity: latest?.severity ?? null,
      };
    });
  }, [sessions]);

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('nav.assessments')}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">{t('assessments.subtitle')}</p>
        </header>

        {/* Instruments grid */}
        <section aria-labelledby="assessments-grid-heading">
          <h2 id="assessments-grid-heading" className="sr-only">
            Available assessments
          </h2>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {instruments.map((instrument) => (
              <AssessmentCard
                key={instrument.id}
                instrument={instrument}
                catalogKey={INSTRUMENT_CATALOG_KEY[instrument.id] ?? 'phq9'}
                locale={locale}
              />
            ))}
          </div>
        </section>

        {/* Clinical disclaimer — required */}
        <aside
          className="rounded-xl border border-border-subtle bg-surface-primary px-5 py-4"
          role="note"
          aria-label="Clinical disclaimer"
        >
          <p className="text-xs leading-relaxed text-ink-tertiary">{t('assessments.disclaimer')}</p>
        </aside>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function AssessmentsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <AssessmentsInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.assessments
 *   assessments.title
 *   assessments.subtitle
 *   assessments.takeAssessment
 *   assessments.notYetTaken
 *   assessments.disclaimer
 *   assessments.instruments.phq9.name / .fullName
 *   assessments.instruments.gad7.name / .fullName
 *   assessments.instruments.auditC.name / .fullName
 *   assessments.instruments.pss10.name / .fullName
 *   assessments.instruments.who5.name / .fullName
 *
 *   assessments.score
 *   assessments.lastCompleted
 */
