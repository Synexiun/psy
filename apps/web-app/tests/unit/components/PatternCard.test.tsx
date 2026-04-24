/**
 * Unit tests for PatternCard.
 *
 * PatternCard renders a single active pattern: type badge, confidence %, and
 * description. Confidence is formatted by formatPercentClinical and must
 * always be Latin digits.
 *
 * Note: PatternCard does not render a dismiss button — that action is
 * expected to be handled at the parent (dashboard) level. Tests accordingly
 * do not assert on dismiss UI.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PatternCard } from '@/components/PatternCard';
import type { PatternData } from '@/hooks/useDashboardData';

vi.mock('@disciplineos/i18n-catalog', () => ({
  formatNumberClinical: (value: number) => String(value),
  formatPercentClinical: (value: number) => `${value}%`,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makePattern(overrides: Partial<PatternData> = {}): PatternData {
  return {
    pattern_id: 'p_test',
    pattern_type: 'temporal',
    detector: 'peak_window',
    confidence: 0.82,
    description: 'Urge intensity tends to rise between 5 PM and 7 PM on weekdays.',
    metadata: { peak_start_hour: 17, peak_end_hour: 19 },
    status: 'active',
    dismissed_at: null,
    dismiss_reason: null,
    created_at: '2026-04-20T10:00:00Z',
    updated_at: '2026-04-20T10:00:00Z',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('PatternCard', () => {
  // --- Content rendering ----------------------------------------------------

  it('renders the pattern description', () => {
    render(<PatternCard pattern={makePattern()} />);
    expect(
      screen.getByText(/urge intensity tends to rise between 5 PM and 7 PM/i),
    ).toBeInTheDocument();
  });

  it('renders confidence as a percentage', () => {
    render(<PatternCard pattern={makePattern({ confidence: 0.82 })} />);
    // formatPercentClinical(Math.round(0.82 * 100)) → "82%"
    expect(screen.getByText(/82%.*confidence/i)).toBeInTheDocument();
  });

  it('confidence uses Latin digits (no Arabic-Indic numerals)', () => {
    const { container } = render(<PatternCard pattern={makePattern({ confidence: 0.74 })} />);
    const text = container.textContent ?? '';
    expect(/[٠-٩۰-۹]/.test(text)).toBe(false);
  });

  // --- Pattern type badge ---------------------------------------------------

  it('renders "Time pattern" badge for temporal type', () => {
    render(<PatternCard pattern={makePattern({ pattern_type: 'temporal' })} />);
    expect(screen.getByText('Time pattern')).toBeInTheDocument();
  });

  it('renders "Context pattern" badge for contextual type', () => {
    render(
      <PatternCard pattern={makePattern({ pattern_type: 'contextual', description: 'Context.' })} />,
    );
    expect(screen.getByText('Context pattern')).toBeInTheDocument();
  });

  it('renders "Body signal" badge for physiological type', () => {
    render(
      <PatternCard
        pattern={makePattern({ pattern_type: 'physiological', description: 'Physiological.' })}
      />,
    );
    expect(screen.getByText('Body signal')).toBeInTheDocument();
  });

  it('renders "Compound signal" badge for compound type', () => {
    render(
      <PatternCard
        pattern={makePattern({ pattern_type: 'compound', description: 'Compound.' })}
      />,
    );
    expect(screen.getByText('Compound signal')).toBeInTheDocument();
  });

  it('renders raw pattern_type when type is unknown', () => {
    render(
      <PatternCard
        pattern={makePattern({ pattern_type: 'unknown_future_type', description: 'Unknown.' })}
      />,
    );
    expect(screen.getByText('unknown_future_type')).toBeInTheDocument();
  });

  // --- Metadata tags --------------------------------------------------------

  it('renders up to 3 metadata key-value chips', () => {
    const metadata = {
      peak_start_hour: 17,
      peak_end_hour: 19,
      day_of_week: 'weekday',
      extra_key: 'extra_value',
    };
    render(<PatternCard pattern={makePattern({ metadata })} />);
    // Only 3 chips should be rendered (.slice(0, 3) in implementation).
    const chips = screen
      .getAllByText(/peak_start_hour|peak_end_hour|day_of_week|extra_key/)
      .filter((el) => el.tagName === 'SPAN');
    expect(chips.length).toBeLessThanOrEqual(3);
  });

  it('does not render metadata chips when metadata is empty', () => {
    const { container } = render(<PatternCard pattern={makePattern({ metadata: {} })} />);
    // The metadata section only renders when Object.keys(metadata).length > 0.
    const chips = container.querySelectorAll('.bg-surface-100');
    expect(chips.length).toBe(0);
  });

  // --- No dismiss button (PatternCard is display-only) ---------------------

  it('does not render a dismiss button', () => {
    render(<PatternCard pattern={makePattern()} />);
    expect(screen.queryByRole('button')).toBeNull();
  });
});
