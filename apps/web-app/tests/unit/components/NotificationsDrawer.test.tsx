'use client';
/**
 * Unit tests for apps/web-app/src/components/NotificationsDrawer.tsx
 *
 * NotificationsDrawer wraps the design-system Sheet primitive (Radix Dialog).
 * Radix portals dialog content to document.body only when open=true:
 *   - open=false  → children are NOT present in the DOM
 *   - open=true   → children ARE present in the DOM (queried via screen)
 *
 * useNotifications() pulls from notificationsStubs (3 items, 1 unread).
 * The empty-state branch ("No notifications yet") is unreachable through
 * props alone since the stub is non-empty. Tests assert this invariant
 * explicitly — the empty-state text must NOT appear.
 *
 * Coverage paths:
 *   1.  open=false → dialog not rendered in DOM
 *   2.  open=false → notification item text not in DOM
 *   3.  open=true  → dialog element rendered
 *   4.  open=true  → all 3 stub notification items rendered
 *   5.  open=true  → notification list has role="list"
 *   6.  open=true  → empty-state NOT in DOM (stub non-empty)
 *   7.  open=true  → drawer title "Notifications" rendered
 *   8.  open=true  → "1 unread" description rendered (stub has 1 unread item)
 *   9.  Close button click → onClose callback called exactly once
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

// next-intl requires NextIntlClientProvider context; mock for unit tests
vi.mock('next-intl', () => ({
  useTranslations: () => (key: string, params?: Record<string, unknown>) => {
    if (key === 'drawerTitle') return 'Notifications';
    if (key === 'closeLabel') return 'Close notifications';
    if (key === 'unreadCount') return `${params?.count ?? 0} unread`;
    if (key === 'empty') return 'No notifications yet';
    return key;
  },
}));

// Freeze markAllRead as a no-op so unreadCount stays at 1 during assertions.
// The hook itself is tested in useNotificationCount.test.ts.
vi.mock('../../../src/hooks/useNotifications', () => ({
  useNotifications: () => ({
    items: [
      { id: 'n1', text: 'Your last check-in showed a rising urge. You handled it — well done.', timestamp: '', read: false },
      { id: 'n2', text: 'New pattern detected: urges are higher on weekday evenings.', timestamp: '', read: true },
      { id: 'n3', text: 'Your resilience streak is growing. Keep going.', timestamp: '', read: true },
    ],
    unreadCount: 1,
    markAllRead: vi.fn(),
    prefs: {
      pushEnabled: false, emailEnabled: true, nudgeFrequency: 'medium' as const,
      setPushEnabled: vi.fn(), setEmailEnabled: vi.fn(), setNudgeFrequency: vi.fn(),
    },
  }),
}));

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
// 3–8. Open state — structure and stub notifications
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

  it('does not render empty-state when stub items exist', () => {
    renderDrawer();
    expect(screen.queryByText('No notifications yet')).toBeNull();
  });

  it('renders the drawer title "Notifications"', () => {
    renderDrawer();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  it('renders "1 unread" description (stub has 1 unread item)', () => {
    renderDrawer();
    // notificationsStubs has 1 unread item (n1), so unreadCount === 1
    expect(screen.getByText(/1 unread/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 9. Close button → onClose callback
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
  it('open drawer has no critical a11y violations', async () => {
    renderDrawer();
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
