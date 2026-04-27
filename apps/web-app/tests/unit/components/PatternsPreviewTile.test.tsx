'use client';
/**
 * Unit tests for PatternsPreviewTile.
 *
 * PatternsPreviewTile is a lightweight dashboard tile that shows:
 *   - pattern type badge
 *   - 1-line description text
 *
 * It intentionally omits all lifecycle UI (dismiss / snooze buttons).
 * That is InsightCard's responsibility on the dedicated Patterns page.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PatternsPreviewTile } from '@/components/PatternsPreviewTile';
import type { PatternData } from '@/hooks/useDashboardData';

// next-intl requires NextIntlClientProvider context; mock for unit tests
vi.mock('next-intl', () => ({
  useTranslations: (namespace: string) => (key: string) => {
    if (namespace === 'patterns') {
      const catalog: Record<string, string> = {
        'types.temporal': 'Time pattern',
        'types.contextual': 'Context pattern',
        'types.physiological': 'Body signal',
        'types.compound': 'Compound signal',
      };
      return catalog[key] ?? key;
    }
    return key;
  },
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

describe('PatternsPreviewTile', () => {
  // 1. Renders pattern type badge
  it('renders "Time pattern" badge for temporal pattern type', () => {
    render(<PatternsPreviewTile pattern={makePattern({ pattern_type: 'temporal' })} />);
    expect(screen.getByText('Time pattern')).toBeInTheDocument();
  });

  // 2. Renders description text
  it('renders the pattern description text', () => {
    render(<PatternsPreviewTile pattern={makePattern()} />);
    expect(
      screen.getByText(/urge intensity tends to rise between 5 PM and 7 PM/i),
    ).toBeInTheDocument();
  });

  // 3. Does NOT render dismiss/snooze buttons (lifecycle UI absent)
  it('does not render a dismiss button', () => {
    render(<PatternsPreviewTile pattern={makePattern()} />);
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('does not render a snooze button', () => {
    render(<PatternsPreviewTile pattern={makePattern()} />);
    expect(screen.queryByText(/snooze/i)).toBeNull();
  });

  // 4a. Renders with contextual pattern type
  it('renders "Context pattern" badge for contextual pattern type', () => {
    render(
      <PatternsPreviewTile
        pattern={makePattern({
          pattern_type: 'contextual',
          description: 'Work stress and social situations co-occur in 68% of logged urges.',
        })}
      />,
    );
    expect(screen.getByText('Context pattern')).toBeInTheDocument();
  });

  // 4b. Renders with physiological pattern type
  it('renders "Body signal" badge for physiological pattern type', () => {
    render(
      <PatternsPreviewTile
        pattern={makePattern({
          pattern_type: 'physiological',
          description: 'Elevated resting heart rate detected before urge events.',
        })}
      />,
    );
    expect(screen.getByText('Body signal')).toBeInTheDocument();
  });

  // 4c. Renders with compound pattern type
  it('renders "Compound signal" badge for compound pattern type', () => {
    render(
      <PatternsPreviewTile
        pattern={makePattern({
          pattern_type: 'compound',
          description: 'Combined time and context signals detected.',
        })}
      />,
    );
    expect(screen.getByText('Compound signal')).toBeInTheDocument();
  });

  // data-testid present
  it('renders with data-testid="pattern-preview-tile"', () => {
    const { container } = render(<PatternsPreviewTile pattern={makePattern()} />);
    expect(container.querySelector('[data-testid="pattern-preview-tile"]')).not.toBeNull();
  });

  // Graceful fallback for unknown types
  it('renders raw pattern_type when type is unknown', () => {
    render(
      <PatternsPreviewTile
        pattern={makePattern({ pattern_type: 'future_type', description: 'Unknown.' })}
      />,
    );
    expect(screen.getByText('future_type')).toBeInTheDocument();
  });

  // No confidence chip / metadata chips (keep tile lightweight)
  it('does not render metadata chips', () => {
    const { container } = render(<PatternsPreviewTile pattern={makePattern()} />);
    // PatternCard renders chips with .bg-surface-tertiary and key:value text.
    // PatternsPreviewTile should have none of those for peak_start_hour.
    expect(screen.queryByText(/peak_start_hour/)).toBeNull();
  });
});
