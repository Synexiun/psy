'use client';
import * as React from 'react';
import { useTranslations } from 'next-intl';
import { Sheet } from '@disciplineos/design-system/primitives/Sheet';
import { useNotifications } from '@/hooks/useNotifications';

export interface NotificationsDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function NotificationsDrawer({ open, onClose }: NotificationsDrawerProps): React.ReactElement {
  const t = useTranslations('notifications');
  const { items, unreadCount, markAllRead } = useNotifications();

  React.useEffect(() => {
    if (open) markAllRead();
  }, [open, markAllRead]);

  return (
    <Sheet
      open={open}
      onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}
      title={t('drawerTitle')}
      {...(unreadCount > 0 && { description: t('unreadCount', { count: unreadCount }) })}
      side="right"
      size="sm"
      closeLabel={t('closeLabel')}
    >
      {items.length > 0 ? (
        <ul className="space-y-3" role="list">
          {items.map((n) => (
            <li
              key={n.id}
              className="rounded-lg border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary"
            >
              {n.text}
            </li>
          ))}
        </ul>
      ) : (
        <p className="py-8 text-center text-sm text-ink-tertiary">{t('empty')}</p>
      )}
    </Sheet>
  );
}
