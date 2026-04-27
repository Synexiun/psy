import { registerStubs } from './index';

export interface NotificationItem {
  id: string;
  text: string;
  timestamp: string;
  read: boolean;
}

export interface NotificationPrefs {
  pushEnabled: boolean;
  emailEnabled: boolean;
  nudgeFrequency: 'low' | 'medium' | 'high';
}

export interface NotificationsStubs {
  items: NotificationItem[];
  prefs: NotificationPrefs;
}

export const notificationsStubs: NotificationsStubs = {
  items: [
    {
      id: 'n1',
      text: 'Your last check-in showed a rising urge. You handled it — well done.',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      read: false,
    },
    {
      id: 'n2',
      text: 'New pattern detected: urges are higher on weekday evenings.',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      read: true,
    },
    {
      id: 'n3',
      text: 'Your resilience streak is growing. Keep going.',
      timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
      read: true,
    },
  ],
  prefs: {
    pushEnabled: false,
    emailEnabled: true,
    nudgeFrequency: 'medium',
  },
};

registerStubs('notifications', notificationsStubs);
