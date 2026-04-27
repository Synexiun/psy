'use client';

import { useTranslations } from 'next-intl';
import type { CheckInHistory } from '@/lib/api';
import { Sparkline, Skeleton } from '@disciplineos/design-system';

interface MoodSparklineProps {
  data?: CheckInHistory | undefined;
  isLoading: boolean;
}

const MOOD_STUB = [3, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 6, 8, 9, 8, 7, 8, 9, 8, 7];

export function MoodSparkline({ data, isLoading }: MoodSparklineProps) {
  const t = useTranslations('moodSparkline');

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
        <Skeleton variant="text" height="1rem" width="40%" />
        <Skeleton variant="rect" height="40px" className="mt-3" />
      </div>
    );
  }

  // Use real intensities when data is present; fall back to MOOD_STUB for
  // stub mode or when the backend has returned an empty history.
  const intensities =
    data && data.items.length > 0 ? data.items.map((item) => item.intensity) : MOOD_STUB;

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
          <p className="text-2xl font-semibold text-ink-primary tabular-nums">
            {intensities[intensities.length - 1]}
          </p>
          <p className="text-xs text-ink-quaternary">/ 10</p>
        </div>
      </div>
    </div>
  );
}
