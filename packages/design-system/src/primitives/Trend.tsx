'use client';
/**
 * Trend — compact card composing Stat + Sparkline side-by-side.
 *
 * Renders a headline metric (via Stat) next to a mini SVG chart (via Sparkline)
 * in a single rounded card. Designed for dashboard widgets, progress summaries,
 * and clinical trend callouts.
 *
 * Clinical-number contract (Rule #9):
 *   When `clinical` is true the Stat receives the flag and enforces Latin digits.
 *   `formatValue` must be provided; a dev-mode warning fires if omitted.
 *
 * Layout tokens:
 *   Root: bg-surface-secondary (not primary) — intentional for card layering.
 *   All spacing uses gap-* / p-4 — no physical inline-axis classes (pl/pr/ml/mr).
 */
import * as React from 'react';
import { Stat } from './Stat';
import { Sparkline } from './Sparkline';

// ---------------------------------------------------------------------------
// Public prop contract
// ---------------------------------------------------------------------------

export interface TrendProps {
  /** The current numeric value (passed to Stat) */
  value: number;
  /** Visible label (passed to Stat as label) */
  label: string;
  /** Historical data points including the current value (last point = value) — passed to Sparkline */
  data: number[];
  /** Optional delta — passed to Stat */
  delta?: number;
  /** Optional delta direction override — passed to Stat */
  deltaDirection?: 'up' | 'down' | 'neutral';
  /** Optional delta label suffix — passed to Stat */
  deltaLabel?: string;
  /** When true: enforce Latin digit formatting. Must provide formatValue. */
  clinical?: boolean;
  /** Formatter callback — required when clinical=true */
  formatValue?: (n: number) => string;
  /** Stat size variant (default 'sm' — Trend is a compact card) */
  size?: 'sm' | 'md' | 'lg';
  /** Sparkline color — defaults to 'var(--color-accent-bronze)' */
  color?: string;
  /** aria-label for the embedded sparkline SVG */
  sparklineAriaLabel?: string;
  /** Additional classes on the root container */
  className?: string;
}

// ---------------------------------------------------------------------------
// Trend component
// ---------------------------------------------------------------------------

export function Trend({
  value,
  label,
  data,
  delta,
  deltaDirection,
  deltaLabel,
  clinical,
  formatValue,
  size = 'sm',
  color,
  sparklineAriaLabel,
  className = '',
}: TrendProps): React.ReactElement {
  // Dev-mode warning: clinical=true without formatValue
  if (process.env.NODE_ENV !== 'production' && clinical && formatValue === undefined) {
    console.warn(
      '[Trend] `clinical` is true but `formatValue` was not provided. ' +
      'Pass formatNumberClinical from @disciplineos/i18n-catalog.',
    );
  }

  // Build Stat props without ever spreading `undefined` explicitly
  // (exactOptionalPropertyTypes compliance)
  const statProps = {
    value,
    label,
    size,
    ...(delta !== undefined && { delta }),
    ...(deltaDirection !== undefined && { deltaDirection }),
    ...(deltaLabel !== undefined && { deltaLabel }),
    ...(clinical !== undefined && { clinical }),
    ...(formatValue !== undefined && { formatValue }),
  };

  // Build Sparkline props similarly
  const sparklineProps = {
    data,
    ...(color !== undefined && { color }),
    ...(sparklineAriaLabel !== undefined && { ariaLabel: sparklineAriaLabel }),
  };

  return (
    <div
      className={`flex items-center gap-4 rounded-xl bg-surface-secondary p-4 ${className}`.trim()}
    >
      {/* Left column: hero metric */}
      <Stat {...statProps} />

      {/* Right column: mini chart — empty when data.length < 2 (Sparkline returns null) */}
      <div>
        <Sparkline {...sparklineProps} />
      </div>
    </div>
  );
}
