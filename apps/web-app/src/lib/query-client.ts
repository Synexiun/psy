'use client';

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 30 s default: balances freshness against unnecessary re-fetches on a
      // clinical app where users frequently tab between surfaces.
      staleTime: 30_000,
      // Avoid surprise re-fetches when a user returns to the tab. Clinical
      // data updates on user action or a timed interval, not on focus.
      refetchOnWindowFocus: false,
      // Two retries covers transient network blips without hammering a backend
      // that is genuinely down.
      retry: 2,
    },
  },
});
