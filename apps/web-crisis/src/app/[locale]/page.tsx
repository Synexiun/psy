import { notFound } from 'next/navigation';
import { allEntries, resolveEntry } from '@disciplineos/safety-directory';
import { COPY, isCrisisLocale, SUPPORTED_LOCALES, type CrisisLocale } from '@/lib/locale';

export function generateStaticParams() {
  return SUPPORTED_LOCALES.map((locale) => ({ locale }));
}

import React from 'react';

/**
 * Inline coping tool content for the crisis surface.
 *
 * These strings are intentionally NOT sourced from the i18n-catalog — this surface
 * must function with zero runtime dependencies. Tools are shown in English for all
 * locales until clinical translator review is complete for ar/fa.
 *
 * TODO: clinical translator review needed for ar/fa before localising these strings.
 * When ready, move into locale.ts COPY dict under the same locale-review gate.
 */
interface CopingTool {
  name: string;
  duration: string;
  steps: string[];
}

const TOOLS: ReadonlyArray<CopingTool> = Object.freeze([
  {
    name: 'Box Breathing',
    duration: '2 min',
    steps: [
      'Breathe in for 4 counts.',
      'Hold for 4 counts.',
      'Breathe out for 4 counts.',
      'Hold for 4 counts.',
      'Repeat 4 times.',
    ],
  },
  {
    name: '5-4-3-2-1 Grounding',
    duration: '3 min',
    steps: [
      'Name 5 things you can see.',
      'Name 4 things you can touch.',
      'Name 3 things you can hear.',
      'Name 2 things you can smell.',
      'Name 1 thing you can taste.',
    ],
  },
  {
    name: 'Cold Water',
    duration: '1 min',
    steps: [
      'Splash cold water on your face, or hold ice cubes in your hands.',
      'This activates your body\'s natural calming response.',
    ],
  },
]);

export default async function CrisisLocalePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isCrisisLocale(locale)) notFound();
  return <CrisisIndex locale={locale} />;
}

function CrisisIndex({ locale }: { locale: CrisisLocale }) {
  const copy = COPY[locale];
  const entriesForLocale = allEntries.filter((e) => e.locale === locale);
  const fallback = resolveEntry(null, locale);

  const visible = entriesForLocale.length > 0 ? entriesForLocale : [fallback];

  return (
    <main className="mx-auto max-w-2xl px-5 py-8">
      <h1 className="text-3xl font-semibold leading-tight">{copy.headline}</h1>
      <p className="mt-3 text-lg text-[hsl(215,16%,47%)]">{copy.body}</p>

      <ul className="mt-8 space-y-6">
        {visible.map((entry) => (
          <li
            key={`${entry.country}-${entry.locale}`}
            className="rounded-xl border border-crisis-500/20 bg-[hsl(0,84%,97%)] p-5"
          >
            <h2 className="text-sm font-medium uppercase tracking-wide text-crisis-600">
              {entry.country}
            </h2>

            <a
              href={`tel:${sanitizeTel(entry.emergency.number)}`}
              className="mt-2 flex min-h-[56px] items-center justify-center rounded-xl bg-crisis-500 px-6 text-lg font-medium text-white hover:bg-crisis-600"
              aria-label={`${copy.callEmergency} ${entry.emergency.label} ${entry.emergency.number}`}
              data-analytics-event="crisis_call_emergency"
              data-country={entry.country}
            >
              {copy.callEmergency} · {entry.emergency.label} · {entry.emergency.number}
            </a>

            <ul className="mt-4 space-y-3">
              {entry.hotlines.map((h) => (
                <li key={h.id} className="rounded-lg border border-white bg-white p-4">
                  <p className="font-medium">{h.name}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {h.number && (
                      <a
                        href={`tel:${sanitizeTel(h.number)}`}
                        className="inline-flex min-h-[44px] items-center rounded-md bg-crisis-500 px-4 text-white hover:bg-crisis-600"
                        data-analytics-event="crisis_call_hotline"
                        data-hotline-id={h.id}
                      >
                        {copy.callHotline} · {h.number}
                      </a>
                    )}
                    {h.sms && (
                      <a
                        href={smsHref(h.sms)}
                        className="inline-flex min-h-[44px] items-center rounded-md border border-crisis-500 px-4 text-crisis-600"
                      >
                        {copy.smsLabel}: {h.sms}
                      </a>
                    )}
                    {h.web && (
                      <a
                        href={h.web}
                        className="inline-flex min-h-[44px] items-center rounded-md border px-4"
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        {copy.webLabel}
                      </a>
                    )}
                  </div>
                  <p className="mt-2 text-xs text-[hsl(215,16%,47%)]">
                    {copy.hours}: {h.hours} · {h.cost === 'free' ? copy.free : h.cost}
                  </p>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>

      {/* ── Coping tools divider ── */}
      <hr className="my-10 border-[hsl(220,14%,90%)]" />

      {/* ── Coping tools section ── */}
      <section aria-labelledby="coping-tools-heading">
        <h2
          id="coping-tools-heading"
          className="text-lg font-semibold text-[hsl(222,47%,11%)]"
        >
          {copy.orTry}
        </h2>
        <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
          While you wait for help to connect.
        </p>

        <ul className="mt-4 space-y-3">
          {TOOLS.map((tool) => (
            <li key={tool.name}>
              {/*
               * <details>/<summary> gives JS-free expand/collapse in all
               * modern browsers and degrades gracefully (shows all content)
               * when JS is disabled or the UA does not support it.
               */}
              <details className="rounded-xl border border-[hsl(220,14%,90%)] bg-white">
                <summary className="flex cursor-pointer select-none items-center justify-between rounded-xl px-5 py-4 font-medium hover:bg-[hsl(220,14%,97%)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-crisis-500">
                  <span>{tool.name}</span>
                  <span className="text-xs font-normal text-[hsl(215,16%,47%)]">
                    {tool.duration}
                  </span>
                </summary>
                <ol className="space-y-1 px-5 pb-5 pt-2 text-sm leading-relaxed text-[hsl(222,47%,11%)]">
                  {tool.steps.map((step, i) => (
                    <li key={i} className="flex gap-2">
                      <span
                        className="clinical-number mt-0.5 shrink-0 text-xs font-medium text-[hsl(215,16%,47%)]"
                        aria-hidden="true"
                      >
                        {i + 1}.
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </details>
            </li>
          ))}
        </ul>
      </section>

      <hr className="my-10 border-[hsl(220,14%,90%)]" />

      <p className="text-sm text-[hsl(215,16%,47%)]">
        <a href="/" className="underline">
          {copy.backToApp}
        </a>
      </p>

      <footer className="mt-10 text-xs text-[hsl(215,16%,47%)]">
        Last verified{' '}
        <time dateTime={mostRecentVerification(visible)}>
          {mostRecentVerification(visible)}
        </time>
        .
      </footer>
    </main>
  );
}

/** Strip formatting so `tel:` links work across countries. */
function sanitizeTel(n: string): string {
  return n.replace(/[^\d+]/g, '');
}

function smsHref(sms: string): string {
  const m = sms.match(/(\d+)/);
  return m ? `sms:${m[1]}` : '#';
}

function mostRecentVerification(entries: ReadonlyArray<{ hotlines: ReadonlyArray<{ verifiedAt: string }> }>): string {
  const all = entries.flatMap((e) => e.hotlines.map((h) => h.verifiedAt));
  if (all.length === 0) return '—';
  const max = all.reduce((a, b) => (a > b ? a : b));
  return max;
}
