'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { Trend } from '../Trend';

const meta: Meta<typeof Trend> = {
  title: 'Design System / Primitives / Trend',
  component: Trend,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Compact card composing Stat + Sparkline side-by-side. ' +
          'Renders a headline metric (via Stat) next to a mini SVG chart (via Sparkline) ' +
          'in a single rounded card. Designed for dashboard widgets, progress summaries, ' +
          'and clinical trend callouts. Default size is `sm` (compact). ' +
          'When `clinical` is true the number is rendered with `direction: ltr` and ' +
          '`font-variant-numeric: tabular-nums` to enforce Latin digits across all locales (Rule #9). ' +
          'Pass `formatValue={formatNumberClinical}` from `@disciplineos/i18n-catalog` in clinical contexts.',
      },
    },
  },
  argTypes: {
    value: {
      control: { type: 'number' },
      description: 'The current numeric value (passed to Stat)',
    },
    label: {
      control: 'text',
      description: 'Visible label (passed to Stat)',
    },
    data: {
      control: 'object',
      description: 'Historical data points including current value — passed to Sparkline',
    },
    delta: {
      control: { type: 'number' },
      description: 'Change since last period — passed to Stat',
    },
    deltaDirection: {
      control: 'select',
      options: ['up', 'down', 'neutral'],
      description: 'Explicit delta direction override',
    },
    deltaLabel: {
      control: 'text',
      description: 'Delta label suffix, e.g. "vs last week"',
    },
    clinical: {
      control: 'boolean',
      description: 'Enforce ltr + tabular-nums for clinical number rendering (Rule #9)',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Stat size variant (default sm — Trend is compact)',
    },
    color: {
      control: 'color',
      description: "Sparkline color (default 'var(--color-accent-bronze)')",
    },
    sparklineAriaLabel: {
      control: 'text',
      description: 'aria-label forwarded to the embedded <svg>',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Trend>;

// ---------------------------------------------------------------------------
// 1. Default
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    value: 20,
    label: 'Sessions',
    data: [10, 15, 12, 18, 14, 20],
    sparklineAriaLabel: 'Sessions trend over 6 weeks',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default compact card — `sm` Stat hero number with a 6-point sparkline. ' +
          'No delta. Background token: `bg-surface-secondary`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. WithDelta
// ---------------------------------------------------------------------------

export const WithDelta: Story = {
  name: 'With Positive Delta',
  args: {
    value: 20,
    label: 'Sessions',
    data: [10, 15, 12, 18, 14, 20],
    delta: 5,
    deltaLabel: 'vs last week',
    sparklineAriaLabel: 'Sessions trend over 6 weeks',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`delta > 0` → `text-signal-stable` (teal) with up-arrow in the Stat column.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. NegativeDelta
// ---------------------------------------------------------------------------

export const NegativeDelta: Story = {
  name: 'Negative Delta',
  args: {
    value: 10,
    label: 'PHQ-9 Score',
    data: [6, 8, 9, 11, 12, 10],
    delta: -2,
    deltaLabel: 'vs baseline',
    sparklineAriaLabel: 'PHQ-9 trend over 6 assessments',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`delta < 0` → `text-signal-warning` (amber) with down-arrow. Signals a score increase (decline).',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. Clinical
// ---------------------------------------------------------------------------

export const Clinical: Story = {
  name: 'Clinical (LTR enforced)',
  args: {
    value: 14,
    label: 'PHQ-9 Score',
    data: [8, 10, 12, 11, 13, 14],
    delta: -3,
    deltaLabel: 'vs baseline',
    clinical: true,
    formatValue: (n: number) => n.toString(),
    sparklineAriaLabel: 'PHQ-9 trend over 6 assessments',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`clinical=true` enforces `direction: ltr` and `font-variant-numeric: tabular-nums` ' +
          'on the hero number. In production pass `formatValue={formatNumberClinical}` from ' +
          '`@disciplineos/i18n-catalog`. Ensures Latin digits regardless of page locale (Rule #9).',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 5. SmallData — only 1 data point → sparkline gracefully absent
// ---------------------------------------------------------------------------

export const SmallData: Story = {
  name: 'Small data (sparkline absent)',
  args: {
    value: 5,
    label: 'Check-ins',
    data: [5],
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `data.length < 2` Sparkline returns null — the right column is empty. ' +
          'Stat still renders normally; the card layout remains intact.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 6. DarkEn — dark background wrapper
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark — English',
  render: () => (
    <div
      className="bg-surface-primary p-8 rounded-2xl flex flex-col gap-4"
      data-theme="dark"
    >
      <Trend
        value={20}
        label="Sessions"
        data={[10, 15, 12, 18, 14, 20]}
        delta={5}
        deltaLabel="vs last week"
        sparklineAriaLabel="Sessions trend"
      />
      <Trend
        value={14}
        label="PHQ-9 Score"
        data={[8, 10, 12, 11, 13, 14]}
        delta={-3}
        deltaLabel="vs baseline"
        clinical={true}
        formatValue={(n) => n.toString()}
        sparklineAriaLabel="PHQ-9 trend"
      />
      <Trend
        value={47}
        label="Resilience Days"
        data={[20, 25, 30, 35, 42, 47]}
        sparklineAriaLabel="Resilience streak trend"
      />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: 'Dark theme — English locale. Three Trend cards stacked vertically.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 7. LightEn — light background wrapper
// ---------------------------------------------------------------------------

export const LightEn: Story = {
  name: 'Light — English',
  render: () => (
    <div
      className="bg-surface-primary p-8 rounded-2xl flex flex-col gap-4"
      data-theme="light"
    >
      <Trend
        value={20}
        label="Sessions"
        data={[10, 15, 12, 18, 14, 20]}
        delta={5}
        deltaLabel="vs last week"
        sparklineAriaLabel="Sessions trend"
      />
      <Trend
        value={14}
        label="PHQ-9 Score"
        data={[8, 10, 12, 11, 13, 14]}
        delta={-3}
        deltaLabel="vs baseline"
        clinical={true}
        formatValue={(n) => n.toString()}
        sparklineAriaLabel="PHQ-9 trend"
      />
      <Trend
        value={47}
        label="Resilience Days"
        data={[20, 25, 30, 35, 42, 47]}
        sparklineAriaLabel="Resilience streak trend"
      />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: 'Light theme — English locale. Tokens remap via `[data-theme="light"]` overrides in globals.css.',
      },
    },
  },
};
