// Pinned from Kroenke et al., 2001. Do NOT hand-edit — update via clinical QA process.
// Mirror of services/api/src/discipline/psychometric/scoring/phq9.py :: PHQ9_SEVERITY_THRESHOLDS
// Python bands: (4,"none"),(9,"mild"),(14,"moderate"),(19,"moderately_severe"),(27,"severe")
export const PHQ9_SEVERITY_THRESHOLDS = {
  minimal:  { min: 0,  max: 4  },
  mild:     { min: 5,  max: 9  },
  moderate: { min: 10, max: 14 },
  severe:   { min: 15, max: 19 },
  extreme:  { min: 20, max: 27 },
} as const;

export type Phq9Severity = keyof typeof PHQ9_SEVERITY_THRESHOLDS;

export function classifyPhq9(score: number): Phq9Severity {
  if (score <= 4)  return 'minimal';
  if (score <= 9)  return 'mild';
  if (score <= 14) return 'moderate';
  if (score <= 19) return 'severe';
  return 'extreme';
}
