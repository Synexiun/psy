/**
 * Contract tests for packages/design-system/src/primitives/WizardShell.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * WizardShell is a pure layout/navigation primitive — no form logic.
 * It orchestrates step display, a segmented progress bar, Back/Next/Skip/Submit
 * buttons, and an optional Save & Exit header action.
 *
 * axe rules disabled:
 *   color-contrast — requires computed styles not available in jsdom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { configureAxe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { WizardShell } from '@disciplineos/design-system/primitives/WizardShell';
import type { WizardStep } from '@disciplineos/design-system/primitives/WizardShell';

expect.extend(toHaveNoViolations);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STEPS_3: WizardStep[] = [
  { id: 'step-1', label: 'Mood', content: <p>Step 1 content</p> },
  { id: 'step-2', label: 'Energy', content: <p>Step 2 content</p> },
  { id: 'step-3', label: 'Sleep', content: <p>Step 3 content</p> },
];

const STEPS_4: WizardStep[] = [
  { id: 'q1', label: 'Q1', content: <p>Question 1</p> },
  { id: 'q2', label: 'Q2', content: <p>Question 2</p> },
  { id: 'q3', label: 'Q3', content: <p>Question 3</p> },
  { id: 'q4', label: 'Q4', content: <p>Question 4</p> },
];

function renderWizard(props: Partial<React.ComponentProps<typeof WizardShell>> = {}) {
  return render(<WizardShell steps={STEPS_3} {...props} />);
}

// ---------------------------------------------------------------------------
// 1. Renders step content for current step
// ---------------------------------------------------------------------------

describe('WizardShell — step content rendering', () => {
  it('renders content for the first step by default', () => {
    renderWizard();
    expect(screen.getByText('Step 1 content')).toBeInTheDocument();
  });

  it('does not render content for inactive steps', () => {
    renderWizard();
    expect(screen.queryByText('Step 2 content')).toBeNull();
    expect(screen.queryByText('Step 3 content')).toBeNull();
  });

  it('renders content for the second step when defaultStep=1', () => {
    renderWizard({ defaultStep: 1 });
    expect(screen.getByText('Step 2 content')).toBeInTheDocument();
    expect(screen.queryByText('Step 1 content')).toBeNull();
  });

  it('renders content for the last step when defaultStep is last index', () => {
    renderWizard({ defaultStep: 2 });
    expect(screen.getByText('Step 3 content')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. "Step N of M" text in header
// ---------------------------------------------------------------------------

describe('WizardShell — header step counter', () => {
  it('shows "Step 1 of 3" on first step', () => {
    renderWizard();
    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument();
  });

  it('shows "Step 2 of 3" when defaultStep=1', () => {
    renderWizard({ defaultStep: 1 });
    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument();
  });

  it('shows "Step 3 of 3" on last step', () => {
    renderWizard({ defaultStep: 2 });
    expect(screen.getByText('Step 3 of 3')).toBeInTheDocument();
  });

  it('updates counter after navigating to next step', () => {
    renderWizard();
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument();
  });

  it('shows correct "N of M" for 4-step wizard', () => {
    render(<WizardShell steps={STEPS_4} defaultStep={2} />);
    expect(screen.getByText('Step 3 of 4')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 3. Progress bar
// ---------------------------------------------------------------------------

describe('WizardShell — progress bar', () => {
  it('renders the correct number of segments (3 for 3-step wizard)', () => {
    const { container } = renderWizard();
    const progressBar = container.querySelector('[role="progressbar"]');
    const segments = progressBar?.querySelectorAll('div') ?? [];
    expect(segments.length).toBe(3);
  });

  it('aria-valuenow matches step number (1-based) on first step', () => {
    const { container } = renderWizard();
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar?.getAttribute('aria-valuenow')).toBe('1');
  });

  it('aria-valuenow matches step number on second step (defaultStep=1)', () => {
    const { container } = renderWizard({ defaultStep: 1 });
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar?.getAttribute('aria-valuenow')).toBe('2');
  });

  it('aria-valuemin is 1', () => {
    const { container } = renderWizard();
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar?.getAttribute('aria-valuemin')).toBe('1');
  });

  it('aria-valuemax equals total steps', () => {
    const { container } = renderWizard();
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar?.getAttribute('aria-valuemax')).toBe('3');
  });

  it('first segment has bg-accent-bronze on step 1', () => {
    const { container } = renderWizard();
    const progressBar = container.querySelector('[role="progressbar"]');
    const segments = progressBar?.querySelectorAll('div') ?? [];
    const firstSegment = segments[0];
    expect(firstSegment?.className).toContain('bg-accent-bronze');
  });

  it('second and third segments are unfilled on step 1', () => {
    const { container } = renderWizard();
    const progressBar = container.querySelector('[role="progressbar"]');
    const segments = progressBar?.querySelectorAll('div') ?? [];
    expect(segments[1]?.className).not.toContain('bg-accent-bronze');
    expect(segments[2]?.className).not.toContain('bg-accent-bronze');
  });

  it('two segments filled on step 2 (defaultStep=1)', () => {
    const { container } = renderWizard({ defaultStep: 1 });
    const progressBar = container.querySelector('[role="progressbar"]');
    const segments = progressBar?.querySelectorAll('div') ?? [];
    expect(segments[0]?.className).toContain('bg-accent-bronze');
    expect(segments[1]?.className).toContain('bg-accent-bronze');
    expect(segments[2]?.className).not.toContain('bg-accent-bronze');
  });

  it('all segments filled on last step', () => {
    const { container } = renderWizard({ defaultStep: 2 });
    const progressBar = container.querySelector('[role="progressbar"]');
    const segments = progressBar?.querySelectorAll('div') ?? [];
    for (const seg of segments) {
      expect(seg.className).toContain('bg-accent-bronze');
    }
  });
});

// ---------------------------------------------------------------------------
// 4. Back button
// ---------------------------------------------------------------------------

describe('WizardShell — Back button', () => {
  it('Back button is disabled on the first step', () => {
    renderWizard();
    const back = screen.getByRole('button', { name: /back/i });
    expect(back).toBeDisabled();
  });

  it('Back button is enabled when not on the first step', () => {
    renderWizard({ defaultStep: 1 });
    const back = screen.getByRole('button', { name: /back/i });
    expect(back).not.toBeDisabled();
  });

  it('Back button is enabled on the last step', () => {
    renderWizard({ defaultStep: 2 });
    const back = screen.getByRole('button', { name: /back/i });
    expect(back).not.toBeDisabled();
  });

  it('clicking Back calls onStepChange with step-1', () => {
    const handler = vi.fn();
    renderWizard({ defaultStep: 1, onStepChange: handler });
    fireEvent.click(screen.getByRole('button', { name: /back/i }));
    expect(handler).toHaveBeenCalledWith(0);
  });

  it('clicking Back navigates to previous step in uncontrolled mode', () => {
    renderWizard({ defaultStep: 2 });
    fireEvent.click(screen.getByRole('button', { name: /back/i }));
    expect(screen.getByText('Step 2 content')).toBeInTheDocument();
  });

  it('uses custom backLabel when provided', () => {
    renderWizard({ backLabel: 'Previous' });
    expect(screen.getByRole('button', { name: 'Previous' })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 5. Next button — calls onStepChange with step+1; shows Submit label on last step
// ---------------------------------------------------------------------------

describe('WizardShell — Next button', () => {
  it('Next button calls onStepChange with step+1', () => {
    const handler = vi.fn();
    renderWizard({ onStepChange: handler });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(handler).toHaveBeenCalledWith(1);
  });

  it('Next button navigates to next step in uncontrolled mode', () => {
    renderWizard();
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Step 2 content')).toBeInTheDocument();
  });

  it('shows "Submit" label on the last step instead of "Next"', () => {
    renderWizard({ defaultStep: 2 });
    expect(screen.queryByRole('button', { name: /^next$/i })).toBeNull();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('shows "Next" label on non-final steps', () => {
    renderWizard({ defaultStep: 0 });
    expect(screen.getByRole('button', { name: /^next$/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^submit$/i })).toBeNull();
  });

  it('uses custom nextLabel when provided', () => {
    renderWizard({ nextLabel: 'Continue' });
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
  });

  it('uses custom submitLabel when provided on last step', () => {
    renderWizard({ defaultStep: 2, submitLabel: 'Finish' });
    expect(screen.getByRole('button', { name: 'Finish' })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 6. Submit button calls onSubmit
// ---------------------------------------------------------------------------

describe('WizardShell — Submit button', () => {
  it('Submit button calls onSubmit when clicked on last step', () => {
    const handler = vi.fn();
    renderWizard({ defaultStep: 2, onSubmit: handler });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(handler).toHaveBeenCalledOnce();
  });

  it('Submit button does not call onStepChange when on last step', () => {
    const stepHandler = vi.fn();
    const submitHandler = vi.fn();
    renderWizard({ defaultStep: 2, onStepChange: stepHandler, onSubmit: submitHandler });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(stepHandler).not.toHaveBeenCalled();
    expect(submitHandler).toHaveBeenCalledOnce();
  });

  it('does not render Submit on non-final steps', () => {
    renderWizard({ defaultStep: 0 });
    expect(screen.queryByRole('button', { name: /^submit$/i })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 7. Skip button
// ---------------------------------------------------------------------------

describe('WizardShell — Skip button', () => {
  it('Skip button is shown when current step has skippable=true', () => {
    const steps: WizardStep[] = [
      { id: 's1', label: 'S1', content: <p>Step 1</p>, skippable: true },
      { id: 's2', label: 'S2', content: <p>Step 2</p> },
    ];
    render(<WizardShell steps={steps} />);
    expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
  });

  it('Skip button is hidden when current step has skippable=false (default)', () => {
    renderWizard();
    expect(screen.queryByRole('button', { name: /skip/i })).toBeNull();
  });

  it('Skip button is hidden when current step has skippable undefined', () => {
    render(<WizardShell steps={STEPS_3} defaultStep={1} />);
    expect(screen.queryByRole('button', { name: /skip/i })).toBeNull();
  });

  it('Skip button calls onStepChange with step+1', () => {
    const handler = vi.fn();
    const steps: WizardStep[] = [
      { id: 's1', label: 'S1', content: <p>Step 1</p>, skippable: true },
      { id: 's2', label: 'S2', content: <p>Step 2</p> },
    ];
    render(<WizardShell steps={steps} onStepChange={handler} />);
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(handler).toHaveBeenCalledWith(1);
  });

  it('Skip button navigates to next step in uncontrolled mode', () => {
    const steps: WizardStep[] = [
      { id: 's1', label: 'S1', content: <p>Step 1</p>, skippable: true },
      { id: 's2', label: 'S2', content: <p>Step 2</p> },
    ];
    render(<WizardShell steps={steps} />);
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(screen.getByText('Step 2')).toBeInTheDocument();
  });

  it('uses custom skipLabel when provided', () => {
    const steps: WizardStep[] = [
      { id: 's1', label: 'S1', content: <p>S1</p>, skippable: true },
      { id: 's2', label: 'S2', content: <p>S2</p> },
    ];
    render(<WizardShell steps={steps} skipLabel="Pass" />);
    expect(screen.getByRole('button', { name: 'Pass' })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 8. Save & Exit button
// ---------------------------------------------------------------------------

describe('WizardShell — Save & Exit button', () => {
  it('is shown when showSave=true AND onSave is provided', () => {
    renderWizard({ showSave: true, onSave: vi.fn() });
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('is hidden when showSave=false (default)', () => {
    renderWizard({ onSave: vi.fn() });
    expect(screen.queryByRole('button', { name: /save/i })).toBeNull();
  });

  it('is hidden when showSave=true but onSave is not provided', () => {
    renderWizard({ showSave: true });
    expect(screen.queryByRole('button', { name: /save/i })).toBeNull();
  });

  it('calls onSave when Save & Exit is clicked', () => {
    const handler = vi.fn();
    renderWizard({ showSave: true, onSave: handler });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    expect(handler).toHaveBeenCalledOnce();
  });

  it('uses default "Save & Exit" label', () => {
    renderWizard({ showSave: true, onSave: vi.fn() });
    expect(screen.getByText('Save & Exit')).toBeInTheDocument();
  });

  it('uses custom saveLabel when provided', () => {
    renderWizard({ showSave: true, onSave: vi.fn(), saveLabel: 'Save progress' });
    expect(screen.getByText('Save progress')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 9. Controlled mode
// ---------------------------------------------------------------------------

describe('WizardShell — controlled mode', () => {
  it('currentStep prop overrides internal state', () => {
    renderWizard({ currentStep: 2 });
    expect(screen.getByText('Step 3 content')).toBeInTheDocument();
    expect(screen.queryByText('Step 1 content')).toBeNull();
  });

  it('shows correct "Step N of M" in controlled mode', () => {
    renderWizard({ currentStep: 1 });
    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument();
  });

  it('does not advance step internally in controlled mode', () => {
    const handler = vi.fn();
    renderWizard({ currentStep: 0, onStepChange: handler });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    // onStepChange fires but internal step does not advance (controlled)
    expect(handler).toHaveBeenCalledWith(1);
    // Still on step 1 content (currentStep=0 is still provided)
    expect(screen.getByText('Step 1 content')).toBeInTheDocument();
  });

  it('calls onStepChange with correct index when Back is clicked in controlled mode', () => {
    const handler = vi.fn();
    renderWizard({ currentStep: 1, onStepChange: handler });
    fireEvent.click(screen.getByRole('button', { name: /back/i }));
    expect(handler).toHaveBeenCalledWith(0);
  });

  it('aria-valuenow on progress bar reflects controlled currentStep', () => {
    const { container } = renderWizard({ currentStep: 2 });
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar?.getAttribute('aria-valuenow')).toBe('3');
  });
});

// ---------------------------------------------------------------------------
// 10. Empty steps — dev-mode console.warn
// ---------------------------------------------------------------------------

describe('WizardShell — empty steps guard', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('console.warn fires when steps is empty in non-production env', () => {
    // NODE_ENV is 'test' which is !== 'production', so the guard should fire.
    render(<WizardShell steps={[]} />);
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('[WizardShell]'),
    );
  });

  it('does not throw when steps is empty', () => {
    expect(() => render(<WizardShell steps={[]} />)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// 11. axe accessibility
// ---------------------------------------------------------------------------

const axe = configureAxe({
  rules: {
    // color-contrast requires computed styles not available in jsdom
    'color-contrast': { enabled: false },
    // region — WizardShell is a content widget, not a full page; axe flags
    // content not contained in landmarks when rendered in the minimal jsdom
    // harness. Not a production violation: WizardShell is always mounted inside
    // a <main> landmark in the real app.
    'region': { enabled: false },
  },
});

describe('WizardShell — axe accessibility', () => {
  it('first step has no critical a11y violations', async () => {
    renderWizard();
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('mid-wizard step has no critical a11y violations', async () => {
    render(<WizardShell steps={STEPS_4} defaultStep={1} />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('last step with Submit has no critical a11y violations', async () => {
    renderWizard({ defaultStep: 2, onSubmit: vi.fn() });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('wizard with Save & Exit has no critical a11y violations', async () => {
    renderWizard({ showSave: true, onSave: vi.fn(), defaultStep: 1 });
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  it('wizard with skippable step has no critical a11y violations', async () => {
    const steps: WizardStep[] = [
      { id: 's1', label: 'S1', content: <p>Step 1</p>, skippable: true },
      { id: 's2', label: 'S2', content: <p>Step 2</p> },
    ];
    render(<WizardShell steps={steps} />);
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('WizardShell — className passthrough', () => {
  it('merges additional className onto the outermost element', () => {
    const { container } = renderWizard({ className: 'custom-wizard-class' });
    const outer = container.firstElementChild;
    expect(outer?.className).toContain('custom-wizard-class');
  });

  it('outermost element className is trimmed (no leading/trailing whitespace)', () => {
    const { container } = renderWizard({ className: '' });
    const outer = container.firstElementChild;
    expect(outer?.className).not.toMatch(/^\s|\s$/);
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() in rendered output
// ---------------------------------------------------------------------------

describe('WizardShell — token hygiene', () => {
  it('no hardcoded hsl() in rendered HTML', () => {
    const { container } = renderWizard({ showSave: true, onSave: vi.fn(), defaultStep: 1 });
    expect(container.innerHTML).not.toContain('hsl(');
  });
});

// ---------------------------------------------------------------------------
// RTL context
// ---------------------------------------------------------------------------

describe('WizardShell — RTL context', () => {
  it('renders without errors in dir="rtl" wrapper', () => {
    expect(() =>
      render(
        <div dir="rtl">
          <WizardShell steps={STEPS_3} />
        </div>,
      ),
    ).not.toThrow();
  });

  it('does not use physical pl-/pr- classes in rendered HTML', () => {
    const { container } = render(
      <div dir="rtl">
        <WizardShell steps={STEPS_3} defaultStep={1} showSave onSave={vi.fn()} />
      </div>,
    );
    expect(container.innerHTML).not.toMatch(/\bpl-\d|\bpr-\d/);
  });
});
