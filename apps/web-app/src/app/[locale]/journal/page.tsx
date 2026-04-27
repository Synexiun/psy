'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Button, Card, Badge } from '@disciplineos/design-system';
import { useJournalEntries } from '@/hooks/useDashboardData';
import { usePhiAudit } from '@/hooks/usePhiAudit';

// ---------------------------------------------------------------------------
// Local view model — maps the API shape to what the UI consumes.
// Journal entries are sensitive PHI: no console.log of content, no export,
// no share UI on individual entries.
// ---------------------------------------------------------------------------

interface JournalEntry {
  id: string;
  date: string;
  preview: string;
  isVoice: boolean;
  wordCount: number;
}


function formatEntryDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Inner component (client)
// ---------------------------------------------------------------------------

function JournalInner({ locale }: { locale: string }) {
  usePhiAudit('/journal');
  const t = useTranslations();
  const router = useRouter();
  const { data, isLoading } = useJournalEntries();

  // Map API items to the local view model.
  // wordCount is a rough proxy — the API does not expose the full body.
  const entries: JournalEntry[] = (data?.items ?? []).map((item) => ({
    id: item.journal_id,
    date: item.created_at,
    preview: item.body_preview,
    isVoice: false, // voice detection not yet exposed by this API endpoint
    wordCount: Math.ceil(item.body_preview.split(' ').length),
  }));

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Page header */}
        <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
              {t('nav.journal')}
            </h1>
            <p className="mt-1 text-sm text-ink-tertiary">{t('journal.subtitle')}</p>
          </div>
          <Button
            variant="primary"
            size="md"
            className="min-h-[44px] self-start"
            aria-label={t('journal.newEntry')}
            onClick={() => router.push(`/${locale}/journal/new`)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            {t('journal.newEntry')}
          </Button>
        </header>

        {/* Entry list */}
        <section aria-labelledby="journal-entries-heading">
          <h2
            id="journal-entries-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
          >
            {t('journal.entriesHeading')}
          </h2>

          {isLoading ? (
            <div className="space-y-3" aria-busy="true" aria-label="Loading journal entries">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-[108px] animate-pulse rounded-lg bg-surface-tertiary"
                  aria-hidden="true"
                />
              ))}
            </div>
          ) : entries.length === 0 ? (
            <Card className="py-12 text-center">
              <p className="text-base font-medium text-ink-secondary">{t('journal.emptyHeadline')}</p>
              <p className="mt-2 text-sm leading-relaxed text-ink-tertiary">{t('journal.emptyBody')}</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {entries.map((entry) => (
                <article key={entry.id}>
                  <a
                    href={`/${locale}/journal/${entry.id}`}
                    className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded-xl"
                    aria-label={`Open journal entry from ${formatEntryDate(entry.date)}`}
                  >
                    <Card hover className="cursor-pointer">
                      <div className="flex items-start justify-between gap-3">
                        <time
                          dateTime={entry.date}
                          className="shrink-0 text-xs font-medium text-ink-quaternary"
                        >
                          {formatEntryDate(entry.date)}
                        </time>
                        <div className="flex shrink-0 items-center gap-2">
                          {entry.isVoice && (
                            <Badge tone="calm" aria-label="Voice recording entry">
                              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3" aria-hidden="true">
                                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                                <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/>
                              </svg>
                              {t('journal.voiceBadge')}
                            </Badge>
                          )}
                          <span className="text-xs text-ink-quaternary">
                            {entry.wordCount.toString()} {t('journal.wordCount')}
                          </span>
                        </div>
                      </div>
                      <p className="mt-3 text-sm leading-relaxed text-ink-secondary line-clamp-3">
                        {entry.preview}
                      </p>
                    </Card>
                  </a>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export — server shell with async params, renders client inner
// ---------------------------------------------------------------------------

export default function JournalPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <JournalInner locale={locale} />;
}
