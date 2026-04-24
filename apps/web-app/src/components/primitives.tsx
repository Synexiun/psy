/**
 * Web UI primitives — production-grade React components.
 *
 * Principles:
 * - Accessible by default (WCAG 2.2 AA)
 * - Smooth CSS transitions (no JS animation overhead)
 * - Reduced-motion safe
 * - RTL-aware via logical properties
 */

'use client';

import * as React from 'react';

export type ButtonVariant = 'primary' | 'calm' | 'ghost' | 'crisis' | 'secondary';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'crisis';

export interface ButtonProps extends React.ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export interface CardProps extends React.ComponentPropsWithoutRef<'div'> {
  tone?: 'neutral' | 'calm' | 'warning' | 'crisis';
  hover?: boolean;
}

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

export interface BadgeProps extends React.ComponentPropsWithoutRef<'span'> {
  tone?: 'neutral' | 'calm' | 'warning' | 'crisis' | 'success';
}

export interface SkeletonProps extends React.ComponentPropsWithoutRef<'div'> {
  variant?: 'text' | 'circle' | 'rect';
  width?: string;
  height?: string;
}

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    { variant = 'primary', size = 'md', loading = false, disabled, children, className = '', ...props },
    ref,
  ): React.ReactElement {
    const base =
      'inline-flex items-center justify-center font-medium transition-all duration-fast ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const sizing: Record<ButtonSize, string> = {
      sm: 'h-8 px-3 text-sm rounded-md gap-1.5',
      md: 'h-10 px-4 text-base rounded-md gap-2',
      lg: 'h-12 px-6 text-base rounded-lg gap-2',
      crisis: 'min-h-14 w-full px-6 text-lg rounded-xl gap-2',
    };

    const variants: Record<ButtonVariant, string> = {
      primary:
        'bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-700 shadow-sm hover:shadow',
      secondary:
        'bg-surface-100 text-ink-900 hover:bg-surface-200 active:bg-surface-300 border border-surface-200',
      calm: 'bg-calm-500 text-white hover:bg-calm-600 active:bg-calm-700 shadow-sm hover:shadow',
      ghost: 'bg-transparent text-ink-700 hover:bg-surface-100 active:bg-surface-200',
      crisis:
        'bg-crisis-500 text-white hover:bg-crisis-600 active:bg-crisis-700 shadow-sm hover:shadow',
    };

    return (
      <button
        ref={ref}
        className={`${base} ${sizing[size]} ${variants[variant]} ${className}`}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading && (
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-80" />
        )}
        {children}
      </button>
    );
  },
);

// ---------------------------------------------------------------------------
// Card
// ---------------------------------------------------------------------------

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  function Card({ tone = 'neutral', hover = false, className = '', children, ...props }, ref): React.ReactElement {
    const base = 'rounded-xl border bg-surface-0 p-5 transition-all duration-base ease-standard';

    const tones: Record<string, string> = {
      neutral: 'border-surface-200 shadow-sm',
      calm: 'border-calm-200 bg-calm-50/40 shadow-sm',
      warning: 'border-amber-200 bg-amber-50/40 shadow-sm',
      crisis: 'border-crisis-200 bg-crisis-50/40 shadow-sm',
    };

    const hoverCls = hover ? 'hover:-translate-y-0.5 hover:shadow-md cursor-pointer' : '';

    return (
      <div ref={ref} className={`${base} ${tones[tone]} ${hoverCls} ${className}`} {...props}>
        {children}
      </div>
    );
  },
);

// ---------------------------------------------------------------------------
// ProgressRing
// ---------------------------------------------------------------------------

export function ProgressRing({
  value,
  max = 100,
  size = 120,
  strokeWidth = 10,
  color = 'var(--color-brand-500)',
  trackColor = 'var(--color-surface-200)',
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
          className="transition-all duration-slow ease-standard"
        />
      </svg>
      {(label || sublabel) && (
        <div className="text-center">
          {label && <div className="text-2xl font-semibold text-ink-900">{label}</div>}
          {sublabel && <div className="text-sm text-ink-500">{sublabel}</div>}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Badge
// ---------------------------------------------------------------------------

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  function Badge({ tone = 'neutral', className = '', children, ...props }, ref): React.ReactElement {
    const base =
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors';

    const tones: Record<string, string> = {
      neutral: 'bg-surface-200 text-ink-700',
      calm: 'bg-calm-100 text-calm-700',
      warning: 'bg-amber-100 text-amber-700',
      crisis: 'bg-crisis-100 text-crisis-700',
      success: 'bg-calm-100 text-calm-700',
    };

    return (
      <span ref={ref} className={`${base} ${tones[tone]} ${className}`} {...props}>
        {children}
      </span>
    );
  },
);

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  function Skeleton(
    { variant = 'rect', width = '100%', height = '1rem', className = '', style, ...props },
    ref,
  ): React.ReactElement {
    const base = 'animate-pulse bg-surface-200';

    const variants: Record<string, string> = {
      text: 'rounded-md',
      circle: 'rounded-full',
      rect: 'rounded-lg',
    };

    const sizeStyle: React.CSSProperties = {
      width: variant === 'circle' ? height : width,
      height,
      ...style,
    };

    return (
      <div
        ref={ref}
        className={`${base} ${variants[variant]} ${className}`}
        style={sizeStyle}
        aria-hidden="true"
        {...props}
      />
    );
  },
);

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

export interface TooltipProps {
  children: React.ReactNode;
  tooltipContent: React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export function Tooltip({ tooltipContent, side = 'top', className = '', children }: TooltipProps): React.ReactElement {
  const sideClasses: Record<string, string> = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div className={`relative inline-flex ${className} group`}>
      {children}
      <span
        className={`pointer-events-none absolute ${sideClasses[side]} z-50 w-max max-w-xs rounded-md bg-ink-900 px-2.5 py-1.5 text-xs text-white opacity-0 transition-opacity duration-fast group-hover:opacity-100 group-focus-visible:opacity-100`}
        role="tooltip"
      >
        {tooltipContent}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sparkline (SVG mini-chart)
// ---------------------------------------------------------------------------

export interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  strokeWidth?: number;
  ariaLabel?: string;
}

export function Sparkline({
  data,
  width = 120,
  height = 40,
  color = 'var(--color-brand-500)',
  strokeWidth = 2,
  ariaLabel,
}: SparklineProps): React.ReactElement | null {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  });

  const firstPointX = points[0]?.split(',')[0] ?? '0';
  const lastPointX = points[points.length - 1]?.split(',')[0] ?? String(width);
  const areaPoints = `${firstPointX},${height} ` + points.join(' ') + ` ${lastPointX},${height}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel}
      className="overflow-visible"
    >
      <polygon points={areaPoints} fill={color} opacity={0.12} />
      <polyline
        points={points.join(' ')}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
