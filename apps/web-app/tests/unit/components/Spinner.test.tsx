/**
 * Contract tests for packages/design-system/src/primitives/Spinner.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets:
 *   - All 3 sizes render with correct SVG width/height attributes
 *   - role="status" is present on the svg element
 *   - aria-label defaults to "Loading" and accepts a custom label
 *   - className passthrough appended to the svg element
 *   - Geometry regression guard: r attribute matches (dim - 6) / 2 for each size
 *   - Token hygiene: no hardcoded hsl() in className output
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Spinner } from '@disciplineos/design-system/primitives/Spinner';

// ---------------------------------------------------------------------------
// Size rendering — SVG width and height attributes
// ---------------------------------------------------------------------------

describe('Spinner — size rendering', () => {
  it('renders size="sm" with width=16 and height=16', () => {
    const { container } = render(<Spinner size="sm" />);
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute('width')).toBe('16');
    expect(svg?.getAttribute('height')).toBe('16');
  });

  it('renders size="md" with width=24 and height=24', () => {
    const { container } = render(<Spinner size="md" />);
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute('width')).toBe('24');
    expect(svg?.getAttribute('height')).toBe('24');
  });

  it('renders size="lg" with width=32 and height=32', () => {
    const { container } = render(<Spinner size="lg" />);
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute('width')).toBe('32');
    expect(svg?.getAttribute('height')).toBe('32');
  });

  it('defaults to size="md" (width=24, height=24) when size is omitted', () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('24');
    expect(svg?.getAttribute('height')).toBe('24');
  });
});

// ---------------------------------------------------------------------------
// Accessibility — role and aria-label
// ---------------------------------------------------------------------------

describe('Spinner — accessibility', () => {
  it('has role="status" on the svg element', () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('role')).toBe('status');
  });

  it('defaults aria-label to "Loading"', () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('aria-label')).toBe('Loading');
  });

  it('accepts a custom aria-label via label prop', () => {
    const { container } = render(<Spinner label="Saving data" />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('aria-label')).toBe('Saving data');
  });

  it('uses the provided label instead of the default', () => {
    const { container } = render(<Spinner label="Please wait" />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('aria-label')).not.toBe('Loading');
    expect(svg?.getAttribute('aria-label')).toBe('Please wait');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Spinner — className passthrough', () => {
  // Note: SVG elements use SVGAnimatedString for className in jsdom, so we
  // read the class attribute via getAttribute('class') rather than .className.

  it('includes animate-spin in the class attribute', () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('class')).toContain('animate-spin');
  });

  it('appends the custom className to the svg element', () => {
    const { container } = render(<Spinner className="text-accent-bronze" />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('class')).toContain('text-accent-bronze');
  });

  it('preserves animate-spin alongside the custom className', () => {
    const { container } = render(<Spinner className="custom-class" />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('class')).toContain('animate-spin');
    expect(svg?.getAttribute('class')).toContain('custom-class');
  });

  it('uses empty string as the className default (animate-spin only)', () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector('svg');
    // Template literal `animate-spin ${className}` with className='' produces
    // "animate-spin " (trailing space). Trim before asserting.
    expect(svg?.getAttribute('class')?.trim()).toBe('animate-spin');
  });
});

// ---------------------------------------------------------------------------
// Geometry regression guard
// ---------------------------------------------------------------------------

describe('Spinner — geometry', () => {
  const cases: Array<{ size: 'sm' | 'md' | 'lg'; dim: number }> = [
    { size: 'sm', dim: 16 },
    { size: 'md', dim: 24 },
    { size: 'lg', dim: 32 },
  ];

  it.each(cases)(
    'size="$size": circle r attribute equals (dim - 6) / 2 = ${ (dim - 6) / 2 }',
    ({ size, dim }) => {
      const { container } = render(<Spinner size={size} />);
      const circle = container.querySelector('circle');
      expect(circle).not.toBeNull();
      const expectedRadius = (dim - 6) / 2;
      expect(circle?.getAttribute('r')).toBe(String(expectedRadius));
    },
  );

  it('size="sm": r=5 (dim=16, (16-6)/2=5)', () => {
    const { container } = render(<Spinner size="sm" />);
    const circle = container.querySelector('circle');
    expect(circle?.getAttribute('r')).toBe('5');
  });

  it('size="md": r=9 (dim=24, (24-6)/2=9)', () => {
    const { container } = render(<Spinner size="md" />);
    const circle = container.querySelector('circle');
    expect(circle?.getAttribute('r')).toBe('9');
  });

  it('size="lg": r=13 (dim=32, (32-6)/2=13)', () => {
    const { container } = render(<Spinner size="lg" />);
    const circle = container.querySelector('circle');
    expect(circle?.getAttribute('r')).toBe('13');
  });

  it('circle cx and cy are always dim/2', () => {
    const sizes: Array<'sm' | 'md' | 'lg'> = ['sm', 'md', 'lg'];
    const dims = { sm: 16, md: 24, lg: 32 };
    for (const size of sizes) {
      const { container } = render(<Spinner size={size} />);
      const circle = container.querySelector('circle');
      const half = String(dims[size] / 2);
      expect(circle?.getAttribute('cx')).toBe(half);
      expect(circle?.getAttribute('cy')).toBe(half);
    }
  });

  it('circle strokeWidth is always 3', () => {
    const { container } = render(<Spinner size="md" />);
    const circle = container.querySelector('circle');
    expect(circle?.getAttribute('stroke-width')).toBe('3');
  });

  it('circle stroke is always "currentColor"', () => {
    const { container } = render(<Spinner size="md" />);
    const circle = container.querySelector('circle');
    expect(circle?.getAttribute('stroke')).toBe('currentColor');
  });

  it('circle fill is always "none"', () => {
    const { container } = render(<Spinner size="md" />);
    const circle = container.querySelector('circle');
    expect(circle?.getAttribute('fill')).toBe('none');
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Spinner — token hygiene', () => {
  const sizes: Array<'sm' | 'md' | 'lg'> = ['sm', 'md', 'lg'];

  it.each(sizes)('no hardcoded hsl() in class attribute for size="%s"', (size) => {
    const { container } = render(<Spinner size={size} />);
    const svg = container.querySelector('svg');
    const cls = svg?.getAttribute('class') ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() with custom className', () => {
    const { container } = render(<Spinner className="text-ink-primary" />);
    const svg = container.querySelector('svg');
    const cls = svg?.getAttribute('class') ?? '';
    expect(cls).not.toContain('hsl(');
  });
});
