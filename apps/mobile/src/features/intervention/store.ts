import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'intervention' });

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

export interface ToolUsage {
  toolId: string;
  usedAt: string; // ISO date
}

export interface UrgeCheckIn {
  id: string;         // Date.now().toString()
  intensity: number;  // 0-10
  triggers: string[];
  notes: string;
  loggedAt: string;   // ISO date
}

interface InterventionState {
  toolUsages: ToolUsage[];
  urgeCheckIns: UrgeCheckIn[];
  recordToolUsage: (toolId: string) => void;
  recordUrgeCheckIn: (intensity: number, triggers: string[], notes: string) => void;
}

export const useIntervention = create<InterventionState>()(
  persist(
    (set) => ({
      toolUsages: [],
      urgeCheckIns: [],

      recordToolUsage: (toolId: string) =>
        set((s) => ({
          toolUsages: [
            ...s.toolUsages,
            { toolId, usedAt: new Date().toISOString() },
          ],
        })),

      recordUrgeCheckIn: (intensity: number, triggers: string[], notes: string) =>
        set((s) => ({
          urgeCheckIns: [
            ...s.urgeCheckIns,
            {
              id: Date.now().toString(),
              intensity,
              triggers,
              notes,
              loggedAt: new Date().toISOString(),
            },
          ],
        })),
    }),
    {
      name: 'intervention-store',
      storage: createJSONStorage(() => mmkvStorage),
    },
  ),
);
