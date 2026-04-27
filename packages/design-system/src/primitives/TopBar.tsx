'use client';
/**
 * TopBar — Quiet Strength–tokenised top navigation bar primitive.
 *
 * Pure layout primitive. All interactivity is via callbacks; no internal
 * routing or theme management. RTL-aware: logical CSS properties throughout,
 * mobile wordmark centring corrected for both LTR and RTL via
 * `start-1/2 -translate-x-1/2 rtl:translate-x-1/2`.
 *
 * Sub-components (inline, not separately exported):
 *   HamburgerIcon  — 3-line SVG, 20×20, aria-hidden
 *   BellIcon       — bell SVG, 20×20, aria-hidden
 *   SunIcon        — sun SVG, 20×20, aria-hidden (shown when theme=dark → click→light)
 *   MoonIcon       — moon SVG, 20×20, aria-hidden (shown when theme=light → click→dark)
 *   OfflineDot     — 8×8 yellow dot with role-complementing aria-label
 *   BellButton     — bell + optional numeric badge
 *   LocaleSelect   — plain <select> (navigation control, no Radix)
 *   ThemeToggleButton
 *
 * Token usage:
 *   bg-surface-primary, border-border-subtle, text-ink-primary, text-ink-tertiary,
 *   ring-accent-bronze/30, accent-bronze, ease-default
 *
 * RTL centering note:
 *   `start-1/2` is the logical equivalent of `left: 50%` and maps to `right: 50%`
 *   in RTL. `-translate-x-1/2` is physical (CSS transform). In RTL the physical
 *   transform must be inverted, hence `rtl:translate-x-1/2`.
 *
 * Logical-CSS-only rule:
 *   ps-N/pe-N/ms-N/me-N/start-N/end-N/border-s/border-e — never pl-N/pr-N/ml-N/mr-N.
 *   block-direction top-N/bottom-N is fine.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

export interface LocaleOption {
  value: string;   // e.g. 'en', 'ar', 'fa'
  label: string;   // e.g. 'English', 'العربية', 'فارسی'
}

export interface TopBarProps {
  /** Wordmark — rendered in the start position on desktop, centered on mobile */
  wordmark?: React.ReactNode;
  /** Hamburger click handler — shows on mobile only */
  onMenuClick?: () => void;
  /** Unread notification count (0 = no badge) */
  bellCount?: number;
  onBellClick?: () => void;
  /** Current locale (e.g. 'en') */
  locale?: string;
  /** Available locale options */
  localeOptions?: LocaleOption[];
  onLocaleChange?: (locale: string) => void;
  /** Current theme */
  theme?: 'dark' | 'light';
  onThemeChange?: (theme: 'dark' | 'light') => void;
  /** Avatar element — slot for user avatar or initials badge */
  avatar?: React.ReactNode;
  /** When true, shows the offline indicator badge */
  isOffline?: boolean;
  /** Accessible label for the hamburger button */
  menuLabel?: string;
  /** Accessible label for the bell button */
  bellLabel?: string;
  /** Accessible label for the theme toggle */
  themeLabel?: string;
  className?: string;
}

// ---------------------------------------------------------------------------
// SVG icons (inline, no external dependency)
// ---------------------------------------------------------------------------

function HamburgerIcon(): React.ReactElement {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M3 5h14M3 10h14M3 15h14"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function BellIcon(): React.ReactElement {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 2a6 6 0 00-6 6v3l-1.5 2.5h15L16 11V8a6 6 0 00-6-6zM8 16a2 2 0 004 0"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SunIcon(): React.ReactElement {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MoonIcon(): React.ReactElement {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Sub-components (inline, not exported)
// ---------------------------------------------------------------------------

interface BellButtonProps {
  bellCount: number | undefined;
  onBellClick: () => void;
  bellLabel: string | undefined;
}

function BellButton({ bellCount, onBellClick, bellLabel }: BellButtonProps): React.ReactElement {
  return (
    <button
      onClick={onBellClick}
      aria-label={bellLabel ?? 'Notifications'}
      className="relative flex h-9 w-9 items-center justify-center rounded-md text-ink-tertiary transition-colors duration-fast ease-default hover:bg-surface-secondary hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
    >
      <BellIcon />
      {bellCount !== undefined && bellCount > 0 && (
        <span className="absolute -top-0.5 -end-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent-bronze text-[10px] font-bold text-surface-primary">
          {bellCount > 99 ? '99+' : bellCount}
        </span>
      )}
    </button>
  );
}

interface LocaleSelectProps {
  locale: string | undefined;
  localeOptions: LocaleOption[];
  onLocaleChange: ((locale: string) => void) | undefined;
}

function LocaleSelect({ locale, localeOptions, onLocaleChange }: LocaleSelectProps): React.ReactElement {
  return (
    <select
      value={locale}
      onChange={(e) => onLocaleChange?.(e.target.value)}
      aria-label="Select language"
      className="cursor-pointer rounded-md border-0 bg-transparent ps-2 pe-6 py-1 text-sm text-ink-tertiary focus:outline-none focus:ring-2 focus:ring-accent-bronze/30"
    >
      {localeOptions.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

interface ThemeToggleButtonProps {
  theme: 'dark' | 'light' | undefined;
  onThemeChange: (theme: 'dark' | 'light') => void;
  themeLabel: string | undefined;
}

function ThemeToggleButton({ theme, onThemeChange, themeLabel }: ThemeToggleButtonProps): React.ReactElement {
  const isDark = theme === 'dark';
  const defaultLabel = isDark ? 'Switch to light mode' : 'Switch to dark mode';

  return (
    <button
      onClick={() => onThemeChange(isDark ? 'light' : 'dark')}
      aria-label={themeLabel ?? defaultLabel}
      className="flex h-9 w-9 items-center justify-center rounded-md text-ink-tertiary transition-colors duration-fast ease-default hover:bg-surface-secondary hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function OfflineDot(): React.ReactElement {
  return (
    <span
      role="img"
      aria-label="Offline"
      title="You're offline"
      className="h-2 w-2 rounded-full bg-yellow-500"
    />
  );
}

// ---------------------------------------------------------------------------
// TopBar
// ---------------------------------------------------------------------------

export function TopBar({
  wordmark,
  onMenuClick,
  bellCount,
  onBellClick,
  locale,
  localeOptions,
  onLocaleChange,
  theme,
  onThemeChange,
  avatar,
  isOffline,
  menuLabel,
  bellLabel,
  themeLabel,
  className = '',
}: TopBarProps): React.ReactElement {
  return (
    <header
      className={`relative border-b border-border-subtle bg-surface-primary ${className}`.trim()}
    >
      <div className="flex h-14 items-center justify-between ps-4 pe-4 sm:ps-6 sm:pe-6">
        {/* Start group — hamburger (mobile only) + wordmark (desktop) */}
        <div className="flex items-center gap-3">
          {onMenuClick !== undefined && (
            <button
              onClick={onMenuClick}
              aria-label={menuLabel ?? 'Menu'}
              className="flex h-9 w-9 items-center justify-center rounded-md text-ink-tertiary transition-colors duration-fast ease-default hover:bg-surface-secondary hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 sm:hidden"
            >
              <HamburgerIcon />
            </button>
          )}
          {/* Wordmark: hidden on mobile (centered separately below), shown on sm+ */}
          <div className="hidden sm:block">{wordmark}</div>
        </div>

        {/* Center — wordmark on mobile only.
            start-1/2: logical 50% from the start edge (LTR: left edge, RTL: right edge).
            -translate-x-1/2: physical CSS transform that must be inverted in RTL.
            rtl:translate-x-1/2: corrects the physical transform for RTL layout.
        */}
        <div className="absolute start-1/2 -translate-x-1/2 rtl:translate-x-1/2 sm:hidden">
          {wordmark}
        </div>

        {/* End group — offline dot, bell, locale selector, theme toggle, avatar */}
        <div className="flex items-center gap-2">
          {isOffline === true && <OfflineDot />}
          {onBellClick !== undefined && (
            <BellButton
              bellCount={bellCount}
              onBellClick={onBellClick}
              bellLabel={bellLabel}
            />
          )}
          {localeOptions !== undefined && (
            <LocaleSelect
              locale={locale}
              localeOptions={localeOptions}
              onLocaleChange={onLocaleChange}
            />
          )}
          {onThemeChange !== undefined && (
            <ThemeToggleButton
              theme={theme}
              onThemeChange={onThemeChange}
              themeLabel={themeLabel}
            />
          )}
          {avatar !== undefined && avatar}
        </div>
      </div>
    </header>
  );
}
