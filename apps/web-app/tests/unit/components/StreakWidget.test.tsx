/**
 * Unit tests for StreakWidget.
 *
 * StreakWidget renders a skeleton when loading, and two ProgressRing cards
 * (continuous + resilience) when data is available. Clinical numbers must
 * always be Latin digits regardless of locale.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StreakWidget } from '@/components/StreakWidget';
import type { StreakData } from '@/hooks/useDashboardData';

// ---------------------------------------------------------------------------
// Mock @disciplineos/i18n-catalog so tests don't require the full package
// build. The formatNumberClinical real implementation just uses
// .toLocaleString('en') which is deterministic anyway — the mock makes the
// dependency explicit and removes any build-time risk.
// ---------------------------------------------------------------------------
vi.mock('@disciplineos/i18n-catalog', () => ({
  formatNumberClinical: (value: number) => String(value),
  formatPercentClinical: (value: number) => `${value}%`,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const STREAK_DATA: StreakData = {
  continuous_days: 12,
  continuous_streak_start: '2026-04-11T00:00:00Z',
  resilience_days: 47,
  resilience_urges_handled_total: 89,
  resilience_streak_start: '2026-03-07T00:00:00Z',
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('StreakWidget', () => {
  it('renders skeletons when isLoading is true', () => {
    const { container } = render(<StreakWidget data={undefined} isLoading={true} />);
    // Skeleton elements are rendered as aria-hidden divs with an animate-pulse class.
    const skeletons = container.querySelectorAll('[aria-hidden="true"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders skeletons when data is undefined regardless of isLoading', () => {
    const { container } = render(<StreakWidget data={undefined} isLoading={false} />);
    const skeletons = container.querySelectorAll('[aria-hidden="true"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('does not render ProgressRings when loading', () => {
    render(<StreakWidget data={undefined} isLoading={true} />);
    // ProgressRing renders with role="img" and an ariaLabel; none should exist in skeleton.
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('renders resilience streak count when data is provided', async () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    // The resilience_days value (47) should appear in the document.
    expect(screen.getAllByText('47').length).toBeGreaterThan(0);
  });

  it('renders continuous streak count when data is provided', async () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    // The continuous_days value (12) should appear in the document.
    expect(screen.getAllByText('12').length).toBeGreaterThan(0);
  });

  it('renders "Resilience streak" label', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(screen.getByText('Resilience streak')).toBeInTheDocument();
  });

  it('renders "Continuous streak" label', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(screen.getByText('Continuous streak')).toBeInTheDocument();
  });

  it('ProgressRing for continuous streak has aria-label', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(
      screen.getByRole('img', { name: /continuous streak/i }),
    ).toBeInTheDocument();
  });

  it('ProgressRing for resilience streak has aria-label', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(
      screen.getByRole('img', { name: /resilience streak/i }),
    ).toBeInTheDocument();
  });

  it('streak counts use Latin digits (no Arabic-Indic numerals)', () => {
    const { container } = render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    const text = container.textContent ?? '';
    // Arabic-Indic digits are U+0660–U+0669; Persian digits are U+06F0–U+06F9.
    expect(/[٠-٩۰-۹]/.test(text)).toBe(false);
  });

  it('renders urges handled count', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(screen.getByText(/89.*urges handled/i)).toBeInTheDocument();
  });

  it('renders "days of growth" copy when resilience_days > 0', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(screen.getByText(/days of growth/i)).toBeInTheDocument();
  });

  it('renders "days strong" copy when continuous_days > 0', () => {
    render(<StreakWidget data={STREAK_DATA} isLoading={false} />);
    expect(screen.getByText(/days strong/i)).toBeInTheDocument();
  });

  it('renders compassionate zero-state copy for continuous streak', () => {
    render(
      <StreakWidget
        data={{ ...STREAK_DATA, continuous_days: 0 }}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/every day is a fresh start/i)).toBeInTheDocument();
  });

  it('renders compassionate zero-state copy for resilience streak', () => {
    render(
      <StreakWidget
        data={{ ...STREAK_DATA, resilience_days: 0 }}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/building resilience/i)).toBeInTheDocument();
  });
});
