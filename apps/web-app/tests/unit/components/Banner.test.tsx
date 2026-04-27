'use client';
/**
 * Contract tests for packages/design-system/src/primitives/Banner.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage targets (17 cases):
 *  1.  Default render: message visible
 *  2.  variant='info': bg-surface-secondary class on root
 *  3.  variant='warning': bg-amber-50 class on root
 *  4.  variant='error': bg-red-50 class on root
 *  5.  Dismiss button visible by default
 *  6.  Clicking dismiss hides banner (uncontrolled)
 *  7.  hideDismiss=true: no dismiss button
 *  8.  onDismiss callback called on dismiss click
 *  9.  Controlled: open=false renders null
 * 10.  Controlled: open=true renders message
 * 11.  Controlled: dismiss click calls onDismiss but does NOT hide the banner
 * 12.  dismissLabel used as sr-only text on dismiss button
 * 13.  role="status" on info variant root
 * 14.  role="status" on warning variant root
 * 15.  role="alert" on error variant root
 * 16.  Custom className applied to root
 * 17.  axe scan passes (color-contrast and region rules disabled)
 */

import type * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import { Banner } from '@disciplineos/design-system/primitives/Banner';

expect.extend(toHaveNoViolations);

// axe instance — color-contrast and region rules disabled (jsdom has no computed styles)
const axe = configureAxe({
  rules: {
    'color-contrast': { enabled: false },
    'region': { enabled: false },
  },
});

// ---------------------------------------------------------------------------
// 1. Default render: message visible
// ---------------------------------------------------------------------------

describe('Banner — default render', () => {
  it('renders the message text', () => {
    const { getByText } = render(
      <Banner message="PHQ-9 due tomorrow" />,
    );
    expect(getByText('PHQ-9 due tomorrow')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 2–4. Variant class names on root
// ---------------------------------------------------------------------------

describe('Banner — variant classes', () => {
  it("applies bg-surface-secondary for variant='info'", () => {
    const { container } = render(
      <Banner message="Info banner" variant="info" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('bg-surface-secondary')).toBe(true);
  });

  it("applies bg-amber-50 for variant='warning'", () => {
    const { container } = render(
      <Banner message="Warning banner" variant="warning" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('bg-amber-50')).toBe(true);
  });

  it("applies bg-red-50 for variant='error'", () => {
    const { container } = render(
      <Banner message="Error banner" variant="error" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('bg-red-50')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 5. Dismiss button visible by default
// ---------------------------------------------------------------------------

describe('Banner — dismiss button visibility', () => {
  it('renders a dismiss button by default', () => {
    const { container } = render(<Banner message="Banner" />);
    const button = container.querySelector('button');
    expect(button).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 6. Clicking dismiss button hides the banner (uncontrolled)
// ---------------------------------------------------------------------------

describe('Banner — uncontrolled dismiss', () => {
  it('hides the banner after dismiss button is clicked', () => {
    const { container, getByText } = render(
      <Banner message="Sync failed" />,
    );
    expect(getByText('Sync failed')).toBeTruthy();
    const button = container.querySelector('button');
    expect(button).not.toBeNull();
    fireEvent.click(button!);
    // After dismiss, the root element should be gone (null render)
    expect(container.firstElementChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 7. hideDismiss=true: no dismiss button
// ---------------------------------------------------------------------------

describe('Banner — hideDismiss', () => {
  it('does not render a dismiss button when hideDismiss=true', () => {
    const { container } = render(
      <Banner message="Permanent banner" hideDismiss={true} />,
    );
    const button = container.querySelector('button');
    expect(button).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 8. onDismiss callback called on dismiss click
// ---------------------------------------------------------------------------

describe('Banner — onDismiss callback', () => {
  it('calls onDismiss when dismiss button is clicked', () => {
    const onDismiss = vi.fn();
    const { container } = render(
      <Banner message="Sync failed" onDismiss={onDismiss} />,
    );
    const button = container.querySelector('button');
    expect(button).not.toBeNull();
    fireEvent.click(button!);
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// 9. Controlled: open=false renders null
// ---------------------------------------------------------------------------

describe('Banner — controlled open=false', () => {
  it('renders nothing when open=false', () => {
    const { container } = render(
      <Banner message="Hidden banner" open={false} />,
    );
    expect(container.firstElementChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 10. Controlled: open=true renders message
// ---------------------------------------------------------------------------

describe('Banner — controlled open=true', () => {
  it('renders the message when open=true', () => {
    const { getByText } = render(
      <Banner message="Visible controlled banner" open={true} />,
    );
    expect(getByText('Visible controlled banner')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 11. Controlled: dismiss click calls onDismiss but does NOT hide the banner
// ---------------------------------------------------------------------------

describe('Banner — controlled dismiss does not hide', () => {
  it('calls onDismiss but keeps banner visible in controlled mode', () => {
    const onDismiss = vi.fn();
    const { container, getByText } = render(
      <Banner message="Controlled banner" open={true} onDismiss={onDismiss} />,
    );
    const button = container.querySelector('button');
    expect(button).not.toBeNull();
    fireEvent.click(button!);
    // onDismiss must have been called
    expect(onDismiss).toHaveBeenCalledOnce();
    // But banner is still visible (consumer owns the state)
    expect(getByText('Controlled banner')).toBeTruthy();
    expect(container.firstElementChild).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 12. dismissLabel used as sr-only text
// ---------------------------------------------------------------------------

describe('Banner — dismissLabel', () => {
  it('uses the dismissLabel as sr-only text on the dismiss button', () => {
    const { getByText } = render(
      <Banner message="Banner" dismissLabel="Close notification" />,
    );
    const srText = getByText('Close notification');
    expect(srText).toBeTruthy();
    expect(srText.classList.contains('sr-only')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 13–15. Role attributes per variant
// ---------------------------------------------------------------------------

describe('Banner — ARIA role', () => {
  it('has role="status" for info variant', () => {
    const { container } = render(
      <Banner message="Info" variant="info" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('role')).toBe('status');
  });

  it('has role="status" for warning variant', () => {
    const { container } = render(
      <Banner message="Warning" variant="warning" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('role')).toBe('status');
  });

  it('has role="alert" for error variant', () => {
    const { container } = render(
      <Banner message="Error" variant="error" />,
    );
    const root = container.firstElementChild;
    expect(root?.getAttribute('role')).toBe('alert');
  });
});

// ---------------------------------------------------------------------------
// 16. Custom className applied to root
// ---------------------------------------------------------------------------

describe('Banner — custom className', () => {
  it('applies a custom className to the root element', () => {
    const { container } = render(
      <Banner message="Banner" className="my-custom-class" />,
    );
    const root = container.firstElementChild;
    expect(root?.classList.contains('my-custom-class')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 17. axe accessibility
// ---------------------------------------------------------------------------

describe('Banner — axe accessibility', () => {
  it('passes axe for info variant', async () => {
    render(<Banner message="PHQ-9 due tomorrow" variant="info" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe for warning variant', async () => {
    render(<Banner message="Offline mode active" variant="warning" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe for error variant', async () => {
    render(<Banner message="Sync failed — tap to retry" variant="error" />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('passes axe with hideDismiss=true', async () => {
    render(<Banner message="Permanent banner" hideDismiss={true} />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
