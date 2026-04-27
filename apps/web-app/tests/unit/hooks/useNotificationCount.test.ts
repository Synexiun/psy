'use client';
/**
 * Tests for useNotificationCount hook.
 *
 * Currently a stub that always returns 0. Tests document the expected
 * shape so that when the real backend is wired (Chunk 8 Phase 5), the
 * call-site contract is clear.
 *
 * Covers:
 * - Returns an object with a count property
 * - Count is 0 (stub)
 * - Count is a number
 */
import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useNotificationCount } from '../../../src/hooks/useNotificationCount';

describe('useNotificationCount', () => {
  it('returns an object with a count property', () => {
    const { result } = renderHook(() => useNotificationCount());
    expect(typeof result.current.count).toBe('number');
  });

  it('stub returns count of 0', () => {
    const { result } = renderHook(() => useNotificationCount());
    expect(result.current.count).toBe(0);
  });

  it('count remains 0 after re-render (stub never changes)', () => {
    const { result, rerender } = renderHook(() => useNotificationCount());
    rerender();
    expect(result.current.count).toBe(0);
  });
});
