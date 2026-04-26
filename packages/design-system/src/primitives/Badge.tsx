'use client';
/**
 * Badge — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Badge exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping (hardcoded hsl() → Quiet Strength design tokens):
 *   variant.default  bg-[hsl(217,91%,96%)] text-[hsl(217,91%,32%)] → bg-accent-bronze/15 text-accent-bronze
 *   variant.success  bg-[hsl(142,71%,93%)] text-[hsl(142,71%,25%)] → bg-signal-stable/15 text-signal-stable
 *   variant.warning  bg-[hsl(38,92%,93%)]  text-[hsl(38,92%,28%)]  → bg-signal-warning/15 text-signal-warning
 *   variant.danger   bg-[hsl(0,84%,95%)]   text-[hsl(0,84%,40%)]   → bg-signal-crisis/15 text-signal-crisis
 *   variant.info     bg-[hsl(220,14%,94%)] text-[hsl(220,14%,30%)] → bg-surface-tertiary text-ink-secondary
 *   variant.neutral  bg-[hsl(220,14%,94%)] text-[hsl(220,14%,46%)] → bg-surface-tertiary text-ink-tertiary
 *
 * Legacy tone fallback (backward compat, only active when variant is omitted):
 *   tone.neutral → bg-surface-tertiary text-ink-secondary
 *   tone.calm    → bg-accent-teal-soft/30 text-accent-teal
 *   tone.warning → bg-signal-warning/15 text-signal-warning
 *   tone.crisis  → bg-signal-crisis/15 text-signal-crisis
 *   tone.success → bg-signal-stable/15 text-signal-stable
 */
import * as React from 'react';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps extends React.ComponentPropsWithoutRef<'span'> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  tone?: 'neutral' | 'calm' | 'warning' | 'crisis' | 'success';
}

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
      default: 'bg-accent-bronze/15 text-accent-bronze',
      success: 'bg-signal-stable/15 text-signal-stable',
      warning: 'bg-signal-warning/15 text-signal-warning',
      danger:  'bg-signal-crisis/15 text-signal-crisis',
      info:    'bg-surface-tertiary text-ink-secondary',
      neutral: 'bg-surface-tertiary text-ink-tertiary',
    };

    // Legacy tone fallback (backward compat, only used when variant is not provided)
    const toneCls: Record<string, string> = {
      neutral: 'bg-surface-tertiary text-ink-secondary',
      calm:    'bg-accent-teal-soft/30 text-accent-teal',
      warning: 'bg-signal-warning/15 text-signal-warning',
      crisis:  'bg-signal-crisis/15 text-signal-crisis',
      success: 'bg-signal-stable/15 text-signal-stable',
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
