'use client';
/**
 * SeverityBand — displays the PHQ-9 severity band for a given score.
 *
 * Thresholds are pinned from Kroenke, Spitzer, Williams (2001), Table 3.
 * They mirror the Python source of truth at:
 *   services/api/src/discipline/psychometric/scoring/phq9.py :: PHQ9_SEVERITY_THRESHOLDS
 *
 * Rule #9 enforcement: the score is always rendered in Latin digits via
 * `toLocaleString('en', { useGrouping: false })` regardless of locale prop.
 *
 * Progress bar: 5 segments, one highlighted per band.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// Threshold constants — mirrored from Python. Update via clinical QA only.
// Python bands: (4,"none"),(9,"mild"),(14,"moderate"),(19,"moderately_severe"),(27,"severe")
// ---------------------------------------------------------------------------

type Severity = 'minimal' | 'mild' | 'moderate' | 'severe' | 'extreme';

const BAND_ORDER: Severity[] = ['minimal', 'mild', 'moderate', 'severe', 'extreme'];

const BAND_LABELS: Record<Severity, string> = {
  minimal:  'Minimal',
  mild:     'Mild',
  moderate: 'Moderate',
  severe:   'Severe',
  extreme:  'Extreme',
};

const BAND_COLORS: Record<Severity, string> = {
  minimal:  'bg-signal-stable',
  mild:     'bg-yellow-400',
  moderate: 'bg-amber-500',
  severe:   'bg-signal-warning',
  extreme:  'bg-red-600',
};

function classifyPhq9(score: number): Severity {
  if (score <= 4)  return 'minimal';
  if (score <= 9)  return 'mild';
  if (score <= 14) return 'moderate';
  if (score <= 19) return 'severe';
  return 'extreme';
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SeverityBandProps {
  /** PHQ-9 score (0–27) */
  score: number;
  /** Locale — for Latin digit enforcement (Rule #9) */
  locale?: string;
  /** Additional classes on root */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SeverityBand({
  score,
  locale: _locale,
  className,
}: SeverityBandProps): React.ReactElement {
  const severity = classifyPhq9(score);
  // Rule #9: always render clinical scores in Latin digits
  const formattedScore = score.toLocaleString('en', { useGrouping: false });

  return (
    <div
      className={['flex flex-col gap-1', className].filter(Boolean).join(' ')}
    >
      <span data-testid="severity-score">{formattedScore}</span>
      <span data-testid="severity-band">{BAND_LABELS[severity]}</span>
      {/* 5-segment progress bar — one segment highlighted per band */}
      <div
        role="presentation"
        aria-hidden="true"
        className="flex gap-0.5"
      >
        {BAND_ORDER.map((band) => (
          <div
            key={band}
            className={[
              'h-1.5 flex-1 rounded-sm',
              band === severity
                ? BAND_COLORS[band]
                : 'bg-gray-200',
            ].join(' ')}
          />
        ))}
      </div>
    </div>
  );
}
