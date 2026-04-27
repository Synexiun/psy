'use client';
/**
 * Contract tests for packages/design-system/src/clinical/SeverityBand.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here.
 *
 * Rules under test:
 *   Rule #9 — Latin digits for clinical scores regardless of locale
 *
 * Threshold parity verified against:
 *   apps/web-app/src/lib/clinical/phq9-thresholds.ts
 *   (mirror of services/api/src/discipline/psychometric/scoring/phq9.py)
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — component renders as a plain div, not a landmark region
 */

import type * as React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { SeverityBand } from '@disciplineos/design-system/clinical/SeverityBand';
import { PHQ9_SEVERITY_THRESHOLDS } from '@/lib/clinical/phq9-thresholds';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Contract: threshold parity with pinned Kroenke 2001 values
// ---------------------------------------------------------------------------

it('severityBand_uses_pinned_phq9_thresholds_not_hand_rolled', () => {
  // Render at boundary scores and verify the correct band shows
  // These expected values come from PHQ9_SEVERITY_THRESHOLDS (Kroenke 2001)
  const cases: Array<[number, string]> = [
    [PHQ9_SEVERITY_THRESHOLDS.minimal.max,  'Minimal'],  // 4
    [PHQ9_SEVERITY_THRESHOLDS.mild.min,     'Mild'],     // 5
    [PHQ9_SEVERITY_THRESHOLDS.mild.max,     'Mild'],     // 9
    [PHQ9_SEVERITY_THRESHOLDS.moderate.min, 'Moderate'], // 10
    [PHQ9_SEVERITY_THRESHOLDS.moderate.max, 'Moderate'], // 14
    [PHQ9_SEVERITY_THRESHOLDS.severe.min,   'Severe'],   // 15
    [PHQ9_SEVERITY_THRESHOLDS.severe.max,   'Severe'],   // 19
    [PHQ9_SEVERITY_THRESHOLDS.extreme.min,  'Extreme'],  // 20
    [PHQ9_SEVERITY_THRESHOLDS.extreme.max,  'Extreme'],  // 27
  ];
  for (const [score, expectedBand] of cases) {
    const { unmount } = render(<SeverityBand score={score} />);
    expect(screen.getByTestId('severity-band').textContent).toBe(expectedBand);
    unmount();
  }
});

// ---------------------------------------------------------------------------
// Rule #9 — Latin digits regardless of locale
// ---------------------------------------------------------------------------

it('severityBand_renders_latin_score_under_fa_locale', () => {
  render(<SeverityBand score={15} locale="fa" />);
  const scoreEl = screen.getByTestId('severity-score');
  expect(scoreEl.textContent).toBe('15');
  expect(scoreEl.textContent).not.toBe('۱۵');
});

// ---------------------------------------------------------------------------
// Default render — score and band label visible
// ---------------------------------------------------------------------------

describe('SeverityBand — default render', () => {
  it('renders without throwing', () => {
    expect(() => render(<SeverityBand score={7} />)).not.toThrow();
  });

  it('displays the score via data-testid="severity-score"', () => {
    render(<SeverityBand score={7} />);
    expect(screen.getByTestId('severity-score').textContent).toBe('7');
  });

  it('displays the band label via data-testid="severity-band"', () => {
    render(<SeverityBand score={7} />);
    expect(screen.getByTestId('severity-band').textContent).toBe('Mild');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('SeverityBand — className', () => {
  it('applies custom className to root element', () => {
    const { container } = render(
      <SeverityBand score={5} className="my-severity-band" />,
    );
    expect(container.firstElementChild?.className).toContain('my-severity-band');
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

describe('SeverityBand — axe accessibility', () => {
  it('default render has no a11y violations', async () => {
    render(<SeverityBand score={12} />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
