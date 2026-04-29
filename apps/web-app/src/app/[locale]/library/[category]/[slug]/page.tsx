'use client';

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card } from '@disciplineos/design-system';
import { useLibraryArticle } from '@/hooks/useLibrary';
import { BackBreadcrumb } from '@/components/BackBreadcrumb';

function LibraryArticleInner({
  locale,
  categorySlug,
  articleSlug,
}: {
  locale: string;
  categorySlug: string;
  articleSlug: string;
}) {
  const t = useTranslations();
  const { article, category, isLoading } = useLibraryArticle(categorySlug, articleSlug);

  if (!article || !category) {
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
      <div className="space-y-6 max-w-2xl mx-auto">
        <BackBreadcrumb
          label={t(`library.categories.${category.titleKey}`)}
          href={`/${locale}/library/${categorySlug}`}
        />

        {/* Article header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t(`library.articles.${article.titleKey}`)}
          </h1>
          <p className="mt-1 text-sm text-ink-quaternary">
            {article.readingTimeMin} {t('library.readingTime')}
          </p>
        </header>

        {/* Article body */}
        <Card>
          <p className="text-sm leading-relaxed text-ink-secondary whitespace-pre-wrap">
            {t(`library.articles.${article.bodyKey}`)}
          </p>
        </Card>

        {/* Crisis footer */}
        <footer className="pt-2 text-center">
          <a
            href={`/${locale}/crisis`}
            className="text-xs text-ink-quaternary hover:text-signal-crisis transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30 rounded"
          >
            {t('checkIn.needHelp')}
          </a>
        </footer>
      </div>
    </Layout>
  );
}

export default function LibraryArticlePage({
  params,
}: {
  params: Promise<{ locale: string; category: string; slug: string }>;
}): React.JSX.Element {
  const { locale, category, slug } = use(params);
  return <LibraryArticleInner locale={locale} categorySlug={category} articleSlug={slug} />;
}
