'use client';

import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import { ProgressRing, Skeleton } from './primitives';
import type { StreakData } from '@/hooks/useDashboardData';

interface StreakWidgetProps {
  data: StreakData | undefined;
  isLoading: boolean;
}

export function StreakWidget({ data, isLoading }: StreakWidgetProps) {
  if (isLoading || !data) {
    return (
      <div className="flex items-center gap-6 rounded-xl border border-border-subtle bg-surface-secondary p-6 shadow-sm">
        <Skeleton variant="circle" height="120px" width="120px" />
        <div className="flex-1 space-y-3">
          <Skeleton variant="text" height="1.5rem" width="60%" />
          <Skeleton variant="text" height="1rem" width="40%" />
          <Skeleton variant="text" height="1rem" width="80%" />
        </div>
      </div>
    );
  }

  const continuousMax = Math.max(data.continuous_days, 30);
  const resilienceMax = Math.max(data.resilience_days, 60);

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="flex items-center gap-5 rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm transition-shadow hover:shadow-md">
        <ProgressRing
          value={data.continuous_days}
          max={continuousMax}
          size={100}
          strokeWidth={8}
          color="var(--color-accent-bronze)"
          label={formatNumberClinical(data.continuous_days)}
          sublabel="Continuous"
          ariaLabel={`Continuous streak: ${formatNumberClinical(data.continuous_days)} days`}
        />
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-primary">Continuous streak</p>
          <p className="mt-0.5 text-sm text-ink-tertiary">
            {data.continuous_days === 0
              ? 'Every day is a fresh start.'
              : `${formatNumberClinical(data.continuous_days)} days strong.`}
          </p>
          {data.continuous_streak_start && (
            <p className="mt-1 text-xs text-ink-tertiary">
              Since {new Date(data.continuous_streak_start).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-5 rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm transition-shadow hover:shadow-md">
        <ProgressRing
          value={data.resilience_days}
          max={resilienceMax}
          size={100}
          strokeWidth={8}
          color="var(--color-signal-stable)"
          label={formatNumberClinical(data.resilience_days)}
          sublabel="Resilience"
          ariaLabel={`Resilience streak: ${formatNumberClinical(data.resilience_days)} days`}
        />
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-primary">Resilience streak</p>
          <p className="mt-0.5 text-sm text-ink-tertiary">
            {data.resilience_days === 0
              ? 'Building resilience, one moment at a time.'
              : `${formatNumberClinical(data.resilience_days)} days of growth.`}
          </p>
          <p className="mt-1 text-xs text-ink-tertiary">
            {formatNumberClinical(data.resilience_urges_handled_total)} urges handled
          </p>
        </div>
      </div>
    </div>
  );
}
