import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '../Button';

const meta: Meta<typeof Button> = {
  title: 'Design System / Primitives / Button',
  component: Button,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised button. Supports five semantic variants and four sizes. `loading` implies `disabled` and renders a spinner. All hover/active states use opacity-based modifiers so the token palette scales across light and dark themes without numeric colour steps.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'calm', 'ghost', 'crisis', 'secondary'],
      description: 'Semantic colour variant',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'crisis'],
      description: 'Size preset',
    },
    loading: {
      control: 'boolean',
      description: 'Shows a spinner and disables the button',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the button without a spinner',
    },
    children: {
      control: 'text',
      description: 'Button label',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

// ---------------------------------------------------------------------------
// Variants
// ---------------------------------------------------------------------------

export const Primary: Story = {
  name: 'Primary (accent-bronze)',
  args: {
    variant: 'primary',
    size: 'md',
    children: 'Start session',
  },
};

export const Calm: Story = {
  name: 'Calm (accent-teal)',
  args: {
    variant: 'calm',
    size: 'md',
    children: 'Breathing exercise',
  },
};

export const Ghost: Story = {
  name: 'Ghost',
  args: {
    variant: 'ghost',
    size: 'md',
    children: 'Cancel',
  },
};

export const Crisis: Story = {
  name: 'Crisis (signal-crisis)',
  args: {
    variant: 'crisis',
    size: 'crisis',
    children: 'Get help now',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Crisis variant with `size="crisis"` — full-width, min-height 56 px, prominent touch target. Used only in T3/T4 crisis escalation flows.',
      },
    },
  },
};

export const Secondary: Story = {
  name: 'Secondary (surface-tertiary)',
  args: {
    variant: 'secondary',
    size: 'md',
    children: 'View details',
  },
};

// ---------------------------------------------------------------------------
// States
// ---------------------------------------------------------------------------

export const Loading: Story = {
  name: 'Loading state',
  args: {
    variant: 'primary',
    size: 'md',
    loading: true,
    children: 'Saving…',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`loading` renders a spinner, sets `aria-busy="true"`, and disables the button — preventing double-submit.',
      },
    },
  },
};

export const Disabled: Story = {
  name: 'Disabled state',
  args: {
    variant: 'primary',
    size: 'md',
    disabled: true,
    children: 'Unavailable',
  },
};

// ---------------------------------------------------------------------------
// Sizes
// ---------------------------------------------------------------------------

export const AllSizes: Story = {
  name: 'All sizes — primary',
  render: () => (
    <div className="flex flex-col items-start gap-3">
      <Button variant="primary" size="sm">Small (sm)</Button>
      <Button variant="primary" size="md">Medium (md)</Button>
      <Button variant="primary" size="lg">Large (lg)</Button>
      <Button variant="crisis" size="crisis">Crisis full-width</Button>
    </div>
  ),
};

// ---------------------------------------------------------------------------
// All variants at a glance
// ---------------------------------------------------------------------------

export const AllVariants: Story = {
  name: 'All variants',
  render: () => (
    <div className="flex flex-col items-start gap-3">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="calm">Calm</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="crisis" size="crisis">Crisis</Button>
    </div>
  ),
};
