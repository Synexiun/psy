/**
 * Contract tests for packages/design-system/src/primitives/TopBar.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * TopBar is a pure layout primitive (no Radix, no portals). All elements
 * render synchronously into the DOM; no fireEvent delays or waitFor needed
 * for most assertions.
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 *   region         — TopBar is a <header> landmark but in the test harness it
 *                    is not embedded in a full page structure; axe flags isolated
 *                    landmark elements in minimal DOM as region violations.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { TopBar } from '@disciplineos/design-system/primitives/TopBar';
import type { LocaleOption } from '@disciplineos/design-system/primitives/TopBar';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const LOCALE_OPTIONS: LocaleOption[] = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Français' },
  { value: 'ar', label: 'العربية' },
  { value: 'fa', label: 'فارسی' },
];

function renderTopBar(props: Partial<React.ComponentProps<typeof TopBar>> = {}) {
  return render(<TopBar {...props} />);
}

// ---------------------------------------------------------------------------
// 1. Renders a <header> element
// ---------------------------------------------------------------------------

describe('TopBar — structure', () => {
  it('renders a <header> element', () => {
    const { container } = renderTopBar();
    expect(container.querySelector('header')).not.toBeNull();
  });

  it('header has role="banner" (implicit for <header> at page level)', () => {
    renderTopBar({ wordmark: <span>Logo</span> });
    // <header> outside a sectioning element has implicit role="banner"
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. Wordmark — desktop slot + mobile center slot
// ---------------------------------------------------------------------------

describe('TopBar — wordmark', () => {
  it('renders the wordmark in the desktop slot (hidden sm:block)', () => {
    const { container } = renderTopBar({ wordmark: <span>Discipline OS</span> });
    const desktopSlot = container.querySelector('.hidden.sm\\:block');
    expect(desktopSlot).not.toBeNull();
    expect(desktopSlot?.textContent).toBe('Discipline OS');
  });

  it('renders the wordmark in the mobile center slot', () => {
    const { container } = renderTopBar({ wordmark: <span>Discipline OS</span> });
    // Mobile center slot uses absolute positioning with start-1/2
    const mobileSlot = container.querySelector('.absolute.start-1\\/2');
    expect(mobileSlot).not.toBeNull();
    expect(mobileSlot?.textContent).toBe('Discipline OS');
  });

  it('renders the same wordmark content in both slots', () => {
    const { container } = renderTopBar({ wordmark: <span data-testid="wm">MyApp</span> });
    const allWm = container.querySelectorAll('[data-testid="wm"]');
    expect(allWm.length).toBe(2);
  });

  it('does not render wordmark slots when wordmark is omitted', () => {
    const { container } = renderTopBar();
    // Desktop slot exists but is empty; mobile slot still exists with no children
    const desktopSlot = container.querySelector('.hidden.sm\\:block');
    expect(desktopSlot?.textContent ?? '').toBe('');
  });
});

// ---------------------------------------------------------------------------
// 3. Hamburger button (onMenuClick)
// ---------------------------------------------------------------------------

describe('TopBar — hamburger (onMenuClick)', () => {
  it('renders a hamburger button when onMenuClick is provided', () => {
    renderTopBar({ onMenuClick: vi.fn() });
    expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument();
  });

  it('does not render a hamburger button when onMenuClick is omitted', () => {
    renderTopBar();
    expect(screen.queryByRole('button', { name: 'Menu' })).toBeNull();
  });

  it('calls onMenuClick when hamburger is clicked', () => {
    const handler = vi.fn();
    renderTopBar({ onMenuClick: handler });
    fireEvent.click(screen.getByRole('button', { name: 'Menu' }));
    expect(handler).toHaveBeenCalledOnce();
  });

  it('hamburger button has sm:hidden class (mobile-only visibility)', () => {
    const { container } = renderTopBar({ onMenuClick: vi.fn() });
    const btn = container.querySelector('button[aria-label="Menu"]');
    expect(btn?.className).toContain('sm:hidden');
  });
});

// ---------------------------------------------------------------------------
// 4 & 5 & 6. Bell button + badge
// ---------------------------------------------------------------------------

describe('TopBar — bell button and badge', () => {
  it('renders a bell button when onBellClick is provided', () => {
    renderTopBar({ onBellClick: vi.fn() });
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument();
  });

  it('does not render a bell button when onBellClick is omitted', () => {
    renderTopBar();
    expect(screen.queryByRole('button', { name: 'Notifications' })).toBeNull();
  });

  it('calls onBellClick when bell button is clicked', () => {
    const handler = vi.fn();
    renderTopBar({ onBellClick: handler });
    fireEvent.click(screen.getByRole('button', { name: 'Notifications' }));
    expect(handler).toHaveBeenCalledOnce();
  });

  it('shows badge with correct count when bellCount > 0', () => {
    const { container } = renderTopBar({ onBellClick: vi.fn(), bellCount: 5 });
    // Badge is a span inside the bell button
    const badge = container.querySelector('button[aria-label="Notifications"] span');
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toBe('5');
  });

  it('does not render a badge when bellCount is 0', () => {
    const { container } = renderTopBar({ onBellClick: vi.fn(), bellCount: 0 });
    const badge = container.querySelector('button[aria-label="Notifications"] span');
    expect(badge).toBeNull();
  });

  it('does not render a badge when bellCount is omitted', () => {
    const { container } = renderTopBar({ onBellClick: vi.fn() });
    const badge = container.querySelector('button[aria-label="Notifications"] span');
    expect(badge).toBeNull();
  });

  it('shows "99+" in badge when bellCount > 99', () => {
    const { container } = renderTopBar({ onBellClick: vi.fn(), bellCount: 150 });
    const badge = container.querySelector('button[aria-label="Notifications"] span');
    expect(badge?.textContent).toBe('99+');
  });

  it('shows "99+" at exactly 100', () => {
    const { container } = renderTopBar({ onBellClick: vi.fn(), bellCount: 100 });
    const badge = container.querySelector('button[aria-label="Notifications"] span');
    expect(badge?.textContent).toBe('99+');
  });

  it('shows exact count at 99', () => {
    const { container } = renderTopBar({ onBellClick: vi.fn(), bellCount: 99 });
    const badge = container.querySelector('button[aria-label="Notifications"] span');
    expect(badge?.textContent).toBe('99');
  });
});

// ---------------------------------------------------------------------------
// 7. Locale selector
// ---------------------------------------------------------------------------

describe('TopBar — locale selector', () => {
  it('renders a <select> when localeOptions is provided', () => {
    const { container } = renderTopBar({ localeOptions: LOCALE_OPTIONS });
    expect(container.querySelector('select')).not.toBeNull();
  });

  it('does not render a <select> when localeOptions is omitted', () => {
    const { container } = renderTopBar();
    expect(container.querySelector('select')).toBeNull();
  });

  it('select has the correct value when locale is provided', () => {
    const { container } = renderTopBar({
      localeOptions: LOCALE_OPTIONS,
      locale: 'ar',
    });
    const select = container.querySelector('select') as HTMLSelectElement;
    expect(select.value).toBe('ar');
  });

  it('renders all locale options as <option> elements', () => {
    const { container } = renderTopBar({ localeOptions: LOCALE_OPTIONS });
    const options = container.querySelectorAll('select option');
    expect(options.length).toBe(4);
  });

  it('calls onLocaleChange with the new locale when selection changes', () => {
    const handler = vi.fn();
    const { container } = renderTopBar({
      localeOptions: LOCALE_OPTIONS,
      locale: 'en',
      onLocaleChange: handler,
    });
    const select = container.querySelector('select') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'fr' } });
    expect(handler).toHaveBeenCalledWith('fr');
  });
});

// ---------------------------------------------------------------------------
// 8. Theme toggle button
// ---------------------------------------------------------------------------

describe('TopBar — theme toggle', () => {
  it('renders the theme toggle when onThemeChange is provided', () => {
    renderTopBar({ onThemeChange: vi.fn(), theme: 'light' });
    expect(screen.getByRole('button', { name: 'Switch to dark mode' })).toBeInTheDocument();
  });

  it('does not render the theme toggle when onThemeChange is omitted', () => {
    renderTopBar();
    expect(screen.queryByRole('button', { name: /switch to/i })).toBeNull();
  });

  it('shows sun icon (aria label = "Switch to light mode") when theme is dark', () => {
    renderTopBar({ onThemeChange: vi.fn(), theme: 'dark' });
    expect(screen.getByRole('button', { name: 'Switch to light mode' })).toBeInTheDocument();
  });

  it('shows moon icon (aria label = "Switch to dark mode") when theme is light', () => {
    renderTopBar({ onThemeChange: vi.fn(), theme: 'light' });
    expect(screen.getByRole('button', { name: 'Switch to dark mode' })).toBeInTheDocument();
  });

  it('calls onThemeChange with "light" when clicked in dark mode', () => {
    const handler = vi.fn();
    renderTopBar({ onThemeChange: handler, theme: 'dark' });
    fireEvent.click(screen.getByRole('button', { name: 'Switch to light mode' }));
    expect(handler).toHaveBeenCalledWith('light');
  });

  it('calls onThemeChange with "dark" when clicked in light mode', () => {
    const handler = vi.fn();
    renderTopBar({ onThemeChange: handler, theme: 'light' });
    fireEvent.click(screen.getByRole('button', { name: 'Switch to dark mode' }));
    expect(handler).toHaveBeenCalledWith('dark');
  });

  it('calls onThemeChange with "light" when theme is undefined (treated as non-dark)', () => {
    const handler = vi.fn();
    renderTopBar({ onThemeChange: handler });
    // theme undefined → isDark=false → clicking toggles to 'dark'
    fireEvent.click(screen.getByRole('button', { name: 'Switch to dark mode' }));
    expect(handler).toHaveBeenCalledWith('dark');
  });
});

// ---------------------------------------------------------------------------
// 9. Offline indicator
// ---------------------------------------------------------------------------

describe('TopBar — offline indicator', () => {
  it('shows offline indicator when isOffline is true', () => {
    renderTopBar({ isOffline: true });
    // The span has role="img" and aria-label="Offline"
    const offlineDot = screen.getByRole('img', { name: 'Offline' });
    expect(offlineDot).toBeInTheDocument();
  });

  it('offline indicator has aria-label="Offline"', () => {
    renderTopBar({ isOffline: true });
    expect(document.querySelector('[aria-label="Offline"]')).not.toBeNull();
  });

  it('offline indicator has title "You\'re offline"', () => {
    renderTopBar({ isOffline: true });
    const dot = document.querySelector('[aria-label="Offline"]');
    expect(dot?.getAttribute('title')).toBe("You're offline");
  });

  it('does not show offline indicator when isOffline is false', () => {
    renderTopBar({ isOffline: false });
    expect(document.querySelector('[aria-label="Offline"]')).toBeNull();
  });

  it('does not show offline indicator when isOffline is omitted', () => {
    renderTopBar();
    expect(document.querySelector('[aria-label="Offline"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 10. Custom aria-labels (menuLabel, bellLabel, themeLabel)
// ---------------------------------------------------------------------------

describe('TopBar — custom aria-labels', () => {
  it('uses menuLabel as aria-label for the hamburger button', () => {
    renderTopBar({ onMenuClick: vi.fn(), menuLabel: 'Open navigation' });
    expect(screen.getByRole('button', { name: 'Open navigation' })).toBeInTheDocument();
  });

  it('uses bellLabel as aria-label for the bell button', () => {
    renderTopBar({ onBellClick: vi.fn(), bellLabel: 'See alerts' });
    expect(screen.getByRole('button', { name: 'See alerts' })).toBeInTheDocument();
  });

  it('uses themeLabel as aria-label for the theme toggle button', () => {
    renderTopBar({ onThemeChange: vi.fn(), themeLabel: 'Toggle appearance' });
    expect(screen.getByRole('button', { name: 'Toggle appearance' })).toBeInTheDocument();
  });

  it('falls back to "Menu" when menuLabel is omitted', () => {
    renderTopBar({ onMenuClick: vi.fn() });
    expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument();
  });

  it('falls back to "Notifications" when bellLabel is omitted', () => {
    renderTopBar({ onBellClick: vi.fn() });
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Avatar slot
// ---------------------------------------------------------------------------

describe('TopBar — avatar slot', () => {
  it('renders avatar element when avatar is provided', () => {
    renderTopBar({ avatar: <img src="/avatar.png" alt="User avatar" /> });
    expect(screen.getByRole('img', { name: 'User avatar' })).toBeInTheDocument();
  });

  it('does not render avatar slot when avatar is omitted', () => {
    renderTopBar();
    expect(screen.queryByRole('img')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 11. RTL context
// ---------------------------------------------------------------------------

describe('TopBar — RTL context', () => {
  it('renders without errors in dir="rtl" context', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <TopBar
            wordmark={<span>Discipline OS</span>}
            onMenuClick={vi.fn()}
            onBellClick={vi.fn()}
            bellCount={3}
            localeOptions={LOCALE_OPTIONS}
            locale="ar"
            theme="dark"
            onThemeChange={vi.fn()}
            isOffline={true}
          />
        </div>,
      ),
    ).not.toThrow();
  });

  it('mobile center slot has rtl:translate-x-1/2 class for RTL-correct centering', () => {
    const { container } = render(
      <div dir="rtl">
        <TopBar wordmark={<span>Logo</span>} />
      </div>,
    );
    const mobileSlot = container.querySelector('.absolute.start-1\\/2');
    expect(mobileSlot?.className).toContain('rtl:translate-x-1/2');
  });

  it('does not use physical pl-/pr- classes anywhere in RTL render', () => {
    const { container } = render(
      <div dir="rtl">
        <TopBar
          wordmark={<span>Logo</span>}
          onMenuClick={vi.fn()}
          onBellClick={vi.fn()}
          localeOptions={LOCALE_OPTIONS}
          locale="ar"
          theme="dark"
          onThemeChange={vi.fn()}
        />
      </div>,
    );
    const header = container.querySelector('header');
    const allClasses = header?.innerHTML ?? '';
    // physical padding classes should not appear in TopBar's own elements
    expect(allClasses).not.toMatch(/\bpl-\d|\bpr-\d/);
  });

  it('renders Arabic locale option text correctly', () => {
    render(
      <div dir="rtl">
        <TopBar localeOptions={LOCALE_OPTIONS} locale="ar" />
      </div>,
    );
    expect(screen.getByText('العربية')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('TopBar — className passthrough', () => {
  it('merges additional className onto the header element', () => {
    const { container } = renderTopBar({ className: 'custom-topbar-class' });
    const header = container.querySelector('header');
    expect(header?.className).toContain('custom-topbar-class');
  });

  it('header className is trimmed (no leading/trailing whitespace)', () => {
    const { container } = renderTopBar({ className: '' });
    const header = container.querySelector('header');
    expect(header?.className).not.toMatch(/^\s|\s$/);
  });
});

// ---------------------------------------------------------------------------
// 12. axe accessibility
// ---------------------------------------------------------------------------

const axe = configureAxe({
  rules: {
    // color-contrast requires computed styles not available in jsdom
    'color-contrast': { enabled: false },
    // region — TopBar is a <header> landmark; axe flags it in minimal DOM harness
    // that lacks a full page context (no <main>, etc.). This is a test-harness
    // limitation, not a production violation.
    'region': { enabled: false },
  },
});

describe('TopBar — axe accessibility', () => {
  it('bare TopBar has no a11y violations', async () => {
    renderTopBar();
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('TopBar with all props has no a11y violations', async () => {
    renderTopBar({
      wordmark: <span>Discipline OS</span>,
      onMenuClick: vi.fn(),
      bellCount: 5,
      onBellClick: vi.fn(),
      localeOptions: LOCALE_OPTIONS,
      locale: 'en',
      onLocaleChange: vi.fn(),
      theme: 'dark',
      onThemeChange: vi.fn(),
      avatar: <span aria-label="User initials">JD</span>,
      isOffline: true,
      menuLabel: 'Open menu',
      bellLabel: 'Notifications (5)',
      themeLabel: 'Switch to light mode',
    });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('TopBar offline variant has no a11y violations', async () => {
    renderTopBar({ isOffline: true });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('TopBar in RTL context has no a11y violations', async () => {
    render(
      <div dir="rtl" lang="ar">
        <TopBar
          wordmark={<span>Discipline OS</span>}
          onBellClick={vi.fn()}
          bellCount={2}
          localeOptions={LOCALE_OPTIONS}
          locale="ar"
          theme="light"
          onThemeChange={vi.fn()}
        />
      </div>,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
