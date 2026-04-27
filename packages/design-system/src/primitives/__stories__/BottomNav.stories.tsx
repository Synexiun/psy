'use client';
import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { BottomNav } from '../BottomNav';
import type { BottomNavItem } from '../BottomNav';

// ---------------------------------------------------------------------------
// Inline SVG placeholder icons
// The real icons come from the app layer; these shapes stand in for Storybook.
// ---------------------------------------------------------------------------

function HomeIcon(): React.ReactElement {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <path
        d="M3 9.5L11 3l8 6.5V19a1 1 0 01-1 1H14v-5h-4v5H4a1 1 0 01-1-1V9.5z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CheckInIcon(): React.ReactElement {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M7.5 11l2.5 2.5 4.5-4.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ToolsIcon(): React.ReactElement {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <path
        d="M14 2a5 5 0 00-4.9 6L3 14l-.5 5.5 5.5-.5 6-6.1A5 5 0 1014 2z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function JournalIcon(): React.ReactElement {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <rect x="4" y="3" width="14" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M8 7h6M8 11h6M8 15h4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CrisisIcon(): React.ReactElement {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <path
        d="M11 2L2 19h18L11 2z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M11 9v4M11 15v1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Item sets
// ---------------------------------------------------------------------------

const ITEMS_WITHOUT_CRISIS: BottomNavItem[] = [
  { value: 'home', label: 'Home', icon: <HomeIcon /> },
  { value: 'checkin', label: 'Check-in', icon: <CheckInIcon /> },
  { value: 'tools', label: 'Tools', icon: <ToolsIcon /> },
  { value: 'journal', label: 'Journal', icon: <JournalIcon /> },
];

const ITEMS_WITH_CRISIS: BottomNavItem[] = [
  { value: 'home', label: 'Home', icon: <HomeIcon /> },
  { value: 'checkin', label: 'Check-in', icon: <CheckInIcon /> },
  { value: 'tools', label: 'Tools', icon: <ToolsIcon /> },
  { value: 'journal', label: 'Journal', icon: <JournalIcon /> },
  { value: 'crisis', label: 'Crisis', icon: <CrisisIcon />, crisis: true },
];

const ITEMS_AR: BottomNavItem[] = [
  { value: 'home', label: 'الرئيسية', icon: <HomeIcon /> },
  { value: 'checkin', label: 'تسجيل الدخول', icon: <CheckInIcon /> },
  { value: 'tools', label: 'الأدوات', icon: <ToolsIcon /> },
  { value: 'journal', label: 'اليوميات', icon: <JournalIcon /> },
  { value: 'crisis', label: 'أزمة', icon: <CrisisIcon />, crisis: true },
];

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------

const meta: Meta<typeof BottomNav> = {
  title: 'Design System / Primitives / BottomNav',
  component: BottomNav,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'Mobile bottom navigation bar. Pure layout primitive — no routing, all navigation via callbacks. Cognitive max: 5 items for reliable thumb-reach. The crisis item (always last per spec §5.3) renders with oxblood (#8B0000) styling, a 56 px minimum touch target, and is never disabled regardless of item.disabled. RTL: flexbox reverses automatically on `dir="rtl"`. Logical CSS throughout (`inset-x-0`, no physical `pl-`/`pr-`).',
      },
    },
  },
  argTypes: {
    activeValue: {
      control: 'select',
      options: ['home', 'checkin', 'tools', 'journal', 'crisis'],
      description: 'Currently active item value',
    },
    className: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof BottomNav>;

// ---------------------------------------------------------------------------
// 1. Default — 5 items, second item active
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    items: ITEMS_WITHOUT_CRISIS,
    activeValue: 'checkin',
    onItemClick: (value) => console.log('nav →', value),
  },
  parameters: {
    docs: {
      description: {
        story:
          'Four items without a crisis tab. Second item (Check-in) is active — shows the bronze dot above the icon and bronze text. Click any item to fire `onItemClick`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. WithCrisis — includes crisis item (always last per spec)
// ---------------------------------------------------------------------------

export const WithCrisis: Story = {
  name: 'With crisis item',
  args: {
    items: ITEMS_WITH_CRISIS,
    activeValue: 'home',
    onItemClick: (value) => console.log('nav →', value),
  },
  parameters: {
    docs: {
      description: {
        story:
          'All five items including the crisis tab (always last). Crisis renders in oxblood (#8B0000) with a 56 px minimum touch target. It can never be disabled. Home is active.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3–6. 4-variant matrix: DarkEn, DarkAr, LightEn, LightAr
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark × EN',
  render: () => (
    <div data-theme="dark" style={{ background: 'var(--color-surface-primary, #0f1117)', minHeight: '120px' }}>
      <BottomNav
        items={ITEMS_WITH_CRISIS}
        activeValue="tools"
        onItemClick={(v) => console.log('nav →', v)}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dark theme, English locale (LTR). Tools is active. Crisis tab is in oxblood.',
      },
    },
  },
};

export const DarkAr: Story = {
  name: 'Dark × AR',
  render: () => (
    <div
      data-theme="dark"
      dir="rtl"
      lang="ar"
      style={{ background: 'var(--color-surface-primary, #0f1117)', minHeight: '120px' }}
    >
      <BottomNav
        items={ITEMS_AR}
        activeValue="home"
        onItemClick={(v) => console.log('nav →', v)}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Dark theme, Arabic locale (`dir="rtl"`, `lang="ar"`). Flexbox reverses item order automatically — crisis tab appears at the physical left. Logical CSS keeps the bar symmetric.',
      },
    },
  },
};

export const LightEn: Story = {
  name: 'Light × EN',
  render: () => (
    <div data-theme="light" style={{ minHeight: '120px' }}>
      <BottomNav
        items={ITEMS_WITH_CRISIS}
        activeValue="journal"
        onItemClick={(v) => console.log('nav →', v)}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Light theme, English locale (LTR). Journal is active. Crisis tab is in oxblood.',
      },
    },
  },
};

export const LightAr: Story = {
  name: 'Light × AR',
  render: () => (
    <div data-theme="light" dir="rtl" lang="ar" style={{ minHeight: '120px' }}>
      <BottomNav
        items={ITEMS_AR}
        activeValue="crisis"
        onItemClick={(v) => console.log('nav →', v)}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Light theme, Arabic locale (`dir="rtl"`, `lang="ar"`). Crisis tab is active — oxblood dot visible. Items flow right-to-left.',
      },
    },
  },
};
