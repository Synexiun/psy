'use client';

import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { TopBar } from '@disciplineos/design-system/primitives/TopBar';
import type { LocaleOption } from '@disciplineos/design-system/primitives/TopBar';
import { SidebarNav } from './SidebarNav';
import { BottomNav } from './BottomNav';
import { WordmarkSvg } from './WordmarkSvg';
import { NotificationsDrawer } from './NotificationsDrawer';
import { OfflineIndicator, useIsOnline } from './OfflineIndicator';
import { useNotificationCount } from '@/hooks/useNotificationCount';
import * as React from 'react';

const LOCALE_OPTIONS: LocaleOption[] = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Français' },
  { value: 'ar', label: 'العربية' },
  { value: 'fa', label: 'فارسی' },
];

interface LayoutProps {
  children: React.ReactNode;
  locale: string;
}

export function Layout({ children, locale }: LayoutProps): React.ReactElement {
  useTranslations();
  const [notifOpen, setNotifOpen] = useState<boolean>(false);
  const { count } = useNotificationCount();
  const isOnline = useIsOnline();

  return (
    <div className="flex min-h-screen flex-col bg-surface-primary">
      <TopBar
        wordmark={<WordmarkSvg />}
        locale={locale}
        localeOptions={LOCALE_OPTIONS}
        bellCount={count}
        onBellClick={() => setNotifOpen(true)}
        isOffline={!isOnline}
        avatar={<OfflineIndicator />}
      />
      <div className="flex flex-1">
        <aside
          aria-label="Main navigation"
          className="hidden lg:flex lg:w-64 lg:flex-col lg:border-e lg:border-border-subtle lg:bg-surface-secondary"
        >
          <SidebarNav locale={locale} />
        </aside>
        <main className="flex-1 overflow-y-auto pb-[calc(6rem+env(safe-area-inset-bottom))] lg:pb-8">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
            {children}
          </div>
        </main>
      </div>
      <BottomNav locale={locale} />
      <NotificationsDrawer
        open={notifOpen}
        onClose={() => setNotifOpen(false)}
      />
    </div>
  );
}
