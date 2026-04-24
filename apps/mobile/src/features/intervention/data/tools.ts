/**
 * Coping tool catalog — fully offline.
 *
 * All content is hardcoded. No API call is ever needed to render any tool.
 * Every tool MUST have a deterministic offline fallback (CLAUDE.md rule 5).
 *
 * toolId values are stable identifiers; never rename once shipped as they are
 * stored in ToolUsage records in the intervention store.
 */

export type ToolCategory =
  | 'Breathing'
  | 'Grounding'
  | 'Body'
  | 'Mindfulness'
  | 'Behavioural';

export interface CopingTool {
  toolId: string;
  name: string;
  tagline: string;
  durationMinutes: number;
  category: ToolCategory;
  fullDescription: string;
  steps: string[];
  /** If true, ToolDetailScreen renders the animated breathing guide. */
  hasBreathingAnimation?: boolean;
}

export const TOOLS: CopingTool[] = [
  {
    toolId: 'box-breathing',
    name: 'Box Breathing',
    tagline: 'Slow your nervous system in 4 minutes.',
    durationMinutes: 4,
    category: 'Breathing',
    hasBreathingAnimation: true,
    fullDescription:
      'Box breathing (4-4-4-4) is used by Navy SEALs and clinical psychologists to ' +
      'rapidly reduce acute stress. Inhale, hold, exhale, and hold again — each for ' +
      '4 seconds. Four rounds take under 70 seconds and reliably lower cortisol.',
    steps: [
      'Inhale through your nose for 4 seconds.',
      'Hold your breath for 4 seconds.',
      'Exhale slowly through your mouth for 4 seconds.',
      'Hold empty for 4 seconds.',
      'Repeat 4–6 times.',
    ],
  },
  {
    toolId: '5-4-3-2-1-grounding',
    name: '5-4-3-2-1 Grounding',
    tagline: 'Anchor yourself to right now.',
    durationMinutes: 5,
    category: 'Grounding',
    fullDescription:
      'The 5-4-3-2-1 technique redirects attention from urge-driven thinking to ' +
      'present-moment sensory input. Clinical evidence shows grounding interrupts ' +
      'the craving loop by occupying the same attentional channels the urge uses.',
    steps: [
      'Name 5 things you can see.',
      'Name 4 things you can touch — and touch them.',
      'Name 3 things you can hear.',
      'Name 2 things you can smell.',
      'Name 1 thing you can taste.',
    ],
  },
  {
    toolId: 'progressive-muscle-relaxation',
    name: 'Progressive Muscle Relaxation',
    tagline: 'Release tension held in your body.',
    durationMinutes: 10,
    category: 'Body',
    fullDescription:
      'PMR works by systematically tensing and releasing muscle groups, activating ' +
      'the parasympathetic nervous system. Particularly effective when urges manifest ' +
      'as physical tension, restlessness, or agitation.',
    steps: [
      'Sit or lie comfortably. Close your eyes.',
      'Tense your feet tightly for 5 seconds, then release.',
      'Move up: calves, thighs, abdomen, hands, arms, shoulders, face.',
      'After each group: breathe out slowly as you release.',
      'End with three slow, full breaths.',
    ],
  },
  {
    toolId: 'cold-water-reset',
    name: 'Cold Water Reset',
    tagline: 'Interrupt the urge with a sensory jolt.',
    durationMinutes: 2,
    category: 'Body',
    fullDescription:
      'Cold water activates the mammalian dive reflex, rapidly slowing heart rate ' +
      'and shifting the nervous system into parasympathetic dominance. Even 30 ' +
      'seconds of cold water on the face or wrists can break an acute urge spiral.',
    steps: [
      'Go to the nearest sink or use a water bottle.',
      'Run cold water over your wrists and the inside of your forearms for 30 seconds.',
      'Alternatively, splash cold water on your face three times.',
      'Breathe normally. Notice the temperature. Stay with that sensation.',
      'Wait 60 seconds — the urge peak is usually already passing.',
    ],
  },
  {
    toolId: 'urge-surfing',
    name: 'Urge Surfing',
    tagline: 'Ride the wave instead of fighting it.',
    durationMinutes: 6,
    category: 'Mindfulness',
    fullDescription:
      'Urge surfing (Marlatt & Gordon, 1985) treats cravings as waves: they peak ' +
      'and pass within 15–20 minutes without any action. Instead of suppressing or ' +
      'obeying the urge, you observe it as a physical sensation without judgment.',
    steps: [
      'Sit comfortably. Do not try to stop the urge.',
      'Notice where you feel it in your body — chest, throat, stomach.',
      'Describe it to yourself: pulsing, heavy, tight, warm.',
      'Breathe into that area. Watch the sensation change.',
      'Stay with it. It will peak and begin to subside — usually within 5–10 minutes.',
    ],
  },
  {
    toolId: 'stop-technique',
    name: 'STOP Technique',
    tagline: 'A 3-minute mindful pause.',
    durationMinutes: 3,
    category: 'Mindfulness',
    fullDescription:
      'STOP is a brief mindfulness intervention from Mindfulness-Based Cognitive ' +
      'Therapy (MBCT). It inserts a structured pause between urge and action, ' +
      'creating enough distance to choose a response rather than react.',
    steps: [
      'S — Stop. Whatever you are doing, pause completely.',
      'T — Take a breath. One slow, deliberate inhale and exhale.',
      'O — Observe. Notice your thoughts, feelings, and body sensations without acting.',
      'P — Proceed. Choose your next action with intention.',
    ],
  },
  {
    toolId: 'compassion-meditation',
    name: 'Compassion Meditation',
    tagline: 'Meet yourself with kindness, not judgment.',
    durationMinutes: 8,
    category: 'Mindfulness',
    fullDescription:
      'Self-compassion (Neff, 2003) is a reliable predictor of recovery resilience. ' +
      'This practice applies loving-kindness (metta) to yourself specifically in ' +
      'moments of struggle — reducing shame spirals that often accelerate relapse.',
    steps: [
      'Sit quietly. Place one hand on your heart.',
      'Acknowledge: "This is a moment of difficulty. I am not alone in this."',
      'Say slowly: "May I be kind to myself. May I give myself what I need."',
      'If self-criticism arises, notice it without following it.',
      'Repeat the phrases for 5–8 minutes. There is no right way to feel.',
    ],
  },
  {
    toolId: 'delay-and-distract',
    name: 'Delay & Distract',
    tagline: 'Buy 15 minutes — urges rarely survive it.',
    durationMinutes: 5,
    category: 'Behavioural',
    fullDescription:
      'Delay and distract is a core relapse-prevention strategy (Marlatt & Donovan). ' +
      'Urges are time-limited: the average craving peaks at 10–20 minutes. ' +
      'Committing to a 15-minute delay — with an absorbing alternative activity — ' +
      'is enough for most urges to pass without acting.',
    steps: [
      'Tell yourself: "I will wait 15 minutes before deciding anything."',
      'Pick an absorbing activity: a walk, a call, a task that uses your hands.',
      'Set a timer if it helps. Start the activity immediately.',
      'When the timer ends, check in: has the urge changed?',
      'If needed, delay another 15 minutes. Each round adds distance.',
    ],
  },
];

/** Look up a single tool by its stable toolId. */
export function getToolById(toolId: string): CopingTool | undefined {
  return TOOLS.find((t) => t.toolId === toolId);
}
