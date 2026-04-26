/**
 * Contract tests for packages/design-system/src/primitives/Tooltip.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Radix Tooltip is pointer-event driven. Testing hover-triggered open state in
 * jsdom is unreliable, so we test structure (children render, no duplicate
 * tooltip content in closed state) and prop passthrough via class assertions.
 *
 * forwardRef is NOT needed for Tooltip (it wraps Radix, not a DOM element).
 *
 * RTL contract: when rendered in a dir="rtl" context the children must still
 * render correctly. Radix's popper layer handles physical side placement
 * automatically — the component itself carries no manual sideClasses map.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Tooltip } from '@disciplineos/design-system/primitives/Tooltip';

// ---------------------------------------------------------------------------
// Children rendering
// ---------------------------------------------------------------------------

describe('Tooltip — children', () => {
  it('renders children in the trigger', () => {
    render(
      <Tooltip tooltipContent="Tip text">
        <button>Hover me</button>
      </Tooltip>,
    );
    expect(screen.getByRole('button', { name: /hover me/i })).toBeInTheDocument();
  });

  it('renders plain text children', () => {
    render(
      <Tooltip tooltipContent="Tip text">
        <span>Label</span>
      </Tooltip>,
    );
    expect(screen.getByText('Label')).toBeInTheDocument();
  });

  it('renders multiple children types without throwing', () => {
    expect(() =>
      render(
        <Tooltip tooltipContent="Tip">
          <span>
            <strong>Bold</strong> text
          </span>
        </Tooltip>,
      ),
    ).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Default closed state — tooltip content NOT in DOM until opened
// ---------------------------------------------------------------------------

describe('Tooltip — default closed', () => {
  it('does not render tooltipContent in the DOM when closed', () => {
    render(
      <Tooltip tooltipContent="Hidden tip">
        <button>Trigger</button>
      </Tooltip>,
    );
    // Radix portals content only when open; jsdom does not trigger pointer events
    expect(screen.queryByText('Hidden tip')).toBeNull();
  });

  it('tooltip panel is not in DOM when tooltip is closed', () => {
    const { container } = render(
      <Tooltip tooltipContent="Panel content">
        <button>T</button>
      </Tooltip>,
    );
    expect(container.querySelector('[role="tooltip"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// tooltipContent prop
// ---------------------------------------------------------------------------

describe('Tooltip — tooltipContent prop', () => {
  it('accepts a string as tooltipContent without throwing', () => {
    expect(() =>
      render(
        <Tooltip tooltipContent="String tip">
          <button>Trigger</button>
        </Tooltip>,
      ),
    ).not.toThrow();
  });

  it('accepts a React node as tooltipContent without throwing', () => {
    expect(() =>
      render(
        <Tooltip tooltipContent={<span><strong>Bold</strong> tip</span>}>
          <button>Trigger</button>
        </Tooltip>,
      ),
    ).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// side prop — component accepts all four sides without throwing
// ---------------------------------------------------------------------------

describe('Tooltip — side prop', () => {
  const sides = ['top', 'bottom', 'left', 'right'] as const;

  it.each(sides)('renders without throwing for side="%s"', (side) => {
    expect(() =>
      render(
        <Tooltip tooltipContent="Tip" side={side}>
          <button>Btn</button>
        </Tooltip>,
      ),
    ).not.toThrow();
  });

  it('defaults to side="top" without throwing (no side prop)', () => {
    expect(() =>
      render(
        <Tooltip tooltipContent="Tip">
          <button>Btn</button>
        </Tooltip>,
      ),
    ).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// className prop — forwarded to trigger wrapper
// ---------------------------------------------------------------------------

describe('Tooltip — className prop', () => {
  it('applies className to the trigger wrapper span', () => {
    const { container } = render(
      <Tooltip tooltipContent="Tip" className="custom-class">
        <button>Btn</button>
      </Tooltip>,
    );
    // The wrapper span should carry the custom class
    const wrapper = container.querySelector('span.custom-class');
    expect(wrapper).not.toBeNull();
  });

  it('trigger wrapper always carries inline-flex class', () => {
    const { container } = render(
      <Tooltip tooltipContent="Tip">
        <button>Btn</button>
      </Tooltip>,
    );
    const span = container.querySelector('span');
    expect(span?.className).toContain('inline-flex');
  });
});

// ---------------------------------------------------------------------------
// RTL — children render correctly in a dir="rtl" context
// ---------------------------------------------------------------------------

describe('Tooltip — RTL context', () => {
  it('renders children correctly inside dir="rtl" wrapper', () => {
    render(
      <div dir="rtl">
        <Tooltip tooltipContent="نکته">
          <button>دکمه</button>
        </Tooltip>
      </div>,
    );
    expect(screen.getByRole('button', { name: /دکمه/i })).toBeInTheDocument();
  });

  it('does not throw when dir="rtl" and side="left"', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <Tooltip tooltipContent="نکته" side="left">
            <button>RTL trigger</button>
          </Tooltip>
        </div>,
      ),
    ).not.toThrow();
  });

  it('does not throw when dir="rtl" and side="right"', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <Tooltip tooltipContent="نکته" side="right">
            <button>RTL trigger</button>
          </Tooltip>
        </div>,
      ),
    ).not.toThrow();
  });

  it('does not throw when dir="rtl" and side="top"', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <Tooltip tooltipContent="نکته" side="top">
            <button>RTL top</button>
          </Tooltip>
        </div>,
      ),
    ).not.toThrow();
  });

  it('does not throw when dir="rtl" and side="bottom"', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <Tooltip tooltipContent="نکته" side="bottom">
            <button>RTL bottom</button>
          </Tooltip>
        </div>,
      ),
    ).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() in trigger className
// ---------------------------------------------------------------------------

describe('Tooltip — token hygiene', () => {
  it('does not contain hardcoded hsl() in trigger className', () => {
    const { container } = render(
      <Tooltip tooltipContent="Tip">
        <button>Btn</button>
      </Tooltip>,
    );
    const className = container.querySelector('span')?.className ?? '';
    expect(className).not.toContain('hsl(');
  });
});
