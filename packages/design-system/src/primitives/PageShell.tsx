'use client';
/**
 * PageShell — Quiet Strength–tokenised page-level layout wrapper.
 *
 * Provides a consistent content column with optional heading, optional back
 * navigation, optional heading-row actions, and a body region. It is NOT a
 * full-page layout — TopBar and SidebarNav live outside it. PageShell is the
 * main content column rendered inside those outer chrome elements.
 *
 * Token mapping:
 *   Outer container  : w-full max-w-4xl ps-4 pe-4 py-6 sm:ps-6 sm:pe-6  (logical padding)
 *   Heading (h1)     : text-2xl font-semibold text-ink-primary
 *   Subheading (p)   : text-sm text-ink-tertiary
 *   Back link (a)    : inline-flex items-center gap-1 text-sm text-ink-tertiary
 *                      hover:text-ink-primary transition-colors duration-fast ease-default
 *   Back arrow (svg) : rtl:-scale-x-100  (chevron-left flips in RTL)
 *   Actions div      : flex items-center gap-2 shrink-0
 *
 * RTL: all inline-direction spacing uses logical properties (ps, pe, gap).
 * No physical pl-/pr-/ml-/mr- anywhere in this file. The back-arrow SVG carries
 * `rtl:-scale-x-100` so the chevron points right-to-left in Arabic/Persian
 * without a separate icon variant.
 *
 * No Radix dependency — PageShell is pure layout.
 */
import type * as React from 'react';

export interface PageShellProps {
  /** Page heading — h1, required for accessibility */
  heading: React.ReactNode;
  /** Optional subheading rendered below the heading */
  subheading?: React.ReactNode;
  /** Optional back navigation — rendered as a link above the heading */
  backHref?: string;
  /** Label for the back link (default: "Back") — translate for non-en locales */
  backLabel?: string;
  /** Optional actions rendered in the heading row (end side) */
  actions?: React.ReactNode;
  /** Page body content */
  children: React.ReactNode;
  /** Additional classes on the outermost container */
  className?: string;
}

export function PageShell({
  heading,
  subheading,
  backHref,
  backLabel = 'Back',
  actions,
  children,
  className = '',
}: PageShellProps): React.ReactElement {
  return (
    <div
      className={`flex w-full max-w-4xl flex-col gap-6 ps-4 pe-4 py-6 sm:ps-6 sm:pe-6 ${className}`.trim()}
    >
      {backHref !== undefined && (
        <a
          href={backHref}
          className="inline-flex items-center gap-1 text-sm text-ink-tertiary transition-colors duration-fast ease-default hover:text-ink-primary"
        >
          {/* Chevron-left arrow — mirrors horizontally in RTL via rtl:-scale-x-100 */}
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
            className="rtl:-scale-x-100"
          >
            <path
              d="M10 12L6 8l4-4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {backLabel}
        </a>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold text-ink-primary">{heading}</h1>
          {subheading !== undefined && (
            <p className="text-sm text-ink-tertiary">{subheading}</p>
          )}
        </div>
        {actions !== undefined && (
          <div className="flex shrink-0 items-center gap-2">{actions}</div>
        )}
      </div>

      <div>{children}</div>
    </div>
  );
}
