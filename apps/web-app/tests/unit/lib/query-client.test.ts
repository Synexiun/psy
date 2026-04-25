/**
 * Tests for src/lib/query-client.ts — TanStack Query client configuration.
 *
 * Clinical app requirements:
 * - staleTime 30 000 ms: avoids unnecessary re-fetches for clinical data
 *   that updates on user action, not polling.
 * - refetchOnWindowFocus: false — clinical data should not surprise users
 *   with a re-fetch when they switch tabs.
 * - retry 2: handles transient network blips without hammering a degraded backend.
 */

import { describe, expect, it } from 'vitest';

import { queryClient } from '../../../src/lib/query-client';

describe('queryClient', () => {
  it('is instantiated', () => {
    expect(queryClient).toBeDefined();
  });

  it('staleTime is 30 000 ms', () => {
    const options = queryClient.getDefaultOptions();
    expect(options.queries?.staleTime).toBe(30_000);
  });

  it('refetchOnWindowFocus is false', () => {
    const options = queryClient.getDefaultOptions();
    expect(options.queries?.refetchOnWindowFocus).toBe(false);
  });

  it('retry is 2', () => {
    const options = queryClient.getDefaultOptions();
    expect(options.queries?.retry).toBe(2);
  });
});
