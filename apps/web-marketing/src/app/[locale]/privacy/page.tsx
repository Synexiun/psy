import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';

export default function PrivacyPage({ params }: { params: Promise<{ locale: string }> }): React.JSX.Element {
  return <PrivacyContent paramsPromise={params} />;
}

async function PrivacyContent({ paramsPromise }: { paramsPromise: Promise<{ locale: string }> }) {
  const { locale } = await paramsPromise;
  setRequestLocale(locale);
  return <PrivacyInner />;
}

function PrivacyInner() {
  const t = useTranslations();
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold">{t('privacy.headline')}</h1>
      <p className="mt-4 text-[hsl(215,16%,47%)]">{t('privacy.body')}</p>
    </main>
  );
}
