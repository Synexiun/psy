/**
 * Contract tests for packages/design-system/src/primitives/Toast.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Radix Toast portals its viewport/content to document.body, so we query
 * the portalled content via `document.body.querySelector` or `screen.getBy*`
 * (which searches document.body). Tests use a `renderWithProvider` helper that
 * wraps the component under test in a <ToastProvider>, and a `TestHarness`
 * that calls `useToast()` to fire toasts programmatically.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import {
  ToastProvider,
  useToast,
} from '@disciplineos/design-system/primitives/Toast';
import type { ToastVariant } from '@disciplineos/design-system/primitives/Toast';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function TestHarness({ variant = 'default' }: { variant?: ToastVariant }) {
  const { toast } = useToast();
  return (
    <button
      onClick={() =>
        toast({ title: 'Test toast', variant })
      }
    >
      Show
    </button>
  );
}

function TestHarnessWithDescription() {
  const { toast } = useToast();
  return (
    <button
      onClick={() =>
        toast({ title: 'Toast title', description: 'Toast description text' })
      }
    >
      Show
    </button>
  );
}

function TestHarnessWithAction({ onAction }: { onAction: () => void }) {
  const { toast } = useToast();
  return (
    <button
      onClick={() =>
        toast({
          title: 'Action toast',
          action: { label: 'Undo', onClick: onAction },
        })
      }
    >
      Show
    </button>
  );
}

function TestHarnessDismiss() {
  const { toast, dismiss, messages } = useToast();
  return (
    <>
      <button
        onClick={() => toast({ title: 'Dismiss me', duration: Infinity })}
      >
        Show
      </button>
      {messages.map((m) => (
        <button key={m.id} onClick={() => dismiss(m.id)}>
          Dismiss {m.id}
        </button>
      ))}
    </>
  );
}

// Type alias to avoid import overhead in helper signatures
type ToastProviderProps = React.ComponentProps<typeof ToastProvider>;

function renderWithProvider(
  ui: React.ReactElement,
  position: ToastProviderProps['position'] = 'bottom-right',
) {
  return render(<ToastProvider position={position}>{ui}</ToastProvider>);
}

// ---------------------------------------------------------------------------
// 1. ToastProvider renders children
// ---------------------------------------------------------------------------

describe('ToastProvider — renders children', () => {
  it('renders its children without crashing', () => {
    render(
      <ToastProvider>
        <p>Child content</p>
      </ToastProvider>,
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders multiple children', () => {
    render(
      <ToastProvider>
        <p>First child</p>
        <p>Second child</p>
      </ToastProvider>,
    );
    expect(screen.getByText('First child')).toBeInTheDocument();
    expect(screen.getByText('Second child')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. useToast().toast() adds a message to the DOM
// ---------------------------------------------------------------------------

describe('useToast — toast() adds message', () => {
  it('shows the toast title after calling toast()', () => {
    renderWithProvider(<TestHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    expect(screen.getByText('Test toast')).toBeInTheDocument();
  });

  it('renders the toast in a Radix Viewport (role="region" wrapper)', () => {
    renderWithProvider(<TestHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    // Radix Toast.Viewport wraps an <ol> in a role="region" DismissableLayer.Branch
    expect(document.body.querySelector('[role="region"]')).not.toBeNull();
  });

  it('useToast throws when used outside ToastProvider', () => {
    function BadConsumer() {
      useToast();
      return null;
    }
    expect(() => render(<BadConsumer />)).toThrow('[useToast]');
  });
});

// ---------------------------------------------------------------------------
// 3. useToast().dismiss() removes the message
// ---------------------------------------------------------------------------

describe('useToast — dismiss() removes message', () => {
  it('removes the toast title from the DOM after dismiss()', async () => {
    renderWithProvider(<TestHarnessDismiss />);
    // Show the toast
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    expect(screen.getByText('Dismiss me')).toBeInTheDocument();

    // The dismiss button text includes the id dynamically; find it via role
    const dismissButtons = screen.getAllByRole('button');
    const dismissBtn = dismissButtons.find((b) =>
      b.textContent?.startsWith('Dismiss '),
    );
    expect(dismissBtn).toBeDefined();
    fireEvent.click(dismissBtn!);

    // In jsdom, CSS animations don't fire animationend, so Radix keeps the
    // element in the DOM with data-state="closed" rather than unmounting it.
    // Accept either: fully removed OR transitioning out (data-state="closed").
    await waitFor(() => {
      const el = screen.queryByText('Dismiss me');
      expect(
        el === null || el.closest('[data-state="closed"]') !== null,
      ).toBe(true);
    });
  });
});

// ---------------------------------------------------------------------------
// 4. maxToasts cap
// ---------------------------------------------------------------------------

describe('ToastProvider — maxToasts cap', () => {
  it('respects maxToasts — drops oldest when limit is exceeded', async () => {
    const TestHarness = () => {
      const { toast } = useToast();
      return (
        <button
          onClick={() => {
            toast({ title: 'Toast 1' });
            toast({ title: 'Toast 2' });
            toast({ title: 'Toast 3' });
            toast({ title: 'Toast 4' }); // exceeds maxToasts=3
          }}
        >
          Add 4 toasts
        </button>
      );
    };
    render(
      <ToastProvider maxToasts={3}>
        <TestHarness />
      </ToastProvider>,
    );
    fireEvent.click(screen.getByRole('button', { name: /add 4/i }));
    // Only 3 most-recent toasts should be visible; oldest is dropped
    await waitFor(() => {
      expect(screen.queryByText('Toast 1')).toBeNull();
      expect(screen.getByText('Toast 2')).toBeInTheDocument();
      expect(screen.getByText('Toast 3')).toBeInTheDocument();
      expect(screen.getByText('Toast 4')).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// 5. Variant classes
// ---------------------------------------------------------------------------

describe('useToast — variant classes', () => {
  it('default variant has border-border-subtle class', () => {
    renderWithProvider(<TestHarness variant="default" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const toast = document.body.querySelector('[data-radix-toast-viewport] li, [data-radix-toast-viewport] [role="status"], [data-radix-toast-viewport] > *');
    // Find the toast root by looking for the border-border-subtle class
    const allToastRoots = document.body.querySelectorAll('[data-state="open"]');
    const toastRoot = Array.from(allToastRoots).find((el) =>
      el.className.includes('border-border-subtle'),
    );
    expect(toastRoot).toBeDefined();
    expect(toastRoot?.className).toContain('border-border-subtle');
  });

  it('success variant has border-accent-bronze class', () => {
    renderWithProvider(<TestHarness variant="success" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const allOpen = document.body.querySelectorAll('[data-state="open"]');
    const toastRoot = Array.from(allOpen).find((el) =>
      el.className.includes('border-accent-bronze'),
    );
    expect(toastRoot).toBeDefined();
    expect(toastRoot?.className).toContain('border-accent-bronze');
  });

  it('warning variant has border-yellow-500/60 class', () => {
    renderWithProvider(<TestHarness variant="warning" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const allOpen = document.body.querySelectorAll('[data-state="open"]');
    const toastRoot = Array.from(allOpen).find((el) =>
      el.className.includes('border-yellow-500/60'),
    );
    expect(toastRoot).toBeDefined();
    expect(toastRoot?.className).toContain('border-yellow-500/60');
  });

  it('error variant has border-red-600/60 class', () => {
    renderWithProvider(<TestHarness variant="error" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const allOpen = document.body.querySelectorAll('[data-state="open"]');
    const toastRoot = Array.from(allOpen).find((el) =>
      el.className.includes('border-red-600/60'),
    );
    expect(toastRoot).toBeDefined();
    expect(toastRoot?.className).toContain('border-red-600/60');
  });
});

// ---------------------------------------------------------------------------
// 6. Toast with action renders an action button
// ---------------------------------------------------------------------------

describe('useToast — action prop', () => {
  it('renders an action button when action is provided', () => {
    const onAction = vi.fn();
    renderWithProvider(<TestHarnessWithAction onAction={onAction} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const actionBtn = screen.getByRole('button', { name: 'Undo' });
    expect(actionBtn).toBeInTheDocument();
  });

  it('calls action.onClick when action button is clicked', () => {
    const onAction = vi.fn();
    renderWithProvider(<TestHarnessWithAction onAction={onAction} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    fireEvent.click(screen.getByRole('button', { name: 'Undo' }));
    expect(onAction).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// 7. Toast with description renders the description text
// ---------------------------------------------------------------------------

describe('useToast — description prop', () => {
  it('renders description text when description is provided', () => {
    renderWithProvider(<TestHarnessWithDescription />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    expect(screen.getByText('Toast description text')).toBeInTheDocument();
  });

  it('does not render a description element when description is omitted', () => {
    renderWithProvider(<TestHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    // The description text used in TestHarnesWithDescription is not present
    expect(screen.queryByText('Toast description text')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 8. Viewport position classes
// ---------------------------------------------------------------------------

describe('ToastProvider — viewport position classes', () => {
  // Radix Toast.Viewport: our className is placed on the <ol> element inside
  // a DismissableLayer.Branch wrapper that carries role="region". The <ol>
  // itself has tabIndex=-1 and receives our position classes.
  // We select it by tag since no unique data-attribute is present on it.
  function getViewport() {
    // The wrapper with role="region" contains the <ol> that carries our className.
    const region = document.body.querySelector('[role="region"]');
    if (region === null) return null;
    // Our className is on the <ol> which is the direct child Collection.Slot wrapper.
    const ol = region.querySelector('ol');
    // If no ol found (should not happen), fall back to the region itself.
    return ol ?? region;
  }

  it('top-right → has end-4 and top-4', () => {
    render(
      <ToastProvider position="top-right">
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).toContain('end-4');
    expect(vp?.className).toContain('top-4');
  });

  it('top-left → has start-4 and top-4', () => {
    render(
      <ToastProvider position="top-left">
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).toContain('start-4');
    expect(vp?.className).toContain('top-4');
  });

  it('bottom-right → has end-4 and bottom-4', () => {
    render(
      <ToastProvider position="bottom-right">
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).toContain('end-4');
    expect(vp?.className).toContain('bottom-4');
  });

  it('bottom-left → has start-4 and bottom-4', () => {
    render(
      <ToastProvider position="bottom-left">
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).toContain('start-4');
    expect(vp?.className).toContain('bottom-4');
  });

  it('top-right does not have start-4', () => {
    render(
      <ToastProvider position="top-right">
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).not.toContain('start-4');
  });

  it('bottom-left does not have end-4', () => {
    render(
      <ToastProvider position="bottom-left">
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).not.toContain('end-4');
  });

  it('defaults to bottom-right when position is omitted', () => {
    render(
      <ToastProvider>
        <span />
      </ToastProvider>,
    );
    const vp = getViewport();
    expect(vp?.className).toContain('bottom-4');
    expect(vp?.className).toContain('end-4');
  });
});

// ---------------------------------------------------------------------------
// 9. axe accessibility
// ---------------------------------------------------------------------------

const axeWithConfig = configureAxe({
  rules: {
    // color-contrast requires computed styles not available in jsdom
    'color-contrast': { enabled: false },
    // region rule flags plain text content not wrapped in a landmark;
    // our harness renders a bare button alongside the ToastProvider —
    // this is a jsdom/test-harness limitation, not a production violation.
    'region': { enabled: false },
  },
});

describe('ToastProvider — axe accessibility', () => {
  it('provider with no toasts has no a11y violations', async () => {
    render(
      <ToastProvider>
        <p>App content</p>
      </ToastProvider>,
    );
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('provider with an open default toast has no a11y violations', async () => {
    renderWithProvider(<TestHarness variant="default" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('provider with a success toast has no a11y violations', async () => {
    renderWithProvider(<TestHarness variant="success" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('provider with an error toast has no a11y violations', async () => {
    renderWithProvider(<TestHarness variant="error" />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('provider with a toast + description has no a11y violations', async () => {
    renderWithProvider(<TestHarnessWithDescription />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('provider with a toast + action has no a11y violations', async () => {
    renderWithProvider(<TestHarnessWithAction onAction={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show' }));
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });
});
