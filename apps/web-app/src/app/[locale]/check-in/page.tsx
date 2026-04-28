'use client';

import * as React from 'react';
import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth } from '@clerk/nextjs';
import { Layout } from '@/components/Layout';
import { Button, Card } from '@disciplineos/design-system';
import { UrgeSlider } from '@disciplineos/design-system/clinical/UrgeSlider';
import { submitCheckIn } from '@/lib/api';
import { useOfflineQueue } from '@/hooks/useOfflineQueue';
import { usePhiAudit } from '@/hooks/usePhiAudit';

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

// ---------------------------------------------------------------------------
// Inner component (all interactivity lives here)
// ---------------------------------------------------------------------------

const USE_STUBS = process.env['NEXT_PUBLIC_USE_STUBS'] === 'true';

function CheckInInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { getToken } = useAuth();
  const router = useRouter();
  usePhiAudit('/check-in');

  const [intensity, setIntensity] = useState(0);
  const [selectedTriggers, setSelectedTriggers] = useState<Set<TriggerTag>>(new Set());
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [offlineQueued, setOfflineQueued] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { enqueue, queuedCount } = useOfflineQueue();

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

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      if (USE_STUBS) {
        await new Promise((r) => setTimeout(r, 600));
      } else {
        const token = await getToken();
        if (!token) throw new Error(t('errors.sessionExpired'));
        await submitCheckIn(token, intensity, Array.from(selectedTriggers), notes || undefined);
      }
      setSubmitted(true);
    } catch (err) {
      const isOffline =
        !navigator.onLine ||
        (err instanceof TypeError && err.message.toLowerCase().includes('fetch'));
      if (isOffline) {
        try {
          await enqueue({
            intensity,
            triggerTags: Array.from(selectedTriggers),
            notes: notes || undefined,
          });
          setOfflineQueued(true);
          setSubmitted(true);
        } catch {
          setSubmitError(err instanceof Error ? err.message : t('errors.submitFailed'));
        }
      } else {
        setSubmitError(err instanceof Error ? err.message : t('errors.submitFailed'));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleReset() {
    setIntensity(0);
    setSelectedTriggers(new Set());
    setNotes('');
    setSubmitted(false);
    setOfflineQueued(false);
    setSubmitError(null);
  }

  const charsLeft = COPY.notesMaxChars - notes.length;

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
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <path d="M4 32c4-8 8-8 12 0s8 8 12 0 8-8 12 0" stroke="var(--color-signal-stable)" strokeWidth="3" strokeLinecap="round"/>
            </svg>
            <h2 className="text-lg font-semibold text-ink-primary">{t('checkIn.compassionHeadline')}</h2>
            {offlineQueued ? (
              <p
                data-testid="submit-offline-queued"
                className="text-sm leading-relaxed text-ink-secondary max-w-sm mx-auto"
              >
                {t('checkIn.offlineSaved')}
              </p>
            ) : (
              <p className="text-sm leading-relaxed text-ink-secondary max-w-sm mx-auto">
                {t('checkIn.compassionBody')}
              </p>
            )}
            <div className="flex flex-col items-center gap-3 pt-2">
              <Button
                variant="calm"
                size="md"
                className="min-h-[44px]"
                onClick={() => router.push(`/${locale}/tools`)}
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
            {/* Error banner — shown when session token is null or submit fails */}
            {submitError && (
              <div role="alert" className="rounded-lg border border-signal-crisis/30 bg-signal-crisis/10 px-4 py-3 text-sm text-signal-crisis">
                {submitError}
              </div>
            )}
            {/* Intensity slider */}
            <Card>
              <fieldset>
                <legend className="text-sm font-medium text-ink-primary">
                  {t('app.urge.intensityLabel')}
                </legend>
                <div className="mt-4">
                  <UrgeSlider
                    value={intensity}
                    onValueChange={setIntensity}
                    ariaLabel={t('app.urge.intensityLabel')}
                  />
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
                {t('checkIn.charsLeft', { count: charsLeft })}
              </p>
            </Card>

            {/* Offline queue badge */}
            {queuedCount > 0 && (
              <p data-testid="check-in-queue-badge" className="text-xs text-ink-tertiary text-center">
                {t('checkIn.offlineQueue', { count: queuedCount })}
              </p>
            )}

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
 *   checkIn.offlineQueue
 *   checkIn.offlineSaved
 *   checkIn.triggers.stress / .boredom / .socialPressure / .loneliness / .anger / .anxiety / .celebration / .fatigue
 */
