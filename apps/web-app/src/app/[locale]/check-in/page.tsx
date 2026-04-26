'use client';

import { use, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@clerk/nextjs';
import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import { Layout } from '@/components/Layout';
import { Button, Card } from '@/components/primitives';
import { submitCheckIn } from '@/lib/api';

// Non-display constants (not i18n strings)
const COPY = {
  notesMaxChars: 280,
} as const;

// Trigger keys map to checkIn.triggers.* in the catalog
type TriggerKey =
  | 'stress'
  | 'boredom'
  | 'socialPressure'
  | 'loneliness'
  | 'anger'
  | 'anxiety'
  | 'celebration'
  | 'fatigue';

const TRIGGER_KEYS: TriggerKey[] = [
  'stress',
  'boredom',
  'socialPressure',
  'loneliness',
  'anger',
  'anxiety',
  'celebration',
  'fatigue',
];

type TriggerTag = TriggerKey;

// Map intensity value (0-10) to a colour for the track fill
function intensityColor(value: number): string {
  if (value <= 3) return 'var(--color-signal-stable)';
  if (value <= 6) return 'var(--color-accent-bronze)';
  return 'var(--color-signal-crisis)';
}

// ---------------------------------------------------------------------------
// Inner component (all interactivity lives here)
// ---------------------------------------------------------------------------

const USE_STUBS = process.env['NEXT_PUBLIC_USE_STUBS'] === 'true';

function CheckInInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { getToken } = useAuth();

  const [intensity, setIntensity] = useState(0);
  const [selectedTriggers, setSelectedTriggers] = useState<Set<TriggerTag>>(new Set());
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function toggleTrigger(tag: TriggerTag) {
    setSelectedTriggers((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (USE_STUBS) {
        await new Promise((r) => setTimeout(r, 600));
      } else {
        const token = await getToken();
        if (token) {
          await submitCheckIn(token, intensity, Array.from(selectedTriggers), notes || undefined);
        }
      }
      setSubmitted(true);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleReset() {
    setIntensity(0);
    setSelectedTriggers(new Set());
    setNotes('');
    setSubmitted(false);
  }

  const charsLeft = COPY.notesMaxChars - notes.length;
  const trackFill = (intensity / 10) * 100;

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('checkIn.title')}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">{t('checkIn.pageSubtitle')}</p>
        </header>

        {/* Crisis shortcut -- always visible per spec */}
        <div className="flex justify-end">
          <a
            href={`/${locale}/crisis`}
            className="text-xs font-medium text-signal-crisis underline underline-offset-2 hover:text-signal-crisis focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30 rounded"
          >
            {t('checkIn.needHelp')}
          </a>
        </div>

        {submitted ? (
          /* Post-submit compassion card */
          <Card tone="calm" className="text-center py-10 space-y-4">
            <p className="text-4xl" aria-hidden="true">{'🌊'}</p>
            <h2 className="text-lg font-semibold text-ink-primary">{t('checkIn.compassionHeadline')}</h2>
            <p className="text-sm leading-relaxed text-ink-secondary max-w-sm mx-auto">
              {t('checkIn.compassionBody')}
            </p>
            <div className="flex flex-col items-center gap-3 pt-2">
              <Button
                variant="calm"
                size="md"
                className="min-h-[44px]"
                onClick={() => {
                  window.location.href = `/${locale}/tools`;
                }}
              >
                {t('checkIn.openTool')}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="min-h-[44px]"
                onClick={handleReset}
              >
                {t('checkIn.logAnother')}
              </Button>
            </div>
          </Card>
        ) : (
          /* Check-in form */
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Intensity slider */}
            <Card>
              <fieldset>
                <legend className="text-sm font-medium text-ink-primary">
                  {t('app.urge.intensityLabel')}
                </legend>
                <div className="mt-4 space-y-3">
                  <div className="relative">
                    <input
                      type="range"
                      min={0}
                      max={10}
                      step={1}
                      value={intensity}
                      onChange={(e) => setIntensity(Number(e.target.value))}
                      aria-label={t('app.urge.intensityLabel')}
                      aria-valuemin={0}
                      aria-valuemax={10}
                      aria-valuenow={intensity}
                      className="clinical-number w-full h-2 rounded-full appearance-none cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
                      style={{
                        background: `linear-gradient(to right, ${intensityColor(intensity)} ${trackFill}%, var(--color-surface-tertiary) ${trackFill}%)`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-ink-quaternary">
                    <span>{t('app.urge.intensityScaleMin')}</span>
                    <span
                      className="text-base font-bold tabular-nums"
                      style={{ color: intensityColor(intensity) }}
                      aria-live="polite"
                    >
                      {formatNumberClinical(intensity)}
                    </span>
                    <span>{t('app.urge.intensityScaleMax')}</span>
                  </div>
                </div>
              </fieldset>
            </Card>

            {/* Trigger tags */}
            <Card>
              <fieldset>
                <legend className="text-sm font-medium text-ink-primary">
                  {t('checkIn.triggersLabel')}
                </legend>
                <div
                  className="mt-3 flex flex-wrap gap-2"
                  role="group"
                  aria-label={t('checkIn.triggersLabel')}
                >
                  {TRIGGER_KEYS.map((key) => {
                    const active = selectedTriggers.has(key);
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => toggleTrigger(key)}
                        aria-pressed={active}
                        className={`min-h-[44px] rounded-full px-4 py-2 text-sm font-medium transition-all duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 ${
                          active
                            ? 'bg-accent-bronze text-white shadow-sm'
                            : 'bg-surface-tertiary text-ink-secondary hover:bg-border-subtle border border-border-subtle'
                        }`}
                      >
                        {t(`checkIn.triggers.${key}`)}
                      </button>
                    );
                  })}
                </div>
              </fieldset>
            </Card>

            {/* Notes */}
            <Card>
              <label
                htmlFor="checkin-notes"
                className="block text-sm font-medium text-ink-primary"
              >
                {t('checkIn.notesLabel')}
              </label>
              <textarea
                id="checkin-notes"
                value={notes}
                onChange={(e) => {
                  if (e.target.value.length <= COPY.notesMaxChars) {
                    setNotes(e.target.value);
                  }
                }}
                placeholder={t('checkIn.notesPlaceholder')}
                rows={3}
                maxLength={COPY.notesMaxChars}
                className="mt-2 w-full resize-none rounded-lg border border-border-subtle bg-surface-primary px-3 py-2.5 text-sm text-ink-primary placeholder-ink-quaternary focus:border-accent-bronze focus:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-accent-bronze/30 transition-colors"
              />
              <p
                className={`mt-1 text-end text-xs ${charsLeft < 30 ? 'text-signal-warning' : 'text-ink-quaternary'}`}
                aria-live="polite"
              >
                {charsLeft} chars left
              </p>
            </Card>

            {/* Submit */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={isSubmitting}
              className="w-full min-h-[44px]"
            >
              {t('checkIn.submit')}
            </Button>
          </form>
        )}
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function CheckInPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <CheckInInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   app.urge.intensityLabel
 *   app.urge.intensityScaleMin
 *   app.urge.intensityScaleMax
 *   checkIn.title
 *   checkIn.pageSubtitle
 *   checkIn.triggersLabel
 *   checkIn.notesLabel
 *   checkIn.notesPlaceholder
 *   checkIn.submit
 *   checkIn.compassionHeadline
 *   checkIn.compassionBody
 *   checkIn.copingPrompt
 *   checkIn.openTool
 *   checkIn.logAnother
 *   checkIn.needHelp
 *   checkIn.triggers.stress / .boredom / .socialPressure / .loneliness / .anger / .anxiety / .celebration / .fatigue
 */
