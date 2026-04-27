'use client';
/**
 * Contract tests for packages/design-system/src/primitives/BarChart.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets (9 cases):
 *  1.  Default render: SVG is in the DOM
 *  2.  Bars rendered: one <rect> per data item
 *  3.  Empty data: "No data" text visible, no SVG
 *  4.  ariaLabel on root element
 *  5.  SVG has aria-hidden="true"
 *  6.  className applied to root
 *  7.  color prop: at least one <rect> has fill equal to the color
 *  8.  yAxisLabel text appears in SVG
 *  9.  axe scan passes (color-contrast and region disabled)
 */

import type * as React from 'react';
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { BarChart } from '@disciplineos/design-system/primitives/BarChart';

expect.extend(toHaveNoViolations);

// axe instance — color-contrast disabled (jsdom has no computed styles)
const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    // region rule: BarChart is a standalone widget, not wrapped in a landmark in tests
    'region': { enabled: false },
  },
});

// Shared test data — weekly PHQ-9 scores Mon-Fri
const weekData = [
  { label: 'Mon', value: 8 },
  { label: 'Tue', value: 10 },
  { label: 'Wed', value: 7 },
  { label: 'Thu', value: 12 },
  { label: 'Fri', value: 9 },
];

// ---------------------------------------------------------------------------
// 1. Default render: SVG is in the DOM
// ---------------------------------------------------------------------------

describe('BarChart — default render', () => {
  it('renders an SVG element', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Weekly PHQ-9 scores" />,
    );
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 2. Bars rendered: one <rect> per data item
// ---------------------------------------------------------------------------

describe('BarChart — bars rendered', () => {
  it('renders one <rect> per data item', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Weekly scores" />,
    );
    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBe(weekData.length);
  });

  it('renders two rects for two data items', () => {
    const twoItems = [
      { label: 'Mon', value: 5 },
      { label: 'Tue', value: 10 },
    ];
    const { container } = render(
      <BarChart data={twoItems} ariaLabel="Two bars" />,
    );
    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// 3. Empty data: "No data" text visible, no SVG
// ---------------------------------------------------------------------------

describe('BarChart — empty data', () => {
  it('renders "No data" text when data is empty', () => {
    const { getByText } = render(
      <BarChart data={[]} ariaLabel="Empty chart" />,
    );
    expect(getByText('No data')).toBeTruthy();
  });

  it('does not render an SVG when data is empty', () => {
    const { container } = render(
      <BarChart data={[]} ariaLabel="Empty chart" />,
    );
    const svg = container.querySelector('svg');
    expect(svg).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 4. ariaLabel on root element
// ---------------------------------------------------------------------------

describe('BarChart — ariaLabel', () => {
  it('applies ariaLabel to the root div', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Weekly PHQ-9 trend" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('aria-label')).toBe('Weekly PHQ-9 trend');
  });

  it('root element has role="img"', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Test chart" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('role')).toBe('img');
  });

  it('does not set aria-label attribute when ariaLabel is omitted', () => {
    const { container } = render(<BarChart data={weekData} />);
    const root = container.firstElementChild;
    expect(root?.hasAttribute('aria-label')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 5. SVG has aria-hidden="true"
// ---------------------------------------------------------------------------

describe('BarChart — SVG aria-hidden', () => {
  it('sets aria-hidden="true" on the SVG element', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Hidden SVG test" />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('aria-hidden')).toBe('true');
  });
});

// ---------------------------------------------------------------------------
// 6. className applied to root
// ---------------------------------------------------------------------------

describe('BarChart — className', () => {
  it('applies a custom className to the root element', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Test" className="my-bar-chart" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('my-bar-chart')).toBe(true);
  });

  it('applies className to the empty state div', () => {
    const { container } = render(
      <BarChart data={[]} className="empty-bar-chart" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('empty-bar-chart')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 7. color prop: at least one <rect> has fill equal to the color
// ---------------------------------------------------------------------------

describe('BarChart — color prop', () => {
  it('sets fill to the custom color on bars', () => {
    const customColor = 'var(--color-accent-teal)';
    const { container } = render(
      <BarChart data={weekData} color={customColor} ariaLabel="Teal bars" />,
    );
    const rects = container.querySelectorAll('rect');
    const fillValues = Array.from(rects).map((r) => r.getAttribute('fill'));
    expect(fillValues.some((f) => f === customColor)).toBe(true);
  });

  it('uses per-datum color override when provided', () => {
    const dataWithColor = [
      { label: 'Mon', value: 8, color: 'red' },
      { label: 'Tue', value: 10 },
    ];
    const { container } = render(
      <BarChart data={dataWithColor} color="blue" ariaLabel="Mixed colors" />,
    );
    const rects = container.querySelectorAll('rect');
    const fills = Array.from(rects).map((r) => r.getAttribute('fill'));
    expect(fills).toContain('red');
    expect(fills).toContain('blue');
  });
});

// ---------------------------------------------------------------------------
// 8. yAxisLabel text appears in SVG
// ---------------------------------------------------------------------------

describe('BarChart — yAxisLabel', () => {
  it('renders yAxisLabel as a <text> element inside the SVG', () => {
    const { container } = render(
      <BarChart data={weekData} yAxisLabel="PHQ-9 Score" ariaLabel="Chart with label" />,
    );
    const textEls = container.querySelectorAll('svg text');
    const textContents = Array.from(textEls).map((el) => el.textContent);
    expect(textContents.some((t) => t === 'PHQ-9 Score')).toBe(true);
  });

  it('does not render an extra <text> for yAxisLabel when omitted', () => {
    const { container } = render(
      <BarChart data={weekData} ariaLabel="Chart without y label" />,
    );
    // AxisBottom renders tick labels but not a rotated y-axis label.
    // The rotated y-axis label contains transform="rotate(-90)".
    const allTexts = Array.from(container.querySelectorAll('svg text'));
    const rotatedLabels = allTexts.filter((el) =>
      (el.getAttribute('transform') ?? '').includes('rotate(-90)'),
    );
    expect(rotatedLabels.length).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// 9. axe scan passes
// ---------------------------------------------------------------------------

describe('BarChart — axe accessibility', () => {
  it('passes axe with default data', async () => {
    render(<BarChart data={weekData} ariaLabel="Weekly PHQ-9 scores" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with empty data', async () => {
    render(<BarChart data={[]} ariaLabel="No data chart" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with yAxisLabel', async () => {
    render(
      <BarChart
        data={weekData}
        yAxisLabel="Score"
        ariaLabel="PHQ-9 trend with y label"
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
