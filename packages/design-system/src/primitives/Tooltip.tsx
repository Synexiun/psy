'use client';
/**
 * Tooltip — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx and upgraded
 * from a CSS-only hover implementation to @radix-ui/react-tooltip. Radix
 * handles ARIA role="tooltip", keyboard focus, pointer events, and RTL-safe
 * side-offset placement automatically — no manual sideClasses map needed.
 *
 * API is intentionally identical to the Tooltip exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping (tooltip panel):
 *   bg-ink-900  → bg-ink-primary          (dark tooltip background, token-aligned)
 *   text-white  → text-surface-primary    (high-contrast text on dark bg)
 *   rounded-md px-2.5 py-1.5 text-xs     — kept as neutral utilities
 *
 * RTL: Radix TooltipContent positions relative to the trigger via its own
 * floating-ui/popper layer; physical margin classes are NOT applied. RTL layouts
 * are automatically correct — left/right sides flip with `dir`.
 */
import * as React from 'react';
import * as RadixTooltip from '@radix-ui/react-tooltip';

export interface TooltipProps {
  children: React.ReactNode;
  tooltipContent: React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export function Tooltip({
  children,
  tooltipContent,
  side = 'top',
  className = '',
}: TooltipProps): React.ReactElement {
  return (
    <RadixTooltip.Provider>
      <RadixTooltip.Root>
        <RadixTooltip.Trigger asChild>
          {/* asChild: Radix merges its trigger props onto the single child element,
              avoiding a wrapper <button> that would break inline/flex layouts. */}
          <span className={`inline-flex ${className}`}>{children}</span>
        </RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            side={side}
            sideOffset={6}
            className="z-50 w-max max-w-xs rounded-md bg-ink-primary px-2.5 py-1.5 text-xs text-surface-primary shadow-sm"
          >
            {tooltipContent}
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  );
}
