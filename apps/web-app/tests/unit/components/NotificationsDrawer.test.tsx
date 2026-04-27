'use client';
/**
 * Unit tests for apps/web-app/src/components/NotificationsDrawer.tsx
 *
 * NotificationsDrawer wraps the design-system Sheet primitive (Radix Dialog).
 * Radix portals dialog content to document.body only when open=true:
 *   - open=false  → children are NOT present in the DOM
 *   - open=true   → children ARE present in the DOM (queried via screen)
 *
 * STUB_NOTIFICATIONS is hardcoded (3 items), so the empty-state branch
 * ("No notifications") is unreachable through props alone. Tests assert
 * this invariant explicitly — the else-branch text must NOT appear.
 *
 * Coverage paths:
 *   1.  open=false → dialog not rendered in DOM
 *   2.  open=false → notification item text not in DOM
 *   3.  open=true  → dialog element rendered
 *   4.  open=true  → all 3 stub notification items rendered
 *   5.  open=true  → notification list has role="list"
 *   6.  open=true  → "No notifications" empty-state NOT in DOM (STUB non-empty)
 *   7.  open=true  → drawer title "Notifications" rendered
 *   8.  count > 0  → description "{count} unread" rendered
 *   9.  count = 0  → no description element rendered (default)
 *  10.  count omitted → no description element rendered
 *  11.  Close button click → onClose callback called exactly once
 *  (+axe): open drawer has no critical a11y violations
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 */

import type * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { NotificationsDrawer } from '../../../src/components/NotificationsDrawer';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderDrawer(
  overrides: Partial<React.ComponentProps<typeof NotificationsDrawer>> = {},
) {
  return render(
    <NotificationsDrawer open={true} onClose={vi.fn()} {...overrides} />,
  );
}

// ---------------------------------------------------------------------------
// axe instance — color-contrast disabled (jsdom has no computed styles)
// ---------------------------------------------------------------------------

const axe = configureAxe({
  rules: { 'color-contrast': { enabled: false } },
});

// ---------------------------------------------------------------------------
// 1–2. Closed state — content absent from DOM
// ---------------------------------------------------------------------------

describe('NotificationsDrawer — closed state', () => {
  it('does not render the dialog when open is false', () => {
    renderDrawer({ open: false });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('does not render notification text in the DOM when open is false', () => {
    renderDrawer({ open: false });
    expect(
      screen.queryByText(
        'Your last check-in showed a rising urge. You handled it — well done.',
      ),
    ).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 3–7. Open state — structure and stub notifications
// ---------------------------------------------------------------------------

describe('NotificationsDrawer — open state', () => {
  it('renders the dialog element when open is true', () => {
    renderDrawer();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('renders all three stub notification items', () => {
    renderDrawer();
    expect(
      screen.getByText(
        'Your last check-in showed a rising urge. You handled it — well done.',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'New pattern detected: urges are higher on weekday evenings.',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Your resilience streak is growing. Keep going.'),
    ).toBeInTheDocument();
  });

  it('notification list has role="list"', () => {
    renderDrawer();
    expect(screen.getByRole('list')).toBeInTheDocument();
  });

  it('does not render "No notifications" empty-state when stub items exist', () => {
    renderDrawer();
    expect(screen.queryByText('No notifications')).toBeNull();
  });

  it('renders the drawer title "Notifications"', () => {
    renderDrawer();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 8–10. count prop — description text
// ---------------------------------------------------------------------------

describe('NotificationsDrawer — count prop', () => {
  it('renders "{count} unread" description when count > 0', () => {
    renderDrawer({ count: 3 });
    expect(screen.getByText('3 unread')).toBeInTheDocument();
  });

  it('does not render a description when count is 0', () => {
    renderDrawer({ count: 0 });
    expect(screen.queryByText(/unread/)).toBeNull();
  });

  it('does not render a description when count is omitted', () => {
    renderDrawer();
    expect(screen.queryByText(/unread/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 11. Close button → onClose callback
// ---------------------------------------------------------------------------

describe('NotificationsDrawer — close callback', () => {
  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn();
    renderDrawer({ onClose });
    const closeBtn = screen.getByRole('button', { name: 'Close notifications' });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// axe accessibility
// ---------------------------------------------------------------------------

describe('NotificationsDrawer — axe accessibility', () => {
  it('open drawer with no count has no critical a11y violations', async () => {
    renderDrawer();
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('open drawer with count > 0 has no critical a11y violations', async () => {
    renderDrawer({ count: 5 });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
