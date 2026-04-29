'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

/**
 * Moves focus to #main-content on every client-side navigation so AT users
 * don't get stranded at the triggering link after a route change (WCAG 2.4.3).
 * Skipped on first render — the page load focus is browser-managed.
 */
export function RouteAnnouncer(): null {
  const pathname = usePathname();
  const firstRender = useRef(true);

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    const el = document.getElementById('main-content');
    el?.focus({ preventScroll: false });
  }, [pathname]);

  return null;
}
