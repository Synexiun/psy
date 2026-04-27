'use client';
/**
 * Contract tests for packages/design-system/src/primitives/EmptyState.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets (10 cases):
 *  1.  Default render: headline visible
 *  2.  illustration renders above headline in DOM
 *  3.  body text renders when provided
 *  4.  body text absent when not provided
 *  5.  CTA button renders when ctaLabel AND onCta both provided
 *  6.  CTA button NOT rendered when ctaLabel omitted
 *  7.  CTA button NOT rendered when onCta omitted
 *  8.  Clicking CTA calls onCta
 *  9.  Custom className applied to root
 * 10.  axe scan passes (color-contrast and region rules disabled)
 */

import type * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { EmptyState } from '@disciplineos/design-system/primitives/EmptyState';

expect.extend(toHaveNoViolations);

// axe instance — color-contrast and region rules disabled (jsdom has no computed styles)
const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    'region': { enabled: false },
  },
});

// ---------------------------------------------------------------------------
// 1. Default render: headline visible
// ---------------------------------------------------------------------------

describe('EmptyState — default render', () => {
  it('renders the headline text', () => {
    const { getByText } = render(
      <EmptyState headline="No check-ins yet" />,
    );
    expect(getByText('No check-ins yet')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 2. illustration renders above headline in DOM
// ---------------------------------------------------------------------------

describe('EmptyState — illustration slot', () => {
  it('renders the illustration above the headline', () => {
    const { container, getByText } = render(
      <EmptyState
        illustration={<span data-testid="illus">🌱</span>}
        headline="No sessions this week"
      />,
    );
    const illustrationWrapper = container.querySelector('[data-testid="illus"]');
    expect(illustrationWrapper).not.toBeNull();
    const headline = getByText('No sessions this week');
    // illustration wrapper's parent (mb-2 div) must appear before the h2 in the DOM
    const illustrationParent = illustrationWrapper!.parentElement;
    expect(illustrationParent).not.toBeNull();
    const rootChildren = Array.from(container.firstElementChild!.children);
    const illustIdx = rootChildren.indexOf(illustrationParent as Element);
    const headlineIdx = rootChildren.indexOf(headline.parentElement === container.firstElementChild ? headline as Element : headline);
    // The illustration wrapper div should come before the h2 in the root's children
    const h2 = container.querySelector('h2');
    const h2Idx = rootChildren.indexOf(h2 as Element);
    expect(illustIdx).toBeLessThan(h2Idx);
  });
});

// ---------------------------------------------------------------------------
// 3. body text renders when provided
// ---------------------------------------------------------------------------

describe('EmptyState — body text', () => {
  it('renders body text when provided', () => {
    const { getByText } = render(
      <EmptyState
        headline="No check-ins yet"
        body="Complete your first check-in to see your progress here."
      />,
    );
    expect(getByText('Complete your first check-in to see your progress here.')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 4. body text absent when not provided
// ---------------------------------------------------------------------------

describe('EmptyState — body text absent', () => {
  it('does not render a <p> when body is not provided', () => {
    const { container } = render(
      <EmptyState headline="No check-ins yet" />,
    );
    const p = container.querySelector('p');
    expect(p).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 5. CTA button renders when ctaLabel AND onCta both provided
// ---------------------------------------------------------------------------

describe('EmptyState — CTA renders with both props', () => {
  it('renders the CTA button when ctaLabel and onCta are both provided', () => {
    const { getByRole } = render(
      <EmptyState
        headline="No check-ins yet"
        ctaLabel="Start check-in"
        onCta={() => {}}
      />,
    );
    const button = getByRole('button', { name: 'Start check-in' });
    expect(button).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 6. CTA button NOT rendered when ctaLabel omitted
// ---------------------------------------------------------------------------

describe('EmptyState — CTA absent without ctaLabel', () => {
  it('does not render a button when ctaLabel is omitted', () => {
    const { container } = render(
      <EmptyState
        headline="No check-ins yet"
        onCta={() => {}}
      />,
    );
    expect(container.querySelector('button')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 7. CTA button NOT rendered when onCta omitted
// ---------------------------------------------------------------------------

describe('EmptyState — CTA absent without onCta', () => {
  it('does not render a button when onCta is omitted', () => {
    const { container } = render(
      <EmptyState
        headline="No check-ins yet"
        ctaLabel="Start check-in"
      />,
    );
    expect(container.querySelector('button')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 8. Clicking CTA calls onCta
// ---------------------------------------------------------------------------

describe('EmptyState — CTA click handler', () => {
  it('calls onCta when the button is clicked', () => {
    const onCta = vi.fn();
    const { container } = render(
      <EmptyState
        headline="No check-ins yet"
        ctaLabel="Start check-in"
        onCta={onCta}
      />,
    );
    const button = container.querySelector('button');
    expect(button).not.toBeNull();
    fireEvent.click(button!);
    expect(onCta).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// 9. Custom className applied to root
// ---------------------------------------------------------------------------

describe('EmptyState — custom className', () => {
  it('applies a custom className to the root element', () => {
    const { container } = render(
      <EmptyState headline="No check-ins yet" className="my-custom-class" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('my-custom-class')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 10. axe accessibility
// ---------------------------------------------------------------------------

describe('EmptyState — axe accessibility', () => {
  it('passes axe for default render', async () => {
    render(<EmptyState headline="No check-ins yet" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with all props', async () => {
    render(
      <EmptyState
        illustration={<span aria-hidden="true">🌱</span>}
        headline="No sessions this week"
        body="Complete your first session to see your progress here."
        ctaLabel="Start now"
        onCta={() => {}}
      />,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
