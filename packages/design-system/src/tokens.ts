/**
 * Design tokens — single source of truth for mobile + web surfaces.
 * See Docs/Technicals/16_Web_Application.md §8 for the design-system spec.
 */

export const colors = {
  background: {
    base: 'hsl(0 0% 100%)',
    subtle: 'hsl(220 14% 96%)',
    inverse: 'hsl(222 47% 11%)',
  },
  foreground: {
    base: 'hsl(222 47% 11%)',
    muted: 'hsl(215 16% 47%)',
    inverse: 'hsl(0 0% 100%)',
  },
  accent: {
    primary: 'hsl(217 91% 60%)',
    calm: 'hsl(173 58% 39%)',
    warning: 'hsl(38 92% 50%)',
  },
  safety: {
    crisis: 'hsl(0 84% 60%)',
    crisisBg: 'hsl(0 84% 97%)',
  },
} as const;

export const typography = {
  fontFamily: {
    latin: 'var(--font-inter), system-ui, sans-serif',
    arabic: 'var(--font-plex-arabic), system-ui, sans-serif',
    persian: 'var(--font-vazirmatn), system-ui, sans-serif',
    mono: 'ui-monospace, Menlo, Consolas, monospace',
  },
  scaleMultiplier: {
    latin: 1.0,
    arabic: 1.15,
    persian: 1.15,
  },
  lineHeight: {
    latin: 1.5,
    arabic: 1.6,
    persian: 1.6,
  },
} as const;

export const space = {
  '2xs': '0.25rem',
  xs: '0.5rem',
  sm: '0.75rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
} as const;

export const radius = {
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  full: '9999px',
} as const;

export const motion = {
  duration: {
    instant: '75ms',
    fast: '150ms',
    base: '250ms',
    slow: '400ms',
    reflective: '700ms',
  },
  easing: {
    standard: 'cubic-bezier(0.2, 0, 0, 1)',
    entrance: 'cubic-bezier(0, 0, 0, 1)',
    exit: 'cubic-bezier(0.3, 0, 1, 1)',
  },
} as const;

export const safety = {
  crisisLaunchTargetMs: 800,
  crisisWarmTargetMs: 200,
  sosButtonMinTouchTargetPx: 56,
} as const;

export type Locale = 'en' | 'fr' | 'ar' | 'fa';

export const rtlLocales: ReadonlySet<Locale> = new Set(['ar', 'fa']);

export const isRtl = (locale: Locale): boolean => rtlLocales.has(locale);
