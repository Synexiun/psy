/**
 * Unit tests for the daysSince() pure helper (inlined from store.ts).
 *
 * daysSince(isoStart) computes the integer number of whole days elapsed
 * between isoStart and Date.now(), clamped to 0 via Math.max.
 *
 * Critical invariants:
 *  - Returns 0 when start === now (same instant)
 *  - Returns 0 for future dates (Math.max guard)
 *  - Returns 0 when delta is < 1 full day (Math.floor)
 *  - Returns 1 at exactly 86 400 000 ms elapsed
 *  - Monotonically non-decreasing as time advances (feeds resilienceDays Rule #3)
 *
 * Date.now() is spied on so tests are deterministic regardless of wall clock.
 */

import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';

// ---------------------------------------------------------------------------
// Inline from apps/mobile/src/features/resilience/store.ts
// ---------------------------------------------------------------------------

function daysSince(isoStart: string): number {
  const start = new Date(isoStart).getTime();
  const now = Date.now();
  return Math.max(0, Math.floor((now - start) / 86_400_000));
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MS_PER_DAY = 86_400_000;

// A fixed "now" epoch for all tests: 2026-04-25T12:00:00.000Z
const FIXED_NOW = Date.UTC(2026, 3, 25, 12, 0, 0, 0); // month is 0-indexed

function isoAt(offsetMs: number): string {
  return new Date(FIXED_NOW + offsetMs).toISOString();
}

// ---------------------------------------------------------------------------
// Test setup
// ---------------------------------------------------------------------------

let dateSpy: ReturnType<typeof jest.spyOn>;

beforeEach(() => {
  dateSpy = jest.spyOn(Date, 'now').mockReturnValue(FIXED_NOW);
});

afterEach(() => {
  dateSpy.mockRestore();
});

// ---------------------------------------------------------------------------
// Zero-day cases
// ---------------------------------------------------------------------------

describe('daysSince — zero-day cases', () => {
  it('returns 0 when start equals now (same instant)', () => {
    expect(daysSince(isoAt(0))).toBe(0);
  });

  it('returns 0 when start is 1 ms before now (< 1 full day)', () => {
    expect(daysSince(isoAt(-1))).toBe(0);
  });

  it('returns 0 when start is 1 ms after now (future — Math.max guard)', () => {
    expect(daysSince(isoAt(1))).toBe(0);
  });

  it('returns 0 when start is 24h in the future (future guard)', () => {
    expect(daysSince(isoAt(MS_PER_DAY))).toBe(0);
  });

  it('returns 0 when start is 86 399 999 ms ago (just under 1 day)', () => {
    expect(daysSince(isoAt(-(MS_PER_DAY - 1)))).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Day-boundary cases
// ---------------------------------------------------------------------------

describe('daysSince — day boundary (Math.floor)', () => {
  it('returns 1 at exactly 86 400 000 ms elapsed (1 full day)', () => {
    expect(daysSince(isoAt(-MS_PER_DAY))).toBe(1);
  });

  it('returns 1 at 86 400 001 ms elapsed (just past 1 day)', () => {
    expect(daysSince(isoAt(-(MS_PER_DAY + 1)))).toBe(1);
  });

  it('returns 1 at 1.9 days elapsed (still rounds down to 1)', () => {
    expect(daysSince(isoAt(-Math.floor(1.9 * MS_PER_DAY)))).toBe(1);
  });

  it('returns 2 at exactly 2 full days elapsed', () => {
    expect(daysSince(isoAt(-2 * MS_PER_DAY))).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// Larger elapsed values
// ---------------------------------------------------------------------------

describe('daysSince — multi-day elapsed values', () => {
  it('returns 7 at exactly 7 days elapsed', () => {
    expect(daysSince(isoAt(-7 * MS_PER_DAY))).toBe(7);
  });

  it('returns 30 at exactly 30 days elapsed', () => {
    expect(daysSince(isoAt(-30 * MS_PER_DAY))).toBe(30);
  });

  it('returns 365 at exactly 365 days elapsed', () => {
    expect(daysSince(isoAt(-365 * MS_PER_DAY))).toBe(365);
  });
});

// ---------------------------------------------------------------------------
// Monotonicity (feeds resilienceDays — CLAUDE.md Rule #3)
// ---------------------------------------------------------------------------

describe('daysSince — monotonicity as start moves further into the past', () => {
  it('value never decreases as start moves earlier', () => {
    const offsets = [0, 1, 2, 7, 14, 30, 60, 90, 180, 365].map(
      (d) => -d * MS_PER_DAY,
    );
    const values = offsets.map((o) => daysSince(isoAt(o)));
    for (let i = 1; i < values.length; i++) {
      expect(values[i]!).toBeGreaterThanOrEqual(values[i - 1]!);
    }
  });
});

// ---------------------------------------------------------------------------
// Return type invariant
// ---------------------------------------------------------------------------

describe('daysSince — return type', () => {
  it('always returns a non-negative integer', () => {
    const samples = [-7 * MS_PER_DAY, -1, 0, 1, 7 * MS_PER_DAY].map(
      (o) => daysSince(isoAt(o)),
    );
    for (const v of samples) {
      expect(Number.isInteger(v)).toBe(true);
      expect(v).toBeGreaterThanOrEqual(0);
    }
  });
});
