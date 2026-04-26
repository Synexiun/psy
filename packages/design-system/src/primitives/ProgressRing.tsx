'use client';
/**
 * ProgressRing — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the ProgressRing exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping (Quiet Strength defaults):
 *   color default:      var(--color-brand-500)      → var(--color-accent-bronze)
 *   trackColor default: var(--color-surface-200)    → var(--color-surface-tertiary)
 *   text-ink-900       → text-ink-primary
 *   text-ink-500       → text-ink-tertiary
 *   ease-standard      → ease-default  (--ease-default in @theme)
 *
 * Geometry (radius, circumference, dashoffset) is identical to the original.
 * The `color` and `trackColor` props accept arbitrary CSS color strings so
 * consumers can override to any value — only the defaults change.
 */
import * as React from 'react';

export interface ProgressRingProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  trackColor?: string;
  label?: React.ReactNode;
  sublabel?: React.ReactNode;
  ariaLabel?: string;
}

export function ProgressRing({
  value,
  max = 100,
  size = 120,
  strokeWidth = 10,
  color = 'var(--color-accent-bronze)',
  trackColor = 'var(--color-surface-tertiary)',
  label,
  sublabel,
  ariaLabel,
}: ProgressRingProps): React.ReactElement {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(value, max));
  const pct = max === 0 ? 0 : clamped / max;
  const dashoffset = circumference * (1 - pct);

  return (
    <div className="inline-flex flex-col items-center gap-2" role="img" aria-label={ariaLabel}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashoffset}
          className="transition-all duration-slow ease-default"
        />
      </svg>
      {(label || sublabel) && (
        <div className="text-center">
          {label && <div className="text-2xl font-semibold text-ink-primary">{label}</div>}
          {sublabel && <div className="text-sm text-ink-tertiary">{sublabel}</div>}
        </div>
      )}
    </div>
  );
}
