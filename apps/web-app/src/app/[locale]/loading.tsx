// Route-level loading state for the dashboard.
// Rendered instantly by Next.js while the page Server Component streams.
// Mirrors the dashboard layout structure so the skeleton matches the real
// content shape: Layout shell → header → quick-actions → state indicator →
// streak widget → patterns/insights grid → sidebar.

import { Skeleton } from '@disciplineos/design-system';

function SectionLabel() {
  return <Skeleton variant="text" width="6rem" height="0.75rem" className="mb-3" />;
}

function CardShell({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export default function DashboardLoading(): React.JSX.Element {
  return (
    // Replicate the Layout shell without client deps so this stays a
    // pure Server Component.  The sidebar/nav chrome comes from the parent
    // [locale]/layout.tsx; here we only render the main-content region.
    <div className="flex min-h-screen bg-surface-primary" aria-busy="true" aria-label="Loading dashboard">
      {/* Sidebar placeholder */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border-subtle lg:bg-surface-secondary">
        <div className="flex h-16 items-center px-6">
          <Skeleton variant="text" width="8rem" height="1.125rem" />
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex h-10 items-center gap-3 rounded-lg px-3">
              <Skeleton variant="circle" height="1.25rem" />
              <Skeleton variant="text" width="5rem" height="0.875rem" />
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        {/* Mobile topbar placeholder */}
        <header className="flex h-16 items-center justify-between border-b border-border-subtle bg-surface-secondary px-4 sm:px-6 lg:hidden">
          <Skeleton variant="text" width="8rem" height="1.125rem" />
          <Skeleton variant="rect" width="5rem" height="2rem" />
        </header>

        <main className="flex-1 overflow-y-auto pb-24 lg:pb-8">
          <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6 lg:py-8">

            {/* Page header */}
            <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-2">
                <Skeleton variant="text" width="14rem" height="1.75rem" />
                <Skeleton variant="text" width="20rem" height="0.875rem" />
              </div>
              <Skeleton variant="rect" width="9rem" height="2.5rem" className="hidden lg:block" />
            </header>

            {/* Quick-actions row */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <CardShell key={i} className="flex flex-col items-center gap-2 py-4">
                  <Skeleton variant="circle" height="2rem" />
                  <Skeleton variant="text" width="4rem" height="0.75rem" />
                </CardShell>
              ))}
            </div>

            {/* State indicator section */}
            <section>
              <SectionLabel />
              <CardShell>
                <div className="flex items-center gap-4">
                  <Skeleton variant="circle" height="3rem" />
                  <div className="flex-1 space-y-2">
                    <Skeleton variant="text" width="6rem" height="0.875rem" />
                    <Skeleton variant="text" width="10rem" height="0.75rem" />
                  </div>
                </div>
              </CardShell>
            </section>

            {/* Streak widget section */}
            <section>
              <SectionLabel />
              <CardShell>
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-2">
                    <Skeleton variant="text" width="5rem" height="0.875rem" />
                    <Skeleton variant="text" width="8rem" height="2rem" />
                    <Skeleton variant="text" width="6rem" height="0.75rem" />
                  </div>
                  <Skeleton variant="circle" height="5rem" />
                </div>
              </CardShell>
            </section>

            {/* Patterns grid + sidebar */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Patterns column */}
              <section className="lg:col-span-2">
                <SectionLabel />
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <CardShell key={i}>
                      <Skeleton variant="text" width="5rem" height="0.875rem" />
                      <Skeleton variant="text" width="75%" height="0.875rem" className="mt-3" />
                      <Skeleton variant="text" width="50%" height="0.75rem" className="mt-2" />
                    </CardShell>
                  ))}
                </div>
              </section>

              {/* Sidebar */}
              <aside className="space-y-6">
                {/* Mood sparkline */}
                <CardShell>
                  <Skeleton variant="text" width="5rem" height="0.875rem" className="mb-3" />
                  <Skeleton variant="rect" width="100%" height="5rem" />
                </CardShell>

                {/* Daily tip */}
                <CardShell>
                  <Skeleton variant="text" width="4rem" height="0.875rem" />
                  <Skeleton variant="text" width="100%" height="0.75rem" className="mt-3" />
                  <Skeleton variant="text" width="80%" height="0.75rem" className="mt-1.5" />
                  <Skeleton variant="text" width="60%" height="0.75rem" className="mt-1.5" />
                </CardShell>
              </aside>
            </div>

          </div>
        </main>

        {/* Bottom nav placeholder (mobile) */}
        <div className="fixed inset-x-0 bottom-0 flex h-16 items-center justify-around border-t border-border-subtle bg-surface-secondary lg:hidden">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-1 px-2">
              <Skeleton variant="circle" height="1.5rem" />
              <Skeleton variant="text" width="2.5rem" height="0.625rem" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
