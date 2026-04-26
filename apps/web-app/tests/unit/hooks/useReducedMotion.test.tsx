import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useReducedMotion } from '@/hooks/useReducedMotion';

describe('useReducedMotion', () => {
  afterEach(() => {
    document.documentElement.removeAttribute('data-ambient-motion');
    vi.restoreAllMocks();
  });

  it('returns true when OS prefers reduced motion', () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
      onchange: null,
    }));
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(true);
  });

  it('reacts to the Settings flag toggling on at runtime', async () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
      matches: false,
      media: '',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
      onchange: null,
    }));
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);

    await act(async () => {
      document.documentElement.setAttribute('data-ambient-motion', 'off');
    });
    expect(result.current).toBe(true);
  });

  it('returns false when neither source signals reduced motion', () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
      matches: false,
      media: '',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
      onchange: null,
    }));
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
  });
});
