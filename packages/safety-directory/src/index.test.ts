import { describe, it, expect } from 'vitest';
import { getEntry, resolveEntry, isStale, safetyDirectoryMeta, allEntries } from './index';

describe('safety-directory', () => {
  it('exports metadata', () => {
    expect(safetyDirectoryMeta.schemaVersion).toBeTruthy();
    expect(safetyDirectoryMeta.reviewWindowDays).toBeGreaterThan(0);
  });

  it('has at least one entry', () => {
    expect(allEntries.length).toBeGreaterThan(0);
  });

  it('getEntry finds US/en', () => {
    const entry = getEntry('US', 'en');
    expect(entry).toBeDefined();
    expect(entry?.country).toBe('US');
    expect(entry?.locale).toBe('en');
    expect(entry?.hotlines.length).toBeGreaterThan(0);
  });

  it('getEntry is case-insensitive for country', () => {
    expect(getEntry('us', 'en')).toBeDefined();
    expect(getEntry('US', 'en')).toBeDefined();
  });

  it('resolveEntry falls back to English', () => {
    const entry = resolveEntry('US', 'fr');
    expect(entry.country).toBe('US');
  });

  it('resolveEntry falls back to US/en for unknown country', () => {
    const entry = resolveEntry('XX', 'en');
    expect(entry.country).toBe('US');
    expect(entry.locale).toBe('en');
  });

  it('resolveEntry handles null/undefined country', () => {
    const entry = resolveEntry(null, 'fr');
    expect(entry.country).toBe('US');
  });

  it('isStale returns false for fresh entries', () => {
    const entry = getEntry('US', 'en');
    if (!entry) throw new Error('US/en missing');
    expect(isStale(entry, new Date())).toBe(false);
  });

  it('isStale returns true for old entries', () => {
    const entry = getEntry('US', 'en');
    if (!entry) throw new Error('US/en missing');
    const farFuture = new Date('2099-01-01T00:00:00Z');
    expect(isStale(entry, farFuture)).toBe(true);
  });
});
