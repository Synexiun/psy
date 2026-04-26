'use client';
/**
 * Dialog — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Composes @radix-ui/react-dialog so focus-trapping, scroll-lock, ARIA roles
 * (role="dialog", aria-modal, aria-labelledby, aria-describedby), and keyboard
 * Escape dismissal are all handled by the library layer.
 *
 * Token mapping:
 *   Overlay background  : bg-ink-primary/40 backdrop-blur-sm
 *   Panel background    : bg-surface-primary
 *   Panel border        : border-border-subtle
 *   Panel shape         : rounded-2xl shadow-xl
 *   Title text          : text-ink-primary text-lg font-semibold
 *   Description text    : text-ink-tertiary text-sm
 *   Close button        : text-ink-tertiary hover:text-ink-primary
 *   Transition easing   : ease-default  (--ease-default in @theme)
 *   Focus ring          : ring-accent-bronze/30
 *
 * Centering: The panel is viewport-centered via `left-1/2 top-1/2
 * -translate-x-1/2 -translate-y-1/2`. Physical `left`/`top` are correct here
 * because dialog centering is positional (viewport-relative), not directional
 * — `start-1/2` would break in RTL by mapping to `right: 50%`. This is an
 * intentional exception to the logical-properties rule.
 *
 * RTL: All internal layout (title/close row, description, body) uses logical
 * CSS properties exclusively — no ml-*/mr-*/pl-*/pr-* classes appear here.
 *
 * Logical properties only for content layout; physical `left`/`top` only for
 * the fixed-position viewport centering transform.
 */
import * as React from 'react';
import * as RadixDialog from '@radix-ui/react-dialog';

export interface DialogProps {
  /** Controlled open state */
  open?: boolean;
  /** Uncontrolled initial open state */
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Trigger element — must be a single ReactElement (Radix asChild clones it) */
  trigger?: React.ReactElement;
  /** Dialog title — required for accessibility (maps to aria-labelledby); must be non-empty */
  title: React.ReactNode;
  /** Optional description — maps to aria-describedby */
  description?: React.ReactNode;
  children: React.ReactNode;
  /** Label for the close button — translate for non-en locales (default: "Close") */
  closeLabel?: string;
  /** Additional classes applied to the panel container */
  className?: string;
}

export function Dialog({
  open,
  defaultOpen,
  onOpenChange,
  trigger,
  title,
  description,
  children,
  closeLabel = 'Close',
  className = '',
}: DialogProps): React.ReactElement {
  if (process.env.NODE_ENV !== 'production' && !title) {
    console.warn('[Dialog] `title` is empty or falsy. The dialog will have no accessible label — screen readers will not announce a meaningful name. Provide a non-empty title.');
  }

  // exactOptionalPropertyTypes: only spread props when defined so Radix
  // does not receive any key set to undefined.
  const optionalRootProps = {
    ...(open !== undefined && { open }),
    ...(defaultOpen !== undefined && { defaultOpen }),
    ...(onOpenChange !== undefined && { onOpenChange }),
  };

  return (
    <RadixDialog.Root {...optionalRootProps}>
      {trigger !== undefined && (
        <RadixDialog.Trigger asChild>{trigger}</RadixDialog.Trigger>
      )}
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-ink-primary/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <RadixDialog.Content
          className={`fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-border-subtle bg-surface-primary p-6 shadow-xl focus-visible:outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 ${className}`.trim()}
        >
          <div className="mb-1 flex items-start justify-between gap-4">
            <RadixDialog.Title className="text-lg font-semibold text-ink-primary">
              {title}
            </RadixDialog.Title>
            <RadixDialog.Close className="rounded-md text-ink-tertiary transition-colors duration-fast ease-default hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2">
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M4 4L12 12M12 4L4 12"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
              <span className="sr-only">{closeLabel}</span>
            </RadixDialog.Close>
          </div>
          {description !== undefined && (
            <RadixDialog.Description className="mb-4 text-sm text-ink-tertiary">
              {description}
            </RadixDialog.Description>
          )}
          <div>{children}</div>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
