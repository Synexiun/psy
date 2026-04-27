'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { BarChart } from '../BarChart';

const meta: Meta<typeof BarChart> = {
  title: 'Design System / Primitives / BarChart',
  component: BarChart,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Visx-backed vertical bar chart for displaying time-series instrument data — e.g. PHQ-9 score per week or session counts per day. ' +
          'Uses scaleBand for the x-axis and scaleLinear for the y-axis. ' +
          'Renders an accessible role="img" root div with aria-hidden SVG. ' +
          'Renders a "No data" empty state when the data array is empty.',
      },
    },
  },
  argTypes: {
    width: {
      control: { type: 'number', min: 100, max: 800, step: 10 },
      description: 'Chart width in px (default: 320)',
    },
    height: {
      control: { type: 'number', min: 80, max: 400, step: 10 },
      description: 'Chart height in px (default: 200)',
    },
    color: {
      control: 'color',
      description: "Bar fill color (default: 'var(--color-accent-bronze)')",
    },
    yAxisLabel: {
      control: 'text',
      description: 'Optional y-axis label rendered as rotated text at the top-left',
    },
    yMax: {
      control: { type: 'number', min: 1, max: 100 },
      description: 'Fixed y-axis maximum — auto-computed from data when omitted',
    },
    ariaLabel: {
      control: 'text',
      description: 'Accessible label for the role="img" root div',
    },
  },
};

export default meta;
type Story = StoryObj<typeof BarChart>;

// ---------------------------------------------------------------------------
// 1. Default — weekly PHQ-9 scores Mon–Fri
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (Weekly PHQ-9)',
  args: {
    data: [
      { label: 'Mon', value: 8 },
      { label: 'Tue', value: 10 },
      { label: 'Wed', value: 7 },
      { label: 'Thu', value: 12 },
      { label: 'Fri', value: 9 },
    ],
    width: 320,
    height: 200,
    ariaLabel: 'Weekly PHQ-9 scores: Mon 8, Tue 10, Wed 7, Thu 12, Fri 9',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default rendering with weekly PHQ-9 scores. Bronze accent color with scaleBand x-axis and auto-computed y maximum.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. Empty — no data
// ---------------------------------------------------------------------------

export const Empty: Story = {
  name: 'Empty (no data)',
  args: {
    data: [],
    width: 320,
    height: 200,
    ariaLabel: 'No data available',
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `data` is an empty array the component renders a "No data" placeholder at the chart dimensions. Use this state before a user has any recorded sessions.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. WithYAxisLabel — shows rotated label
// ---------------------------------------------------------------------------

export const WithYAxisLabel: Story = {
  name: 'With Y-Axis Label',
  args: {
    data: [
      { label: 'Week 1', value: 14 },
      { label: 'Week 2', value: 11 },
      { label: 'Week 3', value: 9 },
      { label: 'Week 4', value: 7 },
    ],
    width: 320,
    height: 200,
    yAxisLabel: 'PHQ-9',
    yMax: 27,
    ariaLabel: 'Monthly PHQ-9 trend: Week 1–4 scores showing improvement from 14 to 7',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Shows the optional `yAxisLabel` prop — a rotated text element at the top-left of the plot area. ' +
          'Also demonstrates a fixed `yMax` of 27 (the maximum possible PHQ-9 score) so the y-axis is anchored consistently across time periods.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. DarkBackground — token preview on dark surface
// ---------------------------------------------------------------------------

export const DarkBackground: Story = {
  name: 'Dark Background',
  render: () => (
    <div
      className="bg-surface-primary p-10 rounded-2xl flex flex-col gap-8"
      data-theme="dark"
    >
      <BarChart
        data={[
          { label: 'Mon', value: 8 },
          { label: 'Tue', value: 10 },
          { label: 'Wed', value: 7 },
          { label: 'Thu', value: 12 },
          { label: 'Fri', value: 9 },
        ]}
        width={320}
        height={180}
        ariaLabel="Weekly PHQ-9 scores on dark background"
      />
      <BarChart
        data={[
          { label: 'Mon', value: 4, color: 'var(--color-signal-stable)' },
          { label: 'Tue', value: 6, color: 'var(--color-signal-stable)' },
          { label: 'Wed', value: 3, color: 'var(--color-accent-amber)' },
          { label: 'Thu', value: 8, color: 'var(--color-signal-stable)' },
          { label: 'Fri', value: 5, color: 'var(--color-signal-stable)' },
        ]}
        width={320}
        height={180}
        yAxisLabel="Sessions"
        ariaLabel="Daily session counts with per-bar color on dark background"
      />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Dark theme — two BarChart variants stacked: a uniform bronze chart and a per-bar colored chart using signal tokens. ' +
          'Wednesday (urge day) is highlighted in amber; all other days use signal-stable.',
      },
    },
  },
};
