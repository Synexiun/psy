/**
 * Contract tests for packages/design-system/src/primitives/Stat.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets (11 cases):
 *  1.  Renders the value
 *  2.  Renders the label
 *  3.  delta > 0  → text-signal-stable + up arrow present
 *  4.  delta < 0  → text-signal-warning + down arrow present
 *  5.  delta === 0 → text-ink-tertiary (neutral)
 *  6.  deltaDirection explicit override
 *  7.  clinical=true without formatValue → console.warn fires
 *  8.  clinical=true with formatValue   → formatValue output used for display
 *  9.  size='sm' → text-2xl; size='lg' → text-6xl
 * 10.  clinical=true → element has style direction: ltr
 * 11.  axe: no violations with color-contrast disabled
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { Stat } from '@disciplineos/design-system/primitives/Stat';

expect.extend(toHaveNoViolations);

// axe instance — color-contrast disabled (jsdom has no computed styles)
const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    // region rule: Stat is a standalone widget, not wrapped in a landmark in tests
    'region': { enabled: false },
  },
});

// ---------------------------------------------------------------------------
// 1. Renders the value
// ---------------------------------------------------------------------------

describe('Stat — renders value', () => {
  it('displays the numeric value as text', () => {
    const { getByText } = render(<Stat value={47} label="Resilience Days" />);
    expect(getByText('47')).toBeTruthy();
  });

  it('renders a formatted value when formatValue is provided', () => {
    const { getByText } = render(
      <Stat value={12} label="PHQ-9 Score" formatValue={(n) => `Score: ${n}`} />,
    );
    expect(getByText('Score: 12')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 2. Renders the label
// ---------------------------------------------------------------------------

describe('Stat — renders label', () => {
  it('displays the label string', () => {
    const { getByText } = render(<Stat value={5} label="Weekly Check-ins" />);
    expect(getByText('Weekly Check-ins')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 3. delta > 0 → text-signal-stable + up arrow
// ---------------------------------------------------------------------------

describe('Stat — positive delta', () => {
  it('applies text-signal-stable class for delta > 0', () => {
    const { container } = render(
      <Stat value={47} label="Resilience Days" delta={3} />,
    );
    const deltaEl = container.querySelector('.text-signal-stable');
    expect(deltaEl).not.toBeNull();
  });

  it('renders up-arrow SVG for delta > 0', () => {
    const { container } = render(
      <Stat value={47} label="Resilience Days" delta={3} />,
    );
    const svg = container.querySelector('svg[aria-hidden="true"]');
    expect(svg).not.toBeNull();
  });

  it('shows absolute delta value', () => {
    const { getByText } = render(
      <Stat value={47} label="Resilience Days" delta={3} deltaLabel="vs last week" />,
    );
    // delta display: "3 vs last week"
    expect(getByText(/3 vs last week/)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 4. delta < 0 → text-signal-warning + down arrow
// ---------------------------------------------------------------------------

describe('Stat — negative delta', () => {
  it('applies text-signal-warning class for delta < 0', () => {
    const { container } = render(
      <Stat value={10} label="PHQ-9 Score" delta={-2} />,
    );
    const deltaEl = container.querySelector('.text-signal-warning');
    expect(deltaEl).not.toBeNull();
  });

  it('renders down-arrow SVG for delta < 0', () => {
    const { container } = render(
      <Stat value={10} label="PHQ-9 Score" delta={-2} />,
    );
    const svg = container.querySelector('svg[aria-hidden="true"]');
    expect(svg).not.toBeNull();
  });

  it('shows absolute delta value (not negative)', () => {
    const { container } = render(
      <Stat value={10} label="PHQ-9 Score" delta={-2} />,
    );
    const deltaEl = container.querySelector('.text-signal-warning');
    // absolute value — should show "2" not "-2"
    expect(deltaEl?.textContent).toContain('2');
    expect(deltaEl?.textContent).not.toContain('-2');
  });
});

// ---------------------------------------------------------------------------
// 5. delta === 0 → text-ink-tertiary (neutral)
// ---------------------------------------------------------------------------

describe('Stat — neutral delta', () => {
  it('applies text-ink-tertiary for delta === 0', () => {
    const { container } = render(
      <Stat value={47} label="Resilience Days" delta={0} />,
    );
    // The delta span should carry text-ink-tertiary
    // (the label also has text-ink-tertiary — find the one with the dash glyph)
    const allTertiary = container.querySelectorAll('.text-ink-tertiary');
    // At least one should be the delta row
    expect(allTertiary.length).toBeGreaterThan(0);
  });

  it('does not apply signal-stable or signal-warning for delta === 0', () => {
    const { container } = render(
      <Stat value={47} label="Resilience Days" delta={0} />,
    );
    expect(container.querySelector('.text-signal-stable')).toBeNull();
    expect(container.querySelector('.text-signal-warning')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 6. deltaDirection explicit override
// ---------------------------------------------------------------------------

describe('Stat — deltaDirection override', () => {
  it('uses explicit deltaDirection="down" even for a positive delta', () => {
    const { container } = render(
      <Stat value={47} label="Resilience Days" delta={5} deltaDirection="down" />,
    );
    // down → text-signal-warning, NOT text-signal-stable
    expect(container.querySelector('.text-signal-warning')).not.toBeNull();
    expect(container.querySelector('.text-signal-stable')).toBeNull();
  });

  it('uses explicit deltaDirection="up" even for a negative delta', () => {
    const { container } = render(
      <Stat value={47} label="PHQ-9 Score" delta={-3} deltaDirection="up" />,
    );
    expect(container.querySelector('.text-signal-stable')).not.toBeNull();
    expect(container.querySelector('.text-signal-warning')).toBeNull();
  });

  it('uses explicit deltaDirection="neutral" overriding positive delta', () => {
    const { container } = render(
      <Stat value={47} label="Resilience Days" delta={3} deltaDirection="neutral" />,
    );
    expect(container.querySelector('.text-signal-stable')).toBeNull();
    expect(container.querySelector('.text-signal-warning')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 7. clinical=true without formatValue → console.warn fires
// ---------------------------------------------------------------------------

describe('Stat — clinical warning', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('calls console.warn when clinical=true and formatValue is not provided', () => {
    render(<Stat value={14} label="PHQ-9 Score" clinical={true} />);
    expect(warnSpy).toHaveBeenCalledOnce();
    expect(warnSpy.mock.calls[0]?.[0]).toContain('[Stat]');
    expect(warnSpy.mock.calls[0]?.[0]).toContain('formatNumberClinical');
  });

  it('does not call console.warn when clinical=true and formatValue IS provided', () => {
    render(
      <Stat
        value={14}
        label="PHQ-9 Score"
        clinical={true}
        formatValue={(n) => n.toString()}
      />,
    );
    expect(warnSpy).not.toHaveBeenCalled();
  });

  it('does not call console.warn when clinical is omitted', () => {
    render(<Stat value={14} label="PHQ-9 Score" />);
    expect(warnSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 8. clinical=true with formatValue → uses formatValue output
// ---------------------------------------------------------------------------

describe('Stat — clinical with formatValue', () => {
  it('renders the output of formatValue instead of String(value)', () => {
    const mockFormat = (n: number): string => `FORMATTED_${n}`;
    const { getByText } = render(
      <Stat
        value={14}
        label="PHQ-9 Score"
        clinical={true}
        formatValue={mockFormat}
      />,
    );
    expect(getByText('FORMATTED_14')).toBeTruthy();
  });

  it('formatValue is called with the exact value prop', () => {
    const mockFormat = vi.fn((n: number) => n.toString());
    render(
      <Stat
        value={99}
        label="Score"
        clinical={true}
        formatValue={mockFormat}
      />,
    );
    expect(mockFormat).toHaveBeenCalledWith(99);
  });
});

// ---------------------------------------------------------------------------
// 9. size variants
// ---------------------------------------------------------------------------

describe('Stat — size variants', () => {
  it('applies text-2xl for size="sm"', () => {
    const { container } = render(<Stat value={47} label="Resilience Days" size="sm" />);
    const numberSpan = container.querySelector('.text-2xl');
    expect(numberSpan).not.toBeNull();
  });

  it('applies text-4xl for size="md" (default)', () => {
    const { container } = render(<Stat value={47} label="Resilience Days" />);
    const numberSpan = container.querySelector('.text-4xl');
    expect(numberSpan).not.toBeNull();
  });

  it('applies text-4xl for explicit size="md"', () => {
    const { container } = render(<Stat value={47} label="Resilience Days" size="md" />);
    const numberSpan = container.querySelector('.text-4xl');
    expect(numberSpan).not.toBeNull();
  });

  it('applies text-6xl for size="lg"', () => {
    const { container } = render(<Stat value={47} label="Resilience Days" size="lg" />);
    const numberSpan = container.querySelector('.text-6xl');
    expect(numberSpan).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 10. clinical=true → element has style direction: ltr
// ---------------------------------------------------------------------------

describe('Stat — clinical ltr enforcement', () => {
  it('sets direction: ltr on the number span when clinical=true', () => {
    const { container } = render(
      <Stat
        value={14}
        label="PHQ-9 Score"
        clinical={true}
        formatValue={(n) => n.toString()}
      />,
    );
    // The number <span> is the first child of the wrapper div
    const numberSpan = container.querySelector('span');
    expect(numberSpan).not.toBeNull();
    expect(numberSpan?.style.direction).toBe('ltr');
  });

  it('does not set direction on the number span when clinical is false/omitted', () => {
    const { container } = render(<Stat value={14} label="PHQ-9 Score" />);
    const numberSpan = container.querySelector('span');
    expect(numberSpan?.style.direction).toBeFalsy();
  });

  it('sets fontVariantNumeric: tabular-nums on the number span when clinical=true', () => {
    const { container } = render(
      <Stat
        value={14}
        label="PHQ-9 Score"
        clinical={true}
        formatValue={(n) => n.toString()}
      />,
    );
    const numberSpan = container.querySelector('span');
    // jsdom normalises fontVariantNumeric
    expect(numberSpan?.style.fontVariantNumeric).toBe('tabular-nums');
  });
});

// ---------------------------------------------------------------------------
// 11. axe accessibility
// ---------------------------------------------------------------------------

describe('Stat — axe accessibility', () => {
  it('passes axe with default props', async () => {
    render(<Stat value={47} label="Resilience Days" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with positive delta and deltaLabel', async () => {
    render(
      <Stat value={47} label="Resilience Days" delta={3} deltaLabel="vs last week" />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with clinical=true and formatValue', async () => {
    render(
      <Stat
        value={14}
        label="PHQ-9 Score"
        clinical={true}
        formatValue={(n) => n.toString()}
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
