'use client';

/**
 * Journal — New Entry page
 *
 * PHI contract:
 * - Journal text is personal health information. Never log content to console.
 * - Draft is stored in localStorage only (cleared on save and discard).
 * - Never use sessionStorage (tab-scoped but visible to same-origin JS).
 * - No AI analysis from this page — pure storage.
 */

import { use, useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth } from '@clerk/nextjs';
import { Layout } from '@/components/Layout';
import { Button, Card } from '@/components/primitives';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_CHARS = 5000;
const DRAFT_KEY = 'journal-draft';
const AUTOSAVE_DELAY_MS = 2_000;

// Mood tag keys — labels are hardcoded because they are not yet in the
// i18n catalog. They will be moved to the catalog when native review is done.
type MoodTag =
  | 'Reflective'
  | 'Grateful'
  | 'Anxious'
  | 'Hopeful'
  | 'Frustrated'
  | 'Neutral';

const MOOD_TAGS: MoodTag[] = [
  'Reflective',
  'Grateful',
  'Anxious',
  'Hopeful',
  'Frustrated',
  'Neutral',
];

const MAX_MOOD_TAGS = 3;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Count words in text — handles multi-whitespace and leading/trailing space. */
function countWords(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return trimmed.split(/\s+/).length;
}

/**
 * Format a number as Latin digits — mirrors the Latin-digit rule for clinical
 * values. Character/word counts are metadata, not validated clinical scores,
 * but the rule is applied here for consistency and because the journal is PHI.
 */
function latinDigits(n: number): string {
  return n.toLocaleString('en-US', { useGrouping: false });
}

// ---------------------------------------------------------------------------
// Inner component (all interactivity)
// ---------------------------------------------------------------------------

function JournalNewInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const router = useRouter();
  const { getToken } = useAuth();

  // ----- Editor state -----
  const [content, setContent] = useState('');
  const [selectedMoods, setSelectedMoods] = useState<Set<MoodTag>>(new Set());

  // ----- UI state -----
  const [restoredDraft, setRestoredDraft] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Timer ref for debounced auto-save
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------------------------------------------------------------------------
  // Draft restoration on mount
  // ---------------------------------------------------------------------------

  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_KEY);
      if (saved && saved.length > 0) {
        setContent(saved);
        setRestoredDraft(true);
      }
    } catch {
      // localStorage may be unavailable in some private-browsing contexts
    }
  }, []);

  // ---------------------------------------------------------------------------
  // beforeunload — persist draft when navigating away mid-write
  // ---------------------------------------------------------------------------

  useEffect(() => {
    function handleBeforeUnload() {
      if (content.trim().length > 0) {
        try {
          localStorage.setItem(DRAFT_KEY, content);
        } catch {
          // best-effort
        }
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [content]);

  // ---------------------------------------------------------------------------
  // Debounced auto-save to localStorage
  // ---------------------------------------------------------------------------

  useEffect(() => {
    // Clear any pending timer when content changes
    if (autoSaveTimerRef.current !== null) {
      clearTimeout(autoSaveTimerRef.current);
    }

    if (content.trim().length === 0) {
      setAutoSaveStatus('idle');
      return;
    }

    setAutoSaveStatus('saving');
    autoSaveTimerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY, content);
        setAutoSaveStatus('saved');
      } catch {
        setAutoSaveStatus('idle');
      }
    }, AUTOSAVE_DELAY_MS);

    return () => {
      if (autoSaveTimerRef.current !== null) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [content]);

  // ---------------------------------------------------------------------------
  // Event handlers
  // ---------------------------------------------------------------------------

  function handleContentChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const value = e.target.value;
    // Hard-cap at MAX_CHARS — the Save button is also disabled, but this
    // prevents paste overflow.
    if (value.length <= MAX_CHARS) {
      setContent(value);
    }
  }

  function toggleMood(mood: MoodTag) {
    setSelectedMoods((prev) => {
      const next = new Set(prev);
      if (next.has(mood)) {
        next.delete(mood);
      } else {
        if (next.size < MAX_MOOD_TAGS) {
          next.add(mood);
        }
      }
      return next;
    });
  }

  const clearDraft = useCallback(() => {
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch {
      // best-effort
    }
  }, []);

  function handleDiscard() {
    clearDraft();
    router.push(`/${locale}/journal`);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (content.trim().length === 0 || content.length > MAX_CHARS) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const token = await getToken();
      if (!token) throw new Error('Not authenticated');

      const BASE_URL = (
        process.env['NEXT_PUBLIC_API_URL'] ??
        process.env['NEXT_PUBLIC_API_BASE_URL'] ??
        'http://localhost:8000'
      ).replace(/\/$/, '');

      const response = await fetch(`${BASE_URL}/v1/journal/entries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          text: content,
          mood_tags: Array.from(selectedMoods),
        }),
      });

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const body = (await response.json()) as { detail?: string };
          if (body.detail) detail = body.detail;
        } catch {
          // non-JSON body — keep default
        }
        throw new Error(detail);
      }

      // Success — clear the draft and navigate to the listing
      clearDraft();
      router.push(`/${locale}/journal`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to save entry. Please try again.';
      setSubmitError(message);
      setIsSubmitting(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Derived values
  // ---------------------------------------------------------------------------

  const charCount = content.length;
  const wordCount = countWords(content);
  const isOverLimit = charCount > MAX_CHARS;
  const isEmpty = content.trim().length === 0;
  const isSaveDisabled = isSubmitting || isOverLimit || isEmpty;

  const charsRemaining = MAX_CHARS - charCount;
  const showCharWarning = charsRemaining >= 0 && charsRemaining < 200;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Layout locale={locale}>
      <div className="space-y-6">
        {/* Back link */}
        <nav aria-label="Breadcrumb">
          <a
            href={`/${locale}/journal`}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-tertiary hover:text-ink-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
          >
            {/* Left-arrow SVG — no emoji, renders identically across locales */}
            <svg
              aria-hidden="true"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="shrink-0"
            >
              <path
                d="M10 12L6 8L10 4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            {t('nav.journal')}
          </a>
        </nav>

        {/* Page heading */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('journal.newEntry')}
          </h1>
        </header>

        {/* Restored-draft banner */}
        {restoredDraft && (
          <div
            role="status"
            aria-live="polite"
            className="flex items-center gap-2 rounded-lg border border-signal-warning/30 bg-signal-warning/10 px-4 py-3 text-sm text-signal-warning"
          >
            <svg
              aria-hidden="true"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="shrink-0"
            >
              <path
                d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM8 5v3.5m0 2h.008"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Restored unsaved draft
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6" noValidate>
          {/* Text editor section */}
          <Card>
            <label
              htmlFor="journal-entry-text"
              className="block text-sm font-medium text-ink-primary"
            >
              {t('journal.newEntry')}
            </label>

            <textarea
              id="journal-entry-text"
              aria-label="Journal entry"
              value={content}
              onChange={handleContentChange}
              placeholder="What's on your mind?"
              rows={8}
              maxLength={MAX_CHARS}
              className="mt-3 w-full resize-y rounded-lg border border-border-subtle bg-surface-primary px-3 py-2.5 text-sm text-ink-primary placeholder-ink-quaternary focus:border-accent-bronze focus:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-accent-bronze/30 transition-colors"
              aria-describedby="journal-char-count journal-word-count"
              disabled={isSubmitting}
            />

            {/* Character counter + auto-save indicator */}
            <div className="mt-2 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                {/* Word count */}
                <p
                  id="journal-word-count"
                  className="text-xs text-ink-quaternary"
                  aria-live="polite"
                >
                  {latinDigits(wordCount)} {wordCount === 1 ? 'word' : 'words'}
                </p>

                {/* Auto-save status */}
                {autoSaveStatus === 'saved' && (
                  <span
                    role="status"
                    aria-live="polite"
                    className="flex items-center gap-1 text-xs text-signal-stable"
                  >
                    <svg
                      aria-hidden="true"
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M2 6L5 9L10 3"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    Saved
                  </span>
                )}
              </div>

              {/* Character counter */}
              <p
                id="journal-char-count"
                aria-live="polite"
                className={`text-xs tabular-nums ${
                  isOverLimit
                    ? 'font-semibold text-signal-crisis'
                    : showCharWarning
                    ? 'text-signal-warning'
                    : 'text-ink-quaternary'
                }`}
              >
                {latinDigits(charCount)}/{latinDigits(MAX_CHARS)}
              </p>
            </div>

            {/* Over-limit warning */}
            {isOverLimit && (
              <p role="alert" className="mt-2 text-xs font-medium text-signal-crisis">
                Entry exceeds {latinDigits(MAX_CHARS)} characters. Please shorten before saving.
              </p>
            )}
          </Card>

          {/* Mood tag section */}
          <Card>
            <fieldset>
              <legend className="text-sm font-medium text-ink-primary">
                How are you feeling?{' '}
                <span className="font-normal text-ink-quaternary">(optional, up to {latinDigits(MAX_MOOD_TAGS)})</span>
              </legend>
              <div
                className="mt-3 flex flex-wrap gap-2"
                role="group"
                aria-label="Mood tags"
              >
                {MOOD_TAGS.map((mood) => {
                  const active = selectedMoods.has(mood);
                  const atLimit = selectedMoods.size >= MAX_MOOD_TAGS && !active;
                  return (
                    <button
                      key={mood}
                      type="button"
                      onClick={() => toggleMood(mood)}
                      aria-pressed={active}
                      disabled={atLimit || isSubmitting}
                      className={`min-h-[44px] rounded-full px-4 py-2 text-sm font-medium transition-all duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 disabled:opacity-40 disabled:cursor-not-allowed ${
                        active
                          ? 'bg-accent-bronze text-white shadow-sm'
                          : 'bg-surface-tertiary text-ink-secondary hover:bg-surface-tertiary border border-border-subtle'
                      }`}
                    >
                      {mood}
                    </button>
                  );
                })}
              </div>
            </fieldset>
          </Card>

          {/* Error message */}
          {submitError !== null && (
            <div
              role="alert"
              aria-live="assertive"
              className="rounded-lg border border-signal-crisis/30 bg-signal-crisis/10 px-4 py-3 text-sm text-signal-crisis"
            >
              {submitError}
            </div>
          )}

          {/* Action row */}
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="secondary"
              size="md"
              className="min-h-[44px] sm:w-auto w-full"
              onClick={handleDiscard}
              disabled={isSubmitting}
            >
              Discard
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={isSubmitting}
              disabled={isSaveDisabled}
              className="min-h-[44px] sm:w-auto w-full"
            >
              Save entry
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export — server shell with async params, renders client inner
// ---------------------------------------------------------------------------

export default function JournalNewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <JournalNewInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.journal          — "Journal" (back-link label)
 *   journal.newEntry     — "New entry" (page heading + textarea label)
 *
 * Hardcoded strings (not yet in catalog — add when native review is done):
 *   "What's on your mind?"          (textarea placeholder)
 *   "Restored unsaved draft"        (draft-restore banner)
 *   "Saved"                         (auto-save indicator)
 *   "How are you feeling?"          (mood fieldset legend)
 *   "(optional, up to 3)"           (mood fieldset hint)
 *   "Discard"                       (secondary action)
 *   "Save entry"                    (primary action)
 *   mood tag labels (6)             (Reflective, Grateful, Anxious, Hopeful, Frustrated, Neutral)
 *   character-limit warning copy
 */
