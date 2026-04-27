'use client';
/**
 * Stat — standalone Quiet Strength–tokenised primitive.
 *
 * Hero number + label + optional delta. Designed for: streak counts, PHQ-9
 * scores, weekly check-in totals, and other headline metrics.
 *
 * Clinical-number contract (Rule #9):
 *   When `clinical` is true the number span gets `direction: ltr` and
 *   `font-variant-numeric: tabular-nums` to enforce Latin digits regardless
 *   of the page locale. `formatValue` must be provided (and should be
 *   `formatNumberClinical` from `@disciplineos/i18n-catalog`); a dev-mode
 *   warning fires if it is omitted.
 *
 * Delta signal tokens:
 *   up      → text-signal-stable  (teal — improvement)
 *   down    → text-signal-warning (amber — decline)
 *   neutral → text-ink-tertiary
 */
import * as React from 'react';

export type DeltaDirection = 'up' | 'down' | 'neutral';

export interface StatProps {
  /** The numeric value to display */
  value: number;
  /** Visible label below the number */
  label: string;
  /** Optional delta (change since last period) — e.g. +3 or -1 */
  delta?: number;
  /** Direction of the delta — drives color. Auto-derived from delta sign if not provided. */
  deltaDirection?: DeltaDirection;
  /** Delta label suffix — e.g. "vs last week" */
  deltaLabel?: string;
  /** When true: enforce ltr direction + tabular-nums + warn if formatValue missing */
  clinical?: boolean;
  /** Number formatter — required when clinical=true, optional otherwise */
  formatValue?: (n: number) => string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// ---------------------------------------------------------------------------
// Size scale
// ---------------------------------------------------------------------------

const sizeNumberCls: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'text-2xl',
  md: 'text-4xl',
  lg: 'text-6xl',
};

// ---------------------------------------------------------------------------
// Delta helpers
// ---------------------------------------------------------------------------

function deriveDeltaDirection(delta: number): DeltaDirection {
  if (delta > 0) return 'up';
  if (delta < 0) return 'down';
  return 'neutral';
}

const deltaColorCls: Record<DeltaDirection, string> = {
  up:      'text-signal-stable',
  down:    'text-signal-warning',
  neutral: 'text-ink-tertiary',
};

function DeltaArrow({ direction }: { direction: DeltaDirection }): React.ReactElement {
  if (direction === 'up') {
    return (
      <svg
        aria-hidden="true"
        width="10"
        height="10"
        viewBox="0 0 10 10"
        fill="currentColor"
      >
        <path d="M5 1 L9 9 L5 7 L1 9 Z" />
      </svg>
    );
  }
  if (direction === 'down') {
    return (
      <svg
        aria-hidden="true"
        width="10"
        height="10"
        viewBox="0 0 10 10"
        fill="currentColor"
      >
        <path d="M5 9 L9 1 L5 3 L1 1 Z" />
      </svg>
    );
  }
  // neutral — em dash
  return <span aria-hidden="true">—</span>;
}

// ---------------------------------------------------------------------------
// Stat component
// ---------------------------------------------------------------------------

export function Stat({
  value,
  label,
  delta,
  deltaDirection,
  deltaLabel,
  clinical,
  formatValue,
  size = 'md',
  className = '',
}: StatProps): React.ReactElement {
  // Dev-mode warning: clinical=true without formatValue
  if (process.env.NODE_ENV !== 'production' && clinical && formatValue === undefined) {
    console.warn(
      '[Stat] `clinical` is true but `formatValue` was not provided. ' +
      'Clinical numbers must be formatted with formatNumberClinical from ' +
      '@disciplineos/i18n-catalog. Pass it as the `formatValue` prop.',
    );
  }

  // Resolve displayed value string
  const formattedValue =
    formatValue !== undefined ? formatValue(value) : String(value);

  // Resolve delta direction
  const resolvedDeltaDir: DeltaDirection | undefined =
    delta !== undefined
      ? (deltaDirection !== undefined ? deltaDirection : deriveDeltaDirection(delta))
      : undefined;

  // Clinical inline style
  const clinicalStyle: React.CSSProperties | undefined = clinical
    ? { direction: 'ltr', fontVariantNumeric: 'tabular-nums' }
    : undefined;

  return (
    <div
      className={`flex flex-col items-center gap-1 ${className}`.trim()}
    >
      {/* Hero number */}
      <span
        className={`font-display tabular-nums font-bold leading-none text-ink-primary ${sizeNumberCls[size]}`}
        {...(clinicalStyle !== undefined && { style: clinicalStyle })}
      >
        {formattedValue}
      </span>

      {/* Label */}
      <span className="text-sm text-ink-tertiary">{label}</span>

      {/* Delta */}
      {delta !== undefined && resolvedDeltaDir !== undefined && (
        <span
          className={`flex items-center gap-0.5 text-xs ${deltaColorCls[resolvedDeltaDir]}`}
        >
          <DeltaArrow direction={resolvedDeltaDir} />
          {Math.abs(delta)}
          {deltaLabel !== undefined ? ` ${deltaLabel}` : ''}
        </span>
      )}
    </div>
  );
}
