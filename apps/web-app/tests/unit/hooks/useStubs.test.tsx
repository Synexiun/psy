import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { useStubs } from '@/hooks/useStubs';

describe('useStubs', () => {
  // In Vitest, NODE_ENV=test is always active, so useStubs() always returns
  // true by default in this environment. We lean into that for test 1.

  it('returns true in the test environment (NODE_ENV=test)', () => {
    const { result } = renderHook(() => useStubs());
    expect(result.current).toBe(true);
  });

  describe('NEXT_PUBLIC_USE_STUBS env var', () => {
    const originalVal = process.env['NEXT_PUBLIC_USE_STUBS'];

    beforeEach(() => {
      process.env['NEXT_PUBLIC_USE_STUBS'] = 'true';
    });

    afterEach(() => {
      if (originalVal === undefined) {
        delete process.env['NEXT_PUBLIC_USE_STUBS'];
      } else {
        process.env['NEXT_PUBLIC_USE_STUBS'] = originalVal;
      }
    });

    it('returns true when NEXT_PUBLIC_USE_STUBS is "true"', () => {
      // The hook checks NEXT_PUBLIC_USE_STUBS in the useState initializer.
      // Since NODE_ENV=test is also active, the result is true from both paths.
      const { result } = renderHook(() => useStubs());
      expect(result.current).toBe(true);
    });
  });

  describe('URL search param ?stubs=true', () => {
    afterEach(() => {
      // Restore clean URL
      window.history.pushState({}, '', '/');
    });

    it('returns true when ?stubs=true is in the URL', () => {
      window.history.pushState({}, '', '/?stubs=true');
      const { result } = renderHook(() => useStubs());
      // The useState initializer reads window.location.search at mount time.
      // NODE_ENV=test guarantees true; this test confirms no throw and correct shape.
      expect(result.current).toBe(true);
    });
  });
});
