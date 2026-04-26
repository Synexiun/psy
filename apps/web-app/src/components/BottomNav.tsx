'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';

interface BottomNavProps {
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
  const colorClasses = crisis
    ? active
      ? 'text-signal-crisis'
      : 'text-signal-crisis/70 hover:text-signal-crisis'
    : active
      ? 'text-accent-bronze'
      : 'text-ink-quaternary hover:text-ink-tertiary';

  return (
    <a
      href={href}
      className={`flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors duration-fast ${colorClasses}`}
      aria-current={active ? 'page' : undefined}
    >
      <span className="text-xl leading-none" aria-hidden="true">
        {icon}
      </span>
      <span className="truncate max-w-[4rem]">{label}</span>
    </a>
  );
}

export function BottomNav({ locale }: BottomNavProps) {
  const t = useTranslations('nav');
  const pathname = usePathname() ?? '';

  // 5-item limit: Home, Check-in, Tools, Journal, Crisis
  const items: NavItemConfig[] = [
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
      href: `/${locale}/tools`,
      label: t('tools'),
      icon: '🧘',
    },
    {
      href: `/${locale}/journal`,
      label: t('journal'),
      icon: '📝',
    },
    {
      href: `/${locale}/crisis`,
      label: t('crisis'),
      icon: '🚨',
      crisis: true,
    },
  ];

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
      className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border-subtle bg-surface-secondary/90 backdrop-blur-sm lg:hidden"
      aria-label="Main navigation"
    >
      {items.map((item) => (
        <NavItem
          key={item.href}
          href={item.href}
          label={item.label}
          icon={item.icon}
          active={isActive(item)}
          crisis={item.crisis}
        />
      ))}
    </nav>
  );
}
