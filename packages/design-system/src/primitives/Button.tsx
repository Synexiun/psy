'use client';
/**
 * Button — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Button exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping:
 *   bg-brand-500       → bg-accent-bronze       (hover: opacity-90)
 *   bg-calm-500        → bg-accent-teal         (hover: opacity-90)
 *   bg-crisis-600      → bg-signal-crisis       (hover: opacity-90)
 *   bg-surface-100     → bg-surface-tertiary    (hover: bg-surface-secondary)
 *   text-ink-900       → text-ink-primary
 *   text-ink-700       → text-ink-secondary
 *   focus:ring-brand-* → focus-visible:ring-accent-bronze/30
 *   ease-standard      → ease-default  (--ease-default in @theme)
 */
import * as React from 'react';

export type ButtonVariant = 'primary' | 'calm' | 'ghost' | 'crisis' | 'secondary';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'crisis';

export interface ButtonProps extends React.ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled,
      children,
      className = '',
      ...props
    },
    ref,
  ): React.ReactElement {
    const base =
      'inline-flex items-center justify-center font-medium transition-all duration-fast ease-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const sizing: Record<ButtonSize, string> = {
      sm: 'h-8 px-3 text-sm rounded-md gap-1.5',
      md: 'h-10 px-4 text-base rounded-md gap-2',
      lg: 'h-12 px-6 text-base rounded-lg gap-2',
      crisis: 'min-h-14 w-full px-6 text-lg rounded-xl gap-2',
    };

    const variants: Record<ButtonVariant, string> = {
      primary:
        'bg-accent-bronze text-white hover:opacity-90 active:opacity-80 shadow-sm hover:shadow',
      secondary:
        'bg-surface-tertiary text-ink-primary hover:bg-surface-secondary active:bg-border-subtle border border-border-subtle',
      calm: 'bg-accent-teal text-white hover:opacity-90 active:opacity-80 shadow-sm hover:shadow',
      ghost: 'bg-transparent text-ink-secondary hover:bg-surface-tertiary active:bg-border-subtle',
      crisis:
        'bg-signal-crisis text-white hover:opacity-90 active:opacity-80 shadow-sm hover:shadow',
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
          <span
            className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-80"
            aria-hidden="true"
          />
        )}
        {children}
      </button>
    );
  },
);
