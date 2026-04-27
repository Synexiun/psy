'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Layout } from '@/components/Layout';
import { Card, Badge } from '@disciplineos/design-system';
import { usePhiAudit } from '@/hooks/usePhiAudit';

// ---------------------------------------------------------------------------
// Stub entry — replaced by useQuery(journalEntry, id) in Phase 5
// ---------------------------------------------------------------------------
interface JournalEntryDetail {
  id: string;
  date: string;
  body: string;
  isVoice: boolean;
  mood?: string;
}

function formatEntryDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

function JournalEntryInner({ locale, entryId }: { locale: string; entryId: string }) {
  usePhiAudit('/journal/[id]');
  const t = useTranslations();
  const router = useRouter();

  const entry: JournalEntryDetail = {
    id: entryId,
    date: new Date().toISOString(),
    body: 'This is a placeholder journal entry body. Real content will be loaded from the API in Phase 5.',
    isVoice: false,
  };

  return (
    <Layout locale={locale}>
      <div className="space-y-6 max-w-2xl mx-auto">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => router.push(`/${locale}/journal`)}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
              <path d="M19 12H5M12 5l-7 7 7 7"/>
            </svg>
            {t('nav.journal')}
          </button>
        </nav>

        {/* Entry header */}
        <header>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
              {t('journal.entryDetailTitle')}
            </h1>
            {entry.isVoice && (
              <Badge tone="calm" aria-label="Voice recording entry">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3" aria-hidden="true">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/>
                </svg>
                {t('journal.voiceBadge')}
              </Badge>
            )}
          </div>
          <time
            dateTime={entry.date}
            className="mt-1 block text-sm text-ink-tertiary"
          >
            {formatEntryDate(entry.date)}
          </time>
        </header>

        {/* Entry body */}
        <Card>
          <p className="text-sm leading-relaxed text-ink-secondary whitespace-pre-wrap">
            {entry.body}
          </p>
        </Card>

        {/* Crisis link — always visible */}
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

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function JournalEntryPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): React.JSX.Element {
  const { locale, id } = use(params);
  return <JournalEntryInner locale={locale} entryId={id} />;
}

/*
 * i18n keys used:
 *   nav.journal
 *   journal.entryDetailTitle
 *   journal.voiceBadge
 */
