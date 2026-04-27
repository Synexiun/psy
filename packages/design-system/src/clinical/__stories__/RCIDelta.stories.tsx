'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { RCIDelta } from '../RCIDelta';

const meta: Meta<typeof RCIDelta> = {
  title: 'Design System / Clinical / RCIDelta',
  component: RCIDelta,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Displays a Reliable Change Index (RCI) delta — a measure of statistically ' +
          'significant change in a clinical score between two assessments (Jacobson & Truax, 1991). ' +
          'Shows: numeric delta (+/−) in Latin digits (Rule #9), a dot-scale significance ' +
          'indicator (●●●, ●●○, ●○○), and a direction label. ' +
          'PHQ-9 threshold: |delta| ≥ 5.26 = significant, ≥ 2.5 = moderate, < 2.5 = non-significant.',
      },
    },
  },
  argTypes: {
    delta: {
      control: { type: 'number' },
      description: 'The delta value (+/−). Positive = improvement (score decreased).',
    },
    locale: {
      control: { type: 'select' },
      options: ['en', 'fr', 'ar', 'fa'],
      description: 'Locale — Latin digits are enforced regardless of this value (Rule #9)',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes on the root element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof RCIDelta>;

// ---------------------------------------------------------------------------
// Significant — |delta| >= 5.26 → ●●●
// ---------------------------------------------------------------------------

export const Significant: Story = {
  name: 'Significant (delta = -6)',
  args: {
    delta: -6,
  },
  parameters: {
    docs: {
      description: {
        story:
          'delta=-6 → |delta|=6 ≥ 5.26 → significant (●●●). ' +
          'Clinically reliable improvement by Jacobson & Truax (1991) criteria.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Moderate — 2.5 <= |delta| < 5.26 → ●●○
// ---------------------------------------------------------------------------

export const Moderate: Story = {
  name: 'Moderate (delta = -3)',
  args: {
    delta: -3,
  },
  parameters: {
    docs: {
      description: {
        story:
          'delta=-3 → |delta|=3 in [2.5, 5.26) → moderate (●●○). ' +
          'Change is in the right direction but does not yet cross the reliable-change threshold.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// NonSignificant — |delta| < 2.5 → ●○○
// ---------------------------------------------------------------------------

export const NonSignificant: Story = {
  name: 'Non-significant (delta = -1)',
  args: {
    delta: -1,
  },
  parameters: {
    docs: {
      description: {
        story:
          'delta=-1 → |delta|=1 < 2.5 → non-significant (●○○). ' +
          'Change is within measurement error — not clinically reliable.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Improvement — positive delta (score went down = improvement)
// ---------------------------------------------------------------------------

export const Improvement: Story = {
  name: 'Improvement (delta = +6)',
  args: {
    delta: 6,
  },
  parameters: {
    docs: {
      description: {
        story:
          'delta=+6 → positive = improvement (PHQ-9 score decreased by 6 points). ' +
          'Renders as "+6" with text-signal-stable color and ●●● dot scale.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Zero — no change
// ---------------------------------------------------------------------------

export const Zero: Story = {
  name: 'Zero (no change)',
  args: {
    delta: 0,
  },
  parameters: {
    docs: {
      description: {
        story:
          'delta=0 → renders as "0" with text-ink-tertiary color and ●○○ dot scale.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Persian — locale="fa", Latin digits enforced (Rule #9)
// ---------------------------------------------------------------------------

export const Persian: Story = {
  name: 'Persian locale (delta = -3, locale = "fa")',
  args: {
    delta: -3,
    locale: 'fa',
  },
  parameters: {
    docs: {
      description: {
        story:
          'locale="fa" with delta=-3. Despite the Persian locale, the delta renders ' +
          'as Latin "-3" (not "-۳") — Rule #9 enforcement.',
      },
    },
  },
};
