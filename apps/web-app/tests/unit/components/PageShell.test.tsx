/**
 * Contract tests for packages/design-system/src/primitives/PageShell.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * PageShell is a pure layout primitive — no Radix, no portals. Every element
 * is synchronously in the DOM after render. Tests cover:
 *   - Heading rendered as <h1>
 *   - Children rendered in the body region
 *   - Optional subheading: present when provided, absent when not
 *   - Optional backHref: <a> with correct href when provided, absent when not
 *   - backLabel default ("Back") when backHref is set but backLabel is omitted
 *   - Optional actions: present when provided, absent when not
 *   - className forwarded to outermost div
 *   - axe accessibility (color-contrast disabled — jsdom has no computed styles)
 *   - RTL: back-arrow SVG carries rtl:-scale-x-100 class
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { PageShell } from '@disciplineos/design-system/primitives/PageShell';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// axe instance — color-contrast disabled (jsdom has no computed styles)
// ---------------------------------------------------------------------------

const axeWithConfig = configureAxe({
  rules: {
    // color-contrast requires computed styles not available in jsdom
    'color-contrast': { enabled: false },
    // region rule flags content not inside a landmark — PageShell is a content
    // column that intentionally renders without a wrapping <main> in tests.
    // In production it is placed inside a <main> by the page layout.
    'region': { enabled: false },
  },
});

// ---------------------------------------------------------------------------
// 1. Heading rendered as <h1>
// ---------------------------------------------------------------------------

describe('PageShell — heading', () => {
  it('renders the heading as an h1 element', () => {
    render(
      <PageShell heading="Dashboard">
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.getByRole('heading', { level: 1, name: /dashboard/i })).toBeInTheDocument();
  });

  it('renders heading text correctly', () => {
    render(
      <PageShell heading="My Page Title">
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.getByText('My Page Title')).toBeInTheDocument();
  });

  it('renders ReactNode heading (JSX content)', () => {
    render(
      <PageShell heading={<span>Rich Heading</span>}>
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.getByText('Rich Heading')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. Children rendered
// ---------------------------------------------------------------------------

describe('PageShell — children', () => {
  it('renders children content', () => {
    render(
      <PageShell heading="Page">
        <p>Body paragraph</p>
      </PageShell>,
    );
    expect(screen.getByText('Body paragraph')).toBeInTheDocument();
  });

  it('renders multiple children', () => {
    render(
      <PageShell heading="Page">
        <p>First child</p>
        <p>Second child</p>
      </PageShell>,
    );
    expect(screen.getByText('First child')).toBeInTheDocument();
    expect(screen.getByText('Second child')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 3. Subheading — optional
// ---------------------------------------------------------------------------

describe('PageShell — subheading', () => {
  it('renders subheading when provided', () => {
    render(
      <PageShell heading="Page" subheading="A helpful description">
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.getByText('A helpful description')).toBeInTheDocument();
  });

  it('does not render a subheading element when omitted', () => {
    const { baseElement } = render(
      <PageShell heading="Page">
        <p>Content</p>
      </PageShell>,
    );
    // The subheading renders as a <p> with text-ink-tertiary; confirm absence
    expect(screen.queryByText('A helpful description')).toBeNull();
    // No second <p> sibling to the h1 should be in the heading block
    const headingBlock = baseElement.querySelector('h1')?.parentElement;
    const paragraphs = headingBlock?.querySelectorAll('p') ?? [];
    expect(paragraphs.length).toBe(0);
  });

  it('renders subheading as a <p> element', () => {
    const { baseElement } = render(
      <PageShell heading="Page" subheading="Sub text">
        <p>Content</p>
      </PageShell>,
    );
    const h1 = baseElement.querySelector('h1');
    const subEl = h1?.nextElementSibling;
    expect(subEl?.tagName.toLowerCase()).toBe('p');
    expect(subEl?.textContent).toBe('Sub text');
  });
});

// ---------------------------------------------------------------------------
// 4. backHref — optional
// ---------------------------------------------------------------------------

describe('PageShell — backHref', () => {
  it('renders a back link with correct href when backHref is provided', () => {
    render(
      <PageShell heading="Page" backHref="/dashboard" backLabel="Back to dashboard">
        <p>Content</p>
      </PageShell>,
    );
    const link = screen.getByRole('link', { name: /back to dashboard/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/dashboard');
  });

  it('does not render a back link when backHref is omitted', () => {
    render(
      <PageShell heading="Page">
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.queryByRole('link')).toBeNull();
  });

  it('back link is an <a> element', () => {
    const { baseElement } = render(
      <PageShell heading="Page" backHref="/home">
        <p>Content</p>
      </PageShell>,
    );
    const anchor = baseElement.querySelector('a');
    expect(anchor).not.toBeNull();
    expect(anchor?.getAttribute('href')).toBe('/home');
  });
});

// ---------------------------------------------------------------------------
// 5. backLabel default
// ---------------------------------------------------------------------------

describe('PageShell — backLabel default', () => {
  it('defaults backLabel to "Back" when backHref is provided but backLabel is omitted', () => {
    render(
      <PageShell heading="Page" backHref="/home">
        <p>Content</p>
      </PageShell>,
    );
    // The link contains visible text "Back" (the SVG aria-hidden label is separate)
    const link = screen.getByRole('link');
    expect(link.textContent).toContain('Back');
  });

  it('uses the provided backLabel when specified', () => {
    render(
      <PageShell heading="Page" backHref="/home" backLabel="Return to overview">
        <p>Content</p>
      </PageShell>,
    );
    const link = screen.getByRole('link');
    expect(link.textContent).toContain('Return to overview');
  });
});

// ---------------------------------------------------------------------------
// 6. actions — optional
// ---------------------------------------------------------------------------

describe('PageShell — actions', () => {
  it('renders actions when provided', () => {
    render(
      <PageShell heading="Page" actions={<button>Save</button>}>
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('does not render actions container when actions is omitted', () => {
    const { baseElement } = render(
      <PageShell heading="Page">
        <p>Content</p>
      </PageShell>,
    );
    // The actions wrapper has 'shrink-0' class — ensure it's not present
    const shrinkEl = baseElement.querySelector('.shrink-0');
    expect(shrinkEl).toBeNull();
  });

  it('renders multiple action elements', () => {
    render(
      <PageShell
        heading="Page"
        actions={
          <>
            <button>Cancel</button>
            <button>Save</button>
          </>
        }
      >
        <p>Content</p>
      </PageShell>,
    );
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 7. className forwarding to outermost div
// ---------------------------------------------------------------------------

describe('PageShell — className forwarding', () => {
  it('forwards className to the outermost container', () => {
    const { baseElement } = render(
      <PageShell heading="Page" className="custom-page-class">
        <p>Content</p>
      </PageShell>,
    );
    const outer = baseElement.firstElementChild?.firstElementChild;
    expect(outer?.className).toContain('custom-page-class');
  });

  it('outermost div className is trimmed (no leading/trailing whitespace)', () => {
    const { baseElement } = render(
      <PageShell heading="Page" className="">
        <p>Content</p>
      </PageShell>,
    );
    const outer = baseElement.firstElementChild?.firstElementChild;
    expect(outer?.className).not.toMatch(/^\s|\s$/);
  });
});

// ---------------------------------------------------------------------------
// 8. axe accessibility
// ---------------------------------------------------------------------------

describe('PageShell — axe accessibility', () => {
  it('heading-only shell has no a11y violations', async () => {
    render(
      <PageShell heading="Dashboard">
        <p>Content</p>
      </PageShell>,
    );
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('shell with back link has no a11y violations', async () => {
    render(
      <PageShell heading="Dashboard" backHref="/home" backLabel="Back to home">
        <p>Content</p>
      </PageShell>,
    );
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });

  it('full shell (all props) has no a11y violations', async () => {
    render(
      <PageShell
        heading="Dashboard"
        subheading="Summary of your progress"
        backHref="/home"
        backLabel="Back"
        actions={<button>Save</button>}
        className="my-class"
      >
        <p>Content</p>
      </PageShell>,
    );
    const results = await axeWithConfig(document.body);
    expect(results).toHaveNoViolations();
  });
});

// ---------------------------------------------------------------------------
// 9. RTL — back arrow SVG has rtl:-scale-x-100 class
// ---------------------------------------------------------------------------

describe('PageShell — RTL back arrow', () => {
  it('back arrow SVG has rtl:-scale-x-100 class for RTL mirroring', () => {
    const { baseElement } = render(
      <PageShell heading="Page" backHref="/home" backLabel="Back">
        <p>Content</p>
      </PageShell>,
    );
    const svg = baseElement.querySelector('a svg');
    expect(svg).not.toBeNull();
    // SVG className is SVGAnimatedString in jsdom — use getAttribute('class')
    expect(svg?.getAttribute('class')).toContain('rtl:-scale-x-100');
  });

  it('renders back arrow and label inside dir="rtl" wrapper without throwing', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <PageShell heading="صفحة" backHref="/home" backLabel="رجوع">
            <p>محتوى</p>
          </PageShell>
        </div>,
      ),
    ).not.toThrow();
  });

  it('renders heading text correctly inside dir="rtl" wrapper', () => {
    render(
      <div dir="rtl">
        <PageShell heading="لوحة التحكم">
          <p>محتوى</p>
        </PageShell>
      </div>,
    );
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });
});
