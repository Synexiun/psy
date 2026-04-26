/**
 * Design tokens — Quiet Strength palette.
 * CSS at apps/web-app/src/app/globals.css is the source of truth.
 * This file re-exports CSS variable NAMES so TypeScript consumers can
 * reference tokens type-safely (e.g., colors.accent.bronze →
 * "var(--color-accent-bronze)").
 */

export const colors = {
  surface: {
    primary:   'var(--color-surface-primary)',
    secondary: 'var(--color-surface-secondary)',
    tertiary:  'var(--color-surface-tertiary)',
    overlay:   'var(--color-surface-overlay)',
  },
  ink: {
    primary:    'var(--color-ink-primary)',
    secondary:  'var(--color-ink-secondary)',
    tertiary:   'var(--color-ink-tertiary)',
    quaternary: 'var(--color-ink-quaternary)',
  },
  accent: {
    bronze:     'var(--color-accent-bronze)',
    bronzeSoft: 'var(--color-accent-bronze-soft)',
    teal:       'var(--color-accent-teal)',
    tealSoft:   'var(--color-accent-teal-soft)',
  },
  signal: {
    stable:  'var(--color-signal-stable)',
    warning: 'var(--color-signal-warning)',
    crisis:  'var(--color-signal-crisis)',
  },
  border: {
    subtle:   'var(--color-border-subtle)',
    emphasis: 'var(--color-border-emphasis)',
  },
} as const;

export const fonts = {
  body:    'var(--font-body)',
  display: 'var(--font-display)',
  fa:      'var(--font-fa)',
} as const;

export const motion = {
  instant:    'var(--motion-instant)',
  fast:       'var(--motion-fast)',
  base:       'var(--motion-base)',
  slow:       'var(--motion-slow)',
  deliberate: 'var(--motion-deliberate)',
} as const;

export const easing = {
  default:    'var(--ease-default)',
  decelerate: 'var(--ease-decelerate)',
  accelerate: 'var(--ease-accelerate)',
  organic:    'var(--ease-organic)',
} as const;

export const textScale = {
  display: {
    '2xl': 'var(--text-display-2xl)',
    xl:    'var(--text-display-xl)',
    lg:    'var(--text-display-lg)',
    md:    'var(--text-display-md)',
  },
  body: {
    lg: 'var(--text-body-lg)',
    md: 'var(--text-body-md)',
    sm: 'var(--text-body-sm)',
    xs: 'var(--text-body-xs)',
  },
} as const;

export type Tokens = {
  colors: typeof colors;
  fonts: typeof fonts;
  motion: typeof motion;
  easing: typeof easing;
  textScale: typeof textScale;
};
