/**
 * Unit tests for mobile design tokens.
 *
 * Design tokens look like static data but the urgency-state colors
 * (calm, elevated, crisis) are clinically load-bearing: they determine how
 * urgency states are rendered on mobile. A silent color regression here would
 * visually misrepresent a user's clinical state — e.g., turning 'crisis' green.
 *
 * These tests pin:
 * - Exact hex values for clinical urgency colors (calm/elevated/crisis)
 * - Monotonic spacing scale (xs < sm < md < lg < xl < xxl)
 * - Positive radius values with pill >> lg
 * - Non-empty font family names
 * - Positive font sizes
 */

import { describe, it, expect } from '@jest/globals';
import { color, space, radius, font, size } from './tokens';

// ---------------------------------------------------------------------------
// color tokens
// ---------------------------------------------------------------------------

describe('color tokens — clinical urgency colors', () => {
  it('crisis is red (#D14B3E)', () => {
    expect(color.crisis).toBe('#D14B3E');
  });

  it('elevated is amber (#E8A85B)', () => {
    expect(color.elevated).toBe('#E8A85B');
  });

  it('calm is teal (#6FB3B8)', () => {
    expect(color.calm).toBe('#6FB3B8');
  });

  it('crisis is visually distinct from elevated (different hue family)', () => {
    expect(color.crisis).not.toBe(color.elevated);
  });

  it('crisis is visually distinct from calm', () => {
    expect(color.crisis).not.toBe(color.calm);
  });
});

describe('color tokens — base palette', () => {
  it('graphite is a dark color (starts with #1)', () => {
    expect(color.graphite).toMatch(/^#[01]/i);
  });

  it('offWhite is a light color (starts with #F)', () => {
    expect(color.offWhite).toMatch(/^#[Ff]/i);
  });

  it('all color values are valid 6-digit hex strings', () => {
    for (const [, value] of Object.entries(color)) {
      expect(value).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });

  it('has exactly 9 color tokens', () => {
    expect(Object.keys(color)).toHaveLength(9);
  });

  it('all color names are unique', () => {
    const values = Object.values(color);
    expect(new Set(values).size).toBe(values.length);
  });
});

// ---------------------------------------------------------------------------
// space tokens
// ---------------------------------------------------------------------------

describe('space tokens — monotonic scale', () => {
  it('xs is 4', () => {
    expect(space.xs).toBe(4);
  });

  it('sm is 8', () => {
    expect(space.sm).toBe(8);
  });

  it('md is 16', () => {
    expect(space.md).toBe(16);
  });

  it('lg is 24', () => {
    expect(space.lg).toBe(24);
  });

  it('xl is 32', () => {
    expect(space.xl).toBe(32);
  });

  it('xxl is 48', () => {
    expect(space.xxl).toBe(48);
  });

  it('scale is strictly increasing: xs < sm < md < lg < xl < xxl', () => {
    expect(space.xs).toBeLessThan(space.sm);
    expect(space.sm).toBeLessThan(space.md);
    expect(space.md).toBeLessThan(space.lg);
    expect(space.lg).toBeLessThan(space.xl);
    expect(space.xl).toBeLessThan(space.xxl);
  });

  it('all space values are positive', () => {
    for (const value of Object.values(space)) {
      expect(value).toBeGreaterThan(0);
    }
  });

  it('has exactly 6 space tokens', () => {
    expect(Object.keys(space)).toHaveLength(6);
  });
});

// ---------------------------------------------------------------------------
// radius tokens
// ---------------------------------------------------------------------------

describe('radius tokens', () => {
  it('sm is 6', () => {
    expect(radius.sm).toBe(6);
  });

  it('md is 12', () => {
    expect(radius.md).toBe(12);
  });

  it('lg is 20', () => {
    expect(radius.lg).toBe(20);
  });

  it('pill is 999 (fully rounded)', () => {
    expect(radius.pill).toBe(999);
  });

  it('scale is strictly increasing: sm < md < lg < pill', () => {
    expect(radius.sm).toBeLessThan(radius.md);
    expect(radius.md).toBeLessThan(radius.lg);
    expect(radius.lg).toBeLessThan(radius.pill);
  });

  it('all radius values are positive', () => {
    for (const value of Object.values(radius)) {
      expect(value).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// font tokens
// ---------------------------------------------------------------------------

describe('font tokens', () => {
  it('body font is Inter', () => {
    expect(font.body).toBe('Inter');
  });

  it('display font is InterDisplay', () => {
    expect(font.display).toBe('InterDisplay');
  });

  it('mono font is JetBrainsMono', () => {
    expect(font.mono).toBe('JetBrainsMono');
  });

  it('all font values are non-empty strings', () => {
    for (const value of Object.values(font)) {
      expect(typeof value).toBe('string');
      expect(value.length).toBeGreaterThan(0);
    }
  });

  it('font names are unique', () => {
    const values = Object.values(font);
    expect(new Set(values).size).toBe(values.length);
  });
});

// ---------------------------------------------------------------------------
// size tokens
// ---------------------------------------------------------------------------

describe('size tokens', () => {
  it('caption is 12', () => {
    expect(size.caption).toBe(12);
  });

  it('body is 16', () => {
    expect(size.body).toBe(16);
  });

  it('crisis is 20 (larger than body for legibility in high-urgency state)', () => {
    expect(size.crisis).toBe(20);
  });

  it('crisis size is larger than body size (readability during crisis)', () => {
    expect(size.crisis).toBeGreaterThan(size.body);
  });

  it('display is 28 (largest size)', () => {
    expect(size.display).toBe(28);
  });

  it('all size values are positive', () => {
    for (const value of Object.values(size)) {
      expect(value).toBeGreaterThan(0);
    }
  });

  it('has exactly 6 size tokens', () => {
    expect(Object.keys(size)).toHaveLength(6);
  });
});
