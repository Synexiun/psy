import { Skeleton } from '@disciplineos/design-system';

function ReportPeriodSkeleton() {
  return (
    <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1.5">
          <Skeleton variant="text" width="9rem" height="0.875rem" />
          <Skeleton variant="text" width="6rem" height="0.75rem" />
        </div>
        <Skeleton variant="rect" width="3.5rem" height="1.25rem" className="rounded-full" />
      </div>
      <div className="flex gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <Skeleton variant="text" width="3rem" height="0.75rem" />
            <Skeleton variant="text" width="2.5rem" height="1.25rem" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ReportsLoading(): React.JSX.Element {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading reports">
      <header className="space-y-2">
        <Skeleton variant="text" width="9rem" height="1.75rem" />
        <Skeleton variant="text" width="22rem" height="0.875rem" />
      </header>

      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <ReportPeriodSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
