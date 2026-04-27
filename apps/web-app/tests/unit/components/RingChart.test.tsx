'use client';
/**
 * Contract tests for packages/design-system/src/primitives/RingChart.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets (11 cases):
 *  1.  Default render: SVG is in the DOM
 *  2.  Single segment renders one progress circle (plus track circle)
 *  3.  Two segments render two progress circles
 *  4.  centerContent renders inside the ring
 *  5.  Empty segments (total = 0): only track ring, no segment circles
 *  6.  ariaLabel is present on the root element
 *  7.  SVG has aria-hidden="true"
 *  8.  axe scan passes (no violations)
 *  9.  size prop changes SVG width/height
 * 10.  strokeWidth prop affects circle r attribute
 * 11.  Custom className applied to root
 */

import type * as React from 'react';
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { RingChart } from '@disciplineos/design-system/primitives/RingChart';

expect.extend(toHaveNoViolations);

// axe instance — color-contrast disabled (jsdom has no computed styles)
const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    // region rule: RingChart is a standalone widget, not wrapped in a landmark in tests
    'region': { enabled: false },
  },
});

// Shared test segments
const twoSegments = [
  { id: 'mood', value: 60, color: 'var(--color-accent-teal)', label: 'Calm mood' },
  { id: 'urge', value: 40, color: 'var(--color-accent-amber)', label: 'Urge present' },
];

const oneSegment = [
  { id: 'phq', value: 100, color: 'var(--color-accent-bronze)', label: 'PHQ-9 total' },
];

// ---------------------------------------------------------------------------
// 1. Default render — SVG is in the DOM
// ---------------------------------------------------------------------------

describe('RingChart — default render', () => {
  it('renders an SVG element', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="Mood distribution" />,
    );
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 2. Single segment renders one progress circle (plus track circle)
// ---------------------------------------------------------------------------

describe('RingChart — single segment', () => {
  it('renders two circle elements: one track + one segment', () => {
    const { container } = render(
      <RingChart segments={oneSegment} ariaLabel="PHQ score" />,
    );
    const circles = container.querySelectorAll('circle');
    // 1 track + 1 segment = 2 total
    expect(circles).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// 3. Two segments render two progress circles (plus track)
// ---------------------------------------------------------------------------

describe('RingChart — two segments', () => {
  it('renders three circle elements: one track + two segments', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="Distribution" />,
    );
    const circles = container.querySelectorAll('circle');
    // 1 track + 2 segments = 3 total
    expect(circles).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------
// 4. centerContent renders inside the ring
// ---------------------------------------------------------------------------

describe('RingChart — centerContent', () => {
  it('renders centerContent text inside the ring wrapper', () => {
    const { getByText } = render(
      <RingChart
        segments={twoSegments}
        centerContent={<span>42%</span>}
        ariaLabel="Distribution with center"
      />,
    );
    expect(getByText('42%')).toBeTruthy();
  });

  it('does not render a center wrapper div when centerContent is undefined', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="No center" />,
    );
    // The absolute center div should not be present
    const absoluteDivs = container.querySelectorAll('.absolute');
    expect(absoluteDivs).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// 5. Empty segments (total = 0) — only track ring rendered, no segment circles
// ---------------------------------------------------------------------------

describe('RingChart — empty segments', () => {
  it('renders only the track circle when segments array is empty', () => {
    const { container } = render(
      <RingChart segments={[]} ariaLabel="Empty chart" />,
    );
    const circles = container.querySelectorAll('circle');
    // Only the track circle
    expect(circles).toHaveLength(1);
  });

  it('renders only the track circle when all segment values are zero', () => {
    const zeroSegments = [
      { id: 'a', value: 0, color: 'red', label: 'Zero A' },
      { id: 'b', value: 0, color: 'blue', label: 'Zero B' },
    ];
    const { container } = render(
      <RingChart segments={zeroSegments} ariaLabel="Zero total chart" />,
    );
    const circles = container.querySelectorAll('circle');
    // total === 0, so no segment circles
    expect(circles).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// 6. ariaLabel is present on the root element
// ---------------------------------------------------------------------------

describe('RingChart — ariaLabel', () => {
  it('applies ariaLabel to the root div', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="Weekly mood distribution" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('aria-label')).toBe('Weekly mood distribution');
  });

  it('root element has role="img"', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="Test ring" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('role')).toBe('img');
  });
});

// ---------------------------------------------------------------------------
// 7. SVG has aria-hidden="true"
// ---------------------------------------------------------------------------

describe('RingChart — SVG aria-hidden', () => {
  it('sets aria-hidden="true" on the SVG element', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="Hidden SVG test" />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('aria-hidden')).toBe('true');
  });
});

// ---------------------------------------------------------------------------
// 8. axe scan passes
// ---------------------------------------------------------------------------

describe('RingChart — axe accessibility', () => {
  it('passes axe with two segments', async () => {
    render(<RingChart segments={twoSegments} ariaLabel="Mood distribution ring" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with empty segments', async () => {
    render(<RingChart segments={[]} ariaLabel="Empty distribution ring" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with centerContent', async () => {
    render(
      <RingChart
        segments={twoSegments}
        centerContent={<span>42%</span>}
        ariaLabel="Ring with center label"
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});

// ---------------------------------------------------------------------------
// 9. size prop changes SVG width/height
// ---------------------------------------------------------------------------

describe('RingChart — size prop', () => {
  it('sets SVG width and height to the size prop value', () => {
    const { container } = render(
      <RingChart segments={twoSegments} size={200} ariaLabel="Large ring" />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('200');
    expect(svg?.getAttribute('height')).toBe('200');
  });

  it('defaults SVG width and height to 120 when size is omitted', () => {
    const { container } = render(
      <RingChart segments={twoSegments} ariaLabel="Default size ring" />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('120');
    expect(svg?.getAttribute('height')).toBe('120');
  });
});

// ---------------------------------------------------------------------------
// 10. strokeWidth prop affects circle r attribute (radius = (size - strokeWidth) / 2)
// ---------------------------------------------------------------------------

describe('RingChart — strokeWidth affects radius', () => {
  it('computes correct radius: (size - strokeWidth) / 2', () => {
    const size = 120;
    const strokeWidth = 20;
    const expectedRadius = (size - strokeWidth) / 2; // 50

    const { container } = render(
      <RingChart
        segments={oneSegment}
        size={size}
        strokeWidth={strokeWidth}
        ariaLabel="Custom strokeWidth ring"
      />,
    );
    // Track circle (first circle) should have r = expectedRadius
    const trackCircle = container.querySelector('circle');
    expect(trackCircle?.getAttribute('r')).toBe(String(expectedRadius));
  });

  it('default strokeWidth=10 gives radius=55 for size=120', () => {
    const { container } = render(
      <RingChart segments={oneSegment} ariaLabel="Default stroke ring" />,
    );
    const trackCircle = container.querySelector('circle');
    expect(trackCircle?.getAttribute('r')).toBe('55');
  });
});

// ---------------------------------------------------------------------------
// 11. Custom className applied to root
// ---------------------------------------------------------------------------

describe('RingChart — custom className', () => {
  it('applies a custom className to the root container element', () => {
    const { container } = render(
      <RingChart
        segments={twoSegments}
        className="my-custom-ring"
        ariaLabel="Custom class ring"
      />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('my-custom-ring')).toBe(true);
  });
});
