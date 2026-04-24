import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'memory' });

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

export interface JournalEntry {
  id: string;
  body: string;
  createdAt: string; // ISO date
}

interface MemoryState {
  entries: JournalEntry[];
  addEntry: (body: string) => void;
}

export const useMemory = create<MemoryState>()(
  persist(
    (set) => ({
      entries: [],

      addEntry: (body: string) =>
        set((s) => ({
          entries: [
            {
              id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
              body: body.trim(),
              createdAt: new Date().toISOString(),
            },
            ...s.entries,
          ],
        })),
    }),
    {
      name: 'memory-store',
      storage: createJSONStorage(() => mmkvStorage),
    },
  ),
);
