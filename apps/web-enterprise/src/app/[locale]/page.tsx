import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';

export default async function EnterpriseDashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <EnterpriseDashboard />;
}

function EnterpriseDashboard() {
  const t = useTranslations();
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="border-b pb-6">
        <h1 className="text-2xl font-semibold">{t('app.name')} · Enterprise</h1>
        <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
          Organization-level aggregate view. Individual user data is never visible in this portal.
        </p>
      </header>

      <div className="mt-6 rounded-md border border-[hsl(38,92%,50%)]/30 bg-[hsl(38,92%,97%)] p-4 text-sm">
        <strong>Privacy floor:</strong> any cohort smaller than 5 people is suppressed — charts
        will show "insufficient data" rather than exact counts. This is enforced in the database,
        not in this app.
      </div>

      <section aria-labelledby="engagement" className="mt-10 grid gap-6 md:grid-cols-3">
        <article className="rounded-xl border bg-white p-5">
          <h2 id="engagement" className="text-sm font-medium text-[hsl(215,16%,47%)]">
            Active members (7d)
          </h2>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </article>
        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-sm font-medium text-[hsl(215,16%,47%)]">Tools used (7d)</h2>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </article>
        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-sm font-medium text-[hsl(215,16%,47%)]">Org wellbeing index</h2>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </article>
      </section>
    </main>
  );
}
