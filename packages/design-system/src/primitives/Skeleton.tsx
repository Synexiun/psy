'use client';
/**
 * Skeleton — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Skeleton exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping:
 *   bg-surface-200 → bg-surface-tertiary   (Quiet Strength token)
 *
 * TypeScript note:
 *   `variants` is typed as Record<'text'|'circle'|'rect', string> (not the
 *   looser Record<string, string> from web.tsx) so noUncheckedIndexedAccess
 *   does not widen the lookup result to `string | undefined`.
 *
 * Reduced-motion:
 *   `animate-pulse` is suppressed automatically by the global
 *   `@media (prefers-reduced-motion: reduce)` rule in globals.css.
 */
import * as React from 'react';

export interface SkeletonProps extends React.ComponentPropsWithoutRef<'div'> {
  variant?: 'text' | 'circle' | 'rect';
  width?: string;
  height?: string;
}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  function Skeleton(
    { variant = 'rect', width = '100%', height = '1rem', className = '', style, ...props },
    ref,
  ): React.ReactElement {
    const base = 'animate-pulse bg-surface-tertiary';

    const variants: Record<'text' | 'circle' | 'rect', string> = {
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
