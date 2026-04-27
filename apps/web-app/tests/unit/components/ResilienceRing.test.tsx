'use client';
/**
 * Contract tests for packages/design-system/src/clinical/ResilienceRing.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here.
 *
 * Rules under test:
 *   Rule #3 — resilience streak never decrements across renders
 *   Rule #9 — Latin digits for clinical scores regardless of locale
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — component renders as role="img", not a landmark region
 */

import type * as React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { ResilienceRing } from '@disciplineos/design-system/clinical/ResilienceRing';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Rule #3 — monotonically non-decreasing value
// ---------------------------------------------------------------------------

it('dashboard_resilienceRing_value_never_decrements_across_renders', () => {
  const { rerender } = render(<ResilienceRing value={10} />);
  rerender(<ResilienceRing value={15} />);
  rerender(<ResilienceRing value={8} />);  // would decrement — must clamp to 15
  rerender(<ResilienceRing value={20} />);
  // After sequence [10, 15, 8, 20], displayed value must be 20
  // Check the label text (the big center number)
  expect(screen.getByText('20')).toBeInTheDocument();
  expect(screen.queryByText('8')).not.toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// Rule #9 — Latin digits regardless of locale
// ---------------------------------------------------------------------------

it('resilienceRing_day_count_renders_latin_in_fa_locale', () => {
  render(<ResilienceRing value={42} locale="fa" />);
  expect(screen.getByText('42')).toBeInTheDocument();
  // Ensure Arabic-Indic digits NOT rendered
  expect(screen.queryByText('۴۲')).not.toBeInTheDocument();
});

it('resilienceRing_day_count_renders_latin_in_ar_locale', () => {
  render(<ResilienceRing value={42} locale="ar" />);
  expect(screen.getByText('42')).toBeInTheDocument();
  expect(screen.queryByText('٤٢')).not.toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// Default render — value visible
// ---------------------------------------------------------------------------

describe('ResilienceRing — default render', () => {
  it('renders without throwing', () => {
    expect(() => render(<ResilienceRing value={7} />)).not.toThrow();
  });

  it('displays the day count label', () => {
    render(<ResilienceRing value={7} />);
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('displays "days" sublabel', () => {
    render(<ResilienceRing value={7} />);
    expect(screen.getByText('days')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// max prop — changes ring fill (verified via aria-label on the SVG wrapper)
// ---------------------------------------------------------------------------

describe('ResilienceRing — max prop', () => {
  it('renders with custom max without throwing', () => {
    expect(() => render(<ResilienceRing value={5} max={10} />)).not.toThrow();
  });

  it('renders correct label when value equals max', () => {
    render(<ResilienceRing value={10} max={10} />);
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('renders ProgressRing SVG circles for geometry (default max=30)', () => {
    const { container } = render(<ResilienceRing value={15} />);
    // ProgressRing renders an SVG with two circles (track + progress)
    const circles = container.querySelectorAll('circle');
    expect(circles.length).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// ariaLabel — forwarded to ProgressRing (which carries role="img")
// ---------------------------------------------------------------------------

describe('ResilienceRing — ariaLabel', () => {
  it('applies ariaLabel to the inner ProgressRing element', () => {
    const { container } = render(
      <ResilienceRing value={14} ariaLabel="14 resilience days" />,
    );
    // ResilienceRing root is a plain div wrapper; ProgressRing is its first child
    // and carries role="img" + aria-label
    const progressRingRoot = container.firstElementChild?.firstElementChild;
    expect(progressRingRoot?.getAttribute('aria-label')).toBe('14 resilience days');
  });

  it('ProgressRing child has role="img"', () => {
    const { container } = render(<ResilienceRing value={14} />);
    const progressRingRoot = container.firstElementChild?.firstElementChild;
    expect(progressRingRoot?.getAttribute('role')).toBe('img');
  });
});

// ---------------------------------------------------------------------------
// className — on root div
// ---------------------------------------------------------------------------

describe('ResilienceRing — className', () => {
  it('applies custom className to root', () => {
    const { container } = render(
      <ResilienceRing value={14} className="my-resilience-ring" />,
    );
    expect(container.firstElementChild?.className).toContain('my-resilience-ring');
  });
});

// ---------------------------------------------------------------------------
// axe accessibility
// ---------------------------------------------------------------------------

const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    region: { enabled: false },
  },
});

describe('ResilienceRing — axe accessibility', () => {
  it('default render has no a11y violations', async () => {
    render(<ResilienceRing value={14} ariaLabel="14 resilience days" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
