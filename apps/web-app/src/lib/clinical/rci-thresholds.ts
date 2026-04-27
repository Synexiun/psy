// Pinned from Jacobson & Truax, 1991. Do NOT hand-edit.
// SE for PHQ-9 = sqrt(2) * SEM, where SEM = SD * sqrt(1 - r)
// Published value (SD=5.72, r=0.84): SE=2.68; RCI threshold=1.96*SE=5.26
export const RCI_PHQ9_THRESHOLD = 5.26 as const;

// Significance bands
export type RciSignificance = 'significant' | 'moderate' | 'non-significant';

export function classifyRciDelta(absDelta: number): RciSignificance {
  if (absDelta >= RCI_PHQ9_THRESHOLD) return 'significant';
  if (absDelta >= 2.5)               return 'moderate';
  return 'non-significant';
}
