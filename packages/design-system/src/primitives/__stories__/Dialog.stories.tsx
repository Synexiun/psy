import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Dialog } from '../Dialog';

const meta: Meta<typeof Dialog> = {
  title: 'Design System / Primitives / Dialog',
  component: Dialog,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Dialog (modal) primitive with Quiet Strength tokens. Composes `@radix-ui/react-dialog` so focus-trapping, scroll-lock, ARIA `role="dialog"`, `aria-modal`, `aria-labelledby`, `aria-describedby`, and keyboard Escape dismissal are all handled by the library layer. Supports both uncontrolled (trigger prop) and controlled (open + onOpenChange) modes. RTL-safe: the panel is viewport-centered via physical `left-1/2 top-1/2` (intentional exception to the logical-properties rule), while all internal layout uses logical properties exclusively.',
      },
    },
  },
  argTypes: {
    title: { control: 'text' },
    description: { control: 'text' },
    className: { control: 'text' },
    open: { control: 'boolean' },
    defaultOpen: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Dialog>;

// ---------------------------------------------------------------------------
// Default — uncontrolled, trigger button opens the dialog
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    title: 'Take a breath',
    description:
      'This short exercise will guide you through a 60-second urge-surfing technique.',
    trigger: (
      <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
        Open dialog
      </button>
    ),
    children: (
      <p className="text-sm text-ink-secondary">
        Focus on the sensation without acting on it. Urges peak and fade — you
        can ride this out.
      </p>
    ),
  },
  parameters: {
    docs: {
      description: {
        story:
          'Uncontrolled mode: pass a `trigger` prop and Radix manages the open/close state internally. Escape key and the close button both dismiss the dialog.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// NoDescription — optional description omitted
// ---------------------------------------------------------------------------

export const NoDescription: Story = {
  name: 'No description',
  args: {
    title: 'Confirm action',
    trigger: (
      <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
        Open dialog
      </button>
    ),
    children: (
      <div className="flex justify-end gap-3 pt-2">
        <button className="rounded-md border border-border-subtle px-4 py-2 text-sm text-ink-secondary hover:bg-surface-secondary">
          Cancel
        </button>
        <button className="rounded-md bg-accent-bronze px-4 py-2 text-sm font-medium text-white hover:opacity-90">
          Confirm
        </button>
      </div>
    ),
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `description` is omitted the `RadixDialog.Description` element is not rendered — no empty `aria-describedby` is emitted. Use this for simple confirmation dialogs where the title is self-explanatory.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Controlled — open state managed externally
// ---------------------------------------------------------------------------

function ControlledDialogDemo(): React.ReactElement {
  const [open, setOpen] = React.useState(false);

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary"
        onClick={() => setOpen(true)}
      >
        Open controlled dialog
      </button>
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title="Controlled dialog"
        description="This dialog's open state is managed by external React state."
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-ink-secondary">
            Use controlled mode when you need to programmatically open or close
            the dialog from outside a trigger element — for example, after an
            async action completes.
          </p>
          <div className="flex justify-end">
            <button
              className="rounded-md bg-accent-bronze px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              onClick={() => setOpen(false)}
            >
              Got it
            </button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

export const Controlled: Story = {
  name: 'Controlled',
  render: () => <ControlledDialogDemo />,
  parameters: {
    docs: {
      description: {
        story:
          'Controlled mode: `open` and `onOpenChange` are wired to external React state. No `trigger` prop is needed — the dialog is opened programmatically. The close button and Escape key call `onOpenChange(false)`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// RTLContext — dir="rtl" wrapper, Arabic title and description
// ---------------------------------------------------------------------------

export const RTLContext: Story = {
  name: 'RTL context (ar/fa)',
  render: () => (
    <div dir="rtl">
      <Dialog
        title="خذ نفسًا عميقًا"
        description="ستُرشدك هذه التقنية خلال 60 ثانية من تمرين ركوب الموجة."
        trigger={
          <button className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary">
            افتح الحوار
          </button>
        }
      >
        <p className="text-sm text-ink-secondary">
          ركّز على الإحساس دون التصرف حيال ذلك. الرغبات تبلغ ذروتها وتتلاشى —
          يمكنك تجاوز هذا.
        </p>
      </Dialog>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context the title/close button row, description, and body all mirror correctly via logical CSS properties. The panel itself remains viewport-centered via physical `left-1/2 top-1/2` — this is an intentional exception to the logical-properties rule because dialog centering is positional (viewport-relative), not directional. Wrap the Dialog in a `dir="rtl"` element for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
