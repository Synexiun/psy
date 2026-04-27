'use client';
/**
 * Contract tests for packages/design-system/src/clinical/RCIDelta.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here.
 *
 * Rules under test:
 *   Rule #9 — Latin digits for clinical scores regardless of locale
 *
 * Threshold source: Jacobson & Truax (1991).
 *   PHQ-9 SE=2.68; RCI threshold=1.96×SE=5.26
 *   Significance bands: |Δ| ≥ 5.26 → significant, ≥ 2.5 → moderate, < 2.5 → non-significant
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — component renders as a plain div, not a landmark region
 */

import type * as React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { RCIDelta } from '@disciplineos/design-system/clinical/RCIDelta';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Contract: Jacobson & Truax 1991 significance thresholds
// ---------------------------------------------------------------------------

it('rciDelta_uses_jacobson_truax_1991_significance_thresholds', () => {
  // Significant: |delta| >= 5.26
  const { rerender } = render(<RCIDelta delta={-6} />);
  expect(screen.getByTestId('rci-significance').textContent).toContain('significant');
  // Moderate: 2.5 <= |delta| < 5.26
  rerender(<RCIDelta delta={-3} />);
  expect(screen.getByTestId('rci-significance').textContent).toContain('moderate');
  // Non-significant: |delta| < 2.5
  rerender(<RCIDelta delta={-1} />);
  expect(screen.getByTestId('rci-significance').textContent).toContain('non-significant');
});

// ---------------------------------------------------------------------------
// Dot scale
// ---------------------------------------------------------------------------

it('rciDelta_renders_dot_scale_for_all_significance_levels', () => {
  // significant → ●●●
  const { rerender } = render(<RCIDelta delta={-6} />);
  expect(screen.getByTestId('rci-dots').textContent).toContain('●●●');
  // moderate → ●●○
  rerender(<RCIDelta delta={-3} />);
  expect(screen.getByTestId('rci-dots').textContent).toContain('●●○');
  // non-significant → ●○○
  rerender(<RCIDelta delta={-1} />);
  expect(screen.getByTestId('rci-dots').textContent).toContain('●○○');
});

// ---------------------------------------------------------------------------
// Rule #9 — Latin digits regardless of locale
// ---------------------------------------------------------------------------

it('rciDelta_renders_latin_delta_in_fa_locale', () => {
  render(<RCIDelta delta={-3} locale="fa" />);
  const deltaEl = screen.getByTestId('rci-delta');
  expect(deltaEl.textContent).toBe('-3');
  expect(deltaEl.textContent).not.toBe('-۳');
});

// ---------------------------------------------------------------------------
// Color classes based on direction
// ---------------------------------------------------------------------------

describe('RCIDelta — color classes', () => {
  it('positive delta applies text-signal-stable', () => {
    render(<RCIDelta delta={6} />);
    const deltaEl = screen.getByTestId('rci-delta');
    expect(deltaEl.className).toContain('text-signal-stable');
  });

  it('negative delta applies text-signal-warning', () => {
    render(<RCIDelta delta={-6} />);
    const deltaEl = screen.getByTestId('rci-delta');
    expect(deltaEl.className).toContain('text-signal-warning');
  });

  it('zero delta applies text-ink-tertiary', () => {
    render(<RCIDelta delta={0} />);
    const deltaEl = screen.getByTestId('rci-delta');
    expect(deltaEl.className).toContain('text-ink-tertiary');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('RCIDelta — className', () => {
  it('applies custom className to root element', () => {
    const { container } = render(
      <RCIDelta delta={-3} className="my-rci-delta" />,
    );
    expect(container.firstElementChild?.className).toContain('my-rci-delta');
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

describe('RCIDelta — axe accessibility', () => {
  it('default render has no a11y violations', async () => {
    render(<RCIDelta delta={-6} />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
