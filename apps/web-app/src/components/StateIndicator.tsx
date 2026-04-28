'use client';

import * as React from 'react';
import { useTranslations } from 'next-intl';
import { formatPercentClinical } from '@disciplineos/i18n-catalog';
import { Badge, Skeleton } from '@disciplineos/design-system';
import type { StateEstimateData } from '@/hooks/useDashboardData';

interface StateIndicatorProps {
  data: StateEstimateData | undefined;
  isLoading: boolean;
}

const stateTones: Record<string, 'neutral' | 'calm' | 'warning' | 'crisis'> = {
  stable: 'calm',
  baseline: 'neutral',
  rising_urge: 'warning',
  peak_urge: 'crisis',
  post_urge: 'calm',
};

export function StateIndicator({ data, isLoading }: StateIndicatorProps) {
  const t = useTranslations('stateIndicator');

  if (isLoading || !data) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm">
        <Skeleton variant="text" height="1.25rem" width="30%" />
        <Skeleton variant="text" height="1rem" width="60%" className="mt-2" />
      </div>
    );
  }

  type StateKey = 'stable' | 'baseline' | 'risingUrge' | 'peakUrge' | 'postUrge';
  const stateKeyMap: Record<string, StateKey> = {
    stable: 'stable',
    baseline: 'baseline',
    rising_urge: 'risingUrge',
    peak_urge: 'peakUrge',
    post_urge: 'postUrge',
  };

  const stateKey = stateKeyMap[data.state_label];
  const label = stateKey
    ? t(`${stateKey}.label`)
    : t('fallback.label', { state: data.state_label });
  const message = stateKey ? t(`${stateKey}.message`) : t('fallback.message');
  const tone = stateTones[data.state_label] ?? 'neutral';

  const config = { label, tone, message };

  return (
    <section
      className="flex items-center justify-between gap-4 rounded-xl border border-border-subtle bg-surface-secondary p-5 shadow-sm"
      aria-label={t('ariaLabel', { label: config.label })}
    >
      <div>
        <div className="flex items-center gap-2">
          <Badge tone={config.tone}>{config.label}</Badge>
          <span className="text-xs text-ink-tertiary tabular-nums">
            {formatPercentClinical(Math.round(data.confidence * 100))} {t('confidence')}
          </span>
        </div>
        <p className="mt-2 text-sm text-ink-secondary">{config.message}</p>
      </div>
      <div
        className={[
          'hidden h-4 w-4 shrink-0 rounded-full sm:block',
          config.tone === 'calm'
            ? 'bg-signal-stable'
            : config.tone === 'warning'
              ? 'bg-signal-warning'
              : config.tone === 'crisis'
                ? 'bg-signal-crisis'
                : 'bg-ink-quaternary',
        ].join(' ')}
        aria-hidden="true"
      />
    </section>
  );
}
