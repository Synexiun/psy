'use client';

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';
import { useLibraryCategories } from '@/hooks/useLibrary';

function LibraryInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { categories } = useLibraryCategories();

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('library.title')}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">{t('library.subtitle')}</p>
        </header>

        <section aria-labelledby="library-categories-heading">
          <h2
            id="library-categories-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('library.categoriesHeading')}
          </h2>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {categories.map((category) => (
              <a
                key={category.slug}
                href={`/${locale}/library/${category.slug}`}
                data-testid={`library-category-${category.slug}`}
                className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded-xl group"
                aria-label={t(`library.categories.${category.titleKey}`)}
              >
                <Card hover className="h-full">
                  <h3 className="text-sm font-semibold text-ink-primary group-hover:text-accent-bronze transition-colors">
                    {t(`library.categories.${category.titleKey}`)}
                  </h3>
                  <p className="mt-1 text-xs leading-relaxed text-ink-tertiary line-clamp-2">
                    {t(`library.categories.${category.descriptionKey}`)}
                  </p>
                  <p className="mt-2 text-xs text-ink-quaternary">
                    {category.articleCount} {t('library.readingTime')}
                  </p>
                </Card>
              </a>
            ))}
          </div>
        </section>
      </div>
    </Layout>
  );
}

export default function LibraryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <LibraryInner locale={locale} />;
}
