// Journal-specific route-level loading state.
// Rendered while the JournalPage Server Component (or its data) is streaming.
// Mirrors the journal page layout: header, "New entry" button, entry list.

import { Skeleton } from '@disciplineos/design-system';

function JournalEntryCardSkeleton() {
  return (
    <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
      {/* Date + badge row */}
      <div className="flex items-start justify-between gap-3">
        <Skeleton variant="text" width="9rem" height="0.75rem" />
        <Skeleton variant="rect" width="4rem" height="1.25rem" className="rounded-full" />
      </div>
      {/* Preview text lines */}
      <Skeleton variant="text" width="100%" height="0.875rem" className="mt-4" />
      <Skeleton variant="text" width="80%" height="0.875rem" className="mt-2" />
      <Skeleton variant="text" width="60%" height="0.875rem" className="mt-2" />
    </div>
  );
}

export default function JournalLoading(): React.JSX.Element {
  return (
    <div
      className="space-y-6"
      aria-busy="true"
      aria-label="Loading journal"
    >
      {/* Page header */}
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <Skeleton variant="text" width="7rem" height="1.75rem" />
          <Skeleton variant="text" width="16rem" height="0.875rem" />
        </div>
        {/* "New entry" button placeholder */}
        <Skeleton variant="rect" width="8rem" height="2.75rem" className="self-start" />
      </header>

      {/* Section label */}
      <Skeleton variant="text" width="6rem" height="0.75rem" />

      {/* Entry cards */}
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <JournalEntryCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
