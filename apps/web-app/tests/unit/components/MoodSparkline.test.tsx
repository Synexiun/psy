/**
 * Unit tests for MoodSparkline.
 *
 * MoodSparkline renders a skeleton during loading, falls back to MOOD_STUB
 * when data is absent or empty, and renders real intensities from data.items
 * when available. The "last N check-ins" counter uses the actual data length,
 * not a hard-coded constant.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MoodSparkline } from '@/components/MoodSparkline';
import type { CheckInHistory } from '@/lib/api';

// next-intl requires NextIntlClientProvider context; mock for unit tests.
vi.mock('next-intl', () => ({
  useTranslations: (namespace: string) => (key: string, params?: Record<string, unknown>) => {
    if (namespace === 'moodSparkline') {
      const count = params?.['count'] as number | undefined;
      const catalog: Record<string, string> = {
        heading: 'Mood trend',
        subtitle: `Last ${count ?? '{count}'} check-ins`,
        ariaLabel: `Mood trend over last ${count ?? '{count}'} check-ins`,
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
    // Skeleton renders pulse animation elements — no "Mood trend" heading yet.
    expect(screen.queryByText('Mood trend')).toBeNull();
    // The container should have animate-pulse elements.
    const pulseEls = container.querySelectorAll('.animate-pulse');
    expect(pulseEls.length).toBeGreaterThan(0);
  });

  it('does not render sparkline when loading', () => {
    render(<MoodSparkline data={undefined} isLoading={true} />);
    expect(screen.queryByRole('img')).toBeNull();
  });

  // --- Stub / empty data fallback -------------------------------------------

  it('renders "Mood trend" heading when not loading', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    expect(screen.getByText('Mood trend')).toBeInTheDocument();
  });

  it('renders sparkline aria-label when data is undefined (uses MOOD_STUB, length 20)', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    // MOOD_STUB has 20 entries → "Mood trend over last 20 check-ins"
    expect(
      screen.getByRole('img', { name: /mood trend over last 20 check-ins/i }),
    ).toBeInTheDocument();
  });

  it('renders "Last 20 check-ins" counter when using MOOD_STUB', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    expect(screen.getByText(/last 20 check-ins/i)).toBeInTheDocument();
  });

  it('falls back to MOOD_STUB when data.items is empty', () => {
    const empty = makeHistory([]);
    render(<MoodSparkline data={empty} isLoading={false} />);
    // MOOD_STUB last value is 7.
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  // --- Real data rendering --------------------------------------------------

  it('renders correct "last N check-ins" count from real data', () => {
    const history = makeHistory([3, 5, 7, 6, 8]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(screen.getByText(/last 5 check-ins/i)).toBeInTheDocument();
  });

  it('renders the last intensity value from real data', () => {
    // Last item in the array is displayed as the current intensity.
    const history = makeHistory([4, 6, 9]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(screen.getByText('9')).toBeInTheDocument();
  });

  it('sparkline aria-label reflects real data length', () => {
    const history = makeHistory([5, 6, 7, 8, 9, 10]);
    render(<MoodSparkline data={history} isLoading={false} />);
    expect(
      screen.getByRole('img', { name: /mood trend over last 6 check-ins/i }),
    ).toBeInTheDocument();
  });

  it('renders "/ 10" scale denominator', () => {
    render(<MoodSparkline data={undefined} isLoading={false} />);
    expect(screen.getByText('/ 10')).toBeInTheDocument();
  });

  // --- Latin digits ---------------------------------------------------------

  it('last intensity is displayed as a Latin digit (no Arabic-Indic numerals)', () => {
    const history = makeHistory([3, 5, 7]);
    const { container } = render(<MoodSparkline data={history} isLoading={false} />);
    const text = container.textContent ?? '';
    expect(/[٠-٩۰-۹]/.test(text)).toBe(false);
  });
});
