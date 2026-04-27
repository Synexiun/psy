'use client';

import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card, Badge } from '@disciplineos/design-system';

// ---------------------------------------------------------------------------
// Tool catalogue — entirely static / deterministic. No API call, works offline.
// Every tool must have a deterministic fallback per CLAUDE.md.
// ---------------------------------------------------------------------------

type ToolCategory = 'breathing' | 'grounding' | 'body' | 'mindfulness';
type ToolCatalogKey = 'boxBreathing' | 'grounding54321' | 'pmr' | 'coldWater' | 'urgeSurfing' | 'stopTechnique' | 'compassionMeditation' | 'delayDistract';

interface CopingTool {
  id: string;
  /** Key into tools.items.* in the i18n catalog */
  catalogKey: ToolCatalogKey;
  /** Key into tools.categories.* in the i18n catalog */
  category: ToolCategory;
  featured?: boolean;
}

const TOOLS: CopingTool[] = [
  {
    id: 'box-breathing',
    catalogKey: 'boxBreathing',
    category: 'breathing',
    featured: true,
  },
  {
    id: '5-4-3-2-1-grounding',
    catalogKey: 'grounding54321',
    category: 'grounding',
  },
  {
    id: 'progressive-muscle-relaxation',
    catalogKey: 'pmr',
    category: 'body',
  },
  {
    id: 'cold-water-reset',
    catalogKey: 'coldWater',
    category: 'body',
  },
  {
    id: 'urge-surfing',
    catalogKey: 'urgeSurfing',
    category: 'mindfulness',
  },
  {
    id: 'stop-technique',
    catalogKey: 'stopTechnique',
    category: 'mindfulness',
  },
  {
    id: 'compassion-meditation',
    catalogKey: 'compassionMeditation',
    category: 'mindfulness',
  },
  {
    id: 'delay-and-distract',
    catalogKey: 'delayDistract',
    category: 'grounding',
  },
];

const CATEGORY_ICONS: Record<ToolCategory, string> = {
  breathing: '🌬',
  grounding: '🌱',
  body: '💧',
  mindfulness: '🧘',
};

const CATEGORY_BADGE_TONE: Record<ToolCategory, 'neutral' | 'calm' | 'warning' | 'success'> = {
  breathing: 'calm',
  grounding: 'neutral',
  body: 'warning',
  mindfulness: 'success',
};


// ---------------------------------------------------------------------------
// Tool card
// ---------------------------------------------------------------------------

function ToolCard({ tool, locale }: { tool: CopingTool; locale: string }) {
  const t = useTranslations();

  return (
    <a
      href={`/${locale}/tools/${tool.id}`}
      className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded-xl group"
      aria-label={`Open ${t(`tools.items.${tool.catalogKey}.name`)}`}
    >
      <Card hover className="h-full">
        <div className="flex items-start justify-between gap-2">
          <span className="text-2xl leading-none" aria-hidden="true">
            {CATEGORY_ICONS[tool.category]}
          </span>
          <div className="flex items-center gap-1.5 shrink-0">
            {tool.featured && (
              <Badge tone="calm">{t('tools.startHereLabel')}</Badge>
            )}
            <span className="text-xs text-ink-quaternary tabular-nums">
              {t(`tools.items.${tool.catalogKey}.duration`)} {t('tools.minutesSuffix')}
            </span>
          </div>
        </div>
        <h3 className="mt-3 text-sm font-semibold text-ink-primary group-hover:text-accent-bronze transition-colors">
          {t(`tools.items.${tool.catalogKey}.name`)}
        </h3>
        <p className="mt-1 text-xs leading-relaxed text-ink-tertiary line-clamp-3">
          {t(`tools.items.${tool.catalogKey}.description`)}
        </p>
        <div className="mt-3">
          <Badge tone={CATEGORY_BADGE_TONE[tool.category]}>
            {t(`tools.categories.${tool.category}`)}
          </Badge>
        </div>
      </Card>
    </a>
  );
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function ToolsInner({ locale }: { locale: string }) {
  const t = useTranslations();

  const featured = TOOLS.find((tool) => tool.featured);
  const rest = TOOLS.filter((tool) => !tool.featured);

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('nav.tools')}
          </h1>
          <p className="mt-1 text-sm text-ink-tertiary">{t('tools.subtitle')}</p>
        </header>

        {/* Featured tool */}
        {featured && (
          <section aria-labelledby="featured-tool-heading">
            <h2
              id="featured-tool-heading"
              className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
            >
              {t('tools.startHereLabel')}
            </h2>
            <a
              href={`/${locale}/tools/${featured.id}`}
              className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded-xl group"
              aria-label={`Open ${t(`tools.items.${featured.catalogKey}.name`)}`}
            >
              <Card tone="calm" hover className="flex gap-4 items-start">
                <span className="text-3xl leading-none shrink-0" aria-hidden="true">
                  {CATEGORY_ICONS[featured.category]}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-base font-semibold text-ink-primary group-hover:text-accent-bronze transition-colors">
                      {t(`tools.items.${featured.catalogKey}.name`)}
                    </h3>
                    <Badge tone="calm">{t('tools.startHereLabel')}</Badge>
                    <span className="text-xs text-ink-quaternary">
                      {t(`tools.items.${featured.catalogKey}.duration`)} {t('tools.minutesSuffix')}
                    </span>
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-secondary">
                    {t(`tools.items.${featured.catalogKey}.description`)}
                  </p>
                  <p className="mt-2 text-xs text-ink-tertiary">{t('tools.featuredDescription')}</p>
                </div>
              </Card>
            </a>
          </section>
        )}

        {/* All tools grid */}
        <section aria-labelledby="all-tools-heading">
          <h2
            id="all-tools-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('tools.sectionAll')}
          </h2>
          <div className="grid gap-4 grid-cols-2 sm:grid-cols-2 lg:grid-cols-3">
            {rest.map((tool) => (
              <ToolCard key={tool.id} tool={tool} locale={locale} />
            ))}
          </div>
        </section>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function ToolsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <ToolsInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.tools
 *   tools.title
 *   tools.subtitle
 *   tools.startHereLabel
 *   tools.minutesSuffix
 *   tools.categories.breathing / .grounding / .body / .mindfulness
 *   tools.items.boxBreathing.name / .description / .duration
 *   tools.items.grounding54321.name / .description / .duration
 *   tools.items.pmr.name / .description / .duration
 *   tools.items.coldWater.name / .description / .duration
 *   tools.items.urgeSurfing.name / .description / .duration
 *   tools.items.stopTechnique.name / .description / .duration
 *   tools.items.compassionMeditation.name / .description / .duration
 *   tools.items.delayDistract.name / .description / .duration
 *
 *   tools.featuredDescription
 *   tools.sectionAll
 */
