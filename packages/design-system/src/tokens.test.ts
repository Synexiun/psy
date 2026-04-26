import { describe, expect, it } from 'vitest';
import { colors, fonts, motion, easing, textScale } from './tokens';

describe('design-system tokens', () => {
  it('exposes accent.bronze as a CSS var reference', () => {
    expect(colors.accent.bronze).toBe('var(--color-accent-bronze)');
  });
  it('exposes signal.crisis as a CSS var reference', () => {
    expect(colors.signal.crisis).toBe('var(--color-signal-crisis)');
  });
  it('exposes fonts.body, fonts.display, fonts.fa', () => {
    expect(fonts.body).toBe('var(--font-body)');
    expect(fonts.display).toBe('var(--font-display)');
    expect(fonts.fa).toBe('var(--font-fa)');
  });
  it('exposes the organic ease', () => {
    expect(easing.organic).toBe('var(--ease-organic)');
  });
  it('exposes 4 motion durations + the deliberate one', () => {
    expect(motion.instant).toBe('var(--motion-instant)');
    expect(motion.deliberate).toBe('var(--motion-deliberate)');
  });
  it('exposes the display 2xl text size', () => {
    expect(textScale.display['2xl']).toBe('var(--text-display-2xl)');
  });
});
