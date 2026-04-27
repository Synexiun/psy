'use client';

import * as React from 'react';

interface QuickActionsProps {
  locale: string;
}

// ---------------------------------------------------------------------------
// Inline SVG icons (aria-hidden, no emoji)
// ---------------------------------------------------------------------------

function IconCheckIn(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      {/* person silhouette */}
      <circle cx="12" cy="7" r="4" />
      <path d="M5.5 20c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5" />
    </svg>
  );
}

function IconCopingTool(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      {/* wrench / tool */}
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  );
}

function IconJournal(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      {/* notepad */}
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <line x1="9" y1="8" x2="15" y2="8" />
      <line x1="9" y1="12" x2="15" y2="12" />
      <line x1="9" y1="16" x2="13" y2="16" />
    </svg>
  );
}

function IconCrisis(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      {/* exclamation triangle */}
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function QuickActions({ locale }: QuickActionsProps): React.ReactElement {
  const actions = [
    {
      label: 'Check in',
      description: 'Log how you feel right now',
      Icon: IconCheckIn,
      href: `/${locale}/check-in`,
    },
    {
      label: 'Coping tool',
      description: 'Open your toolkit',
      Icon: IconCopingTool,
      href: `/${locale}/tools`,
    },
    {
      label: 'Journal',
      description: 'Write or speak',
      Icon: IconJournal,
      href: `/${locale}/journal`,
    },
    {
      label: 'Crisis help',
      description: 'Get support now',
      Icon: IconCrisis,
      href: `/${locale}/crisis`,
    },
  ];

  return (
    <section aria-labelledby="quick-actions" data-testid="quick-actions-section">
      <h2 id="quick-actions" className="sr-only">
        Quick actions
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {actions.map((action) => (
          <a
            key={action.label}
            href={action.href}
            className="group flex flex-col items-center gap-2 rounded-xl border border-border-subtle bg-surface-secondary p-4 text-center shadow-sm transition-all duration-base hover:-translate-y-0.5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
          >
            <span
              className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-tertiary text-ink-secondary transition-colors group-hover:bg-accent-bronze/10 group-hover:text-accent-bronze"
              aria-hidden="true"
            >
              <action.Icon />
            </span>
            <div>
              <p className="text-sm font-medium text-ink-primary">{action.label}</p>
              <p className="text-xs text-ink-quaternary">{action.description}</p>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
