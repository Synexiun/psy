import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';

export default async function ClinicianHomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <ClinicianHome />;
}

function ClinicianHome() {
  const t = useTranslations();
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="flex items-baseline justify-between border-b pb-4">
        <div>
          <h1 className="text-2xl font-semibold">{t('app.name')} · Clinician</h1>
          <p className="text-sm text-[hsl(215,16%,47%)]">
            {t('app.welcome.body')}
          </p>
        </div>
      </header>

      <section aria-labelledby="clients-heading" className="mt-8">
        <h2 id="clients-heading" className="text-lg font-medium">
          Clients
        </h2>
        <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
          Only clients who have actively opted into sharing appear here. Re-authentication
          is required before any individual-level view.
        </p>
        <div className="mt-4 rounded-lg border bg-white p-6 text-sm text-[hsl(215,16%,47%)]">
          No shared clients yet.
        </div>
      </section>
    </main>
  );
}
