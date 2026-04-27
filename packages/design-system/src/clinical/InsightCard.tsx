'use client';
/**
 * InsightCard — clinical behavioral insight display.
 *
 * Displays a behavioral insight auto-detected by the pattern module (Sprint 108).
 * Manages a full dismiss / snooze / acknowledge lifecycle:
 *   - dismiss     → hides permanently (renders null, calls onDismiss)
 *   - snooze(24h) → hides for 24 h, re-shows after (renders null, calls onSnooze)
 *   - snooze(7d)  → hides for 7 days (renders null, calls onSnooze)
 *   - acknowledge → user confirms they've read it (calls onAcknowledge);
 *                   card stays visible in an acknowledged state with dismiss
 *                   still accessible.
 *
 * Latin digits (Rule #9):
 *   The `body` prop is rendered verbatim. Callers MUST pre-format any numeric
 *   values in `body` with `formatNumberClinical` from `@disciplineos/i18n-catalog`
 *   before passing them to this component so that Latin digits are guaranteed
 *   regardless of locale. This component intentionally performs no runtime
 *   digit-transformation — it has no awareness of what sub-strings are clinical
 *   numerics vs. ordinary prose.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SnoozeDuration = '24h' | '7d';

export interface InsightCardProps {
  /** Insight identifier */
  id: string;
  /** Insight headline */
  headline: string;
  /**
   * Insight body text — may contain numeric values.
   *
   * @note Callers must pre-format any clinical numbers with
   * `formatNumberClinical` from `@disciplineos/i18n-catalog` to satisfy
   * Rule #9 (Latin digits for every clinical score). This component renders
   * the string verbatim.
   */
  body: string;
  /** Locale — passed through for caller reference; this component renders body verbatim */
  locale?: string;
  /** Called when user dismisses permanently */
  onDismiss?: (id: string) => void;
  /** Called when user snoozes */
  onSnooze?: (id: string, duration: SnoozeDuration) => void;
  /** Called when user acknowledges */
  onAcknowledge?: (id: string) => void;
  /** Additional classes on root */
  className?: string;
}

type InsightStatus = 'visible' | 'acknowledged' | 'dismissed' | 'snoozed';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function InsightCard({
  id,
  headline,
  body,
  locale: _locale,
  onDismiss,
  onSnooze,
  onAcknowledge,
  className,
}: InsightCardProps): React.ReactElement | null {
  const [status, setStatus] = React.useState<InsightStatus>('visible');

  // State machine exits — render null when dismissed or snoozed
  if (status === 'dismissed' || status === 'snoozed') {
    return null;
  }

  function handleDismiss(): void {
    setStatus('dismissed');
    onDismiss?.(id);
  }

  function handleAcknowledge(): void {
    setStatus('acknowledged');
    onAcknowledge?.(id);
  }

  function handleSnooze(duration: SnoozeDuration): void {
    setStatus('snoozed');
    onSnooze?.(id, duration);
  }

  return (
    <div
      className={[
        'flex flex-col gap-3 rounded-xl bg-surface-secondary p-4',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <h3
          data-testid="insight-headline"
          className="text-sm font-semibold text-ink-primary"
        >
          {headline}
        </h3>

        {/* Dismiss button — always visible regardless of status */}
        <button
          type="button"
          aria-label="Dismiss"
          onClick={handleDismiss}
          className="rounded p-0.5 text-ink-tertiary transition-colors duration-fast ease-default hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze"
        >
          <svg
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
          >
            <path
              d="M12 4L4 12M4 4l8 8"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="sr-only">Dismiss</span>
        </button>
      </div>

      {/* Body */}
      <p
        data-testid="insight-body"
        className="text-sm text-ink-tertiary"
      >
        {body}
      </p>

      {/* Action row — only in visible state */}
      {status === 'visible' && (
        <div className="flex gap-2">
          <button
            type="button"
            data-testid="btn-acknowledge"
            onClick={handleAcknowledge}
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-fast ease-default bg-accent-bronze text-white hover:bg-accent-bronze/90"
          >
            Got it
          </button>
          <button
            type="button"
            data-testid="btn-snooze-24h"
            onClick={() => handleSnooze('24h')}
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-fast ease-default bg-surface-tertiary text-ink-secondary hover:bg-surface-tertiary/80"
          >
            Remind in 24h
          </button>
          <button
            type="button"
            data-testid="btn-snooze-7d"
            onClick={() => handleSnooze('7d')}
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-fast ease-default bg-surface-tertiary text-ink-secondary hover:bg-surface-tertiary/80"
          >
            Remind in 7 days
          </button>
        </div>
      )}

      {/* Acknowledged state indicator */}
      {status === 'acknowledged' && (
        <p
          data-testid="acknowledged-indicator"
          className="text-xs text-signal-stable"
        >
          Acknowledged
        </p>
      )}
    </div>
  );
}
