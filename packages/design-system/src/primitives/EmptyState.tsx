'use client';
/**
 * EmptyState — centered feedback component for empty lists/screens.
 *
 * Used for: "No check-ins yet", "No sessions this week".
 * Has: optional illustration slot, headline, optional body text,
 * optional primary CTA button.
 *
 * Stateless/presentational — no internal state needed.
 */
import * as React from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface EmptyStateProps {
  /** Optional illustration — renders above headline. Accepts any ReactNode (SVG, img, emoji wrapper). */
  illustration?: React.ReactNode;
  /** Headline text — required */
  headline: string;
  /** Optional supporting body text */
  body?: string;
  /** Primary CTA label */
  ctaLabel?: string;
  /** CTA click handler */
  onCta?: () => void;
  /** Additional classes on root div */
  className?: string;
}

// ---------------------------------------------------------------------------
// EmptyState component
// ---------------------------------------------------------------------------

export function EmptyState({
  illustration,
  headline,
  body,
  ctaLabel,
  onCta,
  className = '',
}: EmptyStateProps): React.ReactElement {
  return (
    <div
      className={`flex flex-col items-center gap-4 py-12 text-center${className ? ` ${className}` : ''}`}
    >
      {illustration !== undefined && (
        <div className="mb-2">{illustration}</div>
      )}

      <h2 className="text-xl font-semibold text-ink-primary">{headline}</h2>

      {body !== undefined && (
        <p className="max-w-xs text-sm text-ink-tertiary">{body}</p>
      )}

      {ctaLabel !== undefined && onCta !== undefined && (
        <button
          type="button"
          onClick={onCta}
          className="mt-2 rounded-lg bg-accent-bronze px-5 py-2.5 text-sm font-medium text-white transition-colors duration-fast ease-default hover:bg-accent-bronze/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
