'use client';

import * as React from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import { ProgressRing, Skeleton } from '@disciplineos/design-system';
import { ResilienceRing } from '@disciplineos/design-system/clinical/ResilienceRing';
import type { StreakData } from '@/hooks/useDashboardData';

interface StreakWidgetProps {
  data: StreakData | undefined;
  isLoading: boolean;
}

export function StreakWidget({ data, isLoading }: StreakWidgetProps) {
  const t = useTranslations('streak');
  const locale = useLocale();

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
  const resilienceMax = Math.max(data.resilience_days, 30);

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
          sublabel={t('continuous.sublabel')}
          ariaLabel={t('continuous.ariaLabel', { days: formatNumberClinical(data.continuous_days) })}
        />
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-primary">{t('continuous.heading')}</p>
          <p className="mt-0.5 text-sm text-ink-tertiary">
            {data.continuous_days === 0
              ? t('continuous.zeroMotivation')
              : t('continuous.daysStrong', { days: formatNumberClinical(data.continuous_days) })}
          </p>
          {data.continuous_streak_start && (
            <p className="mt-1 text-xs text-ink-tertiary">
              {t('continuous.since', { date: new Date(data.continuous_streak_start).toLocaleDateString(locale) })}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-5 rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm transition-shadow hover:shadow-md">
        <ResilienceRing
          value={data.resilience_days}
          max={resilienceMax}
          size={100}
          ariaLabel={t('resilience.ariaLabel', { days: formatNumberClinical(data.resilience_days) })}
        />
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-primary">{t('resilience.heading')}</p>
          <p className="mt-0.5 text-sm text-ink-tertiary">
            {data.resilience_days === 0
              ? t('resilience.zeroMotivation')
              : t('resilience.daysGrowth', { days: formatNumberClinical(data.resilience_days) })}
          </p>
          <p className="mt-1 text-xs text-ink-tertiary">
            {t('resilience.urgesHandled', { count: formatNumberClinical(data.resilience_urges_handled_total) })}
          </p>
        </div>
      </div>
    </div>
  );
}
