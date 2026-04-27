'use client';
/**
 * BarChart — Visx-backed vertical bar chart for instrument trends over time.
 *
 * Common use cases: weekly PHQ-9 scores, session counts per day, GAD-7 over time.
 * Designed for clinical dashboard screens.
 *
 * Uses @visx/scale (scaleBand, scaleLinear), @visx/shape (Bar),
 * @visx/axis (AxisBottom), @visx/group (Group).
 *
 * Prop contract is immutable — changing it requires a design-system
 * major-version bump and a coordinated consumer migration.
 */

import * as React from 'react';
import { Bar } from '@visx/shape';
import { scaleBand, scaleLinear } from '@visx/scale';
import { AxisBottom } from '@visx/axis';
import { Group } from '@visx/group';

// ---------------------------------------------------------------------------
// Public prop contract — do NOT change without a major-version bump
// ---------------------------------------------------------------------------

export interface BarDatum {
  /** x-axis label (e.g. "Mon", "Week 1", "Apr 14") */
  label: string;
  /** Numeric value — the bar height */
  value: number;
  /** Optional color override — defaults to the chart's color prop */
  color?: string;
}

export interface BarChartProps {
  data: BarDatum[];
  /** Chart width in px (default 320) */
  width?: number;
  /** Chart height in px (default 200) */
  height?: number;
  /** Margin around the plot area (default { top: 16, right: 8, bottom: 32, left: 32 }) */
  margin?: { top: number; right: number; bottom: number; left: number };
  /** Bar fill color CSS string — default 'var(--color-accent-bronze)' */
  color?: string;
  /** Y-axis label text */
  yAxisLabel?: string;
  /** Max value for y-axis — auto if omitted (max of data) */
  yMax?: number;
  /** aria-label for the SVG */
  ariaLabel?: string;
  /** Additional classes on the root div */
  className?: string;
}

const defaultMargin = { top: 16, right: 8, bottom: 32, left: 32 };

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BarChart({
  data,
  width = 320,
  height = 200,
  margin = defaultMargin,
  color = 'var(--color-accent-bronze)',
  yAxisLabel,
  yMax,
  ariaLabel,
  className,
}: BarChartProps): React.ReactElement {
  // Empty state
  if (data.length === 0) {
    return (
      <div
        role="img"
        {...(ariaLabel !== undefined && { 'aria-label': ariaLabel })}
        className={['text-ink-tertiary text-sm flex items-center justify-center', className]
          .filter(Boolean)
          .join(' ')}
        style={{ width, height }}
      >
        No data
      </div>
    );
  }

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // x-scale: category bands
  const xScale = scaleBand({
    domain: data.map((d) => d.label),
    range: [0, innerWidth],
    padding: 0.3,
  });

  // y-scale: linear value
  const yDomainMax = yMax ?? Math.max(...data.map((d) => d.value), 1);
  const yScale = scaleLinear({
    domain: [0, yDomainMax],
    range: [innerHeight, 0],
  });

  return (
    <div
      role="img"
      {...(ariaLabel !== undefined && { 'aria-label': ariaLabel })}
      className={className}
    >
      <svg width={width} height={height} aria-hidden="true">
        <Group top={margin.top} left={margin.left}>
          {/* Optional y-axis label — rotated text at top-left */}
          {yAxisLabel !== undefined && (
            <text
              x={0}
              y={0}
              transform="rotate(-90)"
              textAnchor="end"
              fill="var(--color-ink-tertiary)"
              fontSize={10}
            >
              {yAxisLabel}
            </text>
          )}

          {/* Bars */}
          {data.map((d) => {
            const barWidth = xScale.bandwidth();
            const barHeight = innerHeight - (yScale(d.value) ?? 0);
            const barX = xScale(d.label) ?? 0;
            const barY = innerHeight - barHeight;

            return (
              <Bar
                key={d.label}
                x={barX}
                y={barY}
                width={barWidth}
                height={barHeight}
                fill={d.color ?? color}
              />
            );
          })}

          {/* X-axis */}
          <AxisBottom
            top={innerHeight}
            scale={xScale}
            stroke="var(--color-border-subtle)"
            tickStroke="var(--color-border-subtle)"
            tickLabelProps={{ fill: 'var(--color-ink-tertiary)', fontSize: 11, textAnchor: 'middle' }}
          />
        </Group>
      </svg>
    </div>
  );
}
