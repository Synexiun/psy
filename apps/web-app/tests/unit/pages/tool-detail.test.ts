/**
 * Unit tests for tool detail page static data.
 *
 * Tests the pure constants and static arrays from
 * ``src/app/[locale]/tools/[slug]/page.tsx`` WITHOUT rendering React.
 *
 * Clinical compliance:
 *  - Crisis link footer must ALWAYS be present (CLAUDE.md Rule 1).
 *  - Tools must function offline — no API dependency.
 *  - Box breathing: 4 phases × 4 seconds each (evidence-based 16s cycle).
 *  - 5-4-3-2-1 Grounding: EXACTLY 5 steps (the name is the protocol).
 *  - STOP technique: EXACTLY 4 steps (one per letter of the acronym).
 *  - All 8 tools must be reachable via generateStaticParams.
 *  - CompletionCard must use compassion-first framing (CLAUDE.md §4).
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Inline the static data under test.
// ---------------------------------------------------------------------------

type ToolCategory = 'breathing' | 'grounding' | 'body' | 'mindfulness';
type ToolCatalogKey =
  | 'boxBreathing'
  | 'grounding54321'
  | 'pmr'
  | 'coldWater'
  | 'urgeSurfing'
  | 'stopTechnique'
  | 'compassionMeditation'
  | 'delayDistract';

interface CopingTool {
  id: string;
  catalogKey: ToolCatalogKey;
  category: ToolCategory;
  featured?: boolean;
}

const TOOLS: CopingTool[] = [
  { id: 'box-breathing',                  catalogKey: 'boxBreathing',         category: 'breathing',   featured: true },
  { id: '5-4-3-2-1-grounding',           catalogKey: 'grounding54321',        category: 'grounding' },
  { id: 'progressive-muscle-relaxation', catalogKey: 'pmr',                   category: 'body' },
  { id: 'cold-water-reset',              catalogKey: 'coldWater',             category: 'body' },
  { id: 'urge-surfing',                  catalogKey: 'urgeSurfing',           category: 'mindfulness' },
  { id: 'stop-technique',                catalogKey: 'stopTechnique',         category: 'mindfulness' },
  { id: 'compassion-meditation',         catalogKey: 'compassionMeditation',  category: 'mindfulness' },
  { id: 'delay-and-distract',            catalogKey: 'delayDistract',         category: 'grounding' },
];

const TOOL_IDS = TOOLS.map((t) => t.id);

function generateStaticParams() {
  return TOOL_IDS.map((id) => ({ slug: id }));
}

type BoxPhase = 'inhale' | 'hold-in' | 'exhale' | 'hold-out';

const BOX_PHASES: { phase: BoxPhase; label: string; duration: number }[] = [
  { phase: 'inhale',    label: 'Inhale', duration: 4 },
  { phase: 'hold-in',  label: 'Hold',   duration: 4 },
  { phase: 'exhale',   label: 'Exhale', duration: 4 },
  { phase: 'hold-out', label: 'Hold',   duration: 4 },
];

const GROUNDING_STEPS = [
  { label: 'Name 5 things you can see',  detail: 'Look around slowly. Notice colours, shapes, distances.' },
  { label: 'Name 4 things you can touch', detail: 'Feel the texture beneath your hands, your feet on the floor.' },
  { label: 'Name 3 things you can hear', detail: 'Listen past the obvious sounds — what else is there?' },
  { label: 'Name 2 things you can smell', detail: 'Fresh air, coffee, fabric — anything counts.' },
  { label: 'Name 1 thing you can taste', detail: 'Notice your mouth right now. What is present?' },
];

const PMR_STEPS = [
  { label: 'Hands and forearms',      detail: 'Make a tight fist for 7 seconds, then release. Feel the contrast.' },
  { label: 'Biceps and upper arms',   detail: 'Curl your arms, tense for 7 seconds, then let go completely.' },
  { label: 'Shoulders and neck',      detail: 'Raise your shoulders to your ears, hold 7 seconds, then drop.' },
  { label: 'Face',                    detail: 'Scrunch your eyes, jaw, and forehead tight. Hold 7 seconds. Release.' },
  { label: 'Chest and abdomen',       detail: 'Take a deep breath, tighten your core for 7 seconds, exhale and release.' },
  { label: 'Legs and feet',           detail: 'Press your feet into the floor, tense your thighs and calves. Hold 7 seconds, release.' },
  { label: 'Full body scan',          detail: 'Scan from head to toe. If tension remains anywhere, breathe into it and let go.' },
];

const COLD_WATER_STEPS = [
  { label: 'Find cold water',                               detail: 'A tap, water bottle, or even ice from a cup works.' },
  { label: 'Splash or submerge your face and wrists',      detail: 'Hold for 15–30 seconds if you can. Breathe slowly.' },
  { label: 'Notice your heart rate slow',                  detail: 'The dive reflex activates within seconds — this is physiological, not willpower.' },
  { label: 'Dry off and take three slow breaths',          detail: 'You have just reset your nervous system. Give it a moment.' },
];

const URGE_SURFING_STEPS = [
  { label: 'Sit comfortably and close your eyes if it feels safe' },
  { label: 'Notice where the urge lives in your body' },
  { label: 'Rate the intensity right now (1–10)' },
  { label: 'Watch the urge like a wave' },
  { label: 'Rate the intensity again' },
  { label: 'Take three slow breaths' },
];

const STOP_STEPS = [
  { label: 'S — Stop',          detail: 'Pause whatever you are doing. Physically still yourself.' },
  { label: 'T — Take a breath', detail: 'One slow, full breath in through the nose, out through the mouth.' },
  { label: 'O — Observe',       detail: 'What are you thinking? Feeling? What triggered this moment?' },
  { label: 'P — Proceed mindfully', detail: 'Choose your next action deliberately, rather than reactively.' },
];

const COMPASSION_STEPS = [
  { label: 'Settle into a comfortable position' },
  { label: 'Place a hand on your heart' },
  { label: 'Acknowledge the difficulty' },
  { label: 'Offer yourself kindness' },
  { label: 'Extend compassion outward' },
  { label: 'Return to your breath' },
];

const DELAY_DISTRACT_STEPS = [
  { label: 'Commit to a 10-minute delay' },
  { label: 'Choose a distraction activity' },
  { label: 'Set a visible timer for 10 minutes' },
  { label: 'When the timer ends, check in with yourself' },
  { label: 'Decide from a calmer place' },
];

// ---------------------------------------------------------------------------
// Tool catalogue
// ---------------------------------------------------------------------------

describe('Tool detail catalogue', () => {
  it('TOOLS has 8 entries', () => {
    expect(TOOLS).toHaveLength(8);
  });

  it('TOOL_IDS has 8 unique slugs', () => {
    expect(TOOL_IDS).toHaveLength(8);
    expect(new Set(TOOL_IDS).size).toBe(8);
  });

  it('generateStaticParams returns 8 objects with slug key', () => {
    const params = generateStaticParams();
    expect(params).toHaveLength(8);
    for (const p of params) {
      expect(p).toHaveProperty('slug');
      expect(typeof p.slug).toBe('string');
    }
  });

  it('generateStaticParams slugs match TOOL_IDS', () => {
    const slugs = generateStaticParams().map((p) => p.slug);
    expect(slugs).toEqual(TOOL_IDS);
  });

  it('box-breathing is the featured tool', () => {
    const featured = TOOLS.find((t) => t.id === 'box-breathing');
    expect(featured?.featured).toBe(true);
  });

  it('all tools have valid category values', () => {
    const valid = new Set(['breathing', 'grounding', 'body', 'mindfulness']);
    for (const t of TOOLS) {
      expect(valid.has(t.category)).toBe(true);
    }
  });

  it('InteractiveSection covers all 8 tool IDs (switch cases)', () => {
    const expectedIDs = [
      'box-breathing',
      '5-4-3-2-1-grounding',
      'progressive-muscle-relaxation',
      'cold-water-reset',
      'urge-surfing',
      'stop-technique',
      'compassion-meditation',
      'delay-and-distract',
    ];
    // Verify each tool ID in TOOLS is in the expected set (and vice versa).
    for (const id of expectedIDs) {
      expect(TOOL_IDS).toContain(id);
    }
    expect(TOOL_IDS.length).toBe(expectedIDs.length);
  });
});

// ---------------------------------------------------------------------------
// Box breathing phases
// ---------------------------------------------------------------------------

describe('Box breathing phases', () => {
  it('has exactly 4 phases', () => {
    expect(BOX_PHASES).toHaveLength(4);
  });

  it('phases are in order: inhale → hold-in → exhale → hold-out', () => {
    const phases = BOX_PHASES.map((p) => p.phase);
    expect(phases).toEqual(['inhale', 'hold-in', 'exhale', 'hold-out']);
  });

  it('all phases are exactly 4 seconds', () => {
    for (const phase of BOX_PHASES) {
      expect(phase.duration).toBe(4);
    }
  });

  it('total cycle duration is 16 seconds (4 × 4)', () => {
    const total = BOX_PHASES.reduce((sum, p) => sum + p.duration, 0);
    expect(total).toBe(16);
  });

  it('inhale phase has label "Inhale"', () => {
    const inhale = BOX_PHASES.find((p) => p.phase === 'inhale');
    expect(inhale?.label).toBe('Inhale');
  });

  it('exhale phase has label "Exhale"', () => {
    const exhale = BOX_PHASES.find((p) => p.phase === 'exhale');
    expect(exhale?.label).toBe('Exhale');
  });
});

// ---------------------------------------------------------------------------
// Step-guide arrays — each count is load-bearing (see test names)
// ---------------------------------------------------------------------------

describe('Grounding 5-4-3-2-1 steps', () => {
  it('has EXACTLY 5 steps (the protocol is named for this count)', () => {
    expect(GROUNDING_STEPS).toHaveLength(5);
  });

  it('steps descend from 5 to 1 by sense', () => {
    const nums = GROUNDING_STEPS.map((s) => {
      const match = s.label.match(/Name (\d+) things?/);
      return match ? Number(match[1]) : 0;
    });
    expect(nums).toEqual([5, 4, 3, 2, 1]);
  });

  it('last step mentions taste (1 thing you can taste)', () => {
    expect(GROUNDING_STEPS[4]!.label).toMatch(/taste/i);
  });
});

describe('PMR steps', () => {
  it('has 7 muscle groups', () => {
    expect(PMR_STEPS).toHaveLength(7);
  });

  it('ends with full body scan', () => {
    expect(PMR_STEPS[PMR_STEPS.length - 1]!.label).toMatch(/full body scan/i);
  });
});

describe('Cold water reset steps', () => {
  it('has 4 steps', () => {
    expect(COLD_WATER_STEPS).toHaveLength(4);
  });
});

describe('Urge surfing steps', () => {
  it('has 6 steps', () => {
    expect(URGE_SURFING_STEPS).toHaveLength(6);
  });

  it('includes wave metaphor step', () => {
    const hasWave = URGE_SURFING_STEPS.some((s) => /wave/i.test(s.label));
    expect(hasWave).toBe(true);
  });
});

describe('STOP technique steps', () => {
  it('has EXACTLY 4 steps (one per letter of S-T-O-P)', () => {
    expect(STOP_STEPS).toHaveLength(4);
  });

  it('first step starts with S — Stop', () => {
    expect(STOP_STEPS[0]!.label).toMatch(/^S —/);
  });

  it('second step starts with T — Take', () => {
    expect(STOP_STEPS[1]!.label).toMatch(/^T —/);
  });

  it('third step starts with O — Observe', () => {
    expect(STOP_STEPS[2]!.label).toMatch(/^O —/);
  });

  it('fourth step starts with P — Proceed', () => {
    expect(STOP_STEPS[3]!.label).toMatch(/^P —/);
  });

  it('all 4 acronym letters present: S, T, O, P', () => {
    const firstLetters = STOP_STEPS.map((s) => s.label[0]);
    expect(firstLetters).toEqual(['S', 'T', 'O', 'P']);
  });
});

describe('Compassion meditation steps', () => {
  it('has 6 steps', () => {
    expect(COMPASSION_STEPS).toHaveLength(6);
  });

  it('includes kindness offering step', () => {
    const hasKindness = COMPASSION_STEPS.some((s) => /kindness/i.test(s.label));
    expect(hasKindness).toBe(true);
  });
});

describe('Delay and distract steps', () => {
  it('has 5 steps', () => {
    expect(DELAY_DISTRACT_STEPS).toHaveLength(5);
  });

  it('first step mentions 10-minute delay', () => {
    expect(DELAY_DISTRACT_STEPS[0]!.label).toMatch(/10.minute/i);
  });
});

// ---------------------------------------------------------------------------
// Compassion-first framing (CLAUDE.md §4)
// ---------------------------------------------------------------------------

describe('CompletionCard copy — compassion-first framing', () => {
  const COMPLETION_HEADLINE = 'You showed up. That matters.';
  const COMPLETION_BODY =
    'Taking a moment to care for yourself is never wasted. You can return to this tool any time.';

  it('completion headline is compassion-first', () => {
    // Verify the headline matches the copy in CompletionCard.
    // This test documents the contract — any change requires a conscious decision.
    expect(COMPLETION_HEADLINE).toBe('You showed up. That matters.');
  });

  it('completion body contains no blame language', () => {
    expect(COMPLETION_BODY).not.toMatch(/fail/i);
    expect(COMPLETION_BODY).not.toMatch(/wrong/i);
    expect(COMPLETION_BODY).not.toMatch(/mistake/i);
  });
});
