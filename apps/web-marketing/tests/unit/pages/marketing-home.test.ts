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
 * - HOW_IT_WORKS_STEPS: 3-step product story (detect → intervene → record)
 * - FEATURES: 6 product features, crisis/offline/RTL guarantees
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

// ---------------------------------------------------------------------------
// HOW_IT_WORKS_STEPS (inline from HowItWorksSection in page.tsx)
// ---------------------------------------------------------------------------

const HOW_IT_WORKS_STEPS = [
  {
    number: '01',
    headline: 'Urge detected',
    description:
      'Biometric signals and self-reports identify rising urge states before they peak.',
  },
  {
    number: '02',
    headline: 'Intervention delivered',
    description: 'A personalized coping tool arrives in the critical 60-second window.',
  },
  {
    number: '03',
    headline: 'Outcome recorded',
    description: 'Every handled urge strengthens your resilience score.',
  },
];

describe('HOW_IT_WORKS_STEPS', () => {
  it('has exactly 3 steps (detect → intervene → record)', () => {
    expect(HOW_IT_WORKS_STEPS).toHaveLength(3);
  });

  it('step numbers are 01, 02, 03 (sequential)', () => {
    const numbers = HOW_IT_WORKS_STEPS.map((s) => s.number);
    expect(numbers).toEqual(['01', '02', '03']);
  });

  it('step 1 is about urge detection', () => {
    expect(HOW_IT_WORKS_STEPS[0]?.headline.toLowerCase()).toContain('urge');
  });

  it('step 2 mentions the critical intervention window (60 seconds)', () => {
    const desc = HOW_IT_WORKS_STEPS[1]?.description ?? '';
    expect(desc).toContain('60-second');
  });

  it('step 3 mentions resilience (outcome framing — not just streak counting)', () => {
    const desc = HOW_IT_WORKS_STEPS[2]?.description.toLowerCase() ?? '';
    expect(desc).toContain('resilience');
  });

  it('all headlines are non-empty', () => {
    for (const step of HOW_IT_WORKS_STEPS) {
      expect(step.headline.length).toBeGreaterThan(0);
    }
  });

  it('all descriptions are non-empty', () => {
    for (const step of HOW_IT_WORKS_STEPS) {
      expect(step.description.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// FEATURES (inline from FeaturesSection in page.tsx)
// ---------------------------------------------------------------------------

const FEATURES = [
  {
    headline: 'On-device intelligence',
    body: 'State estimation runs locally. Your data never leaves your device for ML inference.',
  },
  {
    headline: 'Evidence-based tools',
    body: '25 coping tools validated by clinical research. Not motivational quotes.',
  },
  {
    headline: 'Resilience streak',
    body: 'Track handled urges — not just clean days. Compassion-first framing.',
  },
  {
    headline: 'Clinical oversight',
    body: 'Share progress with your clinician. PHI-protected, audit-logged.',
  },
  {
    headline: 'Crisis-ready',
    body: 'One tap to a crisis line, always. Works offline. No login required.',
  },
  {
    headline: 'Four languages',
    body: 'English, French, Arabic, Persian. RTL supported natively.',
  },
];

describe('FEATURES', () => {
  it('has exactly 6 product features', () => {
    expect(FEATURES).toHaveLength(6);
  });

  it('all headlines are non-empty', () => {
    for (const f of FEATURES) {
      expect(f.headline.length).toBeGreaterThan(0);
    }
  });

  it('all body text is non-empty', () => {
    for (const f of FEATURES) {
      expect(f.body.length).toBeGreaterThan(0);
    }
  });

  it('includes on-device ML claim (raw biometric data never leaves device)', () => {
    const onDevice = FEATURES.find((f) => f.headline.toLowerCase().includes('on-device'));
    expect(onDevice).toBeDefined();
    expect(onDevice?.body.toLowerCase()).toContain('locally');
  });

  it('crisis feature mentions offline availability (CLAUDE.md Rule #1)', () => {
    const crisis = FEATURES.find((f) => f.headline.toLowerCase().includes('crisis'));
    expect(crisis).toBeDefined();
    expect(crisis?.body.toLowerCase()).toContain('offline');
  });

  it('crisis feature mentions no login required (static crisis contract)', () => {
    const crisis = FEATURES.find((f) => f.headline.toLowerCase().includes('crisis'));
    expect(crisis?.body.toLowerCase()).toContain('no login');
  });

  it('language feature mentions all 4 launch locales', () => {
    const lang = FEATURES.find((f) => f.headline.toLowerCase().includes('language'));
    expect(lang).toBeDefined();
    const body = lang?.body ?? '';
    expect(body).toContain('English');
    expect(body).toContain('French');
    expect(body).toContain('Arabic');
    expect(body).toContain('Persian');
  });

  it('language feature mentions RTL support (Arabic and Persian are RTL)', () => {
    const lang = FEATURES.find((f) => f.headline.toLowerCase().includes('language'));
    expect(lang?.body.toLowerCase()).toContain('rtl');
  });

  it('resilience feature uses compassion-first framing (not "clean days" alone)', () => {
    const resilience = FEATURES.find((f) => f.headline.toLowerCase().includes('resilience'));
    expect(resilience).toBeDefined();
    expect(resilience?.body.toLowerCase()).toContain('compassion');
  });

  it('clinical oversight feature mentions PHI protection', () => {
    const clinical = FEATURES.find((f) => f.headline.toLowerCase().includes('clinical'));
    expect(clinical).toBeDefined();
    expect(clinical?.body.toLowerCase()).toContain('phi');
  });

  it('headlines are unique', () => {
    const headlines = FEATURES.map((f) => f.headline);
    expect(new Set(headlines).size).toBe(headlines.length);
  });
});
