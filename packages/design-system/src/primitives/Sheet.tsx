'use client';
/**
 * Sheet — Radix-based slide-in drawer (side panel) primitive.
 *
 * Composes @radix-ui/react-dialog so focus-trapping, scroll-lock, ARIA roles
 * (role="dialog", aria-modal, aria-labelledby, aria-describedby), and keyboard
 * Escape dismissal are all handled by the library layer.
 *
 * Token mapping:
 *   Overlay background  : bg-ink-primary/40 backdrop-blur-sm
 *   Panel background    : bg-surface-primary
 *   Panel border        : border-border-subtle
 *   Panel shape         : no rounded corners — sheet goes edge-to-edge
 *   Title text          : text-ink-primary text-lg font-semibold
 *   Description text    : text-ink-tertiary text-sm
 *   Close button        : text-ink-tertiary hover:text-ink-primary
 *   Transition easing   : ease-default  (--ease-default in @theme)
 *   Focus ring          : ring-accent-bronze/30
 *
 * Logical CSS positioning:
 *   right: `inset-y-0 end-0 h-full border-s` — "end" maps to right in LTR,
 *          left in RTL; "border-s" is the logical start border.
 *   left:  `inset-y-0 start-0 h-full border-e` — "start" maps to left in LTR,
 *          right in RTL; "border-e" is the logical end border.
 *   top/bottom: `inset-x-0` — symmetric, no directional bias.
 *
 * RTL note: In RTL mode a side="right" sheet appears from the LEFT because
 * "end" in RTL is the left edge. This is the correct logical behaviour — Radix
 * reads `dir` from the DOM context. The component itself does NOT detect RTL;
 * callers wrap in a dir="rtl" element to activate it.
 *
 * Panel sizes (vertical panels):
 *   sm  = 320px (w-80)
 *   md  = 400px (w-[400px], default)
 *   lg  = 512px (w-[512px])
 *   full = 100% (w-full)
 *
 * Panel sizes (horizontal panels — top/bottom):
 *   sm  = h-40
 *   md  = h-64 (default)
 *   lg  = h-96
 *   full = h-full
 */
import * as React from 'react';
import * as RadixDialog from '@radix-ui/react-dialog';

export type SheetSide = 'left' | 'right' | 'top' | 'bottom';
export type SheetSize = 'sm' | 'md' | 'lg' | 'full';

export interface SheetProps {
  /** Controlled open state */
  open?: boolean;
  /** Uncontrolled initial open state */
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Trigger element — must be a single ReactElement (Radix asChild clones it) */
  trigger?: React.ReactElement;
  /** Which edge the panel slides in from (default: 'right') */
  side?: SheetSide;
  /** Panel width (left/right) or height (top/bottom) preset (default: 'md') */
  size?: SheetSize;
  /** Sheet title — required for accessibility (maps to aria-labelledby); must be non-empty */
  title: React.ReactNode;
  /** Optional description — maps to aria-describedby */
  description?: React.ReactNode;
  children: React.ReactNode;
  /** Label for the sr-only close button — translate for non-en locales (default: "Close") */
  closeLabel?: string;
  /** Additional classes applied to the panel container */
  className?: string;
}

/**
 * Per-side positioning + animation + border classes.
 *
 * Logical properties used throughout:
 *   end-0 / start-0 : logical inset (not right-0 / left-0)
 *   border-s        : logical start border (right panel has a left border in LTR)
 *   border-e        : logical end border (left panel has a right border in LTR)
 *   inset-y-0       : top-0 + bottom-0 — symmetric, no direction
 *   inset-x-0       : left-0 + right-0 — symmetric, no direction
 */
const SLIDE_CLASSES: Record<SheetSide, string> = {
  right:
    'data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right inset-y-0 end-0 h-full border-s',
  left:
    'data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left inset-y-0 start-0 h-full border-e',
  top:
    'data-[state=open]:slide-in-from-top data-[state=closed]:slide-out-to-top inset-x-0 top-0 w-full border-b',
  bottom:
    'data-[state=open]:slide-in-from-bottom data-[state=closed]:slide-out-to-bottom inset-x-0 bottom-0 w-full border-t',
};

const SIZE_CLASSES: Record<SheetSide, Record<SheetSize, string>> = {
  right:  { sm: 'w-80', md: 'w-[400px]', lg: 'w-[512px]', full: 'w-full' },
  left:   { sm: 'w-80', md: 'w-[400px]', lg: 'w-[512px]', full: 'w-full' },
  top:    { sm: 'h-40', md: 'h-64',      lg: 'h-96',      full: 'h-full' },
  bottom: { sm: 'h-40', md: 'h-64',      lg: 'h-96',      full: 'h-full' },
};

export function Sheet({
  open,
  defaultOpen,
  onOpenChange,
  trigger,
  side = 'right',
  size = 'md',
  title,
  description,
  children,
  closeLabel = 'Close',
  className = '',
}: SheetProps): React.ReactElement {
  if (
    process.env.NODE_ENV !== 'production' &&
    (title === null || title === undefined || title === false || title === '')
  ) {
    console.warn(
      '[Sheet] `title` is empty or falsy. The sheet will have no accessible label — ' +
        'screen readers will not announce a meaningful name. Provide a non-empty title.',
    );
  }

  // exactOptionalPropertyTypes: only spread props when defined so Radix
  // does not receive any key set to undefined.
  const optionalRootProps = {
    ...(open !== undefined && { open }),
    ...(defaultOpen !== undefined && { defaultOpen }),
    ...(onOpenChange !== undefined && { onOpenChange }),
  };

  const slideClass = SLIDE_CLASSES[side];
  const sizeClass = SIZE_CLASSES[side][size];

  return (
    <RadixDialog.Root {...optionalRootProps}>
      {trigger !== undefined && (
        <RadixDialog.Trigger asChild>{trigger}</RadixDialog.Trigger>
      )}
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-ink-primary/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <RadixDialog.Content
          className={`fixed z-50 flex flex-col bg-surface-primary border-border-subtle shadow-xl duration-300 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 ease-default ${slideClass} ${sizeClass} ${className}`.trim()}
        >
          <div className="flex items-start justify-between gap-4 p-6 pb-0">
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
            <RadixDialog.Description className="px-6 pt-1 text-sm text-ink-tertiary">
              {description}
            </RadixDialog.Description>
          )}
          <div className="flex-1 overflow-y-auto p-6">{children}</div>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
