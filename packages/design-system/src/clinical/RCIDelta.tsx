'use client';
/**
 * RCIDelta — displays a Reliable Change Index delta value.
 *
 * Jacobson & Truax (1991): an RCI delta is statistically significant when
 * |delta| ≥ 1.96 × SE. For PHQ-9 (SD=5.72, r=0.84): SE=2.68, threshold=5.26.
 *
 * Shows:
 *   1. Numeric delta (+/−) in Latin digits (Rule #9)
 *   2. A dot-scale significance indicator (●●●, ●●○, ●○○)
 *   3. A significance label
 *
 * Significance bands:
 *   significant    |delta| ≥ 5.26  → ●●●
 *   moderate       |delta| ≥ 2.5   → ●●○
 *   non-significant                 → ●○○
 *
 * Rule #9 enforcement: delta is always formatted as Latin digits via
 * `toLocaleString('en', { useGrouping: false })` regardless of locale prop.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// RCI threshold constants — pinned from Jacobson & Truax, 1991.
// Inlined because packages/design-system does not depend on apps/web-app.
// Authoritative copy: apps/web-app/src/lib/clinical/rci-thresholds.ts
// ---------------------------------------------------------------------------

const RCI_PHQ9_THRESHOLD = 5.26;

type RciSignificance = 'significant' | 'moderate' | 'non-significant';

function classifyDelta(absDelta: number): RciSignificance {
  if (absDelta >= RCI_PHQ9_THRESHOLD) return 'significant';
  if (absDelta >= 2.5)               return 'moderate';
  return 'non-significant';
}

// ---------------------------------------------------------------------------
// Dot scale
// ---------------------------------------------------------------------------

const DOT_SCALE: Record<RciSignificance, string> = {
  'significant':     '●●●',
  'moderate':        '●●○',
  'non-significant': '●○○',
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface RCIDeltaProps {
  /** The delta value (+/−). Positive = improvement (score decreased). */
  delta: number;
  /** Locale — for Latin digit enforcement (Rule #9) */
  locale?: string;
  /** Additional classes on root */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function RCIDelta({
  delta,
  locale: _locale,
  className,
}: RCIDeltaProps): React.ReactElement {
  const absDelta = Math.abs(delta);
  const significance = classifyDelta(absDelta);
  const dots = DOT_SCALE[significance];

  // Rule #9: always render clinical scores in Latin digits regardless of locale.
  // Positive delta = improvement (PHQ-9 score went down), render with '+' prefix.
  // Negative delta = decline, render with '−' prefix.
  // Zero = no change.
  let formattedDelta: string;
  if (delta > 0) {
    formattedDelta = '+' + absDelta.toLocaleString('en', { useGrouping: false });
  } else if (delta < 0) {
    formattedDelta = '-' + absDelta.toLocaleString('en', { useGrouping: false });
  } else {
    formattedDelta = '0';
  }

  // Color the delta value based on direction.
  let deltaColorClass: string;
  if (delta > 0) {
    deltaColorClass = 'text-signal-stable';
  } else if (delta < 0) {
    deltaColorClass = 'text-signal-warning';
  } else {
    deltaColorClass = 'text-ink-tertiary';
  }

  return (
    <div className={['flex items-center gap-2', className].filter(Boolean).join(' ')}>
      <span
        data-testid="rci-delta"
        className={['text-sm font-medium', deltaColorClass].join(' ')}
      >
        {formattedDelta}
      </span>
      <span
        data-testid="rci-dots"
        className="text-xs tracking-tight"
        aria-hidden="true"
      >
        {dots}
      </span>
      <span
        data-testid="rci-significance"
        className="text-xs text-ink-tertiary"
      >
        {significance}
      </span>
    </div>
  );
}
