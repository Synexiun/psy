/**
 * Unit tests for MoodSparkline.
 *
 * Renders a skeleton during loading, an empty state when data is absent or
 * empty, and the real sparkline + last intensity when data.items is populated.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MoodSparkline } from '@/components/MoodSparkline';
import type { CheckInHistory } from '@/lib/api';

vi.mock('next-intl', () => ({
  useTranslations: (namespace: string) => (key: string, params?: Record<string, unknown>) => {
    if (namespace === 'moodSparkline') {
      const count = params?.['count'] as number | undefined;
      const catalog: Record<string, string> = {
        heading: 'Mood trend',
        subtitle: `Last ${count ?? '{count}'} check-ins`,
        ariaLabel: `Mood trend over last ${count ?? '{count}'} check-ins`,
        noDataYet: 'No check-ins yet — start logging to see your mood trend.',
      };
      return catalog[key] ?? key;
    }
    return key;
  },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeHistory(intensities: number[]): CheckInHistory {
  return {
    items: intensities.map((intensity, i) => ({
      session_id: `s-${i}`,
      intensity,
      trigger_tags: [],
      checked_in_at: new Date(Date.now() - i * 3_600_000).toISOString(),
    })),
    total: intensities.length,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('MoodSparkline', () => {
  // --- Loading state --------------------------------------------------------

  it('renders skeleton when isLoading is true', () => {
    const { container } = render(<MoodSparkline data={undefined} isLoading={true} />);
    expect(screen.queryByText('Mood trend')).toBeNull();
    const pulseEls = container.querySelectorAll('.animate-pulse');
    expect(pulseEls.length).toBeGreaterThan(0);
  });

  it('does not render sparkline when loading', () => {
    render(<MoodSparkline data={undefined} isLoading={true} />);
    expect(screen.queryByRole('img')).toBeNull();
  });

  // --- Empty state ----------------------------------------------------------

  it('renders "Mood trend" heading when not loading', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    expect(screen.getByText('Mood trend')).toBeInTheDocument();
  });

  it('renders empty state message when data is undefined', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    expect(screen.getByText(/no check-ins yet/i)).toBeInTheDocument();
  });

  it('renders empty state message when data.items is empty', () => {
    const empty = makeHistory([]);
    render(<MoodSparkline data={empty} isLoading={false} />);
    expect(screen.getByText(/no check-ins yet/i)).toBeInTheDocument();
  });

  it('does not render sparkline or denominator in empty state', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    expect(screen.queryByRole('img')).toBeNull();
    expect(screen.queryByText(/\/\s*10/)).toBeNull();
  });

  // --- Real data rendering --------------------------------------------------

  it('renders correct "last N check-ins" count from real data', () => {
    const history = makeHistory([3, 5, 7, 6, 8]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(screen.getByText(/last 5 check-ins/i)).toBeInTheDocument();
  });

  it('renders the last intensity value from real data', () => {
    const history = makeHistory([4, 6, 9]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(screen.getByText('9')).toBeInTheDocument();
  });

  it('renders "/ 10" scale denominator when real data is present', () => {
    const history = makeHistory([5, 7, 8]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(screen.getByText(/\/\s*10/)).toBeInTheDocument();
  });

  it('sparkline aria-label reflects real data length', () => {
    const history = makeHistory([5, 6, 7, 8, 9, 10]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(
      screen.getByRole('img', { name: /mood trend over last 6 check-ins/i }),
    ).toBeInTheDocument();
  });

  // --- Latin digits ---------------------------------------------------------

  it('last intensity is displayed as a Latin digit (no Arabic-Indic numerals)', () => {
    const history = makeHistory([3, 5, 7]);
    const { container } = render(<MoodSparkline data={history} isLoading={false} />);
    const text = container.textContent ?? '';
    expect(/[٠-٩۰-۹]/.test(text)).toBe(false);
  });
});
