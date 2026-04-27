'use client';

import { useTranslations } from 'next-intl';
import { formatPercentClinical } from '@disciplineos/i18n-catalog';
import { Card, Badge } from '@disciplineos/design-system';
import type { PatternData } from '@/hooks/useDashboardData';

interface PatternCardProps {
  pattern: PatternData;
}

const KNOWN_PATTERN_TYPES = new Set(['temporal', 'contextual', 'physiological', 'compound']);

const typeTones: Record<string, 'calm' | 'neutral' | 'warning'> = {
  temporal: 'calm',
  contextual: 'neutral',
  physiological: 'warning',
  compound: 'warning',
};

export function PatternCard({ pattern }: PatternCardProps) {
  const t = useTranslations('patterns');
  const tone = typeTones[pattern.pattern_type] ?? 'neutral';
  const typeLabel = KNOWN_PATTERN_TYPES.has(pattern.pattern_type)
    ? t(`typeLabels.${pattern.pattern_type}`)
    : pattern.pattern_type;

  return (
    <Card tone={tone} className="group relative">
      <div className="flex items-start justify-between gap-3">
        <Badge tone={tone}>{typeLabel}</Badge>
        <span className="text-xs text-ink-tertiary tabular-nums">
          {formatPercentClinical(Math.round(pattern.confidence * 100))} {t('confidenceLabel')}
        </span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-ink-secondary">{pattern.description}</p>
      {pattern.metadata && Object.keys(pattern.metadata).length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(pattern.metadata).slice(0, 3).map(([key, value]) => (
            <span
              key={key}
              className="inline-flex items-center rounded-md bg-surface-tertiary px-2 py-0.5 text-xs text-ink-secondary"
            >
              {key}: {String(value).slice(0, 20)}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}
