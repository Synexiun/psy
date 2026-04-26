'use client';

/**
 * Sparkline — SVG mini-chart backed by @visx/shape and @visx/scale.
 *
 * Replaces the hand-rolled polyline/polygon implementation with Visx
 * LinePath + AreaClosed, preserving the public prop contract and the
 * monotone-X curve for smooth clinical trend visualisation.
 *
 * Prop contract is immutable — changing it requires a design-system
 * major-version bump and a coordinated consumer migration.
 */

import * as React from 'react';
import { LinePath, AreaClosed } from '@visx/shape';
import { scaleLinear } from '@visx/scale';
import { curveMonotoneX } from '@visx/curve';

// ---------------------------------------------------------------------------
// Public prop contract — do NOT change without a major-version bump
// ---------------------------------------------------------------------------

export interface SparklineProps {
  data: number[];
  width?: number;        // default 120
  height?: number;       // default 40
  color?: string;        // default 'var(--color-accent-bronze)'
  strokeWidth?: number;  // default 2
  ariaLabel?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Sparkline({
  data,
  width = 120,
  height = 40,
  color = 'var(--color-accent-bronze)',
  strokeWidth = 2,
  ariaLabel,
}: SparklineProps): React.ReactElement | null {
  // Guard: need at least two points to draw a meaningful line
  if (data.length < 2) return null;

  const minVal = Math.min(...data);
  const maxVal = Math.max(...data);

  // x-scale: index → pixel column
  const xScale = scaleLinear({
    domain: [0, data.length - 1],
    range: [0, width],
  });

  // y-scale: value → pixel row (inverted — SVG y=0 is top)
  const yScale = scaleLinear({
    domain: [minVal, maxVal === minVal ? minVal + 1 : maxVal],
    range: [height, 0],
  });

  // Accessors for Visx shape components
  const getX = (_: number, i: number): number => xScale(i) ?? 0;
  const getY = (d: number): number => yScale(d) ?? 0;

  // y-baseline accessor used by AreaClosed to close the path at the bottom
  const getY0 = (): number => height;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel}
      className="overflow-visible"
    >
      {/* Filled area under the line — low opacity for subtle visual weight */}
      <AreaClosed
        data={data}
        x={getX}
        y={getY}
        y0={getY0}
        yScale={yScale}
        curve={curveMonotoneX}
        fill={color}
        fillOpacity={0.12}
        stroke="none"
      />

      {/* Main trend line */}
      <LinePath
        data={data}
        x={getX}
        y={getY}
        curve={curveMonotoneX}
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
