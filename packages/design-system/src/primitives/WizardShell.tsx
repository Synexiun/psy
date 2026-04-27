'use client';
/**
 * WizardShell — Quiet Strength–tokenised multi-step wizard shell.
 *
 * Pure layout / navigation primitive — no form logic. Orchestrates step display,
 * a segmented progress bar, Back / Next / Skip / Submit buttons in the footer,
 * and an optional Save & Exit header action for save-and-resume workflows.
 *
 * Used for assessment instruments (PHQ-9, GAD-7, WHO-5, etc.) where the user
 * answers questions one at a time.
 *
 * Token mapping:
 *   Progress filled        : bg-accent-bronze
 *   Progress unfilled      : bg-surface-tertiary
 *   Footer border          : border-border-subtle
 *   Back button            : text-ink-secondary hover:text-ink-primary  (+ disabled state)
 *   Next / Submit button   : bg-accent-bronze text-surface-primary hover:opacity-90
 *   Skip button            : text-ink-tertiary hover:text-ink-secondary
 *   Save & Exit            : text-ink-tertiary hover:text-ink-primary
 *   Focus ring             : focus-visible:ring-2 focus-visible:ring-accent-bronze/30
 *
 * RTL: all inline-direction spacing uses logical CSS properties (ps-* / pe-*).
 * No physical pl-* / pr-* / ml-* / mr-* classes anywhere in this file.
 * Flex direction on the footer reverses automatically in RTL.
 * Progress bar segments fill in document order, which Tailwind flex handles
 * correctly — first N segments filled = start-to-end in both LTR and RTL.
 *
 * Controlled / Uncontrolled:
 *   Pass `currentStep` for controlled mode; omit it (use `defaultStep`) for
 *   uncontrolled. Pattern mirrors CheckboxGroup — a single `isControlled` flag
 *   decides whether internal state or the prop drives rendering.
 */
import * as React from 'react';

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface WizardStep {
  id: string;
  /** Step label for progress indicator / accessibility */
  label: string;
  /** Step body — slotted into the scrollable content region */
  content: React.ReactNode;
  /** When true, a Skip button is shown alongside Back / Next for this step */
  skippable?: boolean;
}

export interface WizardShellProps {
  steps: WizardStep[];
  /** Controlled: current step index (0-based) */
  currentStep?: number;
  /** Uncontrolled: initial step index (default: 0) */
  defaultStep?: number;
  onStepChange?: (step: number) => void;
  onSubmit?: () => void;
  /** Called when the user triggers Save & Exit (save-and-resume) */
  onSave?: () => void;
  /** Label for the Next button (default: "Next") */
  nextLabel?: string;
  /** Label for the Back button (default: "Back") */
  backLabel?: string;
  /** Label for the Skip button (default: "Skip") */
  skipLabel?: string;
  /** Label for the Submit button on the final step (default: "Submit") */
  submitLabel?: string;
  /** Label for the Save & Exit button (default: "Save & Exit") */
  saveLabel?: string;
  /** Show a Save & Exit button in the header (default: false) */
  showSave?: boolean;
  /** Additional classes on the outermost container */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WizardShell({
  steps,
  currentStep,
  defaultStep,
  onStepChange,
  onSubmit,
  onSave,
  nextLabel,
  backLabel,
  skipLabel,
  submitLabel,
  saveLabel,
  showSave = false,
  className = '',
}: WizardShellProps): React.ReactElement {
  // Dev-mode guard — empty steps array is almost certainly a bug.
  if (process.env.NODE_ENV !== 'production' && steps.length === 0) {
    console.warn('[WizardShell] No steps provided. The wizard will render empty.');
  }

  // -------------------------------------------------------------------------
  // Controlled / Uncontrolled step management
  // -------------------------------------------------------------------------

  const [internalStep, setInternalStep] = React.useState(defaultStep ?? 0);
  const isControlled = currentStep !== undefined;
  const activeStep = isControlled ? currentStep : internalStep;

  const goToStep = (next: number) => {
    if (!isControlled) {
      setInternalStep(next);
    }
    onStepChange?.(next);
  };

  // -------------------------------------------------------------------------
  // Derived state
  // -------------------------------------------------------------------------

  const totalSteps = steps.length;
  // stepNumber is 1-based for human-readable display and aria attributes.
  const stepNumber = activeStep + 1;
  const isFirst = activeStep === 0;
  const isLast = activeStep === totalSteps - 1;

  // Guard: clamp activeStep so we never index out of bounds.
  const safeActiveStep = totalSteps === 0 ? 0 : Math.min(Math.max(activeStep, 0), totalSteps - 1);
  const currentStepDef = totalSteps > 0 ? steps[safeActiveStep] : undefined;
  const isSkippable = currentStepDef?.skippable === true;

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleBack = () => {
    if (!isFirst) goToStep(activeStep - 1);
  };

  const handleNext = () => {
    if (!isLast) goToStep(activeStep + 1);
    else onSubmit?.();
  };

  const handleSkip = () => {
    if (!isLast) goToStep(activeStep + 1);
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div
      className={`flex flex-col bg-surface-primary ${className}`.trim()}
    >
      {/* Header ------------------------------------------------------------ */}
      <div className="flex items-center justify-between ps-4 pe-4 pt-4 sm:ps-6 sm:pe-6">
        <p className="text-sm text-ink-tertiary">
          {totalSteps > 0 ? `Step ${stepNumber} of ${totalSteps}` : ''}
        </p>
        {showSave && onSave !== undefined && (
          <button
            type="button"
            onClick={onSave}
            className="text-sm text-ink-tertiary transition-colors duration-fast ease-default hover:text-ink-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
          >
            {saveLabel ?? 'Save & Exit'}
          </button>
        )}
      </div>

      {/* Progress bar ------------------------------------------------------- */}
      <div
        role="progressbar"
        aria-label={totalSteps > 0 ? `Step ${stepNumber} of ${totalSteps}` : 'Wizard progress'}
        aria-valuenow={stepNumber}
        aria-valuemin={1}
        aria-valuemax={totalSteps}
        className="flex gap-1 ps-4 pe-4 py-2 sm:ps-6 sm:pe-6"
      >
        {steps.map((_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full ${i < stepNumber ? 'bg-accent-bronze' : 'bg-surface-tertiary'}`}
          />
        ))}
      </div>

      {/* Step content ------------------------------------------------------- */}
      <div className="flex-1 overflow-y-auto ps-4 pe-4 pb-4 sm:ps-6 sm:pe-6">
        {currentStepDef?.content}
      </div>

      {/* Footer ------------------------------------------------------------ */}
      <div className="flex items-center justify-between gap-3 border-t border-border-subtle ps-4 pe-4 pb-4 pt-4 sm:ps-6 sm:pe-6">
        {/* Back */}
        <button
          type="button"
          onClick={handleBack}
          disabled={isFirst}
          className="rounded-md ps-4 pe-4 py-2 text-sm font-medium text-ink-secondary transition-colors duration-fast ease-default hover:text-ink-primary disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
        >
          {backLabel ?? 'Back'}
        </button>

        {/* Skip + Next/Submit group */}
        <div className="flex gap-3">
          {isSkippable && (
            <button
              type="button"
              onClick={handleSkip}
              className="rounded-md ps-4 pe-4 py-2 text-sm font-medium text-ink-tertiary transition-colors duration-fast ease-default hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
            >
              {skipLabel ?? 'Skip'}
            </button>
          )}
          <button
            type="button"
            onClick={handleNext}
            className="rounded-md bg-accent-bronze ps-4 pe-4 py-2 text-sm font-medium text-surface-primary transition-opacity duration-fast ease-default hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
          >
            {isLast ? (submitLabel ?? 'Submit') : (nextLabel ?? 'Next')}
          </button>
        </div>
      </div>
    </div>
  );
}
