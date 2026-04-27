import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { PageShell } from '../PageShell';

const meta: Meta<typeof PageShell> = {
  title: 'Design System / Primitives / PageShell',
  component: PageShell,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised page-level layout wrapper. Provides a consistent content column with an optional back-navigation link, an optional subheading, optional heading-row actions, and a body region. PageShell is NOT a full-page layout — TopBar and SidebarNav live outside it. RTL is handled via logical CSS properties and an auto-mirroring back-arrow SVG (`rtl:-scale-x-100`).',
      },
    },
  },
  argTypes: {
    heading: { control: 'text', description: 'Page heading — rendered as <h1>' },
    subheading: { control: 'text', description: 'Optional subheading below the heading' },
    backHref: { control: 'text', description: 'Optional back-navigation href' },
    backLabel: { control: 'text', description: 'Back link label (default: "Back")' },
    className: { control: 'text', description: 'Extra classes on the outermost container' },
  },
};

export default meta;
type Story = StoryObj<typeof PageShell>;

// ---------------------------------------------------------------------------
// Default — heading only + children
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    heading: 'Dashboard',
  },
  render: (args) => (
    <PageShell {...args}>
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
        Page body content goes here — cards, tables, charts, etc.
      </div>
    </PageShell>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Minimal usage: a heading and children. No back link, no subheading, no actions.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// WithBackNav — includes backHref and backLabel
// ---------------------------------------------------------------------------

export const WithBackNav: Story = {
  name: 'With back navigation',
  args: {
    heading: 'Session details',
    subheading: 'Review your urge-surfing session and interventions used.',
    backHref: '/dashboard',
    backLabel: 'Back to dashboard',
  },
  render: (args) => (
    <PageShell {...args}>
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
        Session detail content.
      </div>
    </PageShell>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Back-navigation link above the heading. The chevron-left SVG carries `rtl:-scale-x-100` so it mirrors automatically in Arabic/Persian without a separate icon variant.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// WithActions — includes action buttons in the heading row
// ---------------------------------------------------------------------------

export const WithActions: Story = {
  name: 'With heading actions',
  args: {
    heading: 'Progress report',
    subheading: 'Last 30 days',
  },
  render: (args) => (
    <PageShell
      {...args}
      actions={
        <>
          <button className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-ink-primary hover:bg-surface-secondary">
            Export
          </button>
          <button className="rounded-md bg-accent-bronze px-3 py-1.5 text-sm font-medium text-white hover:opacity-90">
            Share
          </button>
        </>
      }
    >
      <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
        Report charts and metrics.
      </div>
    </PageShell>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Actions are rendered in the heading row, aligned to the end (logical `justify-between`). They shrink-safe — the heading always gets priority.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Full — all props populated
// ---------------------------------------------------------------------------

export const Full: Story = {
  name: 'Full (all props)',
  render: () => (
    <PageShell
      heading="Account settings"
      subheading="Manage your profile, notifications, and privacy options."
      backHref="/dashboard"
      backLabel="Back to dashboard"
      actions={
        <>
          <button className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-ink-primary hover:bg-surface-secondary">
            Cancel
          </button>
          <button className="rounded-md bg-accent-bronze px-3 py-1.5 text-sm font-medium text-white hover:opacity-90">
            Save changes
          </button>
        </>
      }
      className="mx-auto"
    >
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          Profile section — name, avatar, timezone.
        </div>
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          Notifications section — push, email, in-app.
        </div>
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          Privacy section — data export, account deletion.
        </div>
      </div>
    </PageShell>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'All props populated: back link, subheading, heading-row actions, multi-section body, and a custom className.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4-variant theme/locale matrix
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark — en (LTR)',
  render: () => (
    <div data-theme="dark" className="min-h-screen bg-surface-primary p-4">
      <PageShell
        heading="Dashboard"
        subheading="Your progress at a glance."
        backHref="/home"
        backLabel="Back"
        actions={
          <button className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-ink-primary">
            Action
          </button>
        }
      >
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          Body content — dark theme, LTR.
        </div>
      </PageShell>
    </div>
  ),
  parameters: {
    docs: {
      description: { story: 'Dark theme, English (LTR). Back chevron points left.' },
    },
  },
};

export const DarkAr: Story = {
  name: 'Dark — ar (RTL)',
  render: () => (
    <div data-theme="dark" dir="rtl" lang="ar" className="min-h-screen bg-surface-primary p-4">
      <PageShell
        heading="لوحة التحكم"
        subheading="نظرة عامة على تقدمك."
        backHref="/home"
        backLabel="رجوع"
        actions={
          <button className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-ink-primary">
            إجراء
          </button>
        }
      >
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          محتوى الصفحة — الوضع الداكن، RTL.
        </div>
      </PageShell>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Dark theme, Arabic (RTL). The back-arrow SVG mirrors via `rtl:-scale-x-100` so the chevron points right (back direction in RTL).',
      },
    },
  },
};

export const LightEn: Story = {
  name: 'Light — en (LTR)',
  render: () => (
    <div data-theme="light" className="min-h-screen bg-surface-primary p-4">
      <PageShell
        heading="Dashboard"
        subheading="Your progress at a glance."
        backHref="/home"
        backLabel="Back"
        actions={
          <button className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-ink-primary">
            Action
          </button>
        }
      >
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          Body content — light theme, LTR.
        </div>
      </PageShell>
    </div>
  ),
  parameters: {
    docs: {
      description: { story: 'Light theme, English (LTR).' },
    },
  },
};

export const LightAr: Story = {
  name: 'Light — ar (RTL)',
  render: () => (
    <div data-theme="light" dir="rtl" lang="ar" className="min-h-screen bg-surface-primary p-4">
      <PageShell
        heading="لوحة التحكم"
        subheading="نظرة عامة على تقدمك."
        backHref="/home"
        backLabel="رجوع"
        actions={
          <button className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-ink-primary">
            إجراء
          </button>
        }
      >
        <div className="rounded-xl border border-border-subtle bg-surface-secondary p-4 text-sm text-ink-primary">
          محتوى الصفحة — الوضع الفاتح، RTL.
        </div>
      </PageShell>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Light theme, Arabic (RTL). Confirms RTL layout and chevron mirroring in light mode.',
      },
    },
  },
};
