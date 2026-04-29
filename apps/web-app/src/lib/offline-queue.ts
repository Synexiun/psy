'use client';
import { openDB, type IDBPDatabase } from 'idb';

export interface QueuedCheckIn {
  id?: number;           // auto-incremented by IDB
  intensity: number;
  triggerTags: string[];
  notes?: string;
  createdAt: string;    // ISO timestamp
  clientDedupKey: string; // ISO minute-rounded timestamp for server dedup
}

const DB_NAME = 'discipline-offline';
const STORE_NAME = 'check-in-queue';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
        }
      },
    }).catch((err: unknown) => {
      dbPromise = null;
      throw err;
    });
  }
  // dbPromise is guaranteed non-null here: we either just assigned it
  // or the guard confirmed it was already set.
  return dbPromise!;
}

export async function enqueueCheckIn(payload: Omit<QueuedCheckIn, 'id'>): Promise<void> {
  const db = await getDb();
  await db.add(STORE_NAME, payload);
}

export async function getAllQueued(): Promise<QueuedCheckIn[]> {
  const db = await getDb();
  return db.getAll(STORE_NAME);
}

export async function dequeueCheckIn(id: number): Promise<void> {
  const db = await getDb();
  await db.delete(STORE_NAME, id);
}

export async function clearQueue(): Promise<void> {
  const db = await getDb();
  await db.clear(STORE_NAME);
}
