'use client';
import { estimateStateClientMirror } from '@/lib/clinical-mirrors';

it('estimateStateClientMirror_parity_with_server_for_all_intensities_0_to_10', () => {
  // Expected values derived from services/api/src/discipline/check_in/router.py
  // _intensity_to_state() — check-in-intensity-v1 model:
  //   0–3  → stable
  //   4–6  → rising_urge
  //   7–10 → peak_urge
  const expected: Record<number, string> = {
    0:  'stable',
    1:  'stable',
    2:  'stable',
    3:  'stable',
    4:  'rising_urge',
    5:  'rising_urge',
    6:  'rising_urge',
    7:  'peak_urge',
    8:  'peak_urge',
    9:  'peak_urge',
    10: 'peak_urge',
  };
  for (let i = 0; i <= 10; i++) {
    expect(estimateStateClientMirror(i)).toBe(expected[i]);
  }
});

it('estimateStateClientMirror_clamps_negative_input_to_stable', () => {
  // Intensity below 0 is clamped to 0 → "stable"
  expect(estimateStateClientMirror(-1)).toBe('stable');
  expect(estimateStateClientMirror(-100)).toBe('stable');
});

it('estimateStateClientMirror_clamps_input_above_10_to_peak_urge', () => {
  // Intensity above 10 is clamped to 10 → "peak_urge"
  expect(estimateStateClientMirror(11)).toBe('peak_urge');
  expect(estimateStateClientMirror(999)).toBe('peak_urge');
});

it('estimateStateClientMirror_boundary_3_is_stable', () => {
  // 3 is the upper bound of the "stable" band
  expect(estimateStateClientMirror(3)).toBe('stable');
});

it('estimateStateClientMirror_boundary_4_is_rising_urge', () => {
  // 4 is the lower bound of the "rising_urge" band
  expect(estimateStateClientMirror(4)).toBe('rising_urge');
});

it('estimateStateClientMirror_boundary_6_is_rising_urge', () => {
  // 6 is the upper bound of the "rising_urge" band
  expect(estimateStateClientMirror(6)).toBe('rising_urge');
});

it('estimateStateClientMirror_boundary_7_is_peak_urge', () => {
  // 7 is the lower bound of the "peak_urge" band (safety-log threshold is >=8)
  expect(estimateStateClientMirror(7)).toBe('peak_urge');
});
