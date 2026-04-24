/**
 * Assessment store — Zustand + MMKV persist.
 *
 * Tracks the in-progress assessment session (instrument, responses) and
 * a lightweight history of last scores per instrument so the AssessmentListScreen
 * can display "last score" without hitting the server.
 *
 * Design constraints:
 * - This store never calls LLM or any network service — scoring is deterministic
 *   (CLAUDE.md §"Non-negotiable rules" + 12_Psychometric_System.md §5.1).
 * - PHQ-9 item 9 safety check is performed in the scoring logic here; the UI is
 *   responsible for presenting the compassionate safety message and navigating to
 *   Crisis when the flag is set (CLAUDE.md rule 1 — T3/T4 flows are deterministic).
 * - Scores are rendered in Latin digits everywhere (CLAUDE.md rule 9).
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

// ---------------------------------------------------------------------------
// Instrument definitions
// ---------------------------------------------------------------------------

export type InstrumentId = 'phq9' | 'gad7' | 'who5';

export interface ResponseOption {
  label: string;
  value: number;
}

export interface InstrumentItem {
  /** 0-based index within the instrument */
  index: number;
  text: string;
}

export interface InstrumentDefinition {
  id: InstrumentId;
  name: string;
  fullName: string;
  itemCount: number;
  estimatedMinutes: number;
  /** Preamble shown above the first question, or null for none. */
  preamble: string | null;
  items: InstrumentItem[];
  responseOptions: ResponseOption[];
  /** Maximum possible score */
  maxScore: number;
  /** Citation for verbatim item wording */
  citation: string;
}

/**
 * PHQ-9 — Kroenke, Spitzer & Williams 2001.
 * Item wording is verbatim; do not paraphrase (CLAUDE.md "Don't paraphrase
 * a validated psychometric instrument").
 */
export const PHQ9: InstrumentDefinition = {
  id: 'phq9',
  name: 'PHQ-9',
  fullName: 'Patient Health Questionnaire — 9',
  itemCount: 9,
  estimatedMinutes: 3,
  preamble:
    'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
  citation: 'Kroenke, Spitzer & Williams (2001). The PHQ-9. J Gen Intern Med.',
  maxScore: 27,
  items: [
    { index: 0, text: 'Little interest or pleasure in doing things' },
    { index: 1, text: 'Feeling down, depressed, or hopeless' },
    {
      index: 2,
      text: 'Trouble falling or staying asleep, or sleeping too much',
    },
    { index: 3, text: 'Feeling tired or having little energy' },
    { index: 4, text: 'Poor appetite or overeating' },
    {
      index: 5,
      text: 'Feeling bad about yourself — or that you are a failure or have let yourself or your family down',
    },
    {
      index: 6,
      text: 'Trouble concentrating on things, such as reading the newspaper or watching television',
    },
    {
      index: 7,
      text: 'Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual',
    },
    {
      index: 8,
      text: 'Thoughts that you would be better off dead or of hurting yourself in some way',
    },
  ],
  responseOptions: [
    { label: 'Not at all', value: 0 },
    { label: 'Several days', value: 1 },
    { label: 'More than half the days', value: 2 },
    { label: 'Nearly every day', value: 3 },
  ],
};

/**
 * GAD-7 — Spitzer et al. 2006.
 * Item wording is verbatim.
 */
export const GAD7: InstrumentDefinition = {
  id: 'gad7',
  name: 'GAD-7',
  fullName: 'Generalized Anxiety Disorder — 7',
  itemCount: 7,
  estimatedMinutes: 2,
  preamble:
    'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
  citation: 'Spitzer et al. (2006). A Brief Measure for Assessing Generalized Anxiety Disorder. Arch Intern Med.',
  maxScore: 21,
  items: [
    { index: 0, text: 'Feeling nervous, anxious, or on edge' },
    { index: 1, text: 'Not being able to stop or control worrying' },
    { index: 2, text: 'Worrying too much about different things' },
    { index: 3, text: 'Trouble relaxing' },
    { index: 4, text: "Being so restless that it's hard to sit still" },
    { index: 5, text: 'Becoming easily annoyed or irritable' },
    {
      index: 6,
      text: 'Feeling afraid as if something awful might happen',
    },
  ],
  responseOptions: [
    { label: 'Not at all', value: 0 },
    { label: 'Several days', value: 1 },
    { label: 'More than half the days', value: 2 },
    { label: 'Nearly every day', value: 3 },
  ],
};

/**
 * WHO-5 — World Health Organization Well-Being Index.
 * Item wording is verbatim. Raw score ×4 = 0–100 percentage.
 */
export const WHO5: InstrumentDefinition = {
  id: 'who5',
  name: 'WHO-5',
  fullName: 'WHO-5 Well-Being Index',
  itemCount: 5,
  estimatedMinutes: 2,
  preamble: null,
  citation: 'World Health Organization (1998). WHO-5 Well-Being Index.',
  maxScore: 25, // raw; displayed as raw ×4 (0–100)
  items: [
    { index: 0, text: 'I have felt cheerful and in good spirits' },
    { index: 1, text: 'I have felt calm and relaxed' },
    { index: 2, text: 'I have felt active and vigorous' },
    { index: 3, text: 'I woke up feeling fresh and rested' },
    { index: 4, text: 'My daily life has been filled with things that interest me' },
  ],
  responseOptions: [
    { label: 'At no time', value: 0 },
    { label: 'Some of the time', value: 1 },
    { label: 'Less than half of the time', value: 2 },
    { label: 'More than half of the time', value: 3 },
    { label: 'Most of the time', value: 4 },
    { label: 'All of the time', value: 5 },
  ],
};

export const INSTRUMENTS: Record<InstrumentId, InstrumentDefinition> = {
  phq9: PHQ9,
  gad7: GAD7,
  who5: WHO5,
};

// ---------------------------------------------------------------------------
// Scoring helpers
// ---------------------------------------------------------------------------

export interface ScoringResult {
  raw: number;
  /** Displayed value — WHO-5 shows raw ×4; others show raw. */
  displayScore: number;
  /** Latin-digit string, always 'en' locale (CLAUDE.md rule 9). */
  displayScoreString: string;
  severityLabel: string;
  compassionMessage: string;
  /** PHQ-9 only — true when item 9 (index 8) response ≥ 1. */
  safetyFlag: boolean;
}

function phq9Severity(score: number): { label: string; message: string } {
  // Bands: Kroenke 2001 pinned in 12_Psychometric_System.md §3.1
  if (score <= 4)
    return {
      label: 'Minimal or none',
      message:
        'Your score today is in the minimal range. Keep taking care of yourself.',
    };
  if (score <= 9)
    return {
      label: 'Mild',
      message:
        'A score of ' +
        score.toLocaleString('en') +
        ' is in the mild range on PHQ-9. One score isn’t a diagnosis. If this feels right, talking to a clinician can help.',
    };
  if (score <= 14)
    return {
      label: 'Moderate',
      message:
        'A score of ' +
        score.toLocaleString('en') +
        ' is in the moderate range. Consider speaking with a mental health professional — support is available.',
    };
  if (score <= 19)
    return {
      label: 'Moderately severe',
      message:
        'A score of ' +
        score.toLocaleString('en') +
        ' is in the moderately severe range. Reaching out to a clinician or counsellor is a meaningful step.',
    };
  return {
    label: 'Severe',
    message:
      'A score of ' +
      score.toLocaleString('en') +
      ' is in the severe range. Please reach out to a mental health professional or your crisis support today.',
  };
}

function gad7Severity(score: number): { label: string; message: string } {
  // Bands: Spitzer 2006
  if (score <= 4)
    return {
      label: 'Minimal',
      message: 'Your anxiety score today is in the minimal range. Well done for checking in.',
    };
  if (score <= 9)
    return {
      label: 'Mild',
      message:
        'A score of ' +
        score.toLocaleString('en') +
        ' is in the mild range on GAD-7. Gentle practices like deep breathing or mindfulness can help.',
    };
  if (score <= 14)
    return {
      label: 'Moderate',
      message:
        'A score of ' +
        score.toLocaleString('en') +
        ' is in the moderate range. Speaking with a professional can provide relief.',
    };
  return {
    label: 'Severe',
    message:
      'A score of ' +
      score.toLocaleString('en') +
      ' is in the severe range. Support from a clinician can make a real difference.',
  };
}

function who5Wellbeing(rawScore: number): { label: string; message: string } {
  const percent = rawScore * 4; // 0–100
  if (percent >= 72)
    return {
      label: 'Good well-being',
      message: 'Your well-being score today is in a positive range. Keep nurturing what’s working.',
    };
  if (percent >= 52)
    return {
      label: 'Moderate well-being',
      message:
        'Your well-being score of ' +
        percent.toLocaleString('en') +
        ' is in a moderate range. Small acts of self-care can add up.',
    };
  // WHO-5 < 52 is indicative of low mood; < 28 major depression screen
  return {
    label: 'Low well-being',
    message:
      'Your well-being score of ' +
      percent.toLocaleString('en') +
      ' suggests you may be going through a difficult time. Talking to someone you trust or a professional can help.',
  };
}

export function scoreInstrument(
  instrumentId: InstrumentId,
  responses: Record<number, number>,
): ScoringResult {
  const instrument = INSTRUMENTS[instrumentId];
  const raw = Object.values(responses).reduce((sum, v) => sum + v, 0);

  let displayScore: number;
  let severityLabel: string;
  let compassionMessage: string;
  let safetyFlag = false;

  if (instrumentId === 'phq9') {
    displayScore = raw;
    const sev = phq9Severity(raw);
    severityLabel = sev.label;
    compassionMessage = sev.message;
    // Item 9 is index 8 (0-based); any response > 0 triggers safety pathway
    safetyFlag = (responses[8] ?? 0) > 0;
  } else if (instrumentId === 'gad7') {
    displayScore = raw;
    const sev = gad7Severity(raw);
    severityLabel = sev.label;
    compassionMessage = sev.message;
  } else {
    // WHO-5: display as percentage (raw ×4)
    displayScore = raw * 4;
    const wb = who5Wellbeing(raw);
    severityLabel = wb.label;
    compassionMessage = wb.message;
  }

  // Latin digits — toLocaleString('en') enforces this on all platforms
  const displayScoreString = displayScore.toLocaleString('en');

  // Suppress TypeScript unused-var on instrument ref (used for validation)
  void instrument;

  return {
    raw,
    displayScore,
    displayScoreString,
    severityLabel,
    compassionMessage,
    safetyFlag,
  };
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

const storage = new MMKV({ id: 'assessment' });

const mmkvStorage = {
  getItem: (name: string) => {
    const value = storage.getString(name);
    return value ?? null;
  },
  setItem: (name: string, value: string) => {
    storage.set(name, value);
  },
  removeItem: (name: string) => {
    storage.delete(name);
  },
};

export interface LastScore {
  instrumentId: InstrumentId;
  displayScore: number;
  displayScoreString: string;
  severityLabel: string;
  completedAt: string; // ISO date
}

export interface AssessmentState {
  /** The instrument currently being administered, or null when idle. */
  currentInstrumentId: InstrumentId | null;
  /**
   * Map from item index (0-based) to selected response value.
   * Keyed by number — JSON serialization stores as string keys; access both.
   */
  responses: Record<number, number>;
  /** Last scores per instrument — shown on the list screen. */
  lastScores: Partial<Record<InstrumentId, LastScore>>;

  // -- Actions --
  startInstrument: (id: InstrumentId) => void;
  setResponse: (itemIndex: number, value: number) => void;
  recordCompletion: (result: LastScore) => void;
  reset: () => void;
}

const initialState: Pick<
  AssessmentState,
  'currentInstrumentId' | 'responses' | 'lastScores'
> = {
  currentInstrumentId: null,
  responses: {},
  lastScores: {},
};

export const useAssessment = create<AssessmentState>()(
  persist(
    (set) => ({
      ...initialState,

      startInstrument: (id) =>
        set({ currentInstrumentId: id, responses: {} }),

      setResponse: (itemIndex, value) =>
        set((s) => ({
          responses: { ...s.responses, [itemIndex]: value },
        })),

      recordCompletion: (result) =>
        set((s) => ({
          lastScores: { ...s.lastScores, [result.instrumentId]: result },
          currentInstrumentId: null,
          responses: {},
        })),

      reset: () => set({ ...initialState }),
    }),
    {
      name: 'assessment-store',
      storage: createJSONStorage(() => mmkvStorage),
    },
  ),
);
