/**
 * Unit tests for pure helper functions in the journal new-entry page.
 *
 * Clinical note: journal entries are PHI. Tests verify display logic only —
 * no content is logged.
 *
 * Covers:
 * - countWords: empty string, single word, multi-word, multi-whitespace
 * - latinDigits: integer and large number always rendered as Latin digits
 * - MAX_CHARS: 5000 character budget
 * - MAX_MOOD_TAGS: 3 tag selection limit
 * - MOOD_TAGS: 6 distinct tags, all non-empty
 */

import { describe, expect, it } from 'vitest';

// ---------------------------------------------------------------------------
// Inline pure helpers from journal/new/page.tsx
// ---------------------------------------------------------------------------

function countWords(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return trimmed.split(/\s+/).length;
}

function latinDigits(n: number): string {
  return n.toLocaleString('en-US', { useGrouping: false });
}

const MAX_CHARS = 5000;
const MAX_MOOD_TAGS = 3;
const MOOD_TAGS = [
  'Reflective',
  'Grateful',
  'Anxious',
  'Hopeful',
  'Frustrated',
  'Neutral',
] as const;

// ---------------------------------------------------------------------------
// countWords
// ---------------------------------------------------------------------------

describe('countWords', () => {
  it('returns 0 for empty string', () => {
    expect(countWords('')).toBe(0);
  });

  it('returns 0 for whitespace-only string', () => {
    expect(countWords('   ')).toBe(0);
  });

  it('returns 1 for single word', () => {
    expect(countWords('hello')).toBe(1);
  });

  it('returns correct count for multi-word string', () => {
    expect(countWords('hello world foo')).toBe(3);
  });

  it('handles multiple spaces between words', () => {
    expect(countWords('hello   world')).toBe(2);
  });

  it('handles leading and trailing whitespace', () => {
    expect(countWords('  hello world  ')).toBe(2);
  });

  it('handles tabs as whitespace', () => {
    expect(countWords('hello\tworld')).toBe(2);
  });

  it('handles newlines as whitespace', () => {
    expect(countWords('first line\nsecond line')).toBe(4);
  });
});

// ---------------------------------------------------------------------------
// latinDigits — mirrors CLAUDE.md Rule #9 for metadata counts
// ---------------------------------------------------------------------------

describe('latinDigits', () => {
  it('renders 0 as "0"', () => {
    expect(latinDigits(0)).toBe('0');
  });

  it('renders 42 as "42"', () => {
    expect(latinDigits(42)).toBe('42');
  });

  it('renders 5000 without thousands separator', () => {
    expect(latinDigits(5000)).toBe('5000');
  });

  it('output contains only ASCII characters', () => {
    for (const n of [0, 1, 100, 999, 5000]) {
      const result = latinDigits(n);
      for (const ch of result) {
        expect(ch.charCodeAt(0)).toBeLessThan(128);
      }
    }
  });

  it('output contains only digit characters (no separators)', () => {
    const result = latinDigits(1234);
    expect(/^\d+$/.test(result)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe('MAX_CHARS', () => {
  it('is 5000', () => {
    expect(MAX_CHARS).toBe(5000);
  });
});

describe('MAX_MOOD_TAGS', () => {
  it('is 3', () => {
    expect(MAX_MOOD_TAGS).toBe(3);
  });
});

describe('MOOD_TAGS', () => {
  it('has exactly 6 tags', () => {
    expect(MOOD_TAGS).toHaveLength(6);
  });

  it('has no duplicates', () => {
    expect(new Set(MOOD_TAGS).size).toBe(MOOD_TAGS.length);
  });

  it('includes Anxious (clinical relevance)', () => {
    expect(MOOD_TAGS).toContain('Anxious');
  });

  it('includes Hopeful (compassion-first design)', () => {
    expect(MOOD_TAGS).toContain('Hopeful');
  });

  it('all tags are non-empty strings', () => {
    for (const tag of MOOD_TAGS) {
      expect(typeof tag).toBe('string');
      expect(tag.length).toBeGreaterThan(0);
    }
  });
});
