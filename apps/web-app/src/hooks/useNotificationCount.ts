'use client';
import { useState } from 'react';

/**
 * Stub hook returning unread notification count.
 * Returns 0 until the real push notification backend (Chunk 8 Phase 5) is wired.
 * Shape: { count: number } — keeps call-site stable when real data arrives.
 */
export function useNotificationCount(): { count: number } {
  const [count] = useState<number>(0);
  return { count };
}
