'use client';

import { useTranslations } from 'next-intl';
import { SidebarNav } from './SidebarNav';
import { BottomNav } from './BottomNav';

interface LayoutProps {
  children: React.ReactNode;
  locale: string;
}

export function Layout({ children, locale }: LayoutProps) {
  const t = useTranslations();

  return (
    <div className="flex min-h-screen bg-surface-50">
      <aside aria-label="Main navigation" className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-surface-200 lg:bg-surface-0">
        <div className="flex h-16 items-center px-6">
          <span className="text-lg font-semibold tracking-tight text-ink-900">
            {t('app.name')}
          </span>
        </div>
        <SidebarNav locale={locale} />
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-surface-200 bg-surface-0 px-4 sm:px-6 lg:hidden">
          <span className="text-lg font-semibold tracking-tight text-ink-900">
            {t('app.name')}
          </span>
          <a
            href={`/${locale}/crisis`}
            className="inline-flex items-center rounded-lg bg-crisis-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-crisis-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-crisis-300"
          >
            {t('crisis.cta.primary')}
          </a>
        </header>

        <main className="flex-1 overflow-y-auto pb-24 lg:pb-8">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
            {children}
          </div>
        </main>

        <BottomNav locale={locale} />
      </div>
    </div>
  );
}
