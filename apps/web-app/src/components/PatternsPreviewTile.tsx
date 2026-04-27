'use client';

import * as React from 'react';
import { useTranslations } from 'next-intl';
import { Badge } from '@disciplineos/design-system';
import type { PatternData } from '@/hooks/useDashboardData';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface PatternsPreviewTileProps {
  pattern: PatternData;
}

// ---------------------------------------------------------------------------
// Tone map + known-type guard (mirrors PatternCard for consistency)
// ---------------------------------------------------------------------------

const typeTones: Record<string, 'calm' | 'neutral' | 'warning'> = {
  temporal: 'calm',
  contextual: 'neutral',
  physiological: 'warning',
  compound: 'warning',
};

const knownTypes = new Set(['temporal', 'contextual', 'physiological', 'compound']);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * PatternsPreviewTile — lightweight summary tile for the Dashboard patterns section.
 *
 * Intentionally thin: shows only the pattern type badge and the 1-line description.
 * No dismiss / snooze / lifecycle UI — that is InsightCard's responsibility
 * (used on the dedicated Patterns page, Task 7.2).
 */
export function PatternsPreviewTile({ pattern }: PatternsPreviewTileProps): React.ReactElement {
  const t = useTranslations('patterns');
  const tone = typeTones[pattern.pattern_type] ?? 'neutral';
  const label = knownTypes.has(pattern.pattern_type)
    ? t(`types.${pattern.pattern_type}`)
    : pattern.pattern_type;

  return (
    <div
      className="flex items-start gap-3 rounded-xl border border-border-subtle bg-surface-secondary p-4 shadow-sm"
      data-testid="pattern-preview-tile"
    >
      <Badge tone={tone}>{label}</Badge>
      <p className="text-sm leading-relaxed text-ink-secondary">{pattern.description}</p>
    </div>
  );
}
