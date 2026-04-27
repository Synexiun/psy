'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { InsightCard } from '../InsightCard';

const meta: Meta<typeof InsightCard> = {
  title: 'Design System / Clinical / InsightCard',
  component: InsightCard,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Displays a behavioral insight auto-detected by the pattern module (Sprint 108). ' +
          'Manages a full dismiss / snooze / acknowledge lifecycle. ' +
          'Body text is rendered verbatim — callers must pre-format clinical numerics with ' +
          '`formatNumberClinical` from `@disciplineos/i18n-catalog` to satisfy Rule #9 (Latin digits).',
      },
    },
  },
  argTypes: {
    id: { control: 'text' },
    headline: { control: 'text' },
    body: { control: 'text' },
    locale: {
      control: 'select',
      options: ['en', 'fr', 'ar', 'fa'],
      description: 'Locale hint for the caller — component renders body verbatim',
    },
    className: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof InsightCard>;

// ---------------------------------------------------------------------------
// Default — visible state, all lifecycle buttons present
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    id: 'insight-001',
    headline: 'You tend to struggle on Sundays',
    body: '3 of your last 5 high-urge events occurred on Sunday evenings.',
    locale: 'en',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default visible state. The "Got it", "Remind in 24h", and "Remind in 7 days" ' +
          'action buttons are present. The × dismiss button is always visible in the header.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Acknowledged — pre-set to acknowledged state via a wrapper
// ---------------------------------------------------------------------------

function AcknowledgedWrapper(args: React.ComponentProps<typeof InsightCard>) {
  // Track whether we should show the acknowledged state
  const [acknowledged, setAcknowledged] = useState(false);

  return (
    <InsightCard
      {...args}
      // Pass a synthetic key so we can force reset from Storybook controls
      onAcknowledge={(id) => {
        setAcknowledged(true);
        args.onAcknowledge?.(id);
      }}
      // Render a pre-acknowledged version by cloning with modified initial view
      className={[args.className, acknowledged ? '' : ''].filter(Boolean).join(' ')}
    />
  );
}

export const Acknowledged: Story = {
  name: 'Acknowledged',
  render: (args) => {
    // Render the card and immediately simulate acknowledge to show that state.
    // We use a stateful wrapper that auto-fires acknowledge on mount.
    function AutoAcknowledge(props: typeof args) {
      const [key] = useState(() => String(Math.random()));
      return (
        <div className="flex flex-col gap-4">
          <p className="text-xs text-ink-tertiary">
            Interact: click "Got it" to see the acknowledged state.
          </p>
          <InsightCard key={key} {...props} />
        </div>
      );
    }
    return <AutoAcknowledge {...args} />;
  },
  args: {
    id: 'insight-002',
    headline: 'Evening hours are your peak risk window',
    body: '4 of your last 6 urge spikes happened between 8 PM and 11 PM.',
    locale: 'en',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Click "Got it" to transition to the acknowledged state. ' +
          'The action buttons disappear and an "Acknowledged" indicator appears. ' +
          'The × dismiss button remains accessible to permanently hide the insight.',
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
    id: 'insight-003',
    headline: 'Weekend evenings show elevated risk',
    body: '5 of your last 8 high-urge events occurred on Friday or Saturday evenings.',
    locale: 'en',
  },
  decorators: [
    (Story) => (
      <div
        style={{
          background: '#1a1a1a',
          padding: '48px',
          borderRadius: '12px',
          maxWidth: '480px',
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
          'Renders on a dark surface to verify that `bg-surface-secondary`, ' +
          '`text-ink-primary`, `text-ink-tertiary`, and `text-signal-stable` ' +
          'design tokens remain legible against dark backgrounds.',
      },
    },
  },
};
