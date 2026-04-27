/**
 * Contract tests for packages/design-system/src/primitives/BottomNav.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * BottomNav is a pure layout primitive (no Radix, no portals). All elements
 * render synchronously into the DOM; no fireEvent delays or waitFor needed.
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { BottomNav } from '@disciplineos/design-system/primitives/BottomNav';
import type { BottomNavItem } from '@disciplineos/design-system/primitives/BottomNav';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeIcon(label: string): React.ReactElement {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <rect width="24" height="24" fill="currentColor" opacity="0.2" />
      <text x="12" y="16" fontSize="8" textAnchor="middle" fill="currentColor">
        {label}
      </text>
    </svg>
  );
}

const FIVE_ITEMS: BottomNavItem[] = [
  { value: 'home', label: 'Home', icon: makeIcon('H') },
  { value: 'checkin', label: 'Check-in', icon: makeIcon('C') },
  { value: 'tools', label: 'Tools', icon: makeIcon('T') },
  { value: 'journal', label: 'Journal', icon: makeIcon('J') },
  { value: 'crisis', label: 'Crisis', icon: makeIcon('!'), crisis: true },
];

const FOUR_ITEMS: BottomNavItem[] = FIVE_ITEMS.slice(0, 4);

function renderNav(props: Partial<React.ComponentProps<typeof BottomNav>> = {}) {
  return render(<BottomNav items={FIVE_ITEMS} {...props} />);
}

// ---------------------------------------------------------------------------
// 1. Renders a <nav> with aria-label
// ---------------------------------------------------------------------------

describe('BottomNav — structure', () => {
  it('renders a <nav> element', () => {
    const { container } = renderNav();
    expect(container.querySelector('nav')).not.toBeNull();
  });

  it('nav has aria-label="Main navigation"', () => {
    renderNav();
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. Renders correct number of items
// ---------------------------------------------------------------------------

describe('BottomNav — item count', () => {
  it('renders exactly 5 buttons when given 5 items', () => {
    renderNav();
    expect(screen.getAllByRole('button').length).toBe(5);
  });

  it('renders exactly 4 buttons when given 4 items', () => {
    renderNav({ items: FOUR_ITEMS });
    expect(screen.getAllByRole('button').length).toBe(4);
  });

  it('renders a button for each item with the correct aria-label', () => {
    renderNav();
    for (const item of FIVE_ITEMS) {
      expect(screen.getByRole('button', { name: item.label })).toBeInTheDocument();
    }
  });
});

// ---------------------------------------------------------------------------
// 3. aria-current="page" on active item; absent on others
// ---------------------------------------------------------------------------

describe('BottomNav — active state (aria-current)', () => {
  it('sets aria-current="page" on the active item', () => {
    renderNav({ activeValue: 'home' });
    const homeBtn = screen.getByRole('button', { name: 'Home' });
    expect(homeBtn).toHaveAttribute('aria-current', 'page');
  });

  it('does not set aria-current on inactive items', () => {
    renderNav({ activeValue: 'home' });
    const checkinBtn = screen.getByRole('button', { name: 'Check-in' });
    expect(checkinBtn).not.toHaveAttribute('aria-current');
  });

  it('no aria-current attributes when activeValue is omitted', () => {
    const { container } = renderNav();
    const withCurrent = container.querySelectorAll('[aria-current]');
    expect(withCurrent.length).toBe(0);
  });

  it('active item has accent-bronze color class', () => {
    renderNav({ activeValue: 'home' });
    const homeBtn = screen.getByRole('button', { name: 'Home' });
    expect(homeBtn.className).toContain('text-accent-bronze');
  });

  it('inactive item has ink-tertiary color class', () => {
    renderNav({ activeValue: 'home' });
    const toolsBtn = screen.getByRole('button', { name: 'Tools' });
    expect(toolsBtn.className).toContain('text-ink-tertiary');
  });
});

// ---------------------------------------------------------------------------
// 4. onItemClick called with correct value on click
// ---------------------------------------------------------------------------

describe('BottomNav — onItemClick', () => {
  it('calls onItemClick with correct value when a button is clicked', () => {
    const handler = vi.fn();
    renderNav({ onItemClick: handler });
    fireEvent.click(screen.getByRole('button', { name: 'Home' }));
    expect(handler).toHaveBeenCalledOnce();
    expect(handler).toHaveBeenCalledWith('home');
  });

  it('calls onItemClick with value for each item', () => {
    const handler = vi.fn();
    renderNav({ onItemClick: handler });
    for (const item of FIVE_ITEMS) {
      handler.mockClear();
      fireEvent.click(screen.getByRole('button', { name: item.label }));
      expect(handler).toHaveBeenCalledWith(item.value);
    }
  });

  it('does not throw when onItemClick is omitted', () => {
    renderNav({ onItemClick: undefined });
    expect(() => fireEvent.click(screen.getByRole('button', { name: 'Home' }))).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// 5. Crisis item: oxblood class, never disabled
// ---------------------------------------------------------------------------

describe('BottomNav — crisis item', () => {
  it('crisis item has oxblood text color class', () => {
    renderNav();
    const crisisBtn = screen.getByRole('button', { name: 'Crisis' });
    expect(crisisBtn.className).toContain('text-[#8B0000]');
  });

  it('crisis item is not disabled even when item.disabled=true', () => {
    const items: BottomNavItem[] = [
      ...FOUR_ITEMS,
      { value: 'crisis', label: 'Crisis', icon: makeIcon('!'), crisis: true, disabled: true },
    ];
    renderNav({ items });
    const crisisBtn = screen.getByRole('button', { name: 'Crisis' });
    expect(crisisBtn).not.toBeDisabled();
  });

  it('crisis item has min-h-[56px] class for 56 px touch target', () => {
    renderNav();
    const crisisBtn = screen.getByRole('button', { name: 'Crisis' });
    expect(crisisBtn.className).toContain('min-h-[56px]');
  });

  it('crisis item can still be clicked when item.disabled=true', () => {
    const handler = vi.fn();
    const items: BottomNavItem[] = [
      ...FOUR_ITEMS,
      { value: 'crisis', label: 'Crisis', icon: makeIcon('!'), crisis: true, disabled: true },
    ];
    renderNav({ items, onItemClick: handler });
    fireEvent.click(screen.getByRole('button', { name: 'Crisis' }));
    expect(handler).toHaveBeenCalledWith('crisis');
  });
});

// ---------------------------------------------------------------------------
// 6. Non-crisis disabled item
// ---------------------------------------------------------------------------

describe('BottomNav — disabled non-crisis item', () => {
  it('non-crisis disabled item has the disabled attribute', () => {
    const items: BottomNavItem[] = [
      { value: 'home', label: 'Home', icon: makeIcon('H'), disabled: true },
      ...FIVE_ITEMS.slice(1),
    ];
    renderNav({ items });
    const homeBtn = screen.getByRole('button', { name: 'Home' });
    expect(homeBtn).toBeDisabled();
  });

  it('non-crisis non-disabled item does not have the disabled attribute', () => {
    renderNav();
    const homeBtn = screen.getByRole('button', { name: 'Home' });
    expect(homeBtn).not.toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// 7. Active dot: rendered for active item, absent for inactive
// ---------------------------------------------------------------------------

describe('BottomNav — active indicator dot', () => {
  it('active item has a visible dot (not bg-transparent)', () => {
    renderNav({ activeValue: 'home' });
    const homeBtn = screen.getByRole('button', { name: 'Home' });
    // The dot is the first aria-hidden span inside the button
    const dot = homeBtn.querySelector('span[aria-hidden="true"]');
    expect(dot).not.toBeNull();
    expect(dot?.className).not.toContain('bg-transparent');
    expect(dot?.className).toContain('bg-accent-bronze');
  });

  it('inactive item dot has bg-transparent class', () => {
    renderNav({ activeValue: 'home' });
    const toolsBtn = screen.getByRole('button', { name: 'Tools' });
    const dot = toolsBtn.querySelector('span[aria-hidden="true"]');
    expect(dot?.className).toContain('bg-transparent');
  });

  it('crisis active item dot has oxblood color', () => {
    renderNav({ activeValue: 'crisis' });
    const crisisBtn = screen.getByRole('button', { name: 'Crisis' });
    const dot = crisisBtn.querySelector('span[aria-hidden="true"]');
    expect(dot?.className).toContain('bg-[#8B0000]');
  });

  it('no active dot when activeValue is not set', () => {
    renderNav();
    for (const item of FIVE_ITEMS) {
      const btn = screen.getByRole('button', { name: item.label });
      const dot = btn.querySelector('span[aria-hidden="true"]');
      expect(dot?.className).toContain('bg-transparent');
    }
  });
});

// ---------------------------------------------------------------------------
// 8. items.length > 5 — dev-mode console.warn
// ---------------------------------------------------------------------------

describe('BottomNav — max items guard', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('fires console.warn when more than 5 items are provided', () => {
    const sixItems: BottomNavItem[] = [
      ...FIVE_ITEMS,
      { value: 'extra', label: 'Extra', icon: makeIcon('E') },
    ];
    // NODE_ENV is 'test' (not 'production') so the guard fires
    renderNav({ items: sixItems });
    expect(warnSpy).toHaveBeenCalledOnce();
    expect(warnSpy.mock.calls[0]?.[0]).toContain('[BottomNav]');
    expect(warnSpy.mock.calls[0]?.[0]).toContain('5');
  });

  it('does not warn when exactly 5 items are provided', () => {
    renderNav({ items: FIVE_ITEMS });
    expect(warnSpy).not.toHaveBeenCalled();
  });

  it('does not warn when fewer than 5 items are provided', () => {
    renderNav({ items: FOUR_ITEMS });
    expect(warnSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 9. RTL: renders without errors in dir="rtl" wrapper
// ---------------------------------------------------------------------------

describe('BottomNav — RTL context', () => {
  it('renders without errors in a dir="rtl" wrapper', () => {
    expect(() =>
      render(
        <div dir="rtl" lang="ar">
          <BottomNav items={FIVE_ITEMS} activeValue="home" />
        </div>,
      ),
    ).not.toThrow();
  });

  it('all buttons are still present in RTL context', () => {
    render(
      <div dir="rtl" lang="ar">
        <BottomNav items={FIVE_ITEMS} activeValue="home" />
      </div>,
    );
    expect(screen.getAllByRole('button').length).toBe(5);
  });

  it('does not use physical pl-/pr- classes in RTL render', () => {
    const { container } = render(
      <div dir="rtl" lang="ar">
        <BottomNav items={FIVE_ITEMS} activeValue="home" />
      </div>,
    );
    const nav = container.querySelector('nav');
    const allClasses = nav?.innerHTML ?? '';
    expect(allClasses).not.toMatch(/\bpl-\d|\bpr-\d/);
  });
});

// ---------------------------------------------------------------------------
// 10. href prop — renders <a> instead of <button>
// ---------------------------------------------------------------------------

describe('BottomNav — href rendering', () => {
  it('renders as <a> when href is provided', () => {
    const items: BottomNavItem[] = [
      { value: 'home', label: 'Home', icon: makeIcon('H'), href: '/home' },
    ];
    render(<BottomNav items={items} />);
    const link = screen.getByRole('link', { name: /home/i });
    expect(link).toBeInTheDocument();
    expect(link.tagName).toBe('A');
    expect(link).toHaveAttribute('href', '/home');
  });

  it('renders as <button> when href is omitted', () => {
    const items: BottomNavItem[] = [
      { value: 'home', label: 'Home', icon: makeIcon('H') },
    ];
    render(<BottomNav items={items} />);
    const btn = screen.getByRole('button', { name: /home/i });
    expect(btn).toBeInTheDocument();
    expect(btn.tagName).toBe('BUTTON');
    expect(btn).not.toHaveAttribute('href');
  });

  it('<a> item carries aria-current="page" when active', () => {
    const items: BottomNavItem[] = [
      { value: 'home', label: 'Home', icon: makeIcon('H'), href: '/home' },
    ];
    render(<BottomNav items={items} activeValue="home" />);
    const link = screen.getByRole('link', { name: /home/i });
    expect(link).toHaveAttribute('aria-current', 'page');
  });

  it('<a> item does not carry aria-current when inactive', () => {
    const items: BottomNavItem[] = [
      { value: 'home', label: 'Home', icon: makeIcon('H'), href: '/home' },
      { value: 'tools', label: 'Tools', icon: makeIcon('T'), href: '/tools' },
    ];
    render(<BottomNav items={items} activeValue="tools" />);
    const homeLink = screen.getByRole('link', { name: /home/i });
    expect(homeLink).not.toHaveAttribute('aria-current');
  });
});

const axe = configureAxe({
  rules: {
    // color-contrast requires computed styles not available in jsdom
    'color-contrast': { enabled: false },
  },
});

describe('BottomNav — axe accessibility', () => {
  it('basic nav (no activeValue) has no a11y violations', async () => {
    renderNav();
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('nav with activeValue has no a11y violations', async () => {
    renderNav({ activeValue: 'tools' });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('nav with crisis item active has no a11y violations', async () => {
    renderNav({ activeValue: 'crisis' });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('nav in RTL context has no a11y violations', async () => {
    render(
      <div dir="rtl" lang="ar">
        <BottomNav items={FIVE_ITEMS} activeValue="crisis" />
      </div>,
    );
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
