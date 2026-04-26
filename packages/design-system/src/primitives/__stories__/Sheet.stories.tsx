import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Sheet } from '../Sheet';

const meta: Meta<typeof Sheet> = {
  title: 'Design System / Primitives / Sheet',
  component: Sheet,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Sheet (slide-in drawer / side panel) primitive with Quiet Strength tokens. Composes `@radix-ui/react-dialog` so focus-trapping, scroll-lock, ARIA `role="dialog"`, `aria-modal`, `aria-labelledby`, `aria-describedby`, and keyboard Escape dismissal are all handled by the library layer. Supports `left`, `right`, `top`, and `bottom` slide directions with `sm`, `md`, `lg`, and `full` size presets. RTL-aware: `side="right"` uses logical `end-0` positioning so in a `dir="rtl"` context the panel appears from the physical left edge — Radix reads the `dir` attribute from the DOM context automatically.',
      },
    },
  },
  argTypes: {
    side: {
      control: 'select',
      options: ['left', 'right', 'top', 'bottom'],
      description: 'Which edge the panel slides in from',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'full'],
      description: 'Panel width (left/right) or height (top/bottom) preset',
    },
    title: { control: 'text' },
    description: { control: 'text' },
    closeLabel: { control: 'text' },
    className: { control: 'text' },
    open: { control: 'boolean' },
    defaultOpen: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Sheet>;

// ---------------------------------------------------------------------------
// RightSheet — default side=right, uncontrolled trigger
// ---------------------------------------------------------------------------

export const RightSheet: Story = {
  name: 'Right (default)',
  args: {
    side: 'right',
    size: 'md',
    title: 'Session details',
    description: 'Review your current urge-surfing session and available interventions.',
    trigger: (
      <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
        Open right sheet
      </button>
    ),
    children: (
      <div className="flex flex-col gap-4">
        <p className="text-sm text-ink-secondary">
          You are 42 seconds into the urge window. Research shows urges peak and
          subside within 60–180 seconds.
        </p>
        <p className="text-sm text-ink-secondary">
          Focus on the sensation without acting on it. You can ride this out.
        </p>
      </div>
    ),
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default configuration: `side="right"`, `size="md"` (400px wide). The panel slides in from the right edge in LTR. Uses logical `end-0` positioning, so in RTL it appears from the physical left edge.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// LeftSheet — side=left
// ---------------------------------------------------------------------------

export const LeftSheet: Story = {
  name: 'Left',
  args: {
    side: 'left',
    size: 'md',
    title: 'Navigation',
    description: 'Quick access to all platform sections.',
    trigger: (
      <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
        Open left sheet
      </button>
    ),
    children: (
      <nav className="flex flex-col gap-2">
        {['Dashboard', 'Journal', 'Assessments', 'Tools', 'Settings'].map((item) => (
          <a
            key={item}
            href="#"
            className="rounded-md px-3 py-2 text-sm text-ink-secondary hover:bg-surface-secondary hover:text-ink-primary"
          >
            {item}
          </a>
        ))}
      </nav>
    ),
  },
  parameters: {
    docs: {
      description: {
        story:
          '`side="left"`: Panel slides in from the left edge. Uses logical `start-0` positioning and `border-e` (logical end border). In RTL, "start" maps to the right edge.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// BottomSheet — side=bottom, useful for mobile-style patterns
// ---------------------------------------------------------------------------

export const BottomSheet: Story = {
  name: 'Bottom (mobile pattern)',
  args: {
    side: 'bottom',
    size: 'md',
    title: 'Quick actions',
    description: 'Choose an intervention to start now.',
    trigger: (
      <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
        Open bottom sheet
      </button>
    ),
    children: (
      <div className="grid grid-cols-2 gap-3">
        {['Breathing exercise', 'Urge surfing', 'Grounding', 'Call support'].map(
          (action) => (
            <button
              key={action}
              className="rounded-lg border border-border-subtle bg-surface-secondary px-4 py-3 text-sm font-medium text-ink-primary hover:bg-surface-tertiary"
            >
              {action}
            </button>
          ),
        )}
      </div>
    ),
  },
  parameters: {
    docs: {
      description: {
        story:
          '`side="bottom"`: Panel slides up from the bottom edge — common for mobile action-sheet patterns. Height is controlled by the `size` prop (`h-64` for `md`). Uses `inset-x-0` (symmetric) so no directional bias in RTL.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Sizes — sm / md / lg variants side-by-side
// ---------------------------------------------------------------------------

function SizesDemo(): React.ReactElement {
  const sizes = ['sm', 'md', 'lg'] as const;

  return (
    <div className="flex flex-wrap items-center gap-3">
      {sizes.map((size) => (
        <Sheet
          key={size}
          side="right"
          size={size}
          title={`Sheet — ${size}`}
          description={`This is a size="${size}" sheet panel.`}
          trigger={
            <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
              {size.toUpperCase()} sheet
            </button>
          }
        >
          <p className="text-sm text-ink-secondary">
            Width for <code className="font-mono">size="{size}"</code>:{' '}
            {size === 'sm' ? '320px' : size === 'md' ? '400px' : '512px'}.
          </p>
        </Sheet>
      ))}
    </div>
  );
}

export const Sizes: Story = {
  name: 'Sizes (sm / md / lg)',
  render: () => <SizesDemo />,
  parameters: {
    docs: {
      description: {
        story:
          'Three panel widths for `side="right"` (or `left`): `sm` = 320px (`w-80`), `md` = 400px (`w-[400px]`, default), `lg` = 512px (`w-[512px]`). A fourth `full` preset is available for full-width panels.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// RTLContext — dir="rtl" wrapper, Arabic title, side="right" → appears at start (physical left)
// ---------------------------------------------------------------------------

export const RTLContext: Story = {
  name: 'RTL context (ar/fa)',
  render: () => (
    <div dir="rtl">
      <Sheet
        side="right"
        size="md"
        title="تفاصيل الجلسة"
        description="راجع جلسة ركوب الأمواج الحالية والتدخلات المتاحة."
        trigger={
          <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
            افتح الدرج
          </button>
        }
      >
        <p className="text-sm text-ink-secondary">
          أنت في الثانية 42 من نافذة الرغبة الشديدة. ركّز على الإحساس دون
          التصرف حيال ذلك — الرغبات تبلغ ذروتها وتتلاشى.
        </p>
      </Sheet>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context, `side="right"` uses logical `end-0` positioning — "end" in RTL maps to the physical **left** edge, so the panel slides in from the left. The title, description, and body all mirror via logical CSS properties. All internal layout uses `gap-*`, `ps-*`/`pe-*` (via `p-6` symmetric padding), and logical flex — no physical `ml-*/mr-*/pl-*/pr-*` present. Wrap the Sheet in a `dir="rtl"` element for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
