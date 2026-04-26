import type { Meta, StoryObj } from '@storybook/react';
import { Spinner } from '../Spinner';

const meta: Meta<typeof Spinner> = {
  title: 'Design System / Primitives / Spinner',
  component: Spinner,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'SVG loading indicator. Uses `currentColor` for the stroke so it inherits the surrounding text colour with no additional props. Three sizes match common touch-target contexts: sm (16 px) for inline use, md (24 px) for button/card loading states, lg (32 px) for page-level transitions. The quarter-arc geometry (radius, dash, gap) is a regression-guarded contract — see `Spinner.test.tsx`. Animation is automatically suppressed for users who prefer reduced motion via the global `prefers-reduced-motion` rule.',
      },
    },
  },
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size preset (sm = 16 px, md = 24 px, lg = 32 px)',
    },
    label: {
      control: 'text',
      description: 'Accessible label surfaced as aria-label on the svg element (default: "Loading")',
    },
    className: {
      control: 'text',
      description: 'Additional Tailwind classes — typically a text-colour utility to drive currentColor',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Spinner>;

// ---------------------------------------------------------------------------
// Sizes
// ---------------------------------------------------------------------------

export const Small: Story = {
  name: 'Small (16 px)',
  args: {
    size: 'sm',
    label: 'Loading',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Inline use — fits inside button labels, table cells, or compact list items without disrupting line height.',
      },
    },
  },
};

export const Medium: Story = {
  name: 'Medium (24 px)',
  args: {
    size: 'md',
    label: 'Loading',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default size. Suitable for card loading states, modal bodies, and most standalone loading indicators.',
      },
    },
  },
};

export const Large: Story = {
  name: 'Large (32 px)',
  args: {
    size: 'lg',
    label: 'Loading',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Page-level or section-level loading state — e.g., while the dashboard fetches initial data.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Custom label
// ---------------------------------------------------------------------------

export const CustomLabel: Story = {
  name: 'Custom aria-label',
  args: {
    size: 'md',
    label: 'Saving your progress',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Pass a descriptive `label` prop to override the default "Loading" aria-label. Screen readers will announce this string when the spinner mounts.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// All sizes at a glance
// ---------------------------------------------------------------------------

export const AllSizes: Story = {
  name: 'All sizes',
  render: () => (
    <div className="flex items-center gap-6">
      <div className="flex flex-col items-center gap-1">
        <Spinner size="sm" label="Loading small" />
        <span className="text-xs text-ink-secondary">sm · 16 px</span>
      </div>
      <div className="flex flex-col items-center gap-1">
        <Spinner size="md" label="Loading medium" />
        <span className="text-xs text-ink-secondary">md · 24 px</span>
      </div>
      <div className="flex flex-col items-center gap-1">
        <Spinner size="lg" label="Loading large" />
        <span className="text-xs text-ink-secondary">lg · 32 px</span>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All three sizes side-by-side for visual regression comparison.',
      },
    },
  },
};
