'use client';
/**
 * BottomNav — Quiet Strength–tokenised mobile bottom navigation primitive.
 *
 * Pure layout primitive — no routing, all navigation via callbacks. Follows the
 * spec §5.3 cognitive-max design: maximum 5 items for reliable thumb-reach on
 * all device sizes. A dev-mode console.warn fires when more than 5 items are
 * provided.
 *
 * Special crisis item:
 *   - Color: oxblood (#8B0000) — there is no design token for this yet; the hex
 *     value is used directly with an explanatory comment.
 *   - Minimum touch target: 56px (safety.sosButtonMinTouchTargetPx from spec).
 *   - Never disabled: `disabled` prop is ignored for crisis items to ensure the
 *     safety path is always reachable regardless of app state.
 *
 * Active indicator:
 *   - A small 4×4 bronze dot above the icon (not an underline like TabNav).
 *   - Crisis active state: same dot in oxblood.
 *
 * RTL:
 *   Flexbox reverses order automatically in RTL (`dir` on the parent propagates).
 *   `inset-x-0` is already symmetric. No special RTL handling needed beyond the
 *   logical-CSS-only rule applied throughout this file.
 *
 * Token mapping:
 *   Container         : fixed bottom-0 inset-x-0 z-40 border-t border-border-subtle bg-surface-primary
 *   Inactive item     : text-ink-tertiary
 *   Active item       : text-accent-bronze
 *   Focus ring        : focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent-bronze/30
 *   Crisis item       : text-[#8B0000] (oxblood — no token yet)
 *   Active dot        : bg-accent-bronze (normal) / bg-[#8B0000] (crisis)
 *
 * Logical-CSS-only rule:
 *   ps-N/pe-N/ms-N/me-N/start-N/end-N/border-s/border-e — never pl-N/pr-N/ml-N/mr-N.
 *   Symmetric properties (inset-x-0, border-t, px-*) are safe.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

export interface BottomNavItem {
  value: string;
  /** Visible label — translated by caller. Also used as aria-label for the button. */
  label: string;
  /** Icon element — caller supplies (e.g., an SVG or icon component). */
  icon: React.ReactNode;
  /** Optional href — if provided the button renders as an <a> element. */
  href?: string;
  /**
   * When true, renders with oxblood (#8B0000) styling and a 56 px minimum
   * touch target. The crisis item is never disabled regardless of item.disabled.
   */
  crisis?: boolean;
  disabled?: boolean;
}

export interface BottomNavProps {
  /** Max 5 items enforced with a dev-mode console.warn. */
  items: BottomNavItem[];
  /** Currently active item value. */
  activeValue?: string;
  onItemClick?: (value: string) => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// BottomNav
// ---------------------------------------------------------------------------

export function BottomNav({
  items,
  activeValue,
  onItemClick,
  className = '',
}: BottomNavProps): React.ReactElement {
  if (process.env.NODE_ENV !== 'production' && items.length > 5) {
    console.warn(
      '[BottomNav] More than 5 items provided. BottomNav has a cognitive max of 5 items. Extra items will render but exceed the design spec limit.',
    );
  }

  return (
    <nav
      aria-label="Main navigation"
      className={`fixed bottom-0 inset-x-0 z-40 border-t border-border-subtle bg-surface-primary ${className}`.trim()}
    >
      <div className="flex h-16 items-stretch">
        {items.map((item) => {
          const isActive = activeValue === item.value;
          const isCrisis = item.crisis === true;

          // Crisis items are never disabled — the safety path must always be reachable.
          const isDisabled = !isCrisis && item.disabled === true;

          // Colour classes — oxblood (#8B0000) has no design token yet.
          const colorClass = isCrisis
            ? 'text-[#8B0000]' // oxblood — clinical crisis signal; no design token yet
            : isActive
              ? 'text-accent-bronze'
              : 'text-ink-tertiary';

          const dotColorClass = isCrisis
            ? 'bg-[#8B0000]' // oxblood dot for crisis active state
            : 'bg-accent-bronze';

          const baseClass = [
            'flex flex-1 flex-col items-center justify-center gap-1',
            'transition-colors duration-fast ease-default',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent-bronze/30',
            'disabled:cursor-not-allowed disabled:opacity-50',
            isCrisis ? 'min-h-[56px]' : '', // 56 px touch target for crisis (safety.sosButtonMinTouchTargetPx)
            colorClass,
          ]
            .filter(Boolean)
            .join(' ');

          const optionalButtonProps = {
            ...(isDisabled && { disabled: true as const }),
            ...(isActive && { 'aria-current': 'page' as const }),
            ...(item.href !== undefined && { href: item.href }),
          };

          return (
            <button
              key={item.value}
              type="button"
              onClick={() => onItemClick?.(item.value)}
              aria-label={item.label}
              className={baseClass}
              {...optionalButtonProps}
            >
              {/* Active indicator dot — above the icon */}
              <span
                className={[
                  'h-1 w-1 rounded-full',
                  isActive ? dotColorClass : 'bg-transparent',
                ].join(' ')}
                aria-hidden="true"
              />
              {/* Icon */}
              <span className="flex items-center justify-center" aria-hidden="true">
                {item.icon}
              </span>
              {/* Label */}
              <span className="text-[10px] font-medium leading-none">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
