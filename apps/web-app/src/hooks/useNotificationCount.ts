'use client';

/**
 * Stub hook returning unread notification count.
 * Returns 0 until the real push notification backend (Chunk 8 Phase 5) is wired.
 * Shape: { count: number } — keeps call-site stable when real data arrives.
 * Replace body with useQuery/subscription in Phase 5; do not mutate the useState stub.
 */
export function useNotificationCount(): { count: number } {
  return { count: 0 };
}
