'use client';
/**
 * Divider — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Divider exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping:
 *   border-[hsl(220,14%,90%)] → border-border-subtle
 *   text-[hsl(215,16%,57%)]   → text-ink-tertiary
 *
 * RTL note:
 *   The vertical Divider uses border-s (border-inline-start) — the logical
 *   property equivalent of the physical border-l. For a separator this is
 *   purely visual and carries no RTL semantics, but using the logical
 *   property keeps the codebase consistent with the rest of the system.
 *   Horizontal dividers use border-t which is axis-neutral.
 */
import * as React from 'react';

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
        className={`inline-block h-full w-px self-stretch border-s border-border-subtle ${className}`.trim()}
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
        <span className="flex-1 border-t border-border-subtle" aria-hidden="true" />
        <span className="px-3 text-xs text-ink-tertiary">{label}</span>
        <span className="flex-1 border-t border-border-subtle" aria-hidden="true" />
      </div>
    );
  }

  return (
    <hr
      role="separator"
      className={`border-t border-border-subtle ${className}`.trim()}
    />
  );
}
