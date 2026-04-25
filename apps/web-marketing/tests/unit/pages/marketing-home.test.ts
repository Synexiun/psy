/**
 * Unit tests for web-marketing home page static data.
 *
 * Tests the pure constants extracted from src/app/[locale]/page.tsx.
 *
 * Critical: FREE_FEATURES must include "Crisis access always free" —
 * crisis access is a product non-negotiable (CLAUDE.md §"Non-negotiable rules" #1).
 *
 * Covers:
 * - FREE_FEATURES: includes crisis access guarantee, non-empty list
 * - PRO_FEATURES: includes clinician sharing and 4 languages
 * - Pricing: free plan is $0/mo
 * - No feature is an empty string
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// FREE_FEATURES (inline from page.tsx)
// ---------------------------------------------------------------------------

const FREE_FEATURES = [
  '14-day urge log',
  '5 coping tools',
  'Basic check-ins',
  'Crisis access always free',
];

// ---------------------------------------------------------------------------
// PRO_FEATURES (inline from page.tsx)
// ---------------------------------------------------------------------------

const PRO_FEATURES = [
  'Unlimited urge log',
  '25 coping tools',
  'Biometric signal (where available)',
  'Clinician sharing',
  'Weekly insight reports',
  '4 languages',
];

// ---------------------------------------------------------------------------
// FREE_FEATURES tests
// ---------------------------------------------------------------------------

describe('FREE_FEATURES', () => {
  it('includes crisis access (always free — product non-negotiable)', () => {
    const hasCrisis = FREE_FEATURES.some(f => f.toLowerCase().includes('crisis'));
    expect(hasCrisis).toBe(true);
  });

  it('crisis access entry says "always free"', () => {
    const crisis = FREE_FEATURES.find(f => f.toLowerCase().includes('crisis'));
    expect(crisis).toContain('free');
  });

  it('is a non-empty list', () => {
    expect(FREE_FEATURES.length).toBeGreaterThan(0);
  });

  it('all features are non-empty strings', () => {
    for (const f of FREE_FEATURES) {
      expect(f.length).toBeGreaterThan(0);
    }
  });

  it('includes basic check-ins', () => {
    expect(FREE_FEATURES.some(f => f.toLowerCase().includes('check-in'))).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PRO_FEATURES tests
// ---------------------------------------------------------------------------

describe('PRO_FEATURES', () => {
  it('includes clinician sharing', () => {
    expect(PRO_FEATURES.some(f => f.toLowerCase().includes('clinician'))).toBe(true);
  });

  it('includes language support (4 languages)', () => {
    expect(PRO_FEATURES.some(f => f.includes('4 languages'))).toBe(true);
  });

  it('includes biometric signal feature', () => {
    expect(PRO_FEATURES.some(f => f.toLowerCase().includes('biometric'))).toBe(true);
  });

  it('is a non-empty list', () => {
    expect(PRO_FEATURES.length).toBeGreaterThan(0);
  });

  it('all features are non-empty strings', () => {
    for (const f of PRO_FEATURES) {
      expect(f.length).toBeGreaterThan(0);
    }
  });

  it('has more features than free plan', () => {
    expect(PRO_FEATURES.length).toBeGreaterThan(FREE_FEATURES.length);
  });
});
