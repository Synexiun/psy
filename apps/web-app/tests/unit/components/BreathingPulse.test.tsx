'use client';
/**
 * Contract tests for packages/design-system/src/clinical/BreathingPulse.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here.
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — component renders as role="img", not a landmark region
 */

import type * as React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { BreathingPulse } from '@disciplineos/design-system/clinical/BreathingPulse';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Default matchMedia stub (non-reduced) — jsdom does not implement matchMedia
// ---------------------------------------------------------------------------

function stubMatchMedia(prefersReduced: boolean): void {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches: prefersReduced ? query.includes('reduce') : false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

beforeEach(() => {
  stubMatchMedia(false);
});

// ---------------------------------------------------------------------------
// Contract: phase durations are locked to 4 000 ms each
// ---------------------------------------------------------------------------

it('breathingPulse_inhale_exhale_phase_durations_locked_to_4000ms_each', () => {
  const { container } = render(<BreathingPulse />);
  const el = container.querySelector('[data-inhale-ms]');
  expect(el?.getAttribute('data-inhale-ms')).toBe('4000');
  expect(el?.getAttribute('data-exhale-ms')).toBe('4000');
});

// ---------------------------------------------------------------------------
// Contract: animation suppressed when prefers-reduced-motion: reduce
// ---------------------------------------------------------------------------

it('breathingPulse_suppressed_when_useReducedMotion_returns_true', () => {
  // Mock window.matchMedia to return prefers-reduced-motion: reduce
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: query.includes('reduce'),
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
  const { container } = render(<BreathingPulse />);
  // Static mode: no animation style on the circle
  const animatedEl = container.querySelector('[style*="animation"]');
  expect(animatedEl).toBeNull();
  // Should still render (static circle or text)
  expect(container.firstElementChild).not.toBeNull();
});


// ---------------------------------------------------------------------------
// Default render
// ---------------------------------------------------------------------------

describe('BreathingPulse — default render', () => {
  it('mounts without error', () => {
    expect(() => render(<BreathingPulse />)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// ariaLabel
// ---------------------------------------------------------------------------

describe('BreathingPulse — ariaLabel', () => {
  it('applies custom ariaLabel to root', () => {
    const { container } = render(<BreathingPulse ariaLabel="Box breathing exercise" />);
    expect(container.firstElementChild?.getAttribute('aria-label')).toBe('Box breathing exercise');
  });

  it('applies default ariaLabel when omitted', () => {
    const { container } = render(<BreathingPulse />);
    expect(container.firstElementChild?.getAttribute('aria-label')).toBe('Breathing guide');
  });
});

// ---------------------------------------------------------------------------
// role="img"
// ---------------------------------------------------------------------------

describe('BreathingPulse — role', () => {
  it('root has role="img"', () => {
    const { container } = render(<BreathingPulse />);
    expect(container.firstElementChild?.getAttribute('role')).toBe('img');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('BreathingPulse — className', () => {
  it('merges custom className onto root', () => {
    const { container } = render(<BreathingPulse className="my-custom-class" />);
    expect(container.firstElementChild?.className).toContain('my-custom-class');
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

describe('BreathingPulse — axe accessibility', () => {
  it('default render has no a11y violations', async () => {
    render(<BreathingPulse />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
