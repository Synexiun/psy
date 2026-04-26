'use client';
/**
 * Spinner — standalone SVG loading indicator extracted from web.tsx.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Spinner exported from web.tsx;
 * consuming code may import from either location.
 *
 * Design notes:
 *   - Uses `currentColor` for stroke — inherits from the parent's text colour.
 *     No token mapping needed; the component is colour-agnostic by design.
 *   - Uses `animate-spin` from Tailwind. The global `@media (prefers-reduced-motion: reduce)`
 *     rule in globals.css sets `animation-duration: 0.01ms !important`, effectively
 *     stopping the spin for users who prefer reduced motion.
 *   - Geometry (radius, circumference, dash, gap) is a regression-guarded contract;
 *     do NOT alter the math without updating the corresponding test expectations.
 *
 * Size mapping (px):
 *   sm → 16 × 16
 *   md → 24 × 24
 *   lg → 32 × 32
 *
 * Radius formula:
 *   r = (dim - 6) / 2
 *   (strokeWidth = 3, half inset per side = 1.5, total inset = 3)
 *
 * Quarter-arc dash pattern:
 *   circumference = 2π × r
 *   dash          = circumference × 0.25
 *   gap           = circumference − dash
 */
import * as React from 'react';

export type SpinnerSize = 'sm' | 'md' | 'lg';

export interface SpinnerProps {
  size?: SpinnerSize;
  className?: string;
  label?: string;
}

export function Spinner({
  size = 'md',
  className = '',
  label = 'Loading',
}: SpinnerProps): React.ReactElement {
  const px: Record<SpinnerSize, number> = { sm: 16, md: 24, lg: 32 };
  const dim = px[size];
  const radius = (dim - 6) / 2; // strokeWidth=3, so half=1.5 inset per side → 3 total
  const circumference = 2 * Math.PI * radius;
  // Quarter-arc: dash = 25% of circumference, gap = rest
  const dash = circumference * 0.25;
  const gap = circumference - dash;

  return (
    <svg
      width={dim}
      height={dim}
      viewBox={`0 0 ${dim} ${dim}`}
      className={`animate-spin ${className}`}
      role="status"
      aria-label={label}
    >
      <circle
        cx={dim / 2}
        cy={dim / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={3}
        strokeLinecap="round"
        strokeDasharray={`${dash} ${gap}`}
        strokeDashoffset={0}
      />
    </svg>
  );
}
