'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import * as React from 'react';

interface SidebarNavProps {
  locale: string;
}

interface NavItemConfig {
  href: string;
  label: string;
  icon: React.ReactNode;
  exactMatch?: boolean;
  crisis?: boolean;
}

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

function JournalIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 6h8M5 9h8M5 12h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
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

function AssessmentsIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M9 2v5M2 9h5M11 9h5M9 11v5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function PatternsIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M3 14l4-5 3 3 3-4 3 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SettingsIcon(): React.ReactElement {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M9 1v2.5M9 14.5V17M1 9h2.5M14.5 9H17M3.34 3.34l1.77 1.77M12.89 12.89l1.77 1.77M14.66 3.34l-1.77 1.77M5.11 12.89l-1.77 1.77" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
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
// NavItem
// ---------------------------------------------------------------------------

function NavItem({
  href,
  label,
  icon,
  active,
  crisis = false,
}: {
  href: string;
  label: string;
  icon: React.ReactNode;
  active: boolean;
  crisis?: boolean;
}): React.ReactElement {
  const baseClasses =
    'group flex items-center gap-3 rounded-lg ps-3 pe-3 py-2.5 text-sm font-medium transition-all duration-fast';

  const stateClasses = crisis
    ? active
      ? 'bg-signal-crisis/10 text-signal-crisis'
      : 'text-signal-crisis hover:bg-signal-crisis/10 hover:text-signal-crisis'
    : active
      ? 'bg-accent-bronze/10 text-accent-bronze'
      : 'text-ink-secondary hover:bg-surface-tertiary hover:text-ink-primary';

  return (
    <a
      href={href}
      className={`${baseClasses} ${stateClasses}`}
      aria-current={active ? 'page' : undefined}
    >
      <span className="flex items-center" aria-hidden="true">
        {icon}
      </span>
      {label}
    </a>
  );
}

// ---------------------------------------------------------------------------
// SidebarNav
// ---------------------------------------------------------------------------

export function SidebarNav({ locale }: SidebarNavProps): React.ReactElement {
  const t = useTranslations('nav');
  const pathname = usePathname() ?? '';

  const mainItems: NavItemConfig[] = [
    {
      href: `/${locale}`,
      label: t('home'),
      icon: <HomeIcon />,
      exactMatch: true,
    },
    {
      href: `/${locale}/check-in`,
      label: t('checkIn'),
      icon: <CheckInIcon />,
    },
    {
      href: `/${locale}/journal`,
      label: t('journal'),
      icon: <JournalIcon />,
    },
    {
      href: `/${locale}/tools`,
      label: t('tools'),
      icon: <ToolsIcon />,
    },
    {
      href: `/${locale}/assessments`,
      label: t('assessments'),
      icon: <AssessmentsIcon />,
    },
    {
      href: `/${locale}/patterns`,
      label: t('patterns'),
      icon: <PatternsIcon />,
    },
    {
      href: `/${locale}/settings`,
      label: t('settings'),
      icon: <SettingsIcon />,
    },
  ];

  const crisisItem: NavItemConfig = {
    href: `/${locale}/crisis`,
    label: t('crisis'),
    icon: <CrisisIcon />,
    crisis: true,
  };

  function isActive(item: NavItemConfig): boolean {
    if (item.exactMatch) {
      return pathname === item.href;
    }
    return (
      pathname === item.href || pathname.startsWith(`${item.href}/`)
    );
  }

  return (
    <nav
      className="flex flex-1 flex-col px-4 py-4"
      aria-label="Main navigation"
    >
      <ul className="space-y-1" role="list">
        {mainItems.map((item) => (
          <li key={item.href}>
            <NavItem
              href={item.href}
              label={item.label}
              icon={item.icon}
              active={isActive(item)}
            />
          </li>
        ))}
      </ul>

      {/* Crisis link — always visible, separated, styled distinctly */}
      <div className="mt-auto border-t border-border-subtle pt-4">
        <NavItem
          href={crisisItem.href}
          label={crisisItem.label}
          icon={crisisItem.icon}
          active={isActive(crisisItem)}
          crisis
        />
      </div>
    </nav>
  );
}
