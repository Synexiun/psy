import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';

export default function SafetyPage({ params }: { params: Promise<{ locale: string }> }): React.JSX.Element {
  return <SafetyContent paramsPromise={params} />;
}

async function SafetyContent({ paramsPromise }: { paramsPromise: Promise<{ locale: string }> }) {
  const { locale } = await paramsPromise;
  setRequestLocale(locale);
  return <SafetyInner />;
}

function SafetyInner() {
  const t = useTranslations();
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold">{t('safety.headline')}</h1>
      <p className="mt-4 text-[hsl(215,16%,47%)]">{t('safety.body')}</p>
      <a href="/crisis" className="mt-6 inline-block underline">
        {t('crisis.cta.primary')}
      </a>
    </main>
  );
}
