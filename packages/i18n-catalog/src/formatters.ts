/**
 * Clinical number formatter — mirror of discipline.shared.i18n.formatters.format_number_clinical.
 *
 * All clinical scores (PHQ-9, GAD-7, RCI deltas, streak counts, percentages in reports)
 * must render as Latin digits regardless of locale. This is a hard non-negotiable rule:
 * reference totals from Kroenke 2001 / Spitzer 2006 are numeric and clinicians must read
 * them identically across locales.
 *
 * Body copy may localize digits. Clinical values NEVER do.
 *
 * Works in both Node.js (SSR) and browser (CSR): `toLocaleString('en', ...)` always
 * produces Latin digits regardless of the system locale.
 */

/** Format a clinical integer score as a Latin-digit string. */
export function formatNumberClinical(value: number): string {
  return value.toLocaleString('en', { useGrouping: false });
}

/** Format a clinical score with its maximum, e.g. "8/27". Always Latin digits. */
export function formatScoreWithMax(score: number, max: number): string {
  return `${formatNumberClinical(score)}/${formatNumberClinical(max)}`;
}

/**
 * Format a percentage for clinical reports. Always Latin digits, no locale-specific
 * decimal or thousands separators.
 */
export function formatPercentClinical(value: number, decimals = 0): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format an RCI (Reliable Change Index) delta — always show sign and Latin digits.
 * Positive values get a leading '+'; negative values keep their '-'.
 */
export function formatRciDelta(delta: number, decimals = 1): string {
  const sign = delta >= 0 ? '+' : '';
  return `${sign}${delta.toFixed(decimals)}`;
}
