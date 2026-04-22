import { act, renderHook } from '@testing-library/react-native';
import { useResilience } from './store';

describe('useResilience', () => {
  beforeEach(() => {
    // Reset store to initial state between tests
    const { result } = renderHook(() => useResilience());
    act(() => {
      result.current.applyRelapse();
    });
  });

  it('has zero initial streaks', () => {
    const { result } = renderHook(() => useResilience());
    expect(result.current.continuousDays).toBe(0);
    expect(result.current.resilienceDays).toBe(0);
    expect(result.current.urgesHandledTotal).toBe(0);
  });

  it('increments urgesHandledTotal on applyHandled', () => {
    const { result } = renderHook(() => useResilience());
    act(() => result.current.applyHandled());
    expect(result.current.urgesHandledTotal).toBe(1);
  });

  it('resets continuousDays on applyRelapse but preserves resilienceDays', () => {
    const { result } = renderHook(() => useResilience());
    act(() => result.current.applyHandled());
    const resilienceBefore = result.current.resilienceDays;
    act(() => result.current.applyRelapse());
    expect(result.current.continuousDays).toBe(0);
    expect(result.current.continuousStreakStart).toBeNull();
    expect(result.current.resilienceDays).toBe(resilienceBefore);
  });

  it('never decrements resilienceDays', () => {
    const { result } = renderHook(() => useResilience());
    act(() => result.current.applyHandled());
    const resilienceBefore = result.current.resilienceDays;
    act(() => result.current.applyRelapse());
    act(() => result.current.applyRelapse());
    expect(result.current.resilienceDays).toBeGreaterThanOrEqual(resilienceBefore);
  });
});
