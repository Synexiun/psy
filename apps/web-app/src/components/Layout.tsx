'use client';

import { useTranslations } from 'next-intl';
import { TopBar } from '@disciplineos/design-system/primitives/TopBar';
import type { LocaleOption } from '@disciplineos/design-system/primitives/TopBar';
import { SidebarNav } from './SidebarNav';
import { BottomNav } from './BottomNav';
import { WordmarkSvg } from './WordmarkSvg';
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
  // useTranslations kept for any future layout-level translated strings
  useTranslations();

  // onBellClick: undefined — wired in Task 6.7b (NotificationsDrawer)
  return (
    <div className="flex min-h-screen flex-col bg-surface-primary">
      <TopBar
        wordmark={<WordmarkSvg />}
        locale={locale}
        localeOptions={LOCALE_OPTIONS}
      />
      <div className="flex flex-1">
        <aside
          aria-label="Main navigation"
          className="hidden lg:flex lg:w-64 lg:flex-col lg:border-e lg:border-border-subtle lg:bg-surface-secondary"
        >
          <SidebarNav locale={locale} />
        </aside>
        <main className="flex-1 overflow-y-auto pb-24 lg:pb-8">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
            {children}
          </div>
        </main>
      </div>
      <BottomNav locale={locale} />
    </div>
  );
}
