'use client';
/**
 * Contract tests for packages/design-system/src/clinical/UrgeSlider.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here.
 *
 * Rules under test:
 *   Rule #9 — Latin digits for clinical scores regardless of locale
 *   RTL     — dir="rtl" forwarded so Radix Slider mirrors thumb drag direction
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — slider is a form control, not a landmark region
 */

import type * as React from 'react';
import { beforeAll, describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { UrgeSlider } from '@disciplineos/design-system/clinical/UrgeSlider';

// ---------------------------------------------------------------------------
// jsdom does not implement ResizeObserver; Radix Slider uses it internally.
// Stub it here so all tests in this file can render the Slider without error.
// ---------------------------------------------------------------------------

beforeAll(() => {
  if (typeof window !== 'undefined' && !('ResizeObserver' in window)) {
    (window as Window & { ResizeObserver: unknown }).ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }
});

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Rule #9 — Latin digits regardless of locale
// ---------------------------------------------------------------------------

it('urgeSlider_value_renders_latin_in_arabic_context', () => {
  render(<UrgeSlider value={7} onValueChange={() => {}} locale="ar" dir="rtl" />);
  const label = screen.getByTestId('urge-value');
  expect(label.textContent).toBe('7');
  // Ensure Eastern Arabic digit NOT rendered
  expect(label.textContent).not.toBe('٧');
});

it('urgeSlider_value_renders_latin_in_persian_context', () => {
  render(<UrgeSlider value={7} onValueChange={() => {}} locale="fa" dir="rtl" />);
  const label = screen.getByTestId('urge-value');
  expect(label.textContent).toBe('7');
  expect(label.textContent).not.toBe('۷');
});

// ---------------------------------------------------------------------------
// RTL — dir forwarded to Slider/Radix so thumb drag direction inverts
// ---------------------------------------------------------------------------

it('urgeSlider_thumb_drag_direction_inverts_in_rtl', () => {
  // In RTL mode, the Slider (Radix) renders with dir="rtl".
  // We verify that the dir attribute is forwarded to the Slider root.
  const { container } = render(
    <UrgeSlider value={5} onValueChange={() => {}} dir="rtl" />,
  );
  // The Radix Slider root or its wrapper must carry dir="rtl"
  const rtlEl = container.querySelector('[dir="rtl"]');
  expect(rtlEl).not.toBeNull();
});

// ---------------------------------------------------------------------------
// Default render — value label visible
// ---------------------------------------------------------------------------

describe('UrgeSlider — default render', () => {
  it('renders without throwing', () => {
    expect(() =>
      render(<UrgeSlider value={5} onValueChange={() => {}} />),
    ).not.toThrow();
  });

  it('displays the current value label via data-testid', () => {
    render(<UrgeSlider value={3} onValueChange={() => {}} />);
    const label = screen.getByTestId('urge-value');
    expect(label.textContent).toBe('3');
  });

  it('displays boundary labels 0 and 10', () => {
    render(<UrgeSlider value={5} onValueChange={() => {}} />);
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// disabled prop
// ---------------------------------------------------------------------------

describe('UrgeSlider — disabled', () => {
  it('forwards disabled to the Slider (thumb becomes disabled)', () => {
    const { container } = render(
      <UrgeSlider value={5} onValueChange={() => {}} disabled />,
    );
    // Radix Slider sets data-disabled on the thumb when disabled
    const thumb = container.querySelector('[role="slider"]');
    // Either data-disabled attribute is present or the element has disabled attribute
    const isDisabled =
      thumb?.hasAttribute('data-disabled') ||
      thumb?.hasAttribute('disabled') ||
      thumb?.getAttribute('aria-disabled') === 'true';
    expect(isDisabled).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// ariaLabel — forwarded to Slider thumb
// ---------------------------------------------------------------------------

describe('UrgeSlider — ariaLabel', () => {
  it('applies custom ariaLabel to the slider thumb', () => {
    const { container } = render(
      <UrgeSlider value={5} onValueChange={() => {}} ariaLabel="Current urge level" />,
    );
    const thumb = container.querySelector('[role="slider"]');
    expect(thumb?.getAttribute('aria-label')).toBe('Current urge level');
  });

  it('uses default ariaLabel "Urge intensity" when omitted', () => {
    const { container } = render(<UrgeSlider value={5} onValueChange={() => {}} />);
    const thumb = container.querySelector('[role="slider"]');
    expect(thumb?.getAttribute('aria-label')).toBe('Urge intensity');
  });
});

// ---------------------------------------------------------------------------
// className — applied to root div
// ---------------------------------------------------------------------------

describe('UrgeSlider — className', () => {
  it('merges custom className onto root div', () => {
    const { container } = render(
      <UrgeSlider value={5} onValueChange={() => {}} className="my-urge-slider" />,
    );
    expect(container.firstElementChild?.className).toContain('my-urge-slider');
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

describe('UrgeSlider — axe accessibility', () => {
  it('default render has no a11y violations', async () => {
    render(
      <UrgeSlider
        value={5}
        onValueChange={() => {}}
        ariaLabel="Urge intensity"
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
