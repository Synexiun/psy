'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';
import { useLibraryCategory } from '@/hooks/useLibrary';

function LibraryCategoryInner({
  locale,
  categorySlug,
}: {
  locale: string;
  categorySlug: string;
}) {
  const t = useTranslations();
  const router = useRouter();
  const { category, isLoading } = useLibraryCategory(categorySlug);

  if (!category) {
    return (
      <Layout locale={locale}>
        <div className="space-y-6 max-w-2xl mx-auto">
          <p className="text-sm text-ink-tertiary">
            {isLoading ? '' : t('library.notFound')}
          </p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => router.push(`/${locale}/library`)}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.75}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
              aria-hidden="true"
            >
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
            {t('library.title')}
          </button>
        </nav>

        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t(`library.categories.${category.titleKey}`)}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">
            {t(`library.categories.${category.descriptionKey}`)}
          </p>
        </header>

        <section aria-labelledby="library-articles-heading">
          <h2
            id="library-articles-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('library.articlesHeading')}
          </h2>
          <div className="space-y-3">
            {category.articles.map((article) => (
              <a
                key={article.slug}
                href={`/${locale}/library/${categorySlug}/${article.slug}`}
                data-testid={`library-article-${article.slug}`}
                className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded-xl group"
              >
                <Card hover>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-ink-primary group-hover:text-accent-bronze transition-colors">
                        {t(`library.articles.${article.titleKey}`)}
                      </h3>
                      <p className="mt-0.5 text-xs leading-relaxed text-ink-tertiary line-clamp-2">
                        {t(`library.articles.${article.excerptKey}`)}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-ink-quaternary whitespace-nowrap">
                      {article.readingTimeMin} {t('library.readingTime')}
                    </span>
                  </div>
                </Card>
              </a>
            ))}
          </div>
        </section>
      </div>
    </Layout>
  );
}

export default function LibraryCategoryPage({
  params,
}: {
  params: Promise<{ locale: string; category: string }>;
}): React.JSX.Element {
  const { locale, category } = use(params);
  return <LibraryCategoryInner locale={locale} categorySlug={category} />;
}
