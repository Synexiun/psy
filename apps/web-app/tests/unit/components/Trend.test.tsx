/**
 * Contract tests for packages/design-system/src/primitives/Trend.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets (15 cases):
 *  1.  Default render: value and label are visible
 *  2.  Sparkline SVG is rendered when data has >= 2 points
 *  3.  Sparkline absent (no <svg>) when data has fewer than 2 points
 *  4.  Positive delta → text-signal-stable class present in DOM
 *  5.  Negative delta → text-signal-warning class present in DOM
 *  6.  deltaLabel text appears in output
 *  7.  clinical=true → hero number has direction: ltr inline style
 *  8.  clinical=true without formatValue → console.warn fires with [Trend] prefix
 *  9.  clinical=true with formatValue → no warn fires
 * 10.  formatValue callback is called with the value
 * 11.  Custom className applied to root element
 * 12.  color prop forwarded to Sparkline (check SVG stroke attribute)
 * 13.  sparklineAriaLabel forwarded to Sparkline (check aria-label on <svg>)
 * 14.  No delta row when delta is undefined
 * 15.  axe: no violations (color-contrast + region rules disabled)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { Trend } from '@disciplineos/design-system/primitives/Trend';

expect.extend(toHaveNoViolations);

// axe instance — color-contrast disabled (jsdom has no computed styles)
// region disabled — Trend is a standalone widget, not wrapped in a landmark in tests
const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    'region': { enabled: false },
  },
});

const SAMPLE_DATA = [10, 15, 12, 18, 14, 20];

// ---------------------------------------------------------------------------
// 1. Default render: value and label visible
// ---------------------------------------------------------------------------

describe('Trend — default render', () => {
  it('displays the numeric value', () => {
    const { getByText } = render(
      <Trend value={20} label="Sessions" data={SAMPLE_DATA} />,
    );
    expect(getByText('20')).toBeTruthy();
  });

  it('displays the label', () => {
    const { getByText } = render(
      <Trend value={20} label="Sessions" data={SAMPLE_DATA} />,
    );
    expect(getByText('Sessions')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 2. Sparkline SVG rendered when data.length >= 2
// ---------------------------------------------------------------------------

describe('Trend — sparkline present with sufficient data', () => {
  it('renders an <svg> element when data has 2 or more points', () => {
    const { container } = render(
      <Trend value={20} label="Sessions" data={SAMPLE_DATA} />,
    );
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
  });

  it('renders an <svg> with exactly 2 data points (minimum)', () => {
    const { container } = render(
      <Trend value={9} label="Minimal" data={[3, 9]} />,
    );
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 3. Sparkline absent when data.length < 2
// ---------------------------------------------------------------------------

describe('Trend — sparkline absent with insufficient data', () => {
  it('renders no <svg> when data is empty', () => {
    const { container } = render(
      <Trend value={5} label="Score" data={[]} />,
    );
    expect(container.querySelector('svg')).toBeNull();
  });

  it('renders no <svg> when data has only 1 point', () => {
    const { container } = render(
      <Trend value={5} label="Score" data={[5]} />,
    );
    expect(container.querySelector('svg')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 4. Positive delta → text-signal-stable
// ---------------------------------------------------------------------------

describe('Trend — positive delta', () => {
  it('applies text-signal-stable class for delta > 0', () => {
    const { container } = render(
      <Trend value={20} label="Sessions" data={SAMPLE_DATA} delta={5} />,
    );
    expect(container.querySelector('.text-signal-stable')).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 5. Negative delta → text-signal-warning
// ---------------------------------------------------------------------------

describe('Trend — negative delta', () => {
  it('applies text-signal-warning class for delta < 0', () => {
    const { container } = render(
      <Trend value={10} label="PHQ-9 Score" data={SAMPLE_DATA} delta={-3} />,
    );
    expect(container.querySelector('.text-signal-warning')).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 6. deltaLabel appears in output
// ---------------------------------------------------------------------------

describe('Trend — deltaLabel', () => {
  it('renders the deltaLabel text when provided', () => {
    const { getByText } = render(
      <Trend
        value={20}
        label="Sessions"
        data={SAMPLE_DATA}
        delta={5}
        deltaLabel="vs last week"
      />,
    );
    expect(getByText(/vs last week/)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 7. clinical=true → hero number has direction: ltr
// ---------------------------------------------------------------------------

describe('Trend — clinical ltr enforcement', () => {
  it('sets direction: ltr on the number span when clinical=true', () => {
    const { container } = render(
      <Trend
        value={14}
        label="PHQ-9 Score"
        data={SAMPLE_DATA}
        clinical={true}
        formatValue={(n) => n.toString()}
      />,
    );
    const numberSpan = container.querySelector('span');
    expect(numberSpan).not.toBeNull();
    expect(numberSpan?.style.direction).toBe('ltr');
  });
});

// ---------------------------------------------------------------------------
// 8. clinical=true without formatValue → console.warn fires with [Trend] prefix
// ---------------------------------------------------------------------------

describe('Trend — clinical warning', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('calls console.warn with [Trend] prefix when clinical=true and formatValue is missing', () => {
    render(
      <Trend value={14} label="PHQ-9 Score" data={SAMPLE_DATA} clinical={true} />,
    );
    // Trend fires its own warn; Stat also fires one — we check the first call contains [Trend]
    const calls = warnSpy.mock.calls;
    const trendCall = calls.find((c) => typeof c[0] === 'string' && (c[0] as string).includes('[Trend]'));
    expect(trendCall).toBeDefined();
    expect(trendCall?.[0]).toContain('[Trend]');
  });

  // ---------------------------------------------------------------------------
  // 9. clinical=true with formatValue → no [Trend] warn fires
  // ---------------------------------------------------------------------------

  it('does not fire a [Trend] warn when clinical=true and formatValue IS provided', () => {
    render(
      <Trend
        value={14}
        label="PHQ-9 Score"
        data={SAMPLE_DATA}
        clinical={true}
        formatValue={(n) => n.toString()}
      />,
    );
    const trendCall = warnSpy.mock.calls.find(
      (c) => typeof c[0] === 'string' && (c[0] as string).includes('[Trend]'),
    );
    expect(trendCall).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// 10. formatValue callback is called with the value
// ---------------------------------------------------------------------------

describe('Trend — formatValue callback', () => {
  it('calls formatValue with the exact value prop and renders the result', () => {
    const mockFormat = vi.fn((n: number) => `FMT_${n}`);
    const { getByText } = render(
      <Trend
        value={99}
        label="Score"
        data={SAMPLE_DATA}
        clinical={true}
        formatValue={mockFormat}
      />,
    );
    expect(mockFormat).toHaveBeenCalledWith(99);
    expect(getByText('FMT_99')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 11. Custom className applied to root element
// ---------------------------------------------------------------------------

describe('Trend — custom className', () => {
  it('applies a custom className to the root container', () => {
    const { container } = render(
      <Trend
        value={20}
        label="Sessions"
        data={SAMPLE_DATA}
        className="my-custom-trend"
      />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('my-custom-trend')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 12. color prop forwarded to Sparkline (check SVG stroke attribute)
// ---------------------------------------------------------------------------

describe('Trend — color forwarded to Sparkline', () => {
  it('passes the color prop to the sparkline SVG stroke', () => {
    const customColor = 'hsl(200, 70%, 50%)';
    const { container } = render(
      <Trend
        value={20}
        label="Sessions"
        data={SAMPLE_DATA}
        color={customColor}
      />,
    );
    // LinePath renders a <path> with the stroke attribute set to the color
    const strokeEl = container.querySelector(`[stroke="${customColor}"]`);
    expect(strokeEl).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 13. sparklineAriaLabel forwarded to Sparkline SVG
// ---------------------------------------------------------------------------

describe('Trend — sparklineAriaLabel forwarded', () => {
  it('sets aria-label on the <svg> element', () => {
    const { container } = render(
      <Trend
        value={20}
        label="Sessions"
        data={SAMPLE_DATA}
        sparklineAriaLabel="Sessions trend over 6 weeks"
      />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('aria-label')).toBe('Sessions trend over 6 weeks');
  });
});

// ---------------------------------------------------------------------------
// 14. No delta row when delta is undefined
// ---------------------------------------------------------------------------

describe('Trend — no delta when delta is undefined', () => {
  it('does not render signal-stable or signal-warning when delta is omitted', () => {
    const { container } = render(
      <Trend value={20} label="Sessions" data={SAMPLE_DATA} />,
    );
    expect(container.querySelector('.text-signal-stable')).toBeNull();
    expect(container.querySelector('.text-signal-warning')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 15. axe accessibility
// ---------------------------------------------------------------------------

describe('Trend — axe accessibility', () => {
  it('passes axe with default props', async () => {
    render(
      <Trend
        value={20}
        label="Sessions"
        data={SAMPLE_DATA}
        sparklineAriaLabel="Sessions trend over 6 weeks"
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with delta and sparklineAriaLabel', async () => {
    render(
      <Trend
        value={20}
        label="Sessions"
        data={SAMPLE_DATA}
        delta={5}
        deltaLabel="vs last week"
        sparklineAriaLabel="Sessions trend over 6 weeks"
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with clinical=true and formatValue', async () => {
    render(
      <Trend
        value={14}
        label="PHQ-9 Score"
        data={SAMPLE_DATA}
        clinical={true}
        formatValue={(n) => n.toString()}
        sparklineAriaLabel="PHQ-9 trend over 6 assessments"
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
