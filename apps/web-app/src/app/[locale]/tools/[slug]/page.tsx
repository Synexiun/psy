'use client';

import * as React from 'react';
import { use } from 'react';
import { useTranslations } from 'next-intl';
import { notFound } from 'next/navigation';
import { useState, useEffect, useCallback, useRef } from 'react';
import { Layout } from '@/components/Layout';
import { Card, Badge, Button } from '@disciplineos/design-system';
import type { ToolCategory, CopingTool } from '@/lib/tools-catalog';
import { TOOLS, TOOL_IDS } from '@/lib/tools-catalog';

function CategoryIcon({ category }: { category: ToolCategory }): React.ReactElement {
  switch (category) {
    case 'breathing':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
          <path d="M5 8h14M5 12h10M5 16h7"/>
        </svg>
      );
    case 'grounding':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
          <path d="M12 22V12M12 12C12 7 17 4 20 4c0 5-3 8-8 8z"/>
          <path d="M12 12C12 8 7 5 4 6c0 4 3 7 8 6z"/>
        </svg>
      );
    case 'body':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
          <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
        </svg>
      );
    case 'mindfulness':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
          <circle cx="12" cy="12" r="9"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
      );
    default: {
      const _exhaustive: never = category;
      void _exhaustive;
      return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="h-6 w-6" aria-hidden="true">
          <circle cx="12" cy="12" r="9"/>
        </svg>
      );
    }
  }
}

const CATEGORY_BADGE_TONE: Record<ToolCategory, 'neutral' | 'calm' | 'warning' | 'success'> = {
  breathing: 'calm',
  grounding: 'neutral',
  body: 'warning',
  mindfulness: 'success',
};

// ---------------------------------------------------------------------------
// generateStaticParams — all 8 tool slugs are statically known.
// ---------------------------------------------------------------------------

export function generateStaticParams() {
  return TOOL_IDS.map((id) => ({ slug: id }));
}

// ---------------------------------------------------------------------------
// Box Breathing — 4-phase animated timer
// Phase durations in seconds: Inhale 4 → Hold 4 → Exhale 4 → Hold 4
// ---------------------------------------------------------------------------

type BoxPhase = 'inhale' | 'hold-in' | 'exhale' | 'hold-out';

const BOX_PHASES: { phase: BoxPhase; label: string; duration: number }[] = [
  { phase: 'inhale', label: 'Inhale', duration: 4 },
  { phase: 'hold-in', label: 'Hold', duration: 4 },
  { phase: 'exhale', label: 'Exhale', duration: 4 },
  { phase: 'hold-out', label: 'Hold', duration: 4 },
];

const BOX_PHASE_COLOR: Record<BoxPhase, string> = {
  inhale: 'var(--color-signal-stable)',
  'hold-in': 'var(--color-accent-bronze)',
  exhale: 'var(--color-ink-quaternary)',
  'hold-out': 'var(--color-accent-bronze-soft)',
};

// ---------------------------------------------------------------------------
// Step-through guide — used by Grounding 5-4-3-2-1 and PMR
// ---------------------------------------------------------------------------

interface StepGuideProps {
  steps: { label: string; detail?: string }[];
  onComplete: () => void;
}

function StepGuide({ steps, onComplete }: StepGuideProps) {
  const [stepIdx, setStepIdx] = useState(0);
  const totalSteps = steps.length;
  const isLast = stepIdx === totalSteps - 1;
  const step = steps[stepIdx]!;

  const handleNext = () => {
    if (isLast) {
      onComplete();
    } else {
      setStepIdx((i) => i + 1);
    }
  };

  const handlePrev = () => {
    if (stepIdx > 0) setStepIdx((i) => i - 1);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Progress dots */}
      <div className="flex gap-2 items-center justify-center" aria-label={`Step ${String(stepIdx + 1)} of ${String(totalSteps)}`}>
        {steps.map((_, i) => (
          <div
            key={i}
            className={`rounded-full transition-all duration-200 ${
              i === stepIdx
                ? 'h-2.5 w-2.5 bg-accent-bronze'
                : i < stepIdx
                ? 'h-2 w-2 bg-signal-stable'
                : 'h-2 w-2 bg-surface-tertiary'
            }`}
          />
        ))}
      </div>

      {/* Step card */}
      <Card tone="calm" className="min-h-36 flex flex-col justify-center items-center text-center gap-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-signal-stable">
          Step {String(stepIdx + 1)} of {String(totalSteps)}
        </span>
        <p className="text-lg font-semibold text-ink-primary leading-snug">{step.label}</p>
        {step.detail && (
          <p className="text-sm text-ink-secondary leading-relaxed">{step.detail}</p>
        )}
      </Card>

      {/* Controls */}
      <div className="flex gap-3 justify-center">
        <Button
          variant="ghost"
          size="md"
          onClick={handlePrev}
          disabled={stepIdx === 0}
          aria-label="Previous step"
        >
          ← Back
        </Button>
        <Button
          variant={isLast ? 'calm' : 'primary'}
          size="md"
          onClick={handleNext}
          aria-label={isLast ? 'Mark as complete' : 'Next step'}
        >
          {isLast ? 'Mark as complete' : 'Next →'}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Numbered steps list — used by remaining tools
// ---------------------------------------------------------------------------

interface NumberedStepsProps {
  steps: { label: string; detail?: string }[];
  onComplete: () => void;
}

function NumberedSteps({ steps, onComplete }: NumberedStepsProps) {
  const [checked, setChecked] = useState<Set<number>>(new Set());

  const toggle = (i: number) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  return (
    <div className="flex flex-col gap-5">
      <ol className="flex flex-col gap-3" aria-label="Steps">
        {steps.map((step, i) => {
          const isChecked = checked.has(i);
          return (
            <li key={i}>
              <button
                type="button"
                onClick={() => toggle(i)}
                className={`w-full text-start rounded-xl border p-4 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 ${
                  isChecked
                    ? 'border-signal-stable/30 bg-signal-stable/10 opacity-70'
                    : 'border-border-subtle bg-surface-secondary hover:border-accent-bronze/30 hover:bg-accent-bronze/5'
                }`}
                aria-pressed={isChecked}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                      isChecked
                        ? 'bg-signal-stable text-white'
                        : 'bg-surface-tertiary text-ink-tertiary'
                    }`}
                    aria-hidden="true"
                  >
                    {isChecked ? (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" width="12" height="12" aria-hidden="true">
                        <path d="M2 6l3 3 5-5"/>
                      </svg>
                    ) : String(i + 1)}
                  </span>
                  <div>
                    <p className={`text-sm font-medium leading-snug ${isChecked ? 'line-through text-ink-quaternary' : 'text-ink-primary'}`}>
                      {step.label}
                    </p>
                    {step.detail && (
                      <p className="mt-0.5 text-xs leading-relaxed text-ink-tertiary">{step.detail}</p>
                    )}
                  </div>
                </div>
              </button>
            </li>
          );
        })}
      </ol>

      <Button
        variant="calm"
        size="lg"
        className="w-full"
        onClick={onComplete}
        aria-label="Mark this tool as complete"
      >
        Mark as complete
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Completion card — compassion-first framing (CLAUDE.md §4)
// ---------------------------------------------------------------------------

function CompletionCard({ locale }: { locale: string }) {
  return (
    <Card tone="calm" className="flex flex-col items-center text-center gap-4 py-10">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none" stroke="var(--color-signal-stable)" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" width="48" height="48" aria-hidden="true">
        <path d="M24 44V24M24 24C24 14 34 8 40 8c0 10-6 16-16 16z"/>
        <path d="M24 24C24 16 14 10 8 12c0 8 6 14 16 12z"/>
      </svg>
      <div>
        <p className="text-lg font-semibold text-ink-primary">You showed up. That matters.</p>
        <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
          Taking a moment to care for yourself is never wasted. You can return to this tool any time.
        </p>
      </div>
      <div className="flex flex-col gap-2 w-full max-w-xs">
        <a
          href={`/${locale}/tools`}
          className="inline-flex items-center justify-center rounded-lg border border-border-subtle bg-surface-secondary px-4 py-2.5 text-sm font-medium text-ink-secondary transition-colors hover:bg-surface-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
        >
          Browse other tools
        </a>
        <a
          href={`/${locale}/check-in`}
          className="inline-flex items-center justify-center rounded-lg bg-accent-bronze px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent-bronze-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30"
        >
          Record a check-in
        </a>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Per-tool step content (hardcoded English — not yet in catalog)
// ---------------------------------------------------------------------------

const GROUNDING_STEPS: StepGuideProps['steps'] = [
  { label: 'Name 5 things you can see', detail: 'Look around slowly. Notice colours, shapes, distances.' },
  { label: 'Name 4 things you can touch', detail: 'Feel the texture beneath your hands, your feet on the floor.' },
  { label: 'Name 3 things you can hear', detail: 'Listen past the obvious sounds — what else is there?' },
  { label: 'Name 2 things you can smell', detail: 'Fresh air, coffee, fabric — anything counts.' },
  { label: 'Name 1 thing you can taste', detail: 'Notice your mouth right now. What is present?' },
];

const PMR_STEPS: StepGuideProps['steps'] = [
  { label: 'Hands and forearms', detail: 'Make a tight fist for 7 seconds, then release. Feel the contrast.' },
  { label: 'Biceps and upper arms', detail: 'Curl your arms, tense for 7 seconds, then let go completely.' },
  { label: 'Shoulders and neck', detail: 'Raise your shoulders to your ears, hold 7 seconds, then drop.' },
  { label: 'Face', detail: 'Scrunch your eyes, jaw, and forehead tight. Hold 7 seconds. Release.' },
  { label: 'Chest and abdomen', detail: 'Take a deep breath, tighten your core for 7 seconds, exhale and release.' },
  { label: 'Legs and feet', detail: 'Press your feet into the floor, tense your thighs and calves. Hold 7 seconds, release.' },
  { label: 'Full body scan', detail: 'Scan from head to toe. If tension remains anywhere, breathe into it and let go.' },
];

const COLD_WATER_STEPS: { label: string; detail?: string }[] = [
  { label: 'Find cold water', detail: 'A tap, water bottle, or even ice from a cup works.' },
  { label: 'Splash or submerge your face and wrists', detail: 'Hold for 15–30 seconds if you can. Breathe slowly.' },
  { label: 'Notice your heart rate slow', detail: 'The dive reflex activates within seconds — this is physiological, not willpower.' },
  { label: 'Dry off and take three slow breaths', detail: 'You have just reset your nervous system. Give it a moment.' },
];

const URGE_SURFING_STEPS: { label: string; detail?: string }[] = [
  { label: 'Sit comfortably and close your eyes if it feels safe', detail: 'You do not need to fight the urge — just observe it.' },
  { label: 'Notice where the urge lives in your body', detail: 'Chest? Throat? Stomach? Locate it without judgment.' },
  { label: 'Rate the intensity right now (1–10)', detail: 'You will check again in two minutes.' },
  { label: 'Watch the urge like a wave', detail: 'It rose. It is peaking. It will fall. Waves always do.' },
  { label: 'Rate the intensity again', detail: 'Has it shifted? Most urges diminish within 3–5 minutes of observation.' },
  { label: 'Take three slow breaths', detail: 'You surfed the wave. That took real skill.' },
];

const STOP_STEPS: { label: string; detail?: string }[] = [
  { label: 'S — Stop', detail: 'Pause whatever you are doing. Physically still yourself.' },
  { label: 'T — Take a breath', detail: 'One slow, full breath in through the nose, out through the mouth.' },
  { label: 'O — Observe', detail: 'What are you thinking? Feeling? What triggered this moment?' },
  { label: 'P — Proceed mindfully', detail: 'Choose your next action deliberately, rather than reactively.' },
];

const COMPASSION_STEPS: { label: string; detail?: string }[] = [
  { label: 'Settle into a comfortable position', detail: 'Close your eyes or soften your gaze downward.' },
  { label: 'Place a hand on your heart', detail: 'Feel warmth and connection — a gesture of care toward yourself.' },
  { label: 'Acknowledge the difficulty', detail: 'Say silently: "This is a difficult moment. Difficulty is part of being human."' },
  { label: 'Offer yourself kindness', detail: 'Say: "May I be kind to myself. May I give myself what I need right now."' },
  { label: 'Extend compassion outward', detail: 'Think of others who share this struggle. You are not alone in this.' },
  { label: 'Return to your breath', detail: 'Take three slow breaths. Open your eyes when you are ready.' },
];

const DELAY_DISTRACT_STEPS: { label: string; detail?: string }[] = [
  { label: 'Commit to a 10-minute delay', detail: 'Tell yourself: I am not saying no forever — I am saying not for 10 minutes.' },
  { label: 'Choose a distraction activity', detail: 'Walk, drink water, text a friend, do 10 push-ups, make tea.' },
  { label: 'Set a visible timer for 10 minutes', detail: 'Use your phone clock or count slowly — the act of waiting is the work.' },
  { label: 'When the timer ends, check in with yourself', detail: 'Rate the urge again. Has it changed? Most urges pass or weaken here.' },
  { label: 'Decide from a calmer place', detail: 'You now have more information than you did 10 minutes ago. Trust it.' },
];

// ---------------------------------------------------------------------------
// Interactive section — routes by tool ID
// ---------------------------------------------------------------------------

function InteractiveSection({ tool, onComplete }: { tool: CopingTool; onComplete: () => void }) {
  switch (tool.id) {
    case 'box-breathing':
      return <BoxBreathingWithCompletion onComplete={onComplete} />;
    case '5-4-3-2-1-grounding':
      return <StepGuide steps={GROUNDING_STEPS} onComplete={onComplete} />;
    case 'progressive-muscle-relaxation':
      return <StepGuide steps={PMR_STEPS} onComplete={onComplete} />;
    case 'cold-water-reset':
      return <NumberedSteps steps={COLD_WATER_STEPS} onComplete={onComplete} />;
    case 'urge-surfing':
      return <NumberedSteps steps={URGE_SURFING_STEPS} onComplete={onComplete} />;
    case 'stop-technique':
      return <NumberedSteps steps={STOP_STEPS} onComplete={onComplete} />;
    case 'compassion-meditation':
      return <NumberedSteps steps={COMPASSION_STEPS} onComplete={onComplete} />;
    case 'delay-and-distract':
      return <NumberedSteps steps={DELAY_DISTRACT_STEPS} onComplete={onComplete} />;
    default:
      return null;
  }
}

// Box breathing completes when all TARGET_CYCLES are done
function BoxBreathingWithCompletion({ onComplete }: { onComplete: () => void }) {
  const [running, setRunning] = useState(false);
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState(BOX_PHASES[0]!.duration);
  const [cycles, setCycles] = useState(0);

  const TARGET_CYCLES = 4;
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const advance = useCallback(() => {
    setSecondsLeft((prev) => {
      if (prev > 1) return prev - 1;
      setPhaseIdx((pIdx) => {
        const nextIdx = (pIdx + 1) % BOX_PHASES.length;
        setSecondsLeft(BOX_PHASES[nextIdx]!.duration);
        if (nextIdx === 0) {
          setCycles((c) => {
            const newC = c + 1;
            if (newC >= TARGET_CYCLES) {
              setRunning(false);
              // Allow state flush before calling onComplete
              setTimeout(onComplete, 600);
            }
            return newC;
          });
        }
        return nextIdx;
      });
      return 0;
    });
  }, [onComplete]);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(advance, 1000);
    } else {
      clearTimer();
    }
    return clearTimer;
  }, [running, advance, clearTimer]);

  const restart = () => {
    clearTimer();
    setRunning(false);
    setPhaseIdx(0);
    setSecondsLeft(BOX_PHASES[0]!.duration);
    setCycles(0);
  };

  const currentPhase = BOX_PHASES[phaseIdx]!;
  const totalSeconds = currentPhase.duration;
  const progress = (totalSeconds - secondsLeft) / totalSeconds;
  const size = 200;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashoffset = circumference * (1 - progress);
  const phaseColor = BOX_PHASE_COLOR[currentPhase.phase];

  const hasStarted = running || cycles > 0;

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Circle animation */}
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
          aria-hidden="true"
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-surface-tertiary)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={phaseColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
            style={{ transition: 'stroke-dashoffset 0.9s linear, stroke 0.4s ease' }}
          />
        </svg>
        <div className="absolute flex flex-col items-center gap-0.5">
          <span
            className="text-5xl font-bold tabular-nums text-ink-primary leading-none"
            aria-live="polite"
            aria-atomic="true"
          >
            {String(secondsLeft)}
          </span>
          <span className="text-sm font-medium text-ink-tertiary mt-1">{currentPhase.label}</span>
        </div>
      </div>

      {/* Cycle counter */}
      <p className="text-sm text-ink-quaternary">
        Cycle{' '}
        <span className="font-semibold text-ink-secondary">
          {String(Math.min(cycles + 1, TARGET_CYCLES))}
        </span>{' '}
        of{' '}
        <span className="font-semibold text-ink-secondary">{String(TARGET_CYCLES)}</span>
      </p>

      {/* Phase strip */}
      <div className="flex gap-2" role="list" aria-label="Breathing phases">
        {BOX_PHASES.map((bp, i) => (
          <div
            key={bp.phase}
            role="listitem"
            className={`flex flex-col items-center gap-1 transition-opacity duration-200 ${
              i === phaseIdx ? 'opacity-100' : 'opacity-30'
            }`}
          >
            <div
              className="h-1.5 w-12 rounded-full"
              style={{
                backgroundColor:
                  i === phaseIdx ? phaseColor : 'var(--color-surface-tertiary)',
              }}
            />
            <span className="text-xs text-ink-tertiary">{bp.label}</span>
            <span className="text-xs text-ink-quaternary tabular-nums">{String(bp.duration)}s</span>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="flex gap-3">
        <Button
          variant="calm"
          size="lg"
          onClick={() => setRunning((r) => !r)}
          aria-label={running ? 'Pause breathing exercise' : 'Start breathing exercise'}
        >
          {running ? 'Pause' : !hasStarted ? 'Start' : 'Resume'}
        </Button>
        {hasStarted && (
          <Button variant="ghost" size="lg" onClick={restart}>
            Restart
          </Button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Detail page inner component
// ---------------------------------------------------------------------------

function ToolDetailInner({ locale, slug }: { locale: string; slug: string }) {
  const t = useTranslations();
  const [completed, setCompleted] = useState(false);

  const tool = TOOLS.find((tc) => tc.id === slug);
  if (!tool) notFound();

  const badgeTone = CATEGORY_BADGE_TONE[tool.category];

  return (
    <Layout locale={locale}>
      <div className="space-y-6 max-w-2xl mx-auto">
        {/* Back link */}
        <nav aria-label="Breadcrumb">
          <a
            href={`/${locale}/tools`}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-accent-bronze transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
          >
            <span aria-hidden="true">←</span>
            {t('nav.tools')}
          </a>
        </nav>

        {/* Tool header */}
        <header className="flex items-start gap-4">
          <span className="text-4xl leading-none mt-0.5 shrink-0">
            <CategoryIcon category={tool.category} />
          </span>
          <div className="min-w-0 space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-semibold tracking-tight text-ink-primary leading-tight">
                {t(`tools.items.${tool.catalogKey}.name`)}
              </h1>
              <Badge tone={badgeTone}>
                {t(`tools.categories.${tool.category}`)}
              </Badge>
            </div>
            <p className="text-sm text-ink-tertiary">
              <span className="tabular-nums">{t(`tools.items.${tool.catalogKey}.duration`)}</span>{' '}
              {t('tools.minutesSuffix')} &middot; {t(`tools.categories.${tool.category}`)}
            </p>
          </div>
        </header>

        {/* Description */}
        <p className="text-sm leading-relaxed text-ink-secondary">
          {t(`tools.items.${tool.catalogKey}.description`)}
        </p>

        {/* Divider */}
        <div className="border-t border-border-subtle" aria-hidden="true" />

        {/* Interactive guide or completion card */}
        {completed ? (
          <CompletionCard locale={locale} />
        ) : (
          <section aria-labelledby="guide-heading">
            <h2
              id="guide-heading"
              className="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
            >
              {tool.id === 'box-breathing' ? 'Breathing exercise' : 'Guided steps'}
            </h2>
            <InteractiveSection tool={tool} onComplete={() => setCompleted(true)} />
          </section>
        )}

        {/* Crisis link — always visible per CLAUDE.md */}
        <footer className="pt-2 text-center">
          <a
            href={`/${locale}/crisis`}
            className="text-xs text-ink-quaternary hover:text-signal-crisis transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-crisis/30 rounded"
          >
            Need immediate help? Get support →
          </a>
        </footer>
      </div>
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export (Next.js 15: params is a Promise)
// ---------------------------------------------------------------------------

export default function ToolDetailPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): React.JSX.Element {
  const { locale, slug } = use(params);
  return <ToolDetailInner locale={locale} slug={slug} />;
}
