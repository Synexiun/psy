'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';

interface BackBreadcrumbProps {
  label: string;
  href: string;
}

export function BackBreadcrumb({ label, href }: BackBreadcrumbProps): React.ReactElement {
  const router = useRouter();
  return (
    <nav aria-label="Breadcrumb">
      <button
        type="button"
        onClick={() => { router.push(href); }}
        className="inline-flex items-center gap-1.5 min-h-[44px] text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.75}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        {label}
      </button>
    </nav>
  );
}
