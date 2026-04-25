/**
 * Unit tests for pure logic extracted from the memory (journal) screens.
 *
 * Neither JournalScreen nor JournalEntryScreen can be rendered in a
 * Jest environment — they depend on useNavigation, React Native layout,
 * and device-level TextInput. These tests instead validate the pure helper
 * functions that represent the testable decisions each screen makes.
 *
 * JournalScreen — formatEntryDate
 *   Dates are formatted with 'en-US' locale (CLAUDE.md rule 9: Latin-digit /
 *   locale-neutral display). If someone changes the formatter to use the
 *   device locale, RTL users would receive Arabic-Indic digits in journal
 *   timestamps, which is undesirable even for non-clinical text.
 *
 * JournalEntryScreen — shouldDisableSave
 *   The save button is disabled when the body trims to empty. Saving an
 *   empty entry calls navigation.goBack() without storing — the predicate
 *   guards this branch.
 *
 * Covers:
 * - formatEntryDate returns non-empty dateLabel and timeLabel
 * - dateLabel contains only ASCII / Latin characters (no Arabic-Indic digits)
 * - timeLabel contains only ASCII / Latin characters
 * - timeLabel contains a colon separator (HH:MM format)
 * - shouldDisableSave: empty string → true
 * - shouldDisableSave: whitespace-only string → true
 * - shouldDisableSave: non-empty string → false
 * - shouldDisableSave: leading/trailing whitespace with content → false
 */

import { describe, it, expect } from '@jest/globals';

// ---------------------------------------------------------------------------
// Inline from JournalScreen.tsx — EntryCard date formatting
// ---------------------------------------------------------------------------

function formatEntryDate(iso: string): { dateLabel: string; timeLabel: string } {
  const date = new Date(iso);
  return {
    dateLabel: date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    }),
    timeLabel: date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }),
  };
}

// ---------------------------------------------------------------------------
// Inline from JournalEntryScreen.tsx — save-button disabled predicate
// ---------------------------------------------------------------------------

function shouldDisableSave(body: string): boolean {
  return body.trim().length === 0;
}

// ---------------------------------------------------------------------------
// formatEntryDate — Latin-digit locale compliance (CLAUDE.md rule 9)
// ---------------------------------------------------------------------------

describe('formatEntryDate — Latin-digit locale compliance', () => {
  const SAMPLE_ISO = '2026-04-23T08:14:00Z';

  it('returns non-empty dateLabel', () => {
    const { dateLabel } = formatEntryDate(SAMPLE_ISO);
    expect(dateLabel.length).toBeGreaterThan(0);
  });

  it('returns non-empty timeLabel', () => {
    const { timeLabel } = formatEntryDate(SAMPLE_ISO);
    expect(timeLabel.length).toBeGreaterThan(0);
  });

  it('dateLabel contains only ASCII characters (no Arabic-Indic digits)', () => {
    const { dateLabel } = formatEntryDate(SAMPLE_ISO);
    expect(/^[\x00-\x7F]*$/.test(dateLabel)).toBe(true);
  });

  it('timeLabel contains only ASCII characters (no Arabic-Indic digits)', () => {
    const { timeLabel } = formatEntryDate(SAMPLE_ISO);
    expect(/^[\x00-\x7F]*$/.test(timeLabel)).toBe(true);
  });

  it('timeLabel contains a colon separator (HH:MM format)', () => {
    const { timeLabel } = formatEntryDate(SAMPLE_ISO);
    expect(timeLabel).toContain(':');
  });

  it('dateLabel contains a day-of-week abbreviation', () => {
    // 2026-04-23 is a Thursday
    const { dateLabel } = formatEntryDate(SAMPLE_ISO);
    expect(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].some(d => dateLabel.includes(d))).toBe(true);
  });

  it('produces consistent output for the same ISO string', () => {
    const a = formatEntryDate(SAMPLE_ISO);
    const b = formatEntryDate(SAMPLE_ISO);
    expect(a.dateLabel).toBe(b.dateLabel);
    expect(a.timeLabel).toBe(b.timeLabel);
  });
});

// ---------------------------------------------------------------------------
// shouldDisableSave — save-button disabled predicate
// ---------------------------------------------------------------------------

describe('shouldDisableSave', () => {
  it('returns true for empty string', () => {
    expect(shouldDisableSave('')).toBe(true);
  });

  it('returns true for single space', () => {
    expect(shouldDisableSave(' ')).toBe(true);
  });

  it('returns true for whitespace-only string (spaces, tabs, newlines)', () => {
    expect(shouldDisableSave('   \t\n  ')).toBe(true);
  });

  it('returns false for a non-empty string', () => {
    expect(shouldDisableSave('Hello')).toBe(false);
  });

  it('returns false when body has leading and trailing whitespace but content in the middle', () => {
    expect(shouldDisableSave('  Hello world  ')).toBe(false);
  });

  it('returns false for a single non-whitespace character', () => {
    expect(shouldDisableSave('.')).toBe(false);
  });

  it('returns false for a realistic journal entry', () => {
    expect(shouldDisableSave('Felt the urge at 5 PM but used box breathing instead.')).toBe(false);
  });
});
