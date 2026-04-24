import { act, renderHook } from '@testing-library/react-native';
import { useIntervention } from './store';
import { getToolById } from './data/tools';

// MMKV is mocked globally in jest.setup.js

/** Reset the intervention store to its blank initial state between tests. */
function resetStore() {
  useIntervention.setState({ toolUsages: [] });
}

describe('useIntervention store', () => {
  beforeEach(resetStore);

  // ------------------------------------------------------------------
  // 1. Initial state
  // ------------------------------------------------------------------
  it('starts with an empty toolUsages array', () => {
    const { result } = renderHook(() => useIntervention());
    expect(result.current.toolUsages).toEqual([]);
  });

  // ------------------------------------------------------------------
  // 2. recordToolUsage — basic happy path
  // ------------------------------------------------------------------
  it('records a ToolUsage with toolId and ISO usedAt', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordToolUsage('box-breathing');
    });

    expect(result.current.toolUsages).toHaveLength(1);
    const usage = result.current.toolUsages[0]!;
    expect(usage.toolId).toBe('box-breathing');
    // usedAt should be a valid ISO 8601 string
    expect(() => new Date(usage.usedAt)).not.toThrow();
    expect(typeof usage.usedAt).toBe('string');
    expect(new Date(usage.usedAt).toISOString()).toBe(usage.usedAt);
  });

  // ------------------------------------------------------------------
  // 3. recordToolUsage — unknown / arbitrary id is stored verbatim
  // ------------------------------------------------------------------
  it('stores the toolId verbatim for any string passed', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordToolUsage('unknown-tool-id');
    });

    expect(result.current.toolUsages[0]!.toolId).toBe('unknown-tool-id');
  });

  // ------------------------------------------------------------------
  // 4. Multiple usages of the same tool create separate entries
  // ------------------------------------------------------------------
  it('creates two separate entries when the same tool is recorded twice', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordToolUsage('urge-surfing');
    });
    act(() => {
      result.current.recordToolUsage('urge-surfing');
    });

    expect(result.current.toolUsages).toHaveLength(2);
    expect(result.current.toolUsages[0]!.toolId).toBe('urge-surfing');
    expect(result.current.toolUsages[1]!.toolId).toBe('urge-surfing');
  });

  // ------------------------------------------------------------------
  // 5. Multiple different tools accumulate in order
  // ------------------------------------------------------------------
  it('accumulates entries from different tools in insertion order', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordToolUsage('box-breathing');
    });
    act(() => {
      result.current.recordToolUsage('5-4-3-2-1-grounding');
    });
    act(() => {
      result.current.recordToolUsage('stop-technique');
    });

    const ids = result.current.toolUsages.map((u) => u.toolId);
    expect(ids).toEqual(['box-breathing', '5-4-3-2-1-grounding', 'stop-technique']);
  });

  // ------------------------------------------------------------------
  // 6. Persistence — state survives store re-initialisation via setState
  //    (mocked MMKV; Zustand persist mid-writes are synchronous in tests)
  // ------------------------------------------------------------------
  it('retains toolUsages after store state is manually rehydrated', () => {
    const snapshot = [
      { toolId: 'cold-water-reset', usedAt: new Date().toISOString() },
      { toolId: 'delay-and-distract', usedAt: new Date().toISOString() },
    ];

    // Simulate what Zustand persist rehydration would do
    useIntervention.setState({ toolUsages: snapshot });

    const { result } = renderHook(() => useIntervention());
    expect(result.current.toolUsages).toHaveLength(2);
    expect(result.current.toolUsages[0]!.toolId).toBe('cold-water-reset');
    expect(result.current.toolUsages[1]!.toolId).toBe('delay-and-distract');
  });

  // ------------------------------------------------------------------
  // 7. usedAt timestamp is recent
  // ------------------------------------------------------------------
  it('records usedAt close to the current time', () => {
    const before = Date.now();
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordToolUsage('compassion-meditation');
    });

    const after = Date.now();
    const usedAtMs = new Date(result.current.toolUsages[0]!.usedAt).getTime();
    expect(usedAtMs).toBeGreaterThanOrEqual(before);
    expect(usedAtMs).toBeLessThanOrEqual(after);
  });
});

// ------------------------------------------------------------------
// recordUrgeCheckIn — UrgeCheckIn persistence
// ------------------------------------------------------------------
describe('recordUrgeCheckIn', () => {
  /** Reset both arrays before each sub-test. */
  beforeEach(() => {
    useIntervention.setState({ toolUsages: [], urgeCheckIns: [] });
  });

  // 1. Adds one entry to urgeCheckIns
  it('adds a single UrgeCheckIn entry to the array', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(7, ['stress', 'anxiety'], 'felt overwhelming');
    });

    expect(result.current.urgeCheckIns).toHaveLength(1);
  });

  // 2. Intensity is stored correctly
  it('stores the intensity value verbatim', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(5, [], '');
    });

    expect(result.current.urgeCheckIns[0]!.intensity).toBe(5);
  });

  // 3. Triggers array is stored correctly
  it('stores the triggers array correctly', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(3, ['boredom', 'loneliness'], '');
    });

    expect(result.current.urgeCheckIns[0]!.triggers).toEqual(['boredom', 'loneliness']);
  });

  // 4. Empty triggers array is stored without error
  it('stores an empty triggers array when no triggers are passed', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(2, [], '');
    });

    expect(result.current.urgeCheckIns[0]!.triggers).toEqual([]);
  });

  // 5. Notes field is stored correctly
  it('stores the notes string verbatim', () => {
    const { result } = renderHook(() => useIntervention());
    const notesText = 'Had a tough meeting, felt the pull strongly.';

    act(() => {
      result.current.recordUrgeCheckIn(8, ['stress'], notesText);
    });

    expect(result.current.urgeCheckIns[0]!.notes).toBe(notesText);
  });

  // 6. loggedAt is a valid ISO string
  it('loggedAt is a valid ISO 8601 string', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(4, [], '');
    });

    const loggedAt = result.current.urgeCheckIns[0]!.loggedAt;
    expect(typeof loggedAt).toBe('string');
    expect(() => new Date(loggedAt)).not.toThrow();
    expect(new Date(loggedAt).toISOString()).toBe(loggedAt);
  });

  // 7. loggedAt is close to current time
  it('loggedAt is recorded close to the current time', () => {
    const before = Date.now();
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(6, ['fatigue'], '');
    });

    const after = Date.now();
    const loggedAtMs = new Date(result.current.urgeCheckIns[0]!.loggedAt).getTime();
    expect(loggedAtMs).toBeGreaterThanOrEqual(before);
    expect(loggedAtMs).toBeLessThanOrEqual(after);
  });

  // 8. id field is a non-empty string
  it('id field is a non-empty string', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(1, [], '');
    });

    const id = result.current.urgeCheckIns[0]!.id;
    expect(typeof id).toBe('string');
    expect(id.length).toBeGreaterThan(0);
  });

  // 9. Multiple entries accumulate in insertion order
  it('accumulates multiple entries in insertion order', () => {
    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(3, ['boredom'], 'first');
    });
    act(() => {
      result.current.recordUrgeCheckIn(8, ['stress', 'anger'], 'second');
    });
    act(() => {
      result.current.recordUrgeCheckIn(1, [], 'third');
    });

    expect(result.current.urgeCheckIns).toHaveLength(3);
    expect(result.current.urgeCheckIns[0]!.notes).toBe('first');
    expect(result.current.urgeCheckIns[1]!.notes).toBe('second');
    expect(result.current.urgeCheckIns[2]!.notes).toBe('third');
  });

  // 10. Adding check-ins does not corrupt existing toolUsages
  it('does not affect existing toolUsages entries', () => {
    useIntervention.setState({
      toolUsages: [{ toolId: 'box-breathing', usedAt: new Date().toISOString() }],
      urgeCheckIns: [],
    });

    const { result } = renderHook(() => useIntervention());

    act(() => {
      result.current.recordUrgeCheckIn(5, [], '');
    });

    expect(result.current.toolUsages).toHaveLength(1);
    expect(result.current.toolUsages[0]!.toolId).toBe('box-breathing');
  });
});

// ------------------------------------------------------------------
// getToolById helper — pure function, no store involvement
// ------------------------------------------------------------------
describe('getToolById helper', () => {
  it('returns the correct CopingTool for a known toolId', () => {
    const tool = getToolById('box-breathing');
    expect(tool).toBeDefined();
    expect(tool!.toolId).toBe('box-breathing');
    expect(tool!.name).toBe('Box Breathing');
    expect(tool!.category).toBe('Breathing');
    expect(tool!.hasBreathingAnimation).toBe(true);
  });

  it('returns undefined for an unknown toolId', () => {
    expect(getToolById('does-not-exist')).toBeUndefined();
  });

  it('returns a tool with a non-empty steps array', () => {
    const tool = getToolById('5-4-3-2-1-grounding');
    expect(tool).toBeDefined();
    expect(tool!.steps.length).toBeGreaterThan(0);
  });

  it('returns all known catalog tools without throwing', () => {
    const ids = [
      'box-breathing',
      '5-4-3-2-1-grounding',
      'progressive-muscle-relaxation',
      'cold-water-reset',
      'urge-surfing',
      'stop-technique',
      'compassion-meditation',
      'delay-and-distract',
    ];
    for (const id of ids) {
      expect(getToolById(id)).toBeDefined();
    }
  });
});
