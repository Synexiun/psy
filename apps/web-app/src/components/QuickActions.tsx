'use client';

interface QuickActionsProps {
  locale: string;
}

export function QuickActions({ locale }: QuickActionsProps) {

  const actions = [
    {
      label: 'Check in',
      description: 'Log how you feel right now',
      icon: '✋',
      variant: 'primary' as const,
      href: `/${locale}/check-in`,
    },
    {
      label: 'Coping tool',
      description: 'Open your toolkit',
      icon: '🧘',
      variant: 'calm' as const,
      href: `/${locale}/tools`,
    },
    {
      label: 'Journal',
      description: 'Write or speak',
      icon: '📝',
      variant: 'secondary' as const,
      href: `/${locale}/journal`,
    },
    {
      label: 'Crisis help',
      description: 'Get support now',
      icon: '🚨',
      variant: 'crisis' as const,
      href: `/${locale}/crisis`,
    },
  ];

  return (
    <section aria-labelledby="quick-actions">
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
              className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-tertiary text-xl transition-colors group-hover:bg-accent-bronze/10"
              aria-hidden="true"
            >
              {action.icon}
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
