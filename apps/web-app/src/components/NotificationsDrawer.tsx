'use client';
import * as React from 'react';
import { Sheet } from '@disciplineos/design-system/primitives/Sheet';

export interface NotificationsDrawerProps {
  open: boolean;
  onClose: () => void;
  /** Unread notification count — for future real data */
  count?: number;
}

const STUB_NOTIFICATIONS = [
  { id: 'n1', text: 'Your last check-in showed a rising urge. You handled it — well done.' },
  { id: 'n2', text: 'New pattern detected: urges are higher on weekday evenings.' },
  { id: 'n3', text: 'Your resilience streak is growing. Keep going.' },
];

export function NotificationsDrawer({ open, onClose, count = 0 }: NotificationsDrawerProps): React.ReactElement {
  return (
    <Sheet
      open={open}
      onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}
      title="Notifications"
      {...(count > 0 && { description: `${count} unread` })}
      side="right"
      size="sm"
      closeLabel="Close notifications"
    >
      {STUB_NOTIFICATIONS.length > 0 ? (
        <ul className="space-y-3" role="list">
          {STUB_NOTIFICATIONS.map((n) => (
            <li
              key={n.id}
              className="rounded-lg border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary"
            >
              {n.text}
            </li>
          ))}
        </ul>
      ) : (
        <p className="py-8 text-center text-sm text-ink-tertiary">No notifications</p>
      )}
    </Sheet>
  );
}
