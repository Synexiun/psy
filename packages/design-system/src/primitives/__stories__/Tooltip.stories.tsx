import type { Meta, StoryObj } from '@storybook/react';
import { Tooltip } from '../Tooltip';

const meta: Meta<typeof Tooltip> = {
  title: 'Design System / Primitives / Tooltip',
  component: Tooltip,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Tooltip primitive. Wraps `@radix-ui/react-tooltip` so ARIA `role="tooltip"`, keyboard focus, and RTL-safe side-offset placement are all handled by the library layer. API is unchanged from the previous CSS-only implementation — `tooltipContent`, `side`, `className`, and `children` are the full prop surface.',
      },
    },
  },
  argTypes: {
    side: {
      control: 'select',
      options: ['top', 'bottom', 'left', 'right'],
      description: 'Which side of the trigger the tooltip appears on',
    },
    tooltipContent: {
      control: 'text',
      description: 'Content rendered inside the tooltip panel',
    },
    className: {
      control: 'text',
      description: 'Additional class applied to the trigger wrapper',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Tooltip>;

// ---------------------------------------------------------------------------
// All four sides
// ---------------------------------------------------------------------------

export const TopSide: Story = {
  name: 'Top (default)',
  args: {
    side: 'top',
    tooltipContent: 'This tooltip appears above',
    children: <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">Hover me</button>,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`side="top"` (the default). Radix positions the panel above the trigger with a `sideOffset` of 6 px.',
      },
    },
  },
};

export const BottomSide: Story = {
  name: 'Bottom',
  args: {
    side: 'bottom',
    tooltipContent: 'This tooltip appears below',
    children: <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">Hover me</button>,
  },
};

export const LeftSide: Story = {
  name: 'Left',
  args: {
    side: 'left',
    tooltipContent: 'This tooltip appears to the left',
    children: <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">Hover me</button>,
  },
};

export const RightSide: Story = {
  name: 'Right',
  args: {
    side: 'right',
    tooltipContent: 'This tooltip appears to the right',
    children: <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">Hover me</button>,
  },
};

// ---------------------------------------------------------------------------
// RTL context (required per spec — ar/fa locales)
// ---------------------------------------------------------------------------

export const RTLContext: Story = {
  name: 'RTL context (ar/fa)',
  render: () => (
    <div dir="rtl" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', justifyContent: 'center' }}>
      <Tooltip side="top" tooltipContent="تولتيپ بالا">
        <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">بالا</button>
      </Tooltip>
      <Tooltip side="bottom" tooltipContent="تولتيپ پایین">
        <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">پایین</button>
      </Tooltip>
      <Tooltip side="left" tooltipContent="تولتيپ چپ">
        <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">چپ</button>
      </Tooltip>
      <Tooltip side="right" tooltipContent="تولتيپ راست">
        <button className="rounded-md bg-surface-secondary px-3 py-1.5 text-sm text-ink-primary">راست</button>
      </Tooltip>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'All four sides in a `dir="rtl"` wrapper (Persian/Arabic locales). Radix's popper layer automatically accounts for RTL directionality — no manual left/right swap is required at the component level.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Rich content
// ---------------------------------------------------------------------------

export const RichContent: Story = {
  name: 'Rich content',
  args: {
    side: 'top',
    tooltipContent: (
      <span>
        <strong>PHQ-9 score</strong>: 14 — Moderate depression
      </span>
    ),
    children: <button className="rounded-md bg-accent-bronze px-3 py-1.5 text-sm text-white">View score</button>,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`tooltipContent` accepts any `React.ReactNode` — useful for clinical score labels that combine bold tokens and plain text.',
      },
    },
  },
};
