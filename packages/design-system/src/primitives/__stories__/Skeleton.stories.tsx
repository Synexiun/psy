import type { Meta, StoryObj } from '@storybook/react';
import { Skeleton } from '../Skeleton';

const meta: Meta<typeof Skeleton> = {
  title: 'Design System / Primitives / Skeleton',
  component: Skeleton,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised skeleton loading placeholder. Three variant shapes — `text` (rounded-md), `circle` (rounded-full), and `rect` (rounded-lg) — cover the common content structures in the dashboard, profile, and list surfaces. The `animate-pulse` animation is automatically suppressed for users who prefer reduced motion via the global `@media (prefers-reduced-motion: reduce)` rule in globals.css. Token used: `bg-surface-tertiary` (maps to the Quiet Strength surface palette; was `bg-surface-200` before retokenisation).',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['text', 'circle', 'rect'],
      description: 'Shape variant — controls the border-radius and, for circle, constrains width to height',
    },
    width: {
      control: 'text',
      description: 'CSS width value (any valid CSS length). Ignored for variant="circle" — width is forced to match height.',
    },
    height: {
      control: 'text',
      description: 'CSS height value (any valid CSS length). For variant="circle" this also becomes the width.',
    },
    className: {
      control: 'text',
      description: 'Additional Tailwind utility classes appended to the element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Skeleton>;

// ---------------------------------------------------------------------------
// Variants
// ---------------------------------------------------------------------------

export const Text: Story = {
  name: 'Text (rounded-md)',
  args: {
    variant: 'text',
    width: '240px',
    height: '1rem',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Inline text placeholder. Use for body copy, labels, and single-line fields. Width is typically set to a fraction of the container width to suggest variable-length text.',
      },
    },
  },
};

export const Circle: Story = {
  name: 'Circle (rounded-full)',
  args: {
    variant: 'circle',
    height: '48px',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Circular placeholder for avatars and icon containers. `width` is always forced to equal `height` so the shape stays perfectly circular regardless of the `width` prop.',
      },
    },
  },
};

export const Rect: Story = {
  name: 'Rect (rounded-lg)',
  args: {
    variant: 'rect',
    width: '320px',
    height: '120px',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Rectangular card/image placeholder. Use for card thumbnails, chart areas, and media containers. Default variant when `variant` is omitted.',
      },
    },
  },
};

export const CustomDimensions: Story = {
  name: 'Custom dimensions',
  args: {
    variant: 'rect',
    width: '100%',
    height: '200px',
  },
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Width accepts any valid CSS length — percentages, rems, pixels. Use `width="100%"` (the default) to fill the parent container.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// InList — composite skeleton to simulate a dashboard content row
// ---------------------------------------------------------------------------

export const InList: Story = {
  name: 'In list — dashboard row simulation',
  render: () => (
    <div className="flex flex-col gap-4" style={{ width: '360px' }}>
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton variant="circle" height="40px" />
          <div className="flex flex-col gap-1.5 flex-1">
            <Skeleton variant="text" width="60%" height="0.875rem" />
            <Skeleton variant="text" width="40%" height="0.75rem" />
          </div>
        </div>
      ))}
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Composite skeleton simulating a dashboard list row with an avatar, a primary text line, and a secondary text line. Demonstrates composing the three variants together. Each skeleton element carries `aria-hidden="true"` so screen readers skip the placeholder entirely and wait for real content.',
      },
    },
  },
};
