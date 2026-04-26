/**
 * Contract tests for packages/design-system/src/primitives/Divider.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests (see packages/design-system/src/primitives/web.test.ts).
 *
 * Coverage target: every prop, every orientation, labeled variant, role="separator"
 * on all variants, className passthrough, token hygiene (no hsl() in className).
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Divider } from '@disciplineos/design-system/primitives/Divider';

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

describe('Divider — defaults', () => {
  it('renders without throwing', () => {
    expect(() => render(<Divider />)).not.toThrow();
  });

  it('renders a separator element by default', () => {
    render(<Divider />);
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('defaults to horizontal orientation and renders as an <hr>', () => {
    const { container } = render(<Divider />);
    expect(container.querySelector('hr')).not.toBeNull();
  });

  it('applies border-t class on the default horizontal variant', () => {
    const { container } = render(<Divider />);
    const hr = container.querySelector('hr');
    expect(hr?.className).toContain('border-t');
  });

  it('applies border-border-subtle token on the default horizontal variant', () => {
    const { container } = render(<Divider />);
    const hr = container.querySelector('hr');
    expect(hr?.className).toContain('border-border-subtle');
  });
});

// ---------------------------------------------------------------------------
// Horizontal orientation (explicit)
// ---------------------------------------------------------------------------

describe('Divider — horizontal orientation', () => {
  it('renders role="separator" for explicit horizontal orientation', () => {
    render(<Divider orientation="horizontal" />);
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('renders as an <hr> for explicit horizontal orientation', () => {
    const { container } = render(<Divider orientation="horizontal" />);
    expect(container.querySelector('hr')).not.toBeNull();
  });

  it('does not set aria-orientation on the plain <hr> (implicit horizontal)', () => {
    render(<Divider orientation="horizontal" />);
    const sep = screen.getByRole('separator');
    // <hr> has implicit horizontal orientation — aria-orientation is redundant and omitted
    expect(sep).not.toHaveAttribute('aria-orientation');
  });
});

// ---------------------------------------------------------------------------
// Vertical orientation
// ---------------------------------------------------------------------------

describe('Divider — vertical orientation', () => {
  it('renders role="separator" for vertical orientation', () => {
    render(<Divider orientation="vertical" />);
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('renders a <div> for vertical orientation', () => {
    const { container } = render(<Divider orientation="vertical" />);
    expect(container.querySelector('div')).not.toBeNull();
  });

  it('sets aria-orientation="vertical"', () => {
    render(<Divider orientation="vertical" />);
    expect(screen.getByRole('separator')).toHaveAttribute('aria-orientation', 'vertical');
  });

  it('applies border-s (logical inline-start) — not physical border-l', () => {
    const { container } = render(<Divider orientation="vertical" />);
    const el = container.querySelector('[role="separator"]');
    expect(el?.className).toContain('border-s');
    expect(el?.className).not.toContain('border-l');
  });

  it('applies border-border-subtle token on the vertical variant', () => {
    const { container } = render(<Divider orientation="vertical" />);
    const el = container.querySelector('[role="separator"]');
    expect(el?.className).toContain('border-border-subtle');
  });

  it('applies w-px class for a 1 px wide rule', () => {
    const { container } = render(<Divider orientation="vertical" />);
    const el = container.querySelector('[role="separator"]');
    expect(el?.className).toContain('w-px');
  });
});

// ---------------------------------------------------------------------------
// Labeled (horizontal with label)
// ---------------------------------------------------------------------------

describe('Divider — labeled variant', () => {
  it('renders role="separator" when a label is provided', () => {
    render(<Divider label="or" />);
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('renders the label text', () => {
    render(<Divider label="or" />);
    expect(screen.getByText('or')).toBeInTheDocument();
  });

  it('renders a <div> (not <hr>) when a label is present', () => {
    const { container } = render(<Divider label="continue with" />);
    expect(container.querySelector('div[role="separator"]')).not.toBeNull();
    expect(container.querySelector('hr')).toBeNull();
  });

  it('sets aria-orientation="horizontal" on the labeled variant', () => {
    render(<Divider label="or" />);
    expect(screen.getByRole('separator')).toHaveAttribute('aria-orientation', 'horizontal');
  });

  it('applies border-border-subtle token on the label rule lines', () => {
    const { container } = render(<Divider label="or" />);
    const spans = container.querySelectorAll('span.flex-1');
    expect(spans.length).toBe(2);
    spans.forEach((span) => {
      expect(span.className).toContain('border-border-subtle');
    });
  });

  it('applies text-ink-tertiary token on the label text', () => {
    const { container } = render(<Divider label="or" />);
    const labelSpan = screen.getByText('or');
    expect(labelSpan.className).toContain('text-ink-tertiary');
  });

  it('applies text-xs class on the label text', () => {
    const { container } = render(<Divider label="or" />);
    const labelSpan = screen.getByText('or');
    expect(labelSpan.className).toContain('text-xs');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Divider — className passthrough', () => {
  it('merges additional className onto horizontal <hr>', () => {
    const { container } = render(<Divider className="my-custom-class" />);
    expect(container.querySelector('hr')?.className).toContain('my-custom-class');
  });

  it('merges additional className onto vertical <div>', () => {
    const { container } = render(<Divider orientation="vertical" className="my-vertical-class" />);
    const el = container.querySelector('[role="separator"]');
    expect(el?.className).toContain('my-vertical-class');
  });

  it('merges additional className onto labeled <div>', () => {
    const { container } = render(<Divider label="or" className="my-label-class" />);
    const el = container.querySelector('[role="separator"]');
    expect(el?.className).toContain('my-label-class');
  });

  it('preserves base classes alongside custom className', () => {
    const { container } = render(<Divider className="extra" />);
    const hr = container.querySelector('hr');
    expect(hr?.className).toContain('border-border-subtle');
    expect(hr?.className).toContain('extra');
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Divider — token hygiene', () => {
  it('no hardcoded hsl() in className for horizontal (default)', () => {
    const { container } = render(<Divider />);
    const cls = container.querySelector('[role="separator"]')?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className for vertical orientation', () => {
    const { container } = render(<Divider orientation="vertical" />);
    const cls = container.querySelector('[role="separator"]')?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className for labeled variant', () => {
    const { container } = render(<Divider label="or" />);
    // Check the separator container and all its children
    const allClassNames = Array.from(container.querySelectorAll('*'))
      .map((el) => el.className)
      .join(' ');
    expect(allClassNames).not.toContain('hsl(');
  });

  it('uses border-border-subtle token (not hardcoded border colour)', () => {
    const { container } = render(<Divider />);
    const cls = container.querySelector('[role="separator"]')?.className ?? '';
    expect(cls).toContain('border-border-subtle');
    expect(cls).not.toContain('[hsl(');
  });
});
