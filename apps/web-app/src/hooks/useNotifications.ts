'use client';
import '@/lib/stubs/notifications';
import { useState } from 'react';
import { getStub } from '@/lib/stubs/index';
import type { NotificationItem, NotificationPrefs } from '@/lib/stubs/notifications';

export type { NotificationItem, NotificationPrefs };

export interface NotificationPrefsState extends NotificationPrefs {
  setPushEnabled: (v: boolean) => void;
  setEmailEnabled: (v: boolean) => void;
  setNudgeFrequency: (v: NotificationPrefs['nudgeFrequency']) => void;
}

export interface UseNotificationsResult {
  items: NotificationItem[];
  unreadCount: number;
  prefs: NotificationPrefsState;
}

export function useNotifications(): UseNotificationsResult {
  const stubPrefs = getStub('notifications', 'prefs') ?? {
    pushEnabled: false,
    emailEnabled: true,
    nudgeFrequency: 'medium' as const,
  };
  const stubItems = getStub('notifications', 'items') ?? [];

  const [pushEnabled, setPushEnabled] = useState(stubPrefs.pushEnabled);
  const [emailEnabled, setEmailEnabled] = useState(stubPrefs.emailEnabled);
  const [nudgeFrequency, setNudgeFrequency] = useState<NotificationPrefs['nudgeFrequency']>(
    stubPrefs.nudgeFrequency,
  );

  const unreadCount = stubItems.filter((item) => !item.read).length;

  return {
    items: stubItems,
    unreadCount,
    prefs: {
      pushEnabled,
      setPushEnabled,
      emailEnabled,
      setEmailEnabled,
      nudgeFrequency,
      setNudgeFrequency,
    },
  };
}
