/**
 * Unit tests for StateIndicator.
 *
 * StateIndicator renders a skeleton when loading and a tone-coded state badge
 * with a confidence percentage when data is available. Confidence uses
 * formatPercentClinical, which must always produce Latin digits.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StateIndicator } from '@/components/StateIndicator';
import type { StateEstimateData } from '@/hooks/useDashboardData';

vi.mock('@disciplineos/i18n-catalog', () => ({
  formatNumberClinical: (value: number) => String(value),
  formatPercentClinical: (value: number) => `${value}%`,
}));

// next-intl requires NextIntlClientProvider context; mock for unit tests
vi.mock('next-intl', () => ({
  useTranslations: (namespace: string) => (key: string, params?: Record<string, unknown>) => {
    if (namespace === 'stateIndicator') {
      const catalog: Record<string, string> = {
        'stable.label': 'Stable',
        'stable.message': 'You appear steady right now. A good moment to build habits.',
        'baseline.label': 'Baseline',
        'baseline.message': 'Resting state. Nothing urgent detected.',
        'risingUrge.label': 'Rising urge',
        'risingUrge.message': 'An urge is building. Try a coping tool or a short walk.',
        'peakUrge.label': 'Peak urge',
        'peakUrge.message': 'This is the hardest moment. Use a tool or reach out.',
        'postUrge.label': 'Post urge',
        'postUrge.message': 'The wave has passed. Be gentle with yourself.',
        'fallback.message': 'State estimate available.',
        'confidence': 'confidence',
      };
      if (key === 'fallback.label') return String(params?.state ?? key);
      if (key === 'ariaLabel') return `Current state: ${String(params?.label ?? '')}`;
      return catalog[key] ?? key;
    }
    return key;
  },
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeEstimate(overrides: Partial<StateEstimateData> = {}): StateEstimateData {
  return {
    estimate_id: 'est_1',
    state_label: 'stable',
    confidence: 0.91,
    model_version: 'v1.2.0',
    inferred_at: '2026-04-23T10:00:00Z',
    created_at: '2026-04-23T10:00:00Z',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('StateIndicator', () => {
  // --- Loading state --------------------------------------------------------

  it('renders skeleton when isLoading is true', () => {
    const { container } = render(<StateIndicator data={undefined} isLoading={true} />);
    const skeletons = container.querySelectorAll('[aria-hidden="true"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders skeleton when data is undefined and not loading', () => {
    const { container } = render(<StateIndicator data={undefined} isLoading={false} />);
    const skeletons = container.querySelectorAll('[aria-hidden="true"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('does not render state badge when loading', () => {
    render(<StateIndicator data={undefined} isLoading={true} />);
    expect(screen.queryByText(/stable/i)).toBeNull();
  });

  // --- "stable" state -------------------------------------------------------

  it('renders "Stable" badge for state_label "stable"', () => {
    render(<StateIndicator data={makeEstimate({ state_label: 'stable' })} isLoading={false} />);
    expect(screen.getByText('Stable')).toBeInTheDocument();
  });

  it('renders calming message for stable state', () => {
    render(<StateIndicator data={makeEstimate({ state_label: 'stable' })} isLoading={false} />);
    expect(screen.getByText(/you appear steady right now/i)).toBeInTheDocument();
  });

  it('has accessible wrapper with aria-label mentioning Stable', () => {
    render(<StateIndicator data={makeEstimate({ state_label: 'stable' })} isLoading={false} />);
    expect(screen.getByRole('img', { name: /stable/i })).toBeInTheDocument();
  });

  // --- "rising_urge" state --------------------------------------------------

  it('renders "Rising urge" badge for state_label "rising_urge"', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'rising_urge' })} isLoading={false} />,
    );
    expect(screen.getByText('Rising urge')).toBeInTheDocument();
  });

  it('renders urge-building message for rising_urge state', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'rising_urge' })} isLoading={false} />,
    );
    expect(screen.getByText(/urge is building/i)).toBeInTheDocument();
  });

  // --- "peak_urge" state ----------------------------------------------------

  it('renders "Peak urge" badge for state_label "peak_urge"', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'peak_urge' })} isLoading={false} />,
    );
    expect(screen.getByText('Peak urge')).toBeInTheDocument();
  });

  it('renders crisis message for peak_urge state', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'peak_urge' })} isLoading={false} />,
    );
    expect(screen.getByText(/this is the hardest moment/i)).toBeInTheDocument();
  });

  // --- "post_urge" state ----------------------------------------------------

  it('renders "Post urge" badge for state_label "post_urge"', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'post_urge' })} isLoading={false} />,
    );
    expect(screen.getByText('Post urge')).toBeInTheDocument();
  });

  it('renders compassionate post-urge message', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'post_urge' })} isLoading={false} />,
    );
    expect(screen.getByText(/the wave has passed/i)).toBeInTheDocument();
  });

  // --- "baseline" state -----------------------------------------------------

  it('renders "Baseline" badge for state_label "baseline"', () => {
    render(
      <StateIndicator data={makeEstimate({ state_label: 'baseline' })} isLoading={false} />,
    );
    expect(screen.getByText('Baseline')).toBeInTheDocument();
  });

  // --- Unknown state graceful fallback --------------------------------------

  it('renders raw state_label for unknown states', () => {
    render(
      <StateIndicator
        data={makeEstimate({ state_label: 'custom_state_xyz' })}
        isLoading={false}
      />,
    );
    expect(screen.getByText('custom_state_xyz')).toBeInTheDocument();
  });

  // --- Confidence display ---------------------------------------------------

  it('renders confidence percentage', () => {
    render(<StateIndicator data={makeEstimate({ confidence: 0.91 })} isLoading={false} />);
    // formatPercentClinical(Math.round(0.91 * 100)) → "91%"
    expect(screen.getByText(/91%.*confidence/i)).toBeInTheDocument();
  });

  it('confidence percentage uses Latin digits (no Arabic-Indic numerals)', () => {
    const { container } = render(
      <StateIndicator data={makeEstimate({ confidence: 0.88 })} isLoading={false} />,
    );
    const text = container.textContent ?? '';
    expect(/[٠-٩۰-۹]/.test(text)).toBe(false);
  });
});
