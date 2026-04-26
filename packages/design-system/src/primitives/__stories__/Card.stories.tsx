import type { Meta, StoryObj } from '@storybook/react';
import { Card } from '../Card';

const meta: Meta<typeof Card> = {
  title: 'Design System / Primitives / Card',
  component: Card,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised card surface. Supports four semantic tones, three padding scales, three shadow levels, three element types (div/article/section), and an optional hover-lift interaction. `border-[hsl(220,14%,90%)]` and `bg-white` have been replaced with `border-border-subtle` and `bg-surface-primary` so the component scales correctly across light and dark themes without numeric colour literals.',
      },
    },
  },
  argTypes: {
    as: {
      control: 'select',
      options: ['div', 'article', 'section'],
      description: 'Underlying HTML element',
    },
    padding: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Inner padding scale',
    },
    shadow: {
      control: 'select',
      options: ['none', 'sm', 'md'],
      description: 'Drop-shadow depth',
    },
    tone: {
      control: 'select',
      options: [undefined, 'neutral', 'calm', 'warning', 'crisis'],
      description: 'Semantic colour tone — overrides border and background',
    },
    hover: {
      control: 'boolean',
      description: 'Enables a subtle upward lift on hover (adds cursor-pointer)',
    },
    children: {
      control: 'text',
      description: 'Card content',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Card>;

// ---------------------------------------------------------------------------
// Default
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    padding: 'md',
    shadow: 'sm',
    children: 'A simple card with default settings — neutral border, primary surface background, medium padding, small shadow.',
  },
};

// ---------------------------------------------------------------------------
// Tones
// ---------------------------------------------------------------------------

export const WithTones: Story = {
  name: 'All tones',
  parameters: {
    docs: {
      description: {
        story:
          'Each tone applies a Quiet Strength semantic border and background. `calm` uses `accent-teal-soft`, `warning` uses `signal-warning`, and `crisis` uses `signal-crisis`. The `neutral` tone simply restates the default border token.',
      },
    },
  },
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Card tone="neutral" padding="md">
        <p className="text-sm font-medium mb-1">tone=&ldquo;neutral&rdquo;</p>
        <p className="text-sm text-ink-secondary">Default border, no background shift.</p>
      </Card>
      <Card tone="calm" padding="md">
        <p className="text-sm font-medium mb-1">tone=&ldquo;calm&rdquo;</p>
        <p className="text-sm text-ink-secondary">Teal border + subtle teal background.</p>
      </Card>
      <Card tone="warning" padding="md">
        <p className="text-sm font-medium mb-1">tone=&ldquo;warning&rdquo;</p>
        <p className="text-sm text-ink-secondary">Amber warning border + tinted background.</p>
      </Card>
      <Card tone="crisis" padding="md">
        <p className="text-sm font-medium mb-1">tone=&ldquo;crisis&rdquo;</p>
        <p className="text-sm text-ink-secondary">Crisis border + tinted background. Reserved for T3/T4 escalation surfaces.</p>
      </Card>
    </div>
  ),
};

// ---------------------------------------------------------------------------
// Hoverable
// ---------------------------------------------------------------------------

export const Hoverable: Story = {
  name: 'Hoverable',
  parameters: {
    docs: {
      description: {
        story:
          '`hover=true` adds a `-translate-y-0.5 hover:shadow-md cursor-pointer` lift. Use for clickable card surfaces such as navigation tiles or drill-down rows.',
      },
    },
  },
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Card hover padding="md">
        <p className="text-sm font-medium mb-1">Hoverable card</p>
        <p className="text-sm text-ink-secondary">Lifts on hover — cursor changes to pointer.</p>
      </Card>
      <Card hover tone="calm" padding="md">
        <p className="text-sm font-medium mb-1">Hoverable + calm tone</p>
        <p className="text-sm text-ink-secondary">Tone and hover compose cleanly.</p>
      </Card>
    </div>
  ),
};

// ---------------------------------------------------------------------------
// Padding scale
// ---------------------------------------------------------------------------

export const Paddings: Story = {
  name: 'Padding scale (sm / md / lg)',
  parameters: {
    docs: {
      description: {
        story: 'Three padding steps — `sm` (p-4 / 16 px), `md` (p-5 / 20 px), `lg` (p-6 / 24 px).',
      },
    },
  },
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Card padding="sm" shadow="none">
        <p className="text-sm font-medium">padding=&ldquo;sm&rdquo; — p-4 (16 px)</p>
      </Card>
      <Card padding="md" shadow="none">
        <p className="text-sm font-medium">padding=&ldquo;md&rdquo; — p-5 (20 px)</p>
      </Card>
      <Card padding="lg" shadow="none">
        <p className="text-sm font-medium">padding=&ldquo;lg&rdquo; — p-6 (24 px)</p>
      </Card>
    </div>
  ),
};

// ---------------------------------------------------------------------------
// As sections
// ---------------------------------------------------------------------------

export const AsSections: Story = {
  name: 'Polymorphic element (div / article / section)',
  parameters: {
    docs: {
      description: {
        story:
          'The `as` prop controls the rendered HTML element for correct landmark semantics. Use `article` for self-contained content, `section` for thematic groupings, and the default `div` for generic layout containers.',
      },
    },
  },
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Card as="div" padding="md">
        <p className="text-sm font-medium mb-1">as=&ldquo;div&rdquo; (default)</p>
        <p className="text-sm text-ink-secondary">Generic layout container — no landmark semantics.</p>
      </Card>
      <Card as="article" padding="md">
        <p className="text-sm font-medium mb-1">as=&ldquo;article&rdquo;</p>
        <p className="text-sm text-ink-secondary">Self-contained content block (e.g. a session summary card).</p>
      </Card>
      <Card as="section" padding="md">
        <p className="text-sm font-medium mb-1">as=&ldquo;section&rdquo;</p>
        <p className="text-sm text-ink-secondary">Thematic grouping within a larger page region.</p>
      </Card>
    </div>
  ),
};
