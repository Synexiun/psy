'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { RingChart } from '../RingChart';

const meta: Meta<typeof RingChart> = {
  title: 'Design System / Primitives / RingChart',
  component: RingChart,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Multi-segment SVG ring chart primitive. Renders a single ring divided into colored segments — common use cases include skill distribution (% of sessions per category), PHQ-9 score breakdown, and weekly mood distribution. No center text by default; compose center content via the `centerContent` slot prop. Geometry (radius, circumference) is consistent with ProgressRing.',
      },
    },
  },
  argTypes: {
    size: {
      control: { type: 'number', min: 40, max: 300, step: 10 },
      description: 'SVG size in px (default: 120)',
    },
    strokeWidth: {
      control: { type: 'number', min: 2, max: 40, step: 1 },
      description: 'Ring stroke width in px (default: 10)',
    },
    trackColor: {
      control: 'text',
      description: 'Background track color (default: var(--color-surface-tertiary))',
    },
    gapDegrees: {
      control: { type: 'number', min: 0, max: 20, step: 0.5 },
      description: 'Gap between segments in degrees (default: 2)',
    },
    ariaLabel: {
      control: 'text',
      description: 'Accessible label for role="img" root div',
    },
  },
};

export default meta;
type Story = StoryObj<typeof RingChart>;

// ---------------------------------------------------------------------------
// 1. Default — 3 segments, PHQ-9 score distribution
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (PHQ Distribution)',
  args: {
    segments: [
      { id: 'minimal', value: 5, color: 'var(--color-signal-stable)', label: 'Minimal (0–4)' },
      { id: 'mild', value: 9, color: 'var(--color-accent-amber)', label: 'Mild (5–9)' },
      { id: 'moderate', value: 13, color: 'var(--color-signal-warning)', label: 'Moderate (10–14)' },
    ],
    ariaLabel: 'PHQ-9 score distribution: minimal 5, mild 9, moderate 13',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Three segments representing a PHQ-9 score distribution across severity bands. Colors map to Quiet Strength signal tokens.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. SingleSegment
// ---------------------------------------------------------------------------

export const SingleSegment: Story = {
  name: 'Single Segment',
  args: {
    segments: [
      { id: 'resilience', value: 100, color: 'var(--color-accent-bronze)', label: 'Resilience' },
    ],
    ariaLabel: 'Single segment: Resilience 100%',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Single segment — no gap is applied (one segment means no inter-segment spacing). Renders as a complete ring in the segment color.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. EmptySegments — total = 0
// ---------------------------------------------------------------------------

export const EmptySegments: Story = {
  name: 'Empty Segments (total = 0)',
  args: {
    segments: [],
    ariaLabel: 'No data available',
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `segments` is empty (or all values sum to zero) only the track ring is rendered. Use this state to signal "no data yet" before a user has any recorded sessions.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. WithCenterContent — total score label centered
// ---------------------------------------------------------------------------

export const WithCenterContent: Story = {
  name: 'With Center Content',
  render: () => (
    <RingChart
      segments={[
        { id: 'calm', value: 60, color: 'var(--color-accent-teal)', label: 'Calm sessions' },
        { id: 'urge', value: 25, color: 'var(--color-accent-amber)', label: 'Urge present' },
        { id: 'crisis', value: 15, color: 'var(--color-signal-warning)', label: 'Crisis activated' },
      ]}
      centerContent={
        <div style={{ textAlign: 'center', lineHeight: 1.2 }}>
          <div style={{ fontSize: 22, fontWeight: 700 }}>100</div>
          <div style={{ fontSize: 11, opacity: 0.6 }}>sessions</div>
        </div>
      }
      ariaLabel="Session type distribution: calm 60, urge 25, crisis 15 — 100 sessions total"
    />
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates the `centerContent` slot. A total count label is composed into the ring center. The root `aria-label` carries the full accessible description — the center content is purely decorative.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 5. DarkBackground — token preview on dark surface
// ---------------------------------------------------------------------------

export const DarkBackground: Story = {
  name: 'Dark Background',
  render: () => (
    <div
      className="bg-surface-primary p-10 rounded-2xl flex gap-10 items-center"
      data-theme="dark"
    >
      <RingChart
        segments={[
          { id: 'calm', value: 60, color: 'var(--color-accent-teal)', label: 'Calm sessions' },
          { id: 'urge', value: 40, color: 'var(--color-accent-amber)', label: 'Urge present' },
        ]}
        ariaLabel="Mood distribution: calm 60%, urge 40%"
      />
      <RingChart
        segments={[
          { id: 'minimal', value: 5, color: 'var(--color-signal-stable)', label: 'Minimal' },
          { id: 'mild', value: 9, color: 'var(--color-accent-amber)', label: 'Mild' },
          { id: 'moderate', value: 13, color: 'var(--color-signal-warning)', label: 'Moderate' },
        ]}
        size={80}
        strokeWidth={8}
        centerContent={
          <span style={{ fontSize: 14, fontWeight: 700 }}>27</span>
        }
        ariaLabel="PHQ-9 distribution, total score 27"
      />
      <RingChart
        segments={[]}
        ariaLabel="No data available"
        size={80}
      />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Dark theme — three RingChart variants side by side: two-segment mood ring, three-segment PHQ distribution with center score, and the empty/no-data state.',
      },
    },
  },
};
