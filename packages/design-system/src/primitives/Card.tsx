'use client';
/**
 * Card — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Card exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping:
 *   border-[hsl(220,14%,90%)]  → border-border-subtle      (Quiet Strength neutral border)
 *   bg-white                   → bg-surface-primary         (Quiet Strength surface base)
 *   ease-standard              → ease-default               (--ease-default in @theme)
 *   duration-base              → duration-base              (already a token — unchanged)
 *
 * Tone mapping:
 *   neutral  → border-border-subtle                         (no bg shift)
 *   calm     → border-accent-teal-soft bg-accent-teal-soft/20
 *   warning  → border-signal-warning   bg-signal-warning/10
 *   crisis   → border-signal-crisis    bg-signal-crisis/10
 */
import * as React from 'react';

export type CardPadding = 'sm' | 'md' | 'lg';
export type CardShadow = 'none' | 'sm' | 'md';
export type CardAs = 'div' | 'article' | 'section';

export interface CardProps extends React.ComponentPropsWithoutRef<'div'> {
  as?: CardAs;
  padding?: CardPadding;
  shadow?: CardShadow;
  tone?: 'neutral' | 'calm' | 'warning' | 'crisis';
  hover?: boolean;
}

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
    const base =
      'rounded-xl border border-border-subtle bg-surface-primary transition-all duration-base ease-default';

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

    // Quiet Strength tone overrides — border + bg
    const toneCls: Record<string, string> = {
      neutral: 'border-border-subtle',
      calm: 'border-accent-teal-soft bg-accent-teal-soft/20',
      warning: 'border-signal-warning bg-signal-warning/10',
      crisis: 'border-signal-crisis bg-signal-crisis/10',
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
