'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@clerk/nextjs';
import { buildButtonClasses } from '@disciplineos/design-system/primitives/web';

export default function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  // params is read but not awaited in client component; Next.js injects it
  const { locale } = params as unknown as { locale: string };
  return <DashboardInner locale={locale} />;
}

function DashboardInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { isSignedIn } = useAuth();

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

      {!isSignedIn && (
        <p className="mt-6 text-sm text-[hsl(215,16%,47%)]">
          {t('nav.signIn')} · {t('nav.signOut')}
        </p>
      )}
    </main>
  );
}
