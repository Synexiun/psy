/**
 * Assessment store — unit tests.
 *
 * Covers:
 * - Initial state
 * - setResponse records answers
 * - reset clears all state
 * - startInstrument sets current instrument and clears responses
 * - scoreInstrument deterministic scoring (PHQ-9 / GAD-7 / WHO-5)
 * - PHQ-9 item 9 safety flag
 *
 * MMKV is mocked globally in jest.setup.js.
 */

import { act, renderHook } from '@testing-library/react-native';
import {
  useAssessment,
  scoreInstrument,
  PHQ9,
  GAD7,
  WHO5,
} from './store';

/** Reset the assessment store to its initial state between tests. */
function resetStore() {
  useAssessment.setState({
    currentInstrumentId: null,
    responses: {},
    lastScores: {},
  });
}

// ---------------------------------------------------------------------------
// useAssessment store
// ---------------------------------------------------------------------------
describe('useAssessment store', () => {
  beforeEach(resetStore);

  // 1. Initial state
  it('starts with null currentInstrumentId', () => {
    const { result } = renderHook(() => useAssessment());
    expect(result.current.currentInstrumentId).toBeNull();
  });

  it('starts with empty responses', () => {
    const { result } = renderHook(() => useAssessment());
    expect(result.current.responses).toEqual({});
  });

  it('starts with empty lastScores', () => {
    const { result } = renderHook(() => useAssessment());
    expect(result.current.lastScores).toEqual({});
  });

  // 2. startInstrument
  it('startInstrument sets currentInstrumentId', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.startInstrument('phq9');
    });
    expect(result.current.currentInstrumentId).toBe('phq9');
  });

  it('startInstrument clears previous responses', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.setResponse(0, 2);
    });
    act(() => {
      result.current.startInstrument('gad7');
    });
    expect(result.current.responses).toEqual({});
  });

  // 3. setResponse
  it('setResponse records the answer for an item index', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.setResponse(0, 1);
    });
    expect(result.current.responses[0]).toBe(1);
  });

  it('setResponse accumulates answers for multiple items', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.setResponse(0, 1);
      result.current.setResponse(3, 3);
      result.current.setResponse(8, 2);
    });
    expect(result.current.responses[0]).toBe(1);
    expect(result.current.responses[3]).toBe(3);
    expect(result.current.responses[8]).toBe(2);
  });

  it('setResponse overwrites a previously set value for the same index', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.setResponse(2, 1);
    });
    act(() => {
      result.current.setResponse(2, 3);
    });
    expect(result.current.responses[2]).toBe(3);
  });

  // 4. reset
  it('reset clears currentInstrumentId', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.startInstrument('phq9');
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.currentInstrumentId).toBeNull();
  });

  it('reset clears responses', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.setResponse(0, 2);
      result.current.setResponse(1, 1);
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.responses).toEqual({});
  });

  it('reset clears lastScores', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.recordCompletion({
        instrumentId: 'phq9',
        displayScore: 5,
        displayScoreString: '5',
        severityLabel: 'Mild',
        completedAt: new Date().toISOString(),
      });
    });
    act(() => {
      result.current.reset();
    });
    expect(result.current.lastScores).toEqual({});
  });

  // 5. recordCompletion
  it('recordCompletion stores a last score entry', () => {
    const { result } = renderHook(() => useAssessment());
    const now = new Date().toISOString();
    act(() => {
      result.current.recordCompletion({
        instrumentId: 'gad7',
        displayScore: 8,
        displayScoreString: '8',
        severityLabel: 'Mild',
        completedAt: now,
      });
    });
    expect(result.current.lastScores['gad7']).toBeDefined();
    expect(result.current.lastScores['gad7']!.displayScore).toBe(8);
    expect(result.current.lastScores['gad7']!.completedAt).toBe(now);
  });

  it('recordCompletion resets currentInstrumentId and responses', () => {
    const { result } = renderHook(() => useAssessment());
    act(() => {
      result.current.startInstrument('who5');
      result.current.setResponse(0, 4);
    });
    act(() => {
      result.current.recordCompletion({
        instrumentId: 'who5',
        displayScore: 64,
        displayScoreString: '64',
        severityLabel: 'Good well-being',
        completedAt: new Date().toISOString(),
      });
    });
    expect(result.current.currentInstrumentId).toBeNull();
    expect(result.current.responses).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// scoreInstrument — deterministic scoring
// ---------------------------------------------------------------------------
describe('scoreInstrument', () => {
  // PHQ-9
  it('PHQ-9: scores all zeros as raw 0, minimal severity', () => {
    const allZero: Record<number, number> = {};
    for (let i = 0; i < 9; i++) allZero[i] = 0;
    const r = scoreInstrument('phq9', allZero);
    expect(r.raw).toBe(0);
    expect(r.displayScore).toBe(0);
    expect(r.displayScoreString).toBe('0');
    expect(r.severityLabel).toMatch(/minimal/i);
    expect(r.safetyFlag).toBe(false);
  });

  it('PHQ-9: scores total correctly', () => {
    const responses: Record<number, number> = {
      0: 2, 1: 1, 2: 3, 3: 2, 4: 1, 5: 2, 6: 1, 7: 2, 8: 0,
    };
    const r = scoreInstrument('phq9', responses);
    expect(r.raw).toBe(14);
    expect(r.severityLabel).toMatch(/moderate/i);
    expect(r.safetyFlag).toBe(false);
  });

  it('PHQ-9: item 9 = 1 sets safetyFlag', () => {
    const responses: Record<number, number> = {};
    for (let i = 0; i < 9; i++) responses[i] = 0;
    responses[8] = 1; // item 9
    const r = scoreInstrument('phq9', responses);
    expect(r.safetyFlag).toBe(true);
  });

  it('PHQ-9: item 9 = 2 sets safetyFlag', () => {
    const responses: Record<number, number> = {};
    for (let i = 0; i < 9; i++) responses[i] = 0;
    responses[8] = 2;
    const r = scoreInstrument('phq9', responses);
    expect(r.safetyFlag).toBe(true);
  });

  it('PHQ-9: item 9 = 0 does not set safetyFlag', () => {
    const responses: Record<number, number> = {};
    for (let i = 0; i < 9; i++) responses[i] = 1;
    responses[8] = 0;
    const r = scoreInstrument('phq9', responses);
    expect(r.safetyFlag).toBe(false);
  });

  it('PHQ-9: score 20+ is severe', () => {
    const responses: Record<number, number> = {};
    for (let i = 0; i < 9; i++) responses[i] = 3;
    const r = scoreInstrument('phq9', responses);
    expect(r.raw).toBe(27);
    expect(r.severityLabel).toMatch(/severe/i);
  });

  // GAD-7
  it('GAD-7: scores correctly and no safetyFlag', () => {
    const responses: Record<number, number> = {
      0: 2, 1: 2, 2: 1, 3: 1, 4: 2, 5: 1, 6: 2,
    };
    const r = scoreInstrument('gad7', responses);
    expect(r.raw).toBe(11);
    expect(r.severityLabel).toMatch(/moderate/i);
    expect(r.safetyFlag).toBe(false);
  });

  it('GAD-7: all zeros is minimal', () => {
    const responses: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0 };
    const r = scoreInstrument('gad7', responses);
    expect(r.raw).toBe(0);
    expect(r.severityLabel).toMatch(/minimal/i);
  });

  // WHO-5
  it('WHO-5: displayScore is raw ×4', () => {
    const responses: Record<number, number> = { 0: 4, 1: 3, 2: 3, 3: 4, 4: 4 };
    const r = scoreInstrument('who5', responses);
    expect(r.raw).toBe(18);
    expect(r.displayScore).toBe(72);
    expect(r.displayScoreString).toBe('72');
  });

  it('WHO-5: low score is "Low well-being"', () => {
    const responses: Record<number, number> = { 0: 0, 1: 0, 2: 1, 3: 0, 4: 0 };
    const r = scoreInstrument('who5', responses);
    expect(r.severityLabel).toMatch(/low/i);
  });

  // Latin digits
  it('displayScoreString always uses Latin digits', () => {
    const responses: Record<number, number> = {};
    for (let i = 0; i < 9; i++) responses[i] = 2;
    const r = scoreInstrument('phq9', responses);
    // Should not contain non-ASCII digit characters
    expect(/^\d+$/.test(r.displayScoreString)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Instrument catalog sanity checks
// ---------------------------------------------------------------------------
describe('instrument definitions', () => {
  it('PHQ-9 has 9 items', () => {
    expect(PHQ9.items).toHaveLength(9);
  });

  it('PHQ-9 item 9 (index 8) mentions self-harm', () => {
    const item = PHQ9.items[8]!;
    expect(item.text.toLowerCase()).toMatch(/dead|hurting yourself/);
  });

  it('GAD-7 has 7 items', () => {
    expect(GAD7.items).toHaveLength(7);
  });

  it('WHO-5 has 5 items', () => {
    expect(WHO5.items).toHaveLength(5);
  });

  it('PHQ-9 response options cover 0–3', () => {
    const values = PHQ9.responseOptions.map((o) => o.value);
    expect(values).toEqual([0, 1, 2, 3]);
  });

  it('WHO-5 response options cover 0–5', () => {
    const values = WHO5.responseOptions.map((o) => o.value);
    expect(values).toEqual([0, 1, 2, 3, 4, 5]);
  });
});
