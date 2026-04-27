import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { TopBar } from '../TopBar';
import type { LocaleOption } from '../TopBar';

const LOCALE_OPTIONS: LocaleOption[] = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'Français' },
  { value: 'ar', label: 'العربية' },
  { value: 'fa', label: 'فارسی' },
];

function WordmarkDemo(): React.ReactElement {
  return (
    <span className="text-base font-semibold tracking-tight text-ink-primary">
      Discipline OS
    </span>
  );
}

function AvatarDemo(): React.ReactElement {
  return (
    <span
      aria-label="User: J D"
      className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-bronze text-sm font-semibold text-surface-primary"
    >
      JD
    </span>
  );
}

const meta: Meta<typeof TopBar> = {
  title: 'Design System / Primitives / TopBar',
  component: TopBar,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'Top navigation bar primitive. Pure layout — all interactivity is via callbacks; no internal routing or theme management. RTL-aware: uses logical CSS properties throughout (`ps-*`/`pe-*`/`start-*`/`end-*`). Mobile wordmark centering corrected for both LTR and RTL with `start-1/2 -translate-x-1/2 rtl:translate-x-1/2`. No Radix dependency.',
      },
    },
  },
  argTypes: {
    theme: {
      control: 'select',
      options: ['dark', 'light'],
      description: 'Current theme — determines sun vs moon icon in theme toggle',
    },
    bellCount: {
      control: 'number',
      description: 'Unread notification count. 0 hides badge. >99 shows "99+".',
    },
    locale: {
      control: 'select',
      options: ['en', 'fr', 'ar', 'fa'],
    },
    isOffline: { control: 'boolean' },
    menuLabel: { control: 'text' },
    bellLabel: { control: 'text' },
    themeLabel: { control: 'text' },
    className: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof TopBar>;

// ---------------------------------------------------------------------------
// Default — all props populated
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default (all props)',
  args: {
    wordmark: <WordmarkDemo />,
    onMenuClick: () => console.log('menu clicked'),
    bellCount: 3,
    onBellClick: () => console.log('bell clicked'),
    locale: 'en',
    localeOptions: LOCALE_OPTIONS,
    onLocaleChange: (l) => console.log('locale →', l),
    theme: 'dark',
    onThemeChange: (t) => console.log('theme →', t),
    avatar: <AvatarDemo />,
    isOffline: false,
  },
  parameters: {
    docs: {
      description: {
        story:
          'All slots populated: hamburger, wordmark (desktop + mobile center), bell with badge (count=3), locale selector, theme toggle (dark → shows sun), avatar. `isOffline=false` so no offline dot.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// NoNotifications — bellCount=0, no badge
// ---------------------------------------------------------------------------

export const NoNotifications: Story = {
  name: 'No notifications (bellCount=0)',
  args: {
    wordmark: <WordmarkDemo />,
    onMenuClick: () => undefined,
    bellCount: 0,
    onBellClick: () => undefined,
    locale: 'en',
    localeOptions: LOCALE_OPTIONS,
    onLocaleChange: () => undefined,
    theme: 'light',
    onThemeChange: () => undefined,
    avatar: <AvatarDemo />,
    isOffline: false,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`bellCount=0`: the bell button renders but the red badge is absent. Light theme — shows moon icon.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Offline — isOffline=true
// ---------------------------------------------------------------------------

export const Offline: Story = {
  name: 'Offline indicator',
  args: {
    wordmark: <WordmarkDemo />,
    onMenuClick: () => undefined,
    bellCount: 1,
    onBellClick: () => undefined,
    locale: 'en',
    localeOptions: LOCALE_OPTIONS,
    onLocaleChange: () => undefined,
    theme: 'light',
    onThemeChange: () => undefined,
    avatar: <AvatarDemo />,
    isOffline: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`isOffline=true`: the small yellow dot appears at the start of the end-group cluster, before the bell button. Title attribute reads "You\'re offline".',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4-variant matrix: DarkEn / DarkAr / LightEn / LightAr
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark × EN',
  render: () => (
    <div data-theme="dark" style={{ background: 'var(--color-surface-primary, #0f1117)' }}>
      <TopBar
        wordmark={<WordmarkDemo />}
        onMenuClick={() => undefined}
        bellCount={7}
        onBellClick={() => undefined}
        locale="en"
        localeOptions={LOCALE_OPTIONS}
        onLocaleChange={() => undefined}
        theme="dark"
        onThemeChange={() => undefined}
        avatar={<AvatarDemo />}
        isOffline={false}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dark theme, English locale (LTR). Sun icon active (click → switch to light).',
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
      style={{ background: 'var(--color-surface-primary, #0f1117)' }}
    >
      <TopBar
        wordmark={<WordmarkDemo />}
        onMenuClick={() => undefined}
        bellCount={2}
        onBellClick={() => undefined}
        locale="ar"
        localeOptions={LOCALE_OPTIONS}
        onLocaleChange={() => undefined}
        theme="dark"
        onThemeChange={() => undefined}
        avatar={<AvatarDemo />}
        isOffline={false}
        menuLabel="القائمة"
        bellLabel="الإشعارات"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Dark theme, Arabic locale (`dir="rtl"`, `lang="ar"`). The bar fully mirrors: hamburger appears at the physical right, end-group at the physical left. Wordmark centered via `start-1/2 rtl:translate-x-1/2`.',
      },
    },
  },
};

export const LightEn: Story = {
  name: 'Light × EN',
  render: () => (
    <div data-theme="light">
      <TopBar
        wordmark={<WordmarkDemo />}
        onMenuClick={() => undefined}
        bellCount={0}
        onBellClick={() => undefined}
        locale="en"
        localeOptions={LOCALE_OPTIONS}
        onLocaleChange={() => undefined}
        theme="light"
        onThemeChange={() => undefined}
        avatar={<AvatarDemo />}
        isOffline={false}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Light theme, English locale (LTR). Moon icon active (click → switch to dark). No badge (bellCount=0).',
      },
    },
  },
};

export const LightAr: Story = {
  name: 'Light × AR',
  render: () => (
    <div data-theme="light" dir="rtl" lang="ar">
      <TopBar
        wordmark={<WordmarkDemo />}
        onMenuClick={() => undefined}
        bellCount={99}
        onBellClick={() => undefined}
        locale="ar"
        localeOptions={LOCALE_OPTIONS}
        onLocaleChange={() => undefined}
        theme="light"
        onThemeChange={() => undefined}
        avatar={<AvatarDemo />}
        isOffline={true}
        menuLabel="القائمة"
        bellLabel="الإشعارات (99)"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Light theme, Arabic locale (`dir="rtl"`, `lang="ar"`). bellCount=99 (shows "99" badge, not "99+"). isOffline=true shows yellow dot. Bar fully mirrors under RTL.',
      },
    },
  },
};
