'use client';
import { useState, useEffect } from 'react';

/**
 * Returns `true` when the app should use stub data instead of live API calls.
 *
 * Active when ANY of the following is true:
 *   1. `NEXT_PUBLIC_USE_STUBS === 'true'`  (Storybook / preview builds)
 *   2. `NODE_ENV === 'test'`               (Vitest / Jest)
 *   3. URL search param `?stubs=true`      (manual QA override)
 *
 * SSR-safe: env-var flags are stable across server and client so `useState`
 * initializes from them only. The URLSearchParams branch is deferred to
 * `useEffect` (client-only) to prevent React hydration mismatch that would
 * occur if the lazy initializer ran `window.location.search` on the server
 * (returning false) but a different value on the client.
 */
const envActive =
  process.env['NEXT_PUBLIC_USE_STUBS'] === 'true' ||
  process.env['NODE_ENV'] === 'test';

export function useStubs(): boolean {
  const [active, setActive] = useState<boolean>(envActive);

  useEffect(() => {
    if (envActive) return;
    setActive(
      new URLSearchParams(window.location.search).get('stubs') === 'true',
    );
  }, []);

  return active;
}
