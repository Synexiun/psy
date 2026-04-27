// No 'use client' — this is a pure utility module usable in both RSC and client

export type UrgeIntensity = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

/**
 * Client-side mirror of discipline.check_in.router._intensity_to_state.
 * Used for Storybook/test stubs only — never called in production paths.
 *
 * Band calibration mirrors the backend (check-in-intensity-v1 model):
 *   0–3  → "stable"      (no significant urge; SUDS below moderate threshold)
 *   4–6  → "rising_urge" (moderate; intervention eligible)
 *   7–10 → "peak_urge"   (high; safety-stream event at >=8)
 *
 * Must produce identical output to the backend for all intensity values 0–10.
 * Source: services/api/src/discipline/check_in/router.py _intensity_to_state()
 */
export function estimateStateClientMirror(intensity: number): string {
  // Clamp to [0, 10] to match backend Field(ge=0, le=10) validation.
  const clamped = Math.max(0, Math.min(10, Math.round(intensity)));

  if (clamped <= 3) {
    return 'stable';
  }
  if (clamped <= 6) {
    return 'rising_urge';
  }
  return 'peak_urge';
}
