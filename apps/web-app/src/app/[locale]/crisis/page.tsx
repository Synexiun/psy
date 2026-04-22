import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';
import { resolveEntry, type Locale as SafetyLocale } from '@disciplineos/safety-directory';
import { type Locale } from '@disciplineos/i18n-catalog';

export default async function CrisisPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<React.JSX.Element> {
  const { locale } = await params;
  setRequestLocale(locale);
  return <CrisisContent locale={locale as Locale} />;
}

function CrisisContent({ locale }: { locale: Locale }) {
  const t = useTranslations('crisis');
  const entry = resolveEntry(null, locale as SafetyLocale);

  return (
    <main className="mx-auto max-w-2xl px-5 py-8" lang={locale}>
      <h1 className="text-2xl font-semibold">{t('headline')}</h1>
      <p className="mt-2 text-[hsl(215,16%,47%)]">{t('body')}</p>

      <section aria-labelledby="emergency" className="mt-8">
        <h2 id="emergency" className="text-lg font-medium">
          {t('callLocal')}
        </h2>
        <a
          href={`tel:${entry.emergency.number}`}
          className="mt-2 inline-block rounded-lg bg-[hsl(0,72%,47%)] px-4 py-3 font-medium text-white hover:bg-[hsl(0,72%,40%)]"
        >
          {entry.emergency.label} — {entry.emergency.number}
        </a>
      </section>

      <section aria-labelledby="hotlines" className="mt-8">
        <h2 id="hotlines" className="text-lg font-medium">
          {t('callHotline')}
        </h2>
        <ul className="mt-3 space-y-3">
          {entry.hotlines.map((h) => (
            <li key={h.id} className="rounded-lg border p-4">
              <p className="font-medium">{h.name}</p>
              <p className="text-sm text-[hsl(215,16%,47%)]">{h.hours}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {h.number && (
                  <a
                    href={`tel:${h.number}`}
                    className="inline-block rounded-md bg-[hsl(217,91%,52%)] px-3 py-2 text-sm font-medium text-white hover:bg-[hsl(217,91%,42%)]"
                  >
                    {h.number}
                  </a>
                )}
                {h.sms && (
                  <a
                    href={`sms:${h.sms}`}
                    className="inline-block rounded-md border px-3 py-2 text-sm font-medium hover:bg-[hsl(0,0%,96%)]"
                  >
                    SMS
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <footer className="mt-10 text-xs text-[hsl(215,16%,47%)]">
        Last verified: {entry.hotlines[0]?.verifiedAt ?? '—'}
      </footer>
    </main>
  );
}
