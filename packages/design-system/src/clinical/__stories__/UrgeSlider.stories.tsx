'use client';
import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { UrgeSlider } from '../UrgeSlider';

const meta: Meta<typeof UrgeSlider> = {
  title: 'Design System / Clinical / UrgeSlider',
  component: UrgeSlider,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Clinical 0–10 urge intensity slider for the just-in-time intervention flow (60–180 s window between urge and action). Enforces Latin digit display (Rule #9) and forwards `dir="rtl"` to Radix Slider for native thumb inversion in Arabic/Persian contexts.',
      },
    },
  },
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 10, step: 1 },
      description: 'Controlled value, 0–10',
    },
    dir: {
      control: { type: 'select' },
      options: ['ltr', 'rtl'],
      description: 'Text direction — pass "rtl" for ar/fa',
    },
    locale: {
      control: 'text',
      description: '"en" | "ar" | "fa" — display is always Latin digits regardless',
    },
    disabled: {
      control: 'boolean',
      description: 'Disables the slider',
    },
    ariaLabel: {
      control: 'text',
      description: 'Accessible label for the thumb (default: "Urge intensity")',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes on the root div',
    },
  },
};

export default meta;
type Story = StoryObj<typeof UrgeSlider>;

// ---------------------------------------------------------------------------
// Default — value=5, LTR
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    value: 5,
    onValueChange: () => {},
    ariaLabel: 'Urge intensity',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default LTR slider at mid-range (5). The value label below the track always renders in Latin digits per Rule #9.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// RTL — Arabic/Persian context
// ---------------------------------------------------------------------------

export const RTL: Story = {
  name: 'RTL (Arabic)',
  args: {
    value: 7,
    onValueChange: () => {},
    dir: 'rtl',
    locale: 'ar',
    ariaLabel: 'Urge intensity',
  },
  decorators: [
    (Story) => (
      <div dir="rtl" style={{ width: 280 }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story:
          'RTL variant used in Arabic/Persian locales. `dir="rtl"` is forwarded to Radix Slider.Root so thumb drag direction mirrors. Value label still shows Latin digit "7", never "٧" or "۷".',
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
    value: 3,
    onValueChange: () => {},
    disabled: true,
    ariaLabel: 'Urge intensity (read-only)',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Disabled state — thumb is not interactive and the track renders at reduced opacity. Used when the slider is shown for review but the user cannot interact with it.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// DarkBackground — verify token contrast
// ---------------------------------------------------------------------------

export const DarkBackground: Story = {
  name: 'Dark Background',
  args: {
    value: 8,
    onValueChange: () => {},
    ariaLabel: 'Urge intensity',
  },
  decorators: [
    (Story) => (
      <div
        style={{
          background: '#1a1a1a',
          padding: '48px',
          borderRadius: '12px',
          width: 280,
        }}
      >
        <Story />
      </div>
    ),
  ],
  parameters: {
    backgrounds: { default: 'dark' },
    docs: {
      description: {
        story:
          'Renders on a dark surface to verify that `accent-bronze` track fill and thumb border remain legible.',
      },
    },
  },
};
