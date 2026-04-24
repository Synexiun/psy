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

export type CardPadding = 'sm' | 'md' | 'lg';
export type CardShadow = 'none' | 'sm' | 'md';
export type CardAs = 'div' | 'article' | 'section';

export interface CardProps extends React.ComponentPropsWithoutRef<'div'> {
  /** Semantic element to render as. Defaults to "div". */
  as?: CardAs;
  /** Internal padding scale. Defaults to "md". */
  padding?: CardPadding;
  /** Box shadow scale. Defaults to "sm". */
  shadow?: CardShadow;
  /** Legacy tone prop — still accepted for backward compat. */
  tone?: 'neutral' | 'calm' | 'warning' | 'crisis';
  /** Subtle lift on hover. */
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

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps extends React.ComponentPropsWithoutRef<'span'> {
  /** Semantic color variant. Defaults to "default". */
  variant?: BadgeVariant;
  /** Size scale. Defaults to "sm". */
  size?: BadgeSize;
  /** Legacy tone prop — still accepted for backward compat. */
  tone?: 'neutral' | 'calm' | 'warning' | 'crisis' | 'success';
}

export interface SkeletonProps extends React.ComponentPropsWithoutRef<'div'> {
  variant?: 'text' | 'circle' | 'rect';
  width?: string;
  height?: string;
}

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------

export type InputType =
  | 'text'
  | 'email'
  | 'password'
  | 'number'
  | 'tel'
  | 'search'
  | 'url';

export interface InputProps {
  id?: string;
  name?: string;
  type?: InputType;
  value?: string | number;
  defaultValue?: string | number;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  autoComplete?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  onFocus?: React.FocusEventHandler<HTMLInputElement>;
  className?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean | 'true' | 'false';
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  function Input(
    {
      type = 'text',
      disabled = false,
      className = '',
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref,
  ): React.ReactElement {
    const isInvalid = ariaInvalid === true || ariaInvalid === 'true';

    const base =
      'w-full rounded-lg border border-[hsl(220,14%,82%)] bg-white px-3 py-2.5 text-sm text-[hsl(222,47%,11%)] placeholder:text-[hsl(215,16%,57%)] transition-colors min-h-[44px]';
    const focusCls =
      'focus:outline-none focus:ring-2 focus:ring-[hsl(217,91%,52%)]/30 focus:border-[hsl(217,91%,52%)]';
    const disabledCls = disabled
      ? 'cursor-not-allowed opacity-50 bg-[hsl(220,14%,96%)]'
      : '';
    const invalidCls = isInvalid
      ? 'border-[hsl(0,84%,60%)] focus:ring-[hsl(0,84%,60%)]/30'
      : '';

    return (
      <input
        ref={ref}
        type={type}
        disabled={disabled}
        aria-invalid={ariaInvalid}
        className={`${base} ${focusCls} ${disabledCls} ${invalidCls} ${className}`.trim()}
        {...props}
      />
    );
  },
);

// ---------------------------------------------------------------------------
// Textarea
// ---------------------------------------------------------------------------

export type TextareaResize = 'none' | 'vertical' | 'horizontal';

export interface TextareaProps {
  id?: string;
  name?: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  autoComplete?: string;
  rows?: number;
  maxLength?: number;
  resize?: TextareaResize;
  onChange?: React.ChangeEventHandler<HTMLTextAreaElement>;
  onBlur?: React.FocusEventHandler<HTMLTextAreaElement>;
  onFocus?: React.FocusEventHandler<HTMLTextAreaElement>;
  className?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean | 'true' | 'false';
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea(
    {
      rows = 3,
      resize = 'vertical',
      disabled = false,
      className = '',
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref,
  ): React.ReactElement {
    const isInvalid = ariaInvalid === true || ariaInvalid === 'true';

    const base =
      'w-full rounded-lg border border-[hsl(220,14%,82%)] bg-white px-3 py-2.5 text-sm text-[hsl(222,47%,11%)] placeholder:text-[hsl(215,16%,57%)] transition-colors min-h-[88px]';
    const focusCls =
      'focus:outline-none focus:ring-2 focus:ring-[hsl(217,91%,52%)]/30 focus:border-[hsl(217,91%,52%)]';
    const disabledCls = disabled
      ? 'cursor-not-allowed opacity-50 bg-[hsl(220,14%,96%)]'
      : '';
    const invalidCls = isInvalid
      ? 'border-[hsl(0,84%,60%)] focus:ring-[hsl(0,84%,60%)]/30'
      : '';
    const resizeCls: Record<TextareaResize, string> = {
      none: 'resize-none',
      vertical: 'resize-y',
      horizontal: 'resize-x',
    };

    return (
      <textarea
        ref={ref}
        rows={rows}
        disabled={disabled}
        aria-invalid={ariaInvalid}
        className={`${base} ${focusCls} ${disabledCls} ${invalidCls} ${resizeCls[resize]} ${className}`.trim()}
        {...props}
      />
    );
  },
);

// ---------------------------------------------------------------------------
// Spinner
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Divider
// ---------------------------------------------------------------------------

export type DividerOrientation = 'horizontal' | 'vertical';

export interface DividerProps {
  className?: string;
  label?: string;
  orientation?: DividerOrientation;
}

export function Divider({
  className = '',
  label,
  orientation = 'horizontal',
}: DividerProps): React.ReactElement {
  if (orientation === 'vertical') {
    return (
      <div
        role="separator"
        aria-orientation="vertical"
        className={`inline-block h-full w-px self-stretch border-l border-[hsl(220,14%,90%)] ${className}`.trim()}
      />
    );
  }

  if (label) {
    return (
      <div
        role="separator"
        aria-orientation="horizontal"
        className={`flex items-center gap-0 ${className}`.trim()}
      >
        <span className="flex-1 border-t border-[hsl(220,14%,90%)]" aria-hidden="true" />
        <span className="px-3 text-xs text-[hsl(215,16%,57%)]">{label}</span>
        <span className="flex-1 border-t border-[hsl(220,14%,90%)]" aria-hidden="true" />
      </div>
    );
  }

  return (
    <hr
      role="separator"
      className={`border-t border-[hsl(220,14%,90%)] ${className}`.trim()}
    />
  );
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
        'bg-crisis-600 text-white hover:bg-crisis-700 active:bg-crisis-800 shadow-sm hover:shadow',
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
  function Card(
    {
      as: Tag = 'div',
      padding = 'md',
      shadow = 'sm',
      tone,
      hover = false,
      className = '',
      children,
      ...props
    },
    ref,
  ): React.ReactElement {
    const base = 'rounded-xl border border-[hsl(220,14%,90%)] bg-white transition-all duration-base ease-standard';

    // Padding scale
    const paddingCls: Record<CardPadding, string> = {
      sm: 'p-4',
      md: 'p-5',
      lg: 'p-6',
    };

    // Shadow scale
    const shadowCls: Record<CardShadow, string> = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
    };

    // Legacy tone overrides border + bg (backward compat)
    const toneCls: Record<string, string> = {
      neutral: 'border-surface-200',
      calm: 'border-calm-200 bg-calm-50/40',
      warning: 'border-amber-200 bg-amber-50/40',
      crisis: 'border-crisis-200 bg-crisis-50/40',
    };

    const hoverCls = hover ? 'hover:-translate-y-0.5 hover:shadow-md cursor-pointer' : '';
    const effectiveTone = tone !== undefined ? (toneCls[tone] ?? '') : '';

    return (
      // @ts-expect-error — polymorphic element: Tag is constrained to CardAs ('div'|'article'|'section')
      <Tag
        ref={ref}
        className={`${base} ${paddingCls[padding]} ${shadowCls[shadow]} ${effectiveTone} ${hoverCls} ${className}`.trim()}
        {...props}
      >
        {children}
      </Tag>
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
  function Badge(
    {
      variant,
      size = 'sm',
      tone,
      className = '',
      children,
      ...props
    },
    ref,
  ): React.ReactElement {
    const base = 'rounded-full font-medium inline-flex items-center transition-colors';

    // Size scale
    const sizeCls: Record<BadgeSize, string> = {
      sm: 'text-xs px-2 py-0.5',
      md: 'text-sm px-2.5 py-1',
    };

    // New variant API (takes priority over legacy tone)
    const variantCls: Record<BadgeVariant, string> = {
      default: 'bg-[hsl(217,91%,96%)] text-[hsl(217,91%,32%)]',
      success: 'bg-[hsl(142,71%,93%)] text-[hsl(142,71%,25%)]',
      warning: 'bg-[hsl(38,92%,93%)] text-[hsl(38,92%,28%)]',
      danger: 'bg-[hsl(0,84%,95%)] text-[hsl(0,84%,40%)]',
      info: 'bg-[hsl(220,14%,94%)] text-[hsl(220,14%,30%)]',
      neutral: 'bg-[hsl(220,14%,94%)] text-[hsl(220,14%,46%)]',
    };

    // Legacy tone fallback (backward compat, only used when variant is not provided)
    const toneCls: Record<string, string> = {
      neutral: 'bg-surface-200 text-ink-700',
      calm: 'bg-calm-100 text-calm-700',
      warning: 'bg-amber-100 text-amber-700',
      crisis: 'bg-crisis-100 text-crisis-700',
      success: 'bg-calm-100 text-calm-700',
    };

    // Resolve color: explicit variant wins, then legacy tone, then default variant
    const colorCls =
      variant !== undefined
        ? variantCls[variant]
        : tone !== undefined
          ? (toneCls[tone] ?? variantCls['default'])
          : variantCls['default'];

    return (
      <span ref={ref} className={`${base} ${sizeCls[size]} ${colorCls} ${className}`.trim()} {...props}>
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
