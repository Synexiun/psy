'use client';

import { useTranslations } from 'next-intl';
import { formatNumberClinical } from '@disciplineos/i18n-catalog';
import type { CheckInHistory } from '@/lib/api';
import { Sparkline, Skeleton } from '@disciplineos/design-system';

interface MoodSparklineProps {
  data?: CheckInHistory | undefined;
  isLoading: boolean;
}

export function MoodSparkline({ data, isLoading }: MoodSparklineProps) {
  const t = useTranslations('moodSparkline');

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <Skeleton variant="text" height="1rem" width="40%" />
          <Skeleton variant="text" height="0.75rem" width="25%" />
        </div>
        <div className="mt-4 flex items-end gap-4">
          <Skeleton variant="rect" height="48px" className="flex-1" />
          <div className="mb-1 space-y-1">
            <Skeleton variant="text" height="1.5rem" width="2rem" />
            <Skeleton variant="text" height="0.75rem" width="1.5rem" />
          </div>
        </div>
      </div>
    );
  }

  const intensities = data && data.items.length > 0
    ? data.items.map((item) => item.intensity)
    : null;

  if (!intensities) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
        <p className="text-sm font-medium text-ink-primary">{t('heading')}</p>
        <p className="mt-3 text-center text-sm text-ink-tertiary py-4">{t('noDataYet')}</p>
      </div>
    );
  }

  const lastValue = intensities[intensities.length - 1] ?? 0;

  return (
    <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-ink-primary">{t('heading')}</p>
        <span className="text-xs text-ink-tertiary">{t('subtitle', { count: intensities.length })}</span>
      </div>
      <div className="mt-4 flex items-end gap-4">
        <Sparkline
          data={intensities}
          width={240}
          height={48}
          color="var(--color-accent-bronze)"
          strokeWidth={2}
          ariaLabel={t('ariaLabel', { count: intensities.length })}
        />
        <div className="mb-1 text-end">
          <p className="text-2xl font-semibold text-ink-primary tabular-nums clinical-number">
            {formatNumberClinical(lastValue)}
          </p>
          <p className="text-xs text-ink-quaternary">/ {formatNumberClinical(10)}</p>
        </div>
      </div>
    </div>
  );
}
