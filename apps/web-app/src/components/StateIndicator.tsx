'use client';

import { formatPercentClinical } from '@disciplineos/i18n-catalog';
import { Badge, Skeleton } from '@disciplineos/design-system';
import type { StateEstimateData } from '@/hooks/useDashboardData';

interface StateIndicatorProps {
  data: StateEstimateData | undefined;
  isLoading: boolean;
}

const stateConfig: Record<
  string,
  { label: string; tone: 'neutral' | 'calm' | 'warning' | 'crisis'; message: string }
> = {
  stable: {
    label: 'Stable',
    tone: 'calm',
    message: 'You appear steady right now. A good moment to build habits.',
  },
  baseline: {
    label: 'Baseline',
    tone: 'neutral',
    message: 'Resting state. Nothing urgent detected.',
  },
  rising_urge: {
    label: 'Rising urge',
    tone: 'warning',
    message: 'A urge is building. Try a coping tool or a short walk.',
  },
  peak_urge: {
    label: 'Peak urge',
    tone: 'crisis',
    message: 'This is the hardest moment. Use a tool or reach out.',
  },
  post_urge: {
    label: 'Post urge',
    tone: 'calm',
    message: 'The wave has passed. Be gentle with yourself.',
  },
};

export function StateIndicator({ data, isLoading }: StateIndicatorProps) {
  if (isLoading || !data) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
        <Skeleton variant="text" height="1.25rem" width="30%" />
        <Skeleton variant="text" height="1rem" width="60%" className="mt-2" />
      </div>
    );
  }

  const config = stateConfig[data.state_label] ?? {
    label: data.state_label,
    tone: 'neutral',
    message: 'State estimate available.',
  };

  return (
    <div
      className="flex items-center justify-between gap-4 rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm"
      role="img"
      aria-label={`Current state: ${config.label}`}
    >
      <div>
        <div className="flex items-center gap-2">
          <Badge tone={config.tone}>{config.label}</Badge>
          <span className="text-xs text-ink-tertiary tabular-nums">
            {formatPercentClinical(Math.round(data.confidence * 100))} confidence
          </span>
        </div>
        <p className="mt-2 text-sm text-ink-secondary">{config.message}</p>
      </div>
      <div
        className="hidden h-12 w-12 shrink-0 rounded-full sm:flex sm:items-center sm:justify-center"
        style={{
          backgroundColor:
            config.tone === 'calm'
              ? 'color-mix(in oklab, var(--color-signal-stable) 15%, transparent)'
              : config.tone === 'warning'
                ? 'color-mix(in oklab, var(--color-signal-warning) 15%, transparent)'
                : config.tone === 'crisis'
                  ? 'color-mix(in oklab, var(--color-signal-crisis) 15%, transparent)'
                  : 'var(--color-surface-tertiary)',
        }}
        aria-hidden="true"
      >
        <span className="text-2xl">
          {config.tone === 'calm' ? '🌿' : config.tone === 'warning' ? '⚡' : config.tone === 'crisis' ? '🔥' : '➖'}
        </span>
      </div>
    </div>
  );
}
