import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from '../Badge';

const meta: Meta<typeof Badge> = {
  title: 'Design System / Primitives / Badge',
  component: Badge,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised badge. Supports six semantic variants (new API) and five legacy tone values for backward compat. `variant` always wins over `tone` when both are supplied. Sizes: `sm` (default) and `md`.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'danger', 'info', 'neutral'],
      description: 'Semantic colour variant (new API — wins over tone)',
    },
    size: {
      control: 'select',
      options: ['sm', 'md'],
      description: 'Size preset',
    },
    tone: {
      control: 'select',
      options: ['neutral', 'calm', 'warning', 'crisis', 'success'],
      description: 'Legacy tone (backward compat — only active when variant is omitted)',
    },
    children: {
      control: 'text',
      description: 'Badge label',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Badge>;

// ---------------------------------------------------------------------------
// All variants
// ---------------------------------------------------------------------------

export const AllVariants: Story = {
  name: 'All variants',
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Badge variant="default">Default</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="danger">Danger</Badge>
      <Badge variant="info">Info</Badge>
      <Badge variant="neutral">Neutral</Badge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'All six `variant` values using Quiet Strength design tokens. No hardcoded `hsl()` values.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// All tones (legacy backward-compat)
// ---------------------------------------------------------------------------

export const AllTones: Story = {
  name: 'All tones (legacy)',
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Badge tone="neutral">Neutral</Badge>
      <Badge tone="calm">Calm</Badge>
      <Badge tone="warning">Warning</Badge>
      <Badge tone="crisis">Crisis</Badge>
      <Badge tone="success">Success</Badge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Legacy `tone` prop — available for backward compat with pre-variant consumers. When `variant` is also supplied, `variant` wins.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Sizes
// ---------------------------------------------------------------------------

export const Sizes: Story = {
  name: 'Sizes',
  render: () => (
    <div className="flex items-center gap-4">
      <Badge variant="default" size="sm">Small (sm)</Badge>
      <Badge variant="default" size="md">Medium (md)</Badge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '`sm` (default) is `text-xs px-2 py-0.5`; `md` is `text-sm px-2.5 py-1`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// InContext — badges used alongside realistic content
// ---------------------------------------------------------------------------

export const InContext: Story = {
  name: 'In context',
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      {/* Session status row */}
      <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-surface-secondary px-4 py-3">
        <span className="text-sm font-medium text-ink-primary">Morning check-in</span>
        <Badge variant="success" size="sm">Completed</Badge>
      </div>

      {/* Risk indicator row */}
      <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-surface-secondary px-4 py-3">
        <span className="text-sm font-medium text-ink-primary">Urge intensity</span>
        <Badge variant="warning" size="sm">Elevated</Badge>
      </div>

      {/* Crisis escalation row */}
      <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-surface-secondary px-4 py-3">
        <span className="text-sm font-medium text-ink-primary">Safety alert</span>
        <Badge variant="danger" size="sm">Needs attention</Badge>
      </div>

      {/* Info / neutral rows */}
      <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-surface-secondary px-4 py-3">
        <span className="text-sm font-medium text-ink-primary">Session type</span>
        <Badge variant="info" size="sm">Guided</Badge>
      </div>

      {/* Medium size with legacy tone */}
      <div className="flex items-center justify-between rounded-xl border border-border-subtle bg-surface-secondary px-4 py-3">
        <span className="text-sm font-medium text-ink-primary">Streak state</span>
        <Badge tone="calm" size="md">42 days</Badge>
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Realistic usage inside card rows — session status, risk level, crisis escalation, and informational tags. Demonstrates both `variant` and legacy `tone` APIs side-by-side.',
      },
    },
  },
};
