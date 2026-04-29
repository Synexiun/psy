'use client';

/**
 * Assessment session page — one instrument at a time, one question per screen.
 *
 * Clinical compliance notes:
 *  - Item text is VERBATIM from validated publications. Do NOT paraphrase.
 *    PHQ-9: Kroenke et al., 2001. GAD-7: Spitzer et al., 2006.
 *    WHO-5: WHO (1998). AUDIT-C: Bush et al., 1998. PSS-10: Cohen et al., 1983.
 *  - PHQ-9 item 9 (suicidal ideation) triggers a compassion-first safety message
 *    if the user selects any score > 0. This is a T4 safety path — never feature-flagged.
 *  - All scores and progress counters render as Latin digits (formatNumberClinical).
 *  - No LLM calls anywhere in this flow.
 *  - Post-submission disclaimer: "This assessment is not a substitute for professional
 *    clinical evaluation."
 */

import * as React from 'react';
import { use } from 'react';
import { notFound } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth } from '@clerk/nextjs';
import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import { Layout } from '@/components/Layout';
import { Button, Card } from '@disciplineos/design-system';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ResponseOption {
  label: string;
  value: number;
}

interface InstrumentQuestion {
  /** 1-based item number matching the source publication */
  item: number;
  /** Verbatim item text — never paraphrase */
  text: string;
  /** Whether this item is reverse-scored (informational; actual reverse scoring done server-side) */
  reverseScored?: boolean;
}

interface InstrumentDefinition {
  /** URL slug */
  id: string;
  /** Short validated name */
  name: string;
  /** Full validated name */
  fullName: string;
  /** Maximum possible raw score */
  maxScore: number;
  /** Validated response options (same for all items, or item overrides if needed) */
  responseOptions: ResponseOption[];
  /** Questions — verbatim item text */
  questions: InstrumentQuestion[];
  /** Estimated completion time string (e.g. "2–3") */
  estimatedMinutes: string;
  /** One-sentence description of the construct being measured */
  description: string;
}

// ---------------------------------------------------------------------------
// PHQ-9 severity bands (Kroenke et al., 2001)
// 0–4: none/minimal; 5–9: mild; 10–14: moderate; 15–19: moderately severe; 20–27: severe
// ---------------------------------------------------------------------------

function phq9SeverityBand(score: number): string {
  if (score <= 4) return 'Minimal';
  if (score <= 9) return 'Mild';
  if (score <= 14) return 'Moderate';
  if (score <= 19) return 'Moderately severe';
  return 'Severe';
}

// GAD-7 severity bands (Spitzer et al., 2006)
// 0–4: minimal; 5–9: mild; 10–14: moderate; 15–21: severe
function gad7SeverityBand(score: number): string {
  if (score <= 4) return 'Minimal';
  if (score <= 9) return 'Mild';
  if (score <= 14) return 'Moderate';
  return 'Severe';
}

// WHO-5 — raw × 4 = 0–100 percentage score
// < 50 suggests poor wellbeing / depression screen positive
function who5SeverityBand(rawScore: number): string {
  const pct = rawScore * 4;
  if (pct < 28) return 'Poor';
  if (pct < 50) return 'Low';
  if (pct < 72) return 'Moderate';
  return 'Good';
}

// AUDIT-C — gender-adjusted thresholds; we show generic bands here (server applies
// gender-adjusted scoring). For display purposes: ≥3 women / ≥4 men → positive screen.
function auditCSeverityBand(score: number): string {
  if (score <= 2) return 'Low risk';
  if (score <= 5) return 'Moderate risk';
  return 'High risk';
}

// PSS-10 — Cohen et al., 1983 normative bands (Normed 10-item version, 0–40)
// Low: 0–13; Moderate: 14–26; High: 27–40
function pss10SeverityBand(score: number): string {
  if (score <= 13) return 'Low';
  if (score <= 26) return 'Moderate';
  return 'High';
}

function getSeverityBand(instrumentId: string, score: number): string {
  switch (instrumentId) {
    case 'phq-9':   return phq9SeverityBand(score);
    case 'gad-7':   return gad7SeverityBand(score);
    case 'who-5':   return who5SeverityBand(score);
    case 'audit-c': return auditCSeverityBand(score);
    case 'pss-10':  return pss10SeverityBand(score);
    default:        return '';
  }
}

// ---------------------------------------------------------------------------
// Instrument catalog — verbatim item text from source publications
// ---------------------------------------------------------------------------

/**
 * Standard PHQ-9/GAD-7 frequency options.
 * Verbatim from the instrument; do not change label text.
 */
const FREQ_4: ResponseOption[] = [
  { label: 'Not at all',             value: 0 },
  { label: 'Several days',           value: 1 },
  { label: 'More than half the days', value: 2 },
  { label: 'Nearly every day',       value: 3 },
];

/**
 * WHO-5 frequency options.
 * Verbatim from WHO-5 (1998 version).
 */
const WHO5_OPTIONS: ResponseOption[] = [
  { label: 'At no time',             value: 0 },
  { label: 'Some of the time',       value: 1 },
  { label: 'Less than half of the time', value: 2 },
  { label: 'More than half of the time', value: 3 },
  { label: 'Most of the time',       value: 4 },
  { label: 'All of the time',        value: 5 },
];

const INSTRUMENTS: Record<string, InstrumentDefinition> = {
  /**
   * PHQ-9 — Patient Health Questionnaire (9-item)
   * Source: Kroenke K, Spitzer RL, Williams JB. The PHQ-9. J Gen Intern Med. 2001;16(9):606-613.
   * Items are verbatim. Scoring: 0–27. Safety item: item 9 (index 8).
   */
  'phq-9': {
    id: 'phq-9',
    name: 'PHQ-9',
    fullName: 'Patient Health Questionnaire – 9',
    maxScore: 27,
    responseOptions: FREQ_4,
    estimatedMinutes: '2–3',
    description:
      'Measures how often you have been bothered by depressive symptoms over the past two weeks.',
    questions: [
      { item: 1, text: 'Little interest or pleasure in doing things' },
      { item: 2, text: 'Feeling down, depressed, or hopeless' },
      { item: 3, text: 'Trouble falling or staying asleep, or sleeping too much' },
      { item: 4, text: 'Feeling tired or having little energy' },
      { item: 5, text: 'Poor appetite or overeating' },
      {
        item: 6,
        text: 'Feeling bad about yourself — or that you are a failure or have let yourself or your family down',
      },
      {
        item: 7,
        text: 'Trouble concentrating on things, such as reading the newspaper or watching television',
      },
      {
        item: 8,
        text: 'Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual',
      },
      {
        item: 9,
        text: 'Thoughts that you would be better off dead or of hurting yourself in some way',
      },
    ],
  },

  /**
   * GAD-7 — Generalized Anxiety Disorder (7-item)
   * Source: Spitzer RL, Kroenke K, Williams JB, Löwe B. A brief measure for assessing
   * generalized anxiety disorder. Arch Intern Med. 2006;166(10):1092-1097.
   * Items are verbatim. Scoring: 0–21.
   */
  'gad-7': {
    id: 'gad-7',
    name: 'GAD-7',
    fullName: 'Generalized Anxiety Disorder – 7',
    maxScore: 21,
    responseOptions: FREQ_4,
    estimatedMinutes: '2–3',
    description:
      'Measures how often you have been bothered by anxiety symptoms over the past two weeks.',
    questions: [
      { item: 1, text: 'Feeling nervous, anxious, or on edge' },
      { item: 2, text: 'Not being able to stop or control worrying' },
      { item: 3, text: 'Worrying too much about different things' },
      { item: 4, text: 'Trouble relaxing' },
      { item: 5, text: "Being so restless that it's hard to sit still" },
      { item: 6, text: 'Becoming easily annoyed or irritable' },
      { item: 7, text: 'Feeling afraid as if something awful might happen' },
    ],
  },

  /**
   * WHO-5 — World Health Organization Well-Being Index (5-item)
   * Source: WHO Regional Office for Europe (1998). Mastering Depression in Primary Care.
   * Items are verbatim. Raw score 0–25; multiply by 4 for 0–100 percentage scale.
   */
  'who-5': {
    id: 'who-5',
    name: 'WHO-5',
    fullName: 'World Health Organization Well-Being Index – 5',
    maxScore: 25,
    responseOptions: WHO5_OPTIONS,
    estimatedMinutes: '2',
    description: 'Measures your general wellbeing over the past two weeks.',
    questions: [
      { item: 1, text: 'I have felt cheerful and in good spirits' },
      { item: 2, text: 'I have felt calm and relaxed' },
      { item: 3, text: 'I have felt active and vigorous' },
      { item: 4, text: 'I woke up feeling fresh and rested' },
      { item: 5, text: 'My daily life has been filled with things that interest me' },
    ],
  },

  /**
   * AUDIT-C — Alcohol Use Disorders Identification Test – Consumption subscale (3 items)
   * Source: Bush K, Kivlahan DR, McDonell MB, Fihn SD, Bradley KA. The AUDIT alcohol
   * consumption questions (AUDIT-C). Arch Intern Med. 1998;158(16):1789-1795.
   * Items are verbatim. Scoring: 0–12.
   */
  'audit-c': {
    id: 'audit-c',
    name: 'AUDIT-C',
    fullName: 'Alcohol Use Disorders Identification Test – Consumption',
    maxScore: 12,
    // Each item has distinct response options; we use a special marker and render per-item.
    responseOptions: [], // see AUDIT_C_ITEM_OPTIONS below
    estimatedMinutes: '1–2',
    description: 'A brief screen for hazardous or harmful alcohol consumption.',
    questions: [
      {
        item: 1,
        text: 'How often do you have a drink containing alcohol?',
      },
      {
        item: 2,
        text: 'How many units of alcohol do you drink on a typical day when you are drinking?',
      },
      {
        item: 3,
        text: 'How often do you have 6 or more units if female, or 8 or more if male, on a single occasion in the last year?',
      },
    ],
  },

  /**
   * PSS-10 — Perceived Stress Scale (10-item)
   * Source: Cohen S, Kamarck T, Mermelstein R. A global measure of perceived stress.
   * J Health Soc Behav. 1983;24(4):385-396.
   * Items are verbatim. Scoring: 0–40.
   * Reverse-scored items (positively framed): 4, 5, 7, 8. Formula: 4 − raw_value.
   */
  'pss-10': {
    id: 'pss-10',
    name: 'PSS-10',
    fullName: 'Perceived Stress Scale – 10',
    maxScore: 40,
    responseOptions: [
      { label: 'Never',          value: 0 },
      { label: 'Almost never',   value: 1 },
      { label: 'Sometimes',      value: 2 },
      { label: 'Fairly often',   value: 3 },
      { label: 'Very often',     value: 4 },
    ],
    estimatedMinutes: '3–5',
    description:
      'Measures the degree to which situations in your life are perceived as stressful over the past month.',
    questions: [
      {
        item: 1,
        text: 'In the last month, how often have you been upset because of something that happened unexpectedly?',
      },
      {
        item: 2,
        text: 'In the last month, how often have you felt that you were unable to control the important things in your life?',
      },
      {
        item: 3,
        text: 'In the last month, how often have you felt nervous and stressed?',
      },
      {
        item: 4,
        text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?',
        reverseScored: true,
      },
      {
        item: 5,
        text: 'In the last month, how often have you felt that things were going your way?',
        reverseScored: true,
      },
      {
        item: 6,
        text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?',
      },
      {
        item: 7,
        text: 'In the last month, how often have you been able to control irritations in your life?',
        reverseScored: true,
      },
      {
        item: 8,
        text: 'In the last month, how often have you felt that you were on top of things?',
        reverseScored: true,
      },
      {
        item: 9,
        text: 'In the last month, how often have you been angered because of things that were outside of your control?',
      },
      {
        item: 10,
        text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?',
      },
    ],
  },
};

// Per-item response options for AUDIT-C (each item has a different scale)
const AUDIT_C_ITEM_OPTIONS: Record<number, ResponseOption[]> = {
  1: [
    { label: 'Never',                        value: 0 },
    { label: 'Monthly or less',              value: 1 },
    { label: '2 to 4 times a month',         value: 2 },
    { label: '2 to 3 times a week',          value: 3 },
    { label: '4 or more times a week',       value: 4 },
  ],
  2: [
    { label: '1 or 2',                       value: 0 },
    { label: '3 or 4',                       value: 1 },
    { label: '5 or 6',                       value: 2 },
    { label: '7, 8, or 9',                   value: 3 },
    { label: '10 or more',                   value: 4 },
  ],
  3: [
    { label: 'Never',                        value: 0 },
    { label: 'Less than monthly',            value: 1 },
    { label: 'Monthly',                      value: 2 },
    { label: 'Weekly',                       value: 3 },
    { label: 'Daily or almost daily',        value: 4 },
  ],
};

function getItemOptions(instrument: InstrumentDefinition, itemNumber: number): ResponseOption[] {
  if (instrument.id === 'audit-c') {
    return AUDIT_C_ITEM_OPTIONS[itemNumber] ?? [];
  }
  return instrument.responseOptions;
}

// ---------------------------------------------------------------------------
// Score computation (client-side — deterministic, matches server scoring)
// PSS-10 reverse-scored items: 4, 5, 7, 8  (1-based). Reverse = 4 - raw value.
// WHO-5: raw sum 0–25 (multiplied by 4 on display to give 0–100 percentage).
// ---------------------------------------------------------------------------

function computeScore(instrument: InstrumentDefinition, responses: Record<number, number>): number {
  let total = 0;
  for (const q of instrument.questions) {
    const raw = responses[q.item] ?? 0;
    if (instrument.id === 'pss-10' && q.reverseScored) {
      total += 4 - raw;
    } else {
      total += raw;
    }
  }
  return total;
}

/** WHO-5 display score: raw × 4 gives the 0–100 percentage-point scale. */
function displayScore(instrument: InstrumentDefinition, rawScore: number): number {
  if (instrument.id === 'who-5') return rawScore * 4;
  return rawScore;
}

/** WHO-5 display max: 25 raw × 4 = 100. */
function displayMax(instrument: InstrumentDefinition): number {
  if (instrument.id === 'who-5') return 100;
  return instrument.maxScore;
}

// ---------------------------------------------------------------------------
// PHQ-9 item 9 safety check
// Trigger: item 9 (1-based) response value > 0 in a completed PHQ-9 session.
// This is part of the T4 safety path — must never be gated, removed, or feature-flagged.
// ---------------------------------------------------------------------------

function phq9SafetyTriggered(
  instrumentId: string,
  responses: Record<number, number>,
): boolean {
  if (instrumentId !== 'phq-9') return false;
  return (responses[9] ?? 0) > 0;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface ProgressBarProps {
  current: number;
  total: number;
}

function ProgressBar({ current, total }: ProgressBarProps): React.ReactElement {
  const pct = total === 0 ? 0 : (current / total) * 100;
  return (
    <div
      role="progressbar"
      aria-valuenow={current}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-label={`Question ${formatNumberClinical(current)} of ${formatNumberClinical(total)}`}
      className="h-1.5 w-full overflow-hidden rounded-full bg-surface-tertiary"
    >
      <div
        className="h-full rounded-full bg-accent-bronze transition-all duration-base ease-standard"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

interface ResponseButtonProps {
  option: ResponseOption;
  selected: boolean;
  onSelect: (value: number) => void;
}

function ResponseButton({ option, selected, onSelect }: ResponseButtonProps): React.ReactElement {
  return (
    <button
      type="button"
      onClick={() => { onSelect(option.value); }}
      aria-pressed={selected}
      className={[
        'flex min-h-[52px] w-full items-center rounded-xl border px-4 py-3 text-start text-sm font-medium transition-all duration-fast',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2',
        selected
          ? 'border-accent-bronze bg-accent-bronze/10 text-accent-bronze'
          : 'border-border-subtle bg-surface-secondary text-ink-primary hover:border-accent-bronze/40 hover:bg-surface-primary',
      ].join(' ')}
    >
      <span
        className={[
          'me-3 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2',
          selected ? 'border-accent-bronze bg-accent-bronze' : 'border-border-emphasis',
        ].join(' ')}
        aria-hidden="true"
      >
        {selected && (
          <span className="block h-2 w-2 rounded-full bg-white" />
        )}
      </span>
      {option.label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Summary / results view
// ---------------------------------------------------------------------------

interface SummaryViewProps {
  instrument: InstrumentDefinition;
  score: number;
  responses: Record<number, number>;
  locale: string;
  submitError: string | null;
}

function SummaryView({
  instrument,
  score,
  responses,
  locale,
  submitError,
}: SummaryViewProps): React.ReactElement {
  const t = useTranslations();
  const dScore = displayScore(instrument, score);
  const dMax = displayMax(instrument);
  const band = getSeverityBand(instrument.id, dScore);
  const showSafety = phq9SafetyTriggered(instrument.id, responses);

  return (
    <div className="space-y-6">
      {/* Thank-you message */}
      <Card tone="calm" className="text-center">
        <p className="text-base font-medium text-ink-primary">
          {t('assessments.session.thankYou')}
        </p>
      </Card>

      {/* Score card */}
      <Card>
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-medium text-ink-tertiary">
              {t('assessments.session.severityLabel')}
            </span>
            {band && (
              <span className="clinical-number rounded-full bg-surface-tertiary px-3 py-0.5 text-sm font-semibold text-ink-primary">
                {band}
              </span>
            )}
          </div>

          {/* Score — always Latin digits */}
          <p className="text-3xl font-bold tabular-nums clinical-number text-ink-primary">
            {/* i18n interpolation not used here — we build the string directly to guarantee
                Latin digits regardless of locale. formatScoreWithMax enforces Latin digits. */}
            {t('assessments.session.yourScore', {
              score: formatNumberClinical(dScore),
              max: formatNumberClinical(dMax),
            })}
          </p>

          {/* WHO-5 note: display score is raw × 4 */}
          {instrument.id === 'who-5' && (
            <p className="text-xs text-ink-quaternary">
              Score shown as percentage (raw × 4). Range: 0–100.
            </p>
          )}

          {/* PSS-10 note: items 4, 5, 7, 8 are reverse-scored */}
          {instrument.id === 'pss-10' && (
            <p className="text-xs text-ink-quaternary">
              Items 4, 5, 7, and 8 are reverse-scored per Cohen et al. (1983).
            </p>
          )}
        </div>
      </Card>

      {/* PHQ-9 item 9 safety message — T4 path. Must always render if triggered. */}
      {showSafety && (
        <Card tone="crisis" role="alert" aria-live="assertive">
          <div className="space-y-3">
            <p className="text-base font-medium text-ink-primary">
              {t('assessments.session.safetyMessage')}
            </p>
            <a
              href={`/${locale}/crisis`}
              className="inline-flex items-center rounded-lg bg-signal-crisis px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-signal-crisis/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30"
            >
              {t('assessments.session.crisisLink')}
            </a>
          </div>
        </Card>
      )}

      {/* Submit error (if POST failed but we still show results) */}
      {submitError && (
        <p className="text-sm text-signal-crisis" role="alert">
          {t('assessments.session.submitError')}
        </p>
      )}

      {/* Clinical disclaimer — required by CLAUDE.md */}
      <aside
        className="rounded-xl border border-border-subtle bg-surface-primary px-5 py-4"
        role="note"
        aria-label="Clinical disclaimer"
      >
        <p className="text-xs leading-relaxed text-ink-tertiary">
          {t('assessments.session.clinicalDisclaimer')}
        </p>
      </aside>

      {/* Navigation */}
      <a
        href={`/${locale}/assessments`}
        className="inline-flex items-center text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:rounded"
      >
        &larr; {t('assessments.session.viewHistory')}
      </a>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Assessment session inner component (stateful)
// ---------------------------------------------------------------------------

interface SessionProps {
  instrument: InstrumentDefinition;
  locale: string;
}

type SessionPhase = 'questions' | 'submitting' | 'summary';

function AssessmentSession({ instrument, locale }: SessionProps): React.ReactElement {
  const t = useTranslations();
  const { getToken } = useAuth();

  // currentIndex is 0-based; questions are 1-based (item numbers).
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [responses, setResponses] = React.useState<Record<number, number>>({});
  const [phase, setPhase] = React.useState<SessionPhase>('questions');
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const [validationError, setValidationError] = React.useState(false);

  const questions = instrument.questions;
  const totalQuestions = questions.length;
  const currentQuestion = questions[currentIndex];

  if (!currentQuestion) {
    // Should never happen given generateStaticParams, but satisfy TypeScript.
    return <p>Invalid question index.</p>;
  }

  const currentItemNumber = currentQuestion.item;
  const selectedValue = responses[currentItemNumber];
  const hasAnswer = selectedValue !== undefined;
  const isLastQuestion = currentIndex === totalQuestions - 1;
  const options = getItemOptions(instrument, currentItemNumber);

  function handleSelect(value: number): void {
    setResponses((prev) => ({ ...prev, [currentItemNumber]: value }));
    setValidationError(false);
  }

  function handlePrevious(): void {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
      setValidationError(false);
    }
  }

  async function handleNext(): Promise<void> {
    if (!hasAnswer) {
      setValidationError(true);
      return;
    }
    if (!isLastQuestion) {
      setCurrentIndex((i) => i + 1);
      setValidationError(false);
      return;
    }
    // Last question — submit.
    await handleSubmit();
  }

  async function handleSubmit(): Promise<void> {
    setPhase('submitting');
    setSubmitError(null);

    const responsePayload = Object.entries(responses).map(([item, value]) => ({
      item: Number(item),
      value,
    }));

    try {
      // Skip API call in test / stub mode — avoids real network in Vitest / E2E stubs.
      const stubMode =
        process.env['NEXT_PUBLIC_USE_STUBS'] === 'true' ||
        process.env['NODE_ENV'] === 'test';

      if (!stubMode) {
        const token = await getToken();
        const baseUrl = (
          process.env['NEXT_PUBLIC_API_URL'] ??
          process.env['NEXT_PUBLIC_API_BASE_URL'] ??
          'http://localhost:8000'
        ).replace(/\/$/, '');

        const res = await fetch(`${baseUrl}/v1/assessments/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            instrument: instrument.id,
            responses: responsePayload,
          }),
        });

        if (!res.ok) {
          // Non-fatal: we still show client-computed results but flag the error.
          setSubmitError('submit_failed');
        }
      }
    } catch {
      setSubmitError('submit_failed');
    } finally {
      setPhase('summary');
    }
  }

  const finalScore = computeScore(instrument, responses);

  if (phase === 'summary') {
    return (
      <SummaryView
        instrument={instrument}
        score={finalScore}
        responses={responses}
        locale={locale}
        submitError={submitError}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress — Latin digit counter */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-medium text-ink-tertiary">
          <span className="clinical-number tabular-nums">
            {t('assessments.session.questionOf', {
              current: formatNumberClinical(currentIndex + 1),
              total: formatNumberClinical(totalQuestions),
            })}
          </span>
          <span className="clinical-number tabular-nums text-ink-quaternary">
            {formatNumberClinical(Math.round(((currentIndex) / totalQuestions) * 100))}%
          </span>
        </div>
        <ProgressBar current={currentIndex} total={totalQuestions} />
      </div>

      {/* Question card */}
      <Card>
        <p className="text-base font-medium leading-relaxed text-ink-primary">
          {currentQuestion.text}
        </p>
      </Card>

      {/* Response options */}
      <fieldset>
        <legend className="sr-only">
          {t('assessments.session.questionOf', {
            current: formatNumberClinical(currentIndex + 1),
            total: formatNumberClinical(totalQuestions),
          })}
          — {currentQuestion.text}
        </legend>
        <div className="space-y-2">
          {options.map((opt) => (
            <ResponseButton
              key={opt.value}
              option={opt}
              selected={selectedValue === opt.value}
              onSelect={handleSelect}
            />
          ))}
        </div>
      </fieldset>

      {/* Validation error */}
      {validationError && (
        <p className="text-sm text-signal-crisis" role="alert">
          {t('assessments.session.answerRequired')}
        </p>
      )}

      {/* Navigation */}
      <div className="flex gap-3">
        <Button
          variant="secondary"
          size="md"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          className="flex-1 min-h-[44px]"
        >
          {t('assessments.session.previous')}
        </Button>
        <Button
          variant="primary"
          size="md"
          loading={phase === 'submitting'}
          onClick={() => { void handleNext(); }}
          className="flex-1 min-h-[44px]"
        >
          {isLastQuestion
            ? t('assessments.session.submit')
            : t('assessments.session.next')}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page header — instrument name, description, estimated time
// ---------------------------------------------------------------------------

interface PageHeaderProps {
  instrument: InstrumentDefinition;
  locale: string;
}

function PageHeader({ instrument, locale }: PageHeaderProps): React.ReactElement {
  const t = useTranslations();

  return (
    <header className="space-y-3">
      {/* Back link */}
      <a
        href={`/${locale}/assessments`}
        className="inline-flex items-center text-sm text-ink-tertiary hover:text-ink-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:rounded"
      >
        &larr; {t('assessments.session.backToAssessments')}
      </a>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
          {instrument.fullName}
        </h1>
        <p className="mt-1 text-sm text-ink-tertiary">{instrument.description}</p>
        <p className="mt-1 text-xs text-ink-quaternary">
          {t('assessments.session.estimatedTime', {
            minutes: instrument.estimatedMinutes,
          })}
        </p>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Inner component — wraps header + session
// ---------------------------------------------------------------------------

function AssessmentInstrumentInner({
  instrumentId,
  locale,
}: {
  instrumentId: string;
  locale: string;
}): React.ReactElement {
  const instrument = INSTRUMENTS[instrumentId];

  // This is a client component, so notFound() must be called during render.
  // generateStaticParams handles the compile-time known set; this catches any
  // runtime navigations to unknown slugs.
  if (!instrument) {
    notFound();
  }

  return (
    <Layout locale={locale}>
      <div className="mx-auto max-w-xl space-y-6">
        <PageHeader instrument={instrument} locale={locale} />
        <AssessmentSession instrument={instrument} locale={locale} />
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function AssessmentInstrumentPage({
  params,
}: {
  params: Promise<{ locale: string; instrument: string }>;
}): React.JSX.Element {
  const { locale, instrument } = use(params);
  return <AssessmentInstrumentInner instrumentId={instrument} locale={locale} />;
}

/*
 * i18n keys used (all under assessments.session.*):
 *   assessments.session.questionOf          — "Question {current} of {total}"
 *   assessments.session.previous            — "Previous"
 *   assessments.session.next                — "Next"
 *   assessments.session.submit              — "Submit assessment"
 *   assessments.session.backToAssessments   — "Back to assessments"
 *   assessments.session.estimatedTime       — "About {minutes} min"
 *   assessments.session.thankYou            — "Thank you for completing this assessment."
 *   assessments.session.yourScore           — "Score: {score}/{max}"
 *   assessments.session.severityLabel       — "Severity"
 *   assessments.session.viewHistory         — "View full history"
 *   assessments.session.safetyMessage       — PHQ-9 item 9 safety message (T4 path)
 *   assessments.session.crisisLink          — "See crisis resources"
 *   assessments.session.clinicalDisclaimer  — Post-submission disclaimer
 *   assessments.session.submitting          — "Submitting…"
 *   assessments.session.submitError         — Error message on POST failure
 *   assessments.session.answerRequired      — Validation message
 */
