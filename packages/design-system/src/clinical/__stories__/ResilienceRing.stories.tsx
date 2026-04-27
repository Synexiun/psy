'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { ResilienceRing } from '../ResilienceRing';

const meta: Meta<typeof ResilienceRing> = {
  title: 'Design System / Clinical / ResilienceRing',
  component: ResilienceRing,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Clinical ProgressRing variant that displays the user\'s resilience streak. ' +
          'Enforces CLAUDE.md Rule #3 (streak never decrements — monotonically non-decreasing across renders) ' +
          'and Rule #9 (Latin digits for clinical scores regardless of locale). ' +
          'Uses the accent-bronze token for the progress arc.',
      },
    },
  },
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 60, step: 1 },
      description: 'Current resilience day count',
    },
    max: {
      control: { type: 'range', min: 1, max: 90, step: 1 },
      description: 'Max value for the ring (default: 30)',
    },
    size: {
      control: { type: 'range', min: 60, max: 300, step: 10 },
      description: 'Ring size in px (default: 120)',
    },
    locale: {
      control: { type: 'select' },
      options: ['en', 'fr', 'ar', 'fa'],
      description: 'Locale — Latin digits are enforced regardless of this value (Rule #9)',
    },
    ariaLabel: {
      control: 'text',
      description: 'aria-label for the root element',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes on the root element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof ResilienceRing>;

// ---------------------------------------------------------------------------
// Default — 14 days / 30-day window
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    value: 14,
    max: 30,
    ariaLabel: '14 resilience days',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default 120px ring at 14 of 30 days. Bronze arc at ~47%. ' +
          'Center label rendered as Latin "14" via formatNumberClinical.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// HighStreak — 28 days / 30-day window
// ---------------------------------------------------------------------------

export const HighStreak: Story = {
  name: 'High Streak',
  args: {
    value: 28,
    max: 30,
    ariaLabel: '28 resilience days',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Near-complete 28/30 ring. Bronze arc at ~93%. ' +
          'Shows the visual completion state as the user approaches the 30-day milestone.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Arabic — locale="ar", value=42 (Latin digits enforced)
// ---------------------------------------------------------------------------

export const Arabic: Story = {
  name: 'Arabic locale',
  args: {
    value: 42,
    max: 60,
    locale: 'ar',
    ariaLabel: '42 resilience days',
  },
  parameters: {
    docs: {
      description: {
        story:
          'locale="ar" with value=42. Despite the Arabic locale, the center label ' +
          'renders as Latin "42" (not "٤٢") — Rule #9 enforcement via formatNumberClinical.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Persian — locale="fa", value=42 (Latin digits enforced)
// ---------------------------------------------------------------------------

export const Persian: Story = {
  name: 'Persian locale',
  args: {
    value: 42,
    max: 60,
    locale: 'fa',
    ariaLabel: '42 resilience days',
  },
  parameters: {
    docs: {
      description: {
        story:
          'locale="fa" with value=42. Despite the Persian locale, the center label ' +
          'renders as Latin "42" (not "۴۲") — Rule #9 enforcement via formatNumberClinical.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// DarkBackground — visualise token contrast on dark surfaces
// ---------------------------------------------------------------------------

export const DarkBackground: Story = {
  name: 'Dark Background',
  args: {
    value: 14,
    max: 30,
    ariaLabel: '14 resilience days',
  },
  decorators: [
    (Story) => (
      <div
        style={{
          background: '#1a1a1a',
          padding: '48px',
          borderRadius: '12px',
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
          'Renders on a dark surface to verify that the accent-bronze arc and ink tokens ' +
          'remain legible against dark backgrounds.',
      },
    },
  },
};
