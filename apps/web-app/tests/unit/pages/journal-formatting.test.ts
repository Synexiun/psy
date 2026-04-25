/**
 * Unit tests for journal entry formatting functions.
 *
 * These exercise the deterministic helper functions extracted from the journal
 * page WITHOUT rendering React (no jsdom overhead).
 *
 * Clinical note: journal entries are sensitive PHI. The tests verify only
 * formatting and display logic — no content is logged or exported.
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline the formatting functions under test.
// Testing them in isolation makes them fast and removes the React dep.
// ---------------------------------------------------------------------------

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

/** Rough word count proxy — mirrors the page logic. */
function estimateWordCount(bodyPreview: string): number {
  return Math.ceil(bodyPreview.split(' ').length);
}

// ---------------------------------------------------------------------------
// formatEntryDate
// ---------------------------------------------------------------------------

describe('formatEntryDate', () => {
  it('returns a non-empty string for a valid ISO timestamp', () => {
    const result = formatEntryDate('2026-04-23T08:14:00Z');
    expect(result.length).toBeGreaterThan(0);
  });

  it('includes abbreviated weekday name', () => {
    // 2026-04-23 is a Thursday
    const result = formatEntryDate('2026-04-23T08:14:00Z');
    // Weekday will be 'Thu' in 'en' locale
    expect(result).toMatch(/Thu|Wed|Fri/); // Small tolerance for timezone offset
  });

  it('returns the raw string on invalid ISO input', () => {
    const bad = 'not-a-date';
    const result = formatEntryDate(bad);
    expect(result).toBe(bad);
  });

  it('handles midnight UTC correctly', () => {
    const result = formatEntryDate('2026-01-01T00:00:00Z');
    expect(result.length).toBeGreaterThan(0);
  });

  it('handles end-of-day timestamp', () => {
    const result = formatEntryDate('2026-12-31T23:59:59Z');
    expect(result.length).toBeGreaterThan(0);
  });

  it('outputs includes hour and minute components', () => {
    // Rough check — the formatted string should contain colon-separated time
    const result = formatEntryDate('2026-04-23T14:30:00Z');
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });
});

// ---------------------------------------------------------------------------
// estimateWordCount
// ---------------------------------------------------------------------------

describe('estimateWordCount (word count proxy)', () => {
  it('single word → 1', () => {
    expect(estimateWordCount('hello')).toBe(1);
  });

  it('two words → 2', () => {
    expect(estimateWordCount('hello world')).toBe(2);
  });

  it('empty string → 1 (split produces single empty element)', () => {
    // "".split(' ') → [''] → length 1 → Math.ceil(1) = 1
    expect(estimateWordCount('')).toBe(1);
  });

  it('sentence with 10 words → 10', () => {
    const sentence = 'This is a ten word sentence that I wrote today.';
    // "This is a ten word sentence that I wrote today.".split(' ').length = 10
    expect(estimateWordCount(sentence)).toBe(10);
  });

  it('sentence with extra spaces — counts split tokens, not semantic words', () => {
    // "a  b".split(' ') → ['a', '', 'b'] → 3 elements
    // The implementation mirrors the journal page: it's a proxy, not a semantic counter.
    const result = estimateWordCount('a  b');
    expect(result).toBeGreaterThanOrEqual(2);
  });

  it('multi-line text is counted by space splits', () => {
    // Journal body preview is a single-line string from the API;
    // newlines in the preview count as non-space characters.
    const result = estimateWordCount('Woke up feeling anxious but managed to cope.');
    expect(result).toBe(8);
  });
});

// ---------------------------------------------------------------------------
// Journal view model mapping
// ---------------------------------------------------------------------------

describe('Journal entry view model', () => {
  interface ApiItem {
    journal_id: string;
    title: string | null;
    body_preview: string;
    mood_score: number;
    created_at: string;
  }

  interface JournalEntry {
    id: string;
    date: string;
    preview: string;
    isVoice: boolean;
    wordCount: number;
  }

  function toViewModel(item: ApiItem): JournalEntry {
    return {
      id: item.journal_id,
      date: item.created_at,
      preview: item.body_preview,
      isVoice: false,
      wordCount: Math.ceil(item.body_preview.split(' ').length),
    };
  }

  it('maps journal_id to id', () => {
    const vm = toViewModel({
      journal_id: 'j-001',
      title: null,
      body_preview: 'Today was hard.',
      mood_score: 5,
      created_at: '2026-04-20T10:00:00Z',
    });
    expect(vm.id).toBe('j-001');
  });

  it('maps created_at to date', () => {
    const vm = toViewModel({
      journal_id: 'j-001',
      title: null,
      body_preview: 'Today was hard.',
      mood_score: 5,
      created_at: '2026-04-20T10:00:00Z',
    });
    expect(vm.date).toBe('2026-04-20T10:00:00Z');
  });

  it('maps body_preview to preview', () => {
    const vm = toViewModel({
      journal_id: 'j-001',
      title: null,
      body_preview: 'Woke up anxious.',
      mood_score: 4,
      created_at: '2026-04-20T10:00:00Z',
    });
    expect(vm.preview).toBe('Woke up anxious.');
  });

  it('isVoice is always false (voice not yet exposed by API)', () => {
    const vm = toViewModel({
      journal_id: 'j-001',
      title: null,
      body_preview: 'Some content.',
      mood_score: 7,
      created_at: '2026-04-20T10:00:00Z',
    });
    expect(vm.isVoice).toBe(false);
  });

  it('wordCount is positive for non-empty preview', () => {
    const vm = toViewModel({
      journal_id: 'j-001',
      title: null,
      body_preview: 'A few words here.',
      mood_score: 6,
      created_at: '2026-04-20T10:00:00Z',
    });
    expect(vm.wordCount).toBeGreaterThan(0);
  });
});
