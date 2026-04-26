import type { Meta, StoryObj } from '@storybook/react';
import { Textarea } from '../Textarea';

const meta: Meta<typeof Textarea> = {
  title: 'Design System / Primitives / Textarea',
  component: Textarea,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised textarea. Supports configurable row count, resize behaviour (none/vertical/horizontal), invalid state via `aria-invalid`, and disabled state. Hardcoded `hsl()` colour literals have been replaced with semantic tokens (`border-border-subtle`, `bg-surface-primary`, `text-ink-primary`, `focus:ring-accent-bronze/30`, `border-signal-crisis`) so the component scales correctly across light and dark themes.',
      },
    },
  },
  argTypes: {
    rows: {
      control: 'number',
      description: 'Number of visible text rows (default: 3)',
    },
    resize: {
      control: 'select',
      options: ['none', 'vertical', 'horizontal'],
      description: 'CSS resize behaviour applied to the textarea',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the textarea and applies reduced-opacity styling',
    },
    'aria-invalid': {
      control: 'select',
      options: [undefined, true, 'true', 'false'],
      description: 'Marks the field as invalid — applies signal-crisis border and focus ring',
    },
    readOnly: {
      control: 'boolean',
      description: 'Makes the textarea read-only',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Textarea>;

// ---------------------------------------------------------------------------
// Default
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    placeholder: 'Enter your notes here…',
    rows: 3,
    resize: 'vertical',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default state — `border-border-subtle`, `bg-surface-primary`, `text-ink-primary`. Focus ring uses `accent-bronze`. Resize is vertical by default.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Disabled
// ---------------------------------------------------------------------------

export const Disabled: Story = {
  name: 'Disabled',
  args: {
    placeholder: 'This field is unavailable',
    disabled: true,
    rows: 3,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Disabled state applies `cursor-not-allowed opacity-50 bg-surface-tertiary`. The field is not interactive.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Invalid
// ---------------------------------------------------------------------------

export const Invalid: Story = {
  name: 'Invalid (aria-invalid)',
  args: {
    placeholder: 'This field has an error',
    'aria-invalid': true,
    'aria-label': 'Notes (required)',
    rows: 3,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`aria-invalid={true}` applies `border-signal-crisis` and `focus:ring-signal-crisis/30`. Used for form validation error states. The `aria-invalid` attribute is forwarded to the DOM for screen-reader consumers.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// ResizeNone
// ---------------------------------------------------------------------------

export const ResizeNone: Story = {
  name: 'Resize: None',
  args: {
    placeholder: 'Fixed size — cannot be resized',
    resize: 'none',
    rows: 4,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`resize="none"` applies `resize-none` to prevent the user from dragging the textarea handle. Use when layout stability is required (e.g. inside a card with fixed height).',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// WithPlaceholder
// ---------------------------------------------------------------------------

export const WithPlaceholder: Story = {
  name: 'With placeholder',
  args: {
    placeholder: 'Describe how you are feeling right now…',
    'aria-label': 'Mood journal entry',
    rows: 5,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Placeholder text renders in `text-ink-tertiary` (muted, accessible contrast). Use `aria-label` or a paired `<label>` element — placeholder alone is not a sufficient accessible label.',
      },
    },
  },
};
