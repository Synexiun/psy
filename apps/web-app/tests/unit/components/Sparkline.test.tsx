/**
 * Contract tests for the Visx-backed Sparkline primitive.
 *
 * These tests pin the public prop contract. Any change that breaks one of
 * these tests signals an API regression — resolve by updating the contract
 * docs and bumping the design-system major version, not by relaxing the test.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Sparkline } from '@disciplineos/design-system/primitives/Sparkline';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const VALID_DATA = [3, 5, 4, 7, 6, 9, 8];
const TWO_POINT_DATA = [3, 7];

// ---------------------------------------------------------------------------
// Null guard — data.length < 2
// ---------------------------------------------------------------------------

describe('Sparkline — null guard', () => {
  it('returns null for empty data', () => {
    const { container } = render(<Sparkline data={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null for a single data point', () => {
    const { container } = render(<Sparkline data={[5]} />);
    expect(container.firstChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// SVG rendering — valid data
// ---------------------------------------------------------------------------

describe('Sparkline — SVG rendering', () => {
  it('renders an SVG element for valid data (length >= 2)', () => {
    const { container } = render(<Sparkline data={VALID_DATA} />);
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('renders an SVG for a two-point dataset (minimum valid)', () => {
    const { container } = render(<Sparkline data={TWO_POINT_DATA} />);
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('sets the SVG role to "img"', () => {
    render(<Sparkline data={VALID_DATA} />);
    expect(screen.getAllByRole('img').length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// aria-label prop
// ---------------------------------------------------------------------------

describe('Sparkline — aria-label', () => {
  it('renders aria-label when ariaLabel prop is provided', () => {
    render(<Sparkline data={VALID_DATA} ariaLabel="Mood trend over 7 check-ins" />);
    expect(
      screen.getByRole('img', { name: /mood trend over 7 check-ins/i }),
    ).toBeInTheDocument();
  });

  it('aria-label is absent when ariaLabel prop is omitted', () => {
    const { container } = render(<Sparkline data={VALID_DATA} />);
    const svg = container.querySelector('svg');
    // aria-label attribute should not be present (or should be empty/undefined)
    expect(svg?.getAttribute('aria-label')).toBeFalsy();
  });
});

// ---------------------------------------------------------------------------
// Dimension props — width / height pass through to SVG attributes
// ---------------------------------------------------------------------------

describe('Sparkline — dimension props', () => {
  it('applies default width (120) to the SVG element', () => {
    const { container } = render(<Sparkline data={VALID_DATA} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '120');
  });

  it('applies default height (40) to the SVG element', () => {
    const { container } = render(<Sparkline data={VALID_DATA} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('height', '40');
  });

  it('applies custom width to the SVG element', () => {
    const { container } = render(<Sparkline data={VALID_DATA} width={240} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '240');
  });

  it('applies custom height to the SVG element', () => {
    const { container } = render(<Sparkline data={VALID_DATA} height={60} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('height', '60');
  });

  it('viewBox reflects the supplied width and height', () => {
    const { container } = render(<Sparkline data={VALID_DATA} width={200} height={50} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('viewBox', '0 0 200 50');
  });
});

// ---------------------------------------------------------------------------
// Color token — accent-bronze default
// ---------------------------------------------------------------------------

describe('Sparkline — color token hygiene', () => {
  it('default color is var(--color-accent-bronze)', () => {
    // The LinePath stroke and AreaClosed fill are both driven by the color prop.
    // We verify by rendering without a color prop and checking that the SVG
    // paths carry the expected CSS variable (jsdom preserves attribute values).
    const { container } = render(<Sparkline data={VALID_DATA} />);
    const paths = container.querySelectorAll('path');
    const strokes = Array.from(paths).map((p) => p.getAttribute('stroke')).filter(Boolean);
    const fills = Array.from(paths).map((p) => p.getAttribute('fill')).filter(Boolean);
    const colorValues = [...strokes, ...fills];
    const hasBronze = colorValues.some((v) => v?.includes('--color-accent-bronze'));
    expect(hasBronze).toBe(true);
  });

  it('default color is NOT var(--color-brand-500) (old token — must not regress)', () => {
    const { container } = render(<Sparkline data={VALID_DATA} />);
    const allElements = container.querySelectorAll('*');
    const hasOldToken = Array.from(allElements).some(
      (el) =>
        el.getAttribute('stroke')?.includes('--color-brand-500') ||
        el.getAttribute('fill')?.includes('--color-brand-500'),
    );
    expect(hasOldToken).toBe(false);
  });

  it('accepts a custom color prop and applies it to the line', () => {
    const { container } = render(
      <Sparkline data={VALID_DATA} color="var(--color-signal-stable)" />,
    );
    const paths = container.querySelectorAll('path');
    const strokes = Array.from(paths).map((p) => p.getAttribute('stroke')).filter(Boolean);
    expect(strokes.some((s) => s?.includes('--color-signal-stable'))).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// strokeWidth prop
// ---------------------------------------------------------------------------

describe('Sparkline — strokeWidth prop', () => {
  it('applies custom strokeWidth to the line path', () => {
    const { container } = render(<Sparkline data={VALID_DATA} strokeWidth={4} />);
    const paths = container.querySelectorAll('path');
    const widths = Array.from(paths).map((p) => p.getAttribute('stroke-width')).filter(Boolean);
    expect(widths.some((w) => w === '4')).toBe(true);
  });

  it('default strokeWidth is 2', () => {
    const { container } = render(<Sparkline data={VALID_DATA} />);
    const paths = container.querySelectorAll('path');
    const widths = Array.from(paths).map((p) => p.getAttribute('stroke-width')).filter(Boolean);
    expect(widths.some((w) => w === '2')).toBe(true);
  });
});
