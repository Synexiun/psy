/**
 * Contract tests for packages/design-system/src/primitives/Skeleton.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets:
 *   - All 3 variants render with the correct border-radius class
 *   - Circle variant makes width equal to height
 *   - Default values: variant=rect, width=100%, height=1rem
 *   - aria-hidden="true" is always present
 *   - forwardRef attaches to the underlying <div>
 *   - className passthrough merges onto the div
 *   - Token hygiene: bg-surface-tertiary (not bg-surface-200)
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { createRef } from 'react';
import { Skeleton } from '@disciplineos/design-system/primitives/Skeleton';

// ---------------------------------------------------------------------------
// Variants — correct border-radius class
// ---------------------------------------------------------------------------

describe('Skeleton — variants', () => {
  it('applies rounded-md for variant="text"', () => {
    const { container } = render(<Skeleton variant="text" />);
    expect(container.firstElementChild?.className).toContain('rounded-md');
  });

  it('applies rounded-full for variant="circle"', () => {
    const { container } = render(<Skeleton variant="circle" />);
    expect(container.firstElementChild?.className).toContain('rounded-full');
  });

  it('applies rounded-lg for variant="rect"', () => {
    const { container } = render(<Skeleton variant="rect" />);
    expect(container.firstElementChild?.className).toContain('rounded-lg');
  });

  it('renders all three variants without throwing', () => {
    const variants = ['text', 'circle', 'rect'] as const;
    for (const variant of variants) {
      expect(() => render(<Skeleton variant={variant} />)).not.toThrow();
    }
  });
});

// ---------------------------------------------------------------------------
// Circle variant — width equals height
// ---------------------------------------------------------------------------

describe('Skeleton — circle variant geometry', () => {
  it('sets width equal to height for variant="circle"', () => {
    const height = '48px';
    const { container } = render(
      <Skeleton variant="circle" height={height} width="200px" />,
    );
    const el = container.firstElementChild as HTMLElement;
    // Circle variant ignores the width prop and uses height for both dimensions
    expect(el.style.width).toBe(height);
    expect(el.style.height).toBe(height);
  });

  it('uses height for both dimensions when width is not provided for circle', () => {
    const { container } = render(<Skeleton variant="circle" height="32px" />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.style.width).toBe('32px');
    expect(el.style.height).toBe('32px');
  });
});

// ---------------------------------------------------------------------------
// Default values
// ---------------------------------------------------------------------------

describe('Skeleton — defaults', () => {
  it('defaults to variant="rect" (rounded-lg class present)', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstElementChild?.className).toContain('rounded-lg');
  });

  it('defaults to width="100%"', () => {
    const { container } = render(<Skeleton />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.style.width).toBe('100%');
  });

  it('defaults to height="1rem"', () => {
    const { container } = render(<Skeleton />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.style.height).toBe('1rem');
  });

  it('renders a <div> element by default', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstElementChild?.tagName).toBe('DIV');
  });
});

// ---------------------------------------------------------------------------
// Accessibility — aria-hidden
// ---------------------------------------------------------------------------

describe('Skeleton — accessibility', () => {
  it('always has aria-hidden="true"', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstElementChild?.getAttribute('aria-hidden')).toBe('true');
  });

  it('preserves aria-hidden="true" for every variant', () => {
    const variants = ['text', 'circle', 'rect'] as const;
    for (const variant of variants) {
      const { container } = render(<Skeleton variant={variant} />);
      expect(container.firstElementChild?.getAttribute('aria-hidden')).toBe('true');
    }
  });
});

// ---------------------------------------------------------------------------
// forwardRef
// ---------------------------------------------------------------------------

describe('Skeleton — forwardRef', () => {
  it('attaches ref to the underlying <div> element', () => {
    const ref = createRef<HTMLDivElement>();
    render(<Skeleton ref={ref} />);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('DIV');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Skeleton — className passthrough', () => {
  it('merges additional className onto the div element', () => {
    const { container } = render(<Skeleton className="custom-class" />);
    expect(container.firstElementChild?.className).toContain('custom-class');
  });

  it('preserves the base animate-pulse class alongside custom className', () => {
    const { container } = render(<Skeleton className="my-extra-class" />);
    expect(container.firstElementChild?.className).toContain('animate-pulse');
    expect(container.firstElementChild?.className).toContain('my-extra-class');
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — bg-surface-tertiary (not bg-surface-200)
// ---------------------------------------------------------------------------

describe('Skeleton — token hygiene', () => {
  it('uses bg-surface-tertiary token (not the deprecated bg-surface-200)', () => {
    const { container } = render(<Skeleton />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('bg-surface-tertiary');
    expect(cls).not.toContain('bg-surface-200');
  });

  it('no hardcoded hsl() in className output', () => {
    const { container } = render(<Skeleton />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  const variants = ['text', 'circle', 'rect'] as const;

  it.each(variants)('no bg-surface-200 for variant="%s"', (variant) => {
    const { container } = render(<Skeleton variant={variant} />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('bg-surface-200');
  });
});
