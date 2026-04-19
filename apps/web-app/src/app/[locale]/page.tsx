import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';
import { auth } from '@clerk/nextjs/server';
import { buildButtonClasses } from '@disciplineos/design-system/primitives/web';

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { userId } = await auth();
  return <DashboardInner signedIn={Boolean(userId)} locale={locale} />;
}

function DashboardInner({ signedIn, locale }: { signedIn: boolean; locale: string }) {
  const t = useTranslations();

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t('app.welcome.title')}</h1>
        <a
          href={`/${locale}/crisis`}
          className={buildButtonClasses('crisis', 'md')}
          data-analytics-event="crisis_cta_click"
        >
          {t('crisis.cta.primary')}
        </a>
      </header>

      <p className="mt-3 text-[hsl(215,16%,47%)]">{t('app.welcome.body')}</p>

      <section aria-labelledby="check-in" className="mt-8 rounded-xl border bg-white p-6 shadow-sm">
        <h2 id="check-in" className="text-lg font-medium">
          {t('app.urge.intensityLabel')}
        </h2>
        <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
          {t('app.urge.intensityScaleMin')} → {t('app.urge.intensityScaleMax')}
        </p>
      </section>

      {!signedIn && (
        <p className="mt-6 text-sm text-[hsl(215,16%,47%)]">
          {t('nav.signIn')} · {t('nav.signOut')}
        </p>
      )}
    </main>
  );
}
