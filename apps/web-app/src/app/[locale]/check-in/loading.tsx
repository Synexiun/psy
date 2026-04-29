import { Skeleton } from '@disciplineos/design-system';

export default function CheckInLoading(): React.JSX.Element {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading check-in">
      <header className="space-y-2">
        <Skeleton variant="text" width="8rem" height="1.75rem" />
        <Skeleton variant="text" width="18rem" height="0.875rem" />
      </header>

      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} variant="circle" height="0.625rem" width="0.625rem" />
        ))}
      </div>

      {/* Wizard card */}
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-6 shadow-sm space-y-6">
        <Skeleton variant="text" width="12rem" height="1.25rem" />
        {/* Slider track */}
        <div className="space-y-3">
          <Skeleton variant="rect" width="100%" height="3rem" className="rounded-full" />
          <div className="flex justify-between">
            <Skeleton variant="text" width="3rem" height="0.75rem" />
            <Skeleton variant="text" width="3rem" height="0.75rem" />
          </div>
        </div>
        <Skeleton variant="text" width="80%" height="0.75rem" />
      </div>

      {/* Button row */}
      <div className="flex justify-between gap-3">
        <Skeleton variant="rect" width="6rem" height="2.75rem" className="rounded-lg" />
        <Skeleton variant="rect" width="8rem" height="2.75rem" className="rounded-lg" />
      </div>
    </div>
  );
}
