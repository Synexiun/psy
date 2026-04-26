/**
 * Journal — New Entry loading skeleton.
 *
 * Shown by Next.js while the page JS bundle is being streamed / hydrated.
 * Uses the Skeleton primitive to mirror the layout of the real page.
 */

import { Skeleton } from '@/components/primitives';

export default function JournalNewLoading(): React.JSX.Element {
  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8 space-y-6">
      {/* Back link skeleton */}
      <Skeleton variant="text" width="6rem" height="1rem" />

      {/* Page heading skeleton */}
      <Skeleton variant="text" width="10rem" height="1.75rem" />

      {/* Text editor card skeleton */}
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm space-y-3">
        <Skeleton variant="text" width="5rem" height="1rem" />
        <Skeleton variant="rect" width="100%" height="13rem" />
        <div className="flex justify-between">
          <Skeleton variant="text" width="4rem" height="0.75rem" />
          <Skeleton variant="text" width="4rem" height="0.75rem" />
        </div>
      </div>

      {/* Mood tags card skeleton */}
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm space-y-3">
        <Skeleton variant="text" width="8rem" height="1rem" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} variant="rect" width="6rem" height="2.75rem" />
          ))}
        </div>
      </div>

      {/* Action row skeleton */}
      <div className="flex justify-end gap-3">
        <Skeleton variant="rect" width="6rem" height="2.5rem" />
        <Skeleton variant="rect" width="7rem" height="2.5rem" />
      </div>
    </div>
  );
}
