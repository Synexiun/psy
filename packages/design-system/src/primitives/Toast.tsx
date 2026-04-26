'use client';
/**
 * Toast — Radix-based notification primitive with Quiet Strength tokens.
 *
 * Composes @radix-ui/react-toast to provide accessible toast notifications
 * with ARIA live region, keyboard Escape dismissal, and swipe-to-dismiss.
 *
 * Token mapping:
 *   Container background : bg-surface-primary
 *   Default border       : border-border-subtle
 *   Success border       : border-accent-bronze  (bronze accent as success indicator)
 *   Warning border       : border-yellow-500/60
 *   Error border         : border-red-600/60
 *   Title text           : text-ink-primary
 *   Description text     : text-ink-tertiary
 *   Close button         : text-ink-tertiary hover:text-ink-primary
 *   Transition easing    : ease-default  (--ease-default in @theme)
 *   Focus ring           : ring-accent-bronze/30
 *
 * Viewport positioning (logical CSS, RTL-safe):
 *   top-right    → top-4 end-4
 *   top-left     → top-4 start-4
 *   bottom-right → bottom-4 end-4
 *   bottom-left  → bottom-4 start-4
 *
 * RTL note: In RTL context `end-4` maps to the physical left edge, so a
 * `bottom-right` toast appears in the physical bottom-left — this is the
 * correct "corner flip" behaviour per the spec.
 *
 * State is managed by ToastContext. `useToast()` returns `toast()`, `dismiss()`,
 * and `messages` — all callers must be descendants of `ToastProvider`.
 */
import * as React from 'react';
import * as RadixToast from '@radix-ui/react-toast';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ToastVariant = 'default' | 'success' | 'warning' | 'error';

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  /** Duration in ms. Default: 5000. Pass Infinity for sticky toasts. */
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface ToastProviderProps {
  children: React.ReactNode;
  /** Corner position for the viewport — flips in RTL (default: 'bottom-right') */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  /** Max toasts visible at once (default: 5) */
  maxToasts?: number;
  /** Swipe direction for dismiss gesture — pass "left" for RTL layouts (default: "right") */
  swipeDirection?: 'right' | 'left' | 'up' | 'down';
}

export interface UseToastReturn {
  toast: (msg: Omit<ToastMessage, 'id'>) => void;
  dismiss: (id: string) => void;
  messages: ToastMessage[];
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface ToastContextValue {
  toast: (msg: Omit<ToastMessage, 'id'>) => void;
  dismiss: (id: string) => void;
  messages: ToastMessage[];
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

// ---------------------------------------------------------------------------
// useToast hook
// ---------------------------------------------------------------------------

export function useToast(): UseToastReturn {
  const ctx = React.useContext(ToastContext);
  if (ctx === null) {
    throw new Error('[useToast] must be used inside a <ToastProvider>.');
  }
  return ctx;
}

// ---------------------------------------------------------------------------
// Variant → border class
// ---------------------------------------------------------------------------

const VARIANT_CLASSES: Record<ToastVariant, string> = {
  default: 'border-border-subtle',
  success: 'border-accent-bronze',
  warning: 'border-yellow-500/60',
  error:   'border-red-600/60',
};

// ---------------------------------------------------------------------------
// Viewport position → Tailwind classes (logical CSS, RTL-safe)
// ---------------------------------------------------------------------------

const POSITION_CLASSES: Record<NonNullable<ToastProviderProps['position']>, string> = {
  'top-right':    'top-4 end-4',
  'top-left':     'top-4 start-4',
  'bottom-right': 'bottom-4 end-4',
  'bottom-left':  'bottom-4 start-4',
};

// ---------------------------------------------------------------------------
// ToastProvider
// ---------------------------------------------------------------------------

export function ToastProvider({
  children,
  position = 'bottom-right',
  maxToasts = 5,
  swipeDirection = 'right',
}: ToastProviderProps): React.ReactElement {
  const [messages, setMessages] = React.useState<ToastMessage[]>([]);

  const toast = React.useCallback((msg: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).slice(2);
    setMessages((prev) => {
      const next = [...prev, { ...msg, id }];
      return next.length > maxToasts ? next.slice(next.length - maxToasts) : next;
    });
  }, [maxToasts]);

  const dismiss = React.useCallback((id: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const positionClass = POSITION_CLASSES[position];

  return (
    <ToastContext.Provider value={{ toast, dismiss, messages }}>
      <RadixToast.Provider swipeDirection={swipeDirection}>
        {children}
        {messages.map((msg) => {
          const variantClass = VARIANT_CLASSES[msg.variant ?? 'default'];
          const duration = msg.duration ?? 5000;

          return (
            <RadixToast.Root
              key={msg.id}
              open
              duration={duration === Infinity ? undefined : duration}
              onOpenChange={(open) => {
                if (!open) dismiss(msg.id);
              }}
              className={`group pointer-events-auto relative flex w-full max-w-sm flex-col gap-1 rounded-lg border bg-surface-primary p-4 shadow-lg transition-all ease-default data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[swipe=end]:animate-out data-[state=closed]:slide-out-to-end-full data-[state=open]:slide-in-from-end-full ${variantClass}`.trim()}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 flex-1 flex-col gap-1">
                  <RadixToast.Title className="text-sm font-semibold leading-snug text-ink-primary">
                    {msg.title}
                  </RadixToast.Title>
                  {msg.description !== undefined && (
                    <RadixToast.Description className="text-sm leading-snug text-ink-tertiary">
                      {msg.description}
                    </RadixToast.Description>
                  )}
                </div>
                <RadixToast.Close
                  aria-label="Dismiss"
                  className="shrink-0 rounded-md text-ink-tertiary transition-colors duration-fast ease-default hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
                >
                  <svg
                    width="14"
                    height="14"
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
                </RadixToast.Close>
              </div>
              {msg.action !== undefined && (
                <RadixToast.Action
                  altText={msg.action.label}
                  asChild
                >
                  <button
                    onClick={msg.action.onClick}
                    className="mt-1 self-start rounded-md border border-border-subtle px-3 py-1 text-xs font-medium text-ink-primary transition-colors duration-fast ease-default hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
                  >
                    {msg.action.label}
                  </button>
                </RadixToast.Action>
              )}
            </RadixToast.Root>
          );
        })}
        <RadixToast.Viewport
          className={`fixed z-[100] flex max-h-screen w-full max-w-sm flex-col-reverse gap-2 p-0 ${positionClass}`.trim()}
        />
      </RadixToast.Provider>
    </ToastContext.Provider>
  );
}
