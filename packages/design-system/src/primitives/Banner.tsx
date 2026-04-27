'use client';
/**
 * Banner — dismissable inline feedback banner.
 *
 * Three severity variants: info | warning | error.
 * Used for: "Sync failed — tap to retry", "Offline mode active",
 * "PHQ-9 due tomorrow".
 *
 * Accessibility:
 *   - role="status" for info/warning (polite live region)
 *   - role="alert"  for error (assertive live region)
 *   - Dismiss button carries a visually-hidden label (dismissLabel)
 *   - Icon SVGs are aria-hidden
 */
import * as React from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type BannerVariant = 'info' | 'warning' | 'error';

export interface BannerProps {
  /** Feedback message — required */
  message: React.ReactNode;
  /** Severity variant (default: 'info') */
  variant?: BannerVariant;
  /** Controlled open state — when provided, component is fully controlled */
  open?: boolean;
  /** Uncontrolled initial open (default: true) */
  defaultOpen?: boolean;
  /** Called when dismiss button is pressed */
  onDismiss?: () => void;
  /** Hide the dismiss button — banner becomes permanent */
  hideDismiss?: boolean;
  /** Dismiss button accessible label (default 'Dismiss') */
  dismissLabel?: string;
  /** Additional classes on the root element */
  className?: string;
}

// ---------------------------------------------------------------------------
// Variant classes
// ---------------------------------------------------------------------------

const variantCls: Record<BannerVariant, string> = {
  info:    'bg-surface-secondary border-border-subtle text-ink-primary',
  warning: 'bg-amber-50 border-amber-300 text-amber-900 dark:bg-amber-950/30 dark:border-amber-700/60 dark:text-amber-200',
  error:   'bg-red-50 border-red-300 text-red-900 dark:bg-red-950/30 dark:border-red-700/60 dark:text-red-200',
};

// ---------------------------------------------------------------------------
// Icons (inline SVG, aria-hidden)
// ---------------------------------------------------------------------------

function InfoIcon(): React.ReactElement {
  return (
    <svg
      aria-hidden="true"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="currentColor"
    >
      {/* Circle */}
      <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.5" />
      {/* Dot */}
      <circle cx="8" cy="5.5" r="1" />
      {/* Stem */}
      <rect x="7.25" y="7.5" width="1.5" height="4" rx="0.75" />
    </svg>
  );
}

function WarningIcon(): React.ReactElement {
  return (
    <svg
      aria-hidden="true"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="currentColor"
    >
      {/* Triangle outline */}
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M8 1.5 L14.928 13.5 H1.072 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      {/* Exclamation stem */}
      <rect x="7.25" y="6" width="1.5" height="4" rx="0.75" />
      {/* Exclamation dot */}
      <circle cx="8" cy="11.5" r="0.875" />
    </svg>
  );
}

function ErrorIcon(): React.ReactElement {
  return (
    <svg
      aria-hidden="true"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="currentColor"
    >
      {/* Circle */}
      <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.5" />
      {/* × crosshair */}
      <path
        d="M5.5 5.5 L10.5 10.5 M10.5 5.5 L5.5 10.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

const icons: Record<BannerVariant, () => React.ReactElement> = {
  info:    InfoIcon,
  warning: WarningIcon,
  error:   ErrorIcon,
};

// ---------------------------------------------------------------------------
// Dismiss × icon
// ---------------------------------------------------------------------------

function DismissIcon(): React.ReactElement {
  return (
    <svg
      aria-hidden="true"
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="currentColor"
    >
      <path
        d="M2 2 L12 12 M12 2 L2 12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Banner component
// ---------------------------------------------------------------------------

export function Banner({
  message,
  variant = 'info',
  open,
  defaultOpen,
  onDismiss,
  hideDismiss = false,
  dismissLabel = 'Dismiss',
  className = '',
}: BannerProps): React.ReactElement | null {
  const [isOpen, setIsOpen] = React.useState(defaultOpen !== undefined ? defaultOpen : true);
  const controlled = open !== undefined;
  const visible = controlled ? open : isOpen;

  function handleDismiss(): void {
    if (!controlled) {
      setIsOpen(false);
    }
    onDismiss?.();
  }

  if (!visible) {
    return null;
  }

  const Icon = icons[variant];
  const role = variant === 'error' ? 'alert' : 'status';

  return (
    <div
      role={role}
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 ${variantCls[variant]}${className ? ` ${className}` : ''}`}
    >
      {/* Icon */}
      <span className="shrink-0">
        <Icon />
      </span>

      {/* Message */}
      <div className="flex-1 text-sm">
        {message}
      </div>

      {/* Dismiss button */}
      {!hideDismiss && (
        <button
          type="button"
          onClick={handleDismiss}
          className="shrink-0 text-ink-tertiary hover:text-ink-primary transition-colors duration-fast ease-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
        >
          <DismissIcon />
          <span className="sr-only">{dismissLabel}</span>
        </button>
      )}
    </div>
  );
}
