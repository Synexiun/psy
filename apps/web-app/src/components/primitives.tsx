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
      'inline-flex items-center justify-center font-medium transition-all duration-fast ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const sizing: Record<ButtonSize, string> = {
      sm: 'h-8 px-3 text-sm rounded-md gap-1.5',
      md: 'h-10 px-4 text-base rounded-md gap-2',
      lg: 'h-12 px-6 text-base rounded-lg gap-2',
      crisis: 'min-h-14 w-full px-6 text-lg rounded-xl gap-2',
    };

    const variants: Record<ButtonVariant, string> = {
      primary:
        'bg-accent-bronze text-white hover:bg-accent-bronze-soft active:bg-accent-bronze-soft shadow-sm hover:shadow',
      secondary:
        'bg-surface-tertiary text-ink-primary hover:bg-border-subtle active:bg-border-emphasis border border-border-subtle',
      calm: 'bg-signal-stable text-white hover:bg-signal-stable/90 active:bg-signal-stable/80 shadow-sm hover:shadow',
      ghost: 'bg-transparent text-ink-secondary hover:bg-surface-tertiary active:bg-border-subtle',
      crisis:
        'bg-signal-crisis text-white hover:bg-signal-crisis/90 active:bg-signal-crisis/80 shadow-sm hover:shadow',
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
    const base = 'rounded-xl border bg-surface-secondary p-5 transition-all duration-base ease-standard';

    const tones: Record<string, string> = {
      neutral: 'border-border-subtle shadow-sm',
      calm: 'border-signal-stable/30 bg-signal-stable/5 shadow-sm',
      warning: 'border-signal-warning/30 bg-signal-warning/5 shadow-sm',
      crisis: 'border-signal-crisis/30 bg-signal-crisis/5 shadow-sm',
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
  color = 'var(--color-accent-bronze)',
  trackColor = 'var(--color-border-subtle)',
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
          {label && <div className="text-2xl font-semibold text-ink-primary">{label}</div>}
          {sublabel && <div className="text-sm text-ink-tertiary">{sublabel}</div>}
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
      neutral: 'bg-surface-tertiary text-ink-secondary',
      calm: 'bg-signal-stable/15 text-signal-stable',
      warning: 'bg-signal-warning/15 text-signal-warning',
      crisis: 'bg-signal-crisis/15 text-signal-crisis',
      success: 'bg-signal-stable/15 text-signal-stable',
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
    const base = 'animate-pulse bg-surface-tertiary';

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
    left: 'right-full top-1/2 -translate-y-1/2 me-2',
    right: 'left-full top-1/2 -translate-y-1/2 ms-2',
  };

  return (
    <div className={`relative inline-flex ${className} group`}>
      {children}
      <span
        className={`pointer-events-none absolute ${sideClasses[side]} z-50 w-max max-w-xs rounded-md bg-ink-primary px-2.5 py-1.5 text-xs text-surface-primary opacity-0 transition-opacity duration-fast group-hover:opacity-100 group-focus-visible:opacity-100`}
        role="tooltip"
      >
        {tooltipContent}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sparkline (SVG mini-chart) — re-exported from the design-system package
// ---------------------------------------------------------------------------

export type { SparklineProps } from '@disciplineos/design-system/primitives/Sparkline';
export { Sparkline } from '@disciplineos/design-system/primitives/Sparkline';
