import type { Meta, StoryObj } from '@storybook/react';
import { Sparkline } from '../Sparkline';

const meta: Meta<typeof Sparkline> = {
  title: 'Design System / Primitives / Sparkline',
  component: Sparkline,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'SVG mini-chart backed by @visx/shape (LinePath + AreaClosed) and @visx/scale (scaleLinear). ' +
          'Designed for compact clinical trend visualisation — mood, urge intensity, resilience streak deltas. ' +
          'Returns null for data.length < 2 (safe to render with loading/empty states). ' +
          'Default color is var(--color-accent-bronze) to match the Quiet Strength token palette.',
      },
    },
  },
  argTypes: {
    data: {
      control: 'object',
      description: 'Array of numeric data points. Requires at least 2 points to render.',
    },
    width: {
      control: { type: 'number', min: 40, max: 400, step: 10 },
      description: 'SVG width in pixels (default 120)',
    },
    height: {
      control: { type: 'number', min: 20, max: 200, step: 4 },
      description: 'SVG height in pixels (default 40)',
    },
    color: {
      control: 'color',
      description: "Stroke and fill color (default 'var(--color-accent-bronze)')",
    },
    strokeWidth: {
      control: { type: 'number', min: 1, max: 6, step: 0.5 },
      description: 'Line stroke width in pixels (default 2)',
    },
    ariaLabel: {
      control: 'text',
      description: 'Accessible label surfaced as aria-label on the SVG element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Sparkline>;

// ---------------------------------------------------------------------------
// Default — accent-bronze, 120 × 40
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (accent-bronze)',
  args: {
    data: [3, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 6, 8, 9, 8, 7, 8, 9, 8, 7],
    width: 120,
    height: 40,
    ariaLabel: 'Mood trend over last 20 check-ins',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default rendering at 120 × 40 px with the Quiet Strength accent-bronze token. ' +
          'This mirrors the dimensions used in the MoodSparkline dashboard widget (stub data).',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// TealLine — signal-stable color
// ---------------------------------------------------------------------------

export const TealLine: Story = {
  name: 'Teal line (signal-stable)',
  args: {
    data: [5, 6, 5, 7, 6, 8, 7, 9, 8, 7, 8, 9],
    width: 160,
    height: 48,
    color: 'var(--color-signal-stable)',
    strokeWidth: 2,
    ariaLabel: 'Resilience trend',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Custom color using the signal-stable token — suitable for resilience streak or urge-free day charts.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// NarrowWide — exercises dimension flexibility
// ---------------------------------------------------------------------------

export const NarrowWide: Story = {
  name: 'Narrow → Wide (dimension comparison)',
  render: () => (
    <div className="flex items-end gap-6">
      <div className="flex flex-col items-center gap-1">
        <Sparkline
          data={[2, 4, 3, 6, 5, 7, 6, 8]}
          width={80}
          height={32}
          ariaLabel="Narrow sparkline"
        />
        <span style={{ fontSize: 11, color: '#888' }}>80 × 32</span>
      </div>
      <div className="flex flex-col items-center gap-1">
        <Sparkline
          data={[2, 4, 3, 6, 5, 7, 6, 8]}
          width={240}
          height={48}
          ariaLabel="Wide sparkline"
        />
        <span style={{ fontSize: 11, color: '#888' }}>240 × 48</span>
      </div>
      <div className="flex flex-col items-center gap-1">
        <Sparkline
          data={[2, 4, 3, 6, 5, 7, 6, 8]}
          width={360}
          height={60}
          strokeWidth={3}
          ariaLabel="Extra-wide sparkline"
        />
        <span style={{ fontSize: 11, color: '#888' }}>360 × 60, sw=3</span>
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Three widths side-by-side to confirm the x-scale stretches correctly. ' +
          'The curve shape should be identical — only the horizontal extent changes.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// SinglePoint — null guard (returns nothing)
// ---------------------------------------------------------------------------

export const SinglePoint: Story = {
  name: 'Single point → null (safe empty state)',
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-start' }}>
      <span style={{ fontSize: 12, color: '#888' }}>
        data.length = 0 → no SVG rendered (blank below):
      </span>
      <div style={{ border: '1px dashed #ccc', width: 120, height: 40 }}>
        <Sparkline data={[]} />
      </div>
      <span style={{ fontSize: 12, color: '#888' }}>
        data.length = 1 → no SVG rendered (blank below):
      </span>
      <div style={{ border: '1px dashed #ccc', width: 120, height: 40 }}>
        <Sparkline data={[7]} />
      </div>
      <span style={{ fontSize: 12, color: '#888' }}>
        data.length = 2 → renders correctly:
      </span>
      <Sparkline data={[3, 9]} width={120} height={40} ariaLabel="Two-point trend" />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Demonstrates the null-guard: 0 or 1 data points render nothing (safe to use in loading states). ' +
          '2 data points is the minimum to produce a visible line.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// CustomColor — hex / hsl override
// ---------------------------------------------------------------------------

export const CustomColor: Story = {
  name: 'Custom color',
  args: {
    data: [1, 3, 2, 5, 4, 7, 5, 8, 6, 9, 7, 8, 9],
    width: 160,
    height: 48,
    color: 'hsl(280, 70%, 55%)',
    strokeWidth: 2.5,
    ariaLabel: 'Custom color trend',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Any CSS color value is accepted — hex, hsl(), or a CSS custom property. ' +
          'The fill area is always rendered at 12 % opacity of the same color.',
      },
    },
  },
};
