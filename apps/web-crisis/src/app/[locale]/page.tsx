import { notFound } from 'next/navigation';
import { allEntries, resolveEntry } from '@disciplineos/safety-directory';
import { COPY, isCrisisLocale, SUPPORTED_LOCALES, type CrisisLocale } from '@/lib/locale';

export function generateStaticParams() {
  return SUPPORTED_LOCALES.map((locale) => ({ locale }));
}

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
            className="rounded-xl border border-[hsl(0,84%,60%)]/20 bg-[hsl(0,84%,97%)] p-5"
          >
            <h2 className="text-sm font-medium uppercase tracking-wide text-[hsl(0,84%,40%)]">
              {entry.country}
            </h2>

            <a
              href={`tel:${sanitizeTel(entry.emergency.number)}`}
              className="mt-2 flex min-h-[56px] items-center justify-center rounded-xl bg-[hsl(0,84%,60%)] px-6 text-lg font-medium text-white hover:bg-[hsl(0,84%,54%)]"
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
                        className="inline-flex min-h-[44px] items-center rounded-md bg-[hsl(0,84%,60%)] px-4 text-white hover:bg-[hsl(0,84%,54%)]"
                        data-analytics-event="crisis_call_hotline"
                        data-hotline-id={h.id}
                      >
                        {copy.callHotline} · {h.number}
                      </a>
                    )}
                    {h.sms && (
                      <a
                        href={smsHref(h.sms)}
                        className="inline-flex min-h-[44px] items-center rounded-md border border-[hsl(0,84%,60%)] px-4 text-[hsl(0,84%,40%)]"
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

      <hr className="my-10 border-[hsl(220,14%,90%)]" />

      <p className="text-sm text-[hsl(215,16%,47%)]">
        <a href="/" className="underline">
          {copy.backToApp}
        </a>
      </p>

      <footer className="mt-10 text-xs text-[hsl(215,16%,47%)]">
        Last verified {mostRecentVerification(visible)}.
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
