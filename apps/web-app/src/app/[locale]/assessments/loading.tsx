// Assessments-specific route-level loading state.
// Rendered while the AssessmentsPage Server Component is streaming.
// Mirrors the assessments page layout: header, instrument card grid, disclaimer.

import { Skeleton } from '@/components/primitives';

function AssessmentCardSkeleton() {
  return (
    <div className="rounded-xl border border-surface-200 bg-surface-0 p-5 shadow-sm flex flex-col gap-4">
      {/* Instrument name + progress ring row */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          {/* Validated instrument short name */}
          <Skeleton variant="text" width="4rem" height="1rem" />
          {/* Full instrument name — two lines */}
          <Skeleton variant="text" width="9rem" height="0.75rem" />
          <Skeleton variant="text" width="6rem" height="0.75rem" />
        </div>
        {/* Progress ring */}
        <Skeleton variant="circle" height="4rem" className="shrink-0" />
      </div>

      {/* Last completed / score lines */}
      <div className="space-y-1.5">
        <Skeleton variant="text" width="10rem" height="0.75rem" />
        <Skeleton variant="text" width="7rem" height="0.75rem" />
      </div>

      {/* CTA button */}
      <Skeleton variant="rect" width="100%" height="2.75rem" className="mt-auto" />
    </div>
  );
}

export default function AssessmentsLoading(): React.JSX.Element {
  return (
    <div
      className="space-y-6"
      aria-busy="true"
      aria-label="Loading assessments"
    >
      {/* Page header */}
      <header className="space-y-2">
        <Skeleton variant="text" width="10rem" height="1.75rem" />
        <Skeleton variant="text" width="22rem" height="0.875rem" />
      </header>

      {/* Instruments grid — 5 instruments (PHQ-9, GAD-7, AUDIT-C, PSS-10, WHO-5) */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <AssessmentCardSkeleton key={i} />
        ))}
      </div>

      {/* Clinical disclaimer placeholder */}
      <div className="rounded-xl border border-surface-200 bg-surface-50 px-5 py-4">
        <Skeleton variant="text" width="100%" height="0.75rem" />
        <Skeleton variant="text" width="80%" height="0.75rem" className="mt-1.5" />
      </div>
    </div>
  );
}
