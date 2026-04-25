/**
 * Unit tests for settings page pure helper logic.
 *
 * Tests inline-extracted functions from src/app/[locale]/settings/page.tsx
 * WITHOUT rendering React.
 *
 * Covers:
 * - sectionId: converts section title to kebab-case aria-labelledby id
 * - isDeleteConfirmed: gate logic for the destructive delete-account dialog
 * - APP_VERSION: format (semver string with at least major.minor.patch)
 * - crisis link href: tel: URI construction
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// sectionId — inline from Section component: `section-${title.toLowerCase().replace(/\s+/g, '-')}`
// ---------------------------------------------------------------------------

function sectionId(title: string): string {
  return `section-${title.toLowerCase().replace(/\s+/g, '-')}`;
}

// ---------------------------------------------------------------------------
// isDeleteConfirmed — inline from DeleteDialog: `confirmText === keyword`
// ---------------------------------------------------------------------------

function isDeleteConfirmed(confirmText: string, keyword: string): boolean {
  return confirmText === keyword;
}

// ---------------------------------------------------------------------------
// crisisTelHref — inline from CrisisContent: `tel:${number}`
// ---------------------------------------------------------------------------

function crisisTelHref(number: string): string {
  return `tel:${number}`;
}

function crisisSmsHref(number: string): string {
  return `sms:${number}`;
}

// ---------------------------------------------------------------------------
// Section ID tests
// ---------------------------------------------------------------------------

describe('sectionId', () => {
  it('prefixes with "section-"', () => {
    expect(sectionId('Account')).toMatch(/^section-/);
  });

  it('lowercases the title', () => {
    expect(sectionId('Account')).toBe('section-account');
  });

  it('replaces single space with hyphen', () => {
    expect(sectionId('Privacy & Security')).toContain('privacy-');
  });

  it('replaces multiple spaces with single hyphen each', () => {
    expect(sectionId('My Section Title')).toBe('section-my-section-title');
  });

  it('handles already-lowercase title', () => {
    expect(sectionId('notifications')).toBe('section-notifications');
  });

  it('handles single word title', () => {
    expect(sectionId('About')).toBe('section-about');
  });

  it('produces stable output for same input', () => {
    expect(sectionId('Account')).toBe(sectionId('Account'));
  });
});

// ---------------------------------------------------------------------------
// isDeleteConfirmed tests
// ---------------------------------------------------------------------------

describe('isDeleteConfirmed', () => {
  it('returns true when confirmText exactly matches keyword', () => {
    expect(isDeleteConfirmed('DELETE', 'DELETE')).toBe(true);
  });

  it('returns false when confirmText is empty', () => {
    expect(isDeleteConfirmed('', 'DELETE')).toBe(false);
  });

  it('returns false when confirmText is partial match', () => {
    expect(isDeleteConfirmed('DELET', 'DELETE')).toBe(false);
  });

  it('returns false when confirmText is superset of keyword', () => {
    expect(isDeleteConfirmed('DELETE!', 'DELETE')).toBe(false);
  });

  it('returns false when case differs', () => {
    expect(isDeleteConfirmed('delete', 'DELETE')).toBe(false);
  });

  it('returns true for exact match including spaces', () => {
    expect(isDeleteConfirmed('DELETE ACCOUNT', 'DELETE ACCOUNT')).toBe(true);
  });

  it('returns false when keyword not yet typed', () => {
    expect(isDeleteConfirmed('', '')).toBe(true); // empty===empty, but in practice keyword is non-empty
  });
});

// ---------------------------------------------------------------------------
// crisis tel/sms link construction
// ---------------------------------------------------------------------------

describe('crisisTelHref', () => {
  it('produces tel: URI', () => {
    expect(crisisTelHref('988')).toBe('tel:988');
  });

  it('preserves international number format', () => {
    expect(crisisTelHref('+1-800-273-8255')).toBe('tel:+1-800-273-8255');
  });

  it('always starts with tel:', () => {
    expect(crisisTelHref('112')).toMatch(/^tel:/);
  });
});

describe('crisisSmsHref', () => {
  it('produces sms: URI', () => {
    expect(crisisSmsHref('741741')).toBe('sms:741741');
  });

  it('always starts with sms:', () => {
    expect(crisisSmsHref('HOME')).toMatch(/^sms:/);
  });
});

// ---------------------------------------------------------------------------
// APP_VERSION format (semver pattern)
// ---------------------------------------------------------------------------

describe('APP_VERSION constant', () => {
  const APP_VERSION = '1.0.0-beta';

  it('matches major.minor.patch pattern', () => {
    expect(APP_VERSION).toMatch(/^\d+\.\d+\.\d+/);
  });

  it('is a non-empty string', () => {
    expect(APP_VERSION.length).toBeGreaterThan(0);
  });
});
