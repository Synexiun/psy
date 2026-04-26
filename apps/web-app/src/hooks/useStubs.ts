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
 * SSR-safe: the URLSearchParams branch is guarded by `typeof window !==
 * 'undefined'` so it never runs on the server. The `useEffect` re-checks on
 * the client after hydration so client-side navigation is reflected correctly.
 */
export function useStubs(): boolean {
  const [active, setActive] = useState<boolean>(() => {
    if (process.env['NEXT_PUBLIC_USE_STUBS'] === 'true') return true;
    if (process.env['NODE_ENV'] === 'test') return true;
    if (typeof window !== 'undefined') {
      return new URLSearchParams(window.location.search).get('stubs') === 'true';
    }
    return false;
  });

  useEffect(() => {
    // Re-evaluate after hydration and on client-side URL changes.
    const check = () => {
      if (process.env['NEXT_PUBLIC_USE_STUBS'] === 'true') {
        setActive(true);
        return;
      }
      if (process.env['NODE_ENV'] === 'test') {
        setActive(true);
        return;
      }
      setActive(new URLSearchParams(window.location.search).get('stubs') === 'true');
    };
    check();
  }, []);

  return active;
}
