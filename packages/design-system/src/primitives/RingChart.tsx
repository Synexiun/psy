'use client';
/**
 * RingChart — multi-segment SVG ring chart primitive for Discipline OS.
 *
 * Renders a single SVG ring divided into multiple colored segments.
 * Common use cases: skill distribution (% of sessions per category),
 * PHQ-9 score breakdown, weekly mood distribution.
 *
 * No center text by default — callers compose center content via the
 * `centerContent` slot prop.
 *
 * Geometry is consistent with ProgressRing:
 *   radius = (size - strokeWidth) / 2
 *   circumference = 2 * Math.PI * radius
 *   SVG wrapper has -rotate-90 so 0° is at the top.
 *
 * Each segment is a <circle> with:
 *   strokeDasharray={circumference}
 *   strokeDashoffset = circumference - arcLength
 *   transform="rotate(startAngleDeg, cx, cy)"
 *
 * Gaps between segments are subtracted from each segment's arc length.
 * If only one segment, no gap is applied.
 * If total === 0, only the track circle is rendered.
 */
import * as React from 'react';

export interface RingSegment {
  /** Identifier — used as React key */
  id: string;
  /** Numeric value of this segment */
  value: number;
  /** CSS color string — caller controls color (Quiet Strength tokens resolve to CSS vars) */
  color: string;
  /** Human-readable label for this segment — used in aria description */
  label: string;
}

export interface RingChartProps {
  /** Ordered array of segments. Total of all values = full ring (auto-normalized). */
  segments: RingSegment[];
  /** SVG size in px (default 120) */
  size?: number;
  /** Ring stroke width in px (default 10) */
  strokeWidth?: number;
  /** Background track color (default 'var(--color-surface-tertiary)') */
  trackColor?: string;
  /** Gap between segments in degrees (default 2) */
  gapDegrees?: number;
  /** Content rendered absolutely-centered inside the ring */
  centerContent?: React.ReactNode;
  /** aria-label for the root wrapper */
  ariaLabel?: string;
  /** Additional classes on the root wrapper div */
  className?: string;
}

export function RingChart({
  segments,
  size = 120,
  strokeWidth = 10,
  trackColor = 'var(--color-surface-tertiary)',
  gapDegrees = 2,
  centerContent,
  ariaLabel,
  className,
}: RingChartProps): React.ReactElement {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const cx = size / 2;
  const cy = size / 2;

  const total = segments.reduce((sum, seg) => sum + seg.value, 0);

  // Convert gapDegrees to arc length fraction of circumference.
  // Only apply gaps when there are multiple segments.
  const gapArc = segments.length > 1 ? (gapDegrees / 360) * circumference : 0;

  // Build per-segment rendering data.
  let startAngle = 0; // degrees; SVG is rotated -90° so 0° maps to the top

  const segmentCircles: React.ReactElement[] = [];

  if (total > 0) {
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      // noUncheckedIndexedAccess guard
      if (seg === undefined) continue;

      const fraction = seg.value / total;
      const arcLength = fraction * circumference - gapArc;

      if (arcLength > 0) {
        const dashoffset = circumference - arcLength;

        segmentCircles.push(
          <circle
            key={seg.id}
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke={seg.color}
            strokeWidth={strokeWidth}
            strokeLinecap="butt"
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
            transform={`rotate(${startAngle}, ${cx}, ${cy})`}
            className="transition-all duration-slow ease-default"
          />,
        );
      }

      startAngle += fraction * 360;
    }
  }

  return (
    <div
      role="img"
      aria-label={ariaLabel}
      className={['relative inline-flex items-center justify-center', className]
        .filter(Boolean)
        .join(' ')}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
        aria-hidden="true"
      >
        {/* Background track */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        {/* Segments */}
        {segmentCircles}
      </svg>

      {centerContent !== undefined && (
        <div className="absolute inset-0 flex items-center justify-center">
          {centerContent}
        </div>
      )}
    </div>
  );
}
