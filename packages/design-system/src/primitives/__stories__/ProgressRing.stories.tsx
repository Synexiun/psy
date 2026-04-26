import type { Meta, StoryObj } from '@storybook/react';
import { ProgressRing } from '../ProgressRing';

const meta: Meta<typeof ProgressRing> = {
  title: 'Design System / Primitives / ProgressRing',
  component: ProgressRing,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised SVG progress ring. Geometry (radius, circumference, dashoffset) is clinically preserved from the original. Default `color` uses `var(--color-accent-bronze)` and `trackColor` uses `var(--color-surface-tertiary)`. Both props accept any CSS color string for full override flexibility.',
      },
    },
  },
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
      description: 'Current progress value',
    },
    max: {
      control: { type: 'number', min: 1 },
      description: 'Maximum value (default: 100)',
    },
    size: {
      control: { type: 'number', min: 40, max: 300, step: 10 },
      description: 'SVG size in px (default: 120)',
    },
    strokeWidth: {
      control: { type: 'number', min: 2, max: 40, step: 1 },
      description: 'Ring stroke width in px (default: 10)',
    },
    color: {
      control: 'text',
      description: 'Progress arc color — any CSS color string (default: var(--color-accent-bronze))',
    },
    trackColor: {
      control: 'text',
      description: 'Track circle color — any CSS color string (default: var(--color-surface-tertiary))',
    },
    label: {
      control: 'text',
      description: 'Primary label rendered below the ring',
    },
    sublabel: {
      control: 'text',
      description: 'Secondary label rendered below the primary label',
    },
    ariaLabel: {
      control: 'text',
      description: 'Accessible label for role="img" wrapper',
    },
  },
};

export default meta;
type Story = StoryObj<typeof ProgressRing>;

// ---------------------------------------------------------------------------
// Empty — value = 0
// ---------------------------------------------------------------------------

export const Empty: Story = {
  name: 'Empty',
  args: {
    value: 0,
    max: 100,
    ariaLabel: 'Progress: 0%',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`value=0` — empty ring. `dashoffset` equals the full circumference so no arc is drawn. Tests that negative values are also clamped to this state.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// HalfFull — value = 50
// ---------------------------------------------------------------------------

export const HalfFull: Story = {
  name: 'Half Full',
  args: {
    value: 50,
    max: 100,
    ariaLabel: 'Progress: 50%',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`value=50` — half-filled ring. `dashoffset` equals half the circumference.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Complete — value = 100
// ---------------------------------------------------------------------------

export const Complete: Story = {
  name: 'Complete',
  args: {
    value: 100,
    max: 100,
    ariaLabel: 'Progress: 100%',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`value=100` — fully filled ring. `dashoffset` equals 0. Values exceeding `max` are clamped to this state.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// WithLabel — value + label + sublabel
// ---------------------------------------------------------------------------

export const WithLabel: Story = {
  name: 'With Label',
  args: {
    value: 73,
    max: 100,
    label: '73%',
    sublabel: 'of daily goal',
    ariaLabel: 'Daily goal: 73%',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Renders with both `label` (large, `text-ink-primary`) and `sublabel` (small, `text-ink-tertiary`) beneath the ring. Typical use: streak percentage, session completion.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// CustomColor — override color and trackColor props
// ---------------------------------------------------------------------------

export const CustomColor: Story = {
  name: 'Custom Color',
  args: {
    value: 60,
    max: 100,
    color: 'var(--color-accent-teal)',
    trackColor: 'var(--color-border-subtle)',
    label: '60%',
    sublabel: 'calm sessions',
    ariaLabel: 'Calm session progress: 60%',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates that `color` and `trackColor` accept any CSS color string. Here `var(--color-accent-teal)` is used for a calm-tone variant. The prop API is backward compatible — only the defaults changed to Quiet Strength tokens.',
      },
    },
  },
};
