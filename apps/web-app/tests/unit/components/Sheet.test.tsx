/**
 * Contract tests for packages/design-system/src/primitives/Sheet.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Radix Dialog (which Sheet composes) portals its content to document.body
 * only when the sheet is open. In the uncontrolled trigger-based stories the
 * sheet is closed by default, so content is not in the DOM until a click event
 * fires the trigger. We test structural rendering (trigger mounts, children
 * absent when closed), prop passthrough via class assertions on the panel, and
 * RTL rendering.
 *
 * All four SheetSide values and all four SheetSize values are exercised. The
 * SLIDE_CLASSES / SIZE_CLASSES lookup tables are tested implicitly by asserting
 * the expected Tailwind classes on the rendered panel.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import type * as React from 'react';
import { Sheet } from '@disciplineos/design-system/primitives/Sheet';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderOpen(props: Partial<React.ComponentProps<typeof Sheet>> = {}) {
  return render(
    <Sheet
      open
      onOpenChange={() => undefined}
      title="Test sheet"
      {...props}
    >
      <p>Sheet body content</p>
    </Sheet>,
  );
}

// ---------------------------------------------------------------------------
// Trigger rendering — closed state
// ---------------------------------------------------------------------------

describe('Sheet — trigger (closed)', () => {
  it('renders a trigger element when trigger prop is provided', () => {
    render(
      <Sheet
        title="My sheet"
        trigger={<button>Open sheet</button>}
      >
        <p>Body</p>
      </Sheet>,
    );
    expect(screen.getByRole('button', { name: /open sheet/i })).toBeInTheDocument();
  });

  it('does not render sheet content in the DOM when closed', () => {
    render(
      <Sheet
        title="My sheet"
        trigger={<button>Open sheet</button>}
      >
        <p>Hidden body</p>
      </Sheet>,
    );
    // Radix portals dialog content only when open
    expect(screen.queryByText('Hidden body')).toBeNull();
  });

  it('does not render dialog role in the DOM when closed', () => {
    render(
      <Sheet
        title="My sheet"
        trigger={<button>Open sheet</button>}
      >
        <p>Body</p>
      </Sheet>,
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Open state — content in DOM
// ---------------------------------------------------------------------------

describe('Sheet — open state', () => {
  it('renders the dialog role when open=true', () => {
    renderOpen();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('renders the title when open', () => {
    renderOpen({ title: 'Session details' });
    expect(screen.getByText('Session details')).toBeInTheDocument();
  });

  it('renders children when open', () => {
    renderOpen();
    expect(screen.getByText('Sheet body content')).toBeInTheDocument();
  });

  it('renders description when provided and open', () => {
    renderOpen({ description: 'This is the description.' });
    expect(screen.getByText('This is the description.')).toBeInTheDocument();
  });

  it('does not render description text when description prop is omitted', () => {
    // The RadixDialog.Description element is not rendered when description is undefined.
    // Verify by checking that "description text" is not in the DOM.
    renderOpen();
    // No description text beyond the children should be visible
    // (children render as "Sheet body content", no additional paragraph text)
    expect(screen.queryByText('description text')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Side prop — class assertions on the panel
// ---------------------------------------------------------------------------

describe('Sheet — side prop', () => {
  it('applies slide-in-from-right class for side="right" (default)', () => {
    const { baseElement } = renderOpen({ side: 'right' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('slide-in-from-right');
  });

  it('applies end-0 class for side="right" (logical end positioning)', () => {
    const { baseElement } = renderOpen({ side: 'right' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('end-0');
  });

  it('applies border-s class for side="right" (logical start border)', () => {
    const { baseElement } = renderOpen({ side: 'right' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('border-s');
  });

  it('applies slide-in-from-left class for side="left"', () => {
    const { baseElement } = renderOpen({ side: 'left' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('slide-in-from-left');
  });

  it('applies start-0 class for side="left" (logical start positioning)', () => {
    const { baseElement } = renderOpen({ side: 'left' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('start-0');
  });

  it('applies border-e class for side="left" (logical end border)', () => {
    const { baseElement } = renderOpen({ side: 'left' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('border-e');
  });

  it('applies slide-in-from-top class for side="top"', () => {
    const { baseElement } = renderOpen({ side: 'top' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('slide-in-from-top');
  });

  it('applies inset-x-0 for side="top" (symmetric, no direction)', () => {
    const { baseElement } = renderOpen({ side: 'top' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('inset-x-0');
  });

  it('applies slide-in-from-bottom class for side="bottom"', () => {
    const { baseElement } = renderOpen({ side: 'bottom' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('slide-in-from-bottom');
  });

  it('applies inset-x-0 for side="bottom" (symmetric, no direction)', () => {
    const { baseElement } = renderOpen({ side: 'bottom' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('inset-x-0');
  });

  it('does not apply end-0 for side="left"', () => {
    const { baseElement } = renderOpen({ side: 'left' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).not.toContain('end-0');
  });

  it('does not apply start-0 for side="right"', () => {
    const { baseElement } = renderOpen({ side: 'right' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).not.toContain('start-0');
  });
});

// ---------------------------------------------------------------------------
// Size prop — class assertions (right/left panels → width, top/bottom → height)
// ---------------------------------------------------------------------------

describe('Sheet — size prop (right panel widths)', () => {
  it('applies w-80 for size="sm" side="right"', () => {
    const { baseElement } = renderOpen({ side: 'right', size: 'sm' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('w-80');
  });

  it('applies w-[400px] for size="md" side="right" (default)', () => {
    const { baseElement } = renderOpen({ side: 'right', size: 'md' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('w-[400px]');
  });

  it('applies w-[512px] for size="lg" side="right"', () => {
    const { baseElement } = renderOpen({ side: 'right', size: 'lg' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('w-[512px]');
  });

  it('applies w-full for size="full" side="right"', () => {
    const { baseElement } = renderOpen({ side: 'right', size: 'full' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('w-full');
  });
});

describe('Sheet — size prop (bottom panel heights)', () => {
  it('applies h-40 for size="sm" side="bottom"', () => {
    const { baseElement } = renderOpen({ side: 'bottom', size: 'sm' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('h-40');
  });

  it('applies h-64 for size="md" side="bottom" (default)', () => {
    const { baseElement } = renderOpen({ side: 'bottom', size: 'md' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('h-64');
  });

  it('applies h-96 for size="lg" side="bottom"', () => {
    const { baseElement } = renderOpen({ side: 'bottom', size: 'lg' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('h-96');
  });

  it('applies h-full for size="full" side="bottom"', () => {
    const { baseElement } = renderOpen({ side: 'bottom', size: 'full' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('h-full');
  });
});

// ---------------------------------------------------------------------------
// closeLabel prop
// ---------------------------------------------------------------------------

describe('Sheet — closeLabel prop', () => {
  it('renders the default "Close" sr-only label', () => {
    renderOpen();
    const srSpan = document.querySelector('.sr-only');
    expect(srSpan?.textContent).toBe('Close');
  });

  it('renders a custom closeLabel', () => {
    renderOpen({ closeLabel: 'Dismiss panel' });
    const srSpan = document.querySelector('.sr-only');
    expect(srSpan?.textContent).toBe('Dismiss panel');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Sheet — className passthrough', () => {
  it('merges additional className onto the panel element', () => {
    const { baseElement } = renderOpen({ className: 'custom-sheet-class' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).toContain('custom-sheet-class');
  });

  it('panel className is trimmed (no leading/trailing whitespace)', () => {
    const { baseElement } = renderOpen({ className: '' });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className).not.toMatch(/^\s|\s$/);
  });
});

// ---------------------------------------------------------------------------
// Trigger — trigger element mounts and has correct ARIA attributes
// ---------------------------------------------------------------------------

describe('Sheet — trigger ARIA attributes', () => {
  it('trigger button has aria-haspopup="dialog"', () => {
    render(
      <Sheet
        title="Trigger ARIA"
        trigger={<button>Open sheet</button>}
      >
        <p>Body</p>
      </Sheet>,
    );
    const trigger = screen.getByRole('button', { name: /open sheet/i });
    expect(trigger).toHaveAttribute('aria-haspopup', 'dialog');
  });

  it('trigger button has aria-expanded="false" when sheet is closed', () => {
    render(
      <Sheet
        title="Trigger state"
        trigger={<button>Open sheet</button>}
      >
        <p>Body</p>
      </Sheet>,
    );
    const trigger = screen.getByRole('button', { name: /open sheet/i });
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });
});

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

describe('Sheet — accessibility', () => {
  it('dialog has aria-labelledby pointing to the title', () => {
    renderOpen({ title: 'Accessible title' });
    const dialog = screen.getByRole('dialog');
    const labelledBy = dialog.getAttribute('aria-labelledby');
    expect(labelledBy).not.toBeNull();
    // The referenced element should contain the title text
    const titleEl = document.getElementById(labelledBy as string);
    expect(titleEl?.textContent).toBe('Accessible title');
  });

  it('close button is present in the panel', () => {
    // The close button contains an sr-only span with the closeLabel
    renderOpen({ closeLabel: 'Close panel' });
    // Verify the sr-only close label is present (means the close button rendered)
    const srSpan = document.querySelector('.sr-only');
    expect(srSpan?.textContent).toBe('Close panel');
  });

  it('close button has an sr-only text label', () => {
    renderOpen({ closeLabel: 'Close sheet' });
    const srSpan = document.querySelector('.sr-only');
    expect(srSpan?.textContent).toBe('Close sheet');
  });

  it('close SVG has aria-hidden="true"', () => {
    renderOpen();
    const svg = document.querySelector('[role="dialog"] svg');
    expect(svg?.getAttribute('aria-hidden')).toBe('true');
  });
});

// ---------------------------------------------------------------------------
// RTL context
// ---------------------------------------------------------------------------

describe('Sheet — RTL context', () => {
  it('renders title correctly inside dir="rtl" wrapper', () => {
    render(
      <div dir="rtl">
        <Sheet open onOpenChange={() => undefined} title="تفاصيل الجلسة">
          <p>محتوى</p>
        </Sheet>
      </div>,
    );
    expect(screen.getByText('تفاصيل الجلسة')).toBeInTheDocument();
  });

  it('renders children correctly inside dir="rtl" wrapper', () => {
    render(
      <div dir="rtl">
        <Sheet open onOpenChange={() => undefined} title="عنوان">
          <p>محتوى الدرج</p>
        </Sheet>
      </div>,
    );
    expect(screen.getByText('محتوى الدرج')).toBeInTheDocument();
  });

  it('does not throw when side="right" in dir="rtl" context', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <Sheet open onOpenChange={() => undefined} title="عنوان" side="right">
            <p>Body</p>
          </Sheet>
        </div>,
      ),
    ).not.toThrow();
  });

  it('does not throw when side="left" in dir="rtl" context', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <Sheet open onOpenChange={() => undefined} title="عنوان" side="left">
            <p>Body</p>
          </Sheet>
        </div>,
      ),
    ).not.toThrow();
  });

  it('side="right" panel carries end-0 and border-s for logical RTL-safe positioning', () => {
    const { baseElement } = render(
      <div dir="rtl">
        <Sheet open onOpenChange={() => undefined} title="عنوان" side="right">
          <p>Body</p>
        </Sheet>
      </div>,
    );
    const dialog = baseElement.querySelector('[role="dialog"]');
    expect(dialog?.className).toContain('end-0');
    expect(dialog?.className).toContain('border-s');
  });

  it('side="left" panel carries start-0 and border-e for logical RTL-safe positioning', () => {
    const { baseElement } = render(
      <div dir="rtl">
        <Sheet open onOpenChange={() => undefined} title="عنوان" side="left">
          <p>Body</p>
        </Sheet>
      </div>,
    );
    const dialog = baseElement.querySelector('[role="dialog"]');
    expect(dialog?.className).toContain('start-0');
    expect(dialog?.className).toContain('border-e');
  });
});

// ---------------------------------------------------------------------------
// Controlled mode — onOpenChange fires
// ---------------------------------------------------------------------------

describe('Sheet — controlled mode', () => {
  it('renders when open=true without a trigger', () => {
    render(
      <Sheet open onOpenChange={() => undefined} title="Controlled">
        <p>Controlled body</p>
      </Sheet>,
    );
    expect(screen.getByText('Controlled body')).toBeInTheDocument();
  });

  it('does not render dialog when open=false', () => {
    render(
      <Sheet open={false} onOpenChange={() => undefined} title="Hidden">
        <p>Hidden body</p>
      </Sheet>,
    );
    expect(screen.queryByText('Hidden body')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() in panel className
// ---------------------------------------------------------------------------

describe('Sheet — token hygiene', () => {
  const sides = ['left', 'right', 'top', 'bottom'] as const;

  it.each(sides)('no hardcoded hsl() in panel className for side="%s"', (side) => {
    const { baseElement } = renderOpen({ side });
    const panel = baseElement.querySelector('[role="dialog"]');
    expect(panel?.className ?? '').not.toContain('hsl(');
  });
});

// ---------------------------------------------------------------------------
// axe accessibility scans
// ---------------------------------------------------------------------------

const axe = configureAxe({
  rules: {
    // color-contrast requires computed styles not available in jsdom
    'color-contrast': { enabled: false },
  },
});

describe('Sheet — axe accessibility', () => {
  it('open right sheet has no critical a11y violations', async () => {
    renderOpen({ side: 'right' });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('open sheet with description has no critical a11y violations', async () => {
    renderOpen({ description: 'Sheet description' });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('open left sheet has no critical a11y violations', async () => {
    renderOpen({ side: 'left' });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
