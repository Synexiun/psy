import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { ToastProvider, useToast } from '../Toast';
import type { ToastVariant } from '../Toast';

// Meta uses ToastProvider as the component for argTypes/docs anchoring
const meta: Meta<typeof ToastProvider> = {
  title: 'Design System / Primitives / Toast',
  component: ToastProvider,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Toast notification primitive with Quiet Strength tokens. ' +
          'Manages state via `ToastContext` — wrap your app (or story) in `<ToastProvider>` ' +
          'and call `useToast().toast()` to fire notifications. ' +
          'Viewport positioning uses logical CSS (`start-*`/`end-*`) so placement flips ' +
          'correctly in RTL contexts. Supports four variants: `default`, `success`, `warning`, `error`.',
      },
    },
  },
  argTypes: {
    position: {
      control: 'select',
      options: ['top-right', 'top-left', 'bottom-right', 'bottom-left'],
      description: 'Corner position for the viewport (flips in RTL)',
    },
    maxToasts: {
      control: 'number',
      description: 'Max toasts visible at once (default: 5)',
    },
  },
};

export default meta;
type Story = StoryObj<typeof ToastProvider>;

// ---------------------------------------------------------------------------
// Trigger component shared across stories
// ---------------------------------------------------------------------------

function ToastTrigger({
  label = 'Show toast',
  variant = 'default',
  title = 'Notification',
  description,
  action,
}: {
  label?: string;
  variant?: ToastVariant;
  title?: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}) {
  const { toast } = useToast();
  return (
    <button
      onClick={() => toast({ title, variant, ...(description !== undefined && { description }), ...(action !== undefined && { action }) })}
      className="rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-tertiary"
    >
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// 1. Default — bottom-right, default variant
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (bottom-right)',
  render: () => (
    <ToastProvider position="bottom-right">
      <ToastTrigger
        label="Show default toast"
        variant="default"
        title="Session saved"
        description="Your urge-surfing session has been recorded."
      />
    </ToastProvider>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Default configuration: `position="bottom-right"`, `variant="default"`. ' +
          'Click the button to fire a toast. The viewport uses logical `end-4 bottom-4` positioning.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. AllVariants — one of each variant rendered open in a column
// ---------------------------------------------------------------------------

function AllVariantsDemo(): React.ReactElement {
  return (
    <ToastProvider position="bottom-right">
      <div className="flex flex-col items-start gap-3">
        <ToastTrigger label="Default" variant="default" title="Default notification" description="Something happened." />
        <ToastTrigger label="Success" variant="success" title="Goal reached" description="You completed your daily check-in." />
        <ToastTrigger label="Warning" variant="warning" title="Streak at risk" description="Log an entry to keep your streak active." />
        <ToastTrigger label="Error" variant="error" title="Sync failed" description="Unable to save — check your connection." />
      </div>
    </ToastProvider>
  );
}

export const AllVariants: Story = {
  name: 'All variants',
  render: () => <AllVariantsDemo />,
  parameters: {
    docs: {
      description: {
        story:
          'One button per variant. Click each to see the corresponding border colour: ' +
          '`default` → `border-border-subtle`, ' +
          '`success` → `border-accent-bronze`, ' +
          '`warning` → `border-yellow-500/60`, ' +
          '`error` → `border-red-600/60`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. WithAction — toast with an action button
// ---------------------------------------------------------------------------

export const WithAction: Story = {
  name: 'With action button',
  render: () => (
    <ToastProvider position="bottom-right">
      <ToastTrigger
        label="Show with action"
        variant="default"
        title="Entry deleted"
        description="Your journal entry was removed."
        action={{ label: 'Undo', onClick: () => { /* no-op in story */ } }}
      />
    </ToastProvider>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Toast with an inline action button. The `action.altText` is passed to Radix for ' +
          'accessibility — screen readers announce it as the action description.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4 & 5. Theme × locale matrix — DarkEn, DarkAr, LightEn, LightAr
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark × EN',
  render: () => (
    <div data-theme="dark" style={{ padding: '2rem', minWidth: '360px', position: 'relative' }}>
      <ToastProvider position="bottom-right">
        <ToastTrigger
          label="Show (dark, EN)"
          variant="success"
          title="Session complete"
          description="Well done — stay strong."
        />
      </ToastProvider>
    </div>
  ),
  parameters: {
    docs: {
      description: { story: 'Dark theme, English locale. Success variant with description.' },
    },
  },
};

export const DarkAr: Story = {
  name: 'Dark × AR',
  render: () => (
    <div data-theme="dark" dir="rtl" lang="ar" style={{ padding: '2rem', minWidth: '360px', position: 'relative' }}>
      <ToastProvider position="bottom-right">
        <ToastTrigger
          label="إظهار الإشعار"
          variant="success"
          title="تم حفظ الجلسة"
          description="عمل رائع — استمر في القوة."
        />
      </ToastProvider>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Dark theme, Arabic locale (`dir="rtl"`, `lang="ar"`). ' +
          'Viewport `end-4` maps to the physical left edge in RTL — toast appears at bottom-left.',
      },
    },
  },
};

export const LightEn: Story = {
  name: 'Light × EN',
  render: () => (
    <div data-theme="light" style={{ padding: '2rem', minWidth: '360px', position: 'relative' }}>
      <ToastProvider position="bottom-right">
        <ToastTrigger
          label="Show (light, EN)"
          variant="default"
          title="Check-in recorded"
          description="Your daily mood check-in was saved."
        />
      </ToastProvider>
    </div>
  ),
  parameters: {
    docs: {
      description: { story: 'Light theme, English locale. Default variant.' },
    },
  },
};

export const LightAr: Story = {
  name: 'Light × AR',
  render: () => (
    <div data-theme="light" dir="rtl" lang="ar" style={{ padding: '2rem', minWidth: '360px', position: 'relative' }}>
      <ToastProvider position="bottom-right">
        <ToastTrigger
          label="إظهار الإشعار"
          variant="default"
          title="تم التسجيل"
          description="تم حفظ تسجيل المزاج اليومي."
        />
      </ToastProvider>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Light theme, Arabic locale. Verify border and surface tokens adapt to the light palette ' +
          'and that logical `end-4` places the viewport at the physical left edge.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 6. RTL story — bottom-right toast appears at bottom-left in RTL
// ---------------------------------------------------------------------------

export const RTLContext: Story = {
  name: 'RTL context (ar/fa)',
  render: () => (
    <div dir="rtl" style={{ padding: '2rem', minWidth: '360px', position: 'relative' }}>
      <ToastProvider position="bottom-right">
        <div className="flex flex-col items-start gap-3">
          <p className="text-sm text-ink-secondary">
            position=&quot;bottom-right&quot; — در RTL در گوشه پایین-چپ ظاهر می‌شود
          </p>
          <ToastTrigger
            label="نمایش اعلان"
            variant="success"
            title="جلسه ذخیره شد"
            description="آفرین — قوی بمانید."
          />
        </div>
      </ToastProvider>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context, `position="bottom-right"` uses logical `end-4 bottom-4`. ' +
          '"end" in RTL maps to the physical LEFT edge — so the toast appears in the bottom-left corner. ' +
          'This is the correct "corner flip" behaviour per spec.',
      },
    },
  },
};
