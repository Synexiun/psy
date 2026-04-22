import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';
import { buildButtonClasses } from '@disciplineos/design-system/primitives/web';

export default function MarketingHomePage({ params }: { params: Promise<{ locale: string }> }): React.JSX.Element {
  return <HomeContent paramsPromise={params} />;
}

async function HomeContent({ paramsPromise }: { paramsPromise: Promise<{ locale: string }> }) {
  const { locale } = await paramsPromise;
  setRequestLocale(locale);
  return <HomeInner />;
}

function HomeInner() {
  const t = useTranslations();

  return (
    <main className="mx-auto max-w-5xl px-6 py-16 md:py-24">
      <section aria-labelledby="hero" className="space-y-6">
        <p className="text-sm font-medium uppercase tracking-wide text-[hsl(217,91%,52%)]">
          {t('app.name')}
        </p>
        <h1
          id="hero"
          className="text-4xl font-semibold leading-tight md:text-5xl md:leading-tight"
        >
          {t('marketing.hero.headline')}
        </h1>
        <p className="max-w-2xl text-lg text-[hsl(215,16%,47%)]">{t('marketing.hero.sub')}</p>
        <div className="flex flex-wrap gap-3 pt-2">
          <a href="#download" className={buildButtonClasses('primary', 'lg')}>
            {t('marketing.hero.ctaPrimary')}
          </a>
          <a href="#how-it-works" className={buildButtonClasses('ghost', 'lg')}>
            {t('marketing.hero.ctaSecondary')}
          </a>
        </div>
      </section>

      <section
        aria-labelledby="crisis-promise"
        className="mt-20 rounded-2xl border border-[hsl(0,84%,60%)]/20 bg-[hsl(0,84%,97%)] p-8"
      >
        <h2 id="crisis-promise" className="text-xl font-semibold text-[hsl(0,84%,30%)]">
          {t('crisis.headline')}
        </h2>
        <p className="mt-2 text-[hsl(222,47%,11%)]">{t('crisis.body')}</p>
        <a
          href="/crisis"
          className={`${buildButtonClasses('crisis', 'crisis')} mt-6 max-w-md`}
          data-analytics-event="crisis_cta_click"
        >
          {t('crisis.cta.primary')}
        </a>
      </section>

      <section id="how-it-works" aria-labelledby="how-heading" className="mt-20 space-y-4">
        <h2 id="how-heading" className="text-2xl font-semibold">
          {t('nav.help')}
        </h2>
        <p className="max-w-2xl text-[hsl(215,16%,47%)]">{t('app.welcome.body')}</p>
      </section>
    </main>
  );
}
