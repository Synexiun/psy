'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserButton } from '@clerk/nextjs';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
}

function NavLink({ href, children }: NavLinkProps): React.JSX.Element {
  const pathname = usePathname();
  // Strip locale prefix for active comparison — pathname is /{locale}/...
  const segments = pathname.split('/').filter(Boolean);
  const pathWithoutLocale = '/' + segments.slice(1).join('/');
  const isActive = pathWithoutLocale === href || (href !== '/' && pathWithoutLocale.startsWith(href));

  return (
    <Link
      href={href}
      className={[
        'rounded-md px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-[hsl(217,91%,96%)] text-[hsl(217,91%,32%)]'
          : 'text-[hsl(215,16%,47%)] hover:bg-[hsl(220,14%,96%)] hover:text-[hsl(222,47%,11%)]',
      ].join(' ')}
      aria-current={isActive ? 'page' : undefined}
    >
      {children}
    </Link>
  );
}

export function EnterpriseNav(): React.JSX.Element {
  return (
    <nav
      className="sticky top-0 z-30 flex items-center justify-between border-b border-[hsl(220,14%,90%)] bg-white px-6 py-3"
      aria-label="Enterprise navigation"
    >
      {/* Logo */}
      <div className="flex items-center gap-6">
        <span className="text-sm font-semibold text-[hsl(222,47%,11%)]" aria-label="Discipline OS Enterprise">
          Discipline OS{' '}
          <span className="font-normal text-[hsl(215,16%,47%)]" aria-hidden="true">
            ·
          </span>{' '}
          <span className="text-[hsl(217,91%,52%)]">Enterprise</span>
        </span>

        {/* Nav links — no individual user data links, ever */}
        <div className="hidden items-center gap-1 sm:flex" role="list">
          <NavLink href="/">Dashboard</NavLink>
          {/*
            "Members" link intentionally omitted — the enterprise portal is
            aggregate-only. Individual member detail views must not exist here.
            The nav item is listed as a placeholder but points nowhere drillable.
          */}
          <NavLink href="/reports">Reports</NavLink>
          <NavLink href="/settings">Settings</NavLink>
        </div>
      </div>

      {/* User controls */}
      <div className="flex items-center gap-3">
        <UserButton
          appearance={{
            elements: {
              avatarBox: 'h-8 w-8',
            },
          }}
        />
      </div>
    </nav>
  );
}
