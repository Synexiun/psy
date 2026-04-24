import { act, renderHook } from '@testing-library/react-native';
import { useMemory } from './store';

// MMKV is mocked globally in jest.setup.js

/** Reset the memory store to its blank initial state between tests. */
function resetStore() {
  useMemory.setState({ entries: [] });
}

describe('useMemory store', () => {
  beforeEach(resetStore);

  // ------------------------------------------------------------------
  // 1. Initial state
  // ------------------------------------------------------------------
  it('starts with an empty entries array', () => {
    const { result } = renderHook(() => useMemory());
    expect(result.current.entries).toEqual([]);
  });

  // ------------------------------------------------------------------
  // 2. addEntry — basic happy path
  // ------------------------------------------------------------------
  it('adds a JournalEntry with id, body, and ISO createdAt', () => {
    const { result } = renderHook(() => useMemory());

    act(() => {
      result.current.addEntry('Today was hard but I managed it.');
    });

    expect(result.current.entries).toHaveLength(1);
    const entry = result.current.entries[0]!;
    expect(typeof entry.id).toBe('string');
    expect(entry.id.length).toBeGreaterThan(0);
    expect(entry.body).toBe('Today was hard but I managed it.');
    expect(typeof entry.createdAt).toBe('string');
    expect(new Date(entry.createdAt).toISOString()).toBe(entry.createdAt);
  });

  // ------------------------------------------------------------------
  // 3. addEntry trims leading/trailing whitespace (store calls .trim())
  // ------------------------------------------------------------------
  it('trims leading and trailing whitespace from entry body', () => {
    const { result } = renderHook(() => useMemory());

    act(() => {
      result.current.addEntry('  I noticed the craving passed.  ');
    });

    expect(result.current.entries[0]!.body).toBe('I noticed the craving passed.');
  });

  // ------------------------------------------------------------------
  // 4. addEntry generates unique ids for each call
  // ------------------------------------------------------------------
  it('generates different ids for two separate entries', () => {
    const { result } = renderHook(() => useMemory());

    act(() => {
      result.current.addEntry('First entry');
    });
    act(() => {
      result.current.addEntry('Second entry');
    });

    const [a, b] = result.current.entries;
    expect(a!.id).not.toBe(b!.id);
  });

  // ------------------------------------------------------------------
  // 5. Entries are prepended — newest first (reverse chronological)
  // ------------------------------------------------------------------
  it('prepends new entries so the list is newest-first', () => {
    const { result } = renderHook(() => useMemory());

    act(() => {
      result.current.addEntry('Oldest');
    });
    act(() => {
      result.current.addEntry('Middle');
    });
    act(() => {
      result.current.addEntry('Newest');
    });

    expect(result.current.entries).toHaveLength(3);
    expect(result.current.entries[0]!.body).toBe('Newest');
    expect(result.current.entries[1]!.body).toBe('Middle');
    expect(result.current.entries[2]!.body).toBe('Oldest');
  });

  // ------------------------------------------------------------------
  // 6. Entry text is preserved verbatim (unicode, emoji, newlines)
  // ------------------------------------------------------------------
  it('preserves unicode, emoji, and newlines in entry body after trim', () => {
    const { result } = renderHook(() => useMemory());
    const complexText = 'I felt okay.\nDay 1 ✅\nأنا بخير\n今日は良い日';

    act(() => {
      result.current.addEntry(complexText);
    });

    expect(result.current.entries[0]!.body).toBe(complexText);
  });

  // ------------------------------------------------------------------
  // 7. createdAt is close to the current time
  // ------------------------------------------------------------------
  it('sets createdAt close to the current time', () => {
    const before = Date.now();
    const { result } = renderHook(() => useMemory());

    act(() => {
      result.current.addEntry('Timestamp check');
    });

    const after = Date.now();
    const createdAtMs = new Date(result.current.entries[0]!.createdAt).getTime();
    expect(createdAtMs).toBeGreaterThanOrEqual(before);
    expect(createdAtMs).toBeLessThanOrEqual(after);
  });

  // ------------------------------------------------------------------
  // 8. Persistence — state survives store re-initialisation via setState
  // ------------------------------------------------------------------
  it('retains entries after store state is manually rehydrated', () => {
    const snapshot = [
      {
        id: 'abc-123',
        body: 'Restored from storage',
        createdAt: new Date().toISOString(),
      },
    ];

    // Simulate what Zustand persist rehydration would do
    useMemory.setState({ entries: snapshot });

    const { result } = renderHook(() => useMemory());
    expect(result.current.entries).toHaveLength(1);
    expect(result.current.entries[0]!.id).toBe('abc-123');
    expect(result.current.entries[0]!.body).toBe('Restored from storage');
  });

  // ------------------------------------------------------------------
  // 9. Empty-string body after trimming is still stored
  // ------------------------------------------------------------------
  it('stores an entry with an empty body when only whitespace is passed', () => {
    const { result } = renderHook(() => useMemory());

    act(() => {
      result.current.addEntry('   ');
    });

    expect(result.current.entries).toHaveLength(1);
    expect(result.current.entries[0]!.body).toBe('');
  });

  // ------------------------------------------------------------------
  // 10. Multiple entries accumulate without limit
  // ------------------------------------------------------------------
  it('accumulates many entries without dropping any', () => {
    const { result } = renderHook(() => useMemory());
    const count = 20;

    act(() => {
      for (let i = 0; i < count; i++) {
        result.current.addEntry(`Entry number ${i}`);
      }
    });

    expect(result.current.entries).toHaveLength(count);
  });
});
