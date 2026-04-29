import { Skeleton } from '@disciplineos/design-system';

function InsightCardSkeleton() {
  return (
    <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm space-y-3">
      <div className="flex items-start justify-between gap-3">
        <Skeleton variant="rect" width="4rem" height="1.25rem" className="rounded-full" />
        <Skeleton variant="circle" height="1.25rem" width="1.25rem" />
      </div>
      <Skeleton variant="text" width="75%" height="0.875rem" />
      <Skeleton variant="text" width="55%" height="0.75rem" />
      <div className="flex gap-2 pt-1">
        <Skeleton variant="rect" width="5rem" height="2rem" className="rounded-lg" />
        <Skeleton variant="rect" width="4rem" height="2rem" className="rounded-lg" />
      </div>
    </div>
  );
}

export default function PatternsLoading(): React.JSX.Element {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading patterns">
      <header className="space-y-2">
        <Skeleton variant="text" width="8rem" height="1.75rem" />
        <Skeleton variant="text" width="20rem" height="0.875rem" />
      </header>

      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <InsightCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
