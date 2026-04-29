'use client';
/**
 * ResilienceRing — clinical ProgressRing variant for the resilience streak.
 *
 * Enforces two hard rules from CLAUDE.md:
 *   Rule #3 — Resilience streak never resets. The component clamps displayed
 *             value to the maximum value seen across renders (monotonically
 *             non-decreasing). This is a UI-layer safety net — the DB trigger
 *             is the authoritative enforcement mechanism.
 *   Rule #9 — Latin digits for all clinical scores. Uses formatNumberClinical
 *             from @disciplineos/i18n-catalog regardless of locale prop.
 *
 * Composing pattern: thin wrapper around ProgressRing with bronze token +
 * clinical number formatting baked in.
 */

import * as React from 'react';
import { ProgressRing } from '../primitives/ProgressRing';

// ---------------------------------------------------------------------------
// Latin-digit formatter — mirrors discipline.shared.i18n.formatters.format_number_clinical
// (Rule #9). Inlined here because packages/design-system does not depend on
// @disciplineos/i18n-catalog; we keep the packages cleanly separated.)
// ---------------------------------------------------------------------------

/**
 * Format a clinical integer as Latin digits regardless of the runtime locale.
 * Mirrors formatNumberClinical in @disciplineos/i18n-catalog/src/formatters.ts.
 */
function formatNumberClinical(value: number): string {
  return value.toLocaleString('en', { useGrouping: false });
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ResilienceRingProps {
  /** Current resilience day count — the component clamps to never go below its previous maximum */
  value: number;
  /** Max value for the ring (default: 30 — "30-day resilience window") */
  max?: number;
  /** Ring size in px (default: 120) */
  size?: number;
  /** locale — 'en' | 'fr' | 'ar' | 'fa' (used to enforce Latin digit rendering per Rule #9) */
  locale?: string;
  /** aria-label for the component */
  ariaLabel?: string;
  /** Additional classes on root */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ResilienceRing({
  value,
  max = 30,
  size = 120,
  locale: _locale,
  ariaLabel,
  className,
}: ResilienceRingProps): React.ReactElement {
  // Rule #3: monotonically non-decreasing display value.
  // Track the maximum value seen across renders so a prop decrement is silently
  // clamped at the UI layer. The DB trigger is the authoritative enforcement;
  // this is a defence-in-depth UI guard.
  const maxSeenRef = React.useRef(value);
  if (value > maxSeenRef.current) maxSeenRef.current = value;
  const clampedValue = maxSeenRef.current;

  // Rule #9: Latin digits regardless of locale.
  const label = formatNumberClinical(clampedValue);

  return (
    <div className={className}>
      <ProgressRing
        value={clampedValue}
        max={max}
        size={size}
        color="var(--color-accent-bronze)"
        label={label}
        sublabel="days"
        {...(ariaLabel !== undefined && { ariaLabel })}
      />
    </div>
  );
}
