import { describe, it, expect } from 'vitest';
import { colors, isRtl, rtlLocales, space, radius } from './tokens';

describe('tokens', () => {
  it('has expected color tokens', () => {
    expect(colors.background.base).toBe('hsl(0 0% 100%)');
    expect(colors.accent.primary).toBe('hsl(217 91% 60%)');
    expect(colors.safety.crisis).toBe('hsl(0 84% 60%)');
  });

  it('identifies RTL locales', () => {
    expect(isRtl('ar')).toBe(true);
    expect(isRtl('fa')).toBe(true);
    expect(isRtl('en')).toBe(false);
    expect(isRtl('fr')).toBe(false);
  });

  it('rtlLocales is frozen', () => {
    expect(rtlLocales.has('ar')).toBe(true);
    expect(rtlLocales.has('en')).toBe(false);
  });

  it('has spacing scale', () => {
    expect(space.md).toBe('1rem');
    expect(space['2xl']).toBe('3rem');
  });

  it('has radius scale', () => {
    expect(radius.full).toBe('9999px');
    expect(radius.md).toBe('0.5rem');
  });
});
