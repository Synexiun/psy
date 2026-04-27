import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { WizardShell } from '../WizardShell';
import type { WizardStep } from '../WizardShell';

const meta: Meta<typeof WizardShell> = {
  title: 'Design System / Primitives / WizardShell',
  component: WizardShell,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Multi-step wizard shell with save-and-resume support. Used for assessment instruments (PHQ-9, GAD-7, WHO-5, etc.) where the user answers questions one at a time. Pure layout / navigation primitive — no form logic. Supports controlled and uncontrolled step management, a segmented progress bar, Back / Next / Skip / Submit footer buttons, and an optional Save & Exit header action. RTL-aware: all spacing uses logical CSS properties (ps-*/pe-*), so Arabic and Persian layouts mirror automatically.',
      },
    },
  },
  argTypes: {
    currentStep: {
      control: 'number',
      description: 'Controlled: current step index (0-based)',
    },
    defaultStep: {
      control: 'number',
      description: 'Uncontrolled: initial step index (default 0)',
    },
    showSave: {
      control: 'boolean',
      description: 'Show a Save & Exit button in the header',
    },
    nextLabel: { control: 'text' },
    backLabel: { control: 'text' },
    skipLabel: { control: 'text' },
    submitLabel: { control: 'text' },
    saveLabel: { control: 'text' },
    className: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof WizardShell>;

// ---------------------------------------------------------------------------
// Shared step sets
// ---------------------------------------------------------------------------

const PHQ9_STEPS_3: WizardStep[] = [
  {
    id: 'phq9-1',
    label: 'Little interest',
    content: (
      <div className="flex flex-col gap-4">
        <p className="text-sm font-medium text-ink-primary">
          Over the last 2 weeks, how often have you been bothered by:
        </p>
        <p className="text-base font-semibold text-ink-primary">
          Little interest or pleasure in doing things?
        </p>
        <div className="flex flex-col gap-2">
          {['Not at all', 'Several days', 'More than half the days', 'Nearly every day'].map(
            (opt) => (
              <label
                key={opt}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-border-subtle px-4 py-3 hover:bg-surface-secondary"
              >
                <input type="radio" name="phq9-1" className="accent-bronze" />
                <span className="text-sm text-ink-primary">{opt}</span>
              </label>
            ),
          )}
        </div>
      </div>
    ),
  },
  {
    id: 'phq9-2',
    label: 'Feeling down',
    content: (
      <div className="flex flex-col gap-4">
        <p className="text-sm font-medium text-ink-primary">
          Over the last 2 weeks, how often have you been bothered by:
        </p>
        <p className="text-base font-semibold text-ink-primary">
          Feeling down, depressed, or hopeless?
        </p>
        <div className="flex flex-col gap-2">
          {['Not at all', 'Several days', 'More than half the days', 'Nearly every day'].map(
            (opt) => (
              <label
                key={opt}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-border-subtle px-4 py-3 hover:bg-surface-secondary"
              >
                <input type="radio" name="phq9-2" className="accent-bronze" />
                <span className="text-sm text-ink-primary">{opt}</span>
              </label>
            ),
          )}
        </div>
      </div>
    ),
  },
  {
    id: 'phq9-3',
    label: 'Sleep',
    content: (
      <div className="flex flex-col gap-4">
        <p className="text-sm font-medium text-ink-primary">
          Over the last 2 weeks, how often have you been bothered by:
        </p>
        <p className="text-base font-semibold text-ink-primary">
          Trouble falling or staying asleep, or sleeping too much?
        </p>
        <div className="flex flex-col gap-2">
          {['Not at all', 'Several days', 'More than half the days', 'Nearly every day'].map(
            (opt) => (
              <label
                key={opt}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-border-subtle px-4 py-3 hover:bg-surface-secondary"
              >
                <input type="radio" name="phq9-3" className="accent-bronze" />
                <span className="text-sm text-ink-primary">{opt}</span>
              </label>
            ),
          )}
        </div>
      </div>
    ),
  },
];

const FOUR_STEP_STEPS: WizardStep[] = [
  {
    id: 'q1',
    label: 'Q1',
    content: <p className="text-sm text-ink-secondary">Question 1 content — answer below.</p>,
  },
  {
    id: 'q2',
    label: 'Q2',
    content: <p className="text-sm text-ink-secondary">Question 2 content — answer below.</p>,
  },
  {
    id: 'q3',
    label: 'Q3',
    content: <p className="text-sm text-ink-secondary">Question 3 content — answer below.</p>,
    skippable: true,
  },
  {
    id: 'q4',
    label: 'Q4',
    content: <p className="text-sm text-ink-secondary">Question 4 content — final step.</p>,
  },
];

// ---------------------------------------------------------------------------
// 1. Default — 3 steps, first step active
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (step 1 of 3)',
  args: {
    steps: PHQ9_STEPS_3,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Three-step wizard in its initial state. Back is disabled on the first step. Progress bar shows 1 of 3 segments filled with bronze. The Next button advances to step 2.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. MidWizard — step 2 of 4, with Save & Exit
// ---------------------------------------------------------------------------

export const MidWizard: Story = {
  name: 'Mid-wizard (step 2 of 4, Save & Exit)',
  args: {
    steps: FOUR_STEP_STEPS,
    defaultStep: 1,
    showSave: true,
    onSave: () => alert('Saved progress — resume later'),
    saveLabel: 'Save & Exit',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Step 2 of 4 with the Save & Exit action visible in the header. The Back button is enabled. Two of four progress segments are filled. Useful for long assessments where users may not complete in one session.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. LastStep — final step with Submit
// ---------------------------------------------------------------------------

export const LastStep: Story = {
  name: 'Last step (Submit)',
  args: {
    steps: PHQ9_STEPS_3,
    defaultStep: 2,
    onSubmit: () => alert('Assessment submitted'),
  },
  parameters: {
    docs: {
      description: {
        story:
          'On the final step, the Next button label changes to "Submit" and clicking it calls `onSubmit`. All progress segments are filled.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. WithSkippable — step with skippable=true
// ---------------------------------------------------------------------------

export const WithSkippable: Story = {
  name: 'With skippable step',
  args: {
    steps: FOUR_STEP_STEPS,
    defaultStep: 2,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Step 3 has `skippable: true`, so a Skip button appears between Back and Next. Skip advances to the next step without requiring an answer — useful for optional demographic or context questions.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 5–8. Dark/Light × EN/AR matrix
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark × EN',
  render: () => (
    <div data-theme="dark" style={{ maxWidth: 480 }}>
      <WizardShell
        steps={PHQ9_STEPS_3}
        defaultStep={1}
        showSave
        onSave={() => undefined}
        onSubmit={() => undefined}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dark theme, English locale. Step 2 of 3 — progress bar, Back enabled, Next.',
      },
    },
  },
};

export const DarkAr: Story = {
  name: 'Dark × AR',
  render: () => (
    <div data-theme="dark" dir="rtl" lang="ar" style={{ maxWidth: 480 }}>
      <WizardShell
        steps={[
          {
            id: 'ar-1',
            label: 'السؤال 1',
            content: (
              <p className="text-sm text-ink-secondary">محتوى السؤال الأول</p>
            ),
          },
          {
            id: 'ar-2',
            label: 'السؤال 2',
            content: (
              <p className="text-sm text-ink-secondary">محتوى السؤال الثاني</p>
            ),
          },
          {
            id: 'ar-3',
            label: 'السؤال 3',
            content: (
              <p className="text-sm text-ink-secondary">محتوى السؤال الثالث</p>
            ),
          },
        ]}
        defaultStep={1}
        showSave
        onSave={() => undefined}
        nextLabel="التالي"
        backLabel="السابق"
        saveLabel="حفظ والخروج"
        submitLabel="إرسال"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Dark theme, Arabic locale (`dir="rtl"`, `lang="ar"`). Logical CSS properties mirror the layout — the footer button order, progress fill direction, and header layout all flip correctly.',
      },
    },
  },
};

export const LightEn: Story = {
  name: 'Light × EN',
  render: () => (
    <div data-theme="light" style={{ maxWidth: 480 }}>
      <WizardShell
        steps={PHQ9_STEPS_3}
        defaultStep={0}
        onSubmit={() => undefined}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Light theme, English locale. First step — Back is disabled, Next is bronze.',
      },
    },
  },
};

export const LightAr: Story = {
  name: 'Light × AR',
  render: () => (
    <div data-theme="light" dir="rtl" lang="ar" style={{ maxWidth: 480 }}>
      <WizardShell
        steps={[
          {
            id: 'ar-1',
            label: 'السؤال 1',
            content: (
              <p className="text-sm text-ink-secondary">محتوى السؤال الأول</p>
            ),
          },
          {
            id: 'ar-2',
            label: 'السؤال 2',
            content: (
              <p className="text-sm text-ink-secondary">محتوى السؤال الثاني</p>
            ),
          },
        ]}
        defaultStep={0}
        nextLabel="التالي"
        backLabel="السابق"
        submitLabel="إرسال"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Light theme, Arabic locale (`dir="rtl"`, `lang="ar"`). Verify token values, logical layout, and RTL button ordering under light design tokens.',
      },
    },
  },
};
