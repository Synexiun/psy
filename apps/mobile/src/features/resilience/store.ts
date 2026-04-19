import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'resilience', encryptionKey: 'placeholder-wire-keychain' });

const mmkvStorage = {
  getItem: (name: string) => {
    const value = storage.getString(name);
    return value ?? null;
  },
  setItem: (name: string, value: string) => {
    storage.set(name, value);
  },
  removeItem: (name: string) => {
    storage.delete(name);
  },
};

type ResilienceState = {
  continuousDays: number;
  continuousStreakStart: string | null;
  resilienceDays: number;
  resilienceStreakStart: string;
  urgesHandledTotal: number;

  applyHandled: () => void;
  applyRelapse: () => void;
};

const initialStart = new Date().toISOString();

/**
 * Streak store.
 *
 * Invariants (see Docs/Technicals/02_Data_Model.md §10.2):
 *  - resilienceDays is monotonically non-decreasing.
 *  - urgesHandledTotal is monotonically non-decreasing.
 *  - On relapse: continuousDays resets; resilience preserved.
 *
 * Server is the source of truth; this store mirrors and must reconcile.
 */
export const useResilience = create<ResilienceState>()(
  persist(
    (set) => ({
      continuousDays: 0,
      continuousStreakStart: null,
      resilienceDays: 0,
      resilienceStreakStart: initialStart,
      urgesHandledTotal: 0,

      applyHandled: () =>
        set((s) => ({
          urgesHandledTotal: s.urgesHandledTotal + 1,
          resilienceDays: Math.max(s.resilienceDays, daysSince(s.resilienceStreakStart)),
          continuousDays: s.continuousStreakStart
            ? daysSince(s.continuousStreakStart)
            : s.continuousDays,
        })),

      applyRelapse: () =>
        set((s) => ({
          continuousDays: 0,
          continuousStreakStart: null,
          resilienceDays: s.resilienceDays,
          urgesHandledTotal: s.urgesHandledTotal,
        })),
    }),
    {
      name: 'resilience-store',
      storage: createJSONStorage(() => mmkvStorage),
    },
  ),
);

function daysSince(isoStart: string): number {
  const start = new Date(isoStart).getTime();
  const now = Date.now();
  return Math.max(0, Math.floor((now - start) / 86_400_000));
}
