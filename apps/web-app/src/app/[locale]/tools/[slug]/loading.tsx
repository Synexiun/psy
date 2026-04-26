/**
 * Loading skeleton for the tool detail page.
 * Shown by Next.js while the page chunk hydrates.
 * No 'use client' needed — this is a Server Component skeleton.
 */

export default function ToolDetailLoading(): React.JSX.Element {
  return (
    <div className="flex min-h-screen bg-surface-primary">
      {/* Sidebar placeholder (desktop) */}
      <aside
        aria-hidden="true"
        className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border-subtle lg:bg-surface-secondary"
      />

      <div className="flex flex-1 flex-col">
        {/* Mobile header placeholder */}
        <div className="flex h-16 items-center justify-between border-b border-border-subtle bg-surface-secondary px-4 sm:px-6 lg:hidden">
          <div className="h-5 w-32 animate-pulse rounded-md bg-surface-tertiary" aria-hidden="true" />
          <div className="h-8 w-24 animate-pulse rounded-lg bg-surface-tertiary" aria-hidden="true" />
        </div>

        <main className="flex-1 overflow-y-auto pb-24 lg:pb-8">
          <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6 lg:py-8 space-y-6">

            {/* Back link placeholder */}
            <div className="h-4 w-20 animate-pulse rounded bg-surface-tertiary" aria-hidden="true" />

            {/* Tool header skeleton */}
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div
                className="h-10 w-10 shrink-0 animate-pulse rounded-xl bg-surface-tertiary mt-0.5"
                aria-hidden="true"
              />
              <div className="min-w-0 space-y-2 flex-1">
                {/* Title + badge row */}
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="h-7 w-48 animate-pulse rounded-lg bg-surface-tertiary" aria-hidden="true" />
                  <div className="h-5 w-20 animate-pulse rounded-full bg-surface-tertiary" aria-hidden="true" />
                </div>
                {/* Duration line */}
                <div className="h-4 w-28 animate-pulse rounded bg-surface-tertiary" aria-hidden="true" />
              </div>
            </div>

            {/* Description skeleton */}
            <div className="space-y-2" aria-hidden="true">
              <div className="h-3.5 w-full animate-pulse rounded bg-surface-tertiary" />
              <div className="h-3.5 w-5/6 animate-pulse rounded bg-surface-tertiary" />
            </div>

            {/* Divider */}
            <div className="border-t border-border-subtle" aria-hidden="true" />

            {/* Section label */}
            <div className="h-3 w-28 animate-pulse rounded bg-surface-tertiary" aria-hidden="true" />

            {/* Content area skeleton — mimics either a circle or step cards */}
            <div
              className="flex flex-col items-center gap-5 rounded-xl border border-border-subtle bg-surface-secondary p-8"
              aria-hidden="true"
            >
              {/* Large circle placeholder (box breathing shape) */}
              <div className="h-48 w-48 animate-pulse rounded-full bg-surface-tertiary" />
              {/* Dots row */}
              <div className="flex gap-2">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="h-2 w-12 animate-pulse rounded-full bg-surface-tertiary" />
                ))}
              </div>
              {/* Button placeholder */}
              <div className="h-11 w-28 animate-pulse rounded-lg bg-surface-tertiary" />
            </div>

            {/* Crisis link placeholder */}
            <div className="flex justify-center pt-2">
              <div className="h-3 w-40 animate-pulse rounded bg-surface-tertiary" aria-hidden="true" />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
