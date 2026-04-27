'use client';

import { useNotifications } from './useNotifications';

export function useNotificationCount(): { count: number } {
  const { unreadCount } = useNotifications();
  return { count: unreadCount };
}
