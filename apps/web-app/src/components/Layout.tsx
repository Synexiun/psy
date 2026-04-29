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
import { RouteAnnouncer } from './RouteAnnouncer';
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
      <RouteAnnouncer />
      {/* Skip navigation — WCAG 2.4.1 bypass blocks */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-accent-bronze focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:outline-none"
      >
        Skip to main content
      </a>
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
        <main id="main-content" tabIndex={-1} className="flex-1 overflow-y-auto pb-[calc(6rem+env(safe-area-inset-bottom))] lg:pb-8 focus:outline-none">
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
