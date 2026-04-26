'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';

interface SidebarNavProps {
  locale: string;
}

interface NavItemConfig {
  href: string;
  label: string;
  icon: string;
  exactMatch?: boolean;
  crisis?: boolean;
}

function NavItem({
  href,
  label,
  icon,
  active,
  crisis = false,
}: {
  href: string;
  label: string;
  icon: string;
  active: boolean;
  crisis?: boolean;
}) {
  const baseClasses =
    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-fast';

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
      <span className="text-lg leading-none" aria-hidden="true">
        {icon}
      </span>
      {label}
    </a>
  );
}

export function SidebarNav({ locale }: SidebarNavProps) {
  const t = useTranslations('nav');
  const pathname = usePathname() ?? '';

  const mainItems: NavItemConfig[] = [
    {
      href: `/${locale}`,
      label: t('home'),
      icon: '🏠',
      exactMatch: true,
    },
    {
      href: `/${locale}/check-in`,
      label: t('checkIn'),
      icon: '✅',
    },
    {
      href: `/${locale}/journal`,
      label: t('journal'),
      icon: '📝',
    },
    {
      href: `/${locale}/tools`,
      label: t('tools'),
      icon: '🧘',
    },
    {
      href: `/${locale}/assessments`,
      label: t('assessments'),
      icon: '📊',
    },
    {
      href: `/${locale}/patterns`,
      label: t('patterns'),
      icon: '🔮',
    },
    {
      href: `/${locale}/settings`,
      label: t('settings'),
      icon: '⚙️',
    },
  ];

  const crisisItem: NavItemConfig = {
    href: `/${locale}/crisis`,
    label: t('crisis'),
    icon: '🚨',
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
