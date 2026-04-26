/**
 * Contract tests for packages/design-system/src/primitives/ProgressRing.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests (see packages/design-system/src/primitives/web.test.ts).
 *
 * Coverage targets:
 *   - Renders without throwing for value 0, 50, 100
 *   - Clamps value > max → treated as max; negative → 0
 *   - Geometry: r attribute = (size - strokeWidth) / 2
 *   - role="img" present; aria-label rendered when provided
 *   - Default color uses var(--color-accent-bronze)
 *   - Default trackColor uses var(--color-surface-tertiary)
 *   - label and sublabel render when provided
 *   - text-ink-primary used (not text-ink-900)
 *   - text-ink-tertiary used (not text-ink-500)
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ProgressRing } from '@disciplineos/design-system/primitives/ProgressRing';

// ---------------------------------------------------------------------------
// Basic rendering
// ---------------------------------------------------------------------------

describe('ProgressRing — basic rendering', () => {
  it('renders without throwing for value=0', () => {
    expect(() => render(<ProgressRing value={0} />)).not.toThrow();
  });

  it('renders without throwing for value=50', () => {
    expect(() => render(<ProgressRing value={50} />)).not.toThrow();
  });

  it('renders without throwing for value=100', () => {
    expect(() => render(<ProgressRing value={100} />)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Clamping
// ---------------------------------------------------------------------------

describe('ProgressRing — value clamping', () => {
  it('treats value > max as max (full ring, dashoffset=0)', () => {
    const { container } = render(<ProgressRing value={150} max={100} size={120} strokeWidth={10} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    // When clamped to max, pct = 1, dashoffset = circumference * (1 - 1) = 0
    expect(progressCircle?.getAttribute('stroke-dashoffset')).toBe('0');
  });

  it('treats negative value as 0 (empty ring, dashoffset=circumference)', () => {
    const { container } = render(<ProgressRing value={-10} max={100} size={120} strokeWidth={10} />);
    const radius = (120 - 10) / 2; // 55
    const circumference = 2 * Math.PI * radius;
    const progressCircle = container.querySelectorAll('circle')[1];
    // When value=0, pct=0, dashoffset = circumference * 1 = circumference
    expect(progressCircle?.getAttribute('stroke-dashoffset')).toBe(String(circumference));
  });
});

// ---------------------------------------------------------------------------
// Geometry
// ---------------------------------------------------------------------------

describe('ProgressRing — geometry', () => {
  it('r attribute = (size - strokeWidth) / 2 with defaults (size=120, strokeWidth=10 → r=55)', () => {
    const { container } = render(<ProgressRing value={50} />);
    const circles = container.querySelectorAll('circle');
    // Both circles share the same radius
    expect(circles[0]?.getAttribute('r')).toBe('55');
    expect(circles[1]?.getAttribute('r')).toBe('55');
  });

  it('r attribute respects custom size and strokeWidth', () => {
    const { container } = render(<ProgressRing value={50} size={200} strokeWidth={20} />);
    const expectedRadius = (200 - 20) / 2; // 90
    const circles = container.querySelectorAll('circle');
    expect(circles[0]?.getAttribute('r')).toBe(String(expectedRadius));
    expect(circles[1]?.getAttribute('r')).toBe(String(expectedRadius));
  });

  it('strokeDasharray on progress circle equals circumference', () => {
    const size = 120;
    const strokeWidth = 10;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const { container } = render(<ProgressRing value={50} size={size} strokeWidth={strokeWidth} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle?.getAttribute('stroke-dasharray')).toBe(String(circumference));
  });

  it('dashoffset at value=50 max=100 is half the circumference', () => {
    const size = 120;
    const strokeWidth = 10;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const expectedOffset = circumference * 0.5; // pct=0.5, offset = circ*(1-0.5)
    const { container } = render(<ProgressRing value={50} max={100} size={size} strokeWidth={strokeWidth} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle?.getAttribute('stroke-dashoffset')).toBe(String(expectedOffset));
  });

  it('handles max=0 without division by zero (empty ring)', () => {
    const size = 120;
    const strokeWidth = 10;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const { container } = render(<ProgressRing value={0} max={0} size={size} strokeWidth={strokeWidth} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    // pct = 0 when max === 0, so dashoffset = circumference
    expect(progressCircle?.getAttribute('stroke-dashoffset')).toBe(String(circumference));
  });
});

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

describe('ProgressRing — accessibility', () => {
  it('has role="img" on the wrapper element', () => {
    const { container } = render(<ProgressRing value={50} />);
    expect(container.firstElementChild?.getAttribute('role')).toBe('img');
  });

  it('renders aria-label when provided', () => {
    const { container } = render(<ProgressRing value={50} ariaLabel="Progress: 50%" />);
    expect(container.firstElementChild?.getAttribute('aria-label')).toBe('Progress: 50%');
  });

  it('does not render aria-label attribute when omitted', () => {
    const { container } = render(<ProgressRing value={50} />);
    expect(container.firstElementChild?.hasAttribute('aria-label')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Token defaults — Quiet Strength
// ---------------------------------------------------------------------------

describe('ProgressRing — default color tokens (Quiet Strength)', () => {
  it('default color prop uses var(--color-accent-bronze), not var(--color-brand-500)', () => {
    const { container } = render(<ProgressRing value={50} />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle?.getAttribute('stroke')).toBe('var(--color-accent-bronze)');
    expect(progressCircle?.getAttribute('stroke')).not.toBe('var(--color-brand-500)');
  });

  it('default trackColor prop uses var(--color-surface-tertiary), not var(--color-surface-200)', () => {
    const { container } = render(<ProgressRing value={50} />);
    const trackCircle = container.querySelectorAll('circle')[0];
    expect(trackCircle?.getAttribute('stroke')).toBe('var(--color-surface-tertiary)');
    expect(trackCircle?.getAttribute('stroke')).not.toBe('var(--color-surface-200)');
  });

  it('accepts custom color override (prop API preserved)', () => {
    const { container } = render(<ProgressRing value={50} color="var(--color-signal-crisis)" />);
    const progressCircle = container.querySelectorAll('circle')[1];
    expect(progressCircle?.getAttribute('stroke')).toBe('var(--color-signal-crisis)');
  });

  it('accepts custom trackColor override (prop API preserved)', () => {
    const { container } = render(<ProgressRing value={50} trackColor="#e5e7eb" />);
    const trackCircle = container.querySelectorAll('circle')[0];
    expect(trackCircle?.getAttribute('stroke')).toBe('#e5e7eb');
  });
});

// ---------------------------------------------------------------------------
// label and sublabel
// ---------------------------------------------------------------------------

describe('ProgressRing — label and sublabel', () => {
  it('renders label when provided', () => {
    const { getByText } = render(<ProgressRing value={50} label="50%" />);
    expect(getByText('50%')).toBeTruthy();
  });

  it('renders sublabel when provided', () => {
    const { getByText } = render(<ProgressRing value={50} sublabel="of daily goal" />);
    expect(getByText('of daily goal')).toBeTruthy();
  });

  it('renders both label and sublabel simultaneously', () => {
    const { getByText } = render(
      <ProgressRing value={75} label="75%" sublabel="sessions complete" />,
    );
    expect(getByText('75%')).toBeTruthy();
    expect(getByText('sessions complete')).toBeTruthy();
  });

  it('does not render label container when neither label nor sublabel is provided', () => {
    const { container } = render(<ProgressRing value={50} />);
    // No text-center div should exist
    const textCenter = container.querySelector('.text-center');
    expect(textCenter).toBeNull();
  });

  it('applies text-ink-primary to label (not text-ink-900)', () => {
    const { container } = render(<ProgressRing value={50} label="Label" />);
    const labelEl = container.querySelector('.text-ink-primary');
    expect(labelEl).not.toBeNull();
    const noOldToken = container.querySelector('.text-ink-900');
    expect(noOldToken).toBeNull();
  });

  it('applies text-ink-tertiary to sublabel (not text-ink-500)', () => {
    const { container } = render(<ProgressRing value={50} sublabel="Sublabel" />);
    const sublabelEl = container.querySelector('.text-ink-tertiary');
    expect(sublabelEl).not.toBeNull();
    const noOldToken = container.querySelector('.text-ink-500');
    expect(noOldToken).toBeNull();
  });

  it('renders React node as label (JSX child)', () => {
    const { getByText } = render(
      <ProgressRing value={50} label={<strong>Bold Label</strong>} />,
    );
    expect(getByText('Bold Label')).toBeTruthy();
  });
});
