import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { TabNav } from '../TabNav';

const EN_TABS = [
  {
    value: 'overview',
    label: 'Overview',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        Overview panel — summary statistics and recent activity.
      </div>
    ),
  },
  {
    value: 'history',
    label: 'History',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        History panel — past sessions and milestone events.
      </div>
    ),
  },
  {
    value: 'settings',
    label: 'Settings',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        Settings panel — preferences and notification controls.
      </div>
    ),
  },
];

const EN_TABS_WITH_DISABLED = [
  {
    value: 'overview',
    label: 'Overview',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        Overview panel content.
      </div>
    ),
  },
  {
    value: 'history',
    label: 'History (locked)',
    disabled: true,
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        History panel — not accessible while locked.
      </div>
    ),
  },
  {
    value: 'settings',
    label: 'Settings',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        Settings panel content.
      </div>
    ),
  },
];

const AR_TABS = [
  {
    value: 'overview',
    label: 'نظرة عامة',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        لوحة النظرة العامة — إحصاءات ملخصة ونشاط حديث.
      </div>
    ),
  },
  {
    value: 'history',
    label: 'السجل',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        لوحة السجل — الجلسات السابقة وأحداث المعالم.
      </div>
    ),
  },
  {
    value: 'settings',
    label: 'الإعدادات',
    content: (
      <div className="rounded-md bg-surface-secondary p-4 text-sm text-ink-primary">
        لوحة الإعدادات — التفضيلات وضوابط الإشعارات.
      </div>
    ),
  },
];

const meta: Meta<typeof TabNav> = {
  title: 'Design System / Primitives / TabNav',
  component: TabNav,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Radix-based TabNav primitive with Quiet Strength tokens. Supports controlled and uncontrolled modes, disabled tabs, and full RTL via a `dir="rtl"` wrapper and the `dir` prop. The active tab displays a bottom border indicator using `border-accent-bronze`.',
      },
    },
  },
  argTypes: {
    dir: { control: { type: 'radio' }, options: ['ltr', 'rtl'] },
    ariaLabel: { control: 'text' },
    className: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof TabNav>;

export const Default: Story = {
  name: 'Default',
  args: {
    tabs: EN_TABS,
    ariaLabel: 'Dashboard sections',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Three tabs with no explicit `value` or `defaultValue` — the first tab is selected automatically via the `tabs[0].value` fallback.',
      },
    },
  },
};

export const Controlled: Story = {
  name: 'Controlled',
  render: function ControlledStory() {
    const [active, setActive] = React.useState('history');
    return (
      <div className="flex flex-col gap-4">
        <p className="text-sm text-ink-tertiary">
          Active tab: <span className="font-medium text-ink-primary">{active}</span>
        </p>
        <TabNav
          tabs={EN_TABS}
          value={active}
          onValueChange={setActive}
          ariaLabel="Controlled dashboard sections"
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          'Controlled mode: `value` and `onValueChange` are managed externally. The current active tab is echoed above the component.',
      },
    },
  },
};

export const WithDisabledTab: Story = {
  name: 'With disabled tab',
  args: {
    tabs: EN_TABS_WITH_DISABLED,
    ariaLabel: 'Dashboard sections — history locked',
  },
  parameters: {
    docs: {
      description: {
        story:
          'The second tab is disabled — it is visually dimmed and excluded from keyboard focus. The first and third tabs remain fully interactive.',
      },
    },
  },
};

export const RTLContext: Story = {
  name: 'RTL context (ar)',
  render: () => (
    <div dir="rtl" className="w-full">
      <TabNav
        tabs={AR_TABS}
        dir="rtl"
        ariaLabel="أقسام لوحة التحكم"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context the tab list flows right-to-left and arrow-key navigation mirrors automatically (Radix Tabs propagates `dir` to the roving focus handler). Wrap in a `dir="rtl"` element and pass `dir="rtl"` to the component for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
