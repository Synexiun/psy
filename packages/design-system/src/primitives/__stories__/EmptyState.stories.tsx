'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { EmptyState } from '../EmptyState';

const meta: Meta<typeof EmptyState> = {
  title: 'Design System / Primitives / EmptyState',
  component: EmptyState,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Centered feedback component for empty lists or screens. ' +
          'Has an optional illustration slot, required headline, optional body text, ' +
          'and an optional primary CTA button (rendered only when both `ctaLabel` and `onCta` are provided). ' +
          'Tokens: `text-ink-primary`, `text-ink-tertiary`, `bg-accent-bronze`, `ease-default`.',
      },
    },
  },
  argTypes: {
    headline: {
      control: 'text',
      description: 'Headline text — required',
    },
    body: {
      control: 'text',
      description: 'Optional supporting body text',
    },
    ctaLabel: {
      control: 'text',
      description: 'Primary CTA label — button only renders when both ctaLabel and onCta are provided',
    },
  },
};

export default meta;
type Story = StoryObj<typeof EmptyState>;

// ---------------------------------------------------------------------------
// 1. Default (no illustration)
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (no illustration)',
  args: {
    headline: 'No check-ins yet',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Minimal render: headline only, no illustration, no body, no CTA.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. WithIllustration (emoji as illustration)
// ---------------------------------------------------------------------------

export const WithIllustration: Story = {
  name: 'With Illustration',
  render: () => (
    <EmptyState
      illustration={<span style={{ fontSize: '3rem' }} aria-hidden="true">🌱</span>}
      headline="No sessions this week"
    />
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Illustration slot accepts any ReactNode — here an emoji wrapper. ' +
          'Rendered inside a `<div className="mb-2">` above the headline.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. WithBody
// ---------------------------------------------------------------------------

export const WithBody: Story = {
  name: 'With Body Text',
  args: {
    headline: 'No check-ins yet',
    body: 'Complete your first check-in to see your progress here.',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Optional `body` prop adds a `<p>` with `max-w-xs text-sm text-ink-tertiary` below the headline.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. WithCta
// ---------------------------------------------------------------------------

export const WithCta: Story = {
  name: 'With CTA Button',
  args: {
    headline: 'No check-ins yet',
    body: 'Complete your first check-in to see your progress here.',
    ctaLabel: 'Start check-in',
    onCta: () => alert('CTA clicked'),
  },
  parameters: {
    docs: {
      description: {
        story:
          'CTA button renders only when both `ctaLabel` and `onCta` are provided. ' +
          'Token: `bg-accent-bronze`. Focus ring: `focus-visible:ring-accent-bronze/30`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 5. Full (all props)
// ---------------------------------------------------------------------------

export const Full: Story = {
  name: 'Full (all props)',
  render: () => (
    <EmptyState
      illustration={<span style={{ fontSize: '3rem' }} aria-hidden="true">📋</span>}
      headline="No sessions this week"
      body="Your session history will appear here once you complete your first check-in."
      ctaLabel="Start now"
      onCta={() => alert('CTA clicked')}
    />
  ),
  parameters: {
    docs: {
      description: {
        story:
          'All props provided: illustration, headline, body, and CTA button.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 6. DarkBackground wrapper
// ---------------------------------------------------------------------------

export const DarkBackground: Story = {
  name: 'Dark Background',
  render: () => (
    <div
      style={{ backgroundColor: '#1a1a2e', borderRadius: '12px', padding: '24px' }}
      className="dark"
    >
      <EmptyState
        illustration={<span style={{ fontSize: '3rem' }} aria-hidden="true">🌙</span>}
        headline="No check-ins yet"
        body="Your progress will appear here once you complete your first check-in."
        ctaLabel="Start check-in"
        onCta={() => alert('CTA clicked')}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'EmptyState on a dark background to verify token contrast in dark mode.',
      },
    },
  },
};
