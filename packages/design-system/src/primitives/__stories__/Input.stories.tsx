import type { Meta, StoryObj } from '@storybook/react';
import { Input } from '../Input';

const meta: Meta<typeof Input> = {
  title: 'Design System / Primitives / Input',
  component: Input,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised input field. Supports all standard HTML input types, invalid state via `aria-invalid`, and disabled state. Hardcoded `hsl()` colour literals have been replaced with semantic tokens (`border-border-subtle`, `bg-surface-primary`, `text-ink-primary`, `focus:ring-accent-bronze/30`, `border-signal-crisis`) so the component scales correctly across light and dark themes.',
      },
    },
  },
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'tel', 'search', 'url'],
      description: 'HTML input type',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the input and applies reduced-opacity styling',
    },
    'aria-invalid': {
      control: 'select',
      options: [undefined, true, 'true', 'false'],
      description: 'Marks the field as invalid — applies signal-crisis border and focus ring',
    },
    readOnly: {
      control: 'boolean',
      description: 'Makes the input read-only',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Input>;

// ---------------------------------------------------------------------------
// Default
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    type: 'text',
    placeholder: 'Enter text…',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default state — `border-border-subtle`, `bg-surface-primary`, `text-ink-primary`. Focus ring uses `accent-bronze`.',
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
    type: 'text',
    placeholder: 'Unavailable',
    disabled: true,
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
    type: 'text',
    placeholder: 'Required field',
    'aria-invalid': true,
    'aria-label': 'Name (required)',
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
// WithPlaceholder
// ---------------------------------------------------------------------------

export const WithPlaceholder: Story = {
  name: 'With placeholder',
  args: {
    type: 'email',
    placeholder: 'you@example.com',
    'aria-label': 'Email address',
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

// ---------------------------------------------------------------------------
// Password
// ---------------------------------------------------------------------------

export const Password: Story = {
  name: 'Password',
  args: {
    type: 'password',
    placeholder: 'Enter passphrase',
    'aria-label': 'Passphrase',
    autoComplete: 'current-password',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`type="password"` masks input. Pair with `autoComplete="current-password"` or `"new-password"` so password managers can detect the field correctly.',
      },
    },
  },
};
