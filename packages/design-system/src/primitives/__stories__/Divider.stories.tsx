import type { Meta, StoryObj } from '@storybook/react';
import { Divider } from '../Divider';

const meta: Meta<typeof Divider> = {
  title: 'Design System / Primitives / Divider',
  component: Divider,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised divider. Three variants: plain horizontal `<hr>`, vertical inline rule, and horizontal with a centred label. All border colours use the `border-border-subtle` token; label text uses `text-ink-tertiary`. The vertical variant uses the logical property `border-s` (border-inline-start) so it is RTL-safe.',
      },
    },
  },
  argTypes: {
    orientation: {
      control: 'select',
      options: ['horizontal', 'vertical'],
      description: 'Axis of the separator rule',
    },
    label: {
      control: 'text',
      description: 'Optional centred label text (horizontal orientation only)',
    },
    className: {
      control: 'text',
      description: 'Additional Tailwind classes merged onto the root element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Divider>;

// ---------------------------------------------------------------------------
// Horizontal (default)
// ---------------------------------------------------------------------------

export const Horizontal: Story = {
  name: 'Horizontal (default)',
  args: {
    orientation: 'horizontal',
  },
  decorators: [
    (Story) => (
      <div className="w-80">
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story:
          'Plain horizontal separator rendered as an `<hr>` with `border-t border-border-subtle`. The `<hr>` element carries the implicit ARIA separator role so no explicit `role` is needed — we add it anyway for clarity.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Vertical
// ---------------------------------------------------------------------------

export const Vertical: Story = {
  name: 'Vertical',
  args: {
    orientation: 'vertical',
  },
  decorators: [
    (Story) => (
      <div className="flex h-12 items-center gap-3">
        <span className="text-sm text-ink-secondary">Left</span>
        <Story />
        <span className="text-sm text-ink-secondary">Right</span>
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story:
          'Vertical separator rendered as a `<div>` with `w-px h-full self-stretch border-s border-border-subtle`. Uses the logical property `border-s` (not physical `border-l`) for RTL consistency.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// WithLabel
// ---------------------------------------------------------------------------

export const WithLabel: Story = {
  name: 'With label',
  args: {
    label: 'or',
  },
  decorators: [
    (Story) => (
      <div className="w-80">
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story:
          'Horizontal separator with a centred label. The label text uses `text-ink-tertiary text-xs px-3`; the flanking rules use `border-t border-border-subtle`. The container carries `role="separator" aria-orientation="horizontal"`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// InContext — between two text blocks
// ---------------------------------------------------------------------------

export const InContext: Story = {
  name: 'In context (between text blocks)',
  render: () => (
    <div className="w-80 rounded-xl bg-surface-primary p-5 shadow-sm">
      <p className="text-sm text-ink-primary">
        Sign in with your passkey to continue.
      </p>
      <Divider label="or" className="my-4" />
      <p className="text-sm text-ink-secondary">
        Use your email and password instead.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Shows the labeled Divider in a realistic card context, separating two authentication options. Demonstrates `className="my-4"` for vertical spacing.',
      },
    },
  },
};
