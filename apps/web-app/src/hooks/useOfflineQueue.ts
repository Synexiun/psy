'use client';
import * as React from 'react';
import { enqueueCheckIn, getAllQueued, dequeueCheckIn, type QueuedCheckIn } from '@/lib/offline-queue';
import { submitCheckIn } from '@/lib/api';

export interface UseOfflineQueueResult {
  queuedCount: number;
  enqueue: (payload: Omit<QueuedCheckIn, 'id' | 'createdAt' | 'clientDedupKey'>) => Promise<void>;
  flush: (getToken: () => Promise<string | null>) => Promise<void>;
  isFlushing: boolean;
}

export function useOfflineQueue(): UseOfflineQueueResult {
  const [queuedCount, setQueuedCount] = React.useState(0);
  const [isFlushing, setIsFlushing] = React.useState(false);

  // Load initial count on mount
  React.useEffect(() => {
    void getAllQueued().then((items) => setQueuedCount(items.length));
  }, []);

  // Listen for online events and auto-flush
  React.useEffect(() => {
    const handleOnline = () => {
      // Signal only — caller decides whether to flush (avoids token coupling)
      void getAllQueued().then((items) => setQueuedCount(items.length));
    };
    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, []);

  async function enqueue(payload: Omit<QueuedCheckIn, 'id' | 'createdAt' | 'clientDedupKey'>): Promise<void> {
    const now = new Date();
    // Round to nearest minute for dedup key
    const minuteRounded = new Date(Math.floor(now.getTime() / 60000) * 60000);
    await enqueueCheckIn({
      ...payload,
      createdAt: now.toISOString(),
      clientDedupKey: minuteRounded.toISOString(),
    });
    setQueuedCount((c) => c + 1);
  }

  async function flush(getToken: () => Promise<string | null>): Promise<void> {
    if (isFlushing) return;
    setIsFlushing(true);
    try {
      const items = await getAllQueued();
      for (const item of items) {
        const token = await getToken();
        if (!token) break; // auth lost mid-flush — stop, leave rest in queue
        try {
          await submitCheckIn(token, item.intensity, item.triggerTags, item.notes);
          await dequeueCheckIn(item.id!);
          setQueuedCount((c) => Math.max(0, c - 1));
        } catch {
          // Network still unavailable for this item — leave in queue
          break;
        }
      }
    } finally {
      setIsFlushing(false);
    }
  }

  return { queuedCount, enqueue, flush, isFlushing };
}
