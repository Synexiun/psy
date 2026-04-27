'use client';

import { Badge } from '@disciplineos/design-system';
import type { PatternData } from '@/hooks/useDashboardData';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface PatternsPreviewTileProps {
  pattern: PatternData;
}

// ---------------------------------------------------------------------------
// Type label + tone maps (mirrors PatternCard for consistency)
// ---------------------------------------------------------------------------

const typeLabels: Record<string, string> = {
  temporal: 'Time pattern',
  contextual: 'Context pattern',
  physiological: 'Body signal',
  compound: 'Compound signal',
};

const typeTones: Record<string, 'calm' | 'neutral' | 'warning'> = {
  temporal: 'calm',
  contextual: 'neutral',
  physiological: 'warning',
  compound: 'warning',
};

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
  const tone = typeTones[pattern.pattern_type] ?? 'neutral';
  const label = typeLabels[pattern.pattern_type] ?? pattern.pattern_type;

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
