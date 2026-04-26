/**
 * Contract tests for packages/design-system/src/primitives/Button.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests (see packages/design-system/src/primitives/web.test.ts).
 *
 * Coverage target: every prop, every variant, every size, ref forwarding.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { Button } from '@disciplineos/design-system/primitives/Button';

// ---------------------------------------------------------------------------
// Rendering — variants
// ---------------------------------------------------------------------------

describe('Button — variants', () => {
  const variants = ['primary', 'calm', 'ghost', 'crisis', 'secondary'] as const;

  it.each(variants)('renders variant="%s" without throwing', (variant) => {
    expect(() =>
      render(<Button variant={variant}>{variant} button</Button>),
    ).not.toThrow();
  });

  it('applies accent-bronze class for primary variant', () => {
    const { container } = render(<Button variant="primary">Primary</Button>);
    expect(container.firstElementChild?.className).toContain('accent-bronze');
  });

  it('applies accent-teal class for calm variant', () => {
    const { container } = render(<Button variant="calm">Calm</Button>);
    expect(container.firstElementChild?.className).toContain('accent-teal');
  });

  it('applies signal-crisis class for crisis variant', () => {
    const { container } = render(<Button variant="crisis">Crisis</Button>);
    expect(container.firstElementChild?.className).toContain('signal-crisis');
  });

  it('applies surface-tertiary class for secondary variant', () => {
    const { container } = render(<Button variant="secondary">Secondary</Button>);
    expect(container.firstElementChild?.className).toContain('surface-tertiary');
  });

  it('applies ink-secondary class for ghost variant', () => {
    const { container } = render(<Button variant="ghost">Ghost</Button>);
    expect(container.firstElementChild?.className).toContain('ink-secondary');
  });
});

// ---------------------------------------------------------------------------
// Rendering — sizes
// ---------------------------------------------------------------------------

describe('Button — sizes', () => {
  const sizes = ['sm', 'md', 'lg', 'crisis'] as const;

  it.each(sizes)('renders size="%s" without throwing', (size) => {
    expect(() =>
      render(<Button size={size}>{size} button</Button>),
    ).not.toThrow();
  });

  it('applies h-8 for sm size', () => {
    const { container } = render(<Button size="sm">Small</Button>);
    expect(container.firstElementChild?.className).toContain('h-8');
  });

  it('applies h-10 for md size', () => {
    const { container } = render(<Button size="md">Medium</Button>);
    expect(container.firstElementChild?.className).toContain('h-10');
  });

  it('applies h-12 for lg size', () => {
    const { container } = render(<Button size="lg">Large</Button>);
    expect(container.firstElementChild?.className).toContain('h-12');
  });

  it('applies min-h-14 and w-full for crisis size', () => {
    const { container } = render(<Button size="crisis">Crisis</Button>);
    expect(container.firstElementChild?.className).toContain('min-h-14');
    expect(container.firstElementChild?.className).toContain('w-full');
  });
});

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

describe('Button — defaults', () => {
  it('renders as a <button> element', () => {
    render(<Button>Default</Button>);
    expect(screen.getByRole('button', { name: /default/i })).toBeInTheDocument();
  });

  it('defaults to variant=primary (accent-bronze class present)', () => {
    const { container } = render(<Button>Default</Button>);
    expect(container.firstElementChild?.className).toContain('accent-bronze');
  });

  it('defaults to size=md (h-10 class present)', () => {
    const { container } = render(<Button>Default</Button>);
    expect(container.firstElementChild?.className).toContain('h-10');
  });
});

// ---------------------------------------------------------------------------
// loading prop
// ---------------------------------------------------------------------------

describe('Button — loading prop', () => {
  it('sets aria-busy="true" when loading', () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });

  it('is disabled when loading (loading implies disabled)', () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders a spinner indicator when loading', () => {
    const { container } = render(<Button loading>Save</Button>);
    // The spinner is a <span> with animate-spin class
    const spinner = container.querySelector('span.animate-spin');
    expect(spinner).not.toBeNull();
  });

  it('does not render a spinner when not loading', () => {
    const { container } = render(<Button>Save</Button>);
    expect(container.querySelector('span.animate-spin')).toBeNull();
  });

  it('sets aria-busy="false" when not loading', () => {
    render(<Button>Save</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
  });
});

// ---------------------------------------------------------------------------
// disabled prop
// ---------------------------------------------------------------------------

describe('Button — disabled prop', () => {
  it('is disabled when disabled prop is set', () => {
    render(<Button disabled>Inactive</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is not disabled by default', () => {
    render(<Button>Active</Button>);
    expect(screen.getByRole('button')).not.toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// forwardRef
// ---------------------------------------------------------------------------

describe('Button — forwardRef', () => {
  it('attaches ref to the underlying <button> element', () => {
    const ref = createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Ref test</Button>);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('BUTTON');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Button — className passthrough', () => {
  it('merges additional className onto the button element', () => {
    const { container } = render(<Button className="custom-class">Extra class</Button>);
    expect(container.firstElementChild?.className).toContain('custom-class');
  });
});

// ---------------------------------------------------------------------------
// onClick / event passthrough
// ---------------------------------------------------------------------------

describe('Button — event passthrough', () => {
  it('calls onClick handler when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    button.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Button — token hygiene', () => {
  const variants = ['primary', 'calm', 'ghost', 'crisis', 'secondary'] as const;

  it.each(variants)('no hardcoded hsl() in className for variant="%s"', (variant) => {
    const { container } = render(<Button variant={variant}>{variant}</Button>);
    const className = container.firstElementChild?.className ?? '';
    // className string must not contain raw hsl( — tokens are Tailwind utility names
    expect(className).not.toContain('hsl(');
  });
});
