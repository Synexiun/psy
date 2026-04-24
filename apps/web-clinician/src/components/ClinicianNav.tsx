'use client';

/**
 * ClinicianNav — top-of-page navigation bar for the clinician portal.
 *
 * Intentionally minimal: no sidebar. The portal is invite-only alpha (Phase 2)
 * and the information density is low enough that a single top nav suffices.
 *
 * Uses Clerk <UserButton> for sign-out and profile management.
 */

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { UserButton } from '@clerk/nextjs';

export function ClinicianNav(): React.JSX.Element {
  const params = useParams<{ locale: string }>();
  const locale = params.locale ?? 'en';

  return (
    <nav
      className="sticky top-0 z-30 border-b border-[hsl(220,14%,90%)] bg-white/95 backdrop-blur-sm"
      aria-label="Clinician portal navigation"
    >
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
        {/* Brand */}
        <Link
          href={`/${locale}`}
          className="flex items-center gap-2 text-sm font-semibold text-[hsl(222,47%,11%)] hover:opacity-80 transition-opacity"
        >
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-[hsl(217,91%,52%)] text-white text-xs font-bold select-none">
            D
          </span>
          <span>Discipline OS</span>
          <span
            className="hidden sm:inline rounded-full bg-[hsl(217,91%,96%)] px-2 py-0.5 text-xs font-medium text-[hsl(217,91%,32%)]"
            aria-label="Clinician portal"
          >
            Clinician
          </span>
        </Link>

        {/* Nav links + user */}
        <div className="flex items-center gap-4">
          <Link
            href={`/${locale}`}
            className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
          >
            Dashboard
          </Link>

          {/* Clerk UserButton handles sign-out + profile */}
          <UserButton
            afterSignOutUrl={`/${locale}/sign-in`}
            appearance={{
              elements: {
                avatarBox: 'h-8 w-8',
              },
            }}
          />
        </div>
      </div>
    </nav>
  );
}
