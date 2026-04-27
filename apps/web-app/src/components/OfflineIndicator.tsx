'use client';

import * as React from 'react';
import { useOfflineQueue } from '@/hooks/useOfflineQueue';

// ---------------------------------------------------------------------------
// useIsOnline — exported so Layout.tsx can pass isOffline to TopBar
// ---------------------------------------------------------------------------

export function useIsOnline(): boolean {
  const [isOnline, setIsOnline] = React.useState<boolean>(() =>
    typeof window === 'undefined' ? true : navigator.onLine,
  );

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// ---------------------------------------------------------------------------
// OfflineIndicator
// ---------------------------------------------------------------------------

const PANEL_ID = 'offline-indicator-panel';

export function OfflineIndicator(): React.ReactElement | null {
  const isOnline = useIsOnline();
  const { queuedCount } = useOfflineQueue();
  const [open, setOpen] = React.useState(false);
  const autoCloseRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-close the panel 2 s after returning fully online with an empty queue
  React.useEffect(() => {
    if (isOnline && queuedCount === 0 && open) {
      autoCloseRef.current = setTimeout(() => setOpen(false), 2000);
    }
    return () => {
      if (autoCloseRef.current !== null) {
        clearTimeout(autoCloseRef.current);
        autoCloseRef.current = null;
      }
    };
  }, [isOnline, queuedCount, open]);

  // Nothing to show on the happy path
  if (isOnline && queuedCount === 0) {
    return null;
  }

  const pillLabel = isOnline
    ? `${queuedCount} check-in(s) pending sync`
    : `Offline — ${queuedCount} pending`;

  const pillText = isOnline
    ? `${queuedCount} pending sync`
    : queuedCount > 0
      ? `Offline · ${queuedCount} pending`
      : 'Offline';

  // Panel message
  let statusMessage: string;
  if (!isOnline) {
    statusMessage = 'Offline — check-ins will sync when you reconnect';
  } else if (queuedCount > 0) {
    statusMessage = `Back online — syncing ${queuedCount} check-in(s)`;
  } else {
    statusMessage = 'All synced ✓';
  }

  const pillBase =
    'relative flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/40';
  const pillVariant = isOnline
    ? // Subtle blue-grey pill when online but queue > 0
      'bg-surface-secondary text-ink-secondary border border-border-subtle hover:bg-surface-secondary/80'
    : // Amber pill when offline
      'bg-yellow-100 text-yellow-800 border border-yellow-300 hover:bg-yellow-200 dark:bg-yellow-900/40 dark:text-yellow-200 dark:border-yellow-700/60';

  return (
    <div className="relative">
      {/* Badge / pill button */}
      <button
        type="button"
        aria-expanded={open}
        aria-controls={PANEL_ID}
        aria-label={pillLabel}
        onClick={() => setOpen((prev) => !prev)}
        className={`${pillBase} ${pillVariant}`}
      >
        {/* Dot indicator */}
        <span
          aria-hidden="true"
          className={`h-2 w-2 flex-shrink-0 rounded-full ${
            isOnline ? 'bg-blue-400' : 'bg-yellow-500'
          }`}
        />
        {pillText}
      </button>

      {/* Expandable panel */}
      {open && (
        <div
          id={PANEL_ID}
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="absolute end-0 top-full z-50 mt-2 w-72 rounded-lg border border-border-subtle bg-surface-primary p-4 shadow-lg"
        >
          {/* Status line */}
          <p className="text-sm font-medium text-ink-primary">{statusMessage}</p>

          {/* Count pill — only shown when something is queued */}
          {queuedCount > 0 && (
            <div className="mt-3 flex items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200">
                {queuedCount} check-in{queuedCount !== 1 ? 's' : ''} pending
              </span>
            </div>
          )}

          {/* Dismiss button */}
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Dismiss offline status panel"
            className="mt-4 w-full rounded-md border border-border-subtle bg-surface-secondary py-1.5 text-xs text-ink-secondary transition-colors hover:bg-surface-secondary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
