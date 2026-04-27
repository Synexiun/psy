'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { BottomNav as BottomNavPrimitive } from '@disciplineos/design-system/primitives/BottomNav';
import type { BottomNavItem } from '@disciplineos/design-system/primitives/BottomNav';
import * as React from 'react';

// ---------------------------------------------------------------------------
// Inline SVG icons — no external dependency
// ---------------------------------------------------------------------------

function HomeIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M2 7.5L9 2l7 5.5V16a1 1 0 01-1 1H3a1 1 0 01-1-1V7.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M6.5 17V10.5h5V17" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

function CheckInIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M6 9l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ToolsIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M13.5 3.5a3 3 0 00-4.24 4.24L3 14l1 1 6.26-6.26A3 3 0 0013.5 3.5z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function JournalIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 6h8M5 9h8M5 12h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function CrisisIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M9 3v6M9 12v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="9" cy="9" r="7.25" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// AppBottomNav
// ---------------------------------------------------------------------------

interface AppBottomNavProps {
  locale: string;
}

export function BottomNav({ locale }: AppBottomNavProps): React.ReactElement {
  const t = useTranslations('nav');
  const pathname = usePathname() ?? '';

  const items: BottomNavItem[] = [
    { value: 'home', label: t('home'), icon: <HomeIcon />, href: `/${locale}` },
    { value: 'checkin', label: t('checkIn'), icon: <CheckInIcon />, href: `/${locale}/check-in` },
    { value: 'tools', label: t('tools'), icon: <ToolsIcon />, href: `/${locale}/tools` },
    { value: 'journal', label: t('journal'), icon: <JournalIcon />, href: `/${locale}/journal` },
    { value: 'crisis', label: t('crisis'), icon: <CrisisIcon />, href: `/${locale}/crisis`, crisis: true },
  ];

  function resolveActiveValue(): string | undefined {
    // home: exact match only
    if (pathname === `/${locale}` || pathname === `/${locale}/`) return 'home';
    // other items: prefix match
    for (const item of items.slice(1)) {
      if (item.href !== undefined && (pathname === item.href || pathname.startsWith(`${item.href}/`))) {
        return item.value;
      }
    }
    return undefined;
  }

  return <BottomNavPrimitive items={items} activeValue={resolveActiveValue()} />;
}
