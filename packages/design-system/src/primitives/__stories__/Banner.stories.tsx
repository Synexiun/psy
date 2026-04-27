'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { Banner } from '../Banner';

const meta: Meta<typeof Banner> = {
  title: 'Design System / Primitives / Banner',
  component: Banner,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Dismissable inline feedback banner. Three severity variants: `info`, `warning`, `error`. ' +
          'Supports both controlled and uncontrolled open state. ' +
          'Uses `role="status"` (polite) for info/warning and `role="alert"` (assertive) for error.',
      },
    },
  },
  argTypes: {
    message: {
      control: 'text',
      description: 'Feedback message — required',
    },
    variant: {
      control: 'select',
      options: ['info', 'warning', 'error'],
      description: 'Severity variant (default: info)',
    },
    hideDismiss: {
      control: 'boolean',
      description: 'Hide the dismiss button — banner becomes permanent',
    },
    dismissLabel: {
      control: 'text',
      description: 'Accessible label for the dismiss button (sr-only)',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Banner>;

// ---------------------------------------------------------------------------
// 1. Default (info)
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (info)',
  args: {
    message: 'PHQ-9 due tomorrow — tap here to begin your check-in.',
    variant: 'info',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default `info` variant. `role="status"` (polite live region). ' +
          'Tokens: `bg-surface-secondary`, `border-border-subtle`, `text-ink-primary`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. Warning
// ---------------------------------------------------------------------------

export const Warning: Story = {
  name: 'Warning',
  args: {
    message: 'Offline mode active — data will sync when connection is restored.',
    variant: 'warning',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`warning` variant. `role="status"`. Tokens: `bg-amber-50`, `border-amber-300`, `text-amber-900`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. Error
// ---------------------------------------------------------------------------

export const Error: Story = {
  name: 'Error',
  args: {
    message: 'Sync failed — tap to retry.',
    variant: 'error',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`error` variant. `role="alert"` (assertive — screen reader announces immediately). ' +
          'Tokens: `bg-red-50`, `border-red-300`, `text-red-900`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. HideDismiss (permanent)
// ---------------------------------------------------------------------------

export const HideDismiss: Story = {
  name: 'HideDismiss (permanent)',
  args: {
    message: 'Offline mode active — dismiss is not available.',
    variant: 'warning',
    hideDismiss: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`hideDismiss=true` removes the dismiss button, making the banner permanent in the UI.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 5. Controlled (open=true)
// ---------------------------------------------------------------------------

export const Controlled: Story = {
  name: 'Controlled (open=true)',
  args: {
    message: 'This banner is controlled externally — dismissing calls onDismiss but does not hide the banner.',
    variant: 'info',
    open: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `open` is provided the component is fully controlled. ' +
          'Clicking dismiss fires `onDismiss` but the consumer owns the visibility state.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 6. RTLWrapper
// ---------------------------------------------------------------------------

export const RTLWrapper: Story = {
  name: 'RTL Layout',
  render: () => (
    <div dir="rtl" lang="ar">
      <Banner
        message="وضع عدم الاتصال نشط — ستتم المزامنة عند استعادة الاتصال."
        variant="info"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Banner inside a RTL wrapper (`dir="rtl"`). ' +
          'Flex layout mirrors correctly — icon leads on the right, dismiss button on the left.',
      },
    },
  },
};
