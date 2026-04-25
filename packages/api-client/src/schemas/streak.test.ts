/**
 * Unit tests for StreakStateSchema.
 *
 * CLAUDE.md non-negotiable #3: resilience_days is monotonically non-decreasing.
 * The DB trigger enforces this server-side; the Zod schema validates the wire
 * representation as nonnegative. These tests verify that negative values are
 * rejected and that nullable fields (continuous_streak_start) are accepted as null.
 *
 * Covers:
 * - accepts valid streak state with all fields
 * - accepts resilience_days = 0 (nonnegative lower bound)
 * - rejects resilience_days < 0 (monotonic invariant: rule #3)
 * - rejects continuous_days < 0
 * - rejects resilience_urges_handled_total < 0
 * - accepts continuous_streak_start as null (no active continuous streak)
 * - rejects non-datetime resilience_streak_start
 * - rejects missing required fields
 */

import { describe, it, expect } from 'vitest';
import { StreakStateSchema } from './streak';

const validStreakState = {
  continuous_days: 12,
  continuous_streak_start: '2026-04-13T00:00:00Z',
  resilience_days: 47,
  resilience_urges_handled_total: 89,
  resilience_streak_start: '2026-03-09T00:00:00Z',
};

describe('StreakStateSchema', () => {
  it('accepts a valid streak state', () => {
    expect(StreakStateSchema.safeParse(validStreakState).success).toBe(true);
  });

  it('accepts resilience_days = 0 (nonnegative lower bound)', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, resilience_days: 0 }).success).toBe(true);
  });

  it('rejects resilience_days < 0 (monotonic invariant — CLAUDE.md rule #3)', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, resilience_days: -1 }).success).toBe(false);
  });

  it('accepts continuous_days = 0 (new or reset streak)', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, continuous_days: 0 }).success).toBe(true);
  });

  it('rejects continuous_days < 0', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, continuous_days: -1 }).success).toBe(false);
  });

  it('rejects resilience_urges_handled_total < 0', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, resilience_urges_handled_total: -1 }).success).toBe(false);
  });

  it('accepts continuous_streak_start as null (no active continuous streak)', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, continuous_streak_start: null }).success).toBe(true);
  });

  it('rejects non-datetime resilience_streak_start', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, resilience_streak_start: '2026-03-09' }).success).toBe(false);
  });

  it('rejects non-integer continuous_days', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, continuous_days: 12.5 }).success).toBe(false);
  });

  it('rejects non-integer resilience_days', () => {
    expect(StreakStateSchema.safeParse({ ...validStreakState, resilience_days: 47.3 }).success).toBe(false);
  });

  it('rejects missing resilience_days', () => {
    const { resilience_days: _, ...rest } = validStreakState;
    expect(StreakStateSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects missing resilience_streak_start', () => {
    const { resilience_streak_start: _, ...rest } = validStreakState;
    expect(StreakStateSchema.safeParse(rest).success).toBe(false);
  });
});
