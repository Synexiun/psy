export const CLINICAL_NUMERIC_PATTERNS: readonly RegExp[] = [
  /_total$/i,
  /Total$/,
  /^intensity$/i,
  /^score$/i,
  /^severity$/i,
  /^band$/i,
  /^phq9/i,
  /^phq_9_/i,
  /^gad7/i,
  /^gad_7_/i,
  /^audit_?c/i,
  /^auditC/,
  /^rci_/i,
  /^rci[A-Z]/,
];

export function isClinicalNumericIdentifier(name: string): boolean {
  return CLINICAL_NUMERIC_PATTERNS.some((re) => re.test(name));
}
