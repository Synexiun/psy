'use client';
/**
 * Contract tests for packages/design-system/src/clinical/InsightCard.tsx
 *
 * Verifies the dismiss / snooze / acknowledge lifecycle per Sprint 108 contract.
 * Body text is rendered verbatim; Latin-digit enforcement is the caller's
 * responsibility (Rule #9).
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — component renders as a card, not a landmark region
 */

import type * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { InsightCard } from '@disciplineos/design-system/clinical/InsightCard';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Sprint 108 lifecycle contract — exact test name required
// ---------------------------------------------------------------------------

it('insightCard_dismiss_lifecycle_per_sprint_108_contract', () => {
  const onDismiss = vi.fn();
  const onSnooze = vi.fn();
  const onAcknowledge = vi.fn();
  const { container } = render(
    <InsightCard
      id="test-insight"
      headline="You tend to struggle on Sundays"
      body="3 of your last 5 high-urge events occurred on Sunday evenings."
      onDismiss={onDismiss}
      onSnooze={onSnooze}
      onAcknowledge={onAcknowledge}
    />
  );

  // Initial: visible state, action buttons present
  expect(screen.getByTestId('btn-acknowledge')).toBeInTheDocument();
  expect(screen.getByTestId('btn-snooze-24h')).toBeInTheDocument();
  expect(screen.getByTestId('btn-snooze-7d')).toBeInTheDocument();

  // Acknowledge transition
  fireEvent.click(screen.getByTestId('btn-acknowledge'));
  expect(onAcknowledge).toHaveBeenCalledWith('test-insight');
  expect(screen.getByTestId('acknowledged-indicator')).toBeInTheDocument();
  expect(screen.queryByTestId('btn-acknowledge')).not.toBeInTheDocument();

  // Dismiss from acknowledged state
  const dismissBtn = container.querySelector('button[aria-label="Dismiss"], button:has(.sr-only)') ??
    container.querySelector('button');
  expect(dismissBtn).not.toBeNull();
  fireEvent.click(dismissBtn!);
  expect(onDismiss).toHaveBeenCalledWith('test-insight');
  expect(container.firstElementChild).toBeNull(); // renders null
});

// ---------------------------------------------------------------------------
// Latin digit contract — exact test name required
// ---------------------------------------------------------------------------

it('insightCard_renders_latin_numerics_under_fa_locale', () => {
  render(
    <InsightCard
      id="test"
      headline="Insight"
      body="3 of 5 events"
      locale="fa"
    />
  );
  // Body text is rendered verbatim — Latin digits are the caller's responsibility
  // The component renders what it receives without transformation
  expect(screen.getByTestId('insight-body').textContent).toBe('3 of 5 events');
});

// ---------------------------------------------------------------------------
// Default render
// ---------------------------------------------------------------------------

describe('InsightCard — default render', () => {
  it('renders headline and body', () => {
    render(
      <InsightCard
        id="ic-1"
        headline="Test headline"
        body="Test body text"
      />
    );
    expect(screen.getByTestId('insight-headline').textContent).toBe('Test headline');
    expect(screen.getByTestId('insight-body').textContent).toBe('Test body text');
  });

  it('mounts without error', () => {
    expect(() =>
      render(<InsightCard id="ic-2" headline="H" body="B" />)
    ).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Snooze 24h
// ---------------------------------------------------------------------------

describe('InsightCard — snooze 24h', () => {
  it('renders null and calls onSnooze with 24h when snooze-24h clicked', () => {
    const onSnooze = vi.fn();
    const { container } = render(
      <InsightCard
        id="test-insight"
        headline="H"
        body="B"
        onSnooze={onSnooze}
      />
    );
    fireEvent.click(screen.getByTestId('btn-snooze-24h'));
    expect(onSnooze).toHaveBeenCalledWith('test-insight', '24h');
    expect(container.firstElementChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Snooze 7d
// ---------------------------------------------------------------------------

describe('InsightCard — snooze 7d', () => {
  it('renders null and calls onSnooze with 7d when snooze-7d clicked', () => {
    const onSnooze = vi.fn();
    const { container } = render(
      <InsightCard
        id="test-insight"
        headline="H"
        body="B"
        onSnooze={onSnooze}
      />
    );
    fireEvent.click(screen.getByTestId('btn-snooze-7d'));
    expect(onSnooze).toHaveBeenCalledWith('test-insight', '7d');
    expect(container.firstElementChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Dismiss from visible state
// ---------------------------------------------------------------------------

describe('InsightCard — dismiss from visible', () => {
  it('renders null and calls onDismiss when dismiss clicked in visible state', () => {
    const onDismiss = vi.fn();
    const { container } = render(
      <InsightCard
        id="test-insight"
        headline="H"
        body="B"
        onDismiss={onDismiss}
      />
    );
    const dismissBtn = container.querySelector('button[aria-label="Dismiss"]');
    expect(dismissBtn).not.toBeNull();
    fireEvent.click(dismissBtn!);
    expect(onDismiss).toHaveBeenCalledWith('test-insight');
    expect(container.firstElementChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('InsightCard — className', () => {
  it('applies extra className to root element', () => {
    const { container } = render(
      <InsightCard id="ic-3" headline="H" body="B" className="my-custom-class" />
    );
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

describe('InsightCard — axe accessibility', () => {
  it('default render has no a11y violations', async () => {
    render(
      <InsightCard
        id="axe-test"
        headline="You tend to struggle on Sundays"
        body="3 of your last 5 high-urge events occurred on Sunday evenings."
      />
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('acknowledged state has no a11y violations', async () => {
    const { getByTestId } = render(
      <InsightCard
        id="axe-ack"
        headline="Evening hours are your peak risk window"
        body="4 of your last 6 urge spikes happened between 8 PM and 11 PM."
      />
    );
    fireEvent.click(getByTestId('btn-acknowledge'));
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
