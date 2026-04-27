'use client';
import type { Meta, StoryObj } from '@storybook/react';
import { useEffect } from 'react';
import { BreathingPulse } from '../BreathingPulse';

const meta: Meta<typeof BreathingPulse> = {
  title: 'Design System / Clinical / BreathingPulse',
  component: BreathingPulse,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Clinical breathing-exercise guide used in T3/T4 intervention flows. A pulsing circle animates through a 4s inhale / 4s exhale cycle (8s total). Phase durations are contract-locked at 4 000 ms each via `data-inhale-ms` and `data-exhale-ms` attributes. Respects `prefers-reduced-motion`.',
      },
    },
  },
  argTypes: {
    size: {
      control: { type: 'range', min: 60, max: 300, step: 10 },
      description: 'Circle diameter in px (default: 120)',
    },
    ariaLabel: {
      control: 'text',
      description: 'Accessible label for role="img" wrapper (default: "Breathing guide")',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes on the root element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof BreathingPulse>;

// ---------------------------------------------------------------------------
// Default — 120px animated
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    size: 120,
    ariaLabel: 'Breathing guide',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default 120px animated circle. Inhale (0→50%) expands the circle to `scale(1.3)` over 4s; exhale (50→100%) contracts back to `scale(1)` over 4s.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// ReducedMotion — mock matchMedia to simulate prefers-reduced-motion: reduce
// ---------------------------------------------------------------------------

function ReducedMotionWrapper(args: React.ComponentProps<typeof BreathingPulse>) {
  useEffect(() => {
    const original = window.matchMedia;
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: (query: string) => ({
        matches: query.includes('reduce'),
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }),
    });
    return () => {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        configurable: true,
        value: original,
      });
    };
  }, []);

  return <BreathingPulse {...args} />;
}

export const ReducedMotion: Story = {
  name: 'Reduced Motion',
  render: (args) => <ReducedMotionWrapper {...args} />,
  args: {
    size: 120,
    ariaLabel: 'Breathing guide (static)',
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `prefers-reduced-motion: reduce` is detected the animation is suppressed. A static "Breathe" text label is shown inside the circle instead. The `data-inhale-ms` and `data-exhale-ms` contract attributes are still present on the DOM element.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Large — size=200
// ---------------------------------------------------------------------------

export const Large: Story = {
  name: 'Large',
  args: {
    size: 200,
    ariaLabel: 'Breathing guide (large)',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Larger 200px variant. The inner dot scales proportionally. Useful for full-screen intervention flows where the circle is the primary focus element.',
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
    size: 120,
    ariaLabel: 'Breathing guide',
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
          'Renders on a dark surface to verify that `accent-bronze/20` fill and `accent-bronze/40` ring remain legible against dark backgrounds.',
      },
    },
  },
};
