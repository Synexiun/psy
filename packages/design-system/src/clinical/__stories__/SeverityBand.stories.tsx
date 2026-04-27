'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { SeverityBand } from '../SeverityBand';

const meta: Meta<typeof SeverityBand> = {
  title: 'Design System / Clinical / SeverityBand',
  component: SeverityBand,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Displays the PHQ-9 severity band for a given score. Thresholds are pinned from Kroenke, Spitzer, Williams (2001). Score always renders in Latin digits regardless of locale (Rule #9).',
      },
    },
  },
  argTypes: {
    score: {
      control: { type: 'range', min: 0, max: 27, step: 1 },
      description: 'PHQ-9 total score (0–27)',
    },
    locale: {
      control: 'text',
      description: 'Locale code — does not affect score digit rendering (always Latin)',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes on the root element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof SeverityBand>;

export const Minimal: Story = {
  name: 'Minimal (score=2)',
  args: { score: 2 },
  parameters: {
    docs: {
      description: { story: 'Score 2 → "Minimal" band (0–4, Kroenke 2001).' },
    },
  },
};

export const Mild: Story = {
  name: 'Mild (score=7)',
  args: { score: 7 },
  parameters: {
    docs: {
      description: { story: 'Score 7 → "Mild" band (5–9, Kroenke 2001).' },
    },
  },
};

export const Moderate: Story = {
  name: 'Moderate (score=12)',
  args: { score: 12 },
  parameters: {
    docs: {
      description: { story: 'Score 12 → "Moderate" band (10–14, Kroenke 2001).' },
    },
  },
};

export const Severe: Story = {
  name: 'Severe (score=17)',
  args: { score: 17 },
  parameters: {
    docs: {
      description: { story: 'Score 17 → "Severe" band (15–19, Kroenke 2001 "Moderately severe").' },
    },
  },
};

export const Extreme: Story = {
  name: 'Extreme (score=23)',
  args: { score: 23 },
  parameters: {
    docs: {
      description: { story: 'Score 23 → "Extreme" band (20–27, Kroenke 2001 "Severe").' },
    },
  },
};

export const Persian: Story = {
  name: 'Persian locale (score=15)',
  args: { score: 15, locale: 'fa' },
  parameters: {
    docs: {
      description: {
        story:
          'Rule #9 verification: score renders as "15" (Latin digits) even under the Persian locale. Arabic-Indic "۱۵" must not appear.',
      },
    },
  },
};
